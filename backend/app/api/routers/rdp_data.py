"""RDP-DB 데이터 보기·엑셀 입출력·역반영 API.

GET  /api/rdp/rows                — rdp.db 행을 JSON으로 (앱 내 표 보기)
GET  /api/rdp/excel/template      — 빈 입력 양식 xlsx 다운로드
GET  /api/rdp/excel/export        — 현재 rdp.db 전체를 xlsx로 다운로드
GET  /api/rdp/excel/export-pccs2  — PCCS2의 RDP 출신 샘플을 rdp_mixes 형식 xlsx로
POST /api/rdp/excel/upload        — xlsx 업로드 → rdp.db에 upsert (빈 셀 = NULL 덮어쓰기)
POST /api/rdp/sync-back           — PCCS2 수정분을 rdp.db에 직접 반영 (값 있는 컬럼만)
"""

from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routers.import_rdp import _resolve_rdp_path
from app.database.session import get_db_session
from app.models.domain import Ink, Plate, Round, Sample
from app.services.rdp_excel import (
    INK_NAME_TO_COLUMN,
    XLSX_MEDIA_TYPE,
    build_template,
    build_workbook,
    is_ink_column,
    layer_to_rdp_row,
    parse_workbook,
    read_rdp_rows,
    upsert_rdp_rows,
)

router = APIRouter(prefix="/api/rdp", tags=["rdp"])


class SyncBackRequest(BaseModel):
    path: str | None = None


def _xlsx_response(data: bytes, filename: str) -> Response:
    return Response(
        content=data,
        media_type=XLSX_MEDIA_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _read_rows_or_400(path: str | None, project: str | None = None) -> list[dict]:
    resolved = _resolve_rdp_path(path)
    if not resolved.is_file():
        raise HTTPException(status_code=404, detail=f"파일을 찾을 수 없습니다: {resolved}")
    try:
        return read_rdp_rows(str(resolved), project=project)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/rows")
async def list_rdp_rows(path: str | None = None, project: str | None = None):
    """rdp.db의 rdp_mixes 행을 JSON으로 반환 (앱 내 한눈에 보기)."""
    rows = _read_rows_or_400(path, project)
    all_projects = sorted({r["project"] for r in _read_rows_or_400(path)} if project else {r["project"] for r in rows})
    return {"total": len(rows), "projects": all_projects, "rows": rows}


@router.get("/excel/template")
async def download_template(db: AsyncSession = Depends(get_db_session)):
    """빈 입력 양식 (예시 1행 + 컬럼 설명 시트).

    PCCS2 잉크 마스터의 원료 잉크 + "기본잉크처럼 사용" 체크된 배합 잉크가
    잉크 컬럼으로 자동 포함된다 — 예: GR 등록 → gr 컬럼.
    """
    inks = (
        await db.scalars(
            select(Ink).where(
                (Ink.is_blend_ink.is_not(True)) | (Ink.is_favorite.is_(True))
            )
        )
    ).all()
    extra_inks = [
        ink.ink_name.lower()
        for ink in inks
        if ink.ink_name not in INK_NAME_TO_COLUMN and is_ink_column(ink.ink_name.lower())
    ]
    return _xlsx_response(build_template(extra_inks=extra_inks), "rdp_template.xlsx")


@router.get("/excel/export")
async def export_rdp_excel(path: str | None = None, project: str | None = None):
    """현재 rdp.db 전체(또는 프로젝트 필터)를 xlsx로 내보내기."""
    rows = _read_rows_or_400(path, project)
    stamp = datetime.now().strftime("%Y%m%d")
    return _xlsx_response(build_workbook(rows), f"rdp_export_{stamp}.xlsx")


async def _collect_pccs2_rows(db: AsyncSession) -> tuple[list[dict], int]:
    """PCCS2의 RDP 출신 샘플 레이어들을 rdp_mixes 행으로 역변환.

    반환: (rows, skipped_layers) — rdp_key 없는 레이어는 건너뛴 수로 집계.
    """
    ink_name_by_id = {
        i.ink_id: i.ink_name for i in (await db.scalars(select(Ink))).all()
    }
    # (pattern_id, plate_code) → 엠보 정보
    emboss_map = {
        (p.pattern_id, p.plate_code): (p.emboss_type, p.emboss_depth_um)
        for p in (await db.scalars(select(Plate))).all()
    }

    result = await db.execute(
        select(Sample, Round.work_date)
        .join(Round, Sample.round_id == Round.round_id)
        .where(Sample.success_notes.like("RDP:%"))
    )
    rows: list[dict] = []
    skipped = 0
    for sample, work_date in result.all():
        for layer in sample.layers or []:
            key = (layer or {}).get("rdp_key") or ""
            plate_code = key[4:].split("/")[2] if key.startswith("RDP:") else ""
            row = layer_to_rdp_row(
                layer,
                work_date.isoformat() if work_date else None,
                ink_name_by_id,
                emboss=emboss_map.get((sample.pattern_id, plate_code)),
            )
            if row is None:
                skipped += 1
            else:
                rows.append(row)
    return rows, skipped


@router.get("/excel/export-pccs2")
async def export_pccs2_excel(db: AsyncSession = Depends(get_db_session)):
    """PCCS2에서 수정한 RDP 출신 샘플들을 rdp_mixes 형식 xlsx로 내보내기.

    검토 후 그대로 업로드하면 rdp.db에 반영되는 안전한 역반영 경로.
    """
    rows, _skipped = await _collect_pccs2_rows(db)
    stamp = datetime.now().strftime("%Y%m%d")
    return _xlsx_response(build_workbook(rows), f"pccs2_to_rdp_{stamp}.xlsx")


@router.post("/excel/upload")
async def upload_rdp_excel(
    file: UploadFile = File(...),
    path: str | None = None,
):
    """xlsx 업로드 → rdp.db에 upsert. 고유키가 같으면 갱신, 없으면 추가.

    빈 셀은 NULL로 덮어쓴다 (엑셀에 보이는 그대로가 결과).
    """
    content = await file.read()
    try:
        rows, errors = parse_workbook(content)
    except Exception:
        raise HTTPException(
            status_code=400, detail="xlsx 파일을 읽을 수 없습니다 — 양식을 확인하세요"
        )
    if not rows and errors:
        raise HTTPException(status_code=400, detail="; ".join(errors[:10]))

    resolved = _resolve_rdp_path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    summary = upsert_rdp_rows(str(resolved), rows)
    return {
        "path": str(resolved),
        "total_rows": len(rows),
        "errors": errors,
        **summary,
    }


@router.post("/sync-back")
async def sync_back_to_rdp(
    body: SyncBackRequest | None = None,
    db: AsyncSession = Depends(get_db_session),
):
    """PCCS2에서 수정한 RDP 출신 샘플을 rdp.db에 직접 반영.

    값이 있는 컬럼만 갱신한다 — PCCS2가 모르는 값으로 원본을 비우지 않는다.
    rdp.db에 없는 키는 새 행으로 추가된다.
    """
    resolved = _resolve_rdp_path(body.path if body else None)
    if not resolved.is_file():
        raise HTTPException(status_code=404, detail=f"파일을 찾을 수 없습니다: {resolved}")

    rows, skipped = await _collect_pccs2_rows(db)
    summary = upsert_rdp_rows(str(resolved), rows, only_non_null=True)
    return {
        "path": str(resolved),
        "total_rows": len(rows),
        "skipped_layers": skipped,
        **summary,
    }

"""RDP-DB 가져오기 API.

POST /api/import/rdp — rdp.db(SQLite) 파일 업로드 → PCCS2 계층으로 변환.
POST /api/import/rdp/local — 서버 로컬 경로의 rdp.db를 직접 읽어 가져오기.
GET  /api/import/rdp/local-status — 로컬 rdp.db 경로/존재 여부 확인.
같은 파일을 다시 올려도 이미 가져온 배합(RDP 고유키)은 건너뛴다.
"""

import os
import tempfile
from datetime import date as date_type, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database.session import get_db_session
from app.models.domain import Ink, Pattern, Project, Round, Sample
from app.services.rdp_import import (
    RDP_INK_COLUMNS,
    RdpImportSummary,
    read_rdp_mixes,
)

router = APIRouter(prefix="/api/import", tags=["import"])

SQLITE_MAGIC = b"SQLite format 3\x00"

# 경로 미설정 시 시도하는 기본 위치 (개인용 워크플로우 관례)
DEFAULT_RDP_DB_PATH = "~/MySecondBrain/Areas/NIFCO/RDP-DB/rdp.db"


def _resolve_rdp_path(override: str | None = None) -> Path:
    raw = override or get_settings().RDP_DB_PATH or DEFAULT_RDP_DB_PATH
    return Path(raw).expanduser()


class LocalImportRequest(BaseModel):
    path: str | None = None


def _parse_date(value: str):
    try:
        return date_type.fromisoformat(value)
    except (TypeError, ValueError):
        return None


async def _ensure_inks(db: AsyncSession, summary: RdpImportSummary) -> dict:
    """RDP 기본 잉크(MT/BK/WH/YE/RD/CL/YE_D)를 마스터에 보장하고 name→ink_id 맵 반환."""
    ink_ids: dict[str, str] = {}
    for _col, (name, category) in RDP_INK_COLUMNS.items():
        ink = await db.scalar(select(Ink).where(Ink.ink_name == name).limit(1))
        if ink is None:
            ink = Ink(
                ink_id=str(uuid4()),
                ink_name=name,
                ink_category=category,
                memo="RDP-DB 가져오기로 자동 등록",
            )
            db.add(ink)
            await db.flush()
            summary.inks_created += 1
        ink_ids[name] = ink.ink_id
    return ink_ids


@router.get("/rdp/local-status")
async def rdp_local_status(path: str | None = None):
    """로컬 rdp.db 파일의 존재 여부와 메타데이터를 반환."""
    resolved = _resolve_rdp_path(path)
    exists = resolved.is_file()
    info = {"path": str(resolved), "exists": exists}
    if exists:
        stat = resolved.stat()
        info["size"] = stat.st_size
        info["modified_at"] = datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds")
    return info


@router.post("/rdp/local")
async def import_rdp_local(
    body: LocalImportRequest | None = None,
    db: AsyncSession = Depends(get_db_session),
):
    """서버(로컬 머신)의 rdp.db를 직접 읽어 가져오기 — 업로드 불필요."""
    resolved = _resolve_rdp_path(body.path if body else None)
    if not resolved.is_file():
        raise HTTPException(status_code=404, detail=f"파일을 찾을 수 없습니다: {resolved}")
    content = resolved.read_bytes()
    if not content.startswith(SQLITE_MAGIC):
        raise HTTPException(status_code=400, detail=f"SQLite 파일이 아닙니다: {resolved}")
    return await _import_content(content, db)


@router.post("/rdp")
async def import_rdp(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db_session),
):
    content = await file.read()
    if not content.startswith(SQLITE_MAGIC):
        raise HTTPException(status_code=400, detail="SQLite 파일이 아닙니다 (rdp.db를 업로드하세요)")
    return await _import_content(content, db)


async def _import_content(content: bytes, db: AsyncSession):
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        try:
            records = read_rdp_mixes(tmp_path)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
    finally:
        if tmp_path:
            os.unlink(tmp_path)

    summary = RdpImportSummary()
    ink_ids = await _ensure_inks(db, summary)

    # 캐시: 같은 요청 내 find-or-create 반복 조회 방지
    projects: dict[str, Project] = {}
    patterns: dict[tuple, Pattern] = {}
    rounds: dict[tuple, Round] = {}

    for rec in records:
        # 중복 검사: 이미 가져온 RDP 키는 건너뜀
        existing = await db.scalar(
            select(Sample.sample_id).where(Sample.success_notes == rec.rdp_key).limit(1)
        )
        if existing:
            summary.samples_skipped += 1
            continue

        # Project
        project = projects.get(rec.project)
        if project is None:
            project = await db.scalar(
                select(Project).where(Project.project_name == rec.project).limit(1)
            )
            if project is None:
                project = Project(
                    project_id=str(uuid4()),
                    project_name=rec.project,
                    memo="RDP-DB 가져오기로 자동 생성",
                )
                db.add(project)
                await db.flush()
                summary.projects_created += 1
            projects[rec.project] = project

        # Pattern (pattern_code + plate 조합이 하나의 패턴)
        pattern_name = f"{rec.pattern_code} ({rec.plate})" if rec.plate else rec.pattern_code
        pkey = (project.project_id, pattern_name)
        pattern = patterns.get(pkey)
        if pattern is None:
            pattern = await db.scalar(
                select(Pattern)
                .where(Pattern.project_id == project.project_id)
                .where(Pattern.pattern_name == pattern_name)
                .limit(1)
            )
            if pattern is None:
                pattern = Pattern(
                    pattern_id=str(uuid4()),
                    project_id=project.project_id,
                    pattern_name=pattern_name,
                    total_print_layers=2,
                    target_base_color_sci=rec.target_color,
                    notes="RDP-DB 가져오기로 자동 생성",
                )
                db.add(pattern)
                await db.flush()
                summary.patterns_created += 1
            elif rec.target_color and not pattern.target_base_color_sci:
                pattern.target_base_color_sci = rec.target_color
            patterns[pkey] = pattern

        # Round (패턴 + 작업일 단위)
        rkey = (pattern.pattern_id, rec.date)
        round_ = rounds.get(rkey)
        if round_ is None:
            round_ = await db.scalar(
                select(Round)
                .where(Round.pattern_id == pattern.pattern_id)
                .where(Round.work_date == _parse_date(rec.date))
                .limit(1)
            )
            if round_ is None:
                max_no = 0
                for existing_round in rounds.values():
                    if existing_round.pattern_id == pattern.pattern_id:
                        max_no = max(max_no, existing_round.round_number)
                db_max = await db.scalar(
                    select(Round.round_number)
                    .where(Round.pattern_id == pattern.pattern_id)
                    .order_by(Round.round_number.desc())
                    .limit(1)
                )
                max_no = max(max_no, db_max or 0)
                round_ = Round(
                    round_id=str(uuid4()),
                    pattern_id=pattern.pattern_id,
                    round_number=max_no + 1,
                    work_date=_parse_date(rec.date),
                    work_location="RDP-DB import",
                )
                db.add(round_)
                await db.flush()
                summary.rounds_created += 1
            rounds[rkey] = round_

        # Sample (배합 1건 = 단일 레이어 샘플)
        max_sample_no = await db.scalar(
            select(Sample.sample_number)
            .where(Sample.round_id == round_.round_id)
            .order_by(Sample.sample_number.desc())
            .limit(1)
        )
        layer = {
            "layer_number": rec.layer_number,
            "ink_items": [
                {"ink_id": ink_ids[name], "amount": amount}
                for name, amount in rec.ink_amounts.items()
            ],
            "thinner_pct": rec.thinner_pct,
            "hardener_pct": rec.hardener_pct,
            "print_color_sci": rec.measured_color,
            "print_color_sce": None,
            "delta_E_from_target": rec.delta_e,
            "note": f"배합 {rec.batch_no}"
            + (" [기준배합]" if rec.is_base else "")
            + (f" | {rec.note}" if rec.note else ""),
        }
        db.add(
            Sample(
                sample_id=str(uuid4()),
                round_id=round_.round_id,
                pattern_id=pattern.pattern_id,
                sample_number=(max_sample_no or 0) + 1,
                base_color_sci=rec.target_color,
                base_color_sce=None,
                layers=[layer],
                final_delta_e=rec.delta_e,
                success_flag=rec.success_flag,
                success_notes=rec.rdp_key,
            )
        )
        summary.samples_created += 1

    await db.commit()
    return {
        "projects_created": summary.projects_created,
        "patterns_created": summary.patterns_created,
        "rounds_created": summary.rounds_created,
        "samples_created": summary.samples_created,
        "samples_skipped": summary.samples_skipped,
        "inks_created": summary.inks_created,
        "total_rows": len(records),
    }

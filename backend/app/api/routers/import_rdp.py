"""RDP-DB 가져오기 API.

POST /api/import/rdp — rdp.db(SQLite) 파일 업로드 → PCCS2 계층으로 변환.
POST /api/import/rdp/local — 서버 로컬 경로의 rdp.db를 직접 읽어 가져오기.
GET  /api/import/rdp/local-status — 로컬 rdp.db 경로/존재 여부 확인.

재가져오기 규칙: 이미 가져온 배합(레이어의 rdp_key)과 내용이 같으면 건너뛰고,
RDP-DB 쪽에서 값이 바뀐 행(예: 측색값 추후 입력)은 해당 레이어를 업데이트한다.

1도/2도 합치기: 같은 패턴·같은 작업일에 각 도수가 정확히 1건씩일 때만
한 샘플의 레이어들로 합친다. 같은 도수가 2건 이상인 날은 어느 1도 위에
어느 2도를 찍었는지 원본에 정보가 없으므로(시편 ID 부재) 추측하지 않고
행마다 별도 샘플로 만든다.
"""

import os
import tempfile
from collections import Counter, defaultdict
from datetime import date as date_type, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.config import get_settings
from app.database.session import get_db_session
from app.models.domain import Ink, Pattern, Plate, Project, Round, Sample
from app.services.rdp_import import (
    RDP_INK_COLUMNS,
    RdpImportSummary,
    RdpMixRecord,
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


def _build_layer(rec: RdpMixRecord, ink_ids: dict) -> dict:
    """rdp_mixes 한 행을 샘플 레이어 JSON으로 변환."""
    note_parts = [f"배합 {rec.batch_no}"]
    if rec.is_base:
        note_parts.append("[기준배합]")
    if rec.note:
        note_parts.append(rec.note)

    layer: dict = {
        "layer_number": rec.layer_number,
        "ink_items": [
            {"ink_id": ink_ids[name], "ink_name": name, "amount": amount}
            for name, amount in rec.ink_amounts.items()
        ],
        "thinner_pct": rec.thinner_pct,
        "hardener_pct": rec.hardener_pct,
        "print_color_sci": rec.measured_color,
        "print_color_sce": rec.measured_color_sce,
        "delta_E_from_target": rec.delta_e,
        "note": " | ".join(note_parts),
        # 행 단위 메타: rdp_key는 중복/업데이트 판정 키
        "rdp_key": rec.rdp_key,
        "batch_no": rec.batch_no,
        "is_base": rec.is_base,
        "result": rec.success_flag,
    }
    # 선택적 필드: None이 아닌 것만 포함해 JSON을 간결하게 유지
    optionals = {
        "target_color_sci": rec.target_color,
        "target_color_sce": rec.target_color_sce,
        "change_summary": rec.note,
        "thinner_g": rec.thinner_g,
        "hardener_g": rec.hardener_g,
        "matting_agent_pct": rec.matting_agent_pct,
        "matting_agent_g": rec.matting_agent_g,
        "total_g": rec.total_g,
        "coating_maker": rec.coating_maker,
        "coating_code": rec.coating_code,
        "coating_lot": rec.coating_lot,
        "pad_name": rec.pad_name,
        "pad_hardness": rec.pad_hardness,
        "source_file": rec.source_file,
    }
    layer.update({k: v for k, v in optionals.items() if v is not None})
    return layer


def _recompute_sample(sample: Sample) -> None:
    """레이어들로부터 샘플 집계 필드를 재계산 (도수 순 정렬 포함)."""
    layers = sorted(sample.layers or [], key=lambda ly: ly.get("layer_number") or 0)
    sample.layers = layers
    flag_modified(sample, "layers")

    flags = [ly.get("result") for ly in layers]
    if any(f == "FAILED" for f in flags):
        sample.success_flag = "FAILED"
    elif flags and all(f == "SUCCESS" for f in flags):
        sample.success_flag = "SUCCESS"
    else:
        sample.success_flag = "PENDING"

    final_de = None
    for ly in layers:
        if ly.get("delta_E_from_target") is not None:
            final_de = ly["delta_E_from_target"]
    sample.final_delta_e = final_de

    keys = sorted(k for k in (ly.get("rdp_key") for ly in layers) if k)
    sample.success_notes = "\n".join(keys)


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
    plates: dict[tuple, Plate] = {}
    rounds: dict[tuple, Round] = {}
    round_samples: dict[str, list[Sample]] = {}

    # 기존 RDP 샘플의 레이어별 키맵.
    # 레거시(행=샘플 1:1, success_notes=키 하나) 샘플은 0번 레이어로 간주해
    # 재가져오기 때 새 구조로 자연 마이그레이션된다.
    key_map: dict[str, tuple[Sample, int]] = {}
    existing_rdp_samples = (
        await db.scalars(select(Sample).where(Sample.success_notes.like("RDP:%")))
    ).all()
    for s in existing_rdp_samples:
        keyed = False
        for i, ly in enumerate(s.layers or []):
            k = (ly or {}).get("rdp_key")
            if k:
                key_map[k] = (s, i)
                keyed = True
        if not keyed and s.success_notes and "\n" not in s.success_notes:
            key_map[s.success_notes] = (s, 0)

    touched: dict[str, Sample] = {}   # 집계 재계산 대상
    created_ids: set[str] = set()
    updated_ids: set[str] = set()

    # 합치기 가능 여부 사전 판정: 같은 날(패턴+동판+작업일)에 어떤 도수든
    # 2건 이상이면 그날은 합치지 않는다 (어느 1도 위에 어느 2도인지 추측 불가).
    layer_counts: dict[tuple, Counter] = defaultdict(Counter)
    for rec in records:
        layer_counts[(rec.project, rec.pattern_code, rec.plate, rec.date)][
            rec.layer_number
        ] += 1

    def _day_is_mergeable(rec) -> bool:
        counts = layer_counts[(rec.project, rec.pattern_code, rec.plate, rec.date)]
        return all(c == 1 for c in counts.values())

    for rec in records:
        layer = _build_layer(rec, ink_ids)

        # 이미 가져온 행: 내용이 같으면 건너뛰고, 바뀌었으면 레이어 업데이트
        if rec.rdp_key in key_map:
            sample, idx = key_map[rec.rdp_key]
            layers = list(sample.layers or [])
            if idx < len(layers) and layers[idx] == layer:
                summary.samples_skipped += 1
                continue
            if idx < len(layers):
                layers[idx] = layer
            else:
                layers.append(layer)
            sample.layers = layers
            # 레거시 보정: 목표색을 베이스 색상 자리에 넣던 것을 해제
            # (베이스 색은 베이스 마스터에서 관리, 목표색은 레이어 target_color_sci)
            if sample.base_color_sci == rec.target_color:
                sample.base_color_sci = None
            touched[sample.sample_id] = sample
            if sample.sample_id not in created_ids:
                updated_ids.add(sample.sample_id)
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
                    target_base_color_sce=rec.target_color_sce,
                    notes="RDP-DB 가져오기로 자동 생성",
                )
                db.add(pattern)
                await db.flush()
                summary.patterns_created += 1
            else:
                if rec.target_color and not pattern.target_base_color_sci:
                    pattern.target_base_color_sci = rec.target_color
                if rec.target_color_sce and not pattern.target_base_color_sce:
                    pattern.target_base_color_sce = rec.target_color_sce
            patterns[pkey] = pattern

        # Plate (동판 마스터): 차종 > 패턴 > 동판 계층 유지
        if rec.plate:
            plkey = (pattern.pattern_id, rec.plate)
            if plkey not in plates:
                plate = await db.scalar(
                    select(Plate)
                    .where(Plate.pattern_id == pattern.pattern_id)
                    .where(Plate.plate_code == rec.plate)
                    .limit(1)
                )
                if plate is None:
                    plate = Plate(
                        plate_id=str(uuid4()),
                        pattern_id=pattern.pattern_id,
                        plate_code=rec.plate,
                        emboss_type=rec.emboss_type,
                        emboss_depth_um=rec.emboss_depth_um,
                        memo="RDP-DB 가져오기로 자동 생성",
                    )
                    db.add(plate)
                    await db.flush()
                    summary.plates_created += 1
                else:
                    # 기존 동판에 엠보스 정보가 없으면 채워넣기
                    if plate.emboss_type is None and rec.emboss_type:
                        plate.emboss_type = rec.emboss_type
                    if plate.emboss_depth_um is None and rec.emboss_depth_um is not None:
                        plate.emboss_depth_um = rec.emboss_depth_um
                plates[plkey] = plate

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

        # Sample: 그날 각 도수가 1건씩뿐이면 같은 라운드의 RDP 샘플 중
        # 이 도수가 비어 있는 샘플에 레이어를 합친다 (1도+2도 = 시편 하나).
        # 모호한 날(같은 도수 2건 이상)이거나 합칠 샘플이 없으면 새 샘플.
        rsamples = round_samples.get(round_.round_id)
        if rsamples is None:
            rsamples = list(
                (
                    await db.scalars(
                        select(Sample)
                        .where(Sample.round_id == round_.round_id)
                        .where(Sample.success_notes.like("RDP:%"))
                    )
                ).all()
            )
            round_samples[round_.round_id] = rsamples

        sample = None
        if _day_is_mergeable(rec):
            sample = next(
                (
                    s
                    for s in rsamples
                    if all(
                        ly.get("layer_number") != rec.layer_number
                        for ly in (s.layers or [])
                    )
                ),
                None,
            )
        if sample is None:
            max_sample_no = await db.scalar(
                select(Sample.sample_number)
                .where(Sample.round_id == round_.round_id)
                .order_by(Sample.sample_number.desc())
                .limit(1)
            )
            sample = Sample(
                sample_id=str(uuid4()),
                round_id=round_.round_id,
                pattern_id=pattern.pattern_id,
                sample_number=(max_sample_no or 0) + 1,
                # 베이스 색은 베이스 마스터에서 — 목표색은 레이어 target_color_sci에
                base_color_sci=None,
                base_color_sce=None,
                layers=[layer],
            )
            db.add(sample)
            rsamples.append(sample)
            created_ids.add(sample.sample_id)
            summary.samples_created += 1
        else:
            sample.layers = list(sample.layers or []) + [layer]
            if sample.sample_id not in created_ids:
                updated_ids.add(sample.sample_id)
        key_map[rec.rdp_key] = (sample, len(sample.layers) - 1)
        touched[sample.sample_id] = sample

    for sample in touched.values():
        _recompute_sample(sample)
    summary.samples_updated = len(updated_ids)

    await db.commit()
    return {
        "projects_created": summary.projects_created,
        "patterns_created": summary.patterns_created,
        "plates_created": summary.plates_created,
        "rounds_created": summary.rounds_created,
        "samples_created": summary.samples_created,
        "samples_updated": summary.samples_updated,
        "samples_skipped": summary.samples_skipped,
        "inks_created": summary.inks_created,
        "total_rows": len(records),
    }

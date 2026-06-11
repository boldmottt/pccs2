"""RDP-DB(rdp.db) 가져오기 서비스.

NIFCO 작업일지에서 추출한 RDP 배합비 SQLite DB(rdp_mixes 테이블)를
PCCS2의 Project → Pattern → Round → Sample 계층으로 변환한다.

rdp_mixes 한 행 = 특정 도수(layer)의 배합 1건(batch_no).
UNIQUE(project, pattern_code, plate, layer, batch_no)가 원본 식별자이며,
이 키를 Sample.success_notes 에 "RDP:..." 태그로 저장해 재가져오기 시 중복을 건너뛴다.
"""

import sqlite3
from dataclasses import dataclass, field
from typing import Optional


# rdp_mixes 잉크 컬럼 → PCCS2 마스터 잉크 (이름, 카테고리)
RDP_INK_COLUMNS = {
    "mt": ("MT", "COLOR"),
    "bk": ("BK", "COLOR"),
    "wh": ("WH", "COLOR"),
    "ye": ("YE", "COLOR"),
    "rd": ("RD", "COLOR"),
    "cl": ("CL", "TRANSPARENT"),
    "ye_d": ("YE_D", "COLOR"),
}

RESULT_FLAG_MAP = {
    "✅": "SUCCESS",
    "⚠️": "PENDING",
    "❌": "FAILED",
}


@dataclass
class RdpMixRecord:
    """rdp_mixes 한 행을 정규화한 레코드."""

    rdp_key: str
    date: str
    project: str
    pattern_code: str
    plate: str
    layer_number: int
    batch_no: str
    is_base: bool
    ink_amounts: dict  # ink name -> grams (0 제외)
    thinner_pct: Optional[float]
    hardener_pct: Optional[float]
    target_color: Optional[dict]  # {"L", "a", "b"} or None
    measured_color: Optional[dict]
    delta_e: Optional[float]
    success_flag: str
    note: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class RdpImportSummary:
    projects_created: int = 0
    patterns_created: int = 0
    rounds_created: int = 0
    samples_created: int = 0
    samples_skipped: int = 0
    inks_created: int = 0
    errors: list = field(default_factory=list)


def _parse_layer_number(layer: Optional[str]) -> int:
    """'1도'/'2도' → 1/2. 파싱 불가 시 1."""
    if not layer:
        return 1
    digits = "".join(ch for ch in str(layer) if ch.isdigit())
    return int(digits) if digits else 1


def _lab_or_none(row: sqlite3.Row, prefix: str) -> Optional[dict]:
    keys = row.keys()
    values = []
    for axis in ("L", "a", "b"):
        col = f"{prefix}_{axis}"
        v = row[col] if col in keys else None
        if v is None:
            return None
        values.append(float(v))
    return {"L": values[0], "a": values[1], "b": values[2]}


def make_rdp_key(project: str, pattern_code: str, plate: str, layer: str, batch_no: str) -> str:
    return f"RDP:{project}/{pattern_code}/{plate}/{layer}/{batch_no}"


def read_rdp_mixes(db_path: str) -> list[RdpMixRecord]:
    """rdp.db 파일에서 rdp_mixes 행을 읽어 정규화한다."""
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        tables = {
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        if "rdp_mixes" not in tables:
            raise ValueError("rdp_mixes 테이블이 없습니다 — 올바른 rdp.db 파일인지 확인하세요")

        records: list[RdpMixRecord] = []
        for row in conn.execute("SELECT * FROM rdp_mixes ORDER BY date, id"):
            keys = row.keys()

            ink_amounts = {}
            for col, (ink_name, _category) in RDP_INK_COLUMNS.items():
                amount = row[col] if col in keys else None
                if amount:
                    ink_amounts[ink_name] = float(amount)

            layer_raw = row["layer"] if row["layer"] is not None else "1도"
            batch_no = str(row["batch_no"]) if row["batch_no"] is not None else ""
            result = (row["result"] or "").strip() if "result" in keys else ""

            records.append(
                RdpMixRecord(
                    rdp_key=make_rdp_key(
                        row["project"], row["pattern_code"] or "", row["plate"] or "",
                        layer_raw, batch_no,
                    ),
                    date=row["date"],
                    project=row["project"],
                    pattern_code=row["pattern_code"] or "(미지정)",
                    plate=row["plate"] or "",
                    layer_number=_parse_layer_number(layer_raw),
                    batch_no=batch_no,
                    is_base=bool(row["is_base"]) if "is_base" in keys else False,
                    ink_amounts=ink_amounts,
                    thinner_pct=float(row["thinner_pct"]) if "thinner_pct" in keys and row["thinner_pct"] is not None else None,
                    hardener_pct=float(row["hardener_pct"]) if "hardener_pct" in keys and row["hardener_pct"] is not None else None,
                    target_color=_lab_or_none(row, "target"),
                    measured_color=_lab_or_none(row, "measured"),
                    delta_e=float(row["delta_e"]) if "delta_e" in keys and row["delta_e"] is not None else None,
                    success_flag=RESULT_FLAG_MAP.get(result, "PENDING"),
                    note=row["change_summary"] if "change_summary" in keys else None,
                    notes=row["notes"] if "notes" in keys else None,
                )
            )
        return records
    finally:
        conn.close()

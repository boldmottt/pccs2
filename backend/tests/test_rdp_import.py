"""RDP-DB(rdp.db) 가져오기 API 테스트."""

import sqlite3

import pytest


RDP_SCHEMA = """
CREATE TABLE rdp_mixes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    project TEXT NOT NULL,
    pattern_code TEXT NOT NULL,
    plate TEXT NOT NULL,
    layer TEXT NOT NULL,
    batch_no TEXT NOT NULL,
    is_base INTEGER DEFAULT 0,
    mt REAL DEFAULT 0,
    bk REAL DEFAULT 0,
    wh REAL DEFAULT 0,
    ye REAL DEFAULT 0,
    rd REAL DEFAULT 0,
    cl REAL DEFAULT 0,
    ye_d REAL DEFAULT 0,
    matting_agent_pct REAL DEFAULT 2,
    matting_agent_g REAL,
    thinner_pct REAL DEFAULT 30,
    thinner_g REAL,
    hardener_pct REAL DEFAULT 20,
    hardener_g REAL,
    total_g REAL,
    result TEXT,
    notes TEXT,
    change_summary TEXT,
    source_file TEXT,
    target_L REAL, target_a REAL, target_b REAL,
    measured_L REAL, measured_a REAL, measured_b REAL,
    delta_e REAL, result_code TEXT,
    UNIQUE(project, pattern_code, plate, layer, batch_no)
)
"""


@pytest.fixture
def rdp_db_file(tmp_path):
    """실제 rdp.db 스키마를 그대로 따르는 테스트 DB 파일."""
    path = tmp_path / "rdp.db"
    conn = sqlite3.connect(path)
    conn.execute(RDP_SCHEMA)
    rows = [
        # NX5a / WB7 / 26_027 — 1도 기준배합 + 변경배합, 2도 1건
        ("2026-05-11", "NX5a", "WB7", "26_027", "1도", "25", 1,
         2.3, 0.0, 35.8, 25.0, 6.3, "✅", None,
         30.0, 73.0, -2.1, 5.2, 73.4, -1.9, 5.0, 0.55),
        ("2026-05-12", "NX5a", "WB7", "26_027", "1도", "28", 0,
         2.3, 0.0, 35.4, 28.0, 6.3, "⚠️", "YE+3g",
         30.0, 73.0, -2.1, 5.2, 72.1, -2.8, 6.9, 2.31),
        ("2026-05-12", "NX5a", "WB7", "26_027", "2도", "AH", 0,
         2.3, 0.0, 35.2, 23.5, 5.9, "❌", "WH-3g",
         30.0, None, None, None, None, None, None, None),
        # MQ5 — 다른 프로젝트
        ("2026-05-11", "MQ5", "M-60507-F1", "26_040", "1도", "라", 1,
         0.5, 1.4, 19.0, 12.8, 0.0, "✅", None,
         30.0, None, None, None, None, None, None, None),
    ]
    for (date, project, pattern, plate, layer, batch, is_base,
         mt, bk, wh, ye, rd, result, change,
         thinner, tl, ta, tb, ml, ma, mb, de) in rows:
        conn.execute(
            """INSERT INTO rdp_mixes
               (date, project, pattern_code, plate, layer, batch_no, is_base,
                mt, bk, wh, ye, rd, result, change_summary, thinner_pct, hardener_pct,
                target_L, target_a, target_b, measured_L, measured_a, measured_b, delta_e)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (date, project, pattern, plate, layer, batch, is_base,
             mt, bk, wh, ye, rd, result, change, thinner, 20.0,
             tl, ta, tb, ml, ma, mb, de),
        )
    conn.commit()
    conn.close()
    return path


def _upload(api_client, path):
    with open(path, "rb") as f:
        return api_client.post(
            "/api/import/rdp",
            files={"file": ("rdp.db", f, "application/octet-stream")},
        )


def test_import_creates_full_hierarchy(api_client, rdp_db_file):
    resp = _upload(api_client, rdp_db_file)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_rows"] == 4
    assert body["projects_created"] == 2       # NX5a, MQ5
    assert body["patterns_created"] == 2       # WB7 (26_027), M-60507-F1 (26_040)
    assert body["rounds_created"] == 3         # WB7: 05-11, 05-12 / MQ5: 05-11
    assert body["samples_created"] == 4
    assert body["samples_skipped"] == 0
    assert body["inks_created"] == 7           # MT/BK/WH/YE/RD/CL/YE_D 자동 등록

    projects = api_client.get("/api/projects/").json()
    names = {p["project_name"] for p in projects}
    assert names == {"NX5a", "MQ5"}


def test_import_maps_colors_and_result(api_client, rdp_db_file):
    _upload(api_client, rdp_db_file)
    samples = api_client.get("/api/samples/").json()
    by_key = {s["success_notes"]: s for s in samples}

    base = by_key["RDP:NX5a/WB7/26_027/1도/25"]
    assert base["success_flag"] == "SUCCESS"
    assert base["base_color_sci"] == {"L": 73.0, "a": -2.1, "b": 5.2}
    assert base["final_delta_e"] == 0.55
    layer = base["layers"][0]
    assert layer["layer_number"] == 1
    assert layer["print_color_sci"] == {"L": 73.4, "a": -1.9, "b": 5.0}
    assert layer["thinner_pct"] == 30.0
    amounts = {i["amount"] for i in layer["ink_items"]}
    assert amounts == {2.3, 35.8, 25.0, 6.3}   # mt, wh, ye, rd (bk=0 제외)
    assert "[기준배합]" in layer["note"]

    failed = by_key["RDP:NX5a/WB7/26_027/2도/AH"]
    assert failed["success_flag"] == "FAILED"
    assert failed["layers"][0]["layer_number"] == 2
    assert "WH-3g" in failed["layers"][0]["note"]


def test_reimport_skips_existing(api_client, rdp_db_file):
    first = _upload(api_client, rdp_db_file).json()
    assert first["samples_created"] == 4

    second = _upload(api_client, rdp_db_file).json()
    assert second["samples_created"] == 0
    assert second["samples_skipped"] == 4
    assert second["projects_created"] == 0
    assert second["inks_created"] == 0


def test_import_rejects_non_sqlite(api_client):
    resp = api_client.post(
        "/api/import/rdp",
        files={"file": ("rdp.db", b"not a sqlite file", "application/octet-stream")},
    )
    assert resp.status_code == 400


def test_import_rejects_sqlite_without_rdp_mixes(api_client, tmp_path):
    path = tmp_path / "other.db"
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE foo (id INTEGER)")
    conn.commit()
    conn.close()
    resp = _upload(api_client, path)
    assert resp.status_code == 400
    assert "rdp_mixes" in resp.json()["detail"]

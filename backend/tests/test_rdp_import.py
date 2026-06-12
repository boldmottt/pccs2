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
    emboss_type TEXT,
    emboss_depth_um INTEGER,
    coating_maker TEXT,
    coating_code TEXT,
    coating_lot TEXT,
    pad_name TEXT,
    pad_hardness TEXT,
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
        # (date, project, pattern, plate, layer, batch, is_base,
        #  mt, bk, wh, ye, rd, result, change,
        #  thinner_pct, mat_pct, mat_g, thinner_g, hardener_g, total_g,
        #  emboss_type, emboss_depth_um, coating_maker, coating_code, coating_lot, pad_name, pad_hardness,
        #  source_file, tl, ta, tb, ml, ma, mb, de)
        ("2026-05-11", "NX5a", "WB7", "26_027", "1도", "25", 1,
         2.3, 0.0, 35.8, 25.0, 6.3, "✅", None,
         30.0, 2.0, 1.5, 18.0, 12.0, 92.5,
         "H-type", 180, "ACME", "CT-01", "L2026-05", "P-10", "70A",
         "worklog_2026-05.xlsx",
         73.0, -2.1, 5.2, 73.4, -1.9, 5.0, 0.55),
        ("2026-05-12", "NX5a", "WB7", "26_027", "1도", "28", 0,
         2.3, 0.0, 35.4, 28.0, 6.3, "⚠️", "YE+3g",
         30.0, 2.0, None, None, None, None,
         "H-type", 180, None, None, None, None, None,
         None,
         73.0, -2.1, 5.2, 72.1, -2.8, 6.9, 2.31),
        ("2026-05-12", "NX5a", "WB7", "26_027", "2도", "AH", 0,
         2.3, 0.0, 35.2, 23.5, 5.9, "❌", "WH-3g",
         30.0, 2.0, None, None, None, None,
         None, None, None, None, None, None, None,
         None,
         None, None, None, None, None, None, None),
        # MQ5 — 다른 프로젝트
        ("2026-05-11", "MQ5", "M-60507-F1", "26_040", "1도", "라", 1,
         0.5, 1.4, 19.0, 12.8, 0.0, "✅", None,
         30.0, 2.0, None, None, None, None,
         None, None, None, None, None, None, None,
         None,
         None, None, None, None, None, None, None),
    ]
    for (date, project, pattern, plate, layer, batch, is_base,
         mt, bk, wh, ye, rd, result, change,
         thinner_pct, mat_pct, mat_g, thinner_g, hardener_g, total_g,
         emboss_type, emboss_depth_um, coating_maker, coating_code, coating_lot, pad_name, pad_hardness,
         source_file, tl, ta, tb, ml, ma, mb, de) in rows:
        conn.execute(
            """INSERT INTO rdp_mixes
               (date, project, pattern_code, plate, layer, batch_no, is_base,
                mt, bk, wh, ye, rd, result, change_summary,
                thinner_pct, hardener_pct, matting_agent_pct, matting_agent_g,
                thinner_g, hardener_g, total_g,
                emboss_type, emboss_depth_um,
                coating_maker, coating_code, coating_lot, pad_name, pad_hardness, source_file,
                target_L, target_a, target_b, measured_L, measured_a, measured_b, delta_e)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (date, project, pattern, plate, layer, batch, is_base,
             mt, bk, wh, ye, rd, result, change,
             thinner_pct, 20.0, mat_pct, mat_g, thinner_g, hardener_g, total_g,
             emboss_type, emboss_depth_um,
             coating_maker, coating_code, coating_lot, pad_name, pad_hardness, source_file,
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


def _find_by_key(samples, rdp_key):
    """rdp_key를 가진 (샘플, 레이어) 쌍을 찾는다."""
    for s in samples:
        for ly in s["layers"] or []:
            if ly.get("rdp_key") == rdp_key:
                return s, ly
    raise AssertionError(f"rdp_key not found: {rdp_key}")


def test_import_creates_full_hierarchy(api_client, rdp_db_file):
    resp = _upload(api_client, rdp_db_file)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_rows"] == 4
    assert body["projects_created"] == 2       # NX5a, MQ5
    assert body["patterns_created"] == 2       # WB7 (26_027), M-60507-F1 (26_040)
    assert body["rounds_created"] == 3         # WB7: 05-11, 05-12 / MQ5: 05-11
    # 05-12의 1도+2도가 한 샘플로 합쳐져 4행 → 샘플 3개
    assert body["samples_created"] == 3
    assert body["samples_updated"] == 0
    assert body["samples_skipped"] == 0
    assert body["inks_created"] == 7           # MT/BK/WH/YE/RD/CL/YE_D 자동 등록

    projects = api_client.get("/api/projects/").json()
    names = {p["project_name"] for p in projects}
    assert names == {"NX5a", "MQ5"}


def test_import_maps_colors_and_result(api_client, rdp_db_file):
    _upload(api_client, rdp_db_file)
    samples = api_client.get("/api/samples/").json()

    base, layer = _find_by_key(samples, "RDP:NX5a/WB7/26_027/1도/25")
    assert base["success_flag"] == "SUCCESS"
    # 베이스 색은 베이스 마스터에서 관리 — 목표색은 레이어에 저장
    assert base["base_color_sci"] is None
    assert base["final_delta_e"] == 0.55
    assert layer["layer_number"] == 1
    assert layer["print_color_sci"] == {"L": 73.4, "a": -1.9, "b": 5.0}
    assert layer["target_color_sci"] == {"L": 73.0, "a": -2.1, "b": 5.2}
    assert layer["thinner_pct"] == 30.0
    assert layer["batch_no"] == "25"
    assert layer["is_base"] is True
    assert layer["result"] == "SUCCESS"
    amounts = {i["amount"] for i in layer["ink_items"]}
    assert amounts == {2.3, 35.8, 25.0, 6.3}   # mt, wh, ye, rd (bk=0 제외)
    assert "[기준배합]" in layer["note"]


def test_same_day_layers_merge_into_one_sample(api_client, rdp_db_file):
    """같은 패턴·같은 작업일의 1도/2도는 한 샘플의 레이어 2개로 합쳐진다."""
    _upload(api_client, rdp_db_file)
    samples = api_client.get("/api/samples/").json()

    s1, ly1 = _find_by_key(samples, "RDP:NX5a/WB7/26_027/1도/28")
    s2, ly2 = _find_by_key(samples, "RDP:NX5a/WB7/26_027/2도/AH")
    assert s1["sample_id"] == s2["sample_id"]
    assert len(s1["layers"]) == 2
    assert [ly["layer_number"] for ly in s1["layers"]] == [1, 2]
    # 1도 ⚠️(PENDING) + 2도 ❌(FAILED) → 샘플은 FAILED
    assert s1["success_flag"] == "FAILED"
    # 2도는 delta 없음 → 마지막 delta 보유 레이어(1도)의 값
    assert s1["final_delta_e"] == 2.31
    assert "WH-3g" in ly2["note"]
    assert "YE+3g" in ly1["note"]
    # success_notes 에 두 키가 모두 기록됨
    assert "RDP:NX5a/WB7/26_027/1도/28" in s1["success_notes"]
    assert "RDP:NX5a/WB7/26_027/2도/AH" in s1["success_notes"]


def test_ambiguous_day_rows_stay_separate(api_client, tmp_path):
    """같은 날 같은 도수가 2건 이상이면 추측 합치기를 하지 않고 행마다 별도 샘플."""
    path = tmp_path / "ambiguous.db"
    conn = sqlite3.connect(path)
    conn.execute(RDP_SCHEMA)
    # 같은 날: 1도 배합 2건(25, 28) + 2도 1건(AH) → 어느 1도 위 2도인지 알 수 없음
    for layer, batch in [("1도", "25"), ("1도", "28"), ("2도", "AH")]:
        conn.execute(
            """INSERT INTO rdp_mixes
               (date, project, pattern_code, plate, layer, batch_no, is_base,
                wh, ye, result, thinner_pct, hardener_pct)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            ("2026-05-20", "NX5a", "WB7", "26_027", layer, batch, 0,
             30.0, 10.0, "✅", 30.0, 20.0),
        )
    conn.commit()
    conn.close()

    body = _upload(api_client, path).json()
    assert body["total_rows"] == 3
    assert body["samples_created"] == 3       # 합치지 않음
    samples = api_client.get("/api/samples/").json()
    assert all(len(s["layers"]) == 1 for s in samples)


def test_reimport_skips_existing(api_client, rdp_db_file):
    first = _upload(api_client, rdp_db_file).json()
    assert first["samples_created"] == 3

    second = _upload(api_client, rdp_db_file).json()
    assert second["samples_created"] == 0
    assert second["samples_updated"] == 0
    assert second["samples_skipped"] == 4
    assert second["projects_created"] == 0
    assert second["inks_created"] == 0


def test_reimport_updates_changed_rows(api_client, rdp_db_file):
    """RDP-DB에서 값이 바뀐 행(예: 측색값 추후 입력)은 재가져오기 때 업데이트된다."""
    _upload(api_client, rdp_db_file)

    conn = sqlite3.connect(rdp_db_file)
    conn.execute(
        "UPDATE rdp_mixes SET measured_L=70.0, measured_a=-2.5, measured_b=6.0,"
        " delta_e=1.2, result='✅' WHERE layer='2도'"
    )
    conn.commit()
    conn.close()

    body = _upload(api_client, rdp_db_file).json()
    assert body["samples_created"] == 0
    assert body["samples_updated"] == 1
    assert body["samples_skipped"] == 3

    samples = api_client.get("/api/samples/").json()
    s, ly = _find_by_key(samples, "RDP:NX5a/WB7/26_027/2도/AH")
    assert ly["print_color_sci"] == {"L": 70.0, "a": -2.5, "b": 6.0}
    assert ly["result"] == "SUCCESS"
    # 이제 마지막 delta 보유 레이어가 2도 → 샘플 delta 갱신
    assert s["final_delta_e"] == 1.2
    # 1도 ⚠️(PENDING) + 2도 ✅ → 샘플은 PENDING
    assert s["success_flag"] == "PENDING"


def test_extended_fields_stored(api_client, rdp_db_file):
    """emboss, coating, pad, matting, total_g 데이터가 올바르게 저장되는지 확인."""
    _upload(api_client, rdp_db_file)

    # Plate 엔드포인트로 동판 확인
    projects = api_client.get("/api/projects/").json()
    nx5a = next(p for p in projects if p["project_name"] == "NX5a")
    patterns = api_client.get("/api/patterns/", params={"project_id": nx5a["project_id"]}).json()
    pattern = patterns[0]
    plates = api_client.get("/api/plates/", params={"pattern_id": pattern["pattern_id"]}).json()
    assert len(plates) == 1
    plate = plates[0]
    assert plate["emboss_type"] == "H-type"
    assert plate["emboss_depth_um"] == 180

    # Layer JSON 안에 coating / pad / matting / total_g 확인
    samples = api_client.get("/api/samples/").json()
    _base, layer = _find_by_key(samples, "RDP:NX5a/WB7/26_027/1도/25")
    assert layer["coating_maker"] == "ACME"
    assert layer["coating_code"] == "CT-01"
    assert layer["coating_lot"] == "L2026-05"
    assert layer["pad_name"] == "P-10"
    assert layer["pad_hardness"] == "70A"
    assert layer["matting_agent_pct"] == 2.0
    assert layer["matting_agent_g"] == 1.5
    assert layer["thinner_g"] == 18.0
    assert layer["total_g"] == 92.5
    assert layer["source_file"] == "worklog_2026-05.xlsx"
    # ink_items에 ink_name 포함 확인
    ink_names = {i["ink_name"] for i in layer["ink_items"]}
    assert "MT" in ink_names
    assert "WH" in ink_names


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


def test_local_status_missing_file(api_client, tmp_path):
    resp = api_client.get(
        "/api/import/rdp/local-status", params={"path": str(tmp_path / "no.db")}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["exists"] is False
    assert body["path"].endswith("no.db")


def test_local_status_existing_file(api_client, rdp_db_file):
    resp = api_client.get("/api/import/rdp/local-status", params={"path": str(rdp_db_file)})
    body = resp.json()
    assert body["exists"] is True
    assert body["size"] > 0
    assert "modified_at" in body


def test_local_import_from_path(api_client, rdp_db_file):
    resp = api_client.post("/api/import/rdp/local", json={"path": str(rdp_db_file)})
    assert resp.status_code == 200
    assert resp.json()["samples_created"] == 3

    again = api_client.post("/api/import/rdp/local", json={"path": str(rdp_db_file)})
    assert again.json()["samples_skipped"] == 4


def test_local_import_missing_file_404(api_client, tmp_path):
    resp = api_client.post("/api/import/rdp/local", json={"path": str(tmp_path / "no.db")})
    assert resp.status_code == 404

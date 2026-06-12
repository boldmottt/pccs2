"""End-to-end CRUD tests for all REST routers on an in-memory SQLite database."""


def _create_project(client, name="테스트 프로젝트"):
    response = client.post("/api/projects/", json={"project_name": name, "customer": "ACME"})
    assert response.status_code == 201
    return response.json()


def _create_pattern(client, project_id, name="패턴 A"):
    response = client.post("/api/patterns/", json={
        "project_id": project_id,
        "pattern_name": name,
        "total_print_layers": 2,
        "target_base_color_sci": {"L": 50.0, "a": 10.0, "b": -5.0},
        "target_base_color_sce": {"L": 48.0, "a": 9.5, "b": -4.5},
    })
    assert response.status_code == 201
    return response.json()


def _create_round(client, pattern_id):
    response = client.post(f"/api/rounds/pattern/{pattern_id}", json={"operator": "kim"})
    assert response.status_code == 201
    return response.json()


def _create_sample(client, round_id, layers=None):
    response = client.post(f"/api/samples/round/{round_id}", json={
        "base_color_sci": {"L": 90.0, "a": 0.0, "b": 0.0},
        "base_color_sce": {"L": 88.0, "a": 0.0, "b": 0.0},
        "base_material": "ABS",
        "layers": layers or [],
    })
    assert response.status_code == 201
    return response.json()


def _create_ink(client, name="화이트", category="COLOR", sci=None, sce=None):
    response = client.post("/api/inks/", json={
        "ink_name": name,
        "ink_category": category,
        "solid_color_sci": sci,
        "solid_color_sce": sce,
    })
    assert response.status_code == 201
    return response.json()


class TestProjectsCRUD:
    def test_create_and_get(self, api_client):
        project = _create_project(api_client)
        assert project["project_name"] == "테스트 프로젝트"
        assert project["status"] == "IN_PROGRESS"

        fetched = api_client.get(f"/api/projects/{project['project_id']}")
        assert fetched.status_code == 200
        assert fetched.json()["customer"] == "ACME"

    def test_list(self, api_client):
        _create_project(api_client, "p1")
        _create_project(api_client, "p2")
        response = api_client.get("/api/projects/")
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_update(self, api_client):
        project = _create_project(api_client)
        response = api_client.put(
            f"/api/projects/{project['project_id']}",
            json={"status": "COMPLETED", "memo": "done"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "COMPLETED"
        assert body["memo"] == "done"
        assert body["project_name"] == "테스트 프로젝트"

    def test_delete(self, api_client):
        project = _create_project(api_client)
        assert api_client.delete(f"/api/projects/{project['project_id']}").status_code == 200
        assert api_client.get(f"/api/projects/{project['project_id']}").status_code == 404

    def test_not_found(self, api_client):
        assert api_client.get("/api/projects/nope").status_code == 404
        assert api_client.put("/api/projects/nope", json={"memo": "x"}).status_code == 404
        assert api_client.delete("/api/projects/nope").status_code == 404

    def test_invalid_status_rejected(self, api_client):
        response = api_client.post("/api/projects/", json={
            "project_name": "bad", "status": "NOT_A_STATUS",
        })
        assert response.status_code == 422


class TestPatternsCRUD:
    def test_create_requires_existing_project(self, api_client):
        response = api_client.post("/api/patterns/", json={
            "project_id": "missing", "pattern_name": "x", "total_print_layers": 1,
        })
        assert response.status_code == 404

    def test_create_get_update_delete(self, api_client):
        project = _create_project(api_client)
        pattern = _create_pattern(api_client, project["project_id"])
        assert pattern["status"] == "DEVELOPING"
        assert pattern["target_base_color_sci"]["L"] == 50.0

        updated = api_client.put(
            f"/api/patterns/{pattern['pattern_id']}",
            json={"status": "COMPLETED", "avg_delta_e": 1.2},
        )
        assert updated.status_code == 200
        assert updated.json()["avg_delta_e"] == 1.2

        assert api_client.delete(f"/api/patterns/{pattern['pattern_id']}").status_code == 200
        assert api_client.get(f"/api/patterns/{pattern['pattern_id']}").status_code == 404

    def test_list_filtered_by_project(self, api_client):
        p1 = _create_project(api_client, "p1")
        p2 = _create_project(api_client, "p2")
        _create_pattern(api_client, p1["project_id"], "pat1")
        _create_pattern(api_client, p2["project_id"], "pat2")

        response = api_client.get("/api/patterns/", params={"project_id": p1["project_id"]})
        body = response.json()
        assert len(body) == 1
        assert body[0]["pattern_name"] == "pat1"


class TestRoundsCRUD:
    def test_round_number_auto_increments(self, api_client):
        project = _create_project(api_client)
        pattern = _create_pattern(api_client, project["project_id"])
        r1 = _create_round(api_client, pattern["pattern_id"])
        r2 = _create_round(api_client, pattern["pattern_id"])
        assert r1["round_number"] == 1
        assert r2["round_number"] == 2

    def test_create_on_missing_pattern(self, api_client):
        assert api_client.post("/api/rounds/pattern/missing", json={}).status_code == 404

    def test_update_and_delete(self, api_client):
        project = _create_project(api_client)
        pattern = _create_pattern(api_client, project["project_id"])
        round_ = _create_round(api_client, pattern["pattern_id"])

        updated = api_client.put(f"/api/rounds/{round_['round_id']}", json={"operator": "lee"})
        assert updated.status_code == 200
        assert updated.json()["operator"] == "lee"

        assert api_client.delete(f"/api/rounds/{round_['round_id']}").status_code == 200
        assert api_client.get(f"/api/rounds/{round_['round_id']}").status_code == 404

    def test_list_filtered_by_pattern(self, api_client):
        project = _create_project(api_client)
        pattern = _create_pattern(api_client, project["project_id"])
        _create_round(api_client, pattern["pattern_id"])
        response = api_client.get("/api/rounds/", params={"pattern_id": pattern["pattern_id"]})
        assert len(response.json()) == 1


class TestSamplesCRUD:
    def _setup_round(self, api_client):
        project = _create_project(api_client)
        pattern = _create_pattern(api_client, project["project_id"])
        return _create_round(api_client, pattern["pattern_id"])

    def test_create_inherits_pattern_and_numbers(self, api_client):
        round_ = self._setup_round(api_client)
        s1 = _create_sample(api_client, round_["round_id"])
        s2 = _create_sample(api_client, round_["round_id"])
        assert s1["pattern_id"] == round_["pattern_id"]
        assert s1["sample_number"] == 1
        assert s2["sample_number"] == 2
        assert s1["success_flag"] == "PENDING"

    def test_create_with_layers(self, api_client):
        round_ = self._setup_round(api_client)
        sample = _create_sample(api_client, round_["round_id"], layers=[{
            "layer_number": 1,
            "ink_items": [{"ink_id": "white", "amount": 80.0}, {"ink_id": "red", "amount": 20.0}],
            "thinner_pct": 10.0,
        }])
        assert len(sample["layers"]) == 1
        assert sample["layers"][0]["ink_items"][0]["ink_id"] == "white"

    def test_layer_keeps_prediction_error_data(self, api_client):
        """예측 믹스색과 예측↔실측 ΔE가 레이어에 저장·반환된다 (엔진 보정용 데이터)."""
        round_ = self._setup_round(api_client)
        sample = _create_sample(api_client, round_["round_id"], layers=[{
            "layer_number": 1,
            "ink_items": [{"ink_id": "white", "amount": 80.0}],
            "print_color_sci": {"L": 71.0, "a": -2.0, "b": 5.5},
            "predicted_color_sci": {"L": 73.0, "a": -2.1, "b": 5.2},
            "prediction_error_delta_e": 2.04,
        }])
        layer = sample["layers"][0]
        assert layer["predicted_color_sci"] == {"L": 73.0, "a": -2.1, "b": 5.2}
        assert layer["prediction_error_delta_e"] == 2.04

    def test_create_on_missing_round(self, api_client):
        response = api_client.post("/api/samples/round/missing", json={
            "base_color_sci": {"L": 90, "a": 0, "b": 0},
            "base_color_sce": {"L": 88, "a": 0, "b": 0},
        })
        assert response.status_code == 404

    def test_update_and_delete(self, api_client):
        round_ = self._setup_round(api_client)
        sample = _create_sample(api_client, round_["round_id"])

        updated = api_client.put(f"/api/samples/{sample['sample_id']}", json={
            "final_delta_e": 0.8, "success_flag": "SUCCESS",
        })
        assert updated.status_code == 200
        assert updated.json()["success_flag"] == "SUCCESS"

        assert api_client.delete(f"/api/samples/{sample['sample_id']}").status_code == 200
        assert api_client.get(f"/api/samples/{sample['sample_id']}").status_code == 404

    def test_copy_layer(self, api_client):
        round_ = self._setup_round(api_client)
        source = _create_sample(api_client, round_["round_id"], layers=[{
            "layer_number": 1,
            "ink_items": [{"ink_id": "blue", "amount": 100.0}],
            "note": "원본 레이어",
        }])
        target = _create_sample(api_client, round_["round_id"])

        response = api_client.post(f"/api/samples/{target['sample_id']}/copy-layer", json={
            "source_sample_id": source["sample_id"],
            "source_layer_number": 1,
            "target_layer_number": 2,
        })
        assert response.status_code == 200
        layers = response.json()["layers"]
        assert len(layers) == 1
        assert layers[0]["layer_number"] == 2
        assert layers[0]["ink_items"][0]["ink_id"] == "blue"
        assert layers[0]["note"] == "원본 레이어"

    def test_copy_layer_replaces_existing(self, api_client):
        round_ = self._setup_round(api_client)
        source = _create_sample(api_client, round_["round_id"], layers=[{
            "layer_number": 1, "ink_items": [{"ink_id": "blue", "amount": 100.0}],
        }])
        target = _create_sample(api_client, round_["round_id"], layers=[{
            "layer_number": 1, "ink_items": [{"ink_id": "red", "amount": 100.0}],
        }])

        response = api_client.post(f"/api/samples/{target['sample_id']}/copy-layer", json={
            "source_sample_id": source["sample_id"],
            "source_layer_number": 1,
            "target_layer_number": 1,
        })
        layers = response.json()["layers"]
        assert len(layers) == 1
        assert layers[0]["ink_items"][0]["ink_id"] == "blue"

    def test_copy_layer_missing_source_layer(self, api_client):
        round_ = self._setup_round(api_client)
        source = _create_sample(api_client, round_["round_id"])
        target = _create_sample(api_client, round_["round_id"])
        response = api_client.post(f"/api/samples/{target['sample_id']}/copy-layer", json={
            "source_sample_id": source["sample_id"],
            "source_layer_number": 9,
            "target_layer_number": 1,
        })
        assert response.status_code == 404

    def test_list_filtered(self, api_client):
        round_ = self._setup_round(api_client)
        _create_sample(api_client, round_["round_id"])
        by_round = api_client.get("/api/samples/", params={"round_id": round_["round_id"]})
        assert len(by_round.json()) == 1
        by_pattern = api_client.get("/api/samples/", params={"pattern_id": round_["pattern_id"]})
        assert len(by_pattern.json()) == 1


class TestInksCRUD:
    def test_create_derives_gloss_fields(self, api_client):
        ink = _create_ink(
            api_client,
            sci={"L": 50.0, "a": 0.0, "b": 0.0},
            sce={"L": 47.0, "a": 0.0, "b": 0.0},
        )
        assert ink["delta_sci_sce"] == 3.0
        assert ink["gloss_index"] == 0.6  # 3.0 / 5.0
        assert ink["is_blend_ink"] is False

    def test_create_without_colors_has_no_derived_fields(self, api_client):
        ink = _create_ink(api_client)
        assert ink["delta_sci_sce"] is None
        assert ink["gloss_index"] is None

    def test_update_recomputes_derived_fields(self, api_client):
        ink = _create_ink(api_client)
        response = api_client.put(f"/api/inks/{ink['ink_id']}", json={
            "solid_color_sci": {"L": 60.0, "a": 0.0, "b": 0.0},
            "solid_color_sce": {"L": 56.0, "a": 0.0, "b": 0.0},
        })
        assert response.status_code == 200
        assert response.json()["delta_sci_sce"] == 4.0

    def test_list_filters(self, api_client):
        _create_ink(api_client, "컬러", "COLOR")
        _create_ink(api_client, "투명", "TRANSPARENT")
        response = api_client.get("/api/inks/", params={"category": "TRANSPARENT"})
        body = response.json()
        assert len(body) == 1
        assert body[0]["ink_name"] == "투명"

    def test_delete(self, api_client):
        ink = _create_ink(api_client)
        assert api_client.delete(f"/api/inks/{ink['ink_id']}").status_code == 200
        assert api_client.get(f"/api/inks/{ink['ink_id']}").status_code == 404

    def test_register_blend_on_existing_ink(self, api_client):
        ink = _create_ink(api_client)
        response = api_client.post(f"/api/inks/{ink['ink_id']}/register-blend", json={
            "ink_name": "배합 화이트",
            "blend_recipe": {
                "ink_items": [{"ink_id": "white", "amount": 80}, {"ink_id": "red", "amount": 20}],
                "solid_color_sci": {"L": 70.0, "a": 5.0, "b": 1.0},
            },
        })
        assert response.status_code == 200
        body = response.json()
        assert body["is_blend_ink"] is True
        assert body["ink_name"] == "배합 화이트"
        assert body["solid_color_sci"]["L"] == 70.0

    def test_register_blend_creates_new_ink(self, api_client):
        response = api_client.post("/api/inks/new-blend/register-blend", json={
            "ink_name": "새 배합 잉크",
            "ink_category": "COLOR",
            "blend_recipe": {"ink_items": [{"ink_id": "blue", "amount": 100}]},
        })
        assert response.status_code == 200
        body = response.json()
        assert body["is_blend_ink"] is True
        assert body["ink_name"] == "새 배합 잉크"

    def test_register_blend_new_without_name_fails(self, api_client):
        response = api_client.post("/api/inks/missing/register-blend", json={})
        assert response.status_code == 400


class TestMatchAPI:
    def _setup_pattern_and_inks(self, api_client):
        project = _create_project(api_client)
        pattern = _create_pattern(api_client, project["project_id"])
        _create_ink(api_client, "화이트", "COLOR",
                    sci={"L": 95.0, "a": 0.0, "b": 0.0}, sce={"L": 93.0, "a": 0.0, "b": 0.0})
        _create_ink(api_client, "블랙", "COLOR",
                    sci={"L": 5.0, "a": 0.0, "b": 0.0}, sce={"L": 4.0, "a": 0.0, "b": 0.0})
        _create_ink(api_client, "레드", "COLOR",
                    sci={"L": 45.0, "a": 60.0, "b": 30.0}, sce={"L": 43.0, "a": 58.0, "b": 29.0})
        return pattern

    def test_match_returns_ranked_recipes(self, api_client):
        pattern = self._setup_pattern_and_inks(api_client)
        response = api_client.post("/api/match/", json={
            "pattern_id": pattern["pattern_id"],
            "target_color": {"L": 50.0, "a": 0.0, "b": 0.0},
            "layer_number": 1,
        })
        assert response.status_code == 200
        body = response.json()
        recipes = body["recommended_recipes"]
        assert len(recipes) > 0
        assert recipes[0]["rank"] == 1
        # Recipes are sorted by predicted delta E
        deltas = [r["predicted_delta_E"] for r in recipes]
        assert deltas == sorted(deltas)
        # A gray target should be well matched by a white+black blend
        assert recipes[0]["predicted_delta_E"] < 5.0
        amounts = sum(item["amount"] for item in recipes[0]["recipe"])
        assert abs(amounts - 100.0) < 0.5

    def test_match_respects_exclusions(self, api_client):
        pattern = self._setup_pattern_and_inks(api_client)
        inks = api_client.get("/api/inks/").json()
        red_id = next(i["ink_id"] for i in inks if i["ink_name"] == "레드")
        response = api_client.post("/api/match/", json={
            "pattern_id": pattern["pattern_id"],
            "target_color": {"L": 45.0, "a": 60.0, "b": 30.0},
            "layer_number": 1,
            "exclude_inks": [red_id],
        })
        used = {
            item["ink_id"]
            for recipe in response.json()["recommended_recipes"]
            for item in recipe["recipe"]
        }
        assert red_id not in used

    def test_match_missing_pattern(self, api_client):
        response = api_client.post("/api/match/", json={
            "pattern_id": "missing",
            "target_color": {"L": 50.0, "a": 0.0, "b": 0.0},
            "layer_number": 1,
        })
        assert response.status_code == 404

    def test_match_without_inks_returns_empty(self, api_client):
        project = _create_project(api_client)
        pattern = _create_pattern(api_client, project["project_id"])
        response = api_client.post("/api/match/", json={
            "pattern_id": pattern["pattern_id"],
            "target_color": {"L": 50.0, "a": 0.0, "b": 0.0},
            "layer_number": 1,
        })
        assert response.status_code == 200
        assert response.json()["recommended_recipes"] == []


class TestCascadeDelete:
    def test_deleting_project_cascades(self, api_client):
        project = _create_project(api_client)
        pattern = _create_pattern(api_client, project["project_id"])
        round_ = _create_round(api_client, pattern["pattern_id"])
        sample = _create_sample(api_client, round_["round_id"])

        assert api_client.delete(f"/api/projects/{project['project_id']}").status_code == 200
        assert api_client.get(f"/api/patterns/{pattern['pattern_id']}").status_code == 404
        assert api_client.get(f"/api/rounds/{round_['round_id']}").status_code == 404
        assert api_client.get(f"/api/samples/{sample['sample_id']}").status_code == 404


def test_predict_with_ink_items_uses_ink_colors(api_client):
    """ink_id+amount 배합 예측 시 잉크 측색값이 실제로 반영되어야 한다 (회귀: 항상 흰색 예측)."""
    bk = api_client.post("/api/inks/", json={
        "ink_name": "BK predict", "ink_category": "COLOR",
        "solid_color_sci": {"L": 5.0, "a": 0.0, "b": 0.0},
    }).json()
    ye = api_client.post("/api/inks/", json={
        "ink_name": "YE predict", "ink_category": "COLOR",
        "solid_color_sci": {"L": 80.0, "a": 5.0, "b": 70.0},
    }).json()

    resp = api_client.post("/api/predict/", json={
        "recipe": {"layers": [{
            "layer_number": 1,
            "ink_items": [
                {"ink_id": bk["ink_id"], "amount": 20.0},
                {"ink_id": ye["ink_id"], "amount": 10.0},
            ],
        }]},
        "base_color": {"L": 80.0, "a": 0.0, "b": 2.0},
    })
    assert resp.status_code == 200
    body = resp.json()
    final = body["final_prediction"]
    # 검정 위주 배합: 베이스(L=80)보다 확실히 어두워야 한다
    assert final["L"] < 60.0
    # 노랑 잉크의 b+ 가 반영되어야 한다
    assert final["b"] > 2.0


def test_predict_without_resolvable_inks_falls_back(api_client):
    """측색값 없는 잉크만 있으면 K/S=0 (기존 동작 유지)."""
    ink = api_client.post("/api/inks/", json={
        "ink_name": "no-color predict", "ink_category": "COLOR",
    }).json()
    resp = api_client.post("/api/predict/", json={
        "recipe": {"layers": [{
            "layer_number": 1,
            "ink_items": [{"ink_id": ink["ink_id"], "amount": 10.0}],
        }]},
        "base_color": {"L": 80.0, "a": 0.0, "b": 2.0},
    })
    assert resp.status_code == 200


# ---------- Base Master ----------

def test_base_master_crud(api_client):
    created = api_client.post("/api/bases/", json={
        "base_code": "K-1116S",
        "base_name": "새틀 패턴 도장",
        "material": "Dd",
        "color_sci": {"L": 73.0, "a": -2.1, "b": 5.2},
        "color_sce": {"L": 71.5, "a": -2.0, "b": 5.0},
        "maker": "HT-77",
    })
    assert created.status_code == 201
    base = created.json()
    assert base["base_code"] == "K-1116S"

    listed = api_client.get("/api/bases/").json()
    assert any(b["base_id"] == base["base_id"] for b in listed)

    searched = api_client.get("/api/bases/", params={"q": "1116"}).json()
    assert len(searched) == 1

    got = api_client.get(f"/api/bases/{base['base_id']}").json()
    assert got["color_sci"]["L"] == 73.0

    updated = api_client.put(f"/api/bases/{base['base_id']}", json={"material": "ABS"})
    assert updated.json()["material"] == "ABS"

    deleted = api_client.delete(f"/api/bases/{base['base_id']}")
    assert deleted.status_code == 200
    assert api_client.get(f"/api/bases/{base['base_id']}").status_code == 404


def test_base_master_duplicate_code_conflict(api_client):
    api_client.post("/api/bases/", json={"base_code": "DUP-1"})
    dup = api_client.post("/api/bases/", json={"base_code": "DUP-1"})
    assert dup.status_code == 409

    other = api_client.post("/api/bases/", json={"base_code": "DUP-2"}).json()
    conflict = api_client.put(f"/api/bases/{other['base_id']}", json={"base_code": "DUP-1"})
    assert conflict.status_code == 409


class TestRecipeMatcherPhysics:
    """3-채널 K-M 혼합 모델의 정성 거동 검증 (감산혼합)."""

    @staticmethod
    def _blend(inks, ratios):
        from app.services.recipe_matcher import _ink_ks_channels, _predict_blend_color
        ks_list = [_ink_ks_channels(i) for i in inks]
        return _predict_blend_color(ks_list, ratios)

    def test_yellow_plus_blue_makes_green(self):
        """노랑+파랑 → 초록 (Lab 평균으로는 불가능한 감산혼합 거동)."""
        yellow = {"ink_id": "ye", "solid_color_sci": {"L": 85.0, "a": -5.0, "b": 80.0}}
        blue = {"ink_id": "bl", "solid_color_sci": {"L": 30.0, "a": 10.0, "b": -55.0}}
        mixed = self._blend([yellow, blue], (0.5, 0.5))
        # 초록 방향: a*가 두 원색 모두보다 음으로 이동
        assert mixed["a"] < -5.0

    def test_white_letdown_is_nonlinear(self):
        """진한 잉크에 흰색 소량은 명도를 거의 못 올린다 (white let-down)."""
        dark = {"ink_id": "bk", "solid_color_sci": {"L": 10.0, "a": 0.0, "b": 0.0}}
        white = {"ink_id": "wh", "solid_color_sci": {"L": 95.0, "a": 0.0, "b": 0.0}}
        ten_pct = self._blend([dark, white], (0.9, 0.1))
        half = self._blend([dark, white], (0.5, 0.5))
        # 선형이라면 10% 흰색에 L이 (95-10)*0.1=8.5 올라야 하지만 훨씬 작아야 함
        assert ten_pct["L"] - 10.0 < 5.0
        # 50%에서도 산술평균(52.5)보다 한참 어두워야 함
        assert half["L"] < 45.0

    def test_small_black_addition_is_potent(self):
        """밝은 잉크에 검정 10%는 산술평균보다 훨씬 어둡게 만든다."""
        white = {"ink_id": "wh", "solid_color_sci": {"L": 95.0, "a": 0.0, "b": 0.0}}
        black = {"ink_id": "bk", "solid_color_sci": {"L": 5.0, "a": 0.0, "b": 0.0}}
        mixed = self._blend([white, black], (0.9, 0.1))
        linear_expectation = 95.0 * 0.9 + 5.0 * 0.1  # 86
        assert mixed["L"] < linear_expectation - 15.0

    def test_pool_includes_lightness_extremes(self):
        """후보 풀에 최명·최암 잉크가 항상 포함된다 (명도 조정용)."""
        from app.services.recipe_matcher import _build_candidate_pool
        # 목표는 중간 채도 빨강 — 흰/검은 단색 ΔE 기준으로는 멀다
        target = {"L": 45.0, "a": 55.0, "b": 30.0}
        inks = [
            {"ink_id": f"red{i}", "ink_category": "COLOR",
             "solid_color_sci": {"L": 45.0 + i, "a": 55.0 - i, "b": 30.0}}
            for i in range(9)
        ]
        inks.append({"ink_id": "white", "ink_category": "COLOR",
                     "solid_color_sci": {"L": 96.0, "a": 0.0, "b": 0.0}})
        inks.append({"ink_id": "black", "ink_category": "COLOR",
                     "solid_color_sci": {"L": 4.0, "a": 0.0, "b": 0.0}})
        pool_ids = {ink["ink_id"] for ink in _build_candidate_pool(inks, target)}
        assert "white" in pool_ids
        assert "black" in pool_ids

    def test_recommendations_are_diverse(self):
        """상위 추천이 동일 조합의 변형으로 도배되지 않는다."""
        from app.services.recipe_matcher import recommend_recipes
        inks = [
            {"ink_id": "wh", "ink_category": "COLOR", "solid_color_sci": {"L": 95.0, "a": 0.0, "b": 0.0}},
            {"ink_id": "bk", "ink_category": "COLOR", "solid_color_sci": {"L": 5.0, "a": 0.0, "b": 0.0}},
            {"ink_id": "rd", "ink_category": "COLOR", "solid_color_sci": {"L": 45.0, "a": 60.0, "b": 30.0}},
            {"ink_id": "ye", "ink_category": "COLOR", "solid_color_sci": {"L": 85.0, "a": -5.0, "b": 80.0}},
            {"ink_id": "bl", "ink_category": "COLOR", "solid_color_sci": {"L": 30.0, "a": 10.0, "b": -55.0}},
        ]
        recipes = recommend_recipes({"L": 50.0, "a": 10.0, "b": 10.0}, inks, top_n=3)
        assert len(recipes) >= 2
        sets = [frozenset(i["ink_id"] for i in r["recipe"]) for r in recipes]
        # 1·2위가 완전히 같은 잉크 집합이면 다양성 실패
        assert sets[0] != sets[1]
        # 비율 합은 100
        for r in recipes:
            assert abs(sum(i["amount"] for i in r["recipe"]) - 100.0) < 0.5


class TestPlatesAPI:
    def _setup_pattern(self, api_client):
        project = _create_project(api_client)
        return _create_pattern(api_client, project["project_id"])

    def test_plate_crud_and_hierarchy(self, api_client):
        pattern = self._setup_pattern(api_client)
        created = api_client.post("/api/plates/", json={
            "pattern_id": pattern["pattern_id"],
            "plate_code": "26_027",
            "emboss_type": "새틀",
            "emboss_depth_um": 25,
        })
        assert created.status_code == 201
        plate = created.json()

        listed = api_client.get("/api/plates/", params={"pattern_id": pattern["pattern_id"]}).json()
        assert [p["plate_code"] for p in listed] == ["26_027"]

        updated = api_client.put(f"/api/plates/{plate['plate_id']}", json={"memo": "테스트"})
        assert updated.json()["memo"] == "테스트"

        deleted = api_client.delete(f"/api/plates/{plate['plate_id']}")
        assert deleted.status_code == 200
        assert api_client.get(f"/api/plates/{plate['plate_id']}").status_code == 404

    def test_plate_duplicate_code_in_pattern_conflict(self, api_client):
        pattern = self._setup_pattern(api_client)
        api_client.post("/api/plates/", json={"pattern_id": pattern["pattern_id"], "plate_code": "26_001"})
        dup = api_client.post("/api/plates/", json={"pattern_id": pattern["pattern_id"], "plate_code": "26_001"})
        assert dup.status_code == 409

    def test_plate_requires_existing_pattern(self, api_client):
        resp = api_client.post("/api/plates/", json={"pattern_id": "missing", "plate_code": "26_001"})
        assert resp.status_code == 404

    def test_blend_ink_binds_to_plate_and_released_on_delete(self, api_client):
        pattern = self._setup_pattern(api_client)
        plate = api_client.post("/api/plates/", json={
            "pattern_id": pattern["pattern_id"], "plate_code": "26_099",
        }).json()

        blend = api_client.post("/api/inks/new-plate-blend/register-blend", json={
            "ink_name": "동판 종속 배합",
            "plate_id": plate["plate_id"],
            "blend_recipe": {"ink_items": [{"ink_id": "x", "amount": 10}]},
        }).json()
        assert blend["plate_id"] == plate["plate_id"]

        # 동판 삭제 시 배합은 독립 배합으로 전환
        api_client.delete(f"/api/plates/{plate['plate_id']}")
        released = api_client.get(f"/api/inks/{blend['ink_id']}").json()
        assert released["plate_id"] is None

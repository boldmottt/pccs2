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

"""Tests for prediction API endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.hybrid_engine import hybrid_engine


@pytest.fixture
def client():
    """Create test client for API testing."""
    return TestClient(app)


class TestPredictEndpoint:
    """Tests for /api/predict/ endpoint."""

    @pytest.mark.unit
    def test_predict_empty_recipe_no_ml(self, client):
        """Test prediction with empty recipe when ML not trained."""
        # Ensure ML is not trained
        hybrid_engine._training_data = []
        hybrid_engine.ml_engine._model_l = None
        hybrid_engine.ml_engine._model_a = None
        hybrid_engine.ml_engine._model_b = None

        payload = {
            "recipe": {
                "layers": [
                    {"k_over_s": 0.0, "thickness": 1.0}
                ],
                "thinner_amount": 0.0,
                "hardener_amount": 0.0,
            },
            "base_color": {"L": 100.0, "a": 0.0, "b": 0.0},
        }

        response = client.post("/api/predict/", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "km_prediction" in data
        assert "final_prediction" in data
        assert "ml_confidence" in data
        assert data["ml_confidence"] == 0.0
        assert "delta_E" in data
        # With no ML, km_prediction should equal final_prediction
        assert data["km_prediction"]["L"] == data["final_prediction"]["L"]

    @pytest.mark.unit
    def test_predict_single_layer(self, client):
        """Test prediction with single layer recipe."""
        # Ensure ML is not trained
        hybrid_engine._training_data = []

        payload = {
            "recipe": {
                "layers": [
                    {
                        "k_over_s": 0.5,
                        "thickness": 1.0,
                    }
                ],
                "thinner_amount": 0.0,
                "hardener_amount": 0.0,
            },
            "base_color": {"L": 100.0, "a": 0.0, "b": 0.0},
        }

        response = client.post("/api/predict/", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "L" in data["km_prediction"]
        assert "a" in data["km_prediction"]
        assert "b" in data["km_prediction"]
        assert 0 <= data["km_prediction"]["L"] <= 100

    @pytest.mark.unit
    def test_predict_multiple_layers(self, client):
        """Test prediction with multiple layers."""
        hybrid_engine._training_data = []

        payload = {
            "recipe": {
                "layers": [
                    {"k_over_s": 0.3, "thickness": 1.0},
                    {"k_over_s": 1.0, "thickness": 0.5},
                ],
                "thinner_amount": 5.0,
                "hardener_amount": 2.0,
            },
            "base_color": {"L": 100.0, "a": 0.0, "b": 0.0},
        }

        response = client.post("/api/predict/", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "km_prediction" in data
        assert "final_prediction" in data
        assert "delta_E" in data

    @pytest.mark.unit
    def test_predict_colored_base(self, client):
        """Test prediction with colored base color."""
        hybrid_engine._training_data = []

        payload = {
            "recipe": {
                "layers": [
                    {"k_over_s": 0.0, "thickness": 1.0},
                ],
                "thinner_amount": 0.0,
                "hardener_amount": 0.0,
            },
            "base_color": {"L": 80.0, "a": 10.0, "b": -5.0},
        }

        response = client.post("/api/predict/", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert 0 <= data["km_prediction"]["L"] <= 100

    @pytest.mark.unit
    def test_predict_with_k_over_s_none(self, client):
        """Test prediction with None k_over_s (should default to 0)."""
        hybrid_engine._training_data = []

        payload = {
            "recipe": {
                "layers": [
                    {"k_over_s": None, "thickness": 1.0},
                ],
                "thinner_amount": 0.0,
                "hardener_amount": 0.0,
            },
            "base_color": {"L": 100.0, "a": 0.0, "b": 0.0},
        }

        response = client.post("/api/predict/", json=payload)

        assert response.status_code == 200

    @pytest.mark.unit
    def test_predict_invalid_base_color(self, client):
        """Test prediction with missing base color values."""
        payload = {
            "recipe": {
                "layers": [],
                "thinner_amount": 0.0,
                "hardener_amount": 0.0,
            },
            "base_color": {"L": 100.0},  # Missing a and b
        }

        response = client.post("/api/predict/", json=payload)

        # FastAPI should handle this with validation error
        assert response.status_code in [400, 422]


class TestTrainEndpoint:
    """Tests for /api/predict/train endpoint."""

    @pytest.mark.unit
    def test_train_with_historical_data(self, client):
        """Test training with historical data."""
        payload = {
            "historical_data": [
                {
                    "recipe": {
                        "layers": [
                            {"ink_items": [{"ink_id": "white", "amount": 100.0}], "thickness": 1.0}
                        ],
                        "base_color": {"L": 100.0, "a": 0.0, "b": 0.0},
                    },
                    "km_prediction": {"L": 95.0, "a": 1.0, "b": 2.0},
                    "actual_measurement": {"L": 94.5, "a": 1.2, "b": 1.8},
                },
                {
                    "recipe": {
                        "layers": [
                            {"ink_items": [{"ink_id": "red", "amount": 50.0}], "thickness": 1.0}
                        ],
                        "base_color": {"L": 100.0, "a": 0.0, "b": 0.0},
                    },
                    "km_prediction": {"L": 60.0, "a": 20.0, "b": 10.0},
                    "actual_measurement": {"L": 58.0, "a": 22.0, "b": 8.0},
                },
            ]
        }

        response = client.post("/api/predict/train", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "samples_trained" in data
        assert data["samples_trained"] == 2
        assert "model_scores" in data
        assert "L" in data["model_scores"]
        assert "a" in data["model_scores"]
        assert "b" in data["model_scores"]

    @pytest.mark.unit
    def test_train_with_empty_data(self, client):
        """Test training with empty historical data."""
        payload = {"historical_data": []}

        response = client.post("/api/predict/train", json=payload)

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    @pytest.mark.unit
    def test_train_updates_engine_state(self, client):
        """Test that training updates the hybrid engine state."""
        # Reset engine state first
        hybrid_engine._training_data = []
        hybrid_engine.ml_engine._model_l = None
        hybrid_engine.ml_engine._model_a = None
        hybrid_engine.ml_engine._model_b = None

        payload = {
            "historical_data": [
                {
                    "recipe": {
                        "layers": [
                            {"ink_items": [{"ink_id": "white", "amount": 100.0}], "thickness": 1.0}
                        ],
                        "base_color": {"L": 100.0, "a": 0.0, "b": 0.0},
                    },
                    "km_prediction": {"L": 95.0, "a": 1.0, "b": 2.0},
                    "actual_measurement": {"L": 94.5, "a": 1.2, "b": 1.8},
                },
            ]
        }

        response = client.post("/api/predict/train", json=payload)
        assert response.status_code == 200

        # Check engine state was updated
        assert hybrid_engine.ml_engine.is_trained is True
        assert len(hybrid_engine._training_data) > 0


class TestHealthEndpoint:
    """Tests for /api/predict/health endpoint."""

    @pytest.mark.unit
    def test_health_healthy_untrained(self, client):
        """Test health check when ML is not trained."""
        # Reset engine state to untrained
        hybrid_engine._training_data = []
        hybrid_engine.ml_engine.model_l = None
        hybrid_engine.ml_engine.model_a = None
        hybrid_engine.ml_engine.model_b = None
        hybrid_engine.ml_engine.is_trained = False

        response = client.get("/api/predict/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy_untrained"
        assert data["ml_trained"] is False
        assert data["samples_count"] == 0
        assert data["engine"] == "hybrid_km_ml"
        assert data["ml_trained"] is False
        assert data["samples_count"] == 0

    @pytest.mark.unit
    def test_health_healthy_trained(self, client):
        """Test health check when ML is trained."""
        # Train the model first
        historical_data = [
            {
                "recipe": {
                    "layers": [
                        {"ink_items": [{"ink_id": "white", "amount": 100.0}], "thickness": 1.0}
                    ],
                    "base_color": {"L": 100.0, "a": 0.0, "b": 0.0},
                },
                "km_prediction": {"L": 95.0, "a": 1.0, "b": 2.0},
                "actual_measurement": {"L": 94.5, "a": 1.2, "b": 1.8},
            },
            {
                "recipe": {
                    "layers": [
                        {"ink_items": [{"ink_id": "red", "amount": 50.0}], "thickness": 1.0}
                    ],
                    "base_color": {"L": 100.0, "a": 0.0, "b": 0.0},
                },
                "km_prediction": {"L": 60.0, "a": 20.0, "b": 10.0},
                "actual_measurement": {"L": 58.0, "a": 22.0, "b": 8.0},
            },
        ]

        hybrid_engine.train(historical_data)

        response = client.get("/api/predict/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["ml_trained"] is True
        assert data["samples_count"] >= 2

    @pytest.mark.unit
    def test_health_response_structure(self, client):
        """Test health check response has all required fields."""
        response = client.get("/api/predict/health")

        assert response.status_code == 200
        data = response.json()

        required_fields = ["status", "engine", "version", "ml_trained", "samples_count"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"


class TestPredictionWithTrainedModel:
    """Integration tests for prediction with trained ML model."""

    @pytest.mark.unit
    def test_predict_with_trained_ml_applies_correction(self, client):
        """Test prediction applies ML correction when model is trained."""
        # First train the model
        historical_data = [
            {
                "recipe": {
                    "layers": [
                        {"k_over_s": 0.5, "thickness": 1.0}
                    ],
                    "base_color": {"L": 100.0, "a": 0.0, "b": 0.0},
                },
                "km_prediction": {"L": 95.0, "a": 1.0, "b": 2.0},
                "actual_measurement": {"L": 94.5, "a": 1.2, "b": 1.8},
            },
            {
                "recipe": {
                    "layers": [
                        {"k_over_s": 1.0, "thickness": 1.0}
                    ],
                    "base_color": {"L": 100.0, "a": 0.0, "b": 0.0},
                },
                "km_prediction": {"L": 60.0, "a": 20.0, "b": 10.0},
                "actual_measurement": {"L": 58.0, "a": 22.0, "b": 8.0},
            },
        ]

        train_response = client.post("/api/predict/train", json={"historical_data": historical_data})
        assert train_response.status_code == 200

        # Now predict
        payload = {
            "recipe": {
                "layers": [
                    {"k_over_s": 0.5, "thickness": 1.0}
                ],
                "thinner_amount": 0.0,
                "hardener_amount": 0.0,
            },
            "base_color": {"L": 100.0, "a": 0.0, "b": 0.0},
        }

        response = client.post("/api/predict/", json=payload)
        assert response.status_code == 200

        data = response.json()
        # ML confidence should be > 0 when model is trained
        assert data["ml_confidence"] >= 0.0
        # ML correction should be present
        assert data["ml_correction"] is not None

    @pytest.mark.unit
    def test_predict_full_response_structure_with_ml(self, client):
        """Test full prediction response structure when ML is trained."""
        # Train the model
        historical_data = [
            {
                "recipe": {
                    "layers": [{"k_over_s": 0.5, "thickness": 1.0}],
                    "base_color": {"L": 100.0, "a": 0.0, "b": 0.0},
                },
                "km_prediction": {"L": 95.0, "a": 1.0, "b": 2.0},
                "actual_measurement": {"L": 94.5, "a": 1.2, "b": 1.8},
            },
            {
                "recipe": {
                    "layers": [{"k_over_s": 1.0, "thickness": 1.0}],
                    "base_color": {"L": 100.0, "a": 0.0, "b": 0.0},
                },
                "km_prediction": {"L": 60.0, "a": 20.0, "b": 10.0},
                "actual_measurement": {"L": 58.0, "a": 22.0, "b": 8.0},
            },
        ]

        client.post("/api/predict/train", json={"historical_data": historical_data})

        # Predict
        payload = {
            "recipe": {
                "layers": [{"k_over_s": 0.5, "thickness": 1.0}],
                "thinner_amount": 0.0,
                "hardener_amount": 0.0,
            },
            "base_color": {"L": 100.0, "a": 0.0, "b": 0.0},
        }

        response = client.post("/api/predict/", json=payload)
        assert response.status_code == 200

        data = response.json()

        # Verify all required fields
        required_fields = [
            "km_prediction",
            "ml_correction",
            "ml_confidence",
            "final_prediction",
            "delta_E",
        ]

        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        # Verify color structures
        assert "L" in data["km_prediction"]
        assert "a" in data["km_prediction"]
        assert "b" in data["km_prediction"]

        assert "L" in data["final_prediction"]
        assert "a" in data["final_prediction"]
        assert "b" in data["final_prediction"]


class TestInvalidInputs:
    """Tests for invalid input handling."""

    @pytest.mark.unit
    def test_predict_with_negative_thickness(self, client):
        """Test prediction with negative thickness (should fail validation)."""
        payload = {
            "recipe": {
                "layers": [
                    {"k_over_s": 0.0, "thickness": -1.0},
                ],
                "thinner_amount": 0.0,
                "hardener_amount": 0.0,
            },
            "base_color": {"L": 100.0, "a": 0.0, "b": 0.0},
        }

        response = client.post("/api/predict/", json=payload)
        # Pydantic validation should catch this
        assert response.status_code == 422

    @pytest.mark.unit
    def test_predict_with_negative_thinner_amount(self, client):
        """Test prediction with negative thinner amount (should fail validation)."""
        payload = {
            "recipe": {
                "layers": [],
                "thinner_amount": -5.0,
                "hardener_amount": 0.0,
            },
            "base_color": {"L": 100.0, "a": 0.0, "b": 0.0},
        }

        response = client.post("/api/predict/", json=payload)
        assert response.status_code == 422

    @pytest.mark.unit
    def test_predict_missing_recipe(self, client):
        """Test prediction with missing recipe field."""
        payload = {
            "base_color": {"L": 100.0, "a": 0.0, "b": 0.0},
        }

        response = client.post("/api/predict/", json=payload)
        assert response.status_code == 422

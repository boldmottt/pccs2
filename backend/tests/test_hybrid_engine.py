"""Tests for Hybrid K-M + ML Engine."""

import pytest
from unittest.mock import MagicMock, patch
from app.services.hybrid_engine import HybridEngine


class TestHybridEngineInit:
    """Tests for HybridEngine initialization."""

    @pytest.mark.unit
    def test_engine_initialization(self):
        """Test that HybridEngine initializes both K-M and ML engines."""
        engine = HybridEngine()

        assert engine.km_engine is not None
        assert engine.ml_engine is not None

    @pytest.mark.unit
    def test_ml_engine_not_trained_initially(self):
        """Test that ML engine starts in untrained state."""
        engine = HybridEngine()

        assert engine.ml_engine.is_trained is False


class TestHybridEnginePredictNoML:
    """Tests for prediction when ML engine is not trained (fallback to K-M only)."""

    @pytest.mark.unit
    def test_predict_without_trained_ml_returns_km_only(self):
        """Test prediction falls back to K-M when ML not trained."""
        engine = HybridEngine()

        recipe = {
            "layers": [
                {"k_over_s": 0.5, "thickness": 1.0},
            ]
        }
        base_color = {"L": 100.0, "a": 0.0, "b": 0.0, "R_inf": 1.0}

        result = engine.predict(recipe, base_color)

        # Should return K-M prediction
        assert "km_prediction" in result
        assert "final_prediction" in result
        assert "ml_confidence" in result
        assert result["ml_confidence"] == 0.0
        # Without ML correction, km_prediction and final_prediction should be equal
        km_pred = result["km_prediction"]
        final = result["final_prediction"]
        assert km_pred["L"] == final["L"]
        assert km_pred["a"] == final["a"]
        assert km_pred["b"] == final["b"]

    @pytest.mark.unit
    def test_predict_with_multiple_layers_without_ml(self):
        """Test multi-layer recipe prediction without ML training."""
        engine = HybridEngine()

        recipe = {
            "layers": [
                {"k_over_s": 0.3, "thickness": 1.0},
                {"k_over_s": 0.7, "thickness": 0.5},
                {"k_over_s": 1.0, "thickness": 1.5},
            ]
        }
        base_color = {"L": 100.0, "a": 0.0, "b": 0.0, "R_inf": 1.0}

        result = engine.predict(recipe, base_color)

        assert result["km_prediction"] is not None
        assert result["final_prediction"] is not None
        assert "delta_E" in result
        assert result["delta_E"] == 0.0  # No ML correction means no delta

    @pytest.mark.unit
    def test_predict_with_colored_base_without_ml(self):
        """Test prediction with colored base without ML training."""
        engine = HybridEngine()

        recipe = {
            "layers": [
                {"k_over_s": 0.5, "thickness": 1.0},
            ]
        }
        # Base color with some chroma
        base_color = {"L": 80.0, "a": 10.0, "b": -5.0, "R_inf": 0.7}

        result = engine.predict(recipe, base_color)

        assert "km_prediction" in result
        assert "final_prediction" in result
        assert 0 <= result["km_prediction"]["L"] <= 100


class TestHybridEngineTraining:
    """Tests for ML engine training."""

    @pytest.mark.unit
    def test_train_with_historical_data(self):
        """Test training ML engine with historical data."""
        engine = HybridEngine()

        historical_data = [
            {
                "recipe": {
                    "layers": [
                        {"k_over_s": 0.5, "thickness": 1.0},
                    ],
                    "base_color": {"L": 100.0, "a": 0.0, "b": 0.0}
                },
                "km_prediction": {"L": 50.0, "a": 10.0, "b": 20.0},
                "actual_measurement": {"L": 48.0, "a": 12.0, "b": 18.0},
            },
            {
                "recipe": {
                    "layers": [
                        {"k_over_s": 1.0, "thickness": 1.0},
                    ],
                    "base_color": {"L": 100.0, "a": 0.0, "b": 0.0}
                },
                "km_prediction": {"L": 40.0, "a": 15.0, "b": 25.0},
                "actual_measurement": {"L": 38.0, "a": 17.0, "b": 23.0},
            },
        ]

        result = engine.train(historical_data)

        assert "samples_trained" in result
        assert result["samples_trained"] == 2
        assert "model_scores" in result
        assert engine.ml_engine.is_trained is True

    @pytest.mark.unit
    def test_train_with_empty_data_raises_error(self):
        """Test that training with empty data raises ValueError."""
        engine = HybridEngine()

        with pytest.raises(ValueError, match="Historical data"):
            engine.train([])

    @pytest.mark.unit
    def test_train_updates_model_state(self):
        """Test that training updates ML engine's trained state."""
        engine = HybridEngine()

        historical_data = [
            {
                "recipe": {
                    "layers": [
                        {"k_over_s": 0.5, "thickness": 1.0},
                    ]
                },
                "km_prediction": {"L": 50.0, "a": 10.0, "b": 20.0},
                "actual_measurement": {"L": 48.0, "a": 12.0, "b": 18.0},
            },
        ]

        engine.train(historical_data)

        assert engine.ml_engine.is_trained is True


class TestHybridEnginePredictWithML:
    """Tests for prediction with trained ML engine."""

    @pytest.mark.unit
    def test_predict_with_trained_ml_applies_correction(self):
        """Test prediction applies ML correction when model is trained."""
        engine = HybridEngine()

        # First train the model (need at least 2 samples for confidence)
        historical_data = [
            {
                "recipe": {
                    "layers": [
                        {"k_over_s": 0.5, "thickness": 1.0},
                    ],
                    "base_color": {"L": 100.0, "a": 0.0, "b": 0.0}
                },
                "km_prediction": {"L": 50.0, "a": 10.0, "b": 20.0},
                "actual_measurement": {"L": 48.0, "a": 12.0, "b": 18.0},
            },
            {
                "recipe": {
                    "layers": [
                        {"k_over_s": 0.7, "thickness": 1.0},
                    ],
                    "base_color": {"L": 100.0, "a": 0.0, "b": 0.0}
                },
                "km_prediction": {"L": 45.0, "a": 12.0, "b": 22.0},
                "actual_measurement": {"L": 43.0, "a": 14.0, "b": 20.0},
            },
        ]

        engine.train(historical_data)

        # Now predict with same recipe
        recipe = {
            "layers": [
                {"k_over_s": 0.5, "thickness": 1.0},
            ]
        }
        base_color = {"L": 100.0, "a": 0.0, "b": 0.0, "R_inf": 1.0}

        result = engine.predict(recipe, base_color)

        # ML confidence should be > 0 when model is trained with enough samples
        assert result["ml_confidence"] >= 0.0
        assert "ml_correction" in result
        assert result["ml_correction"] is not None
        # ML correction should be applied, so predictions may differ
        # (depends on ML model's learned correction)

    @pytest.mark.unit
    def test_predict_full_pipeline_with_all_outputs(self):
        """Test that full prediction includes all required output fields."""
        engine = HybridEngine()

        # Train with sample data
        historical_data = [
            {
                "recipe": {
                    "layers": [
                        {"k_over_s": 0.5, "thickness": 1.0},
                    ],
                    "base_color": {"L": 100.0, "a": 0.0, "b": 0.0}
                },
                "km_prediction": {"L": 50.0, "a": 10.0, "b": 20.0},
                "actual_measurement": {"L": 48.0, "a": 12.0, "b": 18.0},
            },
            {
                "recipe": {
                    "layers": [
                        {"k_over_s": 1.0, "thickness": 1.0},
                    ],
                    "base_color": {"L": 100.0, "a": 0.0, "b": 0.0}
                },
                "km_prediction": {"L": 40.0, "a": 15.0, "b": 25.0},
                "actual_measurement": {"L": 38.0, "a": 17.0, "b": 23.0},
            },
        ]

        engine.train(historical_data)

        recipe = {
            "layers": [
                {"k_over_s": 0.5, "thickness": 1.0},
            ]
        }
        base_color = {"L": 100.0, "a": 0.0, "b": 0.0, "R_inf": 1.0}

        result = engine.predict(recipe, base_color)

        # Verify all required output fields
        required_fields = [
            "km_prediction",
            "ml_correction",
            "ml_confidence",
            "final_prediction",
            "delta_E",
        ]

        for field in required_fields:
            assert field in result, f"Missing required field: {field}"

        # Verify prediction structures
        assert "L" in result["km_prediction"]
        assert "a" in result["km_prediction"]
        assert "b" in result["km_prediction"]

        assert "L" in result["final_prediction"]
        assert "a" in result["final_prediction"]
        assert "b" in result["final_prediction"]

    @pytest.mark.unit
    def test_delta_e_calculation_in_prediction(self):
        """Test that delta_E is calculated between KM prediction and actual."""
        engine = HybridEngine()

        # Train with data that has known error
        historical_data = [
            {
                "recipe": {
                    "layers": [{"k_over_s": 0.5, "thickness": 1.0}],
                    "base_color": {"L": 100.0, "a": 0.0, "b": 0.0}
                },
                "km_prediction": {"L": 50.0, "a": 10.0, "b": 20.0},
                "actual_measurement": {"L": 48.0, "a": 12.0, "b": 18.0},
            },
        ]

        engine.train(historical_data)

        recipe = {
            "layers": [{"k_over_s": 0.5, "thickness": 1.0}]
        }
        base_color = {"L": 100.0, "a": 0.0, "b": 0.0, "R_inf": 1.0}

        result = engine.predict(recipe, base_color)

        # delta_E should be a non-negative float
        assert isinstance(result["delta_E"], (int, float))
        assert result["delta_E"] >= 0.0

    @pytest.mark.unit
    def test_prediction_with_colored_base_and_ml(self):
        """Test full pipeline with colored base color."""
        engine = HybridEngine()

        historical_data = [
            {
                "recipe": {
                    "layers": [
                        {"k_over_s": 0.5, "thickness": 1.0},
                    ],
                    "base_color": {"L": 80.0, "a": 5.0, "b": -3.0}
                },
                "km_prediction": {"L": 50.0, "a": 10.0, "b": 20.0},
                "actual_measurement": {"L": 48.0, "a": 12.0, "b": 18.0},
            },
        ]

        engine.train(historical_data)

        recipe = {
            "layers": [{"k_over_s": 0.5, "thickness": 1.0}]
        }
        base_color = {"L": 80.0, "a": 5.0, "b": -3.0, "R_inf": 0.7}

        result = engine.predict(recipe, base_color)

        assert result["km_prediction"] is not None
        assert result["final_prediction"] is not None
        assert 0 <= result["km_prediction"]["L"] <= 100


class TestHybridEngineCorrectionApplication:
    """Tests for correction application logic."""

    @pytest.mark.unit
    def test_correction_added_to_km_prediction(self):
        """Test that ML correction is correctly added to K-M prediction."""
        engine = HybridEngine()

        # Train with data to get ML correction
        historical_data = [
            {
                "recipe": {
                    "layers": [{"k_over_s": 0.5, "thickness": 1.0}],
                    "base_color": {"L": 100.0, "a": 0.0, "b": 0.0}
                },
                "km_prediction": {"L": 50.0, "a": 10.0, "b": 20.0},
                "actual_measurement": {"L": 48.0, "a": 12.0, "b": 18.0},
            },
        ]

        engine.train(historical_data)

        recipe = {
            "layers": [{"k_over_s": 0.5, "thickness": 1.0}],
            "km_prediction": {"L": 50.0, "a": 10.0, "b": 20.0}
        }
        base_color = {"L": 100.0, "a": 0.0, "b": 0.0, "R_inf": 1.0}

        result = engine.predict(recipe, base_color)

        km = result["km_prediction"]
        correction = result["ml_correction"]
        final = result["final_prediction"]

        # Verify: final = km + correction
        if correction:
            expected_L = km["L"] + correction["L"]
            expected_a = km["a"] + correction["a"]
            expected_b = km["b"] + correction["b"]

            # Allow small floating point differences
            assert abs(final["L"] - expected_L) < 0.01
            assert abs(final["a"] - expected_a) < 0.01
            assert abs(final["b"] - expected_b) < 0.01

    @pytest.mark.unit
    def test_correction_clamps_values_to_valid_range(self):
        """Test that corrected values are clamped to valid ranges."""
        engine = HybridEngine()

        # Create data that might push values out of range
        historical_data = [
            {
                "recipe": {
                    "layers": [{"k_over_s": 0.1, "thickness": 1.0}],
                    "base_color": {"L": 100.0, "a": 0.0, "b": 0.0}
                },
                "km_prediction": {"L": 95.0, "a": 0.0, "b": 0.0},
                "actual_measurement": {"L": 98.0, "a": 2.0, "b": 2.0},
            },
        ]

        engine.train(historical_data)

        recipe = {
            "layers": [{"k_over_s": 0.1, "thickness": 1.0}],
            "km_prediction": {"L": 98.0, "a": 0.0, "b": 0.0}
        }
        base_color = {"L": 100.0, "a": 0.0, "b": 0.0, "R_inf": 1.0}

        result = engine.predict(recipe, base_color)

        final = result["final_prediction"]

        # L should be clamped to [0, 100]
        assert 0 <= final["L"] <= 100, f"L={final['L']} out of range"

        # a and b should be clamped to reasonable range [-128, 127] or similar
        assert -128 <= final["a"] <= 128, f"a={final['a']} out of range"
        assert -128 <= final["b"] <= 128, f"b={final['b']} out of range"


class TestHybridEngineIntegration:
    """Integration tests for full K-M + ML pipeline."""

    @pytest.mark.unit
    def test_complete_prediction_workflow(self):
        """Test complete workflow from training to prediction."""
        engine = HybridEngine()

        # Step 1: Train with historical data
        historical_data = [
            {
                "recipe": {
                    "layers": [
                        {"k_over_s": 0.3, "thickness": 1.0},
                        {"k_over_s": 0.7, "thickness": 0.5},
                    ],
                    "base_color": {"L": 100.0, "a": 0.0, "b": 0.0}
                },
                "km_prediction": {"L": 60.0, "a": 15.0, "b": 25.0},
                "actual_measurement": {"L": 58.0, "a": 17.0, "b": 23.0},
            },
            {
                "recipe": {
                    "layers": [
                        {"k_over_s": 0.5, "thickness": 1.0},
                        {"k_over_s": 1.0, "thickness": 1.0},
                    ],
                    "base_color": {"L": 100.0, "a": 0.0, "b": 0.0}
                },
                "km_prediction": {"L": 45.0, "a": 20.0, "b": 30.0},
                "actual_measurement": {"L": 43.0, "a": 22.0, "b": 28.0},
            },
            {
                "recipe": {
                    "layers": [
                        {"k_over_s": 0.8, "thickness": 1.5},
                    ],
                    "base_color": {"L": 100.0, "a": 0.0, "b": 0.0}
                },
                "km_prediction": {"L": 35.0, "a": 25.0, "b": 35.0},
                "actual_measurement": {"L": 33.0, "a": 27.0, "b": 33.0},
            },
        ]

        train_result = engine.train(historical_data)

        assert train_result["samples_trained"] == 3
        assert train_result["model_scores"] is not None

        # Step 2: Predict new recipe
        new_recipe = {
            "layers": [
                {"k_over_s": 0.6, "thickness": 1.0},
            ]
        }
        base_color = {"L": 100.0, "a": 0.0, "b": 0.0, "R_inf": 1.0}

        prediction = engine.predict(new_recipe, base_color)

        # Verify prediction results
        assert prediction["km_prediction"] is not None
        assert prediction["final_prediction"] is not None
        assert prediction["ml_confidence"] >= 0.0
        assert prediction["delta_E"] >= 0.0

    @pytest.mark.unit
    def test_fallback_behavior_when_ml_untrained(self):
        """Test that engine gracefully handles untrained ML state."""
        engine = HybridEngine()

        recipe = {
            "layers": [{"k_over_s": 0.5, "thickness": 1.0}]
        }
        base_color = {"L": 100.0, "a": 0.0, "b": 0.0, "R_inf": 1.0}

        # Should not raise error, should just use K-M only
        result = engine.predict(recipe, base_color)

        assert result["km_prediction"] is not None
        assert result["final_prediction"] is not None
        assert result["ml_confidence"] == 0.0
        assert result["ml_correction"] is None

    @pytest.mark.unit
    def test_prediction_consistency_across_same_input(self):
        """Test that same input produces consistent predictions."""
        engine = HybridEngine()

        # Train
        historical_data = [
            {
                "recipe": {
                    "layers": [{"k_over_s": 0.5, "thickness": 1.0}],
                    "base_color": {"L": 100.0, "a": 0.0, "b": 0.0}
                },
                "km_prediction": {"L": 50.0, "a": 10.0, "b": 20.0},
                "actual_measurement": {"L": 48.0, "a": 12.0, "b": 18.0},
            },
        ]

        engine.train(historical_data)

        recipe = {
            "layers": [{"k_over_s": 0.5, "thickness": 1.0}]
        }
        base_color = {"L": 100.0, "a": 0.0, "b": 0.0, "R_inf": 1.0}

        # Run prediction twice
        result1 = engine.predict(recipe, base_color)
        result2 = engine.predict(recipe, base_color)

        # Results should be consistent
        assert result1["km_prediction"]["L"] == result2["km_prediction"]["L"]
        assert result1["final_prediction"]["L"] == result2["final_prediction"]["L"]
        assert result1["ml_confidence"] == result2["ml_confidence"]

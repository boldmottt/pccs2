"""Tests for ML Correction Engine."""

import math
import pytest
import numpy as np
from app.services.ml_correction_engine import MLCorrectionEngine


class TestMLCorrectionEngine:
    """Tests for MLCorrectionEngine class."""

    @pytest.mark.unit
    def test_init_untrained(self):
        """Test engine starts untrained."""
        engine = MLCorrectionEngine()
        assert engine.is_trained is False
        assert engine.model_l is None
        assert engine.model_a is None
        assert engine.model_b is None

    @pytest.mark.unit
    def test_predict_before_training_raises_error(self):
        """Test predict raises RuntimeError when model not trained."""
        engine = MLCorrectionEngine()
        recipe = {
            "layers": [
                {"ink_id": "red", "k_over_s": 0.5, "thickness": 1.0},
            ]
        }

        with pytest.raises(RuntimeError, match="Model not trained"):
            engine.predict(recipe)


class TestExtractFeatures:
    """Tests for _extract_features method."""

    @pytest.mark.unit
    def test_extract_features_single_layer(self):
        """Test feature extraction with single layer recipe."""
        engine = MLCorrectionEngine()
        recipe = {
            "layers": [
                {"ink_id": "red", "k_over_s": 0.5, "thickness": 1.0},
            ],
            "base_color": {"L": 100.0, "a": 0.0, "b": 0.0},
        }

        features = engine._extract_features(recipe)

        assert isinstance(features, np.ndarray)
        # Should have padded features: max 4 layers x 2 + 3 base = 11
        # First layer: k_over_s=0.5, thickness=1.0, then 3 padded layers (zeros), then base L,a,b
        assert len(features) == 11
        assert features[0] == pytest.approx(0.5, rel=1e-10)  # k_over_s
        assert features[1] == pytest.approx(1.0, rel=1e-10)  # thickness
        assert features[2] == 0.0  # padded
        assert features[3] == 0.0  # padded
        assert features[8] == pytest.approx(100.0, rel=1e-10)  # base L

    @pytest.mark.unit
    def test_extract_features_multiple_layers(self):
        """Test feature extraction with multiple layers."""
        engine = MLCorrectionEngine()
        recipe = {
            "layers": [
                {"ink_id": "red", "k_over_s": 0.5, "thickness": 1.0},
                {"ink_id": "yellow", "k_over_s": 0.3, "thickness": 0.5},
                {"ink_id": "cyan", "k_over_s": 0.7, "thickness": 1.5},
            ],
            "base_color": {"L": 100.0, "a": 0.0, "b": 0.0},
        }

        features = engine._extract_features(recipe)

        assert isinstance(features, np.ndarray)
        # Should have features for: 3 layers x 2 + 1 padded layer x 2 + 3 base = 11
        assert len(features) == 11
        assert features[0] == pytest.approx(0.5, rel=1e-10)  # layer 1 k_over_s
        assert features[2] == pytest.approx(0.3, rel=1e-10)  # layer 2 k_over_s
        assert features[4] == pytest.approx(0.7, rel=1e-10)  # layer 3 k_over_s
        assert features[10] == pytest.approx(0.0, rel=1e-10)  # base b

    @pytest.mark.unit
    def test_extract_features_empty_layers(self):
        """Test feature extraction with empty recipe."""
        engine = MLCorrectionEngine()
        recipe = {
            "layers": [],
            "base_color": {"L": 100.0, "a": 0.0, "b": 0.0},
        }

        features = engine._extract_features(recipe)

        assert isinstance(features, np.ndarray)
        # All layer features should be zero (padded), base color at end
        assert len(features) == 11
        assert all(features[i] == 0.0 for i in range(8))  # 4 padded layers x 2
        assert features[8] == pytest.approx(100.0, rel=1e-10)  # base L
        assert features[9] == pytest.approx(0.0, rel=1e-10)  # base a
        assert features[10] == pytest.approx(0.0, rel=1e-10)  # base b

    @pytest.mark.unit
    def test_extract_features_with_dilution(self):
        """Test feature extraction includes dilution factors."""
        engine = MLCorrectionEngine()
        recipe = {
            "layers": [
                {"ink_id": "red", "k_over_s": 0.5, "thickness": 1.0, "dilution": 0.8},
            ],
            "base_color": {"L": 100.0, "a": 0.0, "b": 0.0},
        }

        features = engine._extract_features(recipe)

        assert isinstance(features, np.ndarray)
        # Dilution should modify K/S feature (multiply)
        assert features[0] == pytest.approx(0.5 * 0.8, rel=1e-10)


class TestPrepareTrainingData:
    """Tests for _prepare_training_data method."""

    @pytest.mark.unit
    def test_prepare_training_data_single_sample(self):
        """Test training data preparation with single sample."""
        engine = MLCorrectionEngine()
        historical_data = [
            {
                "recipe": {
                    "layers": [{"ink_id": "red", "k_over_s": 0.5, "thickness": 1.0}],
                    "base_color": {"L": 100.0, "a": 0.0, "b": 0.0},
                },
                "km_prediction": {"L": 50.0, "a": 10.0, "b": 20.0},
                "actual_measurement": {"L": 48.0, "a": 12.0, "b": 18.0},
            }
        ]

        X, y = engine._prepare_training_data(historical_data)

        assert isinstance(X, np.ndarray)
        assert isinstance(y, np.ndarray)
        assert X.shape[0] == 1  # 1 sample
        assert y.shape[0] == 1  # 1 sample
        # y should be correction vector: (actual - km) for L, a, b
        assert y[0, 0] == pytest.approx(-2.0, rel=1e-10)  # 48 - 50
        assert y[0, 1] == pytest.approx(2.0, rel=1e-10)   # 12 - 10
        assert y[0, 2] == pytest.approx(-2.0, rel=1e-10)  # 18 - 20

    @pytest.mark.unit
    def test_prepare_training_data_multiple_samples(self):
        """Test training data preparation with multiple samples."""
        engine = MLCorrectionEngine()
        historical_data = [
            {
                "recipe": {
                    "layers": [{"ink_id": "red", "k_over_s": 0.5, "thickness": 1.0}],
                    "base_color": {"L": 100.0, "a": 0.0, "b": 0.0},
                },
                "km_prediction": {"L": 50.0, "a": 10.0, "b": 20.0},
                "actual_measurement": {"L": 48.0, "a": 12.0, "b": 18.0},
            },
            {
                "recipe": {
                    "layers": [{"ink_id": "yellow", "k_over_s": 0.3, "thickness": 0.5}],
                    "base_color": {"L": 100.0, "a": 0.0, "b": 0.0},
                },
                "km_prediction": {"L": 70.0, "a": 20.0, "b": 30.0},
                "actual_measurement": {"L": 68.0, "a": 22.0, "b": 28.0},
            },
        ]

        X, y = engine._prepare_training_data(historical_data)

        assert isinstance(X, np.ndarray)
        assert isinstance(y, np.ndarray)
        assert X.shape[0] == 2  # 2 samples
        assert y.shape[0] == 2  # 2 samples
        assert y.shape[1] == 3  # correction for L, a, b

    @pytest.mark.unit
    def test_prepare_training_data_empty_data_raises_error(self):
        """Test that empty historical data raises error."""
        engine = MLCorrectionEngine()
        historical_data = []

        with pytest.raises(ValueError, match="Historical data required"):
            engine._prepare_training_data(historical_data)

    @pytest.mark.unit
    def test_prepare_training_data_incomplete_sample_raises_error(self):
        """Test that incomplete sample raises error."""
        engine = MLCorrectionEngine()
        historical_data = [
            {
                "recipe": {"layers": [], "base_color": {"L": 100, "a": 0, "b": 0}},
                "km_prediction": {"L": 50.0, "a": 10.0, "b": 20.0},
                # Missing actual_measurement
            }
        ]

        with pytest.raises(ValueError, match="Missing required field"):
            engine._prepare_training_data(historical_data)


class TestTrain:
    """Tests for train method."""

    @pytest.mark.unit
    def test_train_successful(self):
        """Test successful model training."""
        engine = MLCorrectionEngine()
        historical_data = [
            {
                "recipe": {
                    "layers": [{"ink_id": "red", "k_over_s": 0.5, "thickness": 1.0}],
                    "base_color": {"L": 100.0, "a": 0.0, "b": 0.0},
                },
                "km_prediction": {"L": 50.0, "a": 10.0, "b": 20.0},
                "actual_measurement": {"L": 48.0, "a": 12.0, "b": 18.0},
            },
            {
                "recipe": {
                    "layers": [{"ink_id": "yellow", "k_over_s": 0.3, "thickness": 0.5}],
                    "base_color": {"L": 100.0, "a": 0.0, "b": 0.0},
                },
                "km_prediction": {"L": 70.0, "a": 20.0, "b": 30.0},
                "actual_measurement": {"L": 68.0, "a": 22.0, "b": 28.0},
            },
            {
                "recipe": {
                    "layers": [{"ink_id": "cyan", "k_over_s": 0.7, "thickness": 1.5}],
                    "base_color": {"L": 100.0, "a": 0.0, "b": 0.0},
                },
                "km_prediction": {"L": 40.0, "a": 5.0, "b": 15.0},
                "actual_measurement": {"L": 38.0, "a": 7.0, "b": 13.0},
            },
        ]

        engine.train(historical_data)

        assert engine.is_trained is True
        assert engine.model_l is not None
        assert engine.model_a is not None
        assert engine.model_b is not None

    @pytest.mark.unit
    def test_train_empty_data_raises_error(self):
        """Test that training with empty data raises error."""
        engine = MLCorrectionEngine()
        historical_data = []

        with pytest.raises(ValueError, match="Historical data required"):
            engine.train(historical_data)

    @pytest.mark.unit
    def test_train_multiple_times(self):
        """Test retraining overwrites previous model."""
        engine = MLCorrectionEngine()
        historical_data_1 = [
            {
                "recipe": {
                    "layers": [{"ink_id": "red", "k_over_s": 0.5, "thickness": 1.0}],
                    "base_color": {"L": 100.0, "a": 0.0, "b": 0.0},
                },
                "km_prediction": {"L": 50.0, "a": 10.0, "b": 20.0},
                "actual_measurement": {"L": 48.0, "a": 12.0, "b": 18.0},
            }
        ]

        engine.train(historical_data_1)
        assert engine.is_trained is True

        # Retrain with different data
        historical_data_2 = [
            {
                "recipe": {
                    "layers": [{"ink_id": "yellow", "k_over_s": 0.3, "thickness": 0.5}],
                    "base_color": {"L": 100.0, "a": 0.0, "b": 0.0},
                },
                "km_prediction": {"L": 70.0, "a": 20.0, "b": 30.0},
                "actual_measurement": {"L": 68.0, "a": 22.0, "b": 28.0},
            }
        ]

        engine.train(historical_data_2)
        assert engine.is_trained is True


class TestGetConfidence:
    """Tests for _get_confidence method."""

    @pytest.mark.unit
    def test_confidence_untrained(self):
        """Test confidence returns 0.0 when untrained."""
        engine = MLCorrectionEngine()
        confidence = engine._get_confidence()
        assert confidence == 0.0

    @pytest.mark.unit
    def test_confidence_trained(self):
        """Test confidence calculation after training."""
        engine = MLCorrectionEngine()
        historical_data = [
            {
                "recipe": {
                    "layers": [{"ink_id": "red", "k_over_s": 0.5, "thickness": 1.0}],
                    "base_color": {"L": 100.0, "a": 0.0, "b": 0.0},
                },
                "km_prediction": {"L": 50.0, "a": 10.0, "b": 20.0},
                "actual_measurement": {"L": 48.0, "a": 12.0, "b": 18.0},
            },
            {
                "recipe": {
                    "layers": [{"ink_id": "yellow", "k_over_s": 0.3, "thickness": 0.5}],
                    "base_color": {"L": 100.0, "a": 0.0, "b": 0.0},
                },
                "km_prediction": {"L": 70.0, "a": 20.0, "b": 30.0},
                "actual_measurement": {"L": 68.0, "a": 22.0, "b": 28.0},
            },
            {
                "recipe": {
                    "layers": [{"ink_id": "cyan", "k_over_s": 0.7, "thickness": 1.5}],
                    "base_color": {"L": 100.0, "a": 0.0, "b": 0.0},
                },
                "km_prediction": {"L": 40.0, "a": 5.0, "b": 15.0},
                "actual_measurement": {"L": 38.0, "a": 7.0, "b": 13.0},
            },
        ]

        engine.train(historical_data)
        confidence = engine._get_confidence()

        # Confidence should be a valid number between 0 and 1
        assert isinstance(confidence, float)
        assert not (confidence != confidence), "Confidence should not be NaN"
        assert confidence >= 0.0  # May be 0 if model overfits or has issues


class TestPredictAfterTraining:
    """Tests for predict method after training."""

    @pytest.mark.unit
    def test_predict_returns_correction(self):
        """Test prediction returns correction dict."""
        engine = MLCorrectionEngine()
        historical_data = [
            {
                "recipe": {
                    "layers": [{"ink_id": "red", "k_over_s": 0.5, "thickness": 1.0}],
                    "base_color": {"L": 100.0, "a": 0.0, "b": 0.0},
                },
                "km_prediction": {"L": 50.0, "a": 10.0, "b": 20.0},
                "actual_measurement": {"L": 48.0, "a": 12.0, "b": 18.0},
            },
        ]

        engine.train(historical_data)
        recipe = {
            "layers": [{"ink_id": "red", "k_over_s": 0.5, "thickness": 1.0}],
            "base_color": {"L": 100.0, "a": 0.0, "b": 0.0},
        }

        result = engine.predict(recipe)

        assert "correction" in result
        assert "confidence" in result
        assert isinstance(result["correction"], dict)
        assert isinstance(result["confidence"], float)

    @pytest.mark.unit
    def test_predict_correction_structure(self):
        """Test correction dict has L, a, b keys."""
        engine = MLCorrectionEngine()
        historical_data = [
            {
                "recipe": {
                    "layers": [{"ink_id": "red", "k_over_s": 0.5, "thickness": 1.0}],
                    "base_color": {"L": 100.0, "a": 0.0, "b": 0.0},
                },
                "km_prediction": {"L": 50.0, "a": 10.0, "b": 20.0},
                "actual_measurement": {"L": 48.0, "a": 12.0, "b": 18.0},
            },
        ]

        engine.train(historical_data)
        recipe = {
            "layers": [{"ink_id": "red", "k_over_s": 0.5, "thickness": 1.0}],
            "base_color": {"L": 100.0, "a": 0.0, "b": 0.0},
        }

        result = engine.predict(recipe)

        correction = result["correction"]
        assert "L" in correction
        assert "a" in correction
        assert "b" in correction

    @pytest.mark.unit
    def test_predict_full_prediction(self):
        """Test prediction returns full corrected color."""
        engine = MLCorrectionEngine()
        historical_data = [
            {
                "recipe": {
                    "layers": [{"ink_id": "red", "k_over_s": 0.5, "thickness": 1.0}],
                    "base_color": {"L": 100.0, "a": 0.0, "b": 0.0},
                },
                "km_prediction": {"L": 50.0, "a": 10.0, "b": 20.0},
                "actual_measurement": {"L": 48.0, "a": 12.0, "b": 18.0},
            },
        ]

        engine.train(historical_data)
        recipe = {
            "layers": [{"ink_id": "red", "k_over_s": 0.5, "thickness": 1.0}],
            "base_color": {"L": 100.0, "a": 0.0, "b": 0.0},
        }

        result = engine.predict(recipe)

        # Corrected color should be km_prediction + correction
        expected_L = 50.0 + result["correction"]["L"]
        expected_a = 10.0 + result["correction"]["a"]
        expected_b = 20.0 + result["correction"]["b"]

        assert "predicted_L" in result
        assert "predicted_a" in result
        assert "predicted_b" in result
        assert result["predicted_L"] == expected_L
        assert result["predicted_a"] == expected_a
        assert result["predicted_b"] == expected_b

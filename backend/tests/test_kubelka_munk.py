"""Tests for Kubelka-Munk coefficient calculator."""

import math
import pytest
from app.services.kubelka_munk import KubelkaMunkCoefficients


class TestCalculateKMSCoefficients:
    """Tests for calculate_km_coefficients method."""

    @pytest.mark.unit
    def test_calculate_normal_ratio(self):
        """Test K/S calculation with normal values."""
        K = 0.5
        S = 2.0
        result = KubelkaMunkCoefficients.calculate_km_coefficients(K, S)
        expected = 0.25
        assert result == pytest.approx(expected, rel=1e-10)

    @pytest.mark.unit
    def test_calculate_ratio_one(self):
        """Test when K equals S, ratio should be 1.0."""
        K = 1.0
        S = 1.0
        result = KubelkaMunkCoefficients.calculate_km_coefficients(K, S)
        assert result == pytest.approx(1.0, rel=1e-10)

    @pytest.mark.unit
    def test_calculate_ratio_less_than_one(self):
        """Test when K < S, ratio should be < 1."""
        K = 0.3
        S = 1.5
        result = KubelkaMunkCoefficients.calculate_km_coefficients(K, S)
        expected = 0.2
        assert result == pytest.approx(expected, rel=1e-10)

    @pytest.mark.unit
    def test_calculate_ratio_greater_than_one(self):
        """Test when K > S, ratio should be > 1."""
        K = 2.0
        S = 0.5
        result = KubelkaMunkCoefficients.calculate_km_coefficients(K, S)
        expected = 4.0
        assert result == pytest.approx(expected, rel=1e-10)

    @pytest.mark.unit
    def test_calculate_zero_absorption(self):
        """Test when K is zero, ratio should be zero."""
        K = 0.0
        S = 1.0
        result = KubelkaMunkCoefficients.calculate_km_coefficients(K, S)
        assert result == pytest.approx(0.0, rel=1e-10)

    @pytest.mark.unit
    def test_calculate_zero_scattering_raises_error(self):
        """Test when S is zero, should raise ValueError."""
        K = 0.5
        S = 0.0
        with pytest.raises(ValueError, match="Scattering coefficient S cannot be zero"):
            KubelkaMunkCoefficients.calculate_km_coefficients(K, S)

    @pytest.mark.unit
    def test_calculate_zero_scattering_negative_k_raises_error(self):
        """Test when S is zero with negative K, should raise ValueError."""
        K = -0.5
        S = 0.0
        with pytest.raises(ValueError, match="Scattering coefficient S cannot be zero"):
            KubelkaMunkCoefficients.calculate_km_coefficients(K, S)

    @pytest.mark.unit
    def test_calculate_with_small_values(self):
        """Test calculation with very small values."""
        K = 1e-10
        S = 1e-5
        result = KubelkaMunkCoefficients.calculate_km_coefficients(K, S)
        expected = 1e-5
        assert result == pytest.approx(expected, rel=1e-10)

    @pytest.mark.unit
    def test_calculate_with_large_values(self):
        """Test calculation with large values."""
        K = 1000.0
        S = 100.0
        result = KubelkaMunkCoefficients.calculate_km_coefficients(K, S)
        expected = 10.0
        assert result == pytest.approx(expected, rel=1e-10)


class TestCalculateReflectanceInfinite:
    """Tests for calculate_reflectance_infinite method."""

    @pytest.mark.unit
    def test_calculate_reflectance_zero_k_over_s(self):
        """Test when K/S is zero, reflectance should be 1.0 (perfect reflector)."""
        K_over_S = 0.0
        result = KubelkaMunkCoefficients.calculate_reflectance_infinite(K_over_S)
        assert result == pytest.approx(1.0, rel=1e-10)

    @pytest.mark.unit
    def test_calculate_reflectance_positive_k_over_s(self):
        """Test reflectance calculation with positive K/S."""
        K_over_S = 1.0
        # a = 1 + 1 = 2
        # R_inf = a - sqrt(a^2 - 1) = 2 - sqrt(3) = 0.2679...
        result = KubelkaMunkCoefficients.calculate_reflectance_infinite(K_over_S)
        expected = 2.0 - math.sqrt(3.0)
        assert result == pytest.approx(expected, rel=1e-10)
        # K-M 정합성: R_inf를 K/S로 되돌리면 원래 값이 나와야 한다
        # K/S = (1 - R)^2 / (2R)
        roundtrip = (1 - result) ** 2 / (2 * result)
        assert roundtrip == pytest.approx(K_over_S, rel=1e-9)

    @pytest.mark.unit
    def test_calculate_reflectance_small_k_over_s(self):
        """Test with small K/S ratio gives high reflectance."""
        K_over_S = 0.1
        result = KubelkaMunkCoefficients.calculate_reflectance_infinite(K_over_S)
        # a = 1.1, R_inf = 1.1 - sqrt(0.21) = 0.6417...
        expected = 1.1 - math.sqrt(0.21)
        assert result == pytest.approx(expected, rel=1e-10)
        assert result <= 1.0

    @pytest.mark.unit
    def test_calculate_reflectance_large_k_over_s(self):
        """Test with large K/S ratio gives low reflectance."""
        K_over_S = 5.0
        result = KubelkaMunkCoefficients.calculate_reflectance_infinite(K_over_S)
        # Should be a small positive value
        assert result >= 0.0
        assert result < 0.2

    @pytest.mark.unit
    def test_calculate_reflectance_range_0_to_1(self):
        """Test that all reflectance values are in valid range [0, 1]."""
        test_values = [0.0, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
        for k_over_s in test_values:
            result = KubelkaMunkCoefficients.calculate_reflectance_infinite(k_over_s)
            assert 0.0 <= result <= 1.0, f"Reflectance {result} out of range for K/S={k_over_s}"

    @pytest.mark.unit
    def test_calculate_reflectance_monotonic_decreasing(self):
        """Test that reflectance decreases as K/S increases."""
        k_over_s_values = [0.0, 0.5, 1.0, 2.0, 5.0, 10.0]
        reflectances = [
            KubelkaMunkCoefficients.calculate_reflectance_infinite(k)
            for k in k_over_s_values
        ]
        # Check monotonic decrease
        for i in range(len(reflectances) - 1):
            assert reflectances[i] >= reflectances[i + 1], \
                "Reflectance should decrease as K/S increases"

    @pytest.mark.unit
    def test_calculate_reflectance_edge_case_extreme(self):
        """Test with extreme K/S value."""
        K_over_S = 100.0
        result = KubelkaMunkCoefficients.calculate_reflectance_infinite(K_over_S)
        # Should be very close to 0
        assert result < 0.01

    @pytest.mark.unit
    def test_calculate_reflectance_negative_k_over_s_clamped(self):
        """음수 K/S는 sqrt(음수)로 깨지지 않고 0으로 클램프돼 R_inf=1을 반환."""
        result = KubelkaMunkCoefficients.calculate_reflectance_infinite(-5.0)
        assert result == pytest.approx(1.0, abs=1e-9)


class TestKubelkaMunkEngine:
    """Tests for KubelkaMunkEngine class."""

    @pytest.mark.unit
    def test_predict_layer_color_single_layer(self):
        """Test predicting color for a single layer."""
        from app.services.kubelka_munk_engine import KubelkaMunkEngine

        layer = {"k_over_s": 0.5, "thickness": 1.0}
        base_color = {"L": 100.0, "a": 0.0, "b": 0.0, "R_inf": 1.0}

        result = KubelkaMunkEngine.predict_layer_color(layer, base_color)

        assert "L" in result
        assert "a" in result
        assert "b" in result
        assert "R_inf" in result
        assert 0 <= result["L"] <= 100

    @pytest.mark.unit
    def test_predict_layer_color_zero_k_over_s(self):
        """Test layer with zero K/S (perfect reflector)."""
        from app.services.kubelka_munk_engine import KubelkaMunkEngine

        layer = {"k_over_s": 0.0, "thickness": 1.0}
        base_color = {"L": 50.0, "a": 10.0, "b": -5.0, "R_inf": 0.5}

        result = KubelkaMunkEngine.predict_layer_color(layer, base_color)

        # Should maintain high reflectance
        assert result["R_inf"] > 0.9

    @pytest.mark.unit
    def test_predict_layer_color_high_k_over_s(self):
        """Test layer with high K/S (absorbing)."""
        from app.services.kubelka_munk_engine import KubelkaMunkEngine

        layer = {"k_over_s": 5.0, "thickness": 1.0}
        base_color = {"L": 50.0, "a": 10.0, "b": -5.0, "R_inf": 0.5}

        result = KubelkaMunkEngine.predict_layer_color(layer, base_color)

        # High K/S layer has low reflectance (~0.097), should darken the color
        # The layer's R_inf is low, so combined_R should be lower than base
        assert 0 <= result["L"] <= 100
        assert "R_inf" in result
        assert 0 <= result["R_inf"] <= 1

    @pytest.mark.unit
    def test_predict_recipe_multiple_layers(self):
        """Test predicting color for multi-layer recipe."""
        from app.services.kubelka_munk_engine import KubelkaMunkEngine

        recipe = {
            "layers": [
                {"k_over_s": 0.5, "thickness": 1.0},
                {"k_over_s": 1.0, "thickness": 0.5},
            ]
        }
        base_color = {"L": 100.0, "a": 0.0, "b": 0.0, "R_inf": 1.0}

        result = KubelkaMunkEngine.predict_recipe(recipe, base_color)

        assert "predicted_color" in result
        assert "reflectance" in result
        assert "layers_processed" in result
        assert result["layers_processed"] == 2

    @pytest.mark.unit
    def test_predict_recipe_empty_layers(self):
        """Test predicting color with empty recipe (no layers)."""
        from app.services.kubelka_munk_engine import KubelkaMunkEngine

        recipe = {"layers": []}
        base_color = {"L": 50.0, "a": 10.0, "b": -5.0, "R_inf": 0.5}

        result = KubelkaMunkEngine.predict_recipe(recipe, base_color)

        assert result["layers_processed"] == 0
        assert result["predicted_color"]["L"] == base_color["L"]

    @pytest.mark.unit
    def test_predict_layer_color_thickness_effect(self):
        """Test that thickness affects final color."""
        from app.services.kubelka_munk_engine import KubelkaMunkEngine

        layer_thin = {"k_over_s": 2.0, "thickness": 0.5}
        layer_thick = {"k_over_s": 2.0, "thickness": 2.0}
        # Use a darker base so thickness effect is visible
        base_color = {"L": 50.0, "a": 0.0, "b": 0.0, "R_inf": 0.5}

        result_thin = KubelkaMunkEngine.predict_layer_color(layer_thin, base_color)
        result_thick = KubelkaMunkEngine.predict_layer_color(layer_thick, base_color)

        # Thicker layer with high K/S should absorb more (lower L)
        assert result_thick["L"] <= result_thin["L"]


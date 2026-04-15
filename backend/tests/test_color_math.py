"""Tests for color math utilities."""
import pytest
from app.services.color_math import (
    calculate_delta_e_76,
    calculate_delta_e_sci_sce,
    calculate_gloss_index,
    calculate_opacity_index,
    calculate_weighted_average,
)


class TestCalculateDeltaE76:
    """Tests for CIE76 color difference calculation."""

    def test_identical_colors(self):
        """Delta E of identical colors should be 0."""
        color = {"L": 50, "a": 0, "b": 0}
        assert calculate_delta_e_76(color, color) == 0.0

    def test_simple_difference(self):
        """Simple test case: only L differs."""
        color1 = {"L": 50, "a": 0, "b": 0}
        color2 = {"L": 60, "a": 0, "b": 0}
        # Delta = sqrt((60-50)^2 + 0 + 0) = 10
        assert calculate_delta_e_76(color1, color2) == 10.0

    def test_three_axis_difference(self):
        """Test with differences in all three axes."""
        color1 = {"L": 50, "a": 0, "b": 0}
        color2 = {"L": 50, "a": 3, "b": 4}
        # Delta = sqrt(0 + 3^2 + 4^2) = sqrt(25) = 5
        assert abs(calculate_delta_e_76(color1, color2) - 5.0) < 0.001

    def test_negative_difference(self):
        """Test with negative a* and b* values."""
        color1 = {"L": 50, "a": 0, "b": 0}
        color2 = {"L": 50, "a": -3, "b": -4}
        # Delta = sqrt(0 + (-3)^2 + (-4)^2) = 5
        assert abs(calculate_delta_e_76(color1, color2) - 5.0) < 0.001

    def test_large_difference(self):
        """Test with maximum practical difference."""
        color1 = {"L": 0, "a": -128, "b": -128}
        color2 = {"L": 100, "a": 127, "b": 127}
        dl, da, db = 100, 255, 255
        expected = (dl**2 + da**2 + db**2) ** 0.5
        assert abs(calculate_delta_e_76(color1, color2) - expected) < 0.001


class TestCalculateDeltaESCI_SCE:
    """Tests for SCI-SCE delta calculation."""

    def test_identical_sci_sce(self):
        """When SCI and SCE are same, delta should be 0."""
        sci = {"L": 50, "a": 0, "b": 0}
        sce = {"L": 50, "a": 0, "b": 0}
        assert calculate_delta_e_sci_sce(sci, sce) == 0.0

    def test_different_sci_sce(self):
        """Calculate delta between different SCI/SCE values."""
        sci = {"L": 50, "a": 0, "b": 0}
        sce = {"L": 48, "a": -1, "b": 5}
        dl, da, db = 2, 1, -5
        expected = (dl**2 + da**2 + db**2) ** 0.5
        assert abs(calculate_delta_e_sci_sce(sci, sce) - expected) < 0.001


class TestCalculateGlossIndex:
    """Tests for gloss index calculation."""

    def test_exact_half(self):
        """Half of max_delta gives 0.5 gloss index."""
        assert calculate_gloss_index(2.5, 5.0) == 0.5

    def test_full_max(self):
        """Equal to max_delta gives 1.0 gloss index."""
        assert calculate_gloss_index(5.0, 5.0) == 1.0

    def test_exceeds_max(self):
        """Exceeding max_delta returns capped 1.0."""
        assert calculate_gloss_index(10.0, 5.0) == 1.0
        assert calculate_gloss_index(100.0, 5.0) == 1.0

    def test_zero(self):
        """Zero delta gives 0 gloss index."""
        assert calculate_gloss_index(0, 5.0) == 0.0

    def test_custom_max(self):
        """Custom max_delta works correctly."""
        assert calculate_gloss_index(2.5, 10.0) == 0.25


class TestCalculateOpacityIndex:
    """Tests for opacity index calculation."""

    def test_full_opacity(self):
        """Printed equals ink solid = full opacity."""
        ink_solid = {"L": 50, "a": 0, "b": 0}
        base = {"L": 100, "a": 0, "b": 0}
        printed = {"L": 50, "a": 0, "b": 0}
        # Delta(ink_solid, printed) = 0
        # Delta(ink_solid, base) = 50
        # opacity_index = 1 - (0/50) = 1.0
        assert calculate_opacity_index(ink_solid, base, printed) == 1.0

    def test_no_opacity(self):
        """Printed equals base = no opacity (transparent)."""
        ink_solid = {"L": 50, "a": 0, "b": 0}
        base = {"L": 100, "a": 0, "b": 0}
        printed = {"L": 100, "a": 0, "b": 0}
        # Delta(ink_solid, printed) = 50
        # Delta(ink_solid, base) = 50
        # opacity_index = 1 - (50/50) = 0.0
        assert calculate_opacity_index(ink_solid, base, printed) == 0.0

    def test_partial_opacity(self):
        """Halfway between ink and base."""
        ink_solid = {"L": 0, "a": 0, "b": 0}
        base = {"L": 100, "a": 0, "b": 0}
        printed = {"L": 50, "a": 0, "b": 0}
        # Delta(ink_solid, printed) = 50
        # Delta(ink_solid, base) = 100
        # opacity_index = 1 - (50/100) = 0.5
        assert calculate_opacity_index(ink_solid, base, printed) == 0.5

    def test_similar_colors(self):
        """When ink and base are similar, should return None."""
        ink_solid = {"L": 50, "a": 0, "b": 0}
        base = {"L": 50, "a": 0.1, "b": 0.1}
        printed = {"L": 50, "a": 0, "b": 0}
        # Delta(ink_solid, base) < 1.0
        result = calculate_opacity_index(ink_solid, base, printed)
        assert result is None


class TestCalculateWeightedAverage:
    """Tests for weighted color average calculation."""

    def test_equal_weights(self):
        """Two inks with equal weights."""
        colors = {
            "ink1": {"L": 50, "a": 0, "b": 0},
            "ink2": {"L": 100, "a": 0, "b": 0},
        }
        weights = {"ink1": 0.5, "ink2": 0.5}
        result = calculate_weighted_average(colors, weights)
        assert abs(result["L"] - 75.0) < 0.001
        assert result["a"] == 0
        assert result["b"] == 0

    def test_unequal_weights(self):
        """Two inks with unequal weights (2:1 ratio)."""
        colors = {
            "ink1": {"L": 50, "a": 0, "b": 0},
            "ink2": {"L": 100, "a": 0, "b": 0},
        }
        weights = {"ink1": 2/3, "ink2": 1/3}
        result = calculate_weighted_average(colors, weights)
        # L = (50 * 2/3 + 100 * 1/3) = 100/3 + 100/3 = 200/3 = 66.67
        assert abs(result["L"] - 66.67) < 0.01
        assert result["a"] == 0
        assert result["b"] == 0

    def test_three_inks(self):
        """Three inks with equal weights."""
        colors = {
            "ink1": {"L": 0, "a": 0, "b": 0},
            "ink2": {"L": 50, "a": 0, "b": 0},
            "ink3": {"L": 100, "a": 0, "b": 0},
        }
        weights = {"ink1": 1/3, "ink2": 1/3, "ink3": 1/3}
        result = calculate_weighted_average(colors, weights)
        assert abs(result["L"] - 50.0) < 0.001

    def test_with_a_and_b_axis(self):
        """Test with differences in a and b axes."""
        colors = {
            "red": {"L": 50, "a": 50, "b": 0},
            "blue": {"L": 50, "a": 0, "b": -50},
        }
        weights = {"red": 0.5, "blue": 0.5}
        result = calculate_weighted_average(colors, weights)
        assert abs(result["L"] - 50.0) < 0.001
        assert abs(result["a"] - 25.0) < 0.001
        assert abs(result["b"] - (-25.0)) < 0.001

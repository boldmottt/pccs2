"""Tests for blend input processing."""
import pytest
from app.services.blend_processor import BlendProcessor


class TestProcessBlendInputBasic:
    """Tests for basic blend processing without additives."""

    def test_single_ink(self):
        """Single ink input."""
        raw_components = [
            {"ink_id": "red", "amount": 100},
        ]
        result = BlendProcessor.process_blend_input(raw_components)

        assert result["color_component_sum"] == 100
        assert result["thinner_amount"] == 0
        assert result["dilution_factor"] == 1.0
        assert result["normalized_color_ratio"]["red"] == 1.0

    def test_multiple_inks(self):
        """Multiple inks with different amounts."""
        raw_components = [
            {"ink_id": "red", "amount": 30},
            {"ink_id": "yellow", "amount": 20},
            {"ink_id": "transparent", "amount": 50},
        ]
        result = BlendProcessor.process_blend_input(raw_components)

        assert result["color_component_sum"] == 100
        assert result["thinner_amount"] == 0
        assert result["dilution_factor"] == 1.0
        assert result["normalized_color_ratio"]["red"] == 0.3
        assert result["normalized_color_ratio"]["yellow"] == 0.2
        assert result["normalized_color_ratio"]["TRANSPARENT_GLOSS"] == 0.5

    def test_empty_input(self):
        """Empty input should return zero values."""
        raw_components = []
        result = BlendProcessor.process_blend_input(raw_components)

        assert result["color_component_sum"] == 0
        assert result["thinner_amount"] == 0
        assert result["dilution_factor"] == 1.0
        assert result["normalized_color_ratio"] == {}

    def test_zero_amount(self):
        """Ink with zero amount should be excluded."""
        raw_components = [
            {"ink_id": "red", "amount": 0},
            {"ink_id": "yellow", "amount": 100},
        ]
        result = BlendProcessor.process_blend_input(raw_components)

        assert result["color_component_sum"] == 100
        # Zero amount ink should still be in effective components but normalized to 0
        assert result["normalized_color_ratio"]["yellow"] == 1.0


class TestProcessBlendInputWithThinner:
    """Tests for blend processing with thinner."""

    def test_with_thinner(self):
        """Thinner should reduce dilution factor."""
        raw_components = [
            {"ink_id": "red", "amount": 30},
            {"ink_id": "yellow", "amount": 20},
        ]
        thinner_amount = 50

        result = BlendProcessor.process_blend_input(raw_components, thinner_amount=thinner_amount)

        assert result["color_component_sum"] == 50
        assert result["thinner_amount"] == 50
        assert result["dilution_factor"] == 0.5

    def test_no_thinner(self):
        """No thinner should give dilution factor of 1.0."""
        raw_components = [
            {"ink_id": "red", "amount": 100},
        ]
        result = BlendProcessor.process_blend_input(raw_components, thinner_amount=0)

        assert result["dilution_factor"] == 1.0

    def test_thinner_only(self):
        """Only thinner, no color components."""
        raw_components = []
        thinner_amount = 50

        result = BlendProcessor.process_blend_input(raw_components, thinner_amount=thinner_amount)

        assert result["color_component_sum"] == 0
        assert result["thinner_amount"] == 50
        # When color_component_sum is 0, dilution_factor defaults to 1.0
        assert result["dilution_factor"] == 1.0


class TestProcessBlendInputWithHardener:
    """Tests for blend processing with hardener."""

    def test_hardener_added_to_transparent_gloss(self):
        """Hardener should be added to transparent gloss."""
        raw_components = [
            {"ink_id": "red", "amount": 30},
            {"ink_id": "yellow", "amount": 20},
            {"ink_id": "HARDENER", "amount": 10},
        ]
        result = BlendProcessor.process_blend_input(raw_components)

        # Hardener should be added to transparent gloss
        assert result["effective_color_components"]["TRANSPARENT_GLOSS"] == 10
        assert result["color_component_sum"] == 60

    def test_hardener_with_existing_transparent(self):
        """Hardener should be added to existing transparent gloss."""
        raw_components = [
            {"ink_id": "red", "amount": 30},
            {"ink_id": "transparent", "amount": 50},
            {"ink_id": "HARDENER", "amount": 10},
        ]
        result = BlendProcessor.process_blend_input(raw_components)

        # Hardener should be added to transparent gloss
        assert result["effective_color_components"]["TRANSPARENT_GLOSS"] == 60
        assert result["color_component_sum"] == 90

    def test_custom_transparent_gloss_id(self):
        """Custom transparent gloss ID should work."""
        raw_components = [
            {"ink_id": "red", "amount": 30},
            {"ink_id": "HARDENER", "amount": 10},
        ]
        result = BlendProcessor.process_blend_input(
            raw_components,
            transparent_gloss_id="GLOSS_BASE"
        )

        assert result["effective_color_components"]["GLOSS_BASE"] == 10


class TestProcessBlendInputCombined:
    """Tests for combined thinner and hardener processing."""

    def test_with_both_thinner_and_hardener(self):
        """Both thinner and hardener in input."""
        raw_components = [
            {"ink_id": "red", "amount": 30},
            {"ink_id": "yellow", "amount": 20},
            {"ink_id": "HARDENER", "amount": 10},
        ]
        result = BlendProcessor.process_blend_input(
            raw_components,
            thinner_amount=40
        )

        # Color components: red(30) + yellow(20) + hardener→transparent(10) = 60
        assert result["color_component_sum"] == 60
        assert result["thinner_amount"] == 40
        # dilution_factor = 60 / (60 + 40) = 0.6
        assert result["dilution_factor"] == 0.6

    def test_normalize_ratio_with_hardener(self):
        """Normalized ratios should include hardener in transparent."""
        raw_components = [
            {"ink_id": "red", "amount": 30},
            {"ink_id": "yellow", "amount": 20},
            {"ink_id": "HARDENER", "amount": 10},
        ]
        result = BlendProcessor.process_blend_input(raw_components)

        # Total: 60, red: 30/60=0.5, yellow: 20/60=0.333, transparent: 10/60=0.167
        assert abs(result["normalized_color_ratio"]["red"] - 0.5) < 0.001
        assert abs(result["normalized_color_ratio"]["yellow"] - 0.3333) < 0.001
        assert abs(result["normalized_color_ratio"]["TRANSPARENT_GLOSS"] - 0.1667) < 0.001


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_very_small_amounts(self):
        """Very small amounts should still work."""
        raw_components = [
            {"ink_id": "red", "amount": 0.001},
            {"ink_id": "yellow", "amount": 0.002},
        ]
        result = BlendProcessor.process_blend_input(raw_components)

        assert result["color_component_sum"] == 0.003
        assert abs(result["normalized_color_ratio"]["red"] - 1/3) < 0.001
        assert abs(result["normalized_color_ratio"]["yellow"] - 2/3) < 0.001

    def test_very_large_amounts(self):
        """Very large amounts should work."""
        raw_components = [
            {"ink_id": "red", "amount": 1000000},
            {"ink_id": "yellow", "amount": 2000000},
        ]
        result = BlendProcessor.process_blend_input(raw_components)

        assert result["color_component_sum"] == 3000000
        assert result["normalized_color_ratio"]["red"] == 1/3
        assert result["normalized_color_ratio"]["yellow"] == 2/3

    def test_many_inks(self):
        """Many inks should all be processed."""
        raw_components = [
            {"ink_id": f"ink{i}", "amount": 10}
            for i in range(20)
        ]
        result = BlendProcessor.process_blend_input(raw_components)

        assert result["color_component_sum"] == 200
        for i in range(20):
            assert abs(result["normalized_color_ratio"][f"ink{i}"] - 0.05) < 0.001

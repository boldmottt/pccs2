from typing import List, Dict, Optional


class BlendProcessor:
    """Process blend input data"""

    @staticmethod
    def process_blend_input(
        raw_components: List[Dict],
        thinner_amount: Optional[float] = 0.0,
        hardener_amount: Optional[float] = 0.0,
        transparent_gloss_id: str = "TRANSPARENT_GLOSS"
    ) -> Dict:
        """
        Process blend input according to rules:
        1. Hardener → add to Transparent Gloss
        2. Thinner → exclude from color components
        3. Others → keep as is

        Args:
            raw_components: List of {ink_id, amount} dicts
            thinner_amount: Total thinner amount
            hardener_amount: Total hardener amount
            transparent_gloss_id: ID for transparent gloss ink

        Returns:
            Processed blend data with effective components, normalized ratios, dilution factor
        """
        effective_components = {}

        for comp in raw_components:
            ink_id = comp.get("ink_id")
            amount = comp.get("amount", 0)

            if ink_id == "THINNER":
                # Thinner is excluded
                pass
            elif ink_id == "HARDENER":
                # Hardener adds to Transparent Gloss
                current = effective_components.get(transparent_gloss_id, 0.0)
                effective_components[transparent_gloss_id] = current + amount
            else:
                # Others keep as is
                current = effective_components.get(ink_id, 0.0)
                effective_components[ink_id] = current + amount

        # Color component sum
        color_sum = sum(effective_components.values())

        # Normalize (sum = 1.0)
        normalized = {}
        if color_sum > 0:
            for ink_id, amount in effective_components.items():
                normalized[ink_id] = amount / color_sum

        # Dilution factor
        if thinner_amount and thinner_amount > 0:
            dilution_factor = color_sum / (color_sum + thinner_amount)
        else:
            dilution_factor = 1.0

        return {
            "effective_color_components": effective_components,
            "normalized_color_ratio": normalized,
            "color_component_sum": color_sum,
            "thinner_amount": thinner_amount,
            "dilution_factor": dilution_factor,
        }

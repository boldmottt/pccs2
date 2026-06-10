from typing import List, Dict, Optional


def calculate_blend_solid_color(
    layers: List[Dict],
    print_layers: int = 1,
    ink_master_data: Optional[Dict[str, Dict]] = None
) -> Dict[str, float]:
    """Calculate a blend ink's solid color as the amount-weighted average
    of its component master ink colors across the first ``print_layers`` layers.
    """
    total_weight: Dict[str, float] = {}
    total_layers = min(len(layers), print_layers)

    for i in range(total_layers):
        layer = layers[i]
        for ink_item in layer.get("ink_items", []):
            ink_id = ink_item["ink_id"]
            amount = ink_item["amount"]
            total_weight[ink_id] = total_weight.get(ink_id, 0) + amount

    if not total_weight:
        return {"L": 0, "a": 0, "b": 0}

    colors = {}
    weights = {}
    for ink_id, weight in total_weight.items():
        if ink_master_data and ink_id in ink_master_data:
            colors[ink_id] = ink_master_data[ink_id]
            weights[ink_id] = weight

    if not colors:
        return {"L": 0, "a": 0, "b": 0}

    total_w = sum(weights.values())
    return {
        channel: sum(colors[ink_id][channel] * weights[ink_id] for ink_id in weights) / total_w
        for channel in ("L", "a", "b")
    }


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
            elif ink_id.lower() == "transparent" or ink_id.lower() == "transparent_gloss":
                # Normalize transparent variants to transparent_gloss_id
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
        if color_sum > 0:
            dilution_factor = color_sum / (color_sum + thinner_amount)
        else:
            # When no color components, dilution factor defaults to 1.0
            dilution_factor = 1.0

        return {
            "effective_color_components": effective_components,
            "normalized_color_ratio": normalized,
            "color_component_sum": color_sum,
            "thinner_amount": thinner_amount,
            "dilution_factor": dilution_factor,
        }

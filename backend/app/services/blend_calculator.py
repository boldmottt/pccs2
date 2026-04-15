from typing import List, Dict, Optional


def calculate_blend_solid_color(
    layers: List[Dict],
    print_layers: int = 1,
    ink_master_data: Optional[Dict[str, Dict]] = None
) -> Dict[str, float]:
    """
    Calculate blend ink's solid color

    Args:
        layers: Layer data with ink_items
        print_layers: Number of layers to include (default: 1)
        ink_master_data: Dictionary of ink_id → {L, a, b} for master inks

    Returns:
        Blend solid color {L, a, b}
    """
    total_weight = {}
    total_layers = min(len(layers), print_layers)

    # Calculate total weight for each ink
    for i in range(total_layers):
        layer = layers[i]
        for ink_item in layer.get("ink_items", []):
            ink_id = ink_item["ink_id"]
            amount = ink_item["amount"]
            total_weight[ink_id] = total_weight.get(ink_id, 0) + amount

    if not total_weight:
        return {"L": 0, "a": 0, "b": 0}

    # Get colors from master data
    colors = {}
    weights = {}
    for ink_id, weight in total_weight.items():
        if ink_master_data and ink_id in ink_master_data:
            colors[ink_id] = ink_master_data[ink_id]
            weights[ink_id] = weight

    if not colors:
        return {"L": 0, "a": 0, "b": 0}

    # Calculate weighted average
    total_w = sum(weights.values())
    result = {}
    for channel in ["L", "a", "b"]:
        weighted_sum = sum(colors[ink_id][channel] * weights[ink_id] for ink_id in weights)
        result[channel] = weighted_sum / total_w

    return result

import math
from typing import Dict


def calculate_delta_e_76(color1: Dict[str, float], color2: Dict[str, float]) -> float:
    """Calculate ΔE using CIE76 formula"""
    dl = color1["L"] - color2["L"]
    da = color1["a"] - color2["a"]
    db = color1["b"] - color2["b"]
    return math.sqrt(dl**2 + da**2 + db**2)


def calculate_delta_e_sci_sce(sci: Dict[str, float], sce: Dict[str, float]) -> float:
    """Calculate ΔE between SCI and SCE"""
    return calculate_delta_e_76(sci, sce)


def lab_to_reflectance(color: Dict[str, float]) -> float:
    """Approximate diffuse reflectance (R_inf) from a CIE Lab color.

    Uses the inverse of the L* lightness function: L* -> Y/Yn, where the
    luminance factor Y/Yn serves as the reflectance approximation required
    by the Kubelka-Munk engine. Clamped to [0.001, 1.0] to keep the K-M
    adding-up formula numerically stable.
    """
    L = max(0.0, min(100.0, color.get("L", 100.0)))
    if L > 8.0:
        y = ((L + 16.0) / 116.0) ** 3
    else:
        y = L / 903.3
    return max(0.001, min(1.0, y))


def calculate_gloss_index(delta_sci_sce: float, max_delta: float = 5.0) -> float:
    """Calculate gloss index (0-1)"""
    return min(delta_sci_sce / max_delta, 1.0)


def calculate_opacity_index(
    ink_solid: Dict[str, float],
    base: Dict[str, float],
    printed: Dict[str, float]
) -> float:
    """
    Calculate opacity index
    opacity_index = 1 - (ΔE(ink_solid, printed) / ΔE(ink_solid, base))
    """
    delta_ink_printed = calculate_delta_e_76(ink_solid, printed)
    delta_ink_base = calculate_delta_e_76(ink_solid, base)

    if delta_ink_base < 1.0:
        return None  # Ink and base colors too similar

    return 1.0 - (delta_ink_printed / delta_ink_base)


def calculate_weighted_average(
    colors: Dict[str, Dict[str, float]],
    weights: Dict[str, float]
) -> Dict[str, float]:
    """Calculate weighted average of colors"""
    total_weight = sum(weights.values())

    result = {}
    for channel in ["L", "a", "b"]:
        weighted_sum = sum(
            colors[ink_id][channel] * weights[ink_id]
            for ink_id in weights
        )
        result[channel] = weighted_sum / total_weight

    return result

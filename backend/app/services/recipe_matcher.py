"""Recipe recommendation: search ink blends that best reproduce a target color."""

from itertools import combinations
from typing import Dict, List, Optional

from app.services.color_math import calculate_delta_e_76, calculate_weighted_average

# Categories that contribute color when blended
_BLENDABLE_CATEGORIES = {"COLOR", "TRANSPARENT", "EFFECT"}

# Candidate pool size: keep the closest single inks before combining,
# so the combination search stays tractable for large ink libraries.
_MAX_CANDIDATE_POOL = 8

# Mixing ratio grid resolution for the simplex search
_RATIO_STEP = 0.1

DEFAULT_THINNER_RATIO = 0.10


def _ratio_grids(n_components: int):
    """Yield mixing ratio tuples (summing to 1.0) on a coarse simplex grid."""
    steps = int(round(1.0 / _RATIO_STEP))
    if n_components == 1:
        yield (1.0,)
        return
    if n_components == 2:
        for i in range(1, steps):
            yield (i * _RATIO_STEP, 1.0 - i * _RATIO_STEP)
        return
    if n_components == 3:
        for i in range(1, steps - 1):
            for j in range(1, steps - i):
                k = steps - i - j
                if k >= 1:
                    yield (i * _RATIO_STEP, j * _RATIO_STEP, k * _RATIO_STEP)
        return
    # 4 components
    for i in range(1, steps - 2):
        for j in range(1, steps - i - 1):
            for k in range(1, steps - i - j):
                m = steps - i - j - k
                if m >= 1:
                    yield (i * _RATIO_STEP, j * _RATIO_STEP, k * _RATIO_STEP, m * _RATIO_STEP)


def _predict_blend_color(inks: List[Dict], ratios) -> Dict[str, float]:
    colors = {ink["ink_id"]: ink["solid_color_sci"] for ink in inks}
    weights = {ink["ink_id"]: ratio for ink, ratio in zip(inks, ratios)}
    return calculate_weighted_average(colors, weights)


def _confidence_from_delta_e(delta_e: float) -> float:
    """Map delta E to a 0-1 confidence score (dE 0 -> 1.0, dE >= 20 -> 0)."""
    return max(0.0, min(1.0, 1.0 - delta_e / 20.0))


def recommend_recipes(
    target_color: Dict[str, float],
    inks: List[Dict],
    exclude_inks: Optional[List[str]] = None,
    max_components: Optional[int] = None,
    top_n: int = 3,
) -> List[Dict]:
    """Search blends of master inks that minimize delta E against the target.

    Args:
        target_color: Target color {L, a, b}
        inks: Master inks as dicts with ink_id, ink_category, solid_color_sci
        exclude_inks: Ink IDs to exclude from recommendations
        max_components: Maximum number of inks per blend (1-4, default 3)
        top_n: Number of recipes to return

    Returns:
        Ranked recipe dicts: {rank, recipe: [{ink_id, amount}], suggested_thinner_ratio,
        predicted_color, predicted_delta_E, confidence_score}
    """
    excluded = set(exclude_inks or [])
    max_components = min(max(max_components or 3, 1), 4)

    candidates = [
        ink for ink in inks
        if ink.get("solid_color_sci")
        and ink.get("ink_category") in _BLENDABLE_CATEGORIES
        and ink["ink_id"] not in excluded
    ]
    if not candidates:
        return []

    # Narrow the pool to the inks closest to the target before combining
    candidates.sort(key=lambda ink: calculate_delta_e_76(ink["solid_color_sci"], target_color))
    pool = candidates[:_MAX_CANDIDATE_POOL]

    # Best result per ink-combination, keyed by sorted ink ids
    best_per_combo: Dict[tuple, Dict] = {}
    for size in range(1, min(max_components, len(pool)) + 1):
        for combo in combinations(pool, size):
            key = tuple(sorted(ink["ink_id"] for ink in combo))
            for ratios in _ratio_grids(size):
                predicted = _predict_blend_color(list(combo), ratios)
                delta_e = calculate_delta_e_76(predicted, target_color)
                current = best_per_combo.get(key)
                if current is None or delta_e < current["predicted_delta_E"]:
                    best_per_combo[key] = {
                        "recipe": [
                            {"ink_id": ink["ink_id"], "amount": round(ratio * 100.0, 1)}
                            for ink, ratio in zip(combo, ratios)
                        ],
                        "predicted_color": predicted,
                        "predicted_delta_E": delta_e,
                    }

    ranked = sorted(best_per_combo.values(), key=lambda r: r["predicted_delta_E"])[:top_n]
    return [
        {
            "rank": i + 1,
            "recipe": result["recipe"],
            "suggested_thinner_ratio": DEFAULT_THINNER_RATIO,
            "predicted_color": result["predicted_color"],
            "predicted_delta_E": result["predicted_delta_E"],
            "confidence_score": _confidence_from_delta_e(result["predicted_delta_E"]),
        }
        for i, result in enumerate(ranked)
    ]

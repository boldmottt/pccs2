"""Match engine — K-M based ink recipe recommendation.

Given a target color and available inks with K/S values,
finds the best ink combinations that produce colors closest
to the target using Kubelka-Munk theory.
"""

import itertools
from typing import Dict, List, Optional, Tuple

from app.services.kubelka_munk import KubelkaMunkCoefficients
from app.services.kubelka_munk_engine import KubelkaMunkEngine
from app.services.color_math import calculate_delta_e_76


class MatchEngine:
    """K-M based recipe recommendation engine.

    Workflow:
    1. Receive target color (L*a*b*) and list of available inks with K/S values
    2. Generate candidate combinations of inks (1 to max_components inks)
    3. For each combination, search ratio space to minimize Delta E
    4. Return top recipes ranked by predicted Delta E
    """

    # Ratio search grid: 10% to 100% in 10% steps
    RATIO_STEPS = [round(i * 0.1, 1) for i in range(1, 11)]
    DEFAULT_MAX_RESULTS = 5
    DEFAULT_MAX_COMPONENTS = 3
    DEFAULT_THINNER_RATIO = 0.15
    # K-M only attenuates; blend chromaticity from solid colors dominates prediction.
    CHROMATICITY_BLEND_WEIGHT = 0.7

    def recommend(
        self,
        target_color: Dict[str, float],
        available_inks: List[Dict],
        base_color: Optional[Dict[str, float]] = None,
        max_components: int = None,
        max_results: int = None,
        exclude_ink_ids: Optional[List[str]] = None,
    ) -> List[Dict]:
        """Find best ink recipes to match target color.

        Args:
            target_color: Target color {L, a, b}
            available_inks: List of ink dicts, each containing:
                - ink_id: str
                - ink_name: str
                - k_over_s: float (required, must be > 0)
                - solid_color_sci: dict {L, a, b} (optional, used for a/b estimation)
            base_color: Base substrate color {L, a, b}.
                        Defaults to white {L:95, a:0, b:0} if not provided.
            max_components: Maximum number of inks in a single recipe (default: 3)
            max_results: Maximum number of recipes to return (default: 5)
            exclude_ink_ids: List of ink_ids to exclude from candidates

        Returns:
            List of recipe dicts sorted by predicted_delta_E ascending:
                - rank: int (1-based)
                - recipe: List of {ink_id, ink_name, amount}
                - suggested_thinner_ratio: float
                - predicted_color: {L, a, b}
                - predicted_delta_E: float
                - confidence_score: float
        """
        if max_components is None:
            max_components = self.DEFAULT_MAX_COMPONENTS
        if max_results is None:
            max_results = self.DEFAULT_MAX_RESULTS
        if base_color is None:
            base_color = {"L": 95.0, "a": 0.0, "b": 0.0}

        # Filter inks: must have k_over_s > 0 and not be excluded
        exclude_set = set(exclude_ink_ids) if exclude_ink_ids else set()
        candidate_inks = [
            ink for ink in available_inks
            if ink.get("k_over_s") is not None
            and ink["k_over_s"] > 0
            and ink["ink_id"] not in exclude_set
        ]

        if not candidate_inks:
            return []

        # Clamp max_components to actual number of available inks
        max_components = min(max_components, len(candidate_inks))

        # Generate and evaluate all candidate recipes
        all_candidates: List[Tuple[float, Dict]] = []

        for n_inks in range(1, max_components + 1):
            for ink_combo in itertools.combinations(candidate_inks, n_inks):
                best = self._optimize_ratios(
                    ink_combo, target_color, base_color
                )
                if best is not None:
                    all_candidates.append(best)

        # Sort by delta_E ascending (best match first)
        all_candidates.sort(key=lambda x: x[0])

        # Build response
        results = []
        for rank, (delta_e, candidate) in enumerate(all_candidates[:max_results], 1):
            results.append({
                "rank": rank,
                "recipe": candidate["recipe"],
                "suggested_thinner_ratio": self.DEFAULT_THINNER_RATIO,
                "predicted_color": candidate["predicted_color"],
                "predicted_delta_E": round(delta_e, 4),
                "confidence_score": self._calculate_confidence(delta_e),
            })

        return results

    def _optimize_ratios(
        self,
        inks: Tuple[Dict, ...],
        target_color: Dict[str, float],
        base_color: Dict[str, float],
    ) -> Optional[Tuple[float, Dict]]:
        """Find the best ratio combination for a given set of inks.

        Uses grid search over ratio space. For each ratio combination,
        calculates the blended K/S, predicts color via K-M, and computes Delta E.

        Args:
            inks: Tuple of ink dicts
            target_color: Target {L, a, b}
            base_color: Base substrate {L, a, b}

        Returns:
            Tuple of (delta_e, candidate_dict) or None if no valid result
        """
        n = len(inks)
        best_delta_e = float("inf")
        best_result = None

        # For single ink, just search amount
        # For multiple inks, search ratio combinations
        if n == 1:
            ratio_combinations = [(r,) for r in self.RATIO_STEPS]
        elif n == 2:
            ratio_combinations = [
                (r1, r2)
                for r1 in self.RATIO_STEPS
                for r2 in self.RATIO_STEPS
                if round(r1 + r2, 1) <= 1.0
            ]
        elif n == 3:
            ratio_combinations = [
                (r1, r2, r3)
                for r1 in self.RATIO_STEPS
                for r2 in self.RATIO_STEPS
                for r3 in self.RATIO_STEPS
                if round(r1 + r2 + r3, 1) <= 1.0
            ]
        else:
            # For 4+ inks, limit search to equal ratios only (too many combos)
            equal_ratio = round(1.0 / n, 2)
            ratio_combinations = [tuple(equal_ratio for _ in range(n))]

        for ratios in ratio_combinations:
            # Calculate blended K/S as weighted sum
            blended_k_over_s = sum(
                inks[i]["k_over_s"] * ratios[i] for i in range(n)
            )

            if blended_k_over_s <= 0:
                continue

            # Calculate blended a, b from ink solid colors (weighted average)
            blended_a = 0.0
            blended_b = 0.0
            total_ratio = sum(ratios)

            if total_ratio > 0:
                for i in range(n):
                    sci = inks[i].get("solid_color_sci")
                    if sci:
                        blended_a += sci.get("a", 0.0) * ratios[i]
                        blended_b += sci.get("b", 0.0) * ratios[i]
                blended_a /= total_ratio
                blended_b /= total_ratio

            # Predict color using K-M engine
            recipe = {
                "layers": [{
                    "k_over_s": blended_k_over_s,
                    "thickness": 1.0,
                }]
            }
            base_L = base_color.get("L", 95.0)
            km_base = {
                "L": base_L,
                "a": base_color.get("a", 0.0) + blended_a,
                "b": base_color.get("b", 0.0) + blended_b,
                "R_inf": ((base_L + 16.0) / 116.0) ** 3,
            }

            km_result = KubelkaMunkEngine.predict_recipe(recipe, km_base)
            predicted = km_result["predicted_color"]

            w = self.CHROMATICITY_BLEND_WEIGHT
            predicted["a"] = blended_a * w + predicted["a"] * (1 - w)
            predicted["b"] = blended_b * w + predicted["b"] * (1 - w)

            delta_e = calculate_delta_e_76(target_color, predicted)

            if delta_e < best_delta_e:
                best_delta_e = delta_e
                best_result = {
                    "recipe": [
                        {
                            "ink_id": inks[i]["ink_id"],
                            "ink_name": inks[i].get("ink_name", ""),
                            "amount": round(ratios[i] * 100, 1),
                        }
                        for i in range(n)
                        if ratios[i] > 0
                    ],
                    "predicted_color": {
                        "L": round(predicted["L"], 4),
                        "a": round(predicted["a"], 4),
                        "b": round(predicted["b"], 4),
                    },
                }

        if best_result is None:
            return None

        return (best_delta_e, best_result)

    def _calculate_confidence(
        self,
        delta_e: float,
    ) -> float:
        """Calculate confidence score based on delta_E.

        Lower delta_E = higher confidence.
        - delta_E < 1.0  -> confidence ~1.0 (excellent match)
        - delta_E ~ 3.0  -> confidence ~0.5 (acceptable)
        - delta_E > 10.0 -> confidence ~0.1 (poor)

        Uses exponential decay: confidence = exp(-0.2 * delta_E)

        Args:
            delta_e: Predicted Delta E value

        Returns:
            Confidence score between 0.0 and 1.0
        """
        import math
        confidence = math.exp(-0.2 * delta_e)
        return round(max(0.0, min(1.0, confidence)), 4)


# Global singleton
match_engine = MatchEngine()

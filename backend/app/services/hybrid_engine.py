"""Hybrid K-M + ML engine - combines physical model with ML correction."""

from typing import Dict, List, Optional
import numpy as np

from app.services.kubelka_munk_engine import KubelkaMunkEngine
from app.services.ml_correction_engine import MLCorrectionEngine
from app.services.color_math import calculate_delta_e_76


class HybridEngine:
    """Hybrid K-M + ML engine for color prediction.

    Combines the physical Kubelka-Munk model with ML-based correction
    to improve prediction accuracy. When ML model is not trained,
    falls back to pure K-M predictions.
    """

    def __init__(self) -> None:
        """Initialize the hybrid engine.

        Creates instances of K-M engine for physical predictions
        and ML engine for correction refinement.
        """
        self.km_engine = KubelkaMunkEngine()
        self.ml_engine = MLCorrectionEngine()
        self._training_data: List[Dict] = []

    def train(self, historical_data: List[Dict]) -> Dict:
        """Train ML engine on historical data.

        Extracts recipe features and learns correction patterns
        from differences between K-M predictions and actual measurements.

        Args:
            historical_data: List of dicts containing:
                - recipe: Recipe with layers and base_color
                - base_color: Base color {L, a, b}
                - km_prediction: K-M predicted color {L, a, b}
                - actual_measurement: Actual measured color {L, a, b}

        Returns:
            Training result containing:
                - samples_trained: Number of samples used
                - model_scores: Dictionary with R^2 scores for each channel

        Raises:
            ValueError: If historical_data is empty or missing required fields
        """
        self._training_data = historical_data
        self.ml_engine.train(historical_data)

        # Calculate model scores for reporting
        scores = self._get_model_scores()

        return {
            "samples_trained": len(historical_data),
            "model_scores": scores,
        }

    def predict(self, recipe: Dict, base_color: Dict) -> Dict:
        """Run full K-M + ML prediction pipeline.

        1. Run K-M prediction on recipe
        2. If ML trained, predict correction and apply
        3. Calculate delta_E between KM prediction and final

        Args:
            recipe: Recipe dict with:
                - layers: List of layer dicts with k_over_s and thickness
            base_color: Base color with L, a, b, R_inf

        Returns:
            Prediction result containing:
                - km_prediction: K-M predicted {L, a, b}
                - ml_correction: ML correction {L, a, b} or None if not trained
                - ml_confidence: ML confidence score (0.0 to 1.0)
                - final_prediction: Final corrected {L, a, b}
                - delta_E: Delta between KM prediction and final prediction
        """
        # Step 1: Run K-M prediction
        km_result = self.km_engine.predict_recipe(recipe, base_color)
        km_prediction = km_result["predicted_color"]

        # Step 2: Apply ML correction if trained
        if self.ml_engine.is_trained:
            # Prepare recipe features with K-M prediction embedded
            recipe_with_km = recipe.copy()
            recipe_with_km["km_prediction"] = km_prediction

            ml_result = self.ml_engine.predict(recipe_with_km)

            ml_correction = ml_result["correction"]
            ml_confidence = ml_result["confidence"]

            # Step 3: Apply correction to K-M prediction
            final_prediction = self._apply_correction(km_prediction, ml_correction)
        else:
            # Fallback: use K-M prediction directly
            ml_correction = None
            ml_confidence = 0.0
            final_prediction = km_prediction

        # Step 4: Calculate delta_E between KM and final
        delta_E = calculate_delta_e_76(km_prediction, final_prediction)

        return {
            "km_prediction": km_prediction,
            "ml_correction": ml_correction,
            "ml_confidence": ml_confidence,
            "final_prediction": final_prediction,
            "delta_E": delta_E,
        }

    def _apply_correction(
        self,
        km_prediction: Dict[str, float],
        correction: Dict[str, float]
    ) -> Dict[str, float]:
        """Apply ML correction to K-M prediction.

        Adds correction vector to K-M prediction and clamps values
        to valid CIE LAB ranges.

        Args:
            km_prediction: K-M predicted color {L, a, b}
            correction: ML correction vector {L, a, b}

        Returns:
            Corrected color with L clamped to [0, 100],
            a and b clamped to [-128, 127]
        """
        if correction is None:
            return km_prediction.copy()

        # Apply correction
        corrected_L = km_prediction["L"] + correction["L"]
        corrected_a = km_prediction["a"] + correction["a"]
        corrected_b = km_prediction["b"] + correction["b"]

        # Clamp to valid CIE LAB ranges
        # L*: 0 (black) to 100 (white)
        # a*: -128 (green) to +127 (red)
        # b*: -128 (blue) to +127 (yellow)
        final = {
            "L": float(np.clip(corrected_L, 0.0, 100.0)),
            "a": float(np.clip(corrected_a, -128.0, 127.0)),
            "b": float(np.clip(corrected_b, -128.0, 127.0)),
        }

        return final

    def _get_model_scores(self) -> Dict[str, Optional[float]]:
        """Get R^2 scores from trained ML models.

        Uses the training data stored inside ml_engine (set during train())
        to compute R^2 scores for each channel model.

        Returns:
            Dictionary with keys 'L', 'a', 'b' and R^2 scores as values.
            Returns None scores if model not trained or not enough data.
        """
        if not self.ml_engine.is_trained:
            return {"L": None, "a": None, "b": None}

        # Use training data stored inside ml_engine by FIX-009
        X = self.ml_engine._training_X
        y = self.ml_engine._training_y

        if X.size == 0 or y.shape[0] < 2:
            return {"L": None, "a": None, "b": None}

        channel_map = [("L", 0, self.ml_engine.model_l),
                       ("a", 1, self.ml_engine.model_a),
                       ("b", 2, self.ml_engine.model_b)]

        scores = {}
        for channel_name, col_idx, model in channel_map:
            if model is not None:
                try:
                    r2 = model.score(X, y[:, col_idx])
                    scores[channel_name] = float(r2) if not np.isnan(r2) else None
                except (ValueError, RuntimeError, IndexError):
                    scores[channel_name] = None
            else:
                scores[channel_name] = None

        return scores


# Global singleton instance
hybrid_engine = HybridEngine()

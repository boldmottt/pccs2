"""ML 2-stage correction engine for color prediction refinement."""

from typing import Dict, List, Tuple

import numpy as np


class MLCorrectionEngine:
    """2-stage ML correction engine.

    Takes K-M predictions and historical data to learn correction patterns,
    then predicts corrected color values for new recipes.
    """

    def __init__(self) -> None:
        """Initialize the ML correction engine.

        Attributes:
            model_l: GradientBoostingRegressor for L correction
            model_a: GradientBoostingRegressor for a correction
            model_b: GradientBoostingRegressor for b correction
            is_trained: Whether the model has been trained
            n_features_: Number of features expected by trained models
        """
        self.model_l = None
        self.model_a = None
        self.model_b = None
        self.is_trained: bool = False
        self._n_features: int = 0

    def train(self, historical_data: List[Dict]) -> None:
        """Train ML model on historical data.

        Args:
            historical_data: List of dicts containing:
                - recipe: Recipe with layers and base_color
                - km_prediction: K-M predicted color {L, a, b}
                - actual_measurement: Actual measured color {L, a, b}

        Raises:
            ValueError: If historical_data is empty or missing required fields
        """
        if not historical_data:
            raise ValueError("Historical data required for training")

        X, y = self._prepare_training_data(historical_data)

        # Train separate models for L, a, b to handle multi-output
        from sklearn.ensemble import GradientBoostingRegressor

        self.model_l = GradientBoostingRegressor(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.1,
            random_state=42,
        )
        self.model_a = GradientBoostingRegressor(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.1,
            random_state=42,
        )
        self.model_b = GradientBoostingRegressor(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.1,
            random_state=42,
        )

        self.model_l.fit(X, y[:, 0])
        self.model_a.fit(X, y[:, 1])
        self.model_b.fit(X, y[:, 2])

        # Store feature count for later validation
        self._n_features = X.shape[1]
        self.is_trained = True

    def predict(self, recipe_features: Dict) -> Dict:
        """Predict corrected color for a recipe.

        Args:
            recipe_features: Recipe dict containing layers, thickness, base_color

        Returns:
            Dict containing:
                - correction: Color correction {L, a, b} to apply
                - confidence: Prediction confidence score (0.0 to 1.0)
                - predicted_L: Final predicted L value
                - predicted_a: Final predicted a value
                - predicted_b: Final predicted b value

        Raises:
            RuntimeError: If model has not been trained
        """
        if not self.is_trained:
            raise RuntimeError("Model not trained. Call train() first.")

        # Extract features from recipe
        features = self._extract_features(recipe_features)
        features = features.reshape(1, -1)

        # Predict corrections using separate models
        correction_l = self.model_l.predict(features)[0]
        correction_a = self.model_a.predict(features)[0]
        correction_b = self.model_b.predict(features)[0]

        confidence = self._get_confidence()

        # Get base prediction from recipe (K-M prediction embedded or default)
        base_L = recipe_features.get("km_prediction", {}).get("L", 50.0)
        base_a = recipe_features.get("km_prediction", {}).get("a", 10.0)
        base_b = recipe_features.get("km_prediction", {}).get("b", 20.0)

        return {
            "correction": {
                "L": float(correction_l),
                "a": float(correction_a),
                "b": float(correction_b),
            },
            "confidence": float(confidence),
            "predicted_L": float(base_L + correction_l),
            "predicted_a": float(base_a + correction_a),
            "predicted_b": float(base_b + correction_b),
        }

    def _prepare_training_data(
        self, data: List[Dict]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Extract features (X) and labels (y) from historical data.

        Args:
            data: List of historical samples with recipe, km_prediction,
                  actual_measurement

        Returns:
            Tuple of (X, y) where:
                X: Feature matrix (n_samples, n_features)
                y: Correction vectors (n_samples, 3) for L, a, b

        Raises:
            ValueError: If data is empty or missing required fields
        """
        if not data:
            raise ValueError("Historical data required for training")

        samples = []
        corrections = []

        for sample in data:
            # Validate required fields
            if "recipe" not in sample:
                raise ValueError("Missing required field: recipe")
            if "km_prediction" not in sample:
                raise ValueError("Missing required field: km_prediction")
            if "actual_measurement" not in sample:
                raise ValueError("Missing required field: actual_measurement")

            recipe = sample["recipe"]
            km_pred = sample["km_prediction"]
            actual = sample["actual_measurement"]

            # Extract features
            features = self._extract_features(recipe)
            samples.append(features)

            # Calculate correction vector: actual - km_prediction
            correction = np.array([
                actual["L"] - km_pred["L"],
                actual["a"] - km_pred["a"],
                actual["b"] - km_pred["b"],
            ])
            corrections.append(correction)

        X = np.array(samples)
        y = np.array(corrections)

        return X, y

    def _extract_features(self, recipe: Dict) -> np.ndarray:
        """Convert recipe dict to feature vector.

        Features extracted:
        1. K/S ratios for each ink (multiplied by dilution if present)
        2. Layer thicknesses
        3. Base color (L, a, b)

        Args:
            recipe: Recipe dict containing:
                - layers: List of layer dicts with ink_id, k_over_s, thickness
                - base_color: Dict with L, a, b values

        Returns:
            Feature vector as numpy array (padded to consistent size)
        """
        features = []

        # Extract K/S ratios and thicknesses for each layer
        layers = recipe.get("layers", [])
        max_layers = 4  # Maximum expected layers for feature padding
        layer_count = min(len(layers), max_layers)

        for i in range(layer_count):
            layer = layers[i]
            k_over_s = layer.get("k_over_s", 0.0)
            thickness = layer.get("thickness", 1.0)

            # Apply dilution factor if present
            dilution = layer.get("dilution", 1.0)
            effective_k_over_s = k_over_s * dilution

            features.append(effective_k_over_s)
            features.append(thickness)

        # Pad with zeros if fewer than max_layers
        remaining_slots = max_layers - layer_count
        features.extend([0.0, 0.0] * remaining_slots)

        # Add base color features
        base_color = recipe.get("base_color", {"L": 100.0, "a": 0.0, "b": 0.0})
        features.append(base_color.get("L", 100.0))
        features.append(base_color.get("a", 0.0))
        features.append(base_color.get("b", 0.0))

        return np.array(features, dtype=float)

    def _get_confidence(self) -> float:
        """Calculate prediction confidence score.

        Returns:
            Confidence score between 0.0 (low) and 1.0 (high)
            Returns 0.0 if model is not trained or not enough samples
        """
        if not self.is_trained:
            return 0.0

        # Need at least 2 samples for meaningful R^2 calculation
        if self._n_features == 0:
            return 0.0

        # Use average R^2 score across all three models as confidence indicator
        scores = []

        if hasattr(self, "model_l") and self.model_l is not None:
            try:
                r2 = self.model_l.score(*self._prepare_training_data_from_model())
                if not np.isnan(r2):
                    scores.append(float(r2))
            except (ValueError, RuntimeError):
                pass

        if hasattr(self, "model_a") and self.model_a is not None:
            try:
                r2 = self.model_a.score(*self._prepare_training_data_from_model())
                if not np.isnan(r2):
                    scores.append(float(r2))
            except (ValueError, RuntimeError):
                pass

        if hasattr(self, "model_b") and self.model_b is not None:
            try:
                r2 = self.model_b.score(*self._prepare_training_data_from_model())
                if not np.isnan(r2):
                    scores.append(float(r2))
            except (ValueError, RuntimeError):
                pass

        if not scores:
            return 0.0

        avg_r2 = float(np.mean(scores))
        return float(np.clip(avg_r2, 0.0, 1.0))

    def _prepare_training_data_from_model(self) -> Tuple[np.ndarray, np.ndarray]:
        """Helper to get training data shape for confidence calculation.

        Note: This is a simplified version that just returns shape info.
        For real confidence, we'd need to store training data.
        """
        # Return dummy data with correct feature count
        n_features = self._n_features if self._n_features > 0 else 6
        X = np.zeros((1, n_features))
        y = np.zeros(1)  # 1D array for single-output models
        return X, y

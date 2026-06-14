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
        # 학습에 쓴 실제 (X, y)와 그로부터 한 번 계산해 캐시한 신뢰도.
        # 신뢰도는 예측마다 다시 계산하지 않고 학습 시점에 고정한다.
        self._train_X = None
        self._train_y = None
        self._confidence: float = 0.0

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
        # 실제 학습 데이터를 보관하고, 그로부터 신뢰도를 한 번 계산해 캐시한다.
        self._train_X = X
        self._train_y = y
        self.is_trained = True
        self._confidence = self._compute_confidence()

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
        """Return the cached confidence score (computed once at train time).

        Returns:
            Confidence score between 0.0 (low) and 1.0 (high).
            0.0 if the model is not trained.
        """
        return self._confidence if self.is_trained else 0.0

    # 신뢰도를 신뢰할 만하게 만드는 최소 표본 수. 이보다 적으면 교차검증이
    # 의미가 없어(과적합) 보수적으로 0을 반환한다.
    _MIN_SAMPLES_FOR_CONFIDENCE = 4

    def _compute_confidence(self) -> float:
        """Cross-validated R^2 across the three channel models, averaged.

        실제 학습 데이터(self._train_X/_train_y)에 대해 교차검증 R^2을 구한다.
        in-sample 점수는 GradientBoosting 과적합으로 항상 ~1.0이라 의미가 없어,
        held-out 성능(교차검증)으로 신뢰도를 추정한다. 표본이 부족하면 0.

        Returns:
            Confidence in [0.0, 1.0].
        """
        if self._train_X is None or self._train_y is None:
            return 0.0
        n = self._train_X.shape[0]
        if n < self._MIN_SAMPLES_FOR_CONFIDENCE:
            return 0.0

        from sklearn.base import clone
        from sklearn.model_selection import cross_val_score

        # 각 테스트 폴드에 표본이 최소 2개는 들어가도록 cv를 잡는다 (n//2).
        # 그래야 폴드별 R^2이 의미를 갖고 sklearn의 단일표본 경고도 피한다.
        cv = max(2, min(5, n // 2))
        scores = []
        for model, col in (
            (self.model_l, 0),
            (self.model_a, 1),
            (self.model_b, 2),
        ):
            if model is None:
                continue
            try:
                r2 = float(
                    np.mean(
                        cross_val_score(
                            clone(model),
                            self._train_X,
                            self._train_y[:, col],
                            cv=cv,
                            scoring="r2",
                        )
                    )
                )
                if not np.isnan(r2):
                    scores.append(r2)
            except (ValueError, RuntimeError):
                pass

        if not scores:
            return 0.0
        return float(np.clip(float(np.mean(scores)), 0.0, 1.0))

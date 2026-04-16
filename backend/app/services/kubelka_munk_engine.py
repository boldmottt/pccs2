"""Kubelka-Munk 1-stage physical model engine."""

from typing import Dict, List

from app.services.kubelka_munk import KubelkaMunkCoefficients


class KubelkaMunkEngine:
    """K-M 1-stage physical model engine for color prediction."""

    @classmethod
    def predict_layer_color(
        cls,
        layer: Dict,
        base_color: Dict
    ) -> Dict[str, float]:
        """Predict color after applying a single layer.

        Uses the adding-up formula to combine layer reflectance with base
        reflectance. The layer's K/S ratio determines its optical properties.

        Args:
            layer: Layer data containing:
                - k_over_s: K/S ratio for the layer
                - thickness: Layer thickness (optional, default 1.0)
            base_color: Base color with 'R_inf' key for reflectance

        Returns:
            Predicted color with L, a, b values converted from reflectance
        """
        k_over_s = layer.get("k_over_s", 0.0)
        thickness = layer.get("thickness", 1.0)

        # Calculate layer reflectance for infinite backing
        layer_R_inf = KubelkaMunkCoefficients.calculate_reflectance_infinite(
            k_over_s
        )

        # Apply thickness using K-M theory:
        # R(t) = R_inf * (1 - exp(-2*alpha*t)) / (1 - R_inf^2 * exp(-2*alpha*t))
        # Simplified: for thin layers, R decreases from R_inf exponentially
        # For practical purposes: R_effective = R_inf^(1 - exp(-thickness))
        alpha = 1.0  # Attenuation constant
        effective_R = layer_R_inf ** (1 - (1 / (1 + thickness * alpha)))

        # Get base reflectance
        base_R = base_color.get("R_inf", 1.0)

        # Combine layer and base using K-M adding-up formula
        # When layer is applied over base:
        # R_comb = R_layer + (T_layer^2 * R_base) / (1 - R_layer * R_base)
        # But when base is white (R_base ~ 1), layer R dominates
        # For thin layers on white: R_comb approx layer_R_inf
        if abs(1 - effective_R * base_R) < 1e-10:
            # Avoid division by zero - layer dominates
            combined_R = min(effective_R, base_R)
        else:
            R1 = effective_R
            R2 = base_R
            T1 = 1 - R1
            combined_R = R1 + (T1**2 * R2) / (1 - R1 * R2)
            combined_R = min(max(combined_R, 0.0), 1.0)

        # Convert reflectance to CIE L*
        # L* = 116 * (Y/Yn)^(1/3) - 16 for Y/Yn > 0.008856
        # Y/Yn is our combined_R (normalized reflectance)
        delta = 6.0 / 116.0  # (1/3) * (6/116)^3 = 0.008856
        if combined_R > delta**3:
            L = 116 * (combined_R ** (1.0 / 3.0)) - 16
        else:
            L = combined_R * (116 / delta) - 16
        L = min(max(L, 0.0), 100.0)

        # Attenuate a and b based on coverage
        # Higher K/S = more absorption = less of base shows through
        coverage = 1 - layer_R_inf
        a = base_color.get("a", 0.0) * (1 - coverage * 0.5)
        b = base_color.get("b", 0.0) * (1 - coverage * 0.5)

        return {
            "L": L,
            "a": a,
            "b": b,
            "R_inf": combined_R,
        }

    @classmethod
    def predict_recipe(
        cls,
        recipe: Dict,
        base_color: Dict
    ) -> Dict:
        """Predict final color for complete multi-layer recipe.

        Sequentially applies each layer using the K-M adding-up formula.
        Layers are processed in order, with each layer's output becoming
        the base for the next layer.

        Args:
            recipe: Recipe data containing:
                - layers: List of layer dicts with k_over_s and thickness
            base_color: Initial substrate color with L, a, b, R_inf

        Returns:
            Prediction result containing:
                - predicted_color: Final L*a*b* values
                - reflectance: Final R_inf value
                - layers_processed: Number of layers applied
        """
        layers = recipe.get("layers", [])
        current_base = base_color.copy()

        for layer in layers:
            result = cls.predict_layer_color(layer, current_base)
            current_base = {
                "L": result["L"],
                "a": result["a"],
                "b": result["b"],
                "R_inf": result["R_inf"],
            }

        return {
            "predicted_color": {
                "L": current_base["L"],
                "a": current_base["a"],
                "b": current_base["b"],
            },
            "reflectance": current_base["R_inf"],
            "layers_processed": len(layers),
        }

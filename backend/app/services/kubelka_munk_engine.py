"""Kubelka-Munk 1-stage physical model engine."""

import math
from typing import Dict, List

from app.services.kubelka_munk import KubelkaMunkCoefficients

# Optical thickness scale: S·t per unit layer thickness. Pad-print ink
# films are strongly scattering, so a unit layer is close to opaque.
SCATTERING_PER_THICKNESS = 10.0


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

        # Get base reflectance
        base_R = min(max(base_color.get("R_inf", 1.0), 0.001), 1.0)

        # K-M finite-thickness solution (hyperbolic form) — the reflectance
        # of a layer with optical thickness X = S·t over a backing R_g:
        #   a = 1 + K/S,  b = sqrt(a² - 1)
        #   R = (1 - R_g·(a - b·coth(bX))) / (a + b·coth(bX) - R_g)
        # This correctly accounts for absorption: a dark layer transmits
        # little, so the backing barely shows through.
        a_ks = 1.0 + k_over_s
        b_ks = math.sqrt(max(a_ks * a_ks - 1.0, 0.0))
        optical_X = SCATTERING_PER_THICKNESS * thickness

        if optical_X <= 0:
            combined_R = base_R
        elif b_ks < 1e-9:
            # K/S → 0 limit (pure scattering): R = (X(1-Rg) + Rg) / (X(1-Rg) + 1)
            combined_R = (optical_X * (1 - base_R) + base_R) / (
                optical_X * (1 - base_R) + 1.0
            )
        else:
            bX = min(b_ks * optical_X, 50.0)  # coth(50) ≈ 1, avoid overflow
            coth_bx = 1.0 / math.tanh(bX)
            combined_R = (1.0 - base_R * (a_ks - b_ks * coth_bx)) / (
                a_ks + b_ks * coth_bx - base_R
            )
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
        layer_a = layer.get("color_a")
        layer_b = layer.get("color_b")
        if layer_a is not None or layer_b is not None:
            # Layer has its own chroma: mix base -> layer color by coverage
            a = base_color.get("a", 0.0) * (1 - coverage) + (layer_a or 0.0) * coverage
            b = base_color.get("b", 0.0) * (1 - coverage) + (layer_b or 0.0) * coverage
        else:
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

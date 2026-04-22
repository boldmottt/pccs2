"""Kubelka-Munk physical model for color prediction."""

import math
from dataclasses import dataclass
from typing import Dict


@dataclass
class KubelkaMunkCoefficients:
    """Kubelka-Munk coefficient calculations."""

    @staticmethod
    def calculate_km_coefficients(K: float, S: float) -> float:
        """Calculate K/S ratio from Kubelka-Munk coefficients.

        Args:
            K: Absorption coefficient
            S: Scattering coefficient

        Returns:
            K/S ratio

        Raises:
            ValueError: If S is zero
        """
        if S == 0:
            raise ValueError("Scattering coefficient S cannot be zero")
        return K / S

    @staticmethod
    def calculate_reflectance_infinite(K_over_S: float) -> float:
        """Calculate reflectance for infinite backing using K-M theory.

        Formula: R_inf = (a - sqrt(a^2 - 1)) / (a + sqrt(a^2 - 1))
        where a = 1 + K/S

        Args:
            K_over_S: K/S ratio (must be >= 0)

        Returns:
            Reflectance value (0-1)

        Raises:
            ValueError: If K_over_S is negative
        """
        if K_over_S < 0:
            raise ValueError(
                f"K/S ratio must be non-negative, got {K_over_S}. "
                "Negative K/S values are physically invalid."
            )
        a = 1.0 + K_over_S
        sqrt_term = math.sqrt(a**2 - 1)
        R_inf = (a - sqrt_term) / (a + sqrt_term)
        return R_inf

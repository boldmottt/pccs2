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

        Formula: R_inf = 1 + K/S - sqrt((K/S)^2 + 2*K/S)
                       = a - sqrt(a^2 - 1),  where a = 1 + K/S

        주의: (a - sqrt)/(a + sqrt) 형태는 분모·분자 곱이 1이라
        (a - sqrt(a^2-1))^2, 즉 정답의 제곱이 된다. 과거 그 형태로
        구현되어 어두운 색 반사율을 크게 과소평가했다 (K/S=4:
        정답 0.101 vs 버그 0.0102).

        Args:
            K_over_S: K/S ratio

        Returns:
            Reflectance value (0-1)
        """
        a = 1.0 + K_over_S
        return a - math.sqrt(a**2 - 1)

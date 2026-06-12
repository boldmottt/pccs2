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
    # CIE 역L* 함수는 파일 하단의 _lab_f_inv(정확 상수 24389/27)와 공유
    y = _lab_f_inv((L + 16.0) / 116.0)
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


# ---------- CIE Lab <-> XYZ <-> linear sRGB (D65) ----------

_D65 = (0.95047, 1.0, 1.08883)

# sRGB (IEC 61966-2-1) / D65 변환 행렬 — 감마 없이 linear 값을 채널 반사율로 사용
_XYZ_TO_RGB = (
    (3.2404542, -1.5371385, -0.4985314),
    (-0.9692660, 1.8760108, 0.0415560),
    (0.0556434, -0.2040259, 1.0572252),
)
_RGB_TO_XYZ = (
    (0.4124564, 0.3575761, 0.1804375),
    (0.2126729, 0.7151522, 0.0721750),
    (0.0193339, 0.1191920, 0.9503041),
)

_LAB_EPS = 216.0 / 24389.0  # (6/29)^3
_LAB_KAPPA = 24389.0 / 27.0  # (29/3)^3


def _lab_f_inv(t: float) -> float:
    return t ** 3 if t ** 3 > _LAB_EPS else (116.0 * t - 16.0) / _LAB_KAPPA


def _lab_f(t: float) -> float:
    return t ** (1.0 / 3.0) if t > _LAB_EPS else (_LAB_KAPPA * t + 16.0) / 116.0


def lab_to_xyz(color: Dict[str, float]) -> tuple:
    """CIE Lab (D65) -> XYZ (Y_n = 1 스케일)."""
    fy = (color["L"] + 16.0) / 116.0
    fx = fy + color["a"] / 500.0
    fz = fy - color["b"] / 200.0
    return (
        _lab_f_inv(fx) * _D65[0],
        _lab_f_inv(fy) * _D65[1],
        _lab_f_inv(fz) * _D65[2],
    )


def xyz_to_lab(xyz: tuple) -> Dict[str, float]:
    fx = _lab_f(xyz[0] / _D65[0])
    fy = _lab_f(xyz[1] / _D65[1])
    fz = _lab_f(xyz[2] / _D65[2])
    return {
        "L": 116.0 * fy - 16.0,
        "a": 500.0 * (fx - fy),
        "b": 200.0 * (fy - fz),
    }


def lab_to_rgb_reflectance(color: Dict[str, float]) -> tuple:
    """Lab -> linear sRGB 3채널 '유사 반사율' (각 채널 0.001~1.0 클램프).

    분광 데이터가 없을 때 3-채널 K-M 근사의 입력으로 사용한다.
    """
    x, y, z = lab_to_xyz(color)
    rgb = []
    for row in _XYZ_TO_RGB:
        v = row[0] * x + row[1] * y + row[2] * z
        rgb.append(max(0.001, min(1.0, v)))
    return tuple(rgb)


def rgb_reflectance_to_lab(rgb: tuple) -> Dict[str, float]:
    """linear sRGB 3채널 반사율 -> Lab."""
    xyz = []
    for row in _RGB_TO_XYZ:
        xyz.append(row[0] * rgb[0] + row[1] * rgb[1] + row[2] * rgb[2])
    return xyz_to_lab(tuple(xyz))


# ---------- CIEDE2000 ----------

def calculate_delta_e_2000(
    color1: Dict[str, float], color2: Dict[str, float]
) -> float:
    """CIEDE2000 색차 (kL = kC = kH = 1). Sharma et al. (2005) 기준 구현."""
    L1, a1, b1 = color1["L"], color1["a"], color1["b"]
    L2, a2, b2 = color2["L"], color2["a"], color2["b"]

    C1 = math.hypot(a1, b1)
    C2 = math.hypot(a2, b2)
    C_bar = (C1 + C2) / 2.0

    G = 0.5 * (1.0 - math.sqrt(C_bar ** 7 / (C_bar ** 7 + 25.0 ** 7)))
    a1p = (1.0 + G) * a1
    a2p = (1.0 + G) * a2
    C1p = math.hypot(a1p, b1)
    C2p = math.hypot(a2p, b2)

    def _hp(ap: float, b: float) -> float:
        if ap == 0.0 and b == 0.0:
            return 0.0
        h = math.degrees(math.atan2(b, ap))
        return h + 360.0 if h < 0 else h

    h1p = _hp(a1p, b1)
    h2p = _hp(a2p, b2)

    dLp = L2 - L1
    dCp = C2p - C1p

    if C1p * C2p == 0.0:
        dhp = 0.0
    else:
        diff = h2p - h1p
        if abs(diff) <= 180.0:
            dhp = diff
        elif diff > 180.0:
            dhp = diff - 360.0
        else:
            dhp = diff + 360.0
    dHp = 2.0 * math.sqrt(C1p * C2p) * math.sin(math.radians(dhp) / 2.0)

    Lp_bar = (L1 + L2) / 2.0
    Cp_bar = (C1p + C2p) / 2.0

    if C1p * C2p == 0.0:
        hp_bar = h1p + h2p
    else:
        s = h1p + h2p
        diff = abs(h1p - h2p)
        if diff <= 180.0:
            hp_bar = s / 2.0
        elif s < 360.0:
            hp_bar = (s + 360.0) / 2.0
        else:
            hp_bar = (s - 360.0) / 2.0

    T = (
        1.0
        - 0.17 * math.cos(math.radians(hp_bar - 30.0))
        + 0.24 * math.cos(math.radians(2.0 * hp_bar))
        + 0.32 * math.cos(math.radians(3.0 * hp_bar + 6.0))
        - 0.20 * math.cos(math.radians(4.0 * hp_bar - 63.0))
    )

    d_theta = 30.0 * math.exp(-(((hp_bar - 275.0) / 25.0) ** 2))
    R_C = 2.0 * math.sqrt(Cp_bar ** 7 / (Cp_bar ** 7 + 25.0 ** 7))
    S_L = 1.0 + (0.015 * (Lp_bar - 50.0) ** 2) / math.sqrt(20.0 + (Lp_bar - 50.0) ** 2)
    S_C = 1.0 + 0.045 * Cp_bar
    S_H = 1.0 + 0.015 * Cp_bar * T
    R_T = -math.sin(math.radians(2.0 * d_theta)) * R_C

    return math.sqrt(
        (dLp / S_L) ** 2
        + (dCp / S_C) ** 2
        + (dHp / S_H) ** 2
        + R_T * (dCp / S_C) * (dHp / S_H)
    )

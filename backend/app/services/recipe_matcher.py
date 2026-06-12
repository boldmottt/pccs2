"""Recipe recommendation: search ink blends that best reproduce a target color.

혼합 색 예측은 3-채널 Kubelka-Munk 근사를 사용한다: 각 잉크의 Lab 측색값을
linear sRGB 3채널 '유사 반사율'로 바꾸고, 채널별 K/S를 농도 가중 합산한 뒤
반사율로 역변환한다. 분광 데이터 없이도 감산혼합의 방향성(노랑+파랑→초록,
흰색 희석의 비선형 명도, 검정 소량의 강한 영향)을 재현한다. /predict 엔진과
동일한 K-M 물리 모델 계열이라 두 기능의 예측이 일관된다.
"""

from itertools import combinations
from typing import Dict, List, Optional, Sequence, Tuple

from app.services.color_math import (
    calculate_delta_e_2000,
    lab_to_rgb_reflectance,
    rgb_reflectance_to_lab,
)
from app.services.kubelka_munk import KubelkaMunkCoefficients

# Categories that contribute color when blended
_BLENDABLE_CATEGORIES = {"COLOR", "TRANSPARENT", "EFFECT"}

# Candidate pool: closest inks by delta E, plus the lightest/darkest inks
# (명도 조정용 흰/검은 목표색과 멀어도 거의 항상 필요하다).
_MAX_POOL_BY_DELTA_E = 8
_MAX_CANDIDATE_POOL = 10

# Mixing ratio grid resolution for the coarse simplex search
_RATIO_STEP = 0.1

# Local refinement: pairwise mass-transfer steps per round (coarse -> fine)
# 검정처럼 강한 잉크는 실배합에서 2~3%만 쓰이므로 미세 스텝(1%)까지 내려간다
_REFINE_STEPS = (0.05, 0.02, 0.01)
_REFINE_TOP_N = 10
_MIN_COMPONENT_RATIO = 0.02

# Diversity filter: skip near-duplicate recipes among the top picks
_DIVERSITY_JACCARD = 2.0 / 3.0

# 반사율 하한 — 검정 잉크 K/S의 상한을 정하는 캘리브레이션 노브.
# (Saunderson 표면반사 보정은 k1≈4% 하한이 사용자가 입력하는 진한 검정
# Lab(L*<24 ⇔ R<0.04)과 충돌해 단일 잉크조차 자기 색을 재현하지 못하므로
# 적용하지 않는다. 대신 이 하한으로 검정의 혼합 지배력을 제한한다.)
_MIN_CHANNEL_R = 0.01

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


def _ink_ks_channels(ink: Dict) -> Tuple[float, float, float]:
    """잉크 단색 Lab -> 채널별 K/S = (1-R)^2 / (2R)."""
    rgb = lab_to_rgb_reflectance(ink["solid_color_sci"])
    ks = []
    for r in rgb:
        r = max(_MIN_CHANNEL_R, r)
        ks.append((1.0 - r) ** 2 / (2.0 * r))
    return tuple(ks)


def _predict_blend_color(
    ks_list: Sequence[Tuple[float, float, float]], ratios: Sequence[float]
) -> Dict[str, float]:
    """채널별 K/S 가산 혼합 -> 반사율 역변환 -> Lab.

    단일 잉크(ratio=1)는 자기 단색 Lab을 그대로 재현한다 (K/S 변환이
    가역이므로) — 추천 결과의 sanity 기준.
    """
    rgb = []
    for channel in range(3):
        ks_mix = sum(ks[channel] * ratio for ks, ratio in zip(ks_list, ratios))
        r = KubelkaMunkCoefficients.calculate_reflectance_infinite(ks_mix)
        rgb.append(max(_MIN_CHANNEL_R, min(1.0, r)))
    return rgb_reflectance_to_lab(tuple(rgb))


def _confidence_from_delta_e(delta_e: float) -> float:
    """Map ΔE2000 to a 0-1 confidence score (dE 0 -> 1.0, dE >= 20 -> 0).

    참고: ΔE2000은 큰 색차에서 ΔE76보다 압축된 값을 내므로 이 스케일은
    ΔE76 시절보다 관대한 편이다. 실측 데이터가 쌓이면 재캘리브레이션 대상.
    """
    return max(0.0, min(1.0, 1.0 - delta_e / 20.0))


def _build_candidate_pool(
    candidates: List[Dict], target_color: Dict[str, float]
) -> List[Dict]:
    """ΔE2000 상위 8종 + 최명(max L*)·최암(min L*) 잉크를 풀에 보장."""
    ranked = sorted(
        candidates,
        key=lambda ink: calculate_delta_e_2000(ink["solid_color_sci"], target_color),
    )
    pool = ranked[:_MAX_POOL_BY_DELTA_E]
    pool_ids = {ink["ink_id"] for ink in pool}

    lightest = max(candidates, key=lambda ink: ink["solid_color_sci"]["L"])
    darkest = min(candidates, key=lambda ink: ink["solid_color_sci"]["L"])
    for extreme in (lightest, darkest):
        if extreme["ink_id"] not in pool_ids and len(pool) < _MAX_CANDIDATE_POOL:
            pool.append(extreme)
            pool_ids.add(extreme["ink_id"])
    # 남는 슬롯은 ΔE 차순위로 채움
    for ink in ranked[_MAX_POOL_BY_DELTA_E:]:
        if len(pool) >= _MAX_CANDIDATE_POOL:
            break
        if ink["ink_id"] not in pool_ids:
            pool.append(ink)
            pool_ids.add(ink["ink_id"])
    return pool


def _refine_ratios(
    ks_list: Sequence[Tuple[float, float, float]],
    ratios: Tuple[float, ...],
    target_color: Dict[str, float],
    best_delta_e: float,
) -> Tuple[Tuple[float, ...], Dict[str, float], float]:
    """쌍별 질량 이동(coordinate search)으로 비율 미세조정.

    j→i로 δ만큼 옮기면 합=1이 정확히 유지되고 두 성분만 변한다.
    엄격 개선일 때만 수락(진동 방지), 라운드 내 개선 없으면 조기 종료.
    """
    n = len(ratios)
    if n < 2:
        predicted = _predict_blend_color(ks_list, ratios)
        return ratios, predicted, best_delta_e

    best_ratios = list(ratios)
    best_predicted = _predict_blend_color(ks_list, best_ratios)

    for step in _REFINE_STEPS:
        improved = False
        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                # j(donor)에서 i(receiver)로 step 이동
                if best_ratios[j] - step < _MIN_COMPONENT_RATIO:
                    continue
                trial = list(best_ratios)
                trial[j] -= step
                trial[i] += step
                predicted = _predict_blend_color(ks_list, trial)
                delta_e = calculate_delta_e_2000(predicted, target_color)
                if delta_e < best_delta_e:
                    best_ratios = trial
                    best_delta_e = delta_e
                    best_predicted = predicted
                    improved = True
        if not improved:
            break

    return tuple(best_ratios), best_predicted, best_delta_e


def _select_diverse(results: List[Dict], top_n: int) -> List[Dict]:
    """상위 결과에서 잉크 구성이 거의 같은 변형(부분집합/Jaccard 유사)을 걸러
    실질적으로 다른 배합 3가지를 제시한다. 후보가 모자라면 유사한 것으로 채움."""
    selected: List[Dict] = []
    skipped: List[Dict] = []

    for result in results:
        if len(selected) >= top_n:
            break
        ink_set = {item["ink_id"] for item in result["recipe"]}
        similar = False
        for chosen in selected:
            chosen_set = {item["ink_id"] for item in chosen["recipe"]}
            union = ink_set | chosen_set
            jaccard = len(ink_set & chosen_set) / len(union) if union else 1.0
            subset = ink_set <= chosen_set or chosen_set <= ink_set
            if jaccard >= _DIVERSITY_JACCARD or subset:
                similar = True
                break
        if similar:
            skipped.append(result)
        else:
            selected.append(result)

    for result in skipped:
        if len(selected) >= top_n:
            break
        selected.append(result)
    selected.sort(key=lambda r: r["predicted_delta_E"])
    return selected[:top_n]


def recommend_recipes(
    target_color: Dict[str, float],
    inks: List[Dict],
    exclude_inks: Optional[List[str]] = None,
    max_components: Optional[int] = None,
    top_n: int = 3,
) -> List[Dict]:
    """Search blends of master inks that minimize ΔE2000 against the target.

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

    pool = _build_candidate_pool(candidates, target_color)
    ks_by_id = {ink["ink_id"]: _ink_ks_channels(ink) for ink in pool}

    # 1단계: 거친 그리드 전수 탐색 — 조합별 최적 비율만 보관
    # (combinations()는 부분집합을 한 번씩만 내놓으므로 dict 중복제거 불필요)
    grids = {
        size: list(_ratio_grids(size))
        for size in range(1, min(max_components, len(pool)) + 1)
    }
    coarse_results: List[Dict] = []
    for size, grid in grids.items():
        for combo in combinations(pool, size):
            ks_list = [ks_by_id[ink["ink_id"]] for ink in combo]
            best_ratios = None
            best_delta_e = float("inf")
            for ratios in grid:
                predicted = _predict_blend_color(ks_list, ratios)
                delta_e = calculate_delta_e_2000(predicted, target_color)
                if delta_e < best_delta_e:
                    best_ratios = ratios
                    best_delta_e = delta_e
            coarse_results.append({
                "combo": combo,
                "ratios": best_ratios,
                "delta_e": best_delta_e,
            })

    # 2단계: 상위 조합만 쌍별 질량 이동으로 미세조정
    coarse_top = sorted(coarse_results, key=lambda r: r["delta_e"])[:_REFINE_TOP_N]
    refined: List[Dict] = []
    for entry in coarse_top:
        ks_list = [ks_by_id[ink["ink_id"]] for ink in entry["combo"]]
        ratios, predicted, delta_e = _refine_ratios(
            ks_list, entry["ratios"], target_color, entry["delta_e"]
        )
        refined.append({
            "recipe": [
                {"ink_id": ink["ink_id"], "amount": round(ratio * 100.0, 1)}
                for ink, ratio in zip(entry["combo"], ratios)
            ],
            "predicted_color": predicted,
            "predicted_delta_E": delta_e,
        })

    refined.sort(key=lambda r: r["predicted_delta_E"])
    final = _select_diverse(refined, top_n)

    return [
        {
            "rank": i + 1,
            "recipe": result["recipe"],
            "suggested_thinner_ratio": DEFAULT_THINNER_RATIO,
            "predicted_color": result["predicted_color"],
            "predicted_delta_E": result["predicted_delta_E"],
            "confidence_score": _confidence_from_delta_e(result["predicted_delta_E"]),
        }
        for i, result in enumerate(final)
    ]

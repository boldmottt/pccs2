from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict


class InkItemForMatch(BaseModel):
    ink_id: str
    amount: float


class MatchRequest(BaseModel):
    pattern_id: str
    target_color: Dict[str, float]
    # 추천 로직은 아직 도수별로 분기하지 않는다. 클라이언트 호환을 위해 받되
    # 선택 필드로 둔다 (필수였으나 미사용이었음).
    layer_number: Optional[int] = Field(None, ge=1)
    exclude_inks: Optional[List[str]] = None
    max_components: Optional[int] = Field(None, ge=1, le=4)


class RecommendedRecipe(BaseModel):
    rank: int
    recipe: List[InkItemForMatch]
    suggested_thinner_ratio: float
    predicted_color: Dict[str, float]
    predicted_delta_E: float
    confidence_score: float


class MatchResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    result_id: str
    pattern_id: str
    recommended_recipes: List[RecommendedRecipe]
    engine_used: str
    model_version: str

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class InkItemForMatch(BaseModel):
    ink_id: str
    amount: float


class MatchRequest(BaseModel):
    pattern_id: str
    target_color: Dict[str, float]
    layer_number: int
    exclude_inks: Optional[List[str]] = None
    max_components: Optional[int] = None


class RecommendedRecipe(BaseModel):
    rank: int
    recipe: List[InkItemForMatch]
    suggested_thinner_ratio: float
    predicted_color: Dict[str, float]
    predicted_delta_E: float
    confidence_score: float


class MatchResponse(BaseModel):
    result_id: str
    pattern_id: str
    recommended_recipes: List[RecommendedRecipe]
    engine_used: str
    model_version: str


class CopyLayerRequest(BaseModel):
    source_sample_id: str
    layer_number: int

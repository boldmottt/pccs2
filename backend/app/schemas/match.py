from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from uuid import uuid4


class InkItemForMatch(BaseModel):
    """Single ink item in a recommended recipe."""
    ink_id: str
    ink_name: str = ""
    amount: float = Field(..., ge=0.0, description="Amount in percentage (0-100)")


class MatchRequest(BaseModel):
    """Request schema for recipe recommendation.

    - pattern_id: Which pattern to match against (used to look up target color)
    - target_color: Target color {L, a, b} to match. If omitted, fetched from pattern.
    - base_color: Substrate base color {L, a, b}. Defaults to white if omitted.
    - layer_number: Which layer to recommend recipe for
    - exclude_inks: List of ink_ids to exclude from candidates
    - max_components: Max number of inks in a single recipe (default: 3)
    - max_results: Max number of recipe recommendations to return (default: 5)
    """
    pattern_id: str
    target_color: Optional[Dict[str, float]] = Field(
        None,
        description="Target color {L, a, b}. If omitted, uses pattern's target_base_color_sci."
    )
    base_color: Optional[Dict[str, float]] = Field(
        None,
        description="Substrate base color {L, a, b}. Defaults to {L:95, a:0, b:0} if omitted."
    )
    layer_number: int = Field(1, ge=1, description="Layer number to recommend for")
    exclude_inks: Optional[List[str]] = Field(
        None,
        description="List of ink_ids to exclude from recommendation"
    )
    max_components: Optional[int] = Field(
        None,
        ge=1,
        le=5,
        description="Maximum number of inks in a recipe (1-5, default: 3)"
    )
    max_results: Optional[int] = Field(
        None,
        ge=1,
        le=20,
        description="Maximum number of recipes to return (1-20, default: 5)"
    )


class RecommendedRecipe(BaseModel):
    """A single recommended recipe in the response."""
    rank: int = Field(..., description="Rank (1 = best match)")
    recipe: List[InkItemForMatch] = Field(..., description="List of inks and amounts")
    suggested_thinner_ratio: float = Field(..., description="Suggested thinner ratio (0-1)")
    predicted_color: Dict[str, float] = Field(..., description="Predicted color {L, a, b}")
    predicted_delta_E: float = Field(..., description="Predicted Delta E from target")
    confidence_score: float = Field(..., description="Confidence score (0-1)")


class MatchResponse(BaseModel):
    """Response schema for recipe recommendation."""
    result_id: str = Field(..., description="Unique result ID")
    pattern_id: str = Field(..., description="Pattern ID that was matched")
    target_color_used: Dict[str, float] = Field(..., description="Target color used for matching")
    base_color_used: Dict[str, float] = Field(..., description="Base color used for matching")
    recommended_recipes: List[RecommendedRecipe] = Field(..., description="Ranked recipe recommendations")
    engine_used: str = Field("KM_GRID_SEARCH", description="Engine used (KM_GRID_SEARCH)")
    model_version: str = Field("1.0", description="Engine version")
    available_inks_count: int = Field(..., description="Number of inks with K/S data available")

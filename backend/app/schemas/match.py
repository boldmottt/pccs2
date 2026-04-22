from pydantic import BaseModel, Field
from typing import Dict, List, Optional


class MatchRequest(BaseModel):
    """Schema for requesting ink recipe recommendations."""

    target_color: Dict[str, float] = Field(
        ...,
        description="Target color {L, a, b} to match"
    )
    base_color: Optional[Dict[str, float]] = Field(
        None,
        description="Base substrate color {L, a, b}. Defaults to white."
    )
    max_components: int = Field(
        3,
        ge=1,
        le=5,
        description="Maximum number of inks per recipe (default: 3)"
    )
    max_results: int = Field(
        5,
        ge=1,
        le=20,
        description="Maximum number of recipes to return (default: 5)"
    )
    exclude_ink_ids: Optional[List[str]] = Field(
        None,
        description="Ink IDs to exclude from candidates"
    )


class RecipeResult(BaseModel):
    """Single recommended recipe result."""

    rank: int = Field(..., description="Rank (1-based)")
    recipe: List[Dict] = Field(
        ...,
        description="List of {ink_id, ink_name, amount} in the recipe"
    )
    suggested_thinner_ratio: float = Field(
        ...,
        description="Suggested thinner ratio (0.0-1.0)"
    )
    predicted_color: Dict[str, float] = Field(
        ...,
        description="Predicted color {L, a, b} after applying recipe"
    )
    predicted_delta_E: float = Field(
        ...,
        description="Delta E between target and predicted color"
    )
    confidence_score: float = Field(
        ...,
        description="Confidence score (0.0-1.0) based on Delta E"
    )


class MatchResponse(BaseModel):
    """Full match response."""

    target_color: Dict[str, float] = Field(
        ...,
        description="Target color {L, a, b}"
    )
    base_color: Dict[str, float] = Field(
        ...,
        description="Base substrate color {L, a, b}"
    )
    recipes: List[RecipeResult] = Field(
        default_factory=list,
        description="Ranked list of recommended recipes"
    )
    message: Optional[str] = Field(
        None,
        description="Optional status message (e.g., no inks found)"
    )

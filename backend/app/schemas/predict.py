"""Pydantic schemas for prediction API endpoints."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, ConfigDict


class LayerInput(BaseModel):
    """A single layer in a recipe.

    Accepts either k_over_s directly (for engine usage)
    or ink_items for REST API (which gets converted to k_over_s).
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    k_over_s: Optional[float] = Field(
        None, ge=0.0, description="K/S ratio for the layer (alternative to ink_items)"
    )
    ink_items: Optional[List[Dict[str, Any]]] = Field(
        None, description="List of ink items {ink_id, amount} to calculate k_over_s from"
    )
    thickness: float = Field(
        1.0, ge=0.0, description="Layer thickness (default: 1.0)"
    )


class RecipeInput(BaseModel):
    """A complete recipe with multiple layers."""

    layers: List[LayerInput] = Field(..., description="List of layers in the recipe")
    thinner_amount: float = Field(
        0.0, ge=0.0, description="Amount of thinner added (default: 0.0)"
    )
    hardener_amount: float = Field(
        0.0, ge=0.0, description="Amount of hardener added (default: 0.0)"
    )


class PredictRequest(BaseModel):
    """Request schema for prediction endpoint."""

    recipe: RecipeInput = Field(..., description="Recipe to predict")
    base_color: Dict[str, float] = Field(
        ...,
        description="Base color in CIE LAB format {L, a, b}",
        json_schema_extra={"example": {"L": 100.0, "a": 0.0, "b": 0.0}},
    )


class TrainRequest(BaseModel):
    """Request schema for training endpoint."""

    historical_data: List[Dict] = Field(
        ...,
        description="List of historical data entries for training",
        example=[
            {
                "recipe": {
                    "layers": [
                        {"ink_items": [{"ink_id": "white", "amount": 100.0}], "thickness": 1.0}
                    ],
                    "base_color": {"L": 100.0, "a": 0.0, "b": 0.0},
                },
                "km_prediction": {"L": 95.0, "a": 1.0, "b": 2.0},
                "actual_measurement": {"L": 94.5, "a": 1.2, "b": 1.8},
            }
        ],
    )


class PredictResponse(BaseModel):
    """Response schema for prediction endpoint."""

    km_prediction: Dict[str, float] = Field(
        ..., description="Kubelka-Munk prediction {L, a, b}"
    )
    ml_correction: Optional[Dict[str, float]] = Field(
        None, description="ML correction applied {L, a, b}, None if not trained"
    )
    ml_confidence: float = Field(
        ..., description="ML model confidence score (0.0 to 1.0)"
    )
    final_prediction: Dict[str, float] = Field(
        ..., description="Final corrected prediction {L, a, b}"
    )
    delta_E: float = Field(
        ..., description="Delta E between KM prediction and final prediction"
    )


class TrainResponse(BaseModel):
    """Response schema for training endpoint."""

    samples_trained: int = Field(..., description="Number of samples used for training")
    model_scores: Dict[str, Optional[float]] = Field(
        ..., description="R^2 scores for each channel (L, a, b)"
    )


class HealthResponse(BaseModel):
    """Response schema for health check endpoint."""

    status: str = Field(..., description="Overall health status")
    engine: str = Field(..., description="Engine name")
    version: str = Field(..., description="Engine version")
    ml_trained: bool = Field(
        ..., description="Whether ML model has been trained"
    )
    samples_count: int = Field(..., description="Number of training samples stored")

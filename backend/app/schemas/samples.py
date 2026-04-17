from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime


class InkItem(BaseModel):
    """Individual ink item in a layer recipe."""
    ink_id: str = Field(..., description="UUID of the ink material")
    amount: float = Field(
        ...,
        ge=0.0,
        description="Amount or percentage of this ink"
    )


class CopyLayerRequest(BaseModel):
    """Request to copy a layer from one sample to another."""
    source_sample_id: str = Field(..., description="UUID of source sample")
    source_layer_number: int = Field(
        ...,
        ge=1,
        description="Source layer number to copy"
    )
    target_layer_number: int = Field(
        ...,
        ge=1,
        description="Target layer number to paste to"
    )


class LayerInput(BaseModel):
    """Single layer input with ink recipe."""
    layer_number: int = Field(
        ...,
        ge=1,
        le=10,
        description="Layer number (1-10)"
    )
    ink_items: List[InkItem] = Field(
        ...,
        min_items=1,
        description="List of ink items in this layer"
    )
    thinner_pct: Optional[float] = Field(
        None,
        ge=0.0,
        le=100.0,
        description="Thinner percentage (0-100)"
    )
    hardener_pct: Optional[float] = Field(
        None,
        ge=0.0,
        le=100.0,
        description="Hardener percentage (0-100)"
    )
    print_color_sci: Optional[Dict[str, float]] = Field(
        None,
        description="Printed color in SCI mode {L, a, b}"
    )
    print_color_sce: Optional[Dict[str, float]] = Field(
        None,
        description="Printed color in SCE mode {L, a, b}"
    )
    delta_E_from_target: Optional[float] = Field(
        None,
        ge=0.0,
        description="Delta E color difference from target"
    )
    note: Optional[str] = Field(None, description="Layer notes")


class SampleCreate(BaseModel):
    """Schema for creating a new sample."""
    sample_number: int = Field(
        ...,
        ge=1,
        description="Sample number within the round"
    )
    base_color_sci: Dict[str, float] = Field(
        ...,
        description="Base color in SCI mode {L, a, b}"
    )
    base_color_sce: Dict[str, float] = Field(
        ...,
        description="Base color in SCE mode {L, a, b}"
    )
    base_material: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Base material (e.g., cotton, vinyl)"
    )
    layers: List[LayerInput] = Field(
        ...,
        min_items=1,
        max_items=10,
        description="Layer recipes for this sample"
    )

    @field_validator('layers')
    @classmethod
    def validate_layer_percentages(cls, v: List[LayerInput]) -> List[LayerInput]:
        """Validate that layer percentages sum to 100%."""
        for layer in v:
            total = sum(item.amount for item in layer.ink_items)
            if abs(total - 100.0) > 0.5:
                raise ValueError(
                    f"Layer {layer.layer_number} percentages must sum to 100%, "
                    f"got {total:.2f}%"
                )
        return v


class SampleUpdate(BaseModel):
    """Schema for updating an existing sample."""
    sample_number: Optional[int] = Field(None, description="Sample number")
    base_color_sci: Optional[Dict[str, float]] = Field(
        None,
        description="Base color in SCI mode"
    )
    base_color_sce: Optional[Dict[str, float]] = Field(
        None,
        description="Base color in SCE mode"
    )
    base_material: Optional[str] = Field(
        None,
        max_length=200,
        description="Base material"
    )
    layers: Optional[List[LayerInput]] = Field(
        None,
        description="Updated layer recipes"
    )
    final_delta_e: Optional[float] = Field(
        None,
        ge=0.0,
        description="Final Delta E color difference"
    )
    success_flag: Optional[str] = Field(
        None,
        description="Success status: SUCCESS, FAILED, or PENDING"
    )
    success_notes: Optional[str] = Field(
        None,
        max_length=1000,
        description="Notes about success/failure"
    )


class LayerResponse(BaseModel):
    """Response schema for layer data."""
    layer_number: int = Field(..., description="Layer number")
    ink_items: List[InkItem] = Field(..., description="Ink items in this layer")
    thinner_pct: Optional[float] = Field(None, description="Thinner percentage")
    hardener_pct: Optional[float] = Field(None, description="Hardener percentage")
    print_color_sci: Optional[Dict[str, float]] = Field(
        None,
        description="Printed color in SCI mode"
    )
    print_color_sce: Optional[Dict[str, float]] = Field(
        None,
        description="Printed color in SCE mode"
    )
    delta_E_from_target: Optional[float] = Field(
        None,
        description="Delta E from target"
    )
    note: Optional[str] = Field(None, description="Layer notes")

    class Config:
        from_attributes = True


class SampleResponse(BaseModel):
    """Response schema for sample data."""
    sample_id: str = Field(..., description="Sample UUID")
    round_id: str = Field(..., description="Parent round UUID")
    pattern_id: str = Field(..., description="Parent pattern UUID")
    sample_number: int = Field(..., description="Sample number")
    base_color_sci: Optional[Dict[str, float]] = Field(
        None,
        description="Base color in SCI mode"
    )
    base_color_sce: Optional[Dict[str, float]] = Field(
        None,
        description="Base color in SCE mode"
    )
    base_material: Optional[str] = Field(None, description="Base material")
    layers: Optional[List[LayerResponse]] = Field(
        None,
        description="Layer recipes"
    )
    final_delta_e: Optional[float] = Field(
        None,
        description="Final Delta E"
    )
    success_flag: Optional[str] = Field(
        None,
        description="Success status"
    )
    success_notes: Optional[str] = Field(None, description="Success notes")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True

from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class InkCategoryEnum(str, Enum):
    """Ink material category classification."""
    COLOR = "COLOR"
    TRANSPARENT = "TRANSPARENT"
    EFFECT = "EFFECT"
    ADDITIVE = "ADDITIVE"


class InkCreate(BaseModel):
    """Schema for creating a new ink master record."""
    model_config = ConfigDict(
        use_enum_values=True,
    )

    ink_name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Ink name (1-200 characters)"
    )
    ink_category: InkCategoryEnum = Field(
        InkCategoryEnum.COLOR,
        description="Ink category classification"
    )
    manufacturer: Optional[str] = Field(
        None,
        max_length=200,
        description="Ink manufacturer name"
    )
    solid_color_sci: Optional[Dict[str, float]] = Field(
        None,
        description="Solid color in SCI mode {L, a, b}"
    )
    solid_color_sce: Optional[Dict[str, float]] = Field(
        None,
        description="Solid color in SCE mode {L, a, b}"
    )
    gloss_GU: Optional[float] = Field(
        None,
        ge=0.0,
        le=100.0,
        description="Gloss measurement at 60 degrees (0-100)"
    )
    viscosity: Optional[float] = Field(
        None,
        ge=0.0,
        description="Viscosity in centipoise (cP)"
    )
    density: Optional[float] = Field(
        None,
        ge=0.0,
        le=10.0,
        description="Density in g/cm³ (0-10)"
    )
    k_over_s: Optional[float] = Field(
        None,
        ge=0.0,
        description="Kubelka-Munk K/S ratio"
    )
    memo: Optional[str] = Field(
        None,
        max_length=1000,
        description="Additional notes about this ink"
    )

    @field_validator('solid_color_sci', 'solid_color_sce')
    @classmethod
    def validate_color_dict(cls, v: Optional[Dict[str, float]]) -> Optional[Dict[str, float]]:
        """Validate color dictionary has required L, a, b keys."""
        if v is not None:
            if 'L' not in v or 'a' not in v or 'b' not in v:
                raise ValueError("Color dict must contain L, a, b keys")
        return v


class InkUpdate(BaseModel):
    """Schema for updating an existing ink record."""
    model_config = ConfigDict(
        use_enum_values=True,
    )

    ink_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=200,
        description="Ink name"
    )
    ink_category: Optional[InkCategoryEnum] = Field(
        None,
        description="Ink category"
    )
    manufacturer: Optional[str] = Field(
        None,
        max_length=200,
        description="Manufacturer"
    )
    solid_color_sci: Optional[Dict[str, float]] = Field(
        None,
        description="Solid color in SCI mode"
    )
    solid_color_sce: Optional[Dict[str, float]] = Field(
        None,
        description="Solid color in SCE mode"
    )
    gloss_GU: Optional[float] = Field(
        None,
        ge=0.0,
        le=100.0,
        description="Gloss measurement"
    )
    viscosity: Optional[float] = Field(
        None,
        ge=0.0,
        description="Viscosity"
    )
    density: Optional[float] = Field(
        None,
        ge=0.0,
        le=10.0,
        description="Density"
    )
    memo: Optional[str] = Field(
        None,
        max_length=1000,
        description="Additional notes"
    )


class InkResponse(BaseModel):
    """Response schema for ink data."""
    model_config = ConfigDict(
        from_attributes=True,
    )

    ink_id: str = Field(..., description="Ink UUID")
    ink_name: str = Field(..., description="Ink name")
    ink_category: str = Field(..., description="Ink category")
    manufacturer: Optional[str] = Field(None, description="Manufacturer")
    is_blend_ink: bool = Field(..., description="Whether this is a blend ink")
    blend_recipe: Optional[Dict[str, Any]] = Field(
        None,
        description="Blend recipe if this is a blend ink"
    )
    solid_color_sci: Optional[Dict[str, float]] = Field(
        None,
        description="Solid color in SCI mode"
    )
    solid_color_sce: Optional[Dict[str, float]] = Field(
        None,
        description="Solid color in SCE mode"
    )
    delta_sci_sce: Optional[float] = Field(
        None,
        description="Delta E between SCI and SCE"
    )
    k_over_s: Optional[float] = Field(None, description="Kubelka-Munk K/S ratio")
    gloss_index: Optional[float] = Field(None, description="Gloss index")
    gloss_GU: Optional[float] = Field(None, description="Gloss at 60°")
    viscosity: Optional[float] = Field(None, description="Viscosity")
    density: Optional[float] = Field(None, description="Density")
    memo: Optional[str] = Field(None, description="Notes")
    registered_at: datetime = Field(..., description="Registration timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

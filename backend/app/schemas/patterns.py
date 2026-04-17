from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime


class PatternStatusEnum(str):
    DEVELOPING = "DEVELOPING"
    COMPLETED = "COMPLETED"
    ON_HOLD = "ON_HOLD"


class ColorData(BaseModel):
    """CIE LAB color data for color representation.

    CIE LAB is a color space that approximates human vision:
    - L*: Lightness from 0 (black) to 100 (white)
    - a*: Green (-128) to Red (+127) axis
    - b*: Blue (-128) to Yellow (+127) axis
    """
    L: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Lightness value (0=black, 100=white)"
    )
    a: float = Field(
        ...,
        ge=-128.0,
        le=127.0,
        description="Green (-) to Red (+) axis (-128 to 127)"
    )
    b: float = Field(
        ...,
        ge=-128.0,
        le=127.0,
        description="Blue (-) to Yellow (+) axis (-128 to 127)"
    )

    @field_validator('L')
    @classmethod
    def validate_l(cls, v: float) -> float:
        """Validate L value is within valid range."""
        if v < 0 or v > 100:
            raise ValueError('L value must be between 0 and 100')
        return v

    @field_validator('a')
    @classmethod
    def validate_a(cls, v: float) -> float:
        """Validate a value is within valid range."""
        if v < -128 or v > 127:
            raise ValueError('a value must be between -128 and 127')
        return v

    @field_validator('b')
    @classmethod
    def validate_b(cls, v: float) -> float:
        """Validate b value is within valid range."""
        if v < -128 or v > 127:
            raise ValueError('b value must be between -128 and 127')
        return v

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {"L": self.L, "a": self.a, "b": self.b}

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> 'ColorData':
        """Create from dictionary."""
        return cls(L=data['L'], a=data['a'], b=data['b'])


class PatternCreate(BaseModel):
    """Schema for creating a new pattern.

    A Pattern represents the final target color to achieve,
    which guides the development of samples and rounds.
    """
    project_id: str = Field(
        ...,
        description="UUID of the parent project"
    )
    pattern_name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Pattern name (1-200 characters)"
    )
    total_print_layers: int = Field(
        ...,
        ge=1,
        le=10,
        description="Total print layers (1-10)"
    )
    target_base_color_sci: Optional[ColorData] = Field(
        None,
        description="Target base color in SCI mode (Specular Component Included)"
    )
    target_base_color_sce: Optional[ColorData] = Field(
        None,
        description="Target base color in SCE mode (Specular Component Excluded)"
    )
    target_base_material: Optional[str] = Field(
        None,
        max_length=100,
        description="Base material (e.g., '100% Cotton Denim')"
    )
    status: Optional[str] = Field(
        "DEVELOPING",
        description="Pattern status: DEVELOPING, COMPLETED, or ON_HOLD"
    )
    notes: Optional[str] = Field(
        None,
        max_length=1000,
        description="Additional notes about the pattern"
    )


class PatternUpdate(BaseModel):
    """Schema for updating an existing pattern."""
    pattern_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=200,
        description="Pattern name"
    )
    total_print_layers: Optional[int] = Field(
        None,
        ge=1,
        le=10,
        description="Total print layers"
    )
    target_base_color_sci: Optional[ColorData] = Field(
        None,
        description="Target base color in SCI mode"
    )
    target_base_color_sce: Optional[ColorData] = Field(
        None,
        description="Target base color in SCE mode"
    )
    target_base_material: Optional[str] = Field(
        None,
        max_length=100,
        description="Base material"
    )
    status: Optional[str] = Field(
        None,
        description="Pattern status: DEVELOPING, COMPLETED, or ON_HOLD"
    )
    notes: Optional[str] = Field(
        None,
        max_length=1000,
        description="Additional notes"
    )
    approved_sample_id: Optional[str] = Field(
        None,
        description="UUID of the approved sample"
    )


class PatternResponse(BaseModel):
    """Response schema for pattern data."""
    pattern_id: str = Field(..., description="Pattern UUID")
    project_id: str = Field(..., description="Parent project UUID")
    pattern_name: str = Field(..., description="Pattern name")
    total_print_layers: int = Field(..., description="Total print layers")
    target_base_color_sci: Optional[Dict[str, float]] = Field(
        None,
        description="Target base color in SCI mode"
    )
    target_base_color_sce: Optional[Dict[str, float]] = Field(
        None,
        description="Target base color in SCE mode"
    )
    target_base_material: Optional[str] = Field(
        None,
        description="Base material"
    )
    status: str = Field(..., description="Pattern status")
    notes: Optional[str] = Field(None, description="Additional notes")
    approved_sample_id: Optional[str] = Field(
        None,
        description="Approved sample UUID"
    )
    success_rate: Optional[float] = Field(
        None,
        description="Sample success rate percentage"
    )
    avg_delta_e: Optional[float] = Field(
        None,
        description="Average color difference (Delta E)"
    )
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True

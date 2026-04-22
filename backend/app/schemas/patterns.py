from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class PatternStatusEnum(str, Enum):
    """Pattern status values."""
    DEVELOPING = "DEVELOPING"
    COMPLETED = "COMPLETED"
    ON_HOLD = "ON_HOLD"


class ColorData(BaseModel):
    L: float = Field(..., ge=0.0, le=100.0)
    a: float = Field(..., ge=-128.0, le=127.0)
    b: float = Field(..., ge=-128.0, le=127.0)


class PatternCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    project_id: str
    pattern_name: str
    total_print_layers: int = Field(..., ge=1, le=10)
    target_base_color_sci: Optional[ColorData] = None
    target_base_color_sce: Optional[ColorData] = None
    target_base_material: Optional[str] = None
    status: PatternStatusEnum = PatternStatusEnum.DEVELOPING
    notes: Optional[str] = None


class PatternUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    pattern_name: Optional[str] = None
    total_print_layers: Optional[int] = None
    target_base_color_sci: Optional[ColorData] = None
    target_base_color_sce: Optional[ColorData] = None
    target_base_material: Optional[str] = None
    status: Optional[PatternStatusEnum] = None
    notes: Optional[str] = None
    approved_sample_id: Optional[str] = None


class PatternResponse(BaseModel):
    pattern_id: str
    project_id: str
    pattern_name: str
    total_print_layers: int
    target_base_color_sci: Optional[Dict[str, float]]
    target_base_color_sce: Optional[Dict[str, float]]
    target_base_material: Optional[str]
    status: str
    notes: Optional[str]
    approved_sample_id: Optional[str]
    success_rate: Optional[float]
    avg_delta_e: Optional[float]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

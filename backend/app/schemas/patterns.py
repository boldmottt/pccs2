from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Dict
from datetime import datetime
from enum import Enum


class PatternStatusEnum(str, Enum):
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
    pattern_name: str = Field(..., min_length=1, max_length=200)
    total_print_layers: int = Field(..., ge=1, le=10)
    target_base_color_sci: Optional[ColorData] = None
    target_base_color_sce: Optional[ColorData] = None
    target_base_material: Optional[str] = None
    status: PatternStatusEnum = PatternStatusEnum.DEVELOPING
    notes: Optional[str] = None


class PatternUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    pattern_name: Optional[str] = Field(None, min_length=1, max_length=200)
    total_print_layers: Optional[int] = Field(None, ge=1, le=10)
    target_base_color_sci: Optional[ColorData] = None
    target_base_color_sce: Optional[ColorData] = None
    target_base_material: Optional[str] = None
    status: Optional[PatternStatusEnum] = None
    notes: Optional[str] = None
    approved_sample_id: Optional[str] = None
    success_rate: Optional[float] = None
    avg_delta_e: Optional[float] = None


class PatternResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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

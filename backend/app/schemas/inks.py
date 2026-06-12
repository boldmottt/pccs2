from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class InkCategoryEnum(str, Enum):
    COLOR = "COLOR"
    TRANSPARENT = "TRANSPARENT"
    EFFECT = "EFFECT"
    ADDITIVE = "ADDITIVE"


class InkCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    ink_name: str = Field(..., min_length=1, max_length=200)
    ink_category: InkCategoryEnum = InkCategoryEnum.COLOR
    manufacturer: Optional[str] = None
    is_favorite: Optional[bool] = False
    plate_id: Optional[str] = None
    solid_color_sci: Optional[Dict[str, float]] = None
    solid_color_sce: Optional[Dict[str, float]] = None
    gloss_GU: Optional[float] = None
    viscosity: Optional[float] = None
    density: Optional[float] = None
    memo: Optional[str] = None


class InkUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    ink_name: Optional[str] = Field(None, min_length=1, max_length=200)
    ink_category: Optional[InkCategoryEnum] = None
    manufacturer: Optional[str] = None
    is_favorite: Optional[bool] = None
    plate_id: Optional[str] = None
    solid_color_sci: Optional[Dict[str, float]] = None
    solid_color_sce: Optional[Dict[str, float]] = None
    gloss_GU: Optional[float] = None
    viscosity: Optional[float] = None
    density: Optional[float] = None
    memo: Optional[str] = None


class RegisterBlendRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    ink_name: Optional[str] = None
    ink_category: Optional[InkCategoryEnum] = None
    manufacturer: Optional[str] = None
    plate_id: Optional[str] = None
    blend_recipe: Optional[Dict[str, Any]] = None


class InkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ink_id: str
    ink_name: str
    ink_category: str
    manufacturer: Optional[str]
    is_blend_ink: bool
    blend_recipe: Optional[Dict[str, Any]]
    is_favorite: Optional[bool] = None
    plate_id: Optional[str] = None
    solid_color_sci: Optional[Dict[str, float]]
    solid_color_sce: Optional[Dict[str, float]]
    delta_sci_sce: Optional[float]
    gloss_index: Optional[float]
    gloss_GU: Optional[float]
    viscosity: Optional[float]
    density: Optional[float]
    memo: Optional[str]
    registered_at: datetime
    updated_at: datetime

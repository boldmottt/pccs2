from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class InkCategoryEnum(str):
    COLOR = "COLOR"
    TRANSPARENT = "TRANSPARENT"
    EFFECT = "EFFECT"
    ADDITIVE = "ADDITIVE"


class InkCreate(BaseModel):
    ink_name: str = Field(..., min_length=1, max_length=200)
    ink_category: InkCategoryEnum = InkCategoryEnum.COLOR
    manufacturer: Optional[str] = None
    solid_color_sci: Optional[Dict[str, float]] = None
    solid_color_sce: Optional[Dict[str, float]] = None
    gloss_GU: Optional[float] = None
    viscosity: Optional[float] = None
    density: Optional[float] = None
    memo: Optional[str] = None


class InkUpdate(BaseModel):
    ink_name: Optional[str] = None
    ink_category: Optional[InkCategoryEnum] = None
    manufacturer: Optional[str] = None
    solid_color_sci: Optional[Dict[str, float]] = None
    solid_color_sce: Optional[Dict[str, float]] = None
    gloss_GU: Optional[float] = None
    viscosity: Optional[float] = None
    density: Optional[float] = None
    memo: Optional[str] = None


class InkResponse(BaseModel):
    ink_id: str
    ink_name: str
    ink_category: str
    manufacturer: Optional[str]
    is_blend_ink: bool
    blend_recipe: Optional[Dict[str, Any]]
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

    class Config:
        from_attributes = True

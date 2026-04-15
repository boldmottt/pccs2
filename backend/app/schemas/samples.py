from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class InkItem(BaseModel):
    ink_id: str
    amount: float = Field(..., ge=0.0)


class LayerInput(BaseModel):
    layer_number: int
    ink_items: List[InkItem]
    thinner_pct: Optional[float] = None
    hardener_pct: Optional[float] = None
    print_color_sci: Optional[Dict[str, float]] = None
    print_color_sce: Optional[Dict[str, float]] = None
    delta_E_from_target: Optional[float] = None
    note: Optional[str] = None


class SampleCreate(BaseModel):
    round_id: str
    sample_number: int
    base_color_sci: Dict[str, float]
    base_color_sce: Dict[str, float]
    base_material: str
    layers: List[LayerInput]


class SampleUpdate(BaseModel):
    sample_number: Optional[int] = None
    base_color_sci: Optional[Dict[str, float]] = None
    base_color_sce: Optional[Dict[str, float]] = None
    base_material: Optional[str] = None
    layers: Optional[List[LayerInput]] = None
    final_delta_e: Optional[float] = None
    success_flag: Optional[str] = None
    success_notes: Optional[str] = None


class LayerResponse(BaseModel):
    layer_number: int
    ink_items: List[InkItem]
    thinner_pct: Optional[float]
    hardener_pct: Optional[float]
    print_color_sci: Optional[Dict[str, float]]
    print_color_sce: Optional[Dict[str, float]]
    delta_E_from_target: Optional[float]
    note: Optional[str]

    class Config:
        from_attributes = True


class SampleResponse(BaseModel):
    sample_id: str
    round_id: str
    pattern_id: str
    sample_number: int
    base_color_sci: Optional[Dict[str, float]]
    base_color_sce: Optional[Dict[str, float]]
    base_material: Optional[str]
    layers: Optional[List[LayerResponse]]
    final_delta_e: Optional[float]
    success_flag: Optional[str]
    success_notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum


class SampleSuccessFlagEnum(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PENDING = "PENDING"


class InkItem(BaseModel):
    ink_id: str
    amount: float = Field(..., ge=0.0)
    ink_name: Optional[str] = None


class CopyLayerRequest(BaseModel):
    """Copy a layer recipe from a source sample into the target sample."""

    source_sample_id: str
    source_layer_number: int
    target_layer_number: int


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
    model_config = ConfigDict(use_enum_values=True)

    base_color_sci: Dict[str, float]
    base_color_sce: Dict[str, float]
    base_material: Optional[str] = None
    layers: List[LayerInput] = []
    success_flag: SampleSuccessFlagEnum = SampleSuccessFlagEnum.PENDING


class SampleUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    base_color_sci: Optional[Dict[str, float]] = None
    base_color_sce: Optional[Dict[str, float]] = None
    base_material: Optional[str] = None
    layers: Optional[List[LayerInput]] = None
    final_delta_e: Optional[float] = None
    success_flag: Optional[SampleSuccessFlagEnum] = None
    success_notes: Optional[str] = None


class LayerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    layer_number: int
    ink_items: List[InkItem]
    thinner_pct: Optional[float] = None
    thinner_g: Optional[float] = None
    hardener_pct: Optional[float] = None
    hardener_g: Optional[float] = None
    matting_agent_pct: Optional[float] = None
    matting_agent_g: Optional[float] = None
    total_g: Optional[float] = None
    coating_maker: Optional[str] = None
    coating_code: Optional[str] = None
    coating_lot: Optional[str] = None
    pad_name: Optional[str] = None
    pad_hardness: Optional[str] = None
    source_file: Optional[str] = None
    print_color_sci: Optional[Dict[str, float]] = None
    print_color_sce: Optional[Dict[str, float]] = None
    delta_E_from_target: Optional[float] = None
    note: Optional[str] = None


class SampleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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

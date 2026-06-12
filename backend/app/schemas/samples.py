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


class LayerFields(BaseModel):
    """레이어 공통 필드. 입력/응답이 같은 필드를 공유해야
    RDP 메타데이터(rdp_key 등)가 샘플 수정 시 유실되지 않는다."""

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
    rdp_key: Optional[str] = None
    batch_no: Optional[str] = None
    is_base: Optional[bool] = None
    result: Optional[str] = None
    change_summary: Optional[str] = None
    target_color_sci: Optional[Dict[str, float]] = None
    target_color_sce: Optional[Dict[str, float]] = None
    # 저장 시점의 예측 믹스색과 실측 대비 ΔE — 예측↔실측 오차 데이터로
    # 축적해 추천/예측 엔진 보정(ML)에 활용한다
    predicted_color_sci: Optional[Dict[str, float]] = None
    prediction_error_delta_e: Optional[float] = None
    print_color_sci: Optional[Dict[str, float]] = None
    print_color_sce: Optional[Dict[str, float]] = None
    delta_E_from_target: Optional[float] = None
    note: Optional[str] = None


class LayerInput(LayerFields):
    pass


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


class LayerResponse(LayerFields):
    model_config = ConfigDict(from_attributes=True)


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

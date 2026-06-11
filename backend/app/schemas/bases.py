"""베이스 마스터 스키마 — 베이스 코드로 측색값을 불러오기 위한 마스터 데이터."""

from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class BaseMasterCreate(BaseModel):
    base_code: str = Field(..., min_length=1, max_length=100)
    base_name: Optional[str] = None
    material: Optional[str] = None
    color_sci: Optional[Dict[str, float]] = None
    color_sce: Optional[Dict[str, float]] = None
    maker: Optional[str] = None
    memo: Optional[str] = None


class BaseMasterUpdate(BaseModel):
    base_code: Optional[str] = Field(None, min_length=1, max_length=100)
    base_name: Optional[str] = None
    material: Optional[str] = None
    color_sci: Optional[Dict[str, float]] = None
    color_sce: Optional[Dict[str, float]] = None
    maker: Optional[str] = None
    memo: Optional[str] = None


class BaseMasterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    base_id: str
    base_code: str
    base_name: Optional[str] = None
    material: Optional[str] = None
    color_sci: Optional[Dict[str, float]] = None
    color_sce: Optional[Dict[str, float]] = None
    maker: Optional[str] = None
    memo: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

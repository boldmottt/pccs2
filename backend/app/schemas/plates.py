"""동판 마스터 스키마 — 차종 > 패턴 > 동판 > 배합비 계층의 동판."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class PlateCreate(BaseModel):
    pattern_id: str
    plate_code: str = Field(..., min_length=1, max_length=100)
    emboss_type: Optional[str] = None
    emboss_depth_um: Optional[int] = None
    memo: Optional[str] = None


class PlateUpdate(BaseModel):
    plate_code: Optional[str] = Field(None, min_length=1, max_length=100)
    emboss_type: Optional[str] = None
    emboss_depth_um: Optional[int] = None
    memo: Optional[str] = None


class PlateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    plate_id: str
    pattern_id: str
    plate_code: str
    emboss_type: Optional[str] = None
    emboss_depth_um: Optional[int] = None
    memo: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

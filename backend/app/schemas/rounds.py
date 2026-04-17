from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date


class RoundCreate(BaseModel):
    round_number: int = Field(..., ge=1)
    work_date: Optional[date] = None
    operator: Optional[str] = None
    work_location: Optional[str] = None


class RoundUpdate(BaseModel):
    round_number: Optional[int] = None
    work_date: Optional[date] = None
    operator: Optional[str] = None
    work_location: Optional[str] = None


class RoundResponse(BaseModel):
    round_id: str
    pattern_id: str
    round_number: int
    work_date: Optional[date]
    operator: Optional[str]
    work_location: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

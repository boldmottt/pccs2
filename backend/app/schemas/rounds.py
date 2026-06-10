from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime, date


class RoundCreate(BaseModel):
    work_date: Optional[date] = None
    operator: Optional[str] = None
    work_location: Optional[str] = None


class RoundUpdate(BaseModel):
    work_date: Optional[date] = None
    operator: Optional[str] = None
    work_location: Optional[str] = None


class RoundResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    round_id: str
    pattern_id: str
    round_number: int
    work_date: Optional[date]
    operator: Optional[str]
    work_location: Optional[str]
    created_at: datetime
    updated_at: datetime

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date


class ProjectStatusEnum(str):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    ON_HOLD = "ON_HOLD"


class ProjectCreate(BaseModel):
    project_name: str = Field(..., min_length=1, max_length=200)
    customer: Optional[str] = None
    start_date: Optional[date] = None
    target_completion: Optional[date] = None
    memo: Optional[str] = None


class ProjectUpdate(BaseModel):
    project_name: Optional[str] = None
    customer: Optional[str] = None
    status: Optional[str] = None
    target_completion: Optional[date] = None
    memo: Optional[str] = None


class ProjectResponse(BaseModel):
    project_id: str
    project_name: str
    customer: Optional[str]
    status: str
    start_date: Optional[date]
    target_completion: Optional[date]
    memo: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

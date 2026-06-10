from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime, date
from enum import Enum


class ProjectStatusEnum(str, Enum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    ON_HOLD = "ON_HOLD"


class ProjectCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    project_name: str = Field(..., min_length=1, max_length=200)
    customer: Optional[str] = None
    status: ProjectStatusEnum = ProjectStatusEnum.IN_PROGRESS
    start_date: Optional[date] = None
    target_completion: Optional[date] = None
    memo: Optional[str] = None


class ProjectUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    project_name: Optional[str] = Field(None, min_length=1, max_length=200)
    customer: Optional[str] = None
    status: Optional[ProjectStatusEnum] = None
    start_date: Optional[date] = None
    target_completion: Optional[date] = None
    memo: Optional[str] = None


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    project_id: str
    project_name: str
    customer: Optional[str]
    status: str
    start_date: Optional[date]
    target_completion: Optional[date]
    memo: Optional[str]
    created_at: datetime
    updated_at: datetime

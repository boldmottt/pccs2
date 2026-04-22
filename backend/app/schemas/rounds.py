from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime, date


class RoundCreate(BaseModel):
    """Schema for creating a new round.

    Note: pattern_id is provided via URL path, round_number is auto-incremented.
    """

    work_date: Optional[date] = None
    operator: Optional[str] = None
    work_location: Optional[str] = None


class RoundUpdate(BaseModel):
    """Schema for updating an existing round."""

    round_number: Optional[int] = None
    work_date: Optional[date] = None
    operator: Optional[str] = None
    work_location: Optional[str] = None


class RoundResponse(BaseModel):
    """Response schema for round data."""
    model_config = ConfigDict(
        from_attributes=True,
    )

    round_id: str
    pattern_id: str
    round_number: int
    work_date: Optional[date]
    operator: Optional[str]
    work_location: Optional[str]
    created_at: datetime
    updated_at: datetime

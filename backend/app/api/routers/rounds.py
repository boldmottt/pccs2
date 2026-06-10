from uuid import uuid4
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.models.domain import Pattern, Round
from app.schemas.rounds import RoundCreate, RoundUpdate, RoundResponse

router = APIRouter(prefix="/api/rounds", tags=["rounds"])


async def _get_round_or_404(round_id: str, db: AsyncSession) -> Round:
    round_ = await db.get(Round, round_id)
    if round_ is None:
        raise HTTPException(status_code=404, detail="Round not found")
    return round_


@router.get("/", response_model=List[RoundResponse])
async def list_rounds(
    pattern_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session),
):
    stmt = select(Round).order_by(Round.round_number.asc()).offset(skip).limit(limit)
    if pattern_id:
        stmt = stmt.where(Round.pattern_id == pattern_id)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/pattern/{pattern_id}", response_model=RoundResponse, status_code=201)
async def create_round(
    pattern_id: str,
    round_in: RoundCreate,
    db: AsyncSession = Depends(get_db_session),
):
    if await db.get(Pattern, pattern_id) is None:
        raise HTTPException(status_code=404, detail="Pattern not found")

    max_number = await db.scalar(
        select(func.coalesce(func.max(Round.round_number), 0)).where(Round.pattern_id == pattern_id)
    )

    db_round = Round(
        round_id=str(uuid4()),
        pattern_id=pattern_id,
        round_number=(max_number or 0) + 1,
        **round_in.model_dump(),
    )
    db.add(db_round)
    await db.commit()
    await db.refresh(db_round)
    return db_round


@router.get("/{round_id}", response_model=RoundResponse)
async def get_round(round_id: str, db: AsyncSession = Depends(get_db_session)):
    return await _get_round_or_404(round_id, db)


@router.put("/{round_id}", response_model=RoundResponse)
async def update_round(
    round_id: str,
    round_in: RoundUpdate,
    db: AsyncSession = Depends(get_db_session),
):
    db_round = await _get_round_or_404(round_id, db)
    for field, value in round_in.model_dump(exclude_unset=True).items():
        setattr(db_round, field, value)
    await db.commit()
    await db.refresh(db_round)
    return db_round


@router.delete("/{round_id}")
async def delete_round(round_id: str, db: AsyncSession = Depends(get_db_session)):
    db_round = await _get_round_or_404(round_id, db)
    await db.delete(db_round)
    await db.commit()
    return {"message": "Round deleted"}

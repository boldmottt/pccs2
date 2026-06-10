from uuid import uuid4
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.models.domain import Pattern, Project
from app.schemas.patterns import PatternCreate, PatternUpdate, PatternResponse

router = APIRouter(prefix="/api/patterns", tags=["patterns"])


async def _get_pattern_or_404(pattern_id: str, db: AsyncSession) -> Pattern:
    pattern = await db.get(Pattern, pattern_id)
    if pattern is None:
        raise HTTPException(status_code=404, detail="Pattern not found")
    return pattern


@router.get("/", response_model=List[PatternResponse])
async def list_patterns(
    project_id: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session),
):
    stmt = select(Pattern).order_by(Pattern.created_at.desc()).offset(skip).limit(limit)
    if project_id:
        stmt = stmt.where(Pattern.project_id == project_id)
    if status:
        stmt = stmt.where(Pattern.status == status)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/", response_model=PatternResponse, status_code=201)
async def create_pattern(pattern: PatternCreate, db: AsyncSession = Depends(get_db_session)):
    if await db.get(Project, pattern.project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")

    data = pattern.model_dump()
    db_pattern = Pattern(pattern_id=str(uuid4()), **data)
    db.add(db_pattern)
    await db.commit()
    await db.refresh(db_pattern)
    return db_pattern


@router.get("/{pattern_id}", response_model=PatternResponse)
async def get_pattern(pattern_id: str, db: AsyncSession = Depends(get_db_session)):
    return await _get_pattern_or_404(pattern_id, db)


@router.put("/{pattern_id}", response_model=PatternResponse)
async def update_pattern(
    pattern_id: str,
    pattern: PatternUpdate,
    db: AsyncSession = Depends(get_db_session),
):
    db_pattern = await _get_pattern_or_404(pattern_id, db)
    for field, value in pattern.model_dump(exclude_unset=True).items():
        setattr(db_pattern, field, value)
    await db.commit()
    await db.refresh(db_pattern)
    return db_pattern


@router.delete("/{pattern_id}")
async def delete_pattern(pattern_id: str, db: AsyncSession = Depends(get_db_session)):
    db_pattern = await _get_pattern_or_404(pattern_id, db)
    await db.delete(db_pattern)
    await db.commit()
    return {"message": "Pattern deleted"}

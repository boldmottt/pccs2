"""베이스 마스터 CRUD API — 코드만 입력하면 베이스 색상·소재를 불러올 수 있게."""

from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.models.domain import BaseMaster
from app.schemas.bases import BaseMasterCreate, BaseMasterUpdate, BaseMasterResponse

router = APIRouter(prefix="/api/bases", tags=["bases"])


async def _get_base_or_404(base_id: str, db: AsyncSession) -> BaseMaster:
    base = await db.get(BaseMaster, base_id)
    if base is None:
        raise HTTPException(status_code=404, detail="Base master not found")
    return base


async def _check_code_conflict(
    db: AsyncSession, base_code: str, exclude_id: Optional[str] = None
) -> None:
    stmt = select(BaseMaster).where(BaseMaster.base_code == base_code)
    if exclude_id:
        stmt = stmt.where(BaseMaster.base_id != exclude_id)
    existing = await db.scalar(stmt.limit(1))
    if existing:
        raise HTTPException(
            status_code=409, detail=f"이미 등록된 베이스 코드입니다: {base_code}"
        )


@router.get("/", response_model=List[BaseMasterResponse])
async def list_bases(
    q: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session),
):
    stmt = select(BaseMaster).order_by(BaseMaster.base_code.asc()).offset(skip).limit(limit)
    if q:
        stmt = stmt.where(BaseMaster.base_code.ilike(f"%{q}%"))
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/", response_model=BaseMasterResponse, status_code=201)
async def create_base(base: BaseMasterCreate, db: AsyncSession = Depends(get_db_session)):
    await _check_code_conflict(db, base.base_code)
    db_base = BaseMaster(base_id=str(uuid4()), **base.model_dump())
    db.add(db_base)
    await db.commit()
    await db.refresh(db_base)
    return db_base


@router.get("/{base_id}", response_model=BaseMasterResponse)
async def get_base(base_id: str, db: AsyncSession = Depends(get_db_session)):
    return await _get_base_or_404(base_id, db)


@router.put("/{base_id}", response_model=BaseMasterResponse)
async def update_base(
    base_id: str,
    update: BaseMasterUpdate,
    db: AsyncSession = Depends(get_db_session),
):
    db_base = await _get_base_or_404(base_id, db)
    data = update.model_dump(exclude_unset=True)
    if "base_code" in data and data["base_code"] != db_base.base_code:
        await _check_code_conflict(db, data["base_code"], exclude_id=base_id)
    for field, value in data.items():
        setattr(db_base, field, value)
    await db.commit()
    await db.refresh(db_base)
    return db_base


@router.delete("/{base_id}")
async def delete_base(base_id: str, db: AsyncSession = Depends(get_db_session)):
    db_base = await _get_base_or_404(base_id, db)
    await db.delete(db_base)
    await db.commit()
    return {"message": "Base master deleted"}

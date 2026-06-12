"""동판 마스터 CRUD API — 패턴에 종속, 배합 잉크가 동판에 종속될 수 있다."""

from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.models.domain import Ink, Pattern, Plate
from app.schemas.plates import PlateCreate, PlateUpdate, PlateResponse

router = APIRouter(prefix="/api/plates", tags=["plates"])


async def _get_plate_or_404(plate_id: str, db: AsyncSession) -> Plate:
    plate = await db.get(Plate, plate_id)
    if plate is None:
        raise HTTPException(status_code=404, detail="Plate not found")
    return plate


async def _check_code_conflict(
    db: AsyncSession, pattern_id: str, plate_code: str, exclude_id: Optional[str] = None
) -> None:
    stmt = (
        select(Plate)
        .where(Plate.pattern_id == pattern_id)
        .where(Plate.plate_code == plate_code)
    )
    if exclude_id:
        stmt = stmt.where(Plate.plate_id != exclude_id)
    if await db.scalar(stmt.limit(1)):
        raise HTTPException(
            status_code=409, detail=f"이 패턴에 이미 등록된 동판 코드입니다: {plate_code}"
        )


@router.get("/", response_model=List[PlateResponse])
async def list_plates(
    pattern_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 200,
    db: AsyncSession = Depends(get_db_session),
):
    stmt = select(Plate).order_by(Plate.plate_code.asc()).offset(skip).limit(limit)
    if pattern_id:
        stmt = stmt.where(Plate.pattern_id == pattern_id)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/", response_model=PlateResponse, status_code=201)
async def create_plate(plate: PlateCreate, db: AsyncSession = Depends(get_db_session)):
    pattern = await db.get(Pattern, plate.pattern_id)
    if pattern is None:
        raise HTTPException(status_code=404, detail="Pattern not found")
    await _check_code_conflict(db, plate.pattern_id, plate.plate_code)
    db_plate = Plate(plate_id=str(uuid4()), **plate.model_dump())
    db.add(db_plate)
    await db.commit()
    await db.refresh(db_plate)
    return db_plate


@router.get("/{plate_id}", response_model=PlateResponse)
async def get_plate(plate_id: str, db: AsyncSession = Depends(get_db_session)):
    return await _get_plate_or_404(plate_id, db)


@router.put("/{plate_id}", response_model=PlateResponse)
async def update_plate(
    plate_id: str,
    update: PlateUpdate,
    db: AsyncSession = Depends(get_db_session),
):
    db_plate = await _get_plate_or_404(plate_id, db)
    data = update.model_dump(exclude_unset=True)
    if "plate_code" in data and data["plate_code"] != db_plate.plate_code:
        await _check_code_conflict(db, db_plate.pattern_id, data["plate_code"], exclude_id=plate_id)
    for field, value in data.items():
        setattr(db_plate, field, value)
    await db.commit()
    await db.refresh(db_plate)
    return db_plate


@router.delete("/{plate_id}")
async def delete_plate(plate_id: str, db: AsyncSession = Depends(get_db_session)):
    db_plate = await _get_plate_or_404(plate_id, db)
    # 이 동판에 종속된 배합 잉크는 독립 배합으로 전환
    await db.execute(
        sa_update(Ink).where(Ink.plate_id == plate_id).values(plate_id=None)
    )
    await db.delete(db_plate)
    await db.commit()
    return {"message": "Plate deleted"}

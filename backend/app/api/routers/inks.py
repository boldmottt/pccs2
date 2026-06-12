from uuid import uuid4
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.models.domain import Ink
from app.schemas.inks import InkCreate, InkUpdate, InkResponse, RegisterBlendRequest
from app.services.color_math import calculate_delta_e_sci_sce, calculate_gloss_index

router = APIRouter(prefix="/api/inks", tags=["inks"])


async def _get_ink_or_404(ink_id: str, db: AsyncSession) -> Ink:
    ink = await db.get(Ink, ink_id)
    if ink is None:
        raise HTTPException(status_code=404, detail="Ink not found")
    return ink


def _apply_derived_color_fields(ink: Ink) -> None:
    """Derive delta_sci_sce and gloss_index when both SCI/SCE colors exist."""
    if ink.solid_color_sci and ink.solid_color_sce:
        ink.delta_sci_sce = calculate_delta_e_sci_sce(ink.solid_color_sci, ink.solid_color_sce)
        ink.gloss_index = calculate_gloss_index(ink.delta_sci_sce)
    else:
        ink.delta_sci_sce = None
        ink.gloss_index = None


@router.get("/", response_model=List[InkResponse])
async def list_inks(
    category: Optional[str] = None,
    is_blend: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session),
):
    stmt = select(Ink).order_by(Ink.ink_name.asc()).offset(skip).limit(limit)
    if category:
        stmt = stmt.where(Ink.ink_category == category)
    if is_blend is not None:
        stmt = stmt.where(Ink.is_blend_ink == is_blend)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/", response_model=InkResponse, status_code=201)
async def create_ink(ink: InkCreate, db: AsyncSession = Depends(get_db_session)):
    db_ink = Ink(ink_id=str(uuid4()), is_blend_ink=False, **ink.model_dump())
    _apply_derived_color_fields(db_ink)
    db.add(db_ink)
    await db.commit()
    await db.refresh(db_ink)
    return db_ink


@router.get("/{ink_id}", response_model=InkResponse)
async def get_ink(ink_id: str, db: AsyncSession = Depends(get_db_session)):
    return await _get_ink_or_404(ink_id, db)


@router.put("/{ink_id}", response_model=InkResponse)
async def update_ink(
    ink_id: str,
    ink: InkUpdate,
    db: AsyncSession = Depends(get_db_session),
):
    db_ink = await _get_ink_or_404(ink_id, db)
    for field, value in ink.model_dump(exclude_unset=True).items():
        setattr(db_ink, field, value)
    _apply_derived_color_fields(db_ink)
    await db.commit()
    await db.refresh(db_ink)
    return db_ink


@router.delete("/{ink_id}")
async def delete_ink(ink_id: str, db: AsyncSession = Depends(get_db_session)):
    db_ink = await _get_ink_or_404(ink_id, db)
    await db.delete(db_ink)
    await db.commit()
    return {"message": "Ink deleted"}


@router.post("/{ink_id}/register-blend", response_model=InkResponse)
async def register_blend_ink(
    ink_id: str,
    request: RegisterBlendRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Register a blend recipe as a master ink.

    If the ink exists it is converted to a blend master ink in place;
    otherwise a new master ink is created.
    """
    blend_recipe = request.blend_recipe or {}
    ink = await db.get(Ink, ink_id)

    if ink is None:
        if not request.ink_name:
            raise HTTPException(status_code=400, detail="ink_name is required to create a blend ink")
        ink = Ink(
            ink_id=str(uuid4()),
            ink_name=request.ink_name,
            ink_category=request.ink_category or "COLOR",
            manufacturer=request.manufacturer,
            is_blend_ink=True,
            blend_recipe=blend_recipe,
            plate_id=request.plate_id,
            solid_color_sci=blend_recipe.get("solid_color_sci"),
            solid_color_sce=blend_recipe.get("solid_color_sce"),
        )
        db.add(ink)
    else:
        ink.is_blend_ink = True
        ink.blend_recipe = blend_recipe
        if request.plate_id is not None:
            ink.plate_id = request.plate_id
        if request.ink_name:
            ink.ink_name = request.ink_name
        if request.ink_category:
            ink.ink_category = request.ink_category
        if request.manufacturer is not None:
            ink.manufacturer = request.manufacturer
        if blend_recipe.get("solid_color_sci"):
            ink.solid_color_sci = blend_recipe["solid_color_sci"]
        if blend_recipe.get("solid_color_sce"):
            ink.solid_color_sce = blend_recipe["solid_color_sce"]

    _apply_derived_color_fields(ink)
    await db.commit()
    await db.refresh(ink)
    return ink

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import JSONB
from uuid import uuid4

from app.database.session import get_db_session
from app.models.domain import Ink, InkCategory
from app.schemas.inks import InkCreate, InkUpdate, InkResponse


router = APIRouter(prefix="/api/inks", tags=["inks"])


def ink_to_response(ink: Ink) -> InkResponse:
    """Convert Ink model to InkResponse with JSON deserialization"""
    return InkResponse(
        ink_id=ink.ink_id,
        ink_name=ink.ink_name,
        ink_category=ink.ink_category,
        manufacturer=ink.manufacturer,
        is_blend_ink=ink.is_blend_ink,
        blend_recipe=ink.blend_recipe,
        solid_color_sci=ink.solid_color_sci,
        solid_color_sce=ink.solid_color_sce,
        delta_sci_sce=ink.delta_sci_sce,
        gloss_index=ink.gloss_index,
        gloss_GU=ink.gloss_GU,
        viscosity=ink.viscosity,
        density=ink.density,
        memo=ink.memo,
        registered_at=ink.registered_at,
        updated_at=ink.updated_at,
    )


@router.get("/", response_model=list[InkResponse])
async def list_inks(
    category: str = None,
    is_blend: bool = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session)
):
    """Get list of inks with optional filters"""
    query = select(Ink)

    if category:
        query = query.where(Ink.ink_category == category)
    if is_blend is not None:
        query = query.where(Ink.is_blend_ink == is_blend)

    query = query.order_by(Ink.ink_name).offset(skip).limit(limit)
    result = await db.execute(query)
    inks = result.scalars().all()

    return [ink_to_response(ink) for ink in inks]


@router.post("/", response_model=InkResponse)
async def create_ink(ink: InkCreate, db: AsyncSession = Depends(get_db_session)):
    """Create a new ink"""
    ink_id = str(uuid4())

    # Calculate delta if both color values provided
    delta_sci_sce = None
    if ink.solid_color_sci and ink.solid_color_sce:
        dl = ink.solid_color_sci["L"] - ink.solid_color_sce["L"]
        da = ink.solid_color_sci["a"] - ink.solid_color_sce["a"]
        db_val = ink.solid_color_sci["b"] - ink.solid_color_sce["b"]
        delta_sci_sce = (dl**2 + da**2 + db_val**2) ** 0.5

    db_ink = Ink(
        ink_id=ink_id,
        ink_name=ink.ink_name,
        ink_category=ink.ink_category if isinstance(ink.ink_category, str) else ink.ink_category.value,
        manufacturer=ink.manufacturer,
        is_blend_ink=False,
        solid_color_sci=ink.solid_color_sci,
        solid_color_sce=ink.solid_color_sce,
        delta_sci_sce=delta_sci_sce,
        gloss_GU=ink.gloss_GU,
        viscosity=ink.viscosity,
        density=ink.density,
        memo=ink.memo,
    )

    db.add(db_ink)
    await db.flush()
    await db.refresh(db_ink)

    return ink_to_response(db_ink)


@router.post("/{ink_id}/register-blend", response_model=InkResponse)
async def register_blend_ink(
    ink_id: str,
    request: dict,
    db: AsyncSession = Depends(get_db_session)
):
    """Register a blend recipe as a new master ink"""
    ink_name = request.get("ink_name")
    ink_category = request.get("ink_category")
    manufacturer = request.get("manufacturer")
    blend_recipe = request.get("blend_recipe")

    result = await db.execute(
        select(Ink).where(Ink.ink_id == ink_id)
    )
    db_ink = result.scalar_one_or_none()

    if not db_ink:
        # Create new
        new_ink_id = str(uuid4())
        db_ink = Ink(
            ink_id=new_ink_id,
            ink_name=ink_name,
            ink_category=ink_category,
            manufacturer=manufacturer,
            is_blend_ink=True,
            blend_recipe=blend_recipe,
            solid_color_sci=blend_recipe.get("solid_color_sci") if blend_recipe else None,
            solid_color_sce=blend_recipe.get("solid_color_sce") if blend_recipe else None,
        )
        db.add(db_ink)
        await db.flush()
        await db.refresh(db_ink)
    else:
        # Update existing
        db_ink.is_blend_ink = True
        db_ink.blend_recipe = blend_recipe
        db_ink.manufacturer = manufacturer

        await db.flush()
        await db.refresh(db_ink)

    return ink_to_response(db_ink)


@router.get("/{ink_id}", response_model=InkResponse)
async def get_ink(ink_id: str, db: AsyncSession = Depends(get_db_session)):
    """Get a specific ink by ID"""
    result = await db.execute(
        select(Ink).where(Ink.ink_id == ink_id)
    )
    db_ink = result.scalar_one_or_none()

    if not db_ink:
        raise HTTPException(status_code=404, detail="Ink not found")

    return ink_to_response(db_ink)


@router.put("/{ink_id}", response_model=InkResponse)
async def update_ink(
    ink_id: str,
    ink: InkUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    """Update an existing ink"""
    result = await db.execute(
        select(Ink).where(Ink.ink_id == ink_id)
    )
    db_ink = result.scalar_one_or_none()

    if not db_ink:
        raise HTTPException(status_code=404, detail="Ink not found")

    # Update only provided fields
    update_data = ink.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(db_ink, field, value)

    await db.flush()
    await db.refresh(db_ink)

    return ink_to_response(db_ink)


@router.delete("/{ink_id}")
async def delete_ink(ink_id: str, db: AsyncSession = Depends(get_db_session)):
    """Delete an ink by ID"""
    result = await db.execute(
        select(Ink).where(Ink.ink_id == ink_id)
    )
    db_ink = result.scalar_one_or_none()

    if not db_ink:
        raise HTTPException(status_code=404, detail="Ink not found")

    await db.delete(db_ink)
    await db.commit()

    return {"message": "Ink deleted"}

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4
from typing import List
from sqlalchemy import text

from app.database.session import get_db_session
from app.schemas.inks import InkCreate, InkUpdate, InkResponse

router = APIRouter(prefix="/api/inks", tags=["inks"])


@router.get("/", response_model=List[InkResponse])
async def list_inks(
    category: str = None,
    is_blend: bool = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session)
):
    where_clauses = []
    params = {"skip": skip, "limit": limit}

    if category:
        where_clauses.append("ink_category = :category")
        params["category"] = category
    if is_blend is not None:
        where_clauses.append("is_blend_ink = :is_blend")
        params["is_blend"] = is_blend

    where_sql = " AND ".join(where_clauses)
    where_sql = "WHERE " + where_sql if where_sql else ""

    stmt = text(f"""
        SELECT * FROM inks
        {where_sql}
        ORDER BY ink_name ASC
        LIMIT :limit OFFSET :skip
    """)
    result = await db.execute(stmt, params)
    rows = result.fetchall()
    return [InkResponse(**dict(row)) for row in rows]


@router.post("/", response_model=InkResponse)
async def create_ink(ink: InkCreate, db: AsyncSession = Depends(get_db_session)):
    ink_id = str(uuid4())

    # Calculate derived values if color data provided
    delta_sci_sce = None
    if ink.solid_color_sci and ink.solid_color_sce:
        dl = ink.solid_color_sci["L"] - ink.solid_color_sce["L"]
        da = ink.solid_color_sci["a"] - ink.solid_color_sce["a"]
        db_val = ink.solid_color_sci["b"] - ink.solid_color_sce["b"]
        delta_sci_sce = (dl**2 + da**2 + db_val**2) ** 0.5

    stmt = text("""
        INSERT INTO inks (
            ink_id, ink_name, ink_category, manufacturer, is_blend_ink,
            solid_color_sci, solid_color_sce, delta_sci_sce, gloss_GU,
            viscosity, density, memo, registered_at, updated_at
        )
        VALUES (
            :ink_id, :ink_name, :ink_category, :manufacturer, FALSE,
            :solid_color_sci, :solid_color_sce, :delta_sci_sce, :gloss_GU,
            :viscosity, :density, :memo, NOW(), NOW()
        )
        RETURNING *
    """)
    result = await db.execute(stmt, {
        "ink_id": ink_id,
        "ink_name": ink.ink_name,
        "ink_category": ink.ink_category.value if hasattr(ink.ink_category, 'value') else ink.ink_category,
        "manufacturer": ink.manufacturer,
        "solid_color_sci": ink.solid_color_sci,
        "solid_color_sce": ink.solid_color_sce,
        "delta_sci_sce": delta_sci_sce,
        "gloss_GU": ink.gloss_GU,
        "viscosity": ink.viscosity,
        "density": ink.density,
        "memo": ink.memo,
    })
    row = result.fetchone()
    return InkResponse(**dict(row))


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

    # Check if ink exists
    check_stmt = text("SELECT * FROM inks WHERE ink_id = :ink_id")
    result = await db.execute(check_stmt, {"ink_id": ink_id})
    row = result.fetchone()

    if not row:
        # Create new
        new_ink_id = str(uuid4())
        stmt = text("""
            INSERT INTO inks (
                ink_id, ink_name, ink_category, manufacturer, is_blend_ink,
                blend_recipe, solid_color_sci, solid_color_sce, registered_at, updated_at
            )
            VALUES (
                :ink_id, :ink_name, :ink_category, :manufacturer, TRUE,
                :blend_recipe, :solid_color_sci, :solid_color_sce, NOW(), NOW()
            )
            RETURNING *
        """)
        result = await db.execute(stmt, {
            "ink_id": new_ink_id,
            "ink_name": ink_name,
            "ink_category": ink_category,
            "manufacturer": manufacturer,
            "blend_recipe": blend_recipe,
            "solid_color_sci": blend_recipe.get("solid_color_sci") if blend_recipe else None,
            "solid_color_sce": blend_recipe.get("solid_color_sce") if blend_recipe else None,
        })
        row = result.fetchone()
    else:
        # Update existing
        update_stmt = text("""
            UPDATE inks
            SET is_blend_ink = TRUE, blend_recipe = :blend_recipe,
                manufacturer = :manufacturer, updated_at = NOW()
            WHERE ink_id = :ink_id
            RETURNING *
        """)
        result = await db.execute(update_stmt, {
            "ink_id": ink_id,
            "blend_recipe": blend_recipe,
            "manufacturer": manufacturer,
        })
        row = result.fetchone()

    return InkResponse(**dict(row))


@router.get("/{ink_id}", response_model=InkResponse)
async def get_ink(ink_id: str, db: AsyncSession = Depends(get_db_session)):
    stmt = text("SELECT * FROM inks WHERE ink_id = :ink_id")
    result = await db.execute(stmt, {"ink_id": ink_id})
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Ink not found")
    return InkResponse(**dict(row))


@router.put("/{ink_id}", response_model=InkResponse)
async def update_ink(
    ink_id: str,
    ink: InkUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    stmt_check = text("SELECT * FROM inks WHERE ink_id = :ink_id")
    result = await db.execute(stmt_check, {"ink_id": ink_id})
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Ink not found")

    update_fields = []
    params = {"ink_id": ink_id}
    for field, value in ink.model_dump(exclude_unset=True).items():
        if value is not None:
            update_fields.append(f"{field} = :{field}")
            params[field] = value.value if hasattr(value, 'value') else value

    if update_fields:
        stmt = text(f"""
            UPDATE inks
            SET {', '.join(update_fields)}, updated_at = NOW()
            WHERE ink_id = :ink_id
            RETURNING *
        """)
        result = await db.execute(stmt, params)
        row = result.fetchone()

    return InkResponse(**dict(row))


@router.delete("/{ink_id}")
async def delete_ink(ink_id: str, db: AsyncSession = Depends(get_db_session)):
    stmt = text("DELETE FROM inks WHERE ink_id = :ink_id")
    result = await db.execute(stmt, {"ink_id": ink_id})
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Ink not found")
    await db.commit()
    return {"message": "Ink deleted"}

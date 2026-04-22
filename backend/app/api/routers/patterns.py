from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from uuid import uuid4
from typing import List
from sqlalchemy import text
import json

from app.database.session import get_db_session
from app.schemas.patterns import PatternCreate, PatternUpdate, PatternResponse

router = APIRouter(prefix="/api/patterns", tags=["patterns"])


@router.get("/", response_model=List[PatternResponse])
async def list_patterns(
    project_id: str = None,
    status: str = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session)
):
    where_clauses = []
    params = {"skip": skip, "limit": limit}

    if project_id:
        where_clauses.append("project_id = :project_id")
        params["project_id"] = project_id
    if status:
        where_clauses.append("status = :status")
        params["status"] = status

    where_sql = " AND ".join(where_clauses)
    where_sql = "WHERE " + where_sql if where_sql else ""

    stmt = text(f"""
        SELECT * FROM patterns
        {where_sql}
        ORDER BY created_at DESC
        LIMIT :limit OFFSET :skip
    """)
    result = await db.execute(stmt, params)
    rows = result.fetchall()
    return [PatternResponse(**dict(row._mapping)) for row in rows]


@router.post("/", response_model=PatternResponse)
async def create_pattern(pattern: PatternCreate, db: AsyncSession = Depends(get_db_session)):
    pattern_id = str(uuid4())
    stmt = text("""
        INSERT INTO patterns (
            pattern_id, project_id, pattern_name, total_print_layers,
            target_base_color_sci, target_base_color_sce, target_base_material,
            status, notes, created_at, updated_at
        )
        VALUES (
            :pattern_id, :project_id, :pattern_name, :total_print_layers,
            :target_base_color_sci, :target_base_color_sce, :target_base_material,
            :status, :notes, NOW(), NOW()
        )
        RETURNING *
    """)
    try:
        result = await db.execute(stmt, {
            "pattern_id": pattern_id,
            "project_id": pattern.project_id,
            "pattern_name": pattern.pattern_name,
            "total_print_layers": pattern.total_print_layers,
            "target_base_color_sci": json.dumps(pattern.target_base_color_sci.model_dump()) if pattern.target_base_color_sci else None,
            "target_base_color_sce": json.dumps(pattern.target_base_color_sce.model_dump()) if pattern.target_base_color_sce else None,
            "target_base_material": pattern.target_base_material,
            "status": pattern.status or "DEVELOPING",
            "notes": pattern.notes,
        })
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=404, detail="Project not found")
    row = result.fetchone()
    return PatternResponse(**{key: getattr(row, key) for key in row._mapping.keys()})


@router.get("/{pattern_id}", response_model=PatternResponse)
async def get_pattern(pattern_id: str, db: AsyncSession = Depends(get_db_session)):
    stmt = text("SELECT * FROM patterns WHERE pattern_id = :pattern_id")
    result = await db.execute(stmt, {"pattern_id": pattern_id})
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Pattern not found")
    return PatternResponse(**{key: getattr(row, key) for key in row._mapping.keys()})


@router.put("/{pattern_id}", response_model=PatternResponse)
async def update_pattern(
    pattern_id: str,
    pattern: PatternUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    stmt_check = text("SELECT * FROM patterns WHERE pattern_id = :pattern_id")
    result = await db.execute(stmt_check, {"pattern_id": pattern_id})
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Pattern not found")

    update_fields = []
    params = {"pattern_id": pattern_id}
    for field, value in pattern.model_dump(exclude_unset=True).items():
        if value is not None:
            if field in ["target_base_color_sci", "target_base_color_sce"] and isinstance(value, dict):
                params[field] = json.dumps(value)
            elif hasattr(value, 'value'):
                params[field] = value.value
            else:
                params[field] = value
            update_fields.append(f"{field} = :{field}")

    if update_fields:
        stmt = text(f"""
            UPDATE patterns
            SET {', '.join(update_fields)}, updated_at = NOW()
            WHERE pattern_id = :pattern_id
            RETURNING *
        """)
        result = await db.execute(stmt, params)
        await db.commit()  # Added explicit commit
        row = result.fetchone()
    else:
        await db.commit()  # Added explicit commit for no-op case

    return PatternResponse(**{key: getattr(row, key) for key in row._mapping.keys()})


@router.delete("/{pattern_id}")
async def delete_pattern(pattern_id: str, db: AsyncSession = Depends(get_db_session)):
    stmt = text("DELETE FROM patterns WHERE pattern_id = :pattern_id")
    result = await db.execute(stmt, {"pattern_id": pattern_id})
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Pattern not found")
    await db.commit()
    return {"message": "Pattern deleted"}

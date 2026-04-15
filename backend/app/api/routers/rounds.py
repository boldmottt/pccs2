from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4
from typing import List
from sqlalchemy import text

from app.database.session import get_db_session
from app.schemas.rounds import RoundCreate, RoundUpdate, RoundResponse

router = APIRouter(prefix="/api/rounds", tags=["rounds"])


@router.get("/", response_model=List[RoundResponse])
async def list_rounds(
    pattern_id: str = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session)
):
    where_sql = "WHERE pattern_id = :pattern_id" if pattern_id else ""
    params = {"pattern_id": pattern_id, "skip": skip, "limit": limit} if pattern_id else {"skip": skip, "limit": limit}

    stmt = text(f"""
        SELECT * FROM rounds
        {where_sql}
        ORDER BY round_number ASC
        LIMIT :limit OFFSET :skip
    """)
    result = await db.execute(stmt, params)
    rows = result.fetchall()
    return [RoundResponse(**dict(row)) for row in rows]


@router.get("/pattern/{pattern_id}", response_model=List[RoundResponse])
async def get_pattern_rounds(pattern_id: str, db: AsyncSession = Depends(get_db_session)):
    stmt = text("SELECT * FROM rounds WHERE pattern_id = :pattern_id ORDER BY round_number ASC")
    result = await db.execute(stmt, {"pattern_id": pattern_id})
    rows = result.fetchall()
    return [RoundResponse(**dict(row)) for row in rows]


@router.post("/pattern/{pattern_id}", response_model=RoundResponse)
async def create_round(
    pattern_id: str,
    round_data: RoundCreate,
    db: AsyncSession = Depends(get_db_session)
):
    # Auto-increment round_number
    stmt_max = text("SELECT COALESCE(MAX(round_number), 0) FROM rounds WHERE pattern_id = :pattern_id")
    result = await db.execute(stmt_max, {"pattern_id": pattern_id})
    max_num = result.scalar() or 0

    round_id = str(uuid4())
    stmt = text("""
        INSERT INTO rounds (round_id, pattern_id, round_number, work_date, operator, work_location, created_at, updated_at)
        VALUES (:round_id, :pattern_id, :round_number, :work_date, :operator, :work_location, NOW(), NOW())
        RETURNING *
    """)
    result = await db.execute(stmt, {
        "round_id": round_id,
        "pattern_id": pattern_id,
        "round_number": max_num + 1,
        "work_date": round_data.work_date,
        "operator": round_data.operator,
        "work_location": round_data.work_location,
    })
    row = result.fetchone()
    return RoundResponse(**dict(row))


@router.get("/{round_id}", response_model=RoundResponse)
async def get_round(round_id: str, db: AsyncSession = Depends(get_db_session)):
    stmt = text("SELECT * FROM rounds WHERE round_id = :round_id")
    result = await db.execute(stmt, {"round_id": round_id})
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Round not found")
    return RoundResponse(**dict(row))


@router.put("/{round_id}", response_model=RoundResponse)
async def update_round(
    round_id: str,
    round_data: RoundUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    stmt_check = text("SELECT * FROM rounds WHERE round_id = :round_id")
    result = await db.execute(stmt_check, {"round_id": round_id})
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Round not found")

    update_fields = []
    params = {"round_id": round_id}
    for field, value in round_data.model_dump(exclude_unset=True).items():
        if value is not None:
            update_fields.append(f"{field} = :{field}")
            params[field] = value

    if update_fields:
        stmt = text(f"""
            UPDATE rounds
            SET {', '.join(update_fields)}, updated_at = NOW()
            WHERE round_id = :round_id
            RETURNING *
        """)
        result = await db.execute(stmt, params)
        row = result.fetchone()

    return RoundResponse(**dict(row))


@router.delete("/{round_id}")
async def delete_round(round_id: str, db: AsyncSession = Depends(get_db_session)):
    stmt = text("DELETE FROM rounds WHERE round_id = :round_id")
    result = await db.execute(stmt, {"round_id": round_id})
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Round not found")
    await db.commit()
    return {"message": "Round deleted"}

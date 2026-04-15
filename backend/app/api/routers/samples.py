from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4
from typing import List
from sqlalchemy import text

from app.database.session import get_db_session
from app.schemas.samples import SampleCreate, SampleUpdate, SampleResponse, LayerResponse, InkItem, CopyLayerRequest

router = APIRouter(prefix="/api/samples", tags=["samples"])


@router.get("/", response_model=List[SampleResponse])
async def list_samples(
    pattern_id: str = None,
    round_id: str = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session)
):
    where_clauses = []
    params = {"skip": skip, "limit": limit}

    if pattern_id:
        where_clauses.append("pattern_id = :pattern_id")
        params["pattern_id"] = pattern_id
    if round_id:
        where_clauses.append("round_id = :round_id")
        params["round_id"] = round_id

    where_sql = " AND ".join(where_clauses)
    where_sql = "WHERE " + where_sql if where_sql else ""

    stmt = text(f"""
        SELECT * FROM samples
        {where_sql}
        ORDER BY sample_number ASC
        LIMIT :limit OFFSET :skip
    """)
    result = await db.execute(stmt, params)
    rows = result.fetchall()

    response_list = []
    for row in rows:
        row_dict = dict(row)
        if row_dict.get("layers"):
            row_dict["layers"] = [
                LayerResponse(**l) if isinstance(l, dict) else l
                for l in row_dict["layers"]
            ]
        response_list.append(SampleResponse(**row_dict))
    return response_list


@router.get("/{sample_id}", response_model=SampleResponse)
async def get_sample(sample_id: str, db: AsyncSession = Depends(get_db_session)):
    stmt = text("SELECT * FROM samples WHERE sample_id = :sample_id")
    result = await db.execute(stmt, {"sample_id": sample_id})
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Sample not found")
    return SampleResponse(**dict(row))


@router.post("/round/{round_id}", response_model=SampleResponse)
async def create_sample(
    round_id: str,
    sample: SampleCreate,
    db: AsyncSession = Depends(get_db_session)
):
    # Get pattern_id from round
    round_stmt = text("SELECT pattern_id FROM rounds WHERE round_id = :round_id")
    round_result = await db.execute(round_stmt, {"round_id": round_id})
    round_row = round_result.fetchone()
    if not round_row:
        raise HTTPException(status_code=404, detail="Round not found")

    # Auto-increment sample_number
    num_stmt = text("SELECT COALESCE(MAX(sample_number), 0) FROM samples WHERE round_id = :round_id")
    num_result = await db.execute(num_stmt, {"round_id": round_id})
    max_num = num_result.scalar() or 0

    sample_id = str(uuid4())

    # Convert layers
    layers_data = []
    for layer in sample.layers:
        layers_data.append({
            "layer_number": layer.layer_number,
            "ink_items": [{"ink_id": i.ink_id, "amount": i.amount} for i in layer.ink_items],
            "thinner_pct": layer.thinner_pct,
            "hardener_pct": layer.hardener_pct,
            "print_color_sci": layer.print_color_sci,
            "print_color_sce": layer.print_color_sce,
            "delta_E_from_target": layer.delta_E_from_target,
            "note": layer.note,
        })

    stmt = text("""
        INSERT INTO samples (
            sample_id, round_id, pattern_id, sample_number,
            base_color_sci, base_color_sce, base_material, layers,
            created_at, updated_at
        )
        VALUES (
            :sample_id, :round_id, :pattern_id, :sample_number,
            :base_color_sci, :base_color_sce, :base_material, :layers,
            NOW(), NOW()
        )
        RETURNING *
    """)
    result = await db.execute(stmt, {
        "sample_id": sample_id,
        "round_id": round_id,
        "pattern_id": round_row.pattern_id,
        "sample_number": max_num + 1,
        "base_color_sci": sample.base_color_sci,
        "base_color_sce": sample.base_color_sce,
        "base_material": sample.base_material,
        "layers": layers_data,
    })
    row = result.fetchone()
    return SampleResponse(**dict(row))


@router.put("/{sample_id}", response_model=SampleResponse)
async def update_sample(
    sample_id: str,
    sample: SampleUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    stmt_check = text("SELECT * FROM samples WHERE sample_id = :sample_id")
    result = await db.execute(stmt_check, {"sample_id": sample_id})
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Sample not found")

    update_fields = []
    params = {"sample_id": sample_id}
    for field, value in sample.model_dump(exclude_unset=True).items():
        if value is not None:
            update_fields.append(f"{field} = :{field}")
            params[field] = value

    if update_fields:
        stmt = text(f"""
            UPDATE samples
            SET {', '.join(update_fields)}, updated_at = NOW()
            WHERE sample_id = :sample_id
            RETURNING *
        """)
        result = await db.execute(stmt, params)
        row = result.fetchone()

    return SampleResponse(**dict(row))


@router.delete("/{sample_id}")
async def delete_sample(sample_id: str, db: AsyncSession = Depends(get_db_session)):
    stmt = text("DELETE FROM samples WHERE sample_id = :sample_id")
    result = await db.execute(stmt, {"sample_id": sample_id})
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Sample not found")
    await db.commit()
    return {"message": "Sample deleted"}


@router.post("/{sample_id}/copy-layer", response_model=SampleResponse)
async def copy_layer(
    sample_id: str,
    request: CopyLayerRequest,
    db: AsyncSession = Depends(get_db_session)
):
    # Get source sample
    source_stmt = text("SELECT * FROM samples WHERE sample_id = :sample_id")
    source_result = await db.execute(source_stmt, {"sample_id": request.source_sample_id})
    source = source_result.fetchone()
    if not source:
        raise HTTPException(status_code=404, detail="Source sample not found")

    # Get target sample
    target_stmt = text("SELECT * FROM samples WHERE sample_id = :sample_id")
    target_result = await db.execute(target_stmt, {"sample_id": sample_id})
    target = target_result.fetchone()
    if not target:
        raise HTTPException(status_code=404, detail="Target sample not found")

    # Find layer to copy
    source_layers = source.layers or []
    layer_to_copy = None
    for layer in source_layers:
        if layer.get("layer_number") == request.layer_number:
            layer_to_copy = layer
            break

    if not layer_to_copy:
        raise HTTPException(status_code=404, detail=f"Layer {request.layer_number} not found")

    # Update target sample
    target_layers = target.layers or []
    found = False
    for i, layer in enumerate(target_layers):
        if layer.get("layer_number") == request.layer_number:
            target_layers[i] = layer_to_copy
            found = True
            break

    if not found:
        target_layers.append(layer_to_copy)

    target_layers.sort(key=lambda x: x.get("layer_number", 0))

    update_stmt = text("""
        UPDATE samples
        SET layers = :layers, updated_at = NOW()
        WHERE sample_id = :sample_id
        RETURNING *
    """)
    result = await db.execute(update_stmt, {"layers": target_layers, "sample_id": sample_id})
    updated = result.fetchone()
    return SampleResponse(**dict(updated))

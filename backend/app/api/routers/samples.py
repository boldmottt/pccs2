from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import uuid4

from app.database.session import get_db_session
from app.models.domain import Sample, Ink
from app.schemas.samples import SampleCreate, SampleUpdate, SampleResponse, CopyLayerRequest


router = APIRouter(prefix="/api/samples", tags=["samples"])


def sample_to_response(sample: Sample) -> SampleResponse:
    """Convert Sample model to SampleResponse"""
    # JSONB columns are automatically deserialized by SQLAlchemy
    return SampleResponse(
        sample_id=sample.sample_id,
        round_id=sample.round_id,
        pattern_id=sample.pattern_id,
        sample_number=sample.sample_number,
        base_color_sci=sample.base_color_sci,
        base_color_sce=sample.base_color_sce,
        base_material=sample.base_material,
        layers=sample.layers,
        final_delta_e=sample.final_delta_e,
        success_flag=sample.success_flag,
        success_notes=sample.success_notes,
        created_at=sample.created_at,
        updated_at=sample.updated_at,
    )


@router.get("/", response_model=list[SampleResponse])
async def list_samples(
    pattern_id: str = None,
    round_id: str = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session)
):
    """Get list of samples with optional filters"""
    query = select(Sample)

    if pattern_id:
        query = query.where(Sample.pattern_id == pattern_id)
    if round_id:
        query = query.where(Sample.round_id == round_id)

    query = query.order_by(Sample.sample_number).offset(skip).limit(limit)
    result = await db.execute(query)
    samples = result.scalars().all()

    return [sample_to_response(sample) for sample in samples]


@router.get("/{sample_id}", response_model=SampleResponse)
async def get_sample(sample_id: str, db: AsyncSession = Depends(get_db_session)):
    """Get a specific sample by ID"""
    result = await db.execute(
        select(Sample).where(Sample.sample_id == sample_id)
    )
    sample = result.scalar_one_or_none()

    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")

    return sample_to_response(sample)


@router.post("/round/{round_id}", response_model=SampleResponse)
async def create_sample(
    round_id: str,
    sample: SampleCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new sample"""
    from app.models.domain import Round

    # Get pattern_id from round
    result = await db.execute(
        select(Round.pattern_id).where(Round.round_id == round_id)
    )
    round_result = result.scalar_one_or_none()

    if not round_result:
        raise HTTPException(status_code=404, detail="Round not found")

    pattern_id = round_result

    # Auto-increment sample_number
    result = await db.execute(
        select(Sample).where(Sample.round_id == round_id)
        .order_by(Sample.sample_number.desc())
        .limit(1)
    )
    max_sample = result.scalar_one_or_none()
    max_num = max_sample.sample_number if max_sample else 0

    sample_id = str(uuid4())

    # Convert layers from schema to list of dicts
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

    db_sample = Sample(
        sample_id=sample_id,
        round_id=round_id,
        pattern_id=pattern_id,
        sample_number=max_num + 1,
        base_color_sci=sample.base_color_sci,
        base_color_sce=sample.base_color_sce,
        base_material=sample.base_material,
        layers=layers_data,
    )

    db.add(db_sample)
    await db.flush()
    await db.refresh(db_sample)

    return sample_to_response(db_sample)


@router.put("/{sample_id}", response_model=SampleResponse)
async def update_sample(
    sample_id: str,
    sample: SampleUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    """Update an existing sample"""
    result = await db.execute(
        select(Sample).where(Sample.sample_id == sample_id)
    )
    db_sample = result.scalar_one_or_none()

    if not db_sample:
        raise HTTPException(status_code=404, detail="Sample not found")

    # Update only provided fields
    update_data = sample.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(db_sample, field, value)

    await db.flush()
    await db.refresh(db_sample)

    return sample_to_response(db_sample)


@router.delete("/{sample_id}")
async def delete_sample(sample_id: str, db: AsyncSession = Depends(get_db_session)):
    """Delete a sample by ID"""
    result = await db.execute(
        select(Sample).where(Sample.sample_id == sample_id)
    )
    db_sample = result.scalar_one_or_none()

    if not db_sample:
        raise HTTPException(status_code=404, detail="Sample not found")

    await db.delete(db_sample)
    await db.commit()

    return {"message": "Sample deleted"}


@router.post("/{sample_id}/copy-layer", response_model=SampleResponse)
async def copy_layer(
    sample_id: str,
    request: CopyLayerRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """Copy a layer from one sample to another"""
    # Get source sample
    result = await db.execute(
        select(Sample).where(Sample.sample_id == request.source_sample_id)
    )
    source = result.scalar_one_or_none()

    if not source:
        raise HTTPException(status_code=404, detail="Source sample not found")

    # Get target sample
    result = await db.execute(
        select(Sample).where(Sample.sample_id == sample_id)
    )
    target = result.scalar_one_or_none()

    if not target:
        raise HTTPException(status_code=404, detail="Target sample not found")

    # Find layer to copy
    source_layers = source.layers or []
    layer_to_copy = None
    for layer in source_layers:
        if layer.get("layer_number") == request.source_layer_number:
            layer_to_copy = layer
            break

    if not layer_to_copy:
        raise HTTPException(
            status_code=404,
            detail=f"Layer {request.source_layer_number} not found in source sample"
        )

    # Update target sample
    target_layers = target.layers or []

    if request.target_layer_number is not None:
        # Find and replace existing layer at target position
        found = False
        for i, layer in enumerate(target_layers):
            if layer.get("layer_number") == request.target_layer_number:
                target_layers[i] = layer_to_copy.copy()  # shallow copy of dict
                found = True
                break

        if not found:
            raise HTTPException(
                status_code=404,
                detail=f"Target layer {request.target_layer_number} not found in target sample"
            )
    else:
        # No target specified — append as new layer with next available number
        existing_numbers = {l.get("layer_number", 0) for l in target_layers}
        next_num = 1
        while next_num in existing_numbers:
            next_num += 1
        copied_layer = layer_to_copy.copy()
        copied_layer["layer_number"] = next_num
        target_layers.append(copied_layer)

    target_layers.sort(key=lambda x: x.get("layer_number", 0))

    target.layers = target_layers
    await db.flush()
    await db.refresh(target)

    return sample_to_response(target)

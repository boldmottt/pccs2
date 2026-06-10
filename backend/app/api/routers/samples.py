from uuid import uuid4
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.database.session import get_db_session
from app.models.domain import Round, Sample
from app.schemas.samples import (
    CopyLayerRequest,
    SampleCreate,
    SampleUpdate,
    SampleResponse,
)

router = APIRouter(prefix="/api/samples", tags=["samples"])


async def _get_sample_or_404(sample_id: str, db: AsyncSession) -> Sample:
    sample = await db.get(Sample, sample_id)
    if sample is None:
        raise HTTPException(status_code=404, detail="Sample not found")
    return sample


def _layers_to_json(layers) -> list:
    return [layer.model_dump() for layer in layers]


@router.get("/", response_model=List[SampleResponse])
async def list_samples(
    pattern_id: Optional[str] = None,
    round_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session),
):
    stmt = select(Sample).order_by(Sample.created_at.desc()).offset(skip).limit(limit)
    if pattern_id:
        stmt = stmt.where(Sample.pattern_id == pattern_id)
    if round_id:
        stmt = stmt.where(Sample.round_id == round_id)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/round/{round_id}", response_model=SampleResponse, status_code=201)
async def create_sample(
    round_id: str,
    sample: SampleCreate,
    db: AsyncSession = Depends(get_db_session),
):
    round_ = await db.get(Round, round_id)
    if round_ is None:
        raise HTTPException(status_code=404, detail="Round not found")

    max_number = await db.scalar(
        select(func.coalesce(func.max(Sample.sample_number), 0)).where(Sample.round_id == round_id)
    )

    db_sample = Sample(
        sample_id=str(uuid4()),
        round_id=round_id,
        pattern_id=round_.pattern_id,
        sample_number=(max_number or 0) + 1,
        base_color_sci=sample.base_color_sci,
        base_color_sce=sample.base_color_sce,
        base_material=sample.base_material,
        layers=_layers_to_json(sample.layers),
        success_flag=sample.success_flag,
    )
    db.add(db_sample)
    await db.commit()
    await db.refresh(db_sample)
    return db_sample


@router.get("/{sample_id}", response_model=SampleResponse)
async def get_sample(sample_id: str, db: AsyncSession = Depends(get_db_session)):
    return await _get_sample_or_404(sample_id, db)


@router.put("/{sample_id}", response_model=SampleResponse)
async def update_sample(
    sample_id: str,
    sample: SampleUpdate,
    db: AsyncSession = Depends(get_db_session),
):
    db_sample = await _get_sample_or_404(sample_id, db)
    for field, value in sample.model_dump(exclude_unset=True).items():
        setattr(db_sample, field, value)
    await db.commit()
    await db.refresh(db_sample)
    return db_sample


@router.delete("/{sample_id}")
async def delete_sample(sample_id: str, db: AsyncSession = Depends(get_db_session)):
    db_sample = await _get_sample_or_404(sample_id, db)
    await db.delete(db_sample)
    await db.commit()
    return {"message": "Sample deleted"}


@router.post("/{sample_id}/copy-layer", response_model=SampleResponse)
async def copy_layer(
    sample_id: str,
    request: CopyLayerRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Copy a layer recipe from a source sample into this sample."""
    target = await _get_sample_or_404(sample_id, db)

    source = await db.get(Sample, request.source_sample_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source sample not found")

    source_layer = next(
        (
            layer for layer in (source.layers or [])
            if layer.get("layer_number") == request.source_layer_number
        ),
        None,
    )
    if source_layer is None:
        raise HTTPException(
            status_code=404,
            detail=f"Layer {request.source_layer_number} not found in source sample",
        )

    copied = dict(source_layer)
    copied["layer_number"] = request.target_layer_number

    target_layers = list(target.layers or [])
    for i, layer in enumerate(target_layers):
        if layer.get("layer_number") == request.target_layer_number:
            target_layers[i] = copied
            break
    else:
        target_layers.append(copied)
    target_layers.sort(key=lambda layer: layer.get("layer_number", 0))

    target.layers = target_layers
    flag_modified(target, "layers")
    await db.commit()
    await db.refresh(target)
    return target

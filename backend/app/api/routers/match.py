from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4
from typing import List

from app.database.session import get_db_session
from app.schemas.match import MatchRequest, MatchResponse, RecommendedRecipe, InkItemForMatch

router = APIRouter(prefix="/api/match", tags=["match"])


@router.post("/", response_model=MatchResponse)
async def recommend_recipe(request: MatchRequest, db: AsyncSession = Depends(get_db_session)):
    # TODO: Implement 1-stage K-M engine
    # TODO: Implement 2-stage ML engine
    # For now, return placeholder

    return MatchResponse(
        result_id=str(uuid4()),
        pattern_id=request.pattern_id,
        recommended_recipes=[],
        engine_used="STAGE1_ONLY",
        model_version="1.0.0"
    )

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.models.domain import Ink, Pattern
from app.schemas.match import MatchRequest, MatchResponse
from app.services.recipe_matcher import recommend_recipes

router = APIRouter(prefix="/api/match", tags=["match"])


@router.post("/", response_model=MatchResponse)
async def match_recipe(request: MatchRequest, db: AsyncSession = Depends(get_db_session)):
    """Recommend ink blend recipes for the requested target color."""
    if await db.get(Pattern, request.pattern_id) is None:
        raise HTTPException(status_code=404, detail="Pattern not found")

    result = await db.execute(select(Ink))
    inks = [
        {
            "ink_id": ink.ink_id,
            "ink_category": ink.ink_category,
            "solid_color_sci": ink.solid_color_sci,
        }
        for ink in result.scalars().all()
    ]

    recipes = recommend_recipes(
        target_color=request.target_color,
        inks=inks,
        exclude_inks=request.exclude_inks,
        max_components=request.max_components,
    )

    return MatchResponse(
        result_id=str(uuid4()),
        pattern_id=request.pattern_id,
        recommended_recipes=recipes,
        engine_used="STAGE1_KM",
        model_version="1.0.0",
    )

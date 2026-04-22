from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.session import get_db_session
from app.models.domain import Ink
from app.schemas.match import MatchRequest, MatchResponse, RecipeResult
from app.services.match_engine import match_engine


router = APIRouter(prefix="/api/match", tags=["match"])


@router.post("/", response_model=MatchResponse)
async def match_recipe(
    request: MatchRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Find best ink recipes to match target color.

    1. Fetch all available inks with k_over_s from DB
    2. Call match_engine.recommend() to find best combinations
    3. Return ranked recipes with predicted colors and Delta E
    """
    # Fetch all inks from DB that have k_over_s > 0
    result = await db.execute(
        select(Ink).where(Ink.k_over_s > 0)
    )
    inks = result.scalars().all()

    if not inks:
        return MatchResponse(
            target_color=request.target_color,
            base_color=request.base_color,
            recipes=[],
            message="No inks with K/S values found. Register inks first.",
        )

    # Convert to dict format expected by MatchEngine
    available_inks = []
    for ink in inks:
        available_inks.append({
            "ink_id": ink.ink_id,
            "ink_name": ink.ink_name,
            "k_over_s": ink.k_over_s,
            "solid_color_sci": ink.solid_color_sci,
        })

    # Call the engine
    recipes = match_engine.recommend(
        target_color=request.target_color,
        available_inks=available_inks,
        base_color=request.base_color,
        max_components=request.max_components,
        max_results=request.max_results,
        exclude_ink_ids=request.exclude_ink_ids,
    )

    # Build response
    recipe_results = [
        RecipeResult(
            rank=r["rank"],
            recipe=r["recipe"],
            suggested_thinner_ratio=r["suggested_thinner_ratio"],
            predicted_color=r["predicted_color"],
            predicted_delta_E=r["predicted_delta_E"],
            confidence_score=r["confidence_score"],
        )
        for r in recipes
    ]

    return MatchResponse(
        target_color=request.target_color,
        base_color=request.base_color or {"L": 95.0, "a": 0.0, "b": 0.0},
        recipes=recipe_results,
    )

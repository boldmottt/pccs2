from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import uuid4

from app.database.session import get_db_session
from app.models.domain import Ink, Pattern
from app.schemas.match import MatchRequest, MatchResponse, RecommendedRecipe, InkItemForMatch
from app.services.match_engine import match_engine


router = APIRouter(prefix="/api/match", tags=["match"])


@router.post("/", response_model=MatchResponse)
async def match_recipe(
    request: MatchRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Find best ink recipes to match target color.

    1. Look up pattern's target_base_color_sci if target_color not provided
    2. Fetch all available inks with k_over_s from DB
    3. Call match_engine.recommend() to find best combinations
    4. Return ranked recipes with predicted colors and Delta E
    """
    # Resolve target_color: from request or from pattern
    result_id = str(uuid4())

    # Look up pattern to get target color if not provided
    pattern_result = await db.execute(
        select(Pattern).where(Pattern.pattern_id == request.pattern_id)
    )
    pattern = pattern_result.scalar_one_or_none()

    if not pattern:
        raise HTTPException(status_code=404, detail="Pattern not found")

    # Use request target_color if provided, otherwise from pattern
    target_color = request.target_color or pattern.target_base_color_sci

    if not target_color:
        return MatchResponse(
            result_id=result_id,
            pattern_id=request.pattern_id,
            target_color_used={},
            base_color_used={"L": 95.0, "a": 0.0, "b": 0.0},
            recommended_recipes=[],
            available_inks_count=0,
        )

    # Default base_color to white if not provided
    base_color = request.base_color or {"L": 95.0, "a": 0.0, "b": 0.0}

    # Fetch all inks from DB that have k_over_s > 0
    result = await db.execute(
        select(Ink).where(Ink.k_over_s > 0)
    )
    inks = result.scalars().all()

    if not inks:
        return MatchResponse(
            result_id=result_id,
            pattern_id=request.pattern_id,
            target_color_used=target_color,
            base_color_used=base_color,
            recommended_recipes=[],
            available_inks_count=0,
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

    # Call the engine with defaults for Optional fields
    recipes = match_engine.recommend(
        target_color=target_color,
        available_inks=available_inks,
        base_color=base_color,
        max_components=request.max_components or 3,
        max_results=request.max_results or 5,
        exclude_ink_ids=request.exclude_inks,
    )

    # Build response with InkItemForMatch for each recipe item
    recommended_recipes = []
    for r in recipes:
        recipe_items = [
            InkItemForMatch(
                ink_id=item["ink_id"],
                ink_name=item.get("ink_name", ""),
                amount=item["amount"],
            )
            for item in r["recipe"]
        ]

        recommended_recipes.append(RecommendedRecipe(
            rank=r["rank"],
            recipe=recipe_items,
            suggested_thinner_ratio=r["suggested_thinner_ratio"],
            predicted_color=r["predicted_color"],
            predicted_delta_E=r["predicted_delta_E"],
            confidence_score=r["confidence_score"],
        ))

    return MatchResponse(
        result_id=result_id,
        pattern_id=request.pattern_id,
        target_color_used=target_color,
        base_color_used=base_color,
        recommended_recipes=recommended_recipes,
        available_inks_count=len(available_inks),
    )

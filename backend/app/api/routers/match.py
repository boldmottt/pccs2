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
async def recommend_recipe(
    request: MatchRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Get recipe recommendations for a target color.

    Workflow:
    1. Look up pattern to get target color (if not provided in request)
    2. Fetch all inks with k_over_s values from DB
    3. Run match engine to find best ink combinations
    4. Return ranked recommendations
    """

    # Step 1: Resolve target color
    target_color = request.target_color

    if target_color is None:
        # Fetch from pattern
        result = await db.execute(
            select(Pattern).where(Pattern.pattern_id == request.pattern_id)
        )
        pattern = result.scalar_one_or_none()

        if not pattern:
            raise HTTPException(
                status_code=404,
                detail=f"Pattern '{request.pattern_id}' not found",
            )

        if pattern.target_base_color_sci:
            target_color = pattern.target_base_color_sci
        else:
            raise HTTPException(
                status_code=400,
                detail="Pattern has no target_base_color_sci. Please provide target_color in request.",
            )

    # Validate target_color has L, a, b
    if "L" not in target_color or "a" not in target_color or "b" not in target_color:
        raise HTTPException(
            status_code=400,
            detail="target_color must contain L, a, b keys",
        )

    # Step 2: Resolve base color
    base_color = request.base_color
    if base_color is None:
        base_color = {"L": 95.0, "a": 0.0, "b": 0.0}

    # Step 3: Fetch inks with k_over_s from DB
    query = select(Ink).where(Ink.k_over_s.isnot(None))
    result = await db.execute(query)
    db_inks = result.scalars().all()

    # Convert to dicts for match engine
    available_inks = []
    for ink in db_inks:
        available_inks.append({
            "ink_id": ink.ink_id,
            "ink_name": ink.ink_name,
            "k_over_s": ink.k_over_s,
            "solid_color_sci": ink.solid_color_sci,
            "solid_color_sce": ink.solid_color_sce,
            "ink_category": ink.ink_category,
        })

    if not available_inks:
        raise HTTPException(
            status_code=400,
            detail="No inks with K/S data found. Please register inks with k_over_s values first.",
        )

    # Step 4: Run match engine
    try:
        recommendations = match_engine.recommend(
            target_color=target_color,
            available_inks=available_inks,
            base_color=base_color,
            max_components=request.max_components,
            max_results=request.max_results,
            exclude_ink_ids=request.exclude_inks,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Match engine error: {str(e)}",
        )

    # Step 5: Convert to response schema
    recommended_recipes = []
    for rec in recommendations:
        recommended_recipes.append(
            RecommendedRecipe(
                rank=rec["rank"],
                recipe=[
                    InkItemForMatch(
                        ink_id=item["ink_id"],
                        ink_name=item.get("ink_name", ""),
                        amount=item["amount"],
                    )
                    for item in rec["recipe"]
                ],
                suggested_thinner_ratio=rec["suggested_thinner_ratio"],
                predicted_color=rec["predicted_color"],
                predicted_delta_E=rec["predicted_delta_E"],
                confidence_score=rec["confidence_score"],
            )
        )

    return MatchResponse(
        result_id=str(uuid4()),
        pattern_id=request.pattern_id,
        target_color_used=target_color,
        base_color_used=base_color,
        recommended_recipes=recommended_recipes,
        engine_used="KM_GRID_SEARCH",
        model_version="1.0.0",
        available_inks_count=len(available_inks),
    )

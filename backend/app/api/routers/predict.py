"""Prediction API endpoints for K-M + ML engine."""

from fastapi import APIRouter, HTTPException
from app.schemas.predict import (
    PredictRequest,
    PredictResponse,
    TrainRequest,
    TrainResponse,
    HealthResponse,
)
from app.services.color_math import lab_to_reflectance
from app.services.hybrid_engine import hybrid_engine

router = APIRouter(prefix="/api/predict", tags=["prediction"])


@router.post("/", response_model=PredictResponse)
async def predict_recipe(request: PredictRequest):
    """Predict color for given recipe using hybrid K-M + ML engine.

    Takes a recipe with layers and base color, runs K-M prediction,
    applies ML correction if trained, and returns the final prediction.

    Args:
        request: PredictRequest with recipe and base_color

    Returns:
        PredictResponse with km_prediction, ml_correction, ml_confidence,
        final_prediction, and delta_E

    Raises:
        HTTPException: If prediction fails due to invalid input
    """
    try:
        # Build engine-compatible recipe from request
        # Accept either k_over_s directly or convert from ink_items
        engine_recipe = {
            "layers": [],
            "thinner_amount": request.recipe.thinner_amount,
            "hardener_amount": request.recipe.hardener_amount,
        }

        for layer in request.recipe.layers:
            # Use k_over_s directly if provided, otherwise calculate from ink_items
            layer_k_over_s = layer.k_over_s

            # If no k_over_s provided but ink_items exist, try to extract k_over_s
            # from ink_items dicts (they might already contain k_over_s values)
            if layer_k_over_s is None and layer.ink_items:
                # Assume ink_items might contain k_over_s values directly
                k_over_s_sum = 0.0
                for ink_item in layer.ink_items:
                    if isinstance(ink_item, dict) and "k_over_s" in ink_item:
                        k_over_s_sum += ink_item["k_over_s"]
                layer_k_over_s = k_over_s_sum

            # If still no k_over_s, default to 0 (no ink effect)
            if layer_k_over_s is None:
                layer_k_over_s = 0.0

            engine_recipe["layers"].append({
                "k_over_s": layer_k_over_s,
                "thickness": layer.thickness,
            })

        # Run prediction. The K-M engine needs the substrate reflectance
        # (R_inf), which is derived from the Lab lightness here so callers
        # only ever supply {L, a, b}.
        base_color = dict(request.base_color)
        base_color.setdefault("R_inf", lab_to_reflectance(base_color))
        result = hybrid_engine.predict(engine_recipe, base_color)

        return PredictResponse(
            km_prediction=result["km_prediction"],
            ml_correction=result["ml_correction"],
            ml_confidence=result["ml_confidence"],
            final_prediction=result["final_prediction"],
            delta_E=result["delta_E"],
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Prediction failed: {str(e)}",
        )


@router.post("/train", response_model=TrainResponse)
async def train_model(request: TrainRequest):
    """Train ML model on historical data.

    Takes historical recipe data with K-M predictions and actual measurements,
    trains the ML correction model, and returns training statistics.

    Args:
        request: TrainRequest with historical_data

    Returns:
        TrainResponse with samples_trained and model_scores (R^2 for L, a, b)

    Raises:
        HTTPException: If training fails due to invalid data
    """
    # Check for empty data BEFORE any other processing
    if not request.historical_data:
        raise HTTPException(
            status_code=400,
            detail="Historical data is required for training",
        )

    try:
        result = hybrid_engine.train(request.historical_data)

        return TrainResponse(
            samples_trained=result["samples_trained"],
            model_scores=result["model_scores"],
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Training failed: {str(e)}",
        )


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Check engine health and training status.

    Returns the current state of the hybrid engine including whether
    the ML model has been trained and how many samples are stored.

    Returns:
        HealthResponse with status, engine name, version, ml_trained flag,
        and samples_count
    """
    # Check if ML engine is trained
    ml_trained = hybrid_engine.ml_engine.is_trained
    samples_count = len(hybrid_engine._training_data)

    return HealthResponse(
        status="healthy" if ml_trained else "healthy_untrained",
        engine="hybrid_km_ml",
        version="1.0",
        ml_trained=ml_trained,
        samples_count=samples_count,
    )

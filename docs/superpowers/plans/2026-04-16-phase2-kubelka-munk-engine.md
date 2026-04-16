# Kubelka-Munk Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement 1-stage Kubelka-Munk physical model engine for color prediction and 2-stage ML correction engine

**Architecture:** Pure Python implementation using scipy for numerical optimization, integrated with existing blend_processor and color_math services

**Tech Stack:** Python, NumPy, SciPy, scikit-learn

---

## Phase 2A: Kubelka-Munk Physical Model

### Task 2.1: Implement S/M Calculator

**Files:**
- Create: `app/services/kubelka_munk.py`

- [ ] **Step 1: Write S/M calculation tests**

```python
import pytest
from app.services.kubelka_munk import calculate_km_coefficients

def test_km_coefficients_from_absorption_scattering():
    """Test S/M calculation from K and S values."""
    result = calculate_km_coefficients(K=0.5, S=1.0)
    assert result["K_over_S"] == 0.5

def test_km_coefficients_edge_cases():
    """Test S/M with zero scattering."""
    with pytest.raises(ValueError):
        calculate_km_coefficients(K=0.5, S=0.0)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_kubelka_munk.py::test_km_coefficients_from_absorption_scattering -v`
Expected: FAIL with "function not defined"

- [ ] **Step 3: Write minimal S/M implementation**

```python
def calculate_km_coefficients(K: float, S: float) -> Dict[str, float]:
    """Calculate K/S ratio from Kubelka-Munk coefficients."""
    if S == 0:
        raise ValueError("Scattering coefficient S cannot be zero")
    return {"K_over_S": K / S}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_kubelka_munk.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/services/kubelka_munk.py tests/test_kubelka_munk.py
git commit -m "feat: add K/S coefficient calculator"
```

### Task 2.2: Implement Reflectance Calculation

**Files:**
- Create: `app/services/kubelka_munk.py` (extend)
- Test: `tests/test_kubelka_munk.py` (extend)

- [ ] **Step 1: Write reflectance tests**

```python
def test_reflectance_infinite_bed():
    """Test R_infinity calculation."""
    K_over_S = 1.0
    result = calculate_reflectance_infinite(K_over_S)
    expected = (1 + K_over_S - (K_over_S**2 + 2*K_over_S)**0.5) / K_over_S
    assert abs(result - expected) < 0.001

def test_reflectance_zero_absorption():
    """Test when K=0, R_infinity should be 1."""
    result = calculate_reflectance_infinite(0.0)
    assert result == 1.0
```

- [ ] **Step 2-5:** Implement and commit

```python
def calculate_reflectance_infinite(K_over_S: float) -> float:
    """Calculate reflectance for infinite backing."""
    if K_over_S == 0:
        return 1.0
    a = 1 + K_over_S
    b = (K_over_S**2 + 2 * K_over_S) ** 0.5
    return (a - b) / K_over_S
```

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: add R_infinity calculation"
```

### Task 2.3: Implement Layer Prediction

**Files:**
- Create: `app/services/kubelka_munk_engine.py`
- Test: `tests/test_km_engine.py`

- [ ] **Step 1: Write layer prediction tests**

```python
def test_single_layer_prediction():
    """Test single layer color prediction."""
    layers = [{
        "ink_items": [{"ink_id": "red", "amount": 100}],
        "thickness": 1.0
    }]
    base_color = {"L": 100, "a": 0, "b": 0}
    result = predict_layer_color(layers, base_color)
    assert "L" in result
    assert "a" in result
    assert "b" in result

def test_multiple_layers():
    """Test multi-layer prediction."""
    layers = [
        {"ink_items": [{"ink_id": "white", "amount": 100}], "thickness": 1.0},
        {"ink_items": [{"ink_id": "red", "amount": 50}], "thickness": 1.0}
    ]
    base_color = {"L": 100, "a": 0, "b": 0}
    result = predict_layer_color(layers, base_color)
    # Second layer should modify first layer's effect
```

- [ ] **Step 2-5:** Implement and commit

```python
class KubelkaMunkEngine:
    """1-stage K-M physical model engine."""

    @staticmethod
    def predict_layer_color(layers: List[Dict], base_color: Dict) -> Dict[str, float]:
        """Predict final color through layered application."""
        current_color = base_color.copy()

        for layer in layers:
            # Calculate K/S for each ink in layer
            layer_km = KubelkaMunkEngine._calculate_layer_km(layer["ink_items"])

            # Combine layers using adding-up formula
            current_color = KubelkaMunkEngine._combine_layers(
                current_color, layer_km, layer["thickness"]
            )

        return current_color

    @staticmethod
    def _calculate_layer_km(ink_items: List[Dict]) -> Dict:
        """Calculate combined K/S for a layer."""
        pass  # Implement weighted average

    @staticmethod
    def _combine_layers(color1: Dict, color2: Dict, thickness: float) -> Dict:
        """Combine two layers using K-M adding-up formula."""
        pass  # Implement recursive adding-up
```

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: implement layer color prediction"
```

### Task 2.4: Implement Full Recipe Prediction

**Files:**
- Extend: `app/services/kubelka_munk_engine.py`

- [ ] **Step 1: Write full recipe tests**

```python
def test_full_recipe_prediction():
    """Test complete recipe to final color prediction."""
    recipe = {
        "layers": [
            {"ink_items": [{"ink_id": "base", "amount": 100}], "thickness": 1.0}
        ]
    }
    base_color = {"L": 100, "a": 0, "b": 0}
    result = KubelkaMunkEngine.predict_recipe(recipe, base_color)
    assert "predicted_color" in result
    assert "delta_E" in result

def test_recipe_with_multiple_layers():
    """Test 2-layer recipe prediction."""
    recipe = {
        "layers": [
            {"ink_items": [{"ink_id": "white", "amount": 100}], "thickness": 1.0},
            {"ink_items": [{"ink_id": "red", "amount": 50}], "thickness": 1.0}
        ]
    }
    base_color = {"L": 100, "a": 0, "b": 0}
    result = KubelkaMunkEngine.predict_recipe(recipe, base_color)
    assert len(result["layer_predictions"]) == 2
```

- [ ] **Step 2-5:** Implement and commit

```python
class KubelkaMunkEngine:
    @staticmethod
    def predict_recipe(recipe: Dict, base_color: Dict) -> Dict:
        """Predict final color for complete recipe."""
        layer_predictions = []

        for i, layer in enumerate(recipe["layers"]):
            predicted = KubelkaMunkEngine.predict_layer_color([layer], base_color)
            layer_predictions.append({
                "layer_number": i + 1,
                "predicted_color": predicted
            })

        final_color = layer_predictions[-1]["predicted_color"]

        return {
            "predicted_color": final_color,
            "layer_predictions": layer_predictions,
            "delta_E": calculate_delta_e_76(base_color, final_color)
        }
```

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: implement full recipe prediction"
```

## Phase 2B: ML Correction Engine

### Task 2.5: Implement ML Model Interface

**Files:**
- Create: `app/services/ml_correction_engine.py`
- Test: `tests/test_ml_engine.py`

- [ ] **Step 1: Write ML interface tests**

```python
def test_ml_engine_initialization():
    """Test ML engine initialization."""
    engine = MLCorrectionEngine()
    assert engine.model is None
    assert not engine.is_trained

def test_ml_engine_predict_without_training():
    """Test prediction fails when not trained."""
    engine = MLCorrectionEngine()
    with pytest.raises(RuntimeError):
        engine.predict({"features": []})
```

- [ ] **Step 2-5:** Implement and commit

```python
from sklearn.ensemble import GradientBoostingRegressor

class MLCorrectionEngine:
    """2-stage ML correction engine."""

    def __init__(self):
        self.model = None
        self.is_trained = False

    def train(self, historical_data: List[Dict]):
        """Train ML model on historical data."""
        X, y = self._prepare_training_data(historical_data)
        self.model = GradientBoostingRegressor(n_estimators=100)
        self.model.fit(X, y)
        self.is_trained = True

    def predict(self, recipe_features: Dict) -> Dict:
        """Predict corrected color."""
        if not self.is_trained:
            raise RuntimeError("Model not trained")

        X = self._extract_features(recipe_features)
        correction = self.model.predict(X.reshape(1, -1))[0]

        return {"correction": correction, "confidence": self._get_confidence()}

    def _prepare_training_data(self, data: List[Dict]) -> Tuple:
        """Prepare features and labels from historical data."""
        pass

    def _extract_features(self, features: Dict) -> np.ndarray:
        """Extract feature vector from recipe."""
        pass

    def _get_confidence(self) -> float:
        """Get prediction confidence score."""
        pass
```

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: implement ML correction engine interface"
```

### Task 2.6: Integrate K-M + ML Engine

**Files:**
- Create: `app/services/hybrid_engine.py`
- Test: `tests/test_hybrid_engine.py`

- [ ] **Step 1: Write hybrid engine tests**

```python
def test_hybrid_engine_full_pipeline():
    """Test complete K-M + ML pipeline."""
    engine = HybridEngine()

    # Train on historical data
    historical_data = [...]  # Format: {recipe, km_prediction, actual_measurement}
    engine.train(historical_data)

    # Predict new recipe
    recipe = {...}
    base_color = {...}
    result = engine.predict(recipe, base_color)

    assert "km_prediction" in result
    assert "ml_correction" in result
    assert "final_prediction" in result

def test_hybrid_engine_fallback():
    """Test K-M fallback when ML not trained."""
    engine = HybridEngine()
    recipe = {...}
    base_color = {...}
    result = engine.predict(recipe, base_color)

    # Should return K-M prediction without ML correction
    assert "km_prediction" in result
```

- [ ] **Step 2-5:** Implement and commit

```python
class HybridEngine:
    """Hybrid K-M + ML engine."""

    def __init__(self):
        self.km_engine = KubelkaMunkEngine()
        self.ml_engine = MLCorrectionEngine()

    def train(self, historical_data: List[Dict]):
        """Train ML engine on historical data."""
        self.ml_engine.train(historical_data)

    def predict(self, recipe: Dict, base_color: Dict) -> Dict:
        """Run full K-M + ML prediction pipeline."""
        # Stage 1: K-M physical model
        km_result = self.km_engine.predict_recipe(recipe, base_color)

        # Stage 2: ML correction (if trained)
        if self.ml_engine.is_trained:
            ml_correction = self.ml_engine.predict({
                "recipe": recipe,
                "km_prediction": km_result["predicted_color"]
            })
            final_prediction = self._apply_correction(
                km_result["predicted_color"],
                ml_correction["correction"]
            )
        else:
            final_prediction = km_result["predicted_color"]
            ml_correction = None

        return {
            "km_prediction": km_result["predicted_color"],
            "ml_correction": ml_correction,
            "final_prediction": final_prediction,
            "delta_E": calculate_delta_e_76(base_color, final_prediction)
        }

    def _apply_correction(self, km_color: Dict, correction: float) -> Dict:
        """Apply ML correction to K-M prediction."""
        corrected = km_color.copy()
        for channel in ["L", "a", "b"]:
            corrected[channel] = km_color[channel] + correction[channel]
        return corrected
```

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: implement hybrid K-M + ML engine integration"
```

### Task 2.7: Add API Endpoints

**Files:**
- Create: `app/api/routers/predict.py`
- Extend: `app/api/routers/match.py`

- [ ] **Step 1: Write API endpoint tests**

```python
def test_predict_endpoint():
    """Test recipe prediction API."""
    response = client.post("/api/predict/", json={
        "recipe": {...},
        "base_color": {...}
    })
    assert response.status_code == 200
    data = response.json()
    assert "final_prediction" in data
    assert "delta_E" in data
```

- [ ] **Step 2-5:** Implement and commit

```python
from fastapi import APIRouter, HTTPException
from app.schemas.predict import PredictRequest, PredictResponse
from app.services.hybrid_engine import HybridEngine

router = APIRouter(prefix="/predict", tags=["prediction"])

# Global engine instance (will be initialized with DB session)
engine = HybridEngine()

@router.post("/", response_model=PredictResponse)
async def predict_recipe(request: PredictRequest):
    """Predict color for given recipe."""
    result = engine.predict(request.recipe, request.base_color)
    return PredictResponse(**result)

@router.post("/train")
async def train_model(historical_data: List[Dict]):
    """Train ML model on historical data."""
    engine.train(historical_data)
    return {"status": "trained", "samples": len(historical_data)}
```

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: add prediction API endpoints"
```

## Testing Requirements

- Minimum 80% code coverage
- All tests must pass: `pytest tests/ -v --cov=app.services`
- Integration test with sample historical data

## Acceptance Criteria

1. Kubelka-Munk engine correctly calculates R_infinity
2. Layer prediction follows adding-up formula
3. ML engine can be trained on historical data
4. Hybrid engine combines K-M + ML predictions
5. API endpoints functional with OpenAPI docs
6. All tests passing with 80%+ coverage

---

**Plan complete. Ready to execute.**

**Execution options:**
1. **Subagent-Driven** (recommended) - Dispatch subagent per task
2. **Inline Execution** - Execute tasks in this session

**Which approach?**

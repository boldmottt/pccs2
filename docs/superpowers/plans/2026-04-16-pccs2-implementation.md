# PCCS2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build PCCS2 (Pad-print Color Correction System) v2 - a pattern-based color matching system with AI-powered ink recipe recommendation

**Architecture:** Modular monolith with clear separation between API layer, business logic (1-stage K-M engine + 2-stage ML engine), and data access layer. PostgreSQL for persistence, Next.js frontend, FastAPI backend.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy, PostgreSQL, Next.js 16, React 19, TypeScript, Tailwind CSS 4, XGBoost/LightGBM (ML)

---

## Project Structure

```
PCCS2/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app entry point
│   │   ├── config.py               # Configuration management
│   │   │
│   │   ├── models/
│   │   │   └── domain.py           # All SQLAlchemy ORM models
│   │   │
│   │   ├── api/
│   │   │   ├── routers/
│   │   │   │   ├── projects.py
│   │   │   │   ├── patterns.py
│   │   │   │   ├── rounds.py
│   │   │   │   ├── samples.py
│   │   │   │   ├── inks.py
│   │   │   │   └── match.py        # Recipe recommendation
│   │   │   └── dependencies.py     # Common dependencies
│   │   │
│   │   ├── engines/
│   │   │   ├── __init__.py
│   │   │   ├── base.py             # Engine base class
│   │   │   ├── stage1_km.py        # 1-stage: Modified Kubelka-Munk
│   │   │   └── stage2_ml.py        # 2-stage: ML correction
│   │   │
│   │   ├── services/
│   │   │   ├── color_math.py       # Color calculations (ΔE, gloss)
│   │   │   ├── blend_processor.py  # Blend input processing
│   │   │   └── blend_calculator.py # Blend solid color calculation
│   │   │
│   │   └── database/
│   │       ├── session.py          # DB session management
│   │       └── repository.py       # CRUD repository base class
│   │
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx            # Dashboard
│   │   │   ├── projects/
│   │   │   ├── patterns/
│   │   │   └── samples/
│   │   ├── components/
│   │   │   ├── common/
│   │   │   ├── project/
│   │   │   ├── pattern/
│   │   │   ├── round/
│   │   │   ├── sample/
│   │   │   └── visualization/
│   │   │
│   │   └── lib/
│   │       ├── api.ts
│   │       └── color-utils.ts
│   │
│   └── package.json
│
└── docs/
    └── superpowers/
        ├── specs/
        │   └── 2026-04-16-pccs2-design.md
        └── plans/
            └── 2026-04-16-pccs2-implementation.md
```

---

## Phase 1: Backend Foundation & Data Models

### Task 1.1: Create Backend Project Structure

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/Dockerfile`
- Create: `backend/app/__init__.py`
- Create: `backend/app/config.py`
- Create: `backend/app/database/__init__.py`
- Create: `backend/app/database/session.py`
- Create: `backend/app/database/repository.py`
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/domain.py`
- Create: `backend/app/main.py`
- Create: `backend/app/schemas/__init__.py`
- Create: `backend/app/schemas/projects.py`
- Create: `backend/app/schemas/patterns.py`
- Create: `backend/app/schemas/rounds.py`
- Create: `backend/app/schemas/samples.py`
- Create: `backend/app/schemas/inks.py`
- Create: `backend/app/schemas/match.py`
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/api/routers/__init__.py`
- Create: `backend/app/api/routers/projects.py`
- Create: `backend/app/api/routers/patterns.py`
- Create: `backend/app/api/routers/rounds.py`
- Create: `backend/app/api/routers/samples.py`
- Create: `backend/app/api/routers/inks.py`
- Create: `backend/app/api/routers/match.py`
- Create: `backend/app/api/dependencies.py`
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/services/color_math.py`
- Create: `backend/app/services/blend_processor.py`
- Create: `backend/app/services/blend_calculator.py`

- [x] **Step 1: Create requirements.txt** - DONE
- [x] **Step 2: Create Dockerfile** - DONE
- [x] **Step 3: Create app/__init__.py** - DONE
- [x] **Step 4: Create config.py** - DONE
- [x] **Step 5: Create database/__init__.py** - DONE
- [x] **Step 6: Create database/session.py** - DONE
- [x] **Step 7: Create database/repository.py** - DONE
- [x] **Step 8: Create models/__init__.py** - DONE
- [x] **Step 9: Create models/domain.py** - DONE
- [x] **Step 10: Create schemas/__init__.py** - DONE
- [x] **Step 11: Create schemas/projects.py** - DONE
- [x] **Step 12: Create schemas/patterns.py** - DONE
- [x] **Step 13: Create schemas/rounds.py** - DONE
- [x] **Step 14: Create schemas/samples.py** - DONE
- [x] **Step 15: Create schemas/inks.py** - DONE
- [x] **Step 16: Create schemas/match.py** - DONE
- [x] **Step 17: Create api/__init__.py** - DONE
- [x] **Step 18: Create api/routers/__init__.py** - DONE
- [x] **Step 19: Create api/routers/projects.py** - DONE
- [x] **Step 20: Create api/routers/patterns.py** - DONE
- [x] **Step 21: Create api/routers/rounds.py** - DONE
- [x] **Step 22: Create api/routers/samples.py** - DONE
- [x] **Step 23: Create api/routers/inks.py** - DONE
- [x] **Step 24: Create api/routers/match.py** - DONE
- [x] **Step 25: Create api/dependencies.py** - DONE
- [x] **Step 26: Create services/__init__.py** - DONE
- [x] **Step 27: Create services/color_math.py** - DONE
- [x] **Step 28: Create services/blend_processor.py** - DONE
- [x] **Step 29: Create services/blend_calculator.py** - DONE
- [x] **Step 30: Create main.py** - DONE

---

### Task 1.2: Initialize Git Repository

**Files:**
- Initialize: `PCCS2/.git`
- Create: `PCCS2/.gitignore`
- Create: `PCCS2/README.md`

- [ ] **Step 1: Initialize Git repository**

```bash
cd /Users/ttobone/PCCS2
git init
git branch -M main
```

- [ ] **Step 2: Create .gitignore**

```gitignore
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
ENV/
env/
.env
*.db
*.sqlite3
.DS_Store
node_modules/
.next/
out/
*.log
```

- [ ] **Step 3: Create README.md**

```markdown
# PCCS2 - Pad-print Color Correction System v2

패드프린트 잉크 배합비 추천 시스템 - 빅데이터 기반 AI 엔진

## Features

- 패턴 기반 색상 매칭 (Project → Pattern → Round → Sample)
- 1 단계: 수정 Kubelka-Munk 물리 모델
- 2 단계: 머신러닝 보정 (데이터 축적 시)
- SCI/SCE 측색 데이터 지원
- 배합비 시각화 (InkDonutChart)
- 마스터 잉크 등록 (배합 잉크 → 마스터 변환)

## Tech Stack

- **Backend:** Python 3.11, FastAPI, SQLAlchemy, PostgreSQL
- **Frontend:** Next.js 16, React 19, TypeScript, Tailwind CSS 4
- **ML:** XGBoost, scikit-learn

## Getting Started

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
```

- [ ] **Step 4: First commit**

```bash
git add .
git commit -m "feat: initialize PCCS2 project structure"
```

---

### Task 1.3: Write Tests for Core Functions

**Files:**
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/test_color_math.py`
- Create: `backend/tests/test_blend_processor.py`

- [ ] **Step 1: Create test_color_math.py**

```python
import pytest
from app.services.color_math import (
    calculate_delta_e_76,
    calculate_delta_e_sci_sce,
    calculate_gloss_index,
    calculate_opacity_index,
    calculate_weighted_average,
)


def test_calculate_delta_e_76():
    color1 = {"L": 50, "a": 0, "b": 0}
    color2 = {"L": 50, "a": 3, "b": 4}
    # ΔE = sqrt(0^2 + 3^2 + 4^2) = 5
    assert abs(calculate_delta_e_76(color1, color2) - 5.0) < 0.001


def test_calculate_delta_e_sci_sce():
    sci = {"L": 50, "a": 0, "b": 0}
    sce = {"L": 48, "a": -1, "b": 5}
    dl, da, db = 2, 1, -5
    expected = (dl**2 + da**2 + db**2) ** 0.5
    assert abs(calculate_delta_e_sci_sce(sci, sce) - expected) < 0.001


def test_calculate_gloss_index():
    # delta = 2.5, max = 5.0 → gloss_index = 0.5
    assert calculate_gloss_index(2.5, 5.0) == 0.5
    # delta = 10.0, max = 5.0 → gloss_index = 1.0 (capped)
    assert calculate_gloss_index(10.0, 5.0) == 1.0


def test_calculate_opacity_index():
    ink_solid = {"L": 50, "a": 0, "b": 0}
    base = {"L": 100, "a": 0, "b": 0}
    printed = {"L": 50, "a": 0, "b": 0}
    # ΔE(ink_solid, printed) = 0, ΔE(ink_solid, base) = 50
    # opacity_index = 1 - (0/50) = 1.0
    assert calculate_opacity_index(ink_solid, base, printed) == 1.0


def test_calculate_weighted_average():
    colors = {
        "ink1": {"L": 50, "a": 0, "b": 0},
        "ink2": {"L": 100, "a": 0, "b": 0},
    }
    weights = {"ink1": 0.5, "ink2": 0.5}
    result = calculate_weighted_average(colors, weights)
    assert abs(result["L"] - 75.0) < 0.001
    assert result["a"] == 0
    assert result["b"] == 0
```

- [ ] **Step 2: Create test_blend_processor.py**

```python
import pytest
from app.services.blend_processor import BlendProcessor


def test_process_blend_input_basic():
    raw_components = [
        {"ink_id": "red", "amount": 30},
        {"ink_id": "yellow", "amount": 20},
        {"ink_id": "transparent", "amount": 50},
    ]
    result = BlendProcessor.process_blend_input(raw_components)

    assert result["color_component_sum"] == 100
    assert result["thinner_amount"] == 0
    assert result["dilution_factor"] == 1.0
    assert result["normalized_color_ratio"]["red"] == 0.3
    assert result["normalized_color_ratio"]["yellow"] == 0.2
    assert result["normalized_color_ratio"]["transparent"] == 0.5


def test_process_blend_input_with_thinner():
    raw_components = [
        {"ink_id": "red", "amount": 30},
        {"ink_id": "yellow", "amount": 20},
    ]
    thinner_amount = 50

    result = BlendProcessor.process_blend_input(raw_components, thinner_amount=thinner_amount)

    assert result["color_component_sum"] == 50
    assert result["thinner_amount"] == 50
    assert result["dilution_factor"] == 50 / (50 + 50) == 0.5


def test_process_blend_input_with_hardener():
    raw_components = [
        {"ink_id": "red", "amount": 30},
        {"ink_id": "yellow", "amount": 20},
        {"ink_id": "HARDENER", "amount": 10},
    ]
    result = BlendProcessor.process_blend_input(raw_components)

    # Hardener should be added to transparent gloss
    assert result["effective_color_components"]["TRANSPARENT_GLOSS"] == 10
    assert result["color_component_sum"] == 60
```

- [ ] **Step 3: Run tests**

```bash
cd backend
python -m pytest tests/ -v
```

---

## Phase 2: Engine Implementation

### Task 2.1: Create 1-stage K-M Engine

**Files:**
- Create: `backend/app/engines/__init__.py`
- Create: `backend/app/engines/base.py`
- Create: `backend/app/engines/stage1_km.py`

- [ ] **Step 1: Create engines/base.py**

```python
from abc import ABC, abstractmethod
from typing import Dict, List
from app.schemas.match import RecommendedRecipe


class BaseEngine(ABC):
    """Base class for color prediction engines"""

    @abstractmethod
    def predict_color(
        self,
        recipe: List[Dict],
        print_conditions: Dict
    ) -> Dict[str, float]:
        """Predict printed color for a given recipe"""
        pass

    @abstractmethod
    def recommend_recipe(
        self,
        target_color: Dict[str, float],
        print_conditions: Dict
    ) -> List[RecommendedRecipe]:
        """Recommend recipes for target color"""
        pass
```

- [ ] **Step 2: Create engines/stage1_km.py** - See full implementation in implementation guide

- [ ] **Step 3: Write tests for K-M engine**

---

## Phase 3: Frontend Implementation

### Task 3.1: Initialize Next.js Project

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/next.config.js`
- Create: `frontend/tailwind.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/src/app/layout.tsx`
- Create: `frontend/src/app/page.tsx`

---

## Phase 4: Integration & Deployment

### Task 4.1: Docker Compose Setup

**Files:**
- Create: `docker-compose.yml`
- Create: `docker-compose.dev.yml`

---

## Implementation Notes

1. **Use Pydantic v2** - All schemas use `from_attributes = True`
2. **Async database** - All database operations use asyncpg
3. **UUID primary keys** - All IDs are UUIDs for distributed systems
4. **JSON columns** - Color data stored as JSON for flexibility
5. **Timestamps** - All models have created_at/updated_at

---

**Plan complete. Execute task-by-task with subagent-driven development.**

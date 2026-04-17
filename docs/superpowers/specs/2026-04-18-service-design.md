# PCCS2 Service Design Specification

**Date:** 2026-04-18
**Status:** Approved
**Scope:** UX/UI Overhaul + Data Model Improvements

---

## Overview

PCCS2 서비스의 UX/UI 개선과 데이터 모델 정리를 위한 설계입니다. 인증/보안은 제거하고, 전문적인 디자인 시스템과 명확한 데이터 구조에 집중합니다.

---

## Design System (UX/UI)

### Visual Direction: "Professional Dark Luxury"

단순한 템플릿 UI 가 아닌, 전문적인 잉크 배합 시스템에 맞는 깊고 의도적인 디자인으로 개선합니다.

### 1. Layout Structure

```
┌─────────────────────────────────────────────────────────┐
│  FIXED HEADER (z-index: 100)                            │
│  ┌──────────┐  ┌────────────────────────────────────┐  │
│  │  Logo    │  │  Projects  Samples  Inks  Match   │  │
│  └──────────┘  └────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│  PAGE CONTENT (padding-top: 80px)                       │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Hero Section / Page Title                       │  │
│  │  - Large typography, subtle glow effect          │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Main Content (cards, tables, forms)             │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

**Navigation Links:**
- **Projects** - 프로젝트 목록 및 관리
- **Samples** - 샘플 배합비 관리
- **Inks** - 잉크 마스터 데이터
- **Match** - 레시피 추천 (새로 추가)

### 2. Color Palette

```css
/* Dark Luxury Theme */
--bg-primary: oklch(12% 0 0)           /* Very dark gray */
--bg-secondary: oklch(18% 0 0)         /* Dark gray cards */
--bg-tertiary: oklch(24% 0 0)          /* Lighter gray for hover */

--text-primary: oklch(96% 0 0)         /* Almost white */
--text-secondary: oklch(70% 0 0)       /* Muted text */

--accent-primary: oklch(62% 0.22 265)  /* Violet glow */
--accent-secondary: oklch(58% 0.18 190) /* Cyan accent */

--success: oklch(68% 0.15 145)          /* Green */
--warning: oklch(70% 0.18 85)           /* Yellow */
--error: oklch(58% 0.24 15)             /* Red */

--border-subtle: oklch(30% 0 0 / 0.3)  /* Transparent border */
```

### 3. Typography Scale

```css
--text-hero: clamp(2.5rem, 4vw, 4rem)      /* Page titles */
--text-2xl: clamp(1.75rem, 2.5vw, 2.5rem)  /* Section headers */
--text-xl: clamp(1.25rem, 1.75vw, 1.5rem)  /* Card titles */
--text-base: 1rem                          /* Body text */
--text-sm: 0.875rem                        /* Secondary info */
```

### 4. Component Design

#### Button Variants
- **Primary**: Violet background, glow on hover, shadow-lg
- **Secondary**: Dark gray background, subtle border
- **Ghost**: Text only, minimal padding

#### Card Variants
- **Default**: Semi-transparent background, backdrop blur
- **Elevated**: Solid dark gray, shadow-md
- **Interactive**: Hover lift (-2px), glow shadow

#### Form Inputs
- Dark background, subtle border
- Focus state: Violet ring glow
- Error state: Red border + message

### 5. Motion & Transitions

```css
--duration-fast: 150ms   /* Hover states */
--duration-normal: 300ms /* Standard transitions */
--duration-slow: 500ms   /* Page transitions */

--ease-out-expo: cubic-bezier(0.16, 1, 0.3, 1)
--ease-out-back: cubic-bezier(0.34, 1.56, 0.64, 1)
```

**Animations:**
- Fade in on page load (300ms)
- Slide up for new items (300ms)
- Hover effects on cards/buttons (150ms)

---

## Data Model Improvements (Option C)

### Current Structure Analysis

```
Project → Pattern → Round → Sample
               ↑
              layers[]
```

### 1. Field Naming Consistency

**Backend (Python/SQLAlchemy): snake_case**
```python
class Sample(Base):
    sample_id = Column(String, primary_key=True)
    round_id = Column(String, ForeignKey('rounds.round_id'))
    sample_number = Column(Integer)  # Changed from sampleNumber
    base_color_sci = Column(JSONB)
    base_color_sce = Column(JSONB)
    layers = Column(JSONB)
    success_flag = Column(String)    # Changed from successFlag
```

**Frontend (TypeScript): camelCase**
```typescript
interface Sample {
  sampleId: string
  roundId: string
  sampleNumber: number | null
  baseColorSci: ColorData
  baseColorSce: ColorData
  layers: Layer[]
  successFlag: 'SUCCESS' | 'FAILED' | 'PENDING'
}
```

### 2. Enhanced Schema Definitions

#### Pattern (Backend)

Update `backend/app/schemas/patterns.py`:

```python
class PatternCreate(BaseModel):
    project_id: str = Field(..., description="UUID of the parent project")
    pattern_name: str = Field(..., min_length=1, max_length=200, description="Pattern name")
    total_print_layers: int = Field(..., ge=1, le=10, description="Total print layers (1-10)")
    target_base_color_sci: Optional[ColorData] = None
    target_base_color_sce: Optional[ColorData] = None
    target_base_material: Optional[str] = Field(None, max_length=100)
    status: PatternStatus = Field(default=PatternStatus.DEVELOPING)
    notes: Optional[str] = Field(None, max_length=1000)
    approved_sample_id: Optional[str] = Field(None, description="UUID of approved sample")
```

#### ColorData Validation

```python
class ColorData(BaseModel):
    L: float = Field(..., ge=0.0, le=100.0, description="Lightness (0=black, 100=white)")
    a: float = Field(..., ge=-128.0, le=127.0, description="Green(-) to Red(+) axis")
    b: float = Field(..., ge=-128.0, le=127.0, description="Blue(-) to Yellow(+) axis")

    @field_validator('L')
    @classmethod
    def validate_l(cls, v):
        if v < 0 or v > 100:
            raise ValueError('L must be between 0 and 100')
        return v
```

#### Layer Schema

```python
class LayerCreate(BaseModel):
    layer_number: int = Field(..., ge=1, le=10, description="Layer number (1-10)")
    ink_id: str = Field(..., description="UUID of ink")
    percentage: float = Field(..., ge=0.0, le=100.0, description="Ink percentage")

class LayerValidate(BaseModel):
    @field_validator('layers')
    @classmethod
    def validate_percentages(cls, v):
        total = sum(layer.percentage for layer in v)
        if abs(total - 100.0) > 0.5:
            raise ValueError(f"Layer percentages must sum to 100%, got {total:.2f}%")
        return v
```

### 3. Field Addition Priority

| Entity | Field | Type | Reason |
|--------|-------|------|--------|
| Pattern | `success_rate` | float | Sample success rate % |
| Pattern | `avg_delta_e` | float | Average color difference |
| Sample | `measured_color_sci` | ColorData | Actual measurement |
| Sample | `measured_color_sce` | ColorData | Actual measurement |
| Round | `operator` | string | Worker name |
| Round | `work_date` | date | Work date |

### 4. Relationship Improvements

```
Project
├── projectId (PK)
├── projectName
├── customer
├── status
├── start_date
├── target_completion
├── memo
└── patterns[]

Pattern
├── patternId (PK)
├── projectId (FK → Project)
├── pattern_name
├── total_print_layers
├── target_base_color_sci
├── target_base_color_sce
├── target_base_material
├── status
├── notes
├── success_rate
├── avg_delta_e
└── samples[]

Round
├── roundId (PK)
├── patternId (FK → Pattern)
├── round_number
├── work_date
├── operator
└── samples[]

Sample
├── sampleId (PK)
├── roundId (FK → Round)
├── sample_number
├── base_color_sci
├── base_color_sce
├── measured_color_sci
├── measured_color_sce
├── layers[]
├── success_flag
└── delta_e
```

---

## File Organization

```
frontend/src/
├── app/
│   ├── layout.tsx          # Root layout with fixed header
│   ├── globals.css         # Design tokens + Tailwind
│   ├── page.tsx            # Dashboard home
│   ├── projects/
│   │   ├── page.tsx        # Project list
│   │   ├── new/
│   │   │   └── page.tsx    # Create project
│   │   └── [projectId]/
│   │       └── page.tsx    # Project detail
│   ├── samples/
│   │   ├── page.tsx        # Sample list
│   │   └── new/
│   │       └── page.tsx    # Create sample
│   ├── inks/
│   │   └── page.tsx        # Ink master data
│   └── match/
│       └── page.tsx        # Recipe recommendation
├── components/
│   ├── ui/
│   │   ├── Button.tsx      # Enhanced button
│   │   ├── Card.tsx        # Enhanced card
│   │   ├── Input.tsx       # Enhanced input
│   │   └── Select.tsx      # Enhanced select
│   ├── layout/
│   │   ├── Header.tsx      # Fixed header component
│   │   └── Layout.tsx      # Page layout wrapper
│   ├── visualization/
│   │   ├── ColorTrendChart.tsx
│   │   ├── InkDonutChart.tsx
│   │   └── ColorPreview.tsx
│   └── samples/
│       ├── LayerEditor.tsx
│       └── InkSelector.tsx
└── lib/
    ├── types/
    │   ├── project.ts
    │   ├── color.ts
    │   └── pattern.ts      # NEW: Pattern types
    └── api/
        ├── projects.ts
        ├── patterns.ts     # NEW: Pattern API
        ├── samples.ts
        └── inks.ts
```

---

## Implementation Phases

### Phase 1: Design System Foundation (2 hours)
1. Create design tokens (CSS variables)
2. Update globals.css with theme
3. Build enhanced UI components (Button, Card, Input, Select)
4. Create Header component with fixed navigation

### Phase 2: Page Layout Updates (2 hours)
1. Update root layout with Header
2. Redesign homepage with new design system
3. Update project list page
4. Update sample list page
5. Update ink list page

### Phase 3: Data Model Improvements (1.5 hours)
1. Add field descriptions to Pydantic schemas
2. Add validation for color ranges
3. Add validation for layer percentages
4. Update TypeScript types with descriptions
5. Write validation tests

### Phase 4: Polish & Testing (1 hour)
1. Test responsive design (mobile, tablet, desktop)
2. Verify all animations work smoothly
3. Test form validation error states
4. Final UI review

**Total Time: 6.5 hours**

---

## Success Criteria

### UX/UI
- [ ] Fixed header navigation on all pages
- [ ] Dark luxury color palette applied consistently
- [ ] All cards have hover effects and depth
- [ ] Buttons have clear primary/secondary hierarchy
- [ ] Smooth transitions on all interactions
- [ ] Responsive design works on mobile (375px+)

### Data Model
- [ ] All Pydantic schemas have Field descriptions
- [ ] Color values validated (L: 0-100, a/b: -128~127)
- [ ] Layer percentages validated (sum = 100%)
- [ ] TypeScript types match backend schemas
- [ ] New fields documented (success_rate, avg_delta_e, etc.)

---

## Next Steps

1. User approval of this design
2. Implement design system (Button, Card, Header, tokens)
3. Update all pages with new design
4. Add data model improvements
5. Final review

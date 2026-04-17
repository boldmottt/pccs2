# PCCS2 Service Improvements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enhance PCCS2 based on 10+ hour expert UX/UI/frontend testing feedback from multiple perspectives

**Architecture:** Multi-phase improvements addressing security, UX/UI, validation, error handling, and developer experience

**Tech Stack:** FastAPI, Python 3.11, Next.js 16, TypeScript, PostgreSQL, Pydantic

---

## Executive Summary

Based on expert user testing across UX, UI, service experience, web structure, and frontend engineering domains, this plan addresses:

1. **Security Layer** (Priority: CRITICAL) - Authentication, authorization, input validation
2. **UX/UI Overhaul** (Priority: HIGH) - Visual hierarchy, intentional design, motion
3. **Validation & Error Handling** (Priority: HIGH) - Comprehensive input validation, user-friendly errors
4. **Developer Experience** (Priority: MEDIUM) - Documentation, testing, monitoring

## Issues Identified from Testing

### Backend Issues
- JSONB serialization bugs (FIXED in current version)
- Missing authentication/authorization
- Insufficient input validation
- Generic error messages
- No rate limiting

### Frontend Issues
- Template-looking UI (generic Tailwind/Shadcn appearance)
- Lack of visual hierarchy and depth
- Inconsistent interaction patterns
- Missing loading states and feedback
- No animation for state transitions

### UX Issues
- Unclear information architecture
- Missing onboarding guidance
- No progress indicators for multi-step workflows
- Limited discoverability of features

---

## Phase 1: Security Foundation (CRITICAL)

### Files Modified:
- `backend/app/main.py` - Add middleware
- `backend/app/api/dependencies.py` - Add auth deps
- `backend/app/api/routers/*.py` - Add auth guards
- `backend/requirements.txt` - Add auth dependencies

## Task 1.1: Install Authentication Dependencies

- [ ] **Step 1: Add auth packages to requirements.txt**

Add to `backend/requirements.txt`:
```
fastapi-users[sqlalchemy]==13.0.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
```

- [ ] **Step 2: Run pip install**

```bash
cd backend
pip install -r requirements.txt
```

Expected: All packages installed successfully

- [ ] **Step 3: Create auth configuration**

Create `backend/app/config_auth.py`:
```python
from pydantic import Field
from pydantic_settings import BaseSettings

class AuthSettings(BaseSettings):
    SECRET_KEY: str = Field(..., min_length=32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    API_V1_PREFIX: str = "/api/v1"

    class Config:
        env_prefix = "AUTH_"

auth_settings = AuthSettings()
```

- [ ] **Step 4: Add .env example**

Create `backend/.env.auth.example`:
```
AUTH_SECRET_KEY=your-super-secret-key-min-32-chars-generate-with-openssl-rand-hex-32
AUTH_ALGORITHM=HS256
AUTH_ACCESS_TOKEN_EXPIRE_MINUTES=30
AUTH_REFRESH_TOKEN_EXPIRE_DAYS=7
AUTH_API_V1_PREFIX=/api/v1
```

- [ ] **Step 5: Run tests**

```bash
cd backend
pytest tests/test_auth.py -v
```

Expected: Auth tests pass

---

## Task 1.2: Create User Model & Database Schema

- [ ] **Step 1: Create user model**

Create `backend/app/models/user.py`:
```python
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from uuid import uuid4
from datetime import datetime

from app.database.session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    projects = relationship("Project", back_populates="owner", lazy="dynamic")
```

- [ ] **Step 2: Create migration script**

Create `backend/migrations/001_create_users_table.py`:
```python
"""Create users table migration

Revision ID: 001
Revises:
Create Date: 2026-04-18
"""
from alembic import op
import sqlalchemy as sa

revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_superuser', sa.Boolean(), default=False),
        sa.Column('is_verified', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index('idx_users_email', 'users', ['email'])

def downgrade() -> None:
    op.drop_index('idx_users_email', table_name='users')
    op.drop_table('users')
```

- [ ] **Step 3: Run migration**

```bash
cd backend
alembic upgrade head
```

Expected: Users table created

---

## Task 1.3: Implement Authentication Endpoints

- [ ] **Step 1: Create auth router**

Create `backend/app/api/routers/auth.py`:
```python
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import AuthenticationBackend, BearerTransport
from fastapi_users.manager import BaseUserManager, UserManagerDependency
from fastapi_users.schema import UserUpdate, UserCreate, User
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4
import secrets

from app.database.session import get_db_session
from app.models.user import User
from app.config_auth import auth_settings

# JWT transport
bearer_transport = BearerTransport(tokenUrl=auth_settings.API_V1_PREFIX + "/auth/jwt/login")

# JWT backend
JWT_BACKEND_NAME = "jwt"
auth_backend = AuthenticationBackend(
    name=JWT_BACKEND_NAME,
    transport=bearer_transport,
)

# User manager
class SQLAlchemyUserManager(UserManager[User]):
    async def validate_password(
        self, password: str, user: UserCreate
    ) -> str:
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters")
        if password == user.email:
            raise ValueError("Password cannot be the same as email")
        return password

    async def on_after_register(self, user: User, request=None):
        print(f"User {user.id} has registered.")

    async def on_after_login(self, user: User, request=None):
        print(f"User {user.id} has logged in.")

async def get_user_manager_db(db: AsyncSession = Depends(get_db_session)):
    return SQLAlchemyUserManager(User, db)

get_user_manager: UserManagerDependency[User, uuid4] = get_user_manager_db

# FastAPI Users instance
fastapi_users = FastAPIUsers[User, uuid4](
    get_user_manager,
    [auth_backend],
)

# Current user dependency
get_current_user = fastapi_users.current_user(active=True)

# Router
router = APIRouter(prefix=auth_settings.API_V1_PREFIX + "/auth", tags=["auth"])

@router.post("/register", response_model=User)
async def register(user_create: UserCreate, user_manager: UserManagerDependency[User, uuid4] = Depends(get_user_manager_db)):
    return await user_manager.create(user_create)

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    return await auth_backend.login(authentication_helper=authentication_helper, credentials=form_data)

@router.post("/logout")
async def logout(user: User = Depends(get_current_user)):
    return {"message": "Successfully logged out"}
```

- [ ] **Step 2: Add dependencies for protected routes**

Update `backend/app/api/dependencies.py`:
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.models.user import User
from app.config_auth import auth_settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=auth_settings.API_V1_PREFIX + "/auth/jwt/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db_session)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, auth_settings.SECRET_KEY, algorithms=[auth_settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await db.get(User, user_id)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_superuser(
    current_user: User = Depends(get_current_active_user),
) -> User:
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="The user doesn't have enough privileges")
    return current_user
```

- [ ] **Step 3: Test auth endpoints**

```bash
cd backend
pytest tests/test_auth_endpoints.py -v
```

Expected: Auth tests pass

---

## Task 1.4: Add Authorization for Protected Routes

- [ ] **Step 1: Add auth requirement to patterns router**

Update `backend/app/api/routers/patterns.py`:
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4
from typing import List
from sqlalchemy import text
import json

from app.database.session import get_db_session
from app.schemas.patterns import PatternCreate, PatternUpdate, PatternResponse
from app.api.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/patterns", tags=["patterns"])

@router.post("/", response_model=PatternResponse)
async def create_pattern(
    pattern: PatternCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    # Optionally verify user owns the project
    ...
```

- [ ] **Step 2: Add authorization check to all routers**

Apply same pattern to:
- `backend/app/api/routers/projects.py`
- `backend/app/api/routers/samples.py`
- `backend/app/api/routers/rounds.py`
- `backend/app/api/routers/inks.py`

- [ ] **Step 3: Test protected routes**

```bash
cd backend
pytest tests/test_auth_protection.py -v
```

Expected: Unauthenticated requests return 401

---

## Phase 2: Input Validation & Error Handling (HIGH)

### Files Modified:
- `backend/app/schemas/*.py` - Add validation
- `backend/app/api/routers/*.py` - Add error handlers
- `backend/app/main.py` - Add global exception handler

## Task 2.1: Add Comprehensive Input Validation

- [ ] **Step 1: Enhance ColorData schema**

Update `backend/app/schemas/patterns.py`:
```python
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime

class ColorData(BaseModel):
    L: float = Field(..., ge=0.0, le=100.0, description="Lightness value (0-100)")
    a: float = Field(..., ge=-128.0, le=127.0, description="Green-Red axis (-128 to 127)")
    b: float = Field(..., ge=-128.0, le=127.0, description="Blue-Yellow axis (-128 to 127)")

    @field_validator('L')
    @classmethod
    def validate_l(cls, v):
        if v < 0 or v > 100:
            raise ValueError('L value must be between 0 and 100')
        return v

    @field_validator('a')
    @classmethod
    def validate_a(cls, v):
        if v < -128 or v > 127:
            raise ValueError('a value must be between -128 and 127')
        return v

    @field_validator('b')
    @classmethod
    def validate_b(cls, v):
        if v < -128 or v > 127:
            raise ValueError('b value must be between -128 and 127')
        return v

    def to_dict(self) -> Dict[str, float]:
        return {"L": self.L, "a": self.a, "b": self.b}

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> 'ColorData':
        return cls(L=data['L'], a=data['a'], b=data['b'])
```

- [ ] **Step 2: Add validation to sample schemas**

Create `backend/app/schemas/samples.py`:
```python
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime

class LayerCreate(BaseModel):
    layer_number: int = Field(..., ge=1, le=10, description="Layer number (1-10)")
    ink_id: str = Field(..., description="Ink UUID")
    percentage: float = Field(..., ge=0.0, le=100.0, description="Percentage of ink (0-100)")

    @field_validator('percentage')
    @classmethod
    def validate_percentage_sum(cls, v, values):
        # Will be validated at list level
        return v

class SampleCreate(BaseModel):
    round_id: str
    sample_number: Optional[int] = None
    layers: List[LayerCreate] = Field(..., min_items=1, max_items=10)
    target_color_sci: Optional[ColorData] = None
    target_color_sce: Optional[ColorData] = None

    @field_validator('layers')
    @classmethod
    def validate_layer_percentages(cls, v):
        for layer_group in v:
            total = sum(layer.percentage for layer in layer_group)
            if abs(total - 100.0) > 0.1:
                raise ValueError(f"Layer percentages must sum to 100%, got {total}")
        return v
```

- [ ] **Step 3: Add validation to ink schemas**

Update `backend/app/schemas/inks.py`:
```python
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from uuid import UUID

class InkCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    category: str = Field(..., pattern=r"^(Pigment|Dye|Transparent|Opacity|Hardener|Thinner)$")
    color_sci: Optional[Dict[str, float]] = None
    is_master: bool = False
    density: Optional[float] = Field(None, ge=0.0, le=10.0)

    @field_validator('color_sci')
    @classmethod
    def validate_color_sci(cls, v):
        if v is not None:
            if 'L' not in v or 'a' not in v or 'b' not in v:
                raise ValueError("color_sci must contain L, a, b values")
        return v
```

- [ ] **Step 4: Write validation tests**

Create `backend/tests/test_validation.py`:
```python
import pytest
from pydantic import ValidationError
from app.schemas.patterns import ColorData

def test_color_data_valid():
    color = ColorData(L=50.0, a=0.0, b=0.0)
    assert color.L == 50.0

def test_color_data_l_out_of_range():
    with pytest.raises(ValidationError):
        ColorData(L=101.0, a=0.0, b=0.0)

def test_color_data_a_out_of_range():
    with pytest.raises(ValidationError):
        ColorData(L=50.0, a=-129.0, b=0.0)
```

Run: `pytest backend/tests/test_validation.py -v`

---

## Task 2.2: Implement Global Error Handler

- [ ] **Step 1: Create exception handlers**

Create `backend/app/api/exceptions.py`:
```python
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

async def validation_exception_handler(request: Request, exc: PydanticValidationError):
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": {"errors": errors, "message": "Validation error"}},
    )

async def integrity_exception_handler(request: Request, exc: IntegrityError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": {"message": "Database integrity error. Resource may already exist."}},
    )

async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": {"message": "Internal server error"}},
    )
```

- [ ] **Step 2: Register handlers in main.py**

Update `backend/app/main.py`:
```python
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from app.api.exceptions import validation_exception_handler, integrity_exception_handler, general_exception_handler
from app.database.session import init_db

app = FastAPI(title="PCCS2 API", version="2.0.0")

# Register exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(IntegrityError, integrity_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)
```

---

## Task 2.3: Add Rate Limiting

- [ ] **Step 1: Install rate limiting package**

Add to `backend/requirements.txt`:
```
slowapi==0.1.9
```

- [ ] **Step 2: Create rate limiter**

Create `backend/app/api/rate_limiter.py`:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

limiter = Limiter(key_func=get_remote_address)

async def rate_limit_exceeded_handler(request, exc):
    return JSONResponse(
        status_code=429,
        content={"detail": {"message": "Too many requests, please try again later"}},
    )
```

- [ ] **Step 3: Apply rate limits**

Update `backend/app/main.py`:
```python
from slowapi import _rate_limit_exceeded_handler
from app.api.rate_limiter import limiter, rate_limit_exceeded_handler

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

@limiter.limit("100/minute")
@router.get("/")
async def list_items(request: Request):
    ...
```

---

## Phase 3: UX/UI Overhaul (HIGH)

### Files Modified:
- `frontend/src/app/page.tsx` - Hero redesign
- `frontend/src/components/ui/` - Design system
- `frontend/src/app/projects/` - Project cards
- `frontend/src/app/samples/` - Sample viewer

## Task 3.1: Design System Foundation

- [ ] **Step 1: Create design tokens**

Create `frontend/src/styles/tokens.css`:
```css
:root {
  /* Colors - Deep, intentional palette */
  --color-bg-primary: oklch(15% 0 0);
  --color-bg-secondary: oklch(20% 0 0);
  --color-bg-tertiary: oklch(25% 0 0);
  --color-text-primary: oklch(95% 0 0);
  --color-text-secondary: oklch(75% 0 0);
  --color-accent-primary: oklch(65% 0.2 260);  /* Violet */
  --color-accent-secondary: oklch(55% 0.25 180);  /* Cyan */
  --color-success: oklch(65% 0.18 150);  /* Green */
  --color-warning: oklch(65% 0.2 80);  /* Yellow */
  --color-error: oklch(55% 0.25 25);  /* Red */

  /* Typography */
  --font-display: 'Inter var', sans-serif;
  --font-body: 'Inter var', sans-serif;

  --text-xs: clamp(0.75rem, 0.7rem + 0.25vw, 0.875rem);
  --text-sm: clamp(0.875rem, 0.8rem + 0.35vw, 1rem);
  --text-base: clamp(1rem, 0.9rem + 0.5vw, 1.125rem);
  --text-lg: clamp(1.125rem, 1rem + 0.65vw, 1.25rem);
  --text-xl: clamp(1.25rem, 1.1rem + 0.85vw, 1.5rem);
  --text-2xl: clamp(1.5rem, 1.25rem + 1.25vw, 2rem);
  --text-3xl: clamp(2rem, 1.5rem + 2vw, 3rem);
  --text-hero: clamp(2.5rem, 1.5rem + 4vw, 5rem);

  /* Spacing */
  --space-xs: 0.5rem;
  --space-sm: 1rem;
  --space-md: 1.5rem;
  --space-lg: 2rem;
  --space-xl: 3rem;
  --space-2xl: clamp(3rem, 2rem + 3vw, 6rem);

  /* Shadows - Subtle, layered depth */
  --shadow-sm: 0 1px 2px oklch(0 0 0 / 0.05);
  --shadow-md: 0 4px 6px -1px oklch(0 0 0 / 0.1), 0 2px 4px -2px oklch(0 0 0 / 0.1);
  --shadow-lg: 0 10px 15px -3px oklch(0 0 0 / 0.1), 0 4px 6px -4px oklch(0 0 0 / 0.1);
  --shadow-glow: 0 0 40px oklch(65% 0.2 260 / 0.3);

  /* Border radius */
  --radius-sm: 0.25rem;
  --radius-md: 0.5rem;
  --radius-lg: 1rem;
  --radius-xl: 1.5rem;
  --radius-full: 9999px;

  /* Transitions */
  --duration-fast: 150ms;
  --duration-normal: 300ms;
  --duration-slow: 500ms;
  --ease-out-expo: cubic-bezier(0.16, 1, 0.3, 1);
  --ease-out-back: cubic-bezier(0.34, 1.56, 0.64, 1);
}
```

- [ ] **Step 2: Update global CSS**

Update `frontend/src/app/globals.css`:
```css
@import './tokens.css';

@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-bg-primary text-text-primary antialiased;
    font-family: var(--font-body);
  }

  h1, h2, h3, h4, h5, h6 {
    font-family: var(--font-display);
    font-weight: 700;
    letter-spacing: -0.025em;
  }
}

@layer utilities {
  .animate-fade-in {
    animation: fadeIn var(--duration-normal) var(--ease-out-expo);
  }

  .animate-slide-up {
    animation: slideUp var(--duration-normal) var(--ease-out-expo);
  }

  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }

  @keyframes slideUp {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
}
```

- [ ] **Step 3: Create enhanced Button component**

Update `frontend/src/components/ui/Button.tsx`:
```tsx
import React from 'react'
import { cn } from '@/lib/utils'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  isLoading?: boolean
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', isLoading, children, disabled, ...props }, ref) => {
    const baseStyles = 'inline-flex items-center justify-center font-medium transition-all duration-[--duration-fast] focus:outline-none focus:ring-2 focus:ring-accent-primary focus:ring-offset-2 focus:ring-offset-bg-primary disabled:opacity-50 disabled:cursor-not-allowed'

    const variants = {
      primary: 'bg-accent-primary text-white hover:bg-opacity-90 hover:shadow-lg hover:shadow-accent-primary/25 rounded-lg px-4 py-2',
      secondary: 'bg-bg-tertiary text-text-primary border border-bg-secondary hover:bg-bg-secondary rounded-lg px-4 py-2',
      ghost: 'text-text-secondary hover:text-text-primary hover:bg-bg-secondary rounded-lg px-4 py-2',
      danger: 'bg-error text-white hover:bg-opacity-90 rounded-lg px-4 py-2',
    }

    const sizes = {
      sm: 'text-sm px-3 py-1.5',
      md: 'text-base',
      lg: 'text-lg px-6 py-3',
    }

    return (
      <button
        ref={ref}
        className={cn(baseStyles, variants[variant], sizes[size], className)}
        disabled={disabled || isLoading}
        {...props}
      >
        {isLoading && (
          <svg className="animate-spin -ml-1 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
        )}
        {children}
      </button>
    )
  }
)
Button.displayName = 'Button'
```

- [ ] **Step 4: Create enhanced Card component**

Update `frontend/src/components/ui/Card.tsx`:
```tsx
import React from 'react'
import { cn } from '@/lib/utils'

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'elevated' | 'glass'
  hoverEffect?: boolean
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant = 'default', hoverEffect = false, children, ...props }, ref) => {
    const baseStyles = 'rounded-xl border border-bg-secondary bg-bg-secondary p-6'

    const variants = {
      default: 'bg-bg-secondary/50 backdrop-blur-sm',
      elevated: 'bg-bg-primary shadow-md',
      glass: 'bg-bg-primary/30 backdrop-blur-xl border-bg-tertiary',
    }

    const hoverClass = hoverEffect ? 'transition-all duration-[--duration-normal] hover:shadow-xl hover:shadow-accent-primary/10 hover:-translate-y-1' : ''

    return (
      <div
        ref={ref}
        className={cn(baseStyles, variants[variant], hoverClass, className)}
        {...props}
      >
        {children}
      </div>
    )
  }
)
Card.displayName = 'Card'
```

---

This is a comprehensive 20+ hour improvement plan. Let me provide a summary and next steps:

## Implementation Priority Summary

| Phase | Task | Priority | Estimated Time |
|-------|------|----------|----------------|
| 1 | Authentication System | CRITICAL | 4 hours |
| 1 | Authorization Guards | CRITICAL | 2 hours |
| 2 | Input Validation | HIGH | 3 hours |
| 2 | Error Handling | HIGH | 2 hours |
| 2 | Rate Limiting | HIGH | 1 hour |
| 3 | Design System | HIGH | 4 hours |
| 3 | UI Components | HIGH | 4 hours |
| 3 | UX Improvements | MEDIUM | 3 hours |
| 4 | Documentation | MEDIUM | 2 hours |
| 4 | Monitoring | MEDIUM | 2 hours |

**Total Estimated Time: 27 hours**

---

## Execution Choice

**Plan complete and saved to `docs/superpowers/plans/2026-04-18-service-improvements.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**

---

*Plan generated using superpowers:writing-plans skill*

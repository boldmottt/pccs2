# Integration & Deployment Plan

> **For agentic workers:** Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete project integration and deployment setup for PCCS2

**Tech Stack:** Docker, Docker Compose, GitHub Actions

---

## Task 4.1: Docker Configuration

### Files to Create

#### 1. `Dockerfile.backend`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY backend/ .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/api/predict/health')" || exit 1

# Run
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 2. `Dockerfile.frontend`

```dockerfile
FROM node:20-alpine AS builder

WORKDIR /app

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ .
RUN npm run build

# Production image
FROM nginx:alpine

COPY --from=builder /app/out /usr/share/nginx/html
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

#### 3. `docker-compose.yml`

```yaml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://pccs:pccs@db:5432/pccs2
      - API_URL=http://localhost:8000
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
    restart: unless-stopped

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=pccs
      - POSTGRES_PASSWORD=pccs
      - POSTGRES_DB=pccs2
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U pccs"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

#### 4. `frontend/nginx.conf`

```nginx
server {
    listen 80;
    server_name localhost;

    root /usr/share/nginx/html;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # Handle Next.js SPA routing
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Proxy API requests to backend
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

#### 5. `.dockerignore`

```
# Backend
backend/__pycache__
backend/venv
backend/.venv
backend/*.db
backend/*.sqlite3
backend/node_modules
backend/.env
backend/.coverage
backend/.*

# Frontend
frontend/node_modules
frontend/.next
frontend/out
frontend/.env
frontend/.env.local
frontend/coverage
frontend/.*

# Common
.git
.gitignore
*.md
.DS_Store
*.log
```

### Execution

1. Create all Docker files
2. Test with `docker-compose up --build`
3. Verify both services start
4. Commit

---

## Task 4.2: Environment Configuration

### Files to Create

#### 1. `backend/.env.example`

```ini
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/pccs2

# Application
API_URL=http://localhost:8000
SECRET_KEY=your-secret-key-change-in-production

# Optional: ML model storage
MODEL_STORAGE_PATH=./models
```

#### 2. `frontend/.env.example`

```ini
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# Production (will be set at build time)
# NEXT_PUBLIC_API_URL=https://api.yourapp.com
```

#### 3. `backend/.env` (template for local dev)

```ini
DATABASE_URL=postgresql://pccs:pccs@localhost:5432/pccs2
API_URL=http://localhost:8000
SECRET_KEY=dev-secret-key-do-not-use-in-production
```

#### 4. `frontend/.env.local` (template for local dev)

```ini
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Execution

1. Create all env files
2. Update `.gitignore` to exclude `.env` but keep `.env.example`
3. Commit

---

## Task 4.3: GitHub Actions CI/CD

### Files to Create

#### 1. `.github/workflows/backend-ci.yml`

```yaml
name: Backend CI

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: pccs
          POSTGRES_PASSWORD: pccs
          POSTGRES_DB: pccs2_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov

      - name: Run tests
        env:
          DATABASE_URL: postgresql://pccs:pccs@localhost:5432/pccs2_test
        run: |
          cd backend
          pytest tests/ -v --cov=app --cov-report=xml --cov-report=term-missing

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./backend/coverage.xml
          flags: backend
          name: backend-coverage
```

#### 2. `.github/workflows/frontend-ci.yml`

```yaml
name: Frontend CI

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        run: |
          cd frontend
          npm ci

      - name: Type check
        run: |
          cd frontend
          npm run build

      - name: Lint
        run: |
          cd frontend
          npm run lint
```

#### 3. `.github/workflows/deploy.yml`

```yaml
name: Deploy

on:
  push:
    branches: [main, master]

jobs:
  deploy:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' || github.ref == 'refs/heads/master'

    steps:
      - uses: actions/checkout@v4

      - name: Build Docker images
        run: |
          docker-compose build

      - name: Log in to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}

      - name: Push images
        run: |
          docker-compose push

      # Add deployment step for your hosting platform
      # Example: AWS ECS, K8s, DigitalOcean, etc.
```

### Execution

1. Create `.github/workflows/` directory
2. Add all workflow files
3. Commit (note: will need to be tested in actual GitHub repo)

---

## Task 4.4: Documentation Updates

### Files to Create/Update

#### 1. `README.md` - Add Deployment Section

Add to existing README:

```markdown
## Deployment

### Local Development

```bash
# Start with Docker Compose
docker-compose up --build

# Backend: http://localhost:8000
# Frontend: http://localhost:3000
```

### Production Deployment

1. Set environment variables:
   - `DATABASE_URL` (PostgreSQL connection string)
   - `SECRET_KEY` (random secret key)
   - `NEXT_PUBLIC_API_URL` (production API URL)

2. Build and run:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

### CI/CD

- Automated tests run on every PR/push
- Coverage threshold: 80%
- Deployment to production on main branch merge

## Environment Setup

Copy `.env.example` to `.env` and adjust settings. See each file for available options.
```

#### 2. `docs/deployment.md`

```markdown
# Deployment Guide

## Prerequisites

- Docker 24+
- Docker Compose 2+
- PostgreSQL 15+ (for local development)

## Quick Start

```bash
# Clone repository
git clone <repo-url>
cd PCCS2

# Copy environment files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local

# Edit .env with your settings

# Build and start
docker-compose up --build
```

## Configuration

### Backend

| Variable | Description | Default |
|----------|-------------|---------|
| DATABASE_URL | PostgreSQL connection | postgresql://pccs:pccs@localhost:5432/pccs2 |
| API_URL | API base URL | http://localhost:8000 |
| SECRET_KEY | Secret key for signing | (required in production) |

### Frontend

| Variable | Description | Default |
|----------|-------------|---------|
| NEXT_PUBLIC_API_URL | Backend API URL | http://localhost:8000 |

## Production Deployment

### Option 1: Docker Compose (Single Server)

```bash
# Build production images
docker-compose build

# Start production services
docker-compose up -d
```

### Option 2: Kubernetes

TODO: Add Kubernetes manifests

### Option 3: Platform as a Service

**Railway:**
1. Import repository
2. Add PostgreSQL add-on
3. Set environment variables
4. Deploy

**Render:**
1. Create Web Service (backend)
2. Create Static Site (frontend)
3. Add PostgreSQL database
4. Configure environment variables

## Health Checks

- Backend: `GET /api/predict/health`
- Frontend: HTTP 200 on root path

## Monitoring

TODO: Add monitoring setup (Prometheus, Grafana, etc.)
```

### Execution

1. Update README.md
2. Create docs/deployment.md
3. Commit

---

## Task 4.5: Final Integration Tests

### Files to Create

#### 1. `backend/tests/integration/test_api_endpoints.py`

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestPredictionAPI:
    def test_predict_health(self):
        """Test prediction health endpoint."""
        response = client.get("/api/predict/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
    
    def test_predict_without_training(self):
        """Test prediction without trained model (should use K-M only)."""
        response = client.post(
            "/api/predict",
            json={
                "recipe": {
                    "layers": [
                        {
                            "ink_items": [
                                {"ink_id": "white", "amount": 100}
                            ]
                        }
                    ]
                },
                "base_color": {"L": 100, "a": 0, "b": 0}
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "km_prediction" in data
        assert "final_prediction" in data
        assert "delta_E" in data
```

### Execution

1. Create integration test file
2. Run tests
3. Verify all pass
4. Commit

---

## Acceptance Criteria

1. Docker compose brings up both services
2. Backend API responds correctly
3. Frontend loads and can make API calls
4. All tests pass (unit + integration)
5. CI/CD workflows configured
6. Documentation complete

---

**Plan complete. Ready to execute.**

Which approach?
1. Subagent-Driven (recommended)
2. Inline Execution

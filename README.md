# PCCS2 - Pad-print Color Correction System v2

패드프린트 잉크 배합비 추천 시스템 - 빅데이터 기반 AI 엔진

## Features

- 패턴 기반 색상 매칭 (Project → Pattern → Round → Sample)
- 1 단계: 수정 Kubelka-Munk 물리 모델
- 2 단계: 머신러닝 보정 (데이터 축적 시)
- SCI/SCE 측색 데이터 지원
- 배합비 시각화 (InkDonutChart)
- 마스터 잉크 등록 (배합 잉크 → 마스터 변환)
- 배합비 복사 기능 (레이어 단위)

- 배합 추천 (/match — K-M 기반 잉크 조합 탐색)
- 색상 예측 (/predict — 하이브리드 K-M + ML 엔진)

## Tech Stack

- **Backend:** Python 3.11, FastAPI, SQLAlchemy 2 (Async), PostgreSQL (운영) / SQLite (개발·테스트)
- **Frontend:** Next.js 16, React 19, TypeScript, Tailwind CSS, TanStack Query
- **ML:** XGBoost, scikit-learn, NumPy/SciPy

## Project Structure

```
PCCS2/
├── backend/                    # FastAPI Backend
│   ├── app/
│   │   ├── models/            # SQLAlchemy ORM models
│   │   ├── api/routers/       # REST API endpoints
│   │   ├── schemas/           # Pydantic request/response schemas
│   │   ├── services/          # K-M/ML engines, color math, recipe matcher
│   │   └── database/          # Async DB session
│   └── tests/
│
├── frontend/                   # Next.js Frontend
│   └── src/
│       ├── app/               # Pages (projects, patterns, samples, inks, match)
│       ├── components/        # UI components
│       └── lib/               # API clients & types (snake_case 계약)
│
└── docs/
    └── superpowers/
        ├── specs/
        └── plans/
```

## Getting Started

### 원클릭 실행 (One-Click Launch)

저장소 루트의 런처 스크립트를 실행하면 백엔드·프론트엔드가 한 번에 뜨고 브라우저가 자동으로 열립니다. 최초 실행 시 의존성 설치까지 자동 처리합니다 (SQLite 사용, PostgreSQL 불필요).

- **Windows**: `start.bat` 더블클릭 (바탕화면 아이콘: 우클릭 → 보내기 → 바탕 화면에 바로 가기 만들기)
- **macOS / Linux**: `./start.sh`

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+ — **운영 환경에서만 필요** (로컬 단독 실행은 SQLite 기본값으로 동작)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# (선택) 환경변수 — 로컬은 설정 없이도 바로 동작한다.
# 기본 DATABASE_URL 이 SQLite(./pccs2.db)이고 테이블은 기동 시 자동 생성된다.
# 값을 바꾸려면 예시를 복사: cp .env.example .env
# PostgreSQL 을 쓰려면 .env 에서 DATABASE_URL 만 바꾸면 된다.

# Start development server (별도 DB 설정 없이 바로 뜬다)
uvicorn app.main:app --reload

# Run tests
pytest tests/ --cov=app
```

> **RDP-DB 화면을 쓰려면**: 백엔드 `.env` 에 `RDP_DB_PATH=<rdp.db 경로>` 를 설정하세요.
> 설정하지 않으면 `~/MySecondBrain/Areas/NIFCO/RDP-DB/rdp.db` 를 시도하며, 그 파일이 없으면
> RDP 가져오기·RDP-DB 화면이 "파일을 찾을 수 없습니다" 로 표시됩니다 (다른 기능은 정상).

API Documentation: http://localhost:8000/docs

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend: http://localhost:3000

### Docker Setup

```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Stop and remove volumes (careful: this deletes database!)
docker-compose down -v
```

#### Docker Compose Services

- **backend** (port 8000): FastAPI backend with ML prediction engine
- **frontend** (port 3000): Next.js React application
- **db** (port 5432): PostgreSQL 15 database

#### Access Points

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health check: http://localhost:8000/api/predict/health

#### Environment Configuration

1. Copy environment templates:
```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
```

2. Edit `backend/.env` with your database credentials
3. Edit `frontend/.env.local` with your backend API URL

#### Production Deployment

For production, ensure you:
- Use strong secrets in `.env` files (generate with `openssl rand -hex 32`)
- Set `DATABASE_URL` to a production PostgreSQL instance
- Configure reverse proxy (nginx/Apache) with SSL
- Use environment-specific docker-compose.override.yml for production settings

### Deployment Checklist

- [ ] Set strong `SECRET_KEY` in production
- [ ] Use external PostgreSQL (RDS, Cloud SQL, etc.)
- [ ] Configure CORS for frontend domain
- [ ] Enable HTTPS with valid SSL certificate
- [ ] Set up database backups
- [ ] Configure monitoring and logging
- [ ] Set environment variables for API keys (if any)

## API Endpoints

### Projects
- `POST /api/projects/` - Create project
- `GET /api/projects/` - List projects
- `GET /api/projects/{id}` - Get project
- `PUT /api/projects/{id}` - Update project
- `DELETE /api/projects/{id}` - Delete project

### Patterns
- `POST /api/patterns/` - Create pattern
- `GET /api/patterns/` - List patterns
- `GET /api/patterns/{id}` - Get pattern
- `PUT /api/patterns/{id}` - Update pattern
- `DELETE /api/patterns/{id}` - Delete pattern

### Rounds
- `POST /api/rounds/pattern/{id}` - Create round
- `GET /api/rounds/` - List rounds
- `GET /api/rounds/{id}` - Get round
- `PUT /api/rounds/{id}` - Update round
- `DELETE /api/rounds/{id}` - Delete round

### Samples
- `POST /api/samples/round/{id}` - Create sample (sample_number 자동 부여)
- `GET /api/samples/` - List samples (`?round_id=`, `?pattern_id=` 필터)
- `GET /api/samples/{id}` - Get sample
- `PUT /api/samples/{id}` - Update sample
- `DELETE /api/samples/{id}` - Delete sample
- `POST /api/samples/{id}/copy-layer` - Copy layer recipe (body: `{source_sample_id, source_layer_number, target_layer_number}`)

### Inks
- `POST /api/inks/` - Create ink
- `GET /api/inks/` - List inks
- `GET /api/inks/{id}` - Get ink
- `PUT /api/inks/{id}` - Update ink
- `DELETE /api/inks/{id}` - Delete ink
- `POST /api/inks/{id}/register-blend` - Register blend as master ink

### Match (Recipe Recommendation)
- `POST /api/match/` - Get recipe recommendations (마스터 잉크 조합 탐색, ΔE 기준 상위 3개)

### Import (RDP-DB 가져오기)
- `POST /api/import/rdp` - rdp.db(SQLite) 업로드 → Project/Pattern/Round/Sample 일괄 변환 (중복 자동 건너뜀)

### Predict (Color Prediction)
- `POST /api/predict/` - Predict color for a recipe (K-M + ML)
- `POST /api/predict/train` - Train ML correction model
- `GET /api/predict/health` - Engine health/training status

## Key Concepts

### Project → Pattern → Round → Sample Hierarchy

```
Project (프로젝트)
└── Pattern (패턴 - 최종 완성 목표)
    ├── Round (작업 라운드 - 작업 기록)
    │   └── Sample (샘플 - 테스트 결과물)
    │       └── layers[] (1 도，2 도, N 도 배합)
    └── Round
        └── Sample
```

### Ink Processing Rules

1. **경화제 (Hardener)** → 투명 (유광) 에 합산
2. **신너 (Thinner)** → 색 성분에서 제외, 희석 계수 계산
3. **나머지 잉크** → 그대로 유지

### Color Data Format

```typescript
{
  L: number,      // 밝기 (0-100)
  a: number,      // 적-녹 축 (-128~127)
  b: number       // 황-청 축 (-128~127)
}
```

Both SCI (Specular Component Included) and SCE (Specular Component Excluded) modes are supported.

## Development Guidelines

- **Immutability**: Never mutate existing objects
- **TDD**: Write tests before implementation
- **Code Review**: Use code-reviewer agent after writing code
- **80% Coverage**: Maintain minimum test coverage
- **Naming**: snake_case (DB/Pydantic), camelCase (TypeScript)

## License

Proprietary - PCCS2 Project

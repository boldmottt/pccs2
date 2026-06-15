#!/usr/bin/env bash
# PCCS2 원클릭 실행 스크립트 (macOS / Linux)
set -e
cd "$(dirname "$0")"

echo "========================================"
echo "  PCCS2 - Pad-print Color Correction"
echo "========================================"

# ---------- Backend ----------
cd backend

if [ ! -d venv ]; then
    echo "[1/4] Python 가상환경 생성 중..."
    python3 -m venv venv
fi

echo "[2/4] 백엔드 의존성 확인 중..."
source venv/bin/activate
pip install -r requirements.txt -q --timeout 60 --retries 10

if [ ! -f .env ]; then
    cat > .env <<EOF
# 로컬 단독 실행용 (SQLite — PostgreSQL 불필요)
DATABASE_URL=sqlite+aiosqlite:///./pccs2.db
CORS_ORIGINS=http://localhost:3000
SECRET_KEY=dev-secret-key
# RDP-DB 화면을 쓰려면 아래 주석을 풀고 본인 rdp.db 경로로 수정:
# RDP_DB_PATH=~/MySecondBrain/Areas/NIFCO/RDP-DB/rdp.db
EOF
fi

echo "[3/4] 백엔드 서버 시작 (http://localhost:8000)..."
uvicorn app.main:app --port 8000 --reload &
BACKEND_PID=$!

# ---------- Frontend ----------
cd ../frontend

if [ ! -d node_modules ]; then
    echo "[4/4] 프론트엔드 의존성 설치 중 (최초 1회, 수 분 소요)..."
    npm install
fi

if [ ! -f .env.local ]; then
    echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
fi

echo "[4/4] 프론트엔드 시작 (http://localhost:3000)..."
npm run dev &
FRONTEND_PID=$!

# ---------- Open browser ----------
sleep 8
if command -v open >/dev/null; then open http://localhost:3000;      # macOS
elif command -v xdg-open >/dev/null; then xdg-open http://localhost:3000; fi  # Linux

echo ""
echo "실행 완료! http://localhost:3000"
echo "종료: Ctrl+C"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait

#!/usr/bin/env bash
# PCCS2 핸드폰 접속용 실행 스크립트 (macOS / Linux)
#
# 컴퓨터에서 이 스크립트를 실행해두면, 같은 WiFi에 연결된 핸드폰 브라우저에서
# 접속할 수 있습니다. (핸드폰에서 직접 실행하는 스크립트가 아닙니다.)
set -e
cd "$(dirname "$0")"

# ---------- 컴퓨터의 WiFi(LAN) IP 자동 탐지 ----------
detect_ip() {
    # macOS: en0(WiFi) 우선
    if command -v ipconfig >/dev/null 2>&1; then
        for iface in en0 en1; do
            ip=$(ipconfig getifaddr "$iface" 2>/dev/null) && [ -n "$ip" ] && { echo "$ip"; return; }
        done
    fi
    # Linux
    if command -v hostname >/dev/null 2>&1; then
        ip=$(hostname -I 2>/dev/null | awk '{print $1}') && [ -n "$ip" ] && { echo "$ip"; return; }
    fi
    echo ""
}

LAN_IP="$(detect_ip)"
if [ -z "$LAN_IP" ]; then
    echo "⚠️  컴퓨터의 WiFi IP를 자동으로 찾지 못했습니다."
    echo "    수동으로 IP를 입력하세요 (예: 192.168.0.10):"
    read -r LAN_IP
fi

echo "========================================"
echo "  PCCS2 - 핸드폰 접속 모드"
echo "  컴퓨터 IP: $LAN_IP"
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
DATABASE_URL=sqlite+aiosqlite:///./pccs2.db
SECRET_KEY=dev-secret-key
# RDP-DB 화면을 쓰려면 아래 주석을 풀고 본인 rdp.db 경로로 수정:
# RDP_DB_PATH=~/MySecondBrain/Areas/NIFCO/RDP-DB/rdp.db
EOF
fi

# 핸드폰(LAN IP)에서의 접속을 허용하도록 CORS를 환경변수로 덮어쓴다.
# (환경변수가 .env 값보다 우선 적용됨)
export CORS_ORIGINS="http://localhost:3000,http://${LAN_IP}:3000"

echo "[3/4] 백엔드 서버 시작 (0.0.0.0:8000)..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# ---------- Frontend ----------
cd ../frontend

if [ ! -d node_modules ]; then
    echo "[4/4] 프론트엔드 의존성 설치 중 (최초 1회, 수 분 소요)..."
    npm install
fi

# 핸드폰 브라우저가 백엔드를 컴퓨터 IP로 호출하도록 API 주소를 지정한다.
echo "NEXT_PUBLIC_API_URL=http://${LAN_IP}:8000" > .env.local

echo "[4/4] 프론트엔드 시작 (0.0.0.0:3000)..."
npm run dev -- --hostname 0.0.0.0 --port 3000 &
FRONTEND_PID=$!

echo ""
echo "========================================"
echo "  실행 완료!"
echo ""
echo "  📱 핸드폰 브라우저에서 접속:"
echo "      http://${LAN_IP}:3000"
echo ""
echo "  (핸드폰이 컴퓨터와 같은 WiFi에 연결돼 있어야 합니다)"
echo "  종료: Ctrl+C"
echo "========================================"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait

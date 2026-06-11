@echo off
chcp 65001 >nul
title PCCS2 Launcher
cd /d "%~dp0"

echo ========================================
echo   PCCS2 - Pad-print Color Correction
echo ========================================
echo.

REM ---------- Backend ----------
cd backend

if not exist venv (
    echo [1/4] Python 가상환경 생성 중...
    python -m venv venv
)

echo [2/4] 백엔드 의존성 확인 중...
call venv\Scripts\activate.bat
pip install -r requirements.txt -q --timeout 60 --retries 10

if not exist .env (
    echo DATABASE_URL=sqlite:///./pccs2.db> .env
    echo SECRET_KEY=dev-secret-key>> .env
)

echo [3/4] 백엔드 서버 시작 (http://localhost:8000)...
start "PCCS2 Backend" cmd /k "cd /d %~dp0backend && call venv\Scripts\activate.bat && uvicorn app.main:app --port 8000 --reload"

REM ---------- Frontend ----------
cd ..\frontend

if not exist node_modules (
    echo [4/4] 프론트엔드 의존성 설치 중 (최초 1회, 수 분 소요)...
    call npm install
)

if not exist .env.local (
    echo NEXT_PUBLIC_API_URL=http://localhost:8000> .env.local
)

echo [4/4] 프론트엔드 시작 (http://localhost:3000)...
start "PCCS2 Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

REM ---------- Open browser ----------
timeout /t 8 /nobreak >nul
start http://localhost:3000

echo.
echo 실행 완료! 브라우저가 열리지 않으면 http://localhost:3000 접속
echo 종료하려면 열린 Backend/Frontend 창을 닫으세요.
pause

@echo off
REM Meridian AI — Full Stack Startup Script (Windows)
REM
REM Usage:
REM   scripts\start.bat              # start everything
REM   scripts\start.bat --seed-only  # just seed data

echo ============================================
echo   Meridian AI — Starting Full Stack
echo ============================================

cd /d "%~dp0\.."

REM Step 1: Start Docker Compose
echo.
echo [1/3] Starting Docker Compose...
docker compose up -d

echo.
echo [2/3] Waiting for DataHub GMS...
timeout /t 30 /nobreak > nul

REM Check if GMS is ready
curl -sf http://localhost:8080/health > nul 2>&1
if %errorlevel% neq 0 (
    echo   DataHub GMS not ready yet, waiting more...
    timeout /t 30 /nobreak > nul
)

echo   DataHub GMS ready!

REM Step 2: Seed DataHub
echo.
echo [3/3] Seeding Meridian Commerce demo data...
set DATAHUB_MOCK=false
set DATAHUB_GMS_URL=http://localhost:8080/api/gms
python scripts\seed_meridian.py

echo.
echo ============================================
echo   Services running:
echo     DataHub UI:   http://localhost:9002
echo     Meridian API: http://localhost:8000/docs
echo     Meridian UI:  http://localhost:3000
echo ============================================

REM Step 3: Start backend
echo.
echo Starting Meridian AI backend...
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

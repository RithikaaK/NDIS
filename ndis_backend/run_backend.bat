@echo off
echo ==========================================
echo  NDIS Backend Setup
echo ==========================================
cd /d C:\new\ndis_backend

echo.
echo [1/3] Installing Python packages in venv...
call venv\Scripts\activate.bat
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: pip install failed. Check Python installation.
    pause
    exit /b 1
)

echo.
echo [2/3] Starting FastAPI backend in new window...
start "NDIS Backend" cmd /k "cd /d C:\new\ndis_backend && call venv\Scripts\activate.bat && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

echo.
echo [3/3] Waiting 8 seconds for backend to start...
timeout /t 8 /nobreak

echo.
echo Running seed.py to populate sample data...
python seed.py

echo.
echo ==========================================
echo  Done! Backend running at http://localhost:8000
echo  Frontend: http://localhost:5173
echo ==========================================
pause

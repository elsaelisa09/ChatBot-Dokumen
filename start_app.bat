@echo off
echo Starting DocumentAI Application...
echo.

echo [1/2] Starting Backend Server...
cd backend
start "DocumentAI Backend" cmd /k "python main_clean.py"

echo [2/2] Starting Frontend Development Server...
cd ..\frontend
start "DocumentAI Frontend" cmd /k "npm run dev"

echo.
echo DocumentAI Application is starting...
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
echo.
echo Press any key to exit...
pause > nul

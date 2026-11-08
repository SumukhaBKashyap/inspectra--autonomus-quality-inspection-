@echo off
title Inspectra Launcher
set "PATH=C:\Users\ASUS\AppData\Local\Programs\nodejs\node-v20.17.0-win-x64;%PATH%"

echo Checking backend on port 8000...
netstat -ano | findstr "LISTENING" | findstr ":8000" >nul
if %errorlevel% neq 0 (
    echo Starting Backend...
    start "Inspectra Backend" cmd /k "cd /d d:\inspectra && py run.py"
) else (
    echo Backend is already running on port 8000.
)

echo Starting Frontend on port 5173...
start "Inspectra Frontend" cmd /k "cd /d d:\inspectra\frontend && set PATH=C:\Users\ASUS\AppData\Local\Programs\nodejs\node-v20.17.0-win-x64;%%PATH%% && node node_modules\vite\bin\vite.js --host 0.0.0.0 --port 5173"

echo.
echo ===================================================
echo Done! Open: http://localhost:5173/
echo ===================================================

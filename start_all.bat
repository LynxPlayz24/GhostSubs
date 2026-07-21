@echo off
title WhisperLive Translator
echo ============================================
echo   WhisperLive JP-to-EN Translation System
echo ============================================
echo.

REM Start the WhisperLive server in a new window
echo [1/3] Starting WhisperLive Server...
start "WhisperLive Server" cmd /k "cd /d %~dp0 && call venv\Scripts\activate && python run_server.py --backend faster_whisper --omp_num_threads 6"

REM Start the screen overlay
echo [2/3] Starting Subtitle Overlay...
start "Subtitle Overlay" cmd /c "cd /d %~dp0 && call venv\Scripts\activate && python screen_overlay.py"

REM Wait for the server to start listening on port 9090
echo [3/3] Waiting for server to be ready...
:wait_for_server
timeout /t 2 /nobreak >nul
netstat -aon 2>nul | findstr ":9090.*LISTENING" >nul 2>&1
if errorlevel 1 (
    echo        Still loading model, please wait...
    goto wait_for_server
)
echo.
echo   Server is ready!
echo.

REM Start the translator client in this window
echo Starting Translator Client...
echo -------------------------------------------
call venv\Scripts\activate
python run_client.py --model small --lang ja --translate --enable_timestamps
echo.
echo Translator stopped.
pause

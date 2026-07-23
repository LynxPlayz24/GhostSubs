@echo off
title WhisperLive Real-Time JP-to-EN Translator
echo ====================================================
echo   WhisperLive Real-Time JP-to-EN Translation System
echo   (large-v3-turbo ASR + OPUS-MT Translation)
echo ====================================================
echo.

REM Start the WhisperLive server in a new window
echo [1/3] Starting WhisperLive Server (Backend: faster_whisper)...
start "WhisperLive Server" cmd /k "cd /d %~dp0 && call venv\Scripts\activate && python run_server.py --backend faster_whisper --omp_num_threads 6 --max_connection_time 86400"

REM Start the screen overlay
echo [2/3] Starting Subtitle Overlay UI...
start "Subtitle Overlay" cmd /c "cd /d %~dp0 && call venv\Scripts\activate && python screen_overlay.py"

REM Wait for the server to start listening on port 9090
echo [3/3] Waiting for WhisperLive server to initialize...
:wait_for_server
timeout /t 2 /nobreak >nul
netstat -aon 2>nul | findstr ":9090.*LISTENING" >nul 2>&1
if errorlevel 1 (
    echo        Loading models and initializing server, please wait...
    goto wait_for_server
)
echo.
echo   Server is ready! Starting live translation stream...
echo ====================================================
echo.

REM Start the translator client in this window
call venv\Scripts\activate
python run_client.py --model large-v3-turbo --lang ja --enable_translation --target_language en --enable_timestamps
echo.
echo [INFO] Translation session ended.
pause

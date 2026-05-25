@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

REM My Agent — Quick Launcher
REM Double-click to start chat!

python agent.py chat

REM Keep window open after session ends
echo.
echo [Session ended. Press any key to close...]
pause >nul

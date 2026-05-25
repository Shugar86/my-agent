@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

REM My Agent — Quick Start
REM Double-click this file to start!

python agent.py chat

pause

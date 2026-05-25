@echo off
chcp 65001 >nul 2>&1
REM My Agent CLI launcher (alias)
REM Usage: my-agent [command] [options]

cd /d "%~dp0"
python agent.py %*

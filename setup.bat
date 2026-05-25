@echo off
chcp 65001 >nul 2>&1
setlocal EnableDelayedExpansion

REM ============================================
REM My Agent - Windows Setup & Launch
REM ============================================

echo.
echo  ============================================
echo   My Agent - Setup
echo  ============================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  [!] Python not found!
    echo  Please install Python 3.10+ from: https://python.org/downloads
    pause
    exit /b 1
)
for /f "tokens=*" %%a in ('python --version') do echo  [OK] %%a

REM Check .env
set "ENV_FILE=%~dp0.env"
if not exist "%ENV_FILE%" (
    echo.
    echo  [!] API keys not configured!
    echo.
    echo  Do you want to set up API keys now? (y/n)
    set /p setup_keys="> "
    if /i "!setup_keys!"=="y" goto SETUP_KEYS
    echo  [i] Skipping key setup. You can edit .env manually.
    goto MENU
)

goto MENU

:SETUP_KEYS
echo.
echo  --- API Key Setup ---
echo  (Press Enter to skip if you don't have one)
echo.

set /p neuro_key="NeuroAPI Key: "
set /p openrouter_key="OpenRouter Key: "
set /p tavily_key="Tavily Key (optional): "

(
echo # My Agent — Configuration
echo NEUROAPI_API_KEY=!neuro_key!
echo OPENROUTER_API_KEY=!openrouter_key!
echo TAVILY_API_KEY=!tavily_key!
echo AGENT_PASSWORD=admin
echo AGENT_SECRET_KEY=change-me-1234567890abcdef
) > "%ENV_FILE%"

echo  [OK] Keys saved to .env
goto MENU

:MENU
cls
echo.
echo  ============================================
echo   My Agent - Ready!
echo  ============================================
echo.
echo  Choose action:
echo.
echo   [1] Start Chat (default model)
echo   [2] Start Chat with Smart Model
echo   [3] Start Chat with Fast Model
echo   [4] System Status
echo   [5] Create Desktop Shortcut
echo   [6] Add to PATH
echo   [7] Edit API Keys
echo   [8] Exit
echo.
set /p choice="> "

if "%choice%"=="1" goto CHAT
if "%choice%"=="2" goto CHAT_SMART
if "%choice%"=="3" goto CHAT_FAST
if "%choice%"=="4" goto STATUS
if "%choice%"=="5" goto SHORTCUT
if "%choice%"=="6" goto ADD_PATH
if "%choice%"=="7" goto EDIT_KEYS
if "%choice%"=="8" exit /b 0
goto MENU

:CHAT
cd /d "%~dp0"
python "%~dp0agent.py" chat
goto MENU

:CHAT_SMART
cd /d "%~dp0"
python "%~dp0agent.py" chat --model smart
goto MENU

:CHAT_FAST
cd /d "%~dp0"
python "%~dp0agent.py" chat --model fast
goto MENU

:STATUS
cd /d "%~dp0"
python "%~dp0agent.py" status
pause
goto MENU

:SHORTCUT
cd /d "%~dp0"
python "%~dp0scripts\create_shortcut.py"
echo  [OK] Shortcut created!
pause
goto MENU

:ADD_PATH
echo.
echo  Adding to PATH...
setx PATH "%PATH%;%~dp0" >nul 2>&1
if errorlevel 1 (
    echo  [!] Failed. Run as Administrator or add manually.
) else (
    echo  [OK] Added! Restart terminal and type: agent
)
pause
goto MENU

:EDIT_KEYS
notepad "%ENV_FILE%" 2>nul || (
    echo  [!] Could not open notepad. Edit: %ENV_FILE%
    pause
)
goto MENU

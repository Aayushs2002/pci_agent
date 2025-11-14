@echo off
title PCI Compliance Agent
color 0A

REM Get the directory where this batch file is located
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM Check if pci-agent.exe exists
if not exist "%SCRIPT_DIR%pci-agent.exe" (
    echo ERROR: pci-agent.exe not found in %SCRIPT_DIR%
    echo Please make sure launcher.bat is in the same folder as pci-agent.exe
    pause
    exit /b 1
)

:MENU
cls
echo.
echo ========================================
echo   PCI Compliance Agent - Launcher
echo ========================================
echo.
echo What would you like to do?
echo.
echo   1. Start Agent (Connect to Server)
echo   2. Run Quick Scan
echo   3. Show Agent Information
echo   4. Exit
echo.
echo ========================================
echo.
set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" goto START_AGENT
if "%choice%"=="2" goto QUICK_SCAN
if "%choice%"=="3" goto INFO
if "%choice%"=="4" goto EXIT
echo Invalid choice. Please try again.
timeout /t 2 >nul
goto MENU

:START_AGENT
cls
echo.
echo ========================================
echo   Starting PCI Compliance Agent
echo ========================================
echo.
echo NOTE: Use HTTP (not HTTPS) unless your server has SSL enabled
echo.
echo Examples:
echo   - Local:  http://localhost:3001
echo   - Remote: http://192.168.1.100:3001
echo.
set /p SERVER_URL="Enter server URL [default: http://localhost:3001]: "
if "%SERVER_URL%"=="" set SERVER_URL=http://localhost:3001

echo.
echo Connecting to server: %SERVER_URL%
echo Press Ctrl+C to stop the agent
echo.
"%SCRIPT_DIR%pci-agent.exe" --websocket-mode --server-url %SERVER_URL%

echo.
echo Agent stopped.
pause
goto MENU

:QUICK_SCAN
cls
echo.
echo ========================================
echo   Quick Scan Mode
echo ========================================
echo.
set /p OPERATOR="Enter your name: "
if "%OPERATOR%"=="" (
    echo ERROR: Operator name is required!
    pause
    goto MENU
)

set /p SCAN_DIR="Enter directory to scan (e.g., C:\Data): "
if "%SCAN_DIR%"=="" (
    echo ERROR: Directory is required!
    pause
    goto MENU
)

echo.
echo Starting scan...
echo Operator: %OPERATOR%
echo Directory: %SCAN_DIR%
echo.
"%SCRIPT_DIR%pci-agent.exe" --operator "%OPERATOR%" --directories "%SCAN_DIR%"

echo.
echo Scan completed!
pause
goto MENU

:INFO
cls
echo.
echo ========================================
echo   Agent Information
echo ========================================
echo.
"%SCRIPT_DIR%pci-agent.exe" --help
echo.
pause
goto MENU

:EXIT
cls
echo.
echo Thank you for using PCI Compliance Agent!
echo.
timeout /t 2 >nul
exit

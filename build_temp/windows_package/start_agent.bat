@echo off
echo PCI Compliance Agent Starter
echo ============================
echo.

set INSTALL_DIR=C:\Program Files\PCI-Compliance-Agent

if not exist "%INSTALL_DIR%\pci-agent.exe" (
    echo ERROR: Agent not installed!
    echo Please run install.bat first.
    pause
    exit /b 1
)

cd /d "%INSTALL_DIR%"

echo Starting PCI Compliance Agent...
echo.
echo Press Ctrl+C to stop the agent
echo.

REM Prompt for server URL if not configured
set /p SERVER_URL="Enter server URL (e.g., http://localhost:3001): "

if "%SERVER_URL%"=="" (
    echo ERROR: Server URL is required
    pause
    exit /b 1
)

REM Start the agent
pci-agent.exe --websocket-mode --server-url %SERVER_URL%

pause

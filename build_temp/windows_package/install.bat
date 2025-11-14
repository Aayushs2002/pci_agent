@echo off
echo PCI Compliance Agent Installer
echo ==============================
echo.

REM Check if running as Administrator
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: This installer must be run as Administrator!
    echo Right-click install.bat and select "Run as administrator"
    echo.
    pause
    exit /b 1
)

REM Get the directory where the script is located
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM Check if files exist
if not exist "%SCRIPT_DIR%pci-agent.exe" (
    echo ERROR: pci-agent.exe not found in current directory!
    echo Please make sure you extracted all files from the ZIP.
    echo Current directory: %SCRIPT_DIR%
    echo.
    pause
    exit /b 1
)

if not exist "%SCRIPT_DIR%config.yaml" (
    echo ERROR: config.yaml not found in current directory!
    echo Please make sure you extracted all files from the ZIP.
    echo Current directory: %SCRIPT_DIR%
    echo.
    pause
    exit /b 1
)

REM Create installation directory
set INSTALL_DIR=C:\Program Files\PCI-Compliance-Agent
echo Creating installation directory: %INSTALL_DIR%
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

REM Copy files
echo Copying files...
copy /Y "%SCRIPT_DIR%pci-agent.exe" "%INSTALL_DIR%\pci-agent.exe"
if %errorlevel% neq 0 (
    echo ERROR: Failed to copy pci-agent.exe
    pause
    exit /b 1
)
echo   - pci-agent.exe copied

copy /Y "%SCRIPT_DIR%config.yaml" "%INSTALL_DIR%\config.yaml"
if %errorlevel% neq 0 (
    echo ERROR: Failed to copy config.yaml
    pause
    exit /b 1
)
echo   - config.yaml copied

REM Copy launcher if exists
if exist "%SCRIPT_DIR%launcher.bat" (
    copy /Y "%SCRIPT_DIR%launcher.bat" "%INSTALL_DIR%\launcher.bat"
    echo   - launcher.bat copied
)

REM Create logs and reports directories
echo Creating directories...
if not exist "%INSTALL_DIR%\logs" mkdir "%INSTALL_DIR%\logs"
echo   - logs directory created
if not exist "%INSTALL_DIR%\reports" mkdir "%INSTALL_DIR%\reports"
echo   - reports directory created

echo.
echo ========================================
echo Installation complete!
echo ========================================
echo.
echo Agent location: %INSTALL_DIR%
echo Configuration: %INSTALL_DIR%\config.yaml
echo Logs: %INSTALL_DIR%\logs
echo Reports: %INSTALL_DIR%\reports
echo.
echo IMPORTANT: Edit the configuration file to set your server URL:
echo   notepad "%INSTALL_DIR%\config.yaml"
echo.
echo To start the agent:
echo   Option 1: Double-click launcher.bat (User-friendly menu)
echo   Option 2: Use command line:
echo     cd "%INSTALL_DIR%"
echo     pci-agent.exe --websocket-mode --server-url http://your-server:3001
echo.
pause

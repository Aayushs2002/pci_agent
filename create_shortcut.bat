@echo off
echo Creating Desktop Shortcut...

set TARGET="C:\Program Files\PCI-Compliance-Agent\launcher.bat"
set SHORTCUT="%USERPROFILE%\Desktop\PCI Agent.lnk"
set ICON="C:\Program Files\PCI-Compliance-Agent\pci-agent.exe"

powershell -Command "$WS = New-Object -ComObject WScript.Shell; $SC = $WS.CreateShortcut('%SHORTCUT%'); $SC.TargetPath = '%TARGET%'; $SC.WorkingDirectory = 'C:\Program Files\PCI-Compliance-Agent'; $SC.IconLocation = '%ICON%'; $SC.Description = 'PCI Compliance Agent Launcher'; $SC.Save()"

if exist %SHORTCUT% (
    echo.
    echo ✓ Desktop shortcut created successfully!
    echo.
    echo You can now double-click "PCI Agent" on your desktop.
) else (
    echo.
    echo ✗ Failed to create shortcut
)

echo.
pause

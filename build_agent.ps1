# PCI Compliance Agent Builder - Windows PowerShell Script
# This script builds the agent installer for Windows

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "PCI Compliance Agent Builder for Windows" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
Write-Host "Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found. Please install Python 3.8 or higher." -ForegroundColor Red
    exit 1
}

# Check if we're in the agent directory
if (-not (Test-Path "main.py")) {
    Write-Host "✗ Error: main.py not found. Please run this script from the pci-compliance-agent directory." -ForegroundColor Red
    exit 1
}

# Install build dependencies
Write-Host ""
Write-Host "Installing build dependencies..." -ForegroundColor Yellow
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Run the build script
Write-Host ""
Write-Host "Building agent installer..." -ForegroundColor Yellow
python build_agent.py

# Check if build was successful
if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "==================================================" -ForegroundColor Green
    Write-Host "✓ Build completed successfully!" -ForegroundColor Green
    Write-Host "==================================================" -ForegroundColor Green
    Write-Host ""
    
    if (Test-Path "installers") {
        Write-Host "Installers created:" -ForegroundColor Cyan
        Get-ChildItem "installers" -Filter "*.zip" | ForEach-Object {
            $sizeMB = [math]::Round($_.Length / 1MB, 2)
            Write-Host "  📦 $($_.Name) ($sizeMB MB)" -ForegroundColor White
        }
        Write-Host ""
        Write-Host "Installation packages are ready for deployment!" -ForegroundColor Green
        Write-Host "You can now upload these to your server or distribute them manually." -ForegroundColor Gray
    }
} else {
    Write-Host ""
    Write-Host "✗ Build failed. Please check the error messages above." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
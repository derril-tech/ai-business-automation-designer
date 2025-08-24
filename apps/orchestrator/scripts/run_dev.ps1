# AI Business Automation Designer - Development Script for Windows
# Run this script to test the CrewAI system locally

Write-Host "🚀 AI Business Automation Designer - Development Test Suite" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Cyan

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python 3.9+ and try again." -ForegroundColor Red
    exit 1
}

# Check if we're in the right directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$orchestratorDir = Split-Path -Parent $scriptDir
$appDir = Join-Path $orchestratorDir "app"

if (-not (Test-Path $appDir)) {
    Write-Host "❌ App directory not found. Please run this script from the orchestrator directory." -ForegroundColor Red
    exit 1
}

# Set environment variables
$env:PYTHONPATH = $orchestratorDir
$env:OPENAI_API_KEY = "your-openai-api-key"
$env:ANTHROPIC_API_KEY = "your-anthropic-api-key"
$env:CREWAI_LLM_MODEL = "gpt-4"
$env:CREWAI_VERBOSE = "true"
$env:CREWAI_MAX_ITERATIONS = "10"

Write-Host "📁 Working directory: $orchestratorDir" -ForegroundColor Yellow
Write-Host "🔧 Environment variables set" -ForegroundColor Yellow

# Check if required packages are installed
Write-Host "`n🔍 Checking required packages..." -ForegroundColor Cyan

$requiredPackages = @("crewai", "fastapi", "pydantic", "structlog")
$missingPackages = @()

foreach ($package in $requiredPackages) {
    try {
        python -c "import $package" 2>$null
        Write-Host "   ✅ $package" -ForegroundColor Green
    } catch {
        Write-Host "   ❌ $package (missing)" -ForegroundColor Red
        $missingPackages += $package
    }
}

if ($missingPackages.Count -gt 0) {
    Write-Host "`n📦 Installing missing packages..." -ForegroundColor Yellow
    foreach ($package in $missingPackages) {
        Write-Host "   Installing $package..." -ForegroundColor Yellow
        pip install $package
    }
}

# Run the development test script
Write-Host "`n🧪 Running development tests..." -ForegroundColor Cyan

try {
    python scripts/run_dev.py
    Write-Host "`n✅ Development tests completed successfully!" -ForegroundColor Green
} catch {
    Write-Host "`n❌ Development tests failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host "`n🎉 All done! The CrewAI system is ready for development." -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "1. Set your actual API keys in the environment variables" -ForegroundColor White
Write-Host "2. Run 'python -m uvicorn main:app --reload' to start the FastAPI server" -ForegroundColor White
Write-Host "3. Visit http://localhost:8000/docs to see the API documentation" -ForegroundColor White

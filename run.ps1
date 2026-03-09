# The Steady Compass - One script: update packages, push to Git, run app
# Usage:
#   .\run.ps1              # Update packages, then run app
#   .\run.ps1 -UpdateOnly  # Update packages only
#   .\run.ps1 -RunOnly     # Run app only (no update)
#   .\run.ps1 -Push        # Update, push to Git (y/n), then run app
#   .\run.ps1 -PushOnly    # Update, push to Git (y/n), do not run app
#   .\run.ps1 -Push -Message "Your commit message"
# If script won't run: Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
#   or: powershell -ExecutionPolicy Bypass -File .\run.ps1

param(
    [switch]$UpdateOnly,
    [switch]$RunOnly,
    [switch]$Push,
    [switch]$PushOnly,
    [string]$Message = "Update: S&P 500 annual returns chart, mobile, scripts"
)

$ProjectRoot = $PSScriptRoot
Set-Location $ProjectRoot

# --- 1. Update packages (unless RunOnly) ---
if (-not $RunOnly) {
    Write-Host "Updating Python packages..." -ForegroundColor Cyan
    python -m pip install --upgrade pip -q
    python -m pip install -r requirements.txt --upgrade -q
    if ($LASTEXITCODE -ne 0) {
        Write-Host "pip install failed. Check requirements.txt." -ForegroundColor Red
        exit 1
    }
    Write-Host "Packages updated." -ForegroundColor Green
}

# --- 2. Push to Git (if -Push or -PushOnly) ---
if ($Push -or $PushOnly) {
    Write-Host "Adding changed files..." -ForegroundColor Cyan
    git add app.py pages/ components/ requirements.txt .streamlit/ .cursorrules .gitignore *.ps1
    git add -A
    Write-Host "Status:" -ForegroundColor Cyan
    git status
    $confirm = Read-Host "Commit and push to origin main? (y/n)"
    if ($confirm -eq 'y' -or $confirm -eq 'Y') {
        git commit -m "$Message"
        if ($LASTEXITCODE -eq 0) {
            git push origin main
            if ($LASTEXITCODE -eq 0) {
                Write-Host "Pushed. Deployed app will update after host pulls." -ForegroundColor Green
            } else {
                Write-Host "Push failed. Check remote (origin main)." -ForegroundColor Red
                exit 1
            }
        } else {
            Write-Host "Commit failed (nothing to commit or error)." -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "Push cancelled." -ForegroundColor Yellow
    }
}

# --- 3. Run app (unless UpdateOnly or PushOnly) ---
if (-not $UpdateOnly -and -not $PushOnly) {
    Write-Host "Starting Streamlit app..." -ForegroundColor Cyan
    Write-Host "Press Ctrl+C to stop." -ForegroundColor Gray
    streamlit run app.py
}

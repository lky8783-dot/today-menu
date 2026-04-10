$ErrorActionPreference = "Stop"

$repoRoot = "C:\tistory-auto\today-menu-repo"
$pythonExe = "python"
$playwrightPython = "C:\tistory-auto\venv\Scripts\python.exe"
$logDir = Join-Path $repoRoot "logs"
$logFile = Join-Path $logDir "menu-update.log"

New-Item -ItemType Directory -Force -Path $logDir | Out-Null

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$timestamp] $Message"
    $line | Out-File -FilePath $logFile -Append -Encoding utf8
    Write-Output $line
}

Set-Location $repoRoot

try {
    Write-Log "Start menu update"

    if (Test-Path ".git\index.lock") {
        Remove-Item ".git\index.lock" -Force
        Write-Log "Removed stale git index.lock"
    }

    & git pull --rebase origin main
    if ($LASTEXITCODE -ne 0) {
        throw "git pull --rebase failed"
    }

    & $pythonExe "scripts\fetch_kakao_profile_images.py"
    if ($LASTEXITCODE -ne 0) {
        throw "fetch_kakao_profile_images.py failed"
    }

    if (Test-Path $playwrightPython) {
        & $playwrightPython "scripts\fetch_dynamic_menu_images.py"
        if ($LASTEXITCODE -ne 0) {
            throw "fetch_dynamic_menu_images.py failed"
        }
    } else {
        Write-Log "Playwright Python not found. Skip dynamic image fetch."
    }

    & $pythonExe "scripts\update_menu_from_ocr.py"
    if ($LASTEXITCODE -ne 0) {
        throw "update_menu_from_ocr.py failed"
    }

    & $pythonExe "scripts\build_menu_page.py"
    if ($LASTEXITCODE -ne 0) {
        throw "build_menu_page.py failed"
    }

    & git add "menu-today\collection_log.json" "menu-today\dynamic_menu_hints.json" "menu-today\images\*.png" "menu-today\index.html" "menu-today\menu_today.json"
    if ($LASTEXITCODE -ne 0) {
        throw "git add failed"
    }

    & git diff --cached --quiet
    if ($LASTEXITCODE -eq 0) {
        Write-Log "No changes to commit"
        exit 0
    }

    $commitTime = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    & git commit -m "Auto update menu board ($commitTime)"
    if ($LASTEXITCODE -ne 0) {
        throw "git commit failed"
    }

    & git push origin main
    if ($LASTEXITCODE -ne 0) {
        throw "git push failed"
    }

    Write-Log "Menu update completed"
    exit 0
}
catch {
    Write-Log "FAILED: $($_.Exception.Message)"
    exit 1
}

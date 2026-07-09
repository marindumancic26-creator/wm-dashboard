$ErrorActionPreference = "Stop"

$repo = $PSScriptRoot
$today = Get-Date -Format "yyyy-MM-dd"
$marker = Join-Path $repo "data\snapshots\daily_success_${today}.ok"
$log = Join-Path $repo "data\snapshots\automation_watchdog.log"
$runner = Join-Path $repo "run_daily.ps1"
$pagesWatchdog = Join-Path $repo "run_pages_watchdog.ps1"
$githubPagesHealth = Join-Path $repo "run_github_pages_health.ps1"
$powershell = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
$dailyMutex = [Threading.Mutex]::new($false, "Local\WM-Dashboard-Daily")
$hasDailyLock = $false

function Write-WatchdogLog {
    param([string]$Message)
    $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    for ($attempt = 1; $attempt -le 5; $attempt++) {
        try {
            $line | Out-File -LiteralPath $log -Append -Encoding utf8
            return
        }
        catch {
            Start-Sleep -Milliseconds (200 * $attempt)
        }
    }
}

try {
    if (Test-Path -LiteralPath $marker) {
        Write-WatchdogLog "Daily-Lauf fuer $today bereits erfolgreich; Pages-Status wird geprueft."
        & $powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $pagesWatchdog
        $pagesCode = $LASTEXITCODE
        if ($pagesCode -ne 0) {
            Write-WatchdogLog "Pages-Watchdog meldete Exit $pagesCode; Daily-Recovery bleibt unberuehrt."
        }
        & $powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $githubPagesHealth
        $healthCode = $LASTEXITCODE
        if ($healthCode -ne 0) {
            Write-WatchdogLog "GitHub-Pages-Health-Check meldete Exit $healthCode; Daily-Recovery bleibt unberuehrt."
        }
        if ($pagesCode -ne 0) {
            exit $pagesCode
        }
        if ($healthCode -ne 0) {
            exit $healthCode
        }
        exit 0
    }

    try {
        $hasDailyLock = $dailyMutex.WaitOne(0)
    }
    catch [Threading.AbandonedMutexException] {
        $hasDailyLock = $true
    }
    if (-not $hasDailyLock) {
        Write-WatchdogLog "Daily-Lauf fuer $today ist bereits aktiv; Watchdog startet keinen zweiten Lauf."
        exit 0
    }
    $dailyMutex.ReleaseMutex()
    $hasDailyLock = $false

    Write-WatchdogLog "Erfolgsmarke fuer $today fehlt; Recovery-Lauf wird gestartet."
    & $powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $runner
    $runnerCode = $LASTEXITCODE
    if ($runnerCode -ne 0) {
        Write-WatchdogLog "Recovery-Lauf fehlgeschlagen (Exit $runnerCode)."
        exit $runnerCode
    }
    if (-not (Test-Path -LiteralPath $marker)) {
        Write-WatchdogLog "Recovery-Lauf ohne Erfolgsmarke beendet; naechster Watchdog prueft erneut."
        exit 0
    }

    Write-WatchdogLog "Recovery-Lauf erfolgreich abgeschlossen."
    & $powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $pagesWatchdog
    $pagesCode = $LASTEXITCODE
    if ($pagesCode -ne 0) {
        Write-WatchdogLog "Pages-Watchdog nach Recovery meldete Exit $pagesCode."
    }
    & $powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $githubPagesHealth
    $healthCode = $LASTEXITCODE
    if ($healthCode -ne 0) {
        Write-WatchdogLog "GitHub-Pages-Health-Check nach Recovery meldete Exit $healthCode."
    }
    if ($pagesCode -ne 0) {
        exit $pagesCode
    }
    if ($healthCode -ne 0) {
        exit $healthCode
    }
    exit 0
}
catch {
    Write-WatchdogLog "FEHLER im Daily-Watchdog: $($_.Exception.Message)"
    exit 1
}
finally {
    if ($hasDailyLock) {
        $dailyMutex.ReleaseMutex()
    }
    $dailyMutex.Dispose()
}

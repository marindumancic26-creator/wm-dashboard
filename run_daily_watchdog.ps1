$ErrorActionPreference = "Stop"

$repo = $PSScriptRoot
$today = Get-Date -Format "yyyy-MM-dd"
$marker = Join-Path $repo "data\snapshots\daily_success_${today}.ok"
$log = Join-Path $repo "data\snapshots\automation_watchdog.log"
$runner = Join-Path $repo "run_daily.ps1"
$powershell = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"

function Write-WatchdogLog {
    param([string]$Message)
    "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message |
        Out-File -LiteralPath $log -Append -Encoding utf8
}

try {
    if (Test-Path -LiteralPath $marker) {
        Write-WatchdogLog "Daily-Lauf fuer $today bereits erfolgreich; kein Recovery noetig."
        exit 0
    }

    Write-WatchdogLog "Erfolgsmarke fuer $today fehlt; Recovery-Lauf wird gestartet."
    & $powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $runner
    $runnerCode = $LASTEXITCODE
    if ($runnerCode -ne 0) {
        Write-WatchdogLog "Recovery-Lauf fehlgeschlagen (Exit $runnerCode)."
        exit $runnerCode
    }
    if (-not (Test-Path -LiteralPath $marker)) {
        Write-WatchdogLog "Recovery-Lauf ohne Erfolgsmarke beendet; vermutlich laeuft bereits eine andere Instanz."
        exit 1
    }

    Write-WatchdogLog "Recovery-Lauf erfolgreich abgeschlossen."
    exit 0
}
catch {
    Write-WatchdogLog "FEHLER im Daily-Watchdog: $($_.Exception.Message)"
    exit 1
}

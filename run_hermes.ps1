$ErrorActionPreference = "Stop"

$repo = $PSScriptRoot
$log = Join-Path $repo "data\snapshots\automation_hermes.log"
$codex = "C:\Users\marin\AppData\Roaming\npm\codex.cmd"
$prompt = @"
Lies HERMES.md in diesem Projekt und fuehre die taegliche Hermes-Analyse aus (Schritte 2 bis 5).
Lies den heutigen Snapshot data/processed/dashboard_data.json und die heutigen Dateien in memory/daily_runs/.
Schreibe das Hermes-Narrativ in den heutigen closing_loop-Report unter '## Hermes-Analyse' und haenge
einen datierten Eintrag an memory/learnings.md an. Halte dich strikt an HERMES.md, aendere keinen
Quellcode und uebernimm keine Modell-, Gewichts- oder Staking-Parameter automatisch.
"@

function Write-HermesLog {
    param([string]$Message)
    "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message |
        Out-File -LiteralPath $log -Append -Encoding utf8
}

function Invoke-Logged {
    param(
        [string]$Command,
        [string[]]$Arguments
    )

    $previousPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = "Continue"
        & $Command @Arguments 2>&1 | Out-File -LiteralPath $log -Append -Encoding utf8
        return $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previousPreference
    }
}

try {
    Set-Location -LiteralPath $repo
    $env:OPENAI_API_KEY = $null
    Write-HermesLog "Automatische Hermes-Analyse gestartet."

    $codexCode = Invoke-Logged $codex @(
        "exec", "-C", ".", "-s", "workspace-write",
        "-c", 'approval_policy="never"', "--skip-git-repo-check",
        "-o", "data\snapshots\hermes_last.md", $prompt
    )
    if ($codexCode -ne 0) {
        Write-HermesLog "FEHLER: Hermes-Analyse fehlgeschlagen (Exit $codexCode); kein Commit und kein Push."
        exit $codexCode
    }

    $addCode = Invoke-Logged "git" @("add", "memory\daily_runs", "memory\learnings.md")
    if ($addCode -ne 0) {
        Write-HermesLog "FEHLER: git add fehlgeschlagen (Exit $addCode)."
        exit $addCode
    }

    $commitCode = Invoke-Logged "git" @("commit", "-m", ("Hermes-Analyse {0}" -f (Get-Date -Format "yyyy-MM-dd")))
    if ($commitCode -ne 0) {
        Write-HermesLog "Kein Hermes-Commit noetig oder Commit fehlgeschlagen (Exit $commitCode)."
    }

    $pushCode = Invoke-Logged "git" @("push")
    if ($pushCode -ne 0) {
        Write-HermesLog "FEHLER: git push fehlgeschlagen (Exit $pushCode)."
        exit $pushCode
    }

    Write-HermesLog "Automatische Hermes-Analyse erfolgreich beendet."
    exit 0
}
catch {
    Write-HermesLog "FEHLER im Hermes-Runner: $($_.Exception.Message)"
    exit 1
}

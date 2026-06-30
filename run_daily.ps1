$ErrorActionPreference = "Stop"

$repo = $PSScriptRoot
$log = Join-Path $repo "data\snapshots\automation_daily.log"
$successMarker = Join-Path $repo ("data\snapshots\daily_success_{0}.ok" -f (Get-Date -Format "yyyy-MM-dd"))
$mutex = [Threading.Mutex]::new($false, "Local\WM-Dashboard-Daily")
$hasLock = $false

function Write-RunLog {
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
    try {
        $hasLock = $mutex.WaitOne(0)
    }
    catch [Threading.AbandonedMutexException] {
        $hasLock = $true
    }

    if (-not $hasLock) {
        Write-RunLog "Daily-Lauf uebersprungen: Ein anderer Lauf ist noch aktiv."
        exit 0
    }

    Set-Location -LiteralPath $repo
    Write-RunLog "Automatischer Daily-Lauf gestartet."

    $pullCode = Invoke-Logged "git" @("pull", "--rebase", "--autostash")
    if ($pullCode -ne 0) {
        Write-RunLog "WARNUNG: git pull fehlgeschlagen (Exit $pullCode); Pipeline laeuft mit lokalem Stand weiter."
    }

    $pipelineCode = Invoke-Logged "python" @("-m", "src.pipeline.daily_matchday_run")
    if ($pipelineCode -ne 0) {
        Write-RunLog "FEHLER: Pipeline fehlgeschlagen (Exit $pipelineCode); kein Commit und kein Push."
        exit $pipelineCode
    }

    $addCode = Invoke-Logged "git" @("add", "-A")
    if ($addCode -ne 0) {
        Write-RunLog "FEHLER: git add fehlgeschlagen (Exit $addCode)."
        exit $addCode
    }

    $commitMessage = "Daily run {0}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
    $commitCode = Invoke-Logged "git" @("commit", "-m", $commitMessage)
    if ($commitCode -ne 0) {
        Write-RunLog "Kein Commit noetig oder Commit fehlgeschlagen (Exit $commitCode)."
    }

    $pushCode = Invoke-Logged "git" @("push")
    if ($pushCode -ne 0) {
        Write-RunLog "FEHLER: git push fehlgeschlagen (Exit $pushCode)."
        exit $pushCode
    }

    Write-RunLog "Automatischer Daily-Lauf erfolgreich beendet."
    [IO.File]::WriteAllText($successMarker, (Get-Date).ToString("o"),
                            [Text.UTF8Encoding]::new($false))
    exit 0
}
catch {
    Write-RunLog "FEHLER im Daily-Runner: $($_.Exception.Message)"
    exit 1
}
finally {
    if ($hasLock) {
        $mutex.ReleaseMutex()
    }
    $mutex.Dispose()
}

$ErrorActionPreference = "Stop"

$repo = $PSScriptRoot
$log = Join-Path $repo "data\snapshots\automation_pages_watchdog.log"
$stateDir = Join-Path $repo "data\snapshots\pages_retry_state"
$retryFile = Join-Path $repo "docs\.pages-retry"
$mutex = [Threading.Mutex]::new($false, "Local\WM-Dashboard-PagesWatchdog")
$hasLock = $false
$maxRetriesPerCommit = 3

function Write-PagesLog {
    param([string]$Message)
    $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    for ($attempt = 1; $attempt -le 5; $attempt++) {
        try {
            New-Item -ItemType Directory -Force -Path (Split-Path -Parent $log) | Out-Null
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
        [string[]]$Arguments,
        [int]$TimeoutSeconds = 180
    )
    $stdout = [IO.Path]::GetTempFileName()
    $stderr = [IO.Path]::GetTempFileName()
    try {
        $argumentLine = ($Arguments | ForEach-Object { ConvertTo-CommandArgument $_ }) -join " "
        $process = Start-Process -FilePath $Command -ArgumentList $argumentLine `
            -NoNewWindow -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr
        if (-not $process.WaitForExit($TimeoutSeconds * 1000)) {
            Write-PagesLog "FEHLER: $Command Zeitlimit nach $TimeoutSeconds Sekunden."
            Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
            return 124
        }
        foreach ($path in @($stdout, $stderr)) {
            if ((Test-Path -LiteralPath $path) -and (Get-Item -LiteralPath $path).Length -gt 0) {
                Get-Content -LiteralPath $path -Raw -Encoding utf8 |
                    Out-File -LiteralPath $log -Append -Encoding utf8
            }
        }
        $process.Refresh()
        if ($null -eq $process.ExitCode) {
            return 0
        }
        return $process.ExitCode
    }
    finally {
        Remove-Item -LiteralPath $stdout, $stderr -Force -ErrorAction SilentlyContinue
    }
}

function ConvertTo-CommandArgument {
    param([string]$Argument)
    if ($Argument -notmatch '[\s"]') {
        return $Argument
    }
    return '"' + ($Argument -replace '\\', '\\' -replace '"', '\"') + '"'
}

try {
    try {
        $hasLock = $mutex.WaitOne(0)
    }
    catch [Threading.AbandonedMutexException] {
        $hasLock = $true
    }
    if (-not $hasLock) {
        Write-PagesLog "Pages-Watchdog uebersprungen: Ein anderer Pages-Watchdog ist aktiv."
        exit 0
    }

    Set-Location -LiteralPath $repo
    New-Item -ItemType Directory -Force -Path $stateDir | Out-Null

    $checkJson = & python -m src.pipeline.pages_publish_check
    $checkCode = $LASTEXITCODE
    if ($checkCode -ne 0) {
        Write-PagesLog "FEHLER: Pages-Check fehlgeschlagen (Exit $checkCode)."
        exit 0
    }
    $check = $checkJson | ConvertFrom-Json
    Write-PagesLog ("Pages-Status {0}: lokal={1}, remote={2}, note={3}" -f
        $check.status, $check.local_generated_at, $check.remote_generated_at, $check.note)

    if ($check.status -eq "fresh") {
        exit 0
    }
    $retryableStatuses = @("stale", "missing_remote")
    if ($retryableStatuses -notcontains $check.status) {
        Write-PagesLog "Kein Retry: Status ist $($check.status)."
        exit 0
    }

    $head = (& git rev-parse --short HEAD).Trim()
    $stateKey = (($check.local_generated_at, $check.remote_generated_at, $check.status) -join "_")
    $stateKey = [Regex]::Replace($stateKey, "[^0-9A-Za-z._-]", "_")
    if ([string]::IsNullOrWhiteSpace($stateKey)) {
        $stateKey = $head
    }
    $stateFile = Join-Path $stateDir "$stateKey.txt"
    $retryCount = 0
    if (Test-Path -LiteralPath $stateFile) {
        [int]::TryParse((Get-Content -LiteralPath $stateFile -Raw).Trim(), [ref]$retryCount) | Out-Null
    }
    if ($retryCount -ge $maxRetriesPerCommit) {
        Write-PagesLog "Kein Retry: Limit $maxRetriesPerCommit fuer Pages-Stand $stateKey erreicht."
        exit 0
    }

    $stagedDiff = & git diff --cached --name-only
    if (-not [string]::IsNullOrWhiteSpace($stagedDiff)) {
        Write-PagesLog "Kein Retry: Es gibt bereits staged Changes; Watchdog fasst den Index nicht an."
        exit 0
    }

    $attempt = $retryCount + 1
    $msg = "Retry GitHub Pages deploy $head attempt $attempt"
    $retryPayload = @(
        "retry_at=$((Get-Date).ToString('o'))",
        "source_head=$head",
        "status=$($check.status)",
        "local_generated_at=$($check.local_generated_at)",
        "remote_generated_at=$($check.remote_generated_at)",
        "attempt=$attempt"
    ) -join "`n"
    [IO.File]::WriteAllText($retryFile, $retryPayload, [Text.UTF8Encoding]::new($false))
    $addCode = Invoke-Logged "git" @("add", "docs\.pages-retry") 180
    if ($addCode -ne 0) {
        Write-PagesLog "FEHLER: Retry-Datei konnte nicht gestaged werden (Exit $addCode)."
        exit 0
    }
    $commitCode = Invoke-Logged "git" @("commit", "-m", $msg) 180
    if ($commitCode -ne 0) {
        Write-PagesLog "FEHLER: Retry-Commit fehlgeschlagen (Exit $commitCode)."
        exit 0
    }
    $pushCode = Invoke-Logged "git" @("push") 300
    if ($pushCode -ne 0) {
        Write-PagesLog "FEHLER: Retry-Push fehlgeschlagen (Exit $pushCode)."
        exit 0
    }
    [IO.File]::WriteAllText($stateFile, [string]$attempt, [Text.UTF8Encoding]::new($false))
    Write-PagesLog "Retry-Push ausgeloest: $msg"
    exit 0
}
catch {
    Write-PagesLog "FEHLER im Pages-Watchdog: $($_.Exception.Message)"
    exit 0
}
finally {
    if ($hasLock) {
        $mutex.ReleaseMutex()
    }
    $mutex.Dispose()
}

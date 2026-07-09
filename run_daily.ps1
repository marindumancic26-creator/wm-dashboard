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
        [string[]]$Arguments,
        [int]$TimeoutSeconds = 600
    )

    $stdout = [IO.Path]::GetTempFileName()
    $stderr = [IO.Path]::GetTempFileName()
    try {
        $argumentLine = ($Arguments | ForEach-Object { ConvertTo-CommandArgument $_ }) -join " "
        $process = Start-Process -FilePath $Command -ArgumentList $argumentLine `
            -NoNewWindow -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr
        if (-not $process.WaitForExit($TimeoutSeconds * 1000)) {
            Append-CommandOutput $stdout
            Append-CommandOutput $stderr
            Write-RunLog "FEHLER: $Command Zeitlimit nach $TimeoutSeconds Sekunden; Prozessbaum wird beendet."
            Stop-ProcessTree $process.Id
            return 124
        }
        $process.WaitForExit()
        $process.Refresh()
        Append-CommandOutput $stdout
        Append-CommandOutput $stderr
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

function Append-CommandOutput {
    param([string]$Path)
    if ((Test-Path -LiteralPath $Path) -and (Get-Item -LiteralPath $Path).Length -gt 0) {
        Get-Content -LiteralPath $Path -Raw -Encoding utf8 |
            Out-File -LiteralPath $log -Append -Encoding utf8
    }
}

function Stop-ProcessTree {
    param([int]$ProcessId)
    $children = @(Get-CimInstance Win32_Process |
        Where-Object { $_.ParentProcessId -eq $ProcessId })
    foreach ($child in $children) {
        Stop-ProcessTree ([int]$child.ProcessId)
    }
    Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue
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

    $pullCode = Invoke-Logged "git" @("pull", "--rebase", "--autostash") 180
    if ($pullCode -ne 0) {
        Write-RunLog "WARNUNG: git pull fehlgeschlagen (Exit $pullCode); Pipeline laeuft mit lokalem Stand weiter."
    }

    $pipelineCode = Invoke-Logged "python" @("-m", "src.pipeline.daily_matchday_run") 1200
    if ($pipelineCode -ne 0) {
        Write-RunLog "FEHLER: Pipeline fehlgeschlagen (Exit $pipelineCode); kein Commit und kein Push."
        exit $pipelineCode
    }

    $addCode = Invoke-Logged "git" @("add", "-A") 180
    if ($addCode -ne 0) {
        Write-RunLog "FEHLER: git add fehlgeschlagen (Exit $addCode)."
        exit $addCode
    }

    $hasStagedChanges = $true
    & git diff --cached --quiet
    $diffCode = $LASTEXITCODE
    if ($diffCode -eq 0) {
        $hasStagedChanges = $false
        Write-RunLog "Kein Commit noetig: keine gestagten Aenderungen."
    }
    elseif ($diffCode -ne 1) {
        Write-RunLog "FEHLER: git diff --cached --quiet fehlgeschlagen (Exit $diffCode)."
        exit $diffCode
    }

    if ($hasStagedChanges) {
        $commitMessage = "Daily run {0}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
        $commitCode = Invoke-Logged "git" @("commit", "-m", $commitMessage) 180
        if ($commitCode -ne 0) {
            Write-RunLog "FEHLER: git commit fehlgeschlagen (Exit $commitCode); kein Push und keine Erfolgsmarke."
            exit $commitCode
        }
    }

    $pushCode = Invoke-Logged "git" @("push") 300
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

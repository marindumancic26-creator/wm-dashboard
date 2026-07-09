$ErrorActionPreference = "Stop"

$repo = $PSScriptRoot
$powershell = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
$userId = "$env:USERDOMAIN\$env:USERNAME"

function New-ProjectAction {
    param([string]$ScriptName)
    New-ScheduledTaskAction `
        -Execute $powershell `
        -Argument ('-NoProfile -NonInteractive -ExecutionPolicy Bypass -File "{0}"' -f (Join-Path $repo $ScriptName)) `
        -WorkingDirectory $repo
}

function New-ProjectSettings {
    param([TimeSpan]$ExecutionTimeLimit)
    New-ScheduledTaskSettingsSet `
        -StartWhenAvailable `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -WakeToRun `
        -MultipleInstances IgnoreNew `
        -ExecutionTimeLimit $ExecutionTimeLimit `
        -RestartCount 2 `
        -RestartInterval (New-TimeSpan -Minutes 5)
}

function Register-ProjectTask {
    param(
        [string]$TaskName,
        [string]$ScriptName,
        [Microsoft.Management.Infrastructure.CimInstance[]]$Triggers,
        [TimeSpan]$ExecutionTimeLimit,
        [string]$Description
    )
    $principal = New-ScheduledTaskPrincipal -UserId $userId -LogonType Interactive -RunLevel Limited
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action (New-ProjectAction $ScriptName) `
        -Trigger $Triggers `
        -Settings (New-ProjectSettings $ExecutionTimeLimit) `
        -Principal $principal `
        -Description $Description `
        -Force | Out-Null
}

$daily = New-ScheduledTaskTrigger -Daily -At 09:00
$mittag = New-ScheduledTaskTrigger -Daily -At 16:00
$abend = New-ScheduledTaskTrigger -Daily -At 23:00
$hermes = New-ScheduledTaskTrigger -Daily -At 10:05

$watchdog = New-ScheduledTaskTrigger -Daily -At 00:05
$watchdog.Repetition = New-CimInstance `
    -Namespace "Root/Microsoft/Windows/TaskScheduler" `
    -ClassName "MSFT_TaskRepetitionPattern" `
    -ClientOnly `
    -Property @{
        Interval = "PT10M"
        Duration = "P1D"
        StopAtDurationEnd = $false
    }

Register-ProjectTask `
    -TaskName "WM-Dashboard Daily" `
    -ScriptName "run_daily.ps1" `
    -Triggers @($daily) `
    -ExecutionTimeLimit (New-TimeSpan -Hours 3) `
    -Description "WM-Dashboard Daily: 09:00, holt verpasste Starts nach."

Register-ProjectTask `
    -TaskName "WM-Dashboard Daily Mittag" `
    -ScriptName "run_daily.ps1" `
    -Triggers @($mittag) `
    -ExecutionTimeLimit (New-TimeSpan -Hours 3) `
    -Description "WM-Dashboard Daily Mittag: 16:00, zusaetzlicher Push-Lauf."

Register-ProjectTask `
    -TaskName "WM-Dashboard Daily Abend" `
    -ScriptName "run_daily.ps1" `
    -Triggers @($abend) `
    -ExecutionTimeLimit (New-TimeSpan -Hours 3) `
    -Description "WM-Dashboard Daily Abend: 23:00, zusaetzlicher Push-Lauf."

Register-ProjectTask `
    -TaskName "WM-Dashboard Daily Watchdog" `
    -ScriptName "run_daily_watchdog.ps1" `
    -Triggers @($watchdog) `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 30) `
    -Description "WM-Dashboard Watchdog: alle 10 Minuten ganztags, auch auf Akku; holt fehlende Daily-Artefakte nach und prueft GitHub Pages."

Register-ProjectTask `
    -TaskName "WM-Dashboard Hermes" `
    -ScriptName "run_hermes.ps1" `
    -Triggers @($hermes) `
    -ExecutionTimeLimit (New-TimeSpan -Hours 3) `
    -Description "WM-Dashboard Hermes: Analyse nach Daily-Lauf."

Get-ScheduledTask | Where-Object { $_.TaskName -like "WM-Dashboard*" } |
    ForEach-Object {
        $info = $_ | Get-ScheduledTaskInfo
        [pscustomobject]@{
            TaskName = $_.TaskName
            State = $_.State
            LastRunTime = $info.LastRunTime
            LastTaskResult = $info.LastTaskResult
            NextRunTime = $info.NextRunTime
            StartWhenAvailable = $_.Settings.StartWhenAvailable
            DisallowStartIfOnBatteries = $_.Settings.DisallowStartIfOnBatteries
            StopIfGoingOnBatteries = $_.Settings.StopIfGoingOnBatteries
        }
    } | Format-Table -AutoSize

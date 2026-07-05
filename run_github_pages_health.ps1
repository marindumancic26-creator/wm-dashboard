$ErrorActionPreference = "Stop"

$repo = $PSScriptRoot
$log = Join-Path $repo "data\snapshots\automation_github_pages_health.log"
$output = Join-Path $repo "data\snapshots\github_pages_health_last.json"

function Write-HealthLog {
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

try {
    Set-Location -LiteralPath $repo
    $json = & python -m src.pipeline.github_pages_health --output $output
    $code = $LASTEXITCODE
    if ($code -ne 0) {
        Write-HealthLog "FEHLER: GitHub-Pages-Health-Check fehlgeschlagen (Exit $code)."
        exit 0
    }
    $result = $json | ConvertFrom-Json
    Write-HealthLog ("GitHub-Pages-Health {0}: {1}" -f $result.status, $result.note)
    if ($result.status -eq "error") {
        Write-HealthLog "WARNUNG: GitHub-Stand ist nicht konsistent; Details in data\snapshots\github_pages_health_last.json."
    }
    exit 0
}
catch {
    Write-HealthLog "FEHLER im GitHub-Pages-Health-Runner: $($_.Exception.Message)"
    exit 0
}

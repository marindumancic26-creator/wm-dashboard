param([switch]$UseExistingOutput)

$ErrorActionPreference = "Stop"

$repo = $PSScriptRoot
$log = Join-Path $repo "data\snapshots\automation_hermes.log"
$codex = "C:\Users\marin\AppData\Roaming\npm\codex.cmd"
$output = Join-Path $repo "data\snapshots\hermes_last.json"
$schema = Join-Path $repo "automation\hermes_output_schema.json"
$mutex = [Threading.Mutex]::new($false, "Local\WM-Dashboard-Hermes")
$hasLock = $false
$prompt = @"
Lies HERMES.md in diesem Projekt und fuehre die taegliche Hermes-Analyse aus (Schritte 2 bis 5).
Lies den heutigen Snapshot data/processed/dashboard_data.json und die heutigen Dateien in memory/daily_runs/.
Du arbeitest absichtlich read-only: Versuche keine Dateien zu schreiben und erwaehne die Sandbox nicht.
Gib ausschliesslich das verlangte JSON aus. narrative enthaelt eine konkrete deutschsprachige Analyse
in 4 bis 7 Absaetzen, ohne Ueberschrift, Codeblock, Dateipfad oder Meta-Kommentar. learning enthaelt
genau vier deutschsprachige Markdown-Bullets mit den Praefixen [Beobachtung], [Beobachtung], [Hypothese]
und [Aktion], ohne Datums-Ueberschrift. Nenne konkrete Metriken und Stichprobenumfaenge. Halte dich
strikt an HERMES.md und empfehle keine automatische Uebernahme von Modell-, Gewichts- oder
Staking-Parametern.
"@

function Write-HermesLog {
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

function Set-MarkdownSection {
    param(
        [string]$Path,
        [string]$Heading,
        [string]$Body
    )

    $content = [IO.File]::ReadAllText($Path, [Text.Encoding]::UTF8)
    $section = "$Heading`r`n`r`n$($Body.Trim())`r`n"
    # Beide automatisch gepflegten Abschnitte stehen jeweils am Dateiende.
    $pattern = "(?ms)^$([Regex]::Escape($Heading))\r?\n.*\z"
    if ([Regex]::IsMatch($content, $pattern)) {
        $regex = [Regex]::new($pattern)
        $content = $regex.Replace($content, { param($match) $section }, 1)
    }
    else {
        $content = "$($content.TrimEnd())`r`n`r`n$section"
    }
    [IO.File]::WriteAllText($Path, $content, [Text.UTF8Encoding]::new($false))
}

try {
    try {
        $hasLock = $mutex.WaitOne(0)
    }
    catch [Threading.AbandonedMutexException] {
        $hasLock = $true
    }
    if (-not $hasLock) {
        Write-HermesLog "Hermes-Lauf uebersprungen: Ein anderer Hermes-Lauf ist noch aktiv."
        exit 0
    }

    Set-Location -LiteralPath $repo
    $env:OPENAI_API_KEY = $null
    Write-HermesLog "Automatische Hermes-Analyse gestartet."
    $today = Get-Date -Format "yyyy-MM-dd"
    $successMarker = Join-Path $repo "data\snapshots\daily_success_${today}.ok"
    $closingLoop = Join-Path $repo "memory\daily_runs\${today}_closing_loop.md"
    $learnings = Join-Path $repo "memory\learnings.md"
    $deadline = (Get-Date).AddMinutes(90)
    while ((-not (Test-Path -LiteralPath $successMarker) -or
            -not (Test-Path -LiteralPath $closingLoop) -or
            -not (Test-Path -LiteralPath $learnings)) -and
           (Get-Date) -lt $deadline) {
        Write-HermesLog "Daily-Artefakte fuer $today fehlen noch; Hermes wartet."
        Start-Sleep -Seconds 60
    }
    if (-not (Test-Path -LiteralPath $successMarker) -or
        -not (Test-Path -LiteralPath $closingLoop) -or
        -not (Test-Path -LiteralPath $learnings)) {
        Write-HermesLog "FEHLER: Heutiger Daily-Success-Marker, Closing-Loop oder learnings.md fehlt nach Wartezeit."
        exit 1
    }

    if (-not $UseExistingOutput) {
        Remove-Item -LiteralPath $output -Force -ErrorAction SilentlyContinue
        $codexCode = Invoke-Logged $codex @(
            "exec", "--ignore-user-config", "-C", ".", "-s", "read-only",
            "-c", 'approval_policy="never"', "--skip-git-repo-check",
            "--ephemeral", "--color", "never",
            "--output-schema", $schema, "-o", $output, $prompt
        )
        if ($codexCode -ne 0) {
            Write-HermesLog "FEHLER: Hermes-Analyse fehlgeschlagen (Exit $codexCode); kein Commit und kein Push."
            exit $codexCode
        }
    }

    if (-not (Test-Path -LiteralPath $closingLoop) -or -not (Test-Path -LiteralPath $learnings)) {
        Write-HermesLog "FEHLER: Heutiger Closing-Loop oder learnings.md fehlt."
        exit 1
    }

    try {
        $analysis = Get-Content -LiteralPath $output -Raw -Encoding utf8 | ConvertFrom-Json
    }
    catch {
        Write-HermesLog "FEHLER: Hermes-Ausgabe ist kein gueltiges JSON."
        exit 1
    }
    if ([string]::IsNullOrWhiteSpace($analysis.narrative) -or
        [string]::IsNullOrWhiteSpace($analysis.learning)) {
        Write-HermesLog "FEHLER: Hermes-Ausgabe enthaelt nicht beide Pflichtfelder."
        exit 1
    }
    $analysis.narrative = [Regex]::Replace(
        $analysis.narrative,
        '(?i)\s*[^.!?]*(?:read-only|sandbox|einzutragen|schreiben konnte)[^.!?]*[.!?]',
        ''
    ).Trim()
    $forbiddenNarrative = '(?i)read-only|sandbox|einzutragen|schreiben konnte|```|^## '
    $learningLines = @($analysis.learning -split "\r?\n" | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
    if ($analysis.narrative.Length -lt 500 -or $analysis.narrative -match $forbiddenNarrative -or
        $learningLines.Count -ne 4 -or $learningLines[0] -notmatch '^- \[Beobachtung\]' -or
        $learningLines[1] -notmatch '^- \[Beobachtung\]' -or
        $learningLines[2] -notmatch '^- \[Hypothese\]' -or
        $learningLines[3] -notmatch '^- \[Aktion\]') {
        Write-HermesLog "FEHLER: Hermes-Ausgabe erfuellt die inhaltlichen Format-Gates nicht."
        exit 1
    }

    Set-MarkdownSection $closingLoop "## Hermes-Analyse" $analysis.narrative
    Set-MarkdownSection $learnings "## $today" $analysis.learning

    $hasNarrative = (Test-Path -LiteralPath $closingLoop) -and
        [bool](Select-String -LiteralPath $closingLoop -SimpleMatch "## Hermes-Analyse" -Quiet)
    $hasLearning = (Test-Path -LiteralPath $learnings) -and
        [bool](Select-String -LiteralPath $learnings -SimpleMatch "## $today" -Quiet)
    if (-not ($hasNarrative -and $hasLearning)) {
        Write-HermesLog "FEHLER: Hermes meldete Erfolg, hat die heutigen Zieldateien aber nicht vollstaendig geschrieben."
        exit 1
    }

    $addCode = Invoke-Logged "git" @("add", "memory\daily_runs\${today}_closing_loop.md", "memory\learnings.md")
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
finally {
    if ($hasLock) {
        $mutex.ReleaseMutex()
    }
    $mutex.Dispose()
}

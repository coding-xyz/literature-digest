param(
    [string]$Date = (Get-Date -Format "yyyy-MM-dd"),
    [switch]$SkipCollect,
    [switch]$Publish
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"
$Root = Split-Path -Parent $PSScriptRoot
$WorkspacePython = "C:\Users\Zhou\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"

if (Test-Path -LiteralPath $WorkspacePython) {
    $Python = $WorkspacePython
} else {
    $Python = "python"
}

Push-Location $Root
try {
    if (-not $SkipCollect) {
        Write-Host "[1/4] collect $Date"
        & $Python "scripts\collect.py" --date $Date
        if ($LASTEXITCODE -ne 0) { throw "collect.py failed" }
    } else {
        Write-Host "[1/4] skip collect (using existing data\$Date)"
    }

    $Report = Join-Path $Root "data\$Date\report.json"
    $Reviews = Join-Path $Root "data\$Date\reviews"
    if (-not (Test-Path -LiteralPath $Report)) {
        throw "AI curation is not ready: $Report is missing"
    }
    if (-not (Test-Path -LiteralPath $Reviews)) {
        throw "AI reviews are not ready: $Reviews is missing"
    }

    Write-Host "[2/4] merge reviews"
    & $Python "scripts\merge_reviews.py" --date $Date
    if ($LASTEXITCODE -ne 0) { throw "merge_reviews.py failed" }

    Write-Host "[3/4] build report"
    & $Python "scripts\build_report.py" --date $Date
    if ($LASTEXITCODE -ne 0) { throw "build_report.py failed" }

    if ($Publish) {
        Write-Host "[4/4] publish to GitHub"
        & (Join-Path $PSScriptRoot "publish.ps1") -Date $Date
        if ($LASTEXITCODE -ne 0) { throw "publish.ps1 failed" }
    } else {
        Write-Host "[4/4] publish skipped (use -Publish to push)"
    }

    Write-Host "Done: reports\$Date.html"
} finally {
    Pop-Location
}

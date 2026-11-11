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
        Write-Host "[1/5] collect $Date"
        & $Python "scripts\collect.py" --date $Date
        if ($LASTEXITCODE -ne 0) { throw "collect.py failed" }
    } else {
        Write-Host "[1/5] skip collect (using existing data\$Date)"
    }

    Write-Host "[2/5] dynamic selection budget"
    & $Python "scripts\selection_budget.py" --date $Date
    if ($LASTEXITCODE -ne 0) { throw "selection_budget.py failed" }

    $Report = Join-Path $Root "data\$Date\report.json"
    $Reviews = Join-Path $Root "data\$Date\reviews"
    if (-not (Test-Path -LiteralPath $Report)) {
        throw "AI curation is not ready: $Report is missing"
    }
    if (-not (Test-Path -LiteralPath $Reviews)) {
        throw "AI reviews are not ready: $Reviews is missing"
    }

    Write-Host "[3/5] merge reviews"
    & $Python "scripts\merge_reviews.py" --date $Date
    if ($LASTEXITCODE -ne 0) { throw "merge_reviews.py failed" }

    Write-Host "[4/5] build report"
    & $Python "scripts\build_report.py" --date $Date
    if ($LASTEXITCODE -ne 0) { throw "build_report.py failed" }

    if ($Publish) {
        Write-Host "[5/5] publish to GitHub"
        & (Join-Path $PSScriptRoot "publish.ps1") -Date $Date
        if ($LASTEXITCODE -ne 0) { throw "publish.ps1 failed" }
    } else {
        Write-Host "[5/5] publish skipped (use -Publish to push)"
    }

    Write-Host "Done: reports\$Date.html"
} finally {
    Pop-Location
}

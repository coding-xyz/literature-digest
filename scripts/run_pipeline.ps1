param(
    [string]$Date = (Get-Date -Format "yyyy-MM-dd")
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
    Write-Host "[1/3] collect $Date"
    & $Python "scripts\collect.py" --date $Date
    if ($LASTEXITCODE -ne 0) { throw "collect.py failed" }

    $Report = Join-Path $Root "data\$Date\report.json"
    $Reviews = Join-Path $Root "data\$Date\reviews"
    if (-not (Test-Path -LiteralPath $Report)) {
        throw "AI curation is not ready: $Report is missing"
    }
    if (-not (Test-Path -LiteralPath $Reviews)) {
        throw "AI reviews are not ready: $Reviews is missing"
    }

    Write-Host "[2/3] merge reviews"
    & $Python "scripts\merge_reviews.py" --date $Date
    if ($LASTEXITCODE -ne 0) { throw "merge_reviews.py failed" }

    Write-Host "[3/3] build report"
    & $Python "scripts\build_report.py" --date $Date
    if ($LASTEXITCODE -ne 0) { throw "build_report.py failed" }

    Write-Host "Done: reports\$Date.html"
} finally {
    Pop-Location
}

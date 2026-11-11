param(
    [string]$Date = (Get-Date -Format "yyyy-MM-dd"),
    [string]$Branch = "main",
    [string]$Remote = "origin"
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"
$env:GIT_TERMINAL_PROMPT = "0"

$Root = Split-Path -Parent $PSScriptRoot
Push-Location $Root
try {
    if (-not (Test-Path -LiteralPath (Join-Path $Root ".git"))) {
        throw "not a git repository: $Root"
    }

    $Index = Join-Path $Root "index.html"
    $Report = Join-Path $Root "reports\$Date.html"
    if (-not (Test-Path -LiteralPath $Index)) { throw "missing $Index" }
    if (-not (Test-Path -LiteralPath $Report)) { throw "missing $Report" }

    # Only publish generated site artifacts; data/ stays local and ignored.
    git add -- index.html reports
    $Pending = git status --porcelain -- index.html reports
    if (-not [string]::IsNullOrWhiteSpace($Pending)) {
        $Name = (git config user.name)
    $Email = (git config user.email)
    if ([string]::IsNullOrWhiteSpace($Name)) { git config user.name "coding-xyz" }
        if ([string]::IsNullOrWhiteSpace($Email)) { git config user.email "yijia_zhou@outlook.com" }

        git commit -m "publish $Date report"
        if ($LASTEXITCODE -ne 0) { throw "git commit failed" }
    } else {
        Write-Host "No report changes to commit; checking for unpushed commits."
    }

    $Token = $env:GH_TOKEN
    if ([string]::IsNullOrWhiteSpace($Token)) { $Token = $env:GITHUB_TOKEN }

    if (-not [string]::IsNullOrWhiteSpace($Token)) {
        $pair = "x-access-token:$Token"
        $b64 = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes($pair))
        git -c "http.extraHeader=AUTHORIZATION: basic $b64" push $Remote $Branch
    } else {
        # Uses Git Credential Manager / existing HTTPS credentials.
        git push $Remote $Branch
    }
    if ($LASTEXITCODE -ne 0) { throw "git push failed" }

    Write-Host "Published $Date to $Remote/$Branch"
} finally {
    Pop-Location
}

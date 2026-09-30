param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Url
)

$Script = Join-Path $PSScriptRoot "ytd.py"

if (-not (Test-Path $Script)) {
    Write-Host "ERROR: ytd.py was not found." -ForegroundColor Red
    exit 1
}

$Python = Get-Command python -ErrorAction SilentlyContinue
if (-not $Python) {
    $Python = Get-Command py -ErrorAction SilentlyContinue
}

if (-not $Python) {
    Write-Host "ERROR: Python 3.11 or newer is required." -ForegroundColor Red
    Write-Host "Run setup.ps1 after installing Python from python.org." -ForegroundColor Yellow
    exit 1
}

if ($Python.Name -eq "py.exe") {
    & $Python.Source -3 $Script $Url
} else {
    & $Python.Source $Script $Url
}

exit $LASTEXITCODE

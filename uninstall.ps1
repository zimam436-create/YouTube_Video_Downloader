$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$bin = Join-Path $env:USERPROFILE "bin"
$shim = Join-Path $bin "ytd.cmd"

if (Test-Path $shim) { Remove-Item $shim -Force }

$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
$parts = @($userPath -split ';' | Where-Object { $_ -and $_.Trim() -ne '' -and $_ -ne $bin })
[Environment]::SetEnvironmentVariable("Path", ($parts -join ';'), "User")

Write-Host "YTD command launcher removed." -ForegroundColor Green
Write-Host "The GitHub repository itself and your downloaded videos were not deleted."

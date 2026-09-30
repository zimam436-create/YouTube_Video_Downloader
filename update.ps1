$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$yt = Join-Path $Root "yt-dlp.exe"

if (-not (Test-Path $yt)) {
    Write-Host "yt-dlp.exe is missing from the repository." -ForegroundColor Red
    exit 1
}

Write-Host "Updating bundled yt-dlp..." -ForegroundColor Cyan
& $yt -U
Write-Host ""
Write-Host "Note: FFmpeg and Deno are intentionally kept at the versions bundled with this release." -ForegroundColor Yellow

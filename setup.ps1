$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host ""
Write-Host "YTD - YouTube Downloader" -ForegroundColor Cyan
Write-Host "Checking bundled installation..." -ForegroundColor Cyan
Write-Host ""

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command py -ErrorAction SilentlyContinue }
if (-not $python) {
    Write-Host "Python 3.11+ was not found." -ForegroundColor Red
    Write-Host "Install Python from https://www.python.org/downloads/ and run setup.ps1 again."
    exit 1
}

$required = @(
    "yt-dlp.exe",
    "ffmpeg.exe",
    "ffprobe.exe",
    "deno.exe",
    "avcodec-63.dll",
    "avdevice-63.dll",
    "avfilter-12.dll",
    "avformat-63.dll",
    "avutil-61.dll",
    "swresample-7.dll",
    "swscale-10.dll"
)

$missing = @($required | Where-Object { -not (Test-Path (Join-Path $Root $_)) })
if ($missing.Count -gt 0) {
    Write-Host "The bundled YTD toolset is incomplete:" -ForegroundColor Red
    $missing | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
    Write-Host ""
    Write-Host "If you are the maintainer, run prepare-github.ps1 against your tested D:\ytdlp-tools folder." -ForegroundColor Yellow
    exit 1
}

$bin = Join-Path $env:USERPROFILE "bin"
New-Item -ItemType Directory -Force -Path $bin | Out-Null

$shim = Join-Path $bin "ytd.cmd"
$shimText = "@echo off`r`npowershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$Root\ytd.ps1`" %*`r`nexit /b %ERRORLEVEL%`r`n"
Set-Content -Path $shim -Value $shimText -Encoding ASCII

$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
$parts = @($userPath -split ';' | Where-Object { $_ -and $_.Trim() -ne '' })
if ($parts -notcontains $bin) {
    [Environment]::SetEnvironmentVariable("Path", (($parts + $bin) -join ';'), "User")
}

Write-Host "Bundled tools verified successfully." -ForegroundColor Green
Write-Host "YTD launcher installed at: $shim" -ForegroundColor Green
Write-Host "Close and reopen PowerShell, then run: ytd \"https://www.youtube.com/watch?v=...\""

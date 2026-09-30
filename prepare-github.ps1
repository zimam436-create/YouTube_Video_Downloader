[CmdletBinding()]
param(
    [string]$Source = "D:\ytdlp-tools"
)

$ErrorActionPreference = "Stop"
$Repo = Split-Path -Parent $MyInvocation.MyCommand.Path

if (-not (Test-Path $Source)) {
    throw "Source folder not found: $Source"
}

Write-Host "Preparing YTD GitHub repository..." -ForegroundColor Cyan
Write-Host "Source: $Source"
Write-Host "Target: $Repo"
Write-Host ""

# Copy the complete tested tool bundle, including every DLL/executable.
# Project documentation and source files are preserved from this repository.
$items = @(
    "avcodec-63.dll",
    "avdevice-63.dll",
    "avfilter-12.dll",
    "avformat-63.dll",
    "avutil-61.dll",
    "deno.exe",
    "ffmpeg.exe",
    "ffplay.exe",
    "ffprobe.exe",
    "swresample-7.dll",
    "swscale-10.dll",
    "yt-dlp.exe",
    "yt-dlp.exe.old"
)

foreach ($name in $items) {
    $src = Join-Path $Source $name
    if (-not (Test-Path $src)) {
        throw "Required bundled file is missing: $name"
    }
    Copy-Item $src (Join-Path $Repo $name) -Force
    Write-Host "Copied $name" -ForegroundColor Green
}

Write-Host ""
Write-Host "Verifying bundled tools..." -ForegroundColor Cyan
& (Join-Path $Repo "yt-dlp.exe") --version
& (Join-Path $Repo "ffmpeg.exe") -version | Select-Object -First 1
& (Join-Path $Repo "deno.exe") --version | Select-Object -First 1

Write-Host ""
Write-Host "Repository bundle is ready." -ForegroundColor Green
Write-Host "Run: .\ytd.cmd \"https://www.youtube.com/watch?v=...\""

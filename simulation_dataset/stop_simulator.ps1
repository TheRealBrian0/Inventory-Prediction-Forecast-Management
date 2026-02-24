$ErrorActionPreference = "Stop"
$simDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pidFile = Join-Path $simDir "simulator.pid"

if (-not (Test-Path $pidFile)) {
    Write-Host "No PID file found. Simulator may already be stopped."
    exit 0
}

$pid = Get-Content $pidFile -ErrorAction SilentlyContinue
if (-not $pid) {
    Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
    Write-Host "PID file was empty; cleaned up."
    exit 0
}

$proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
if ($proc) {
    Stop-Process -Id $pid -Force
    Write-Host "Simulator stopped. PID: $pid"
} else {
    Write-Host "Process $pid not running. Cleaning stale PID file."
}

Remove-Item $pidFile -Force -ErrorAction SilentlyContinue

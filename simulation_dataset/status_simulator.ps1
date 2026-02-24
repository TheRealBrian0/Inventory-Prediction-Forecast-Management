$simDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pidFile = Join-Path $simDir "simulator.pid"
$logFile = Join-Path $simDir "simulator.log"

if (-not (Test-Path $pidFile)) {
    Write-Host "Simulator status: STOPPED (no PID file)"
    exit 0
}

$pid = Get-Content $pidFile -ErrorAction SilentlyContinue
if (-not $pid) {
    Write-Host "Simulator status: STOPPED (empty PID file)"
    exit 0
}

$proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
if ($proc) {
    Write-Host "Simulator status: RUNNING (PID $pid)"
    if (Test-Path $logFile) {
        Write-Host "Recent logs:"
        Get-Content $logFile -Tail 8
    }
} else {
    Write-Host "Simulator status: STOPPED (stale PID $pid)"
}

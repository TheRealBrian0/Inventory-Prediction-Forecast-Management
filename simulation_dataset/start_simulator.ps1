param(
    [int]$IntervalSeconds = 180
)

$ErrorActionPreference = "Stop"
$simDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $simDir
$pythonExe = Join-Path $rootDir ".syscodb_env\Scripts\python.exe"
$scriptPath = Join-Path $simDir "simulator.py"
$pidFile = Join-Path $simDir "simulator.pid"

if (-not (Test-Path $pythonExe)) {
    throw "Python not found in venv: $pythonExe"
}

if (Test-Path $pidFile) {
    $existingPid = Get-Content $pidFile -ErrorAction SilentlyContinue
    if ($existingPid) {
        $existingProc = Get-Process -Id $existingPid -ErrorAction SilentlyContinue
        if ($existingProc) {
            Write-Host "Simulator already running with PID $existingPid"
            exit 0
        }
    }
    Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
}

$args = "`"$scriptPath`" --loop --interval-seconds $IntervalSeconds"
$proc = Start-Process -FilePath $pythonExe -ArgumentList $args -WorkingDirectory $rootDir -PassThru
$proc.Id | Set-Content $pidFile

Write-Host "Simulator started. PID: $($proc.Id)"
Write-Host "PID file: $pidFile"
Write-Host "Logs: $(Join-Path $simDir 'simulator.log')"

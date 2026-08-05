$port = 8002
$connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
if ($connections) {
    foreach ($conn in $connections) {
        try {
            Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
        } catch {
            Write-Host "Failed to stop process $($conn.OwningProcess): $_"
        }
    }
    Start-Sleep -Seconds 2
}
$pythonPath = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-Not (Test-Path $pythonPath)) {
    throw "Python executable not found at $pythonPath"
}
Start-Process -FilePath $pythonPath -ArgumentList '-m','uvicorn','main:app','--host','127.0.0.1','--port','8002' -WorkingDirectory $PSScriptRoot -NoNewWindow
Write-Host "Backend restart initiated."
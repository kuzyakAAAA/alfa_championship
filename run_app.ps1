param(
    [int]$Port = 8501
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $python)) {
    throw "Не найдено виртуальное окружение: $python"
}

$listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
    Select-Object -First 1
if ($listener) {
    $runningProcess = Get-CimInstance Win32_Process -Filter "ProcessId=$($listener.OwningProcess)"
    if ($runningProcess.CommandLine -notmatch "streamlit") {
        throw "Порт $Port занят не процессом Streamlit. Освободите порт или укажите другой: .\run_app.ps1 -Port 8502"
    }
    Stop-Process -Id $listener.OwningProcess -Force
    Start-Sleep -Seconds 1
}

& $python -m streamlit cache clear

$url = "http://localhost:$Port/?fresh=$([DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds())"
Start-Process $url
& $python -m streamlit run (Join-Path $projectRoot "app.py") --server.port=$Port --server.headless=true --server.runOnSave=true

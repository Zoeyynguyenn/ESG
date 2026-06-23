# Dung process dang listen port 8787 (LangGraph API)
param([int]$Port = 8787)

$lines = netstat -ano | Select-String "LISTENING" | Select-String ":$Port\s"
if (-not $lines) {
    Write-Host "Khong co process nao listen port $Port"
    exit 0
}

$pids = $lines | ForEach-Object {
    ($_ -split '\s+')[-1]
} | Select-Object -Unique

foreach ($procId in $pids) {
    if ($procId -match '^\d+$') {
        Write-Host "Dang dung PID $procId (port $Port)..."
        Stop-Process -Id ([int]$procId) -Force -ErrorAction SilentlyContinue
    }
}
Write-Host "Xong. Co the chay lai: python scripts/run_langgraph_evidence_api.py --host 0.0.0.0 --port $Port"

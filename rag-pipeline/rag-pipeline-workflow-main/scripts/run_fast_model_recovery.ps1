# Sau mat dien / 12h timeout: ~2-3h, khong lap full 9 case.
# 1) Prebuild BGE index 1 lan
# 2) Chi rerun case fail + 1 case BGE hybrid
# 3) RAGAS top-3 (neu co .env)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path))

function Import-DotEnvFile {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return }
    Get-Content $Path | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
            [Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), "Process")
        }
    }
}
if (Test-Path ".env") { Import-DotEnvFile ".env" }

Write-Host "=== [1/3] Prebuild BGE-M3 index (1 lan) ===" -ForegroundColor Cyan
python -u src/prebuild_benchmark_index.py --lane company_public_dev --embedding-model "BAAI/bge-m3"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "=== [2/3] Fast eval: minilm_hybrid + bge_hybrid + e5_dense ===" -ForegroundColor Cyan
python -u src/run_model_candidate_benchmark.py `
    --config configs/benchmark_model_candidates_company_public_fast.yaml `
    --lane company_public_dev `
    --resume `
    --reuse-index true `
    --enable-ragas false

if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$key = [Environment]::GetEnvironmentVariable("OPENAI_API_KEY", "Process")
if (-not [string]::IsNullOrWhiteSpace($key)) {
    Write-Host "=== [3/3] RAGAS top-3 (ragas-only, ~30 phut) ===" -ForegroundColor Cyan
    python -u src/run_model_candidate_benchmark.py `
        --config configs/benchmark_model_candidates_company_public_v1.yaml `
        --ragas-only --enable-ragas true --ragas-top-n 3 --ragas-max-questions 10
}
Write-Host "Done. Xem reports/model_candidate_benchmark_summary.md" -ForegroundColor Green

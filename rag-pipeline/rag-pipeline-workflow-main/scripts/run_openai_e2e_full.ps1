param(
  [int]$RagasMaxQuestions = 10,
  [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
$env:RAGAS_ENABLED = "true"
$env:RAG_BENCHMARK_LLM_PROVIDER = "openai_api"
$env:RAG_OPENAI_EMBED_BATCH = "32"

if (-not $SkipInstall) {
  Write-Host "Installing RAGAS dependencies..."
  python -m pip install -r requirements-ragas.txt -q
}

Write-Host "Preflight OpenAI API (.env + key validity)..."
python scripts/openai_e2e_preflight.py
if ($LASTEXITCODE -ne 0) {
  throw "OpenAI preflight failed - fix OPENAI_API_KEY in .env (do not commit) then rerun."
}

Write-Host "Running full-lane E2E (extractive vs generative + RAGAS max $RagasMaxQuestions)..."
python src/run_model_candidate_benchmark.py `
  --config configs/benchmark_exportjson_openai_e2e.yaml `
  --enable-ragas true `
  --ragas-max-questions $RagasMaxQuestions `
  --timeout-sec 3600

Write-Host "Done. See reports/benchmark_exportjson_openai_e2e_*.csv"

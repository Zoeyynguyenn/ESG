param(
  [switch]$SmokeOnly,
  [switch]$SkipSmoke,
  [switch]$Fresh,
  [int]$TimeoutSec = 1800
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
$env:RAG_EMBED_LOCAL_ONLY = "true"
$env:HF_HUB_OFFLINE = "1"
$env:TRANSFORMERS_OFFLINE = "1"
$env:RAG_PDF_PARSER = "pypdf"
$env:RAGAS_ENABLED = "false"

$LogDir = Join-Path $Root "reports"
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$LogPath = Join-Path $LogDir "exportjson_overnight_3phase_$Stamp.log"

if ($Fresh) {
  $ArchiveDir = Join-Path $LogDir "archive_exportjson_$Stamp"
  New-Item -ItemType Directory -Path $ArchiveDir -Force | Out-Null
  $Patterns = @(
    "benchmark_model_candidates_exportjson_smoke_*",
    "benchmark_exportjson_phase1_*",
    "benchmark_exportjson_phase2_*",
    "benchmark_exportjson_phase3_*"
  )
  foreach ($Pattern in $Patterns) {
    Get-ChildItem $LogDir -Filter $Pattern -ErrorAction SilentlyContinue | ForEach-Object {
      Move-Item -LiteralPath $_.FullName -Destination (Join-Path $ArchiveDir $_.Name) -Force
    }
  }
  "Fresh run requested. Previous exportjson benchmark artifacts archived to $ArchiveDir" | Tee-Object -FilePath $LogPath -Append
}

function Run-Step {
  param(
    [string]$Name,
    [scriptblock]$Command
  )
  "===== $Name :: $(Get-Date -Format o) =====" | Tee-Object -FilePath $LogPath -Append
  & $Command 2>&1 | Tee-Object -FilePath $LogPath -Append
  if ($LASTEXITCODE -ne 0) {
    throw "Step failed: $Name (exit=$LASTEXITCODE)"
  }
}

Run-Step "preflight-py-compile" {
  python -m py_compile `
    src/rag_common.py `
    src/run_benchmark_case.py `
    src/run_model_candidate_benchmark.py `
    src/prepare_exportjson_phase_configs.py
}

Run-Step "preflight-local-models" {
  python -c "from sentence_transformers import SentenceTransformer, CrossEncoder
models=['sentence-transformers/all-MiniLM-L6-v2','BAAI/bge-m3','intfloat/multilingual-e5-base']
for m in models:
    try:
        SentenceTransformer(m, local_files_only=True)
        print(m + '\tLOCAL_OK')
    except Exception as e:
        print(m + '\tLOCAL_MISSING\t' + str(e)[:160])
for m in ['cross-encoder/ms-marco-MiniLM-L-6-v2']:
    try:
        CrossEncoder(m, local_files_only=True)
        print(m + '\tLOCAL_OK')
    except Exception as e:
        print(m + '\tLOCAL_MISSING\t' + str(e)[:160])"
}

if (-not $SkipSmoke) {
  Run-Step "smoke-minilm-dev" {
    python src/run_model_candidate_benchmark.py `
      --config configs/benchmark_model_candidates_exportjson_smoke.yaml `
      --reuse-index true `
      --resume `
      --prefetch-mode local `
      --timeout-sec 900
  }
}

if ($SmokeOnly) {
  "SmokeOnly requested. Stop before Phase 1." | Tee-Object -FilePath $LogPath -Append
  exit 0
}

Run-Step "phase1-chunking-embedding-retrieval" {
  python src/run_model_candidate_benchmark.py `
    --config configs/benchmark_model_candidates_exportjson_phase1.yaml `
    --reuse-index true `
    --resume `
    --prefetch-mode local `
    --timeout-sec $TimeoutSec
}

Run-Step "prepare-phase2-config" {
  python src/prepare_exportjson_phase_configs.py `
    --phase phase2 `
    --input-csv reports/benchmark_exportjson_phase1_results.csv `
    --output-config configs/benchmark_model_candidates_exportjson_phase2.yaml `
    --top-n 3
}

Run-Step "phase2-reranker" {
  python src/run_model_candidate_benchmark.py `
    --config configs/benchmark_model_candidates_exportjson_phase2.yaml `
    --reuse-index true `
    --resume `
    --prefetch-mode local `
    --timeout-sec $TimeoutSec
}

Run-Step "prepare-phase3-config" {
  python src/prepare_exportjson_phase_configs.py `
    --phase phase3 `
    --input-csv reports/benchmark_exportjson_phase2_results.csv `
    --output-config configs/benchmark_model_candidates_exportjson_phase3.yaml `
    --top-n 3
}

Run-Step "phase3-vector-db" {
  python src/run_model_candidate_benchmark.py `
    --config configs/benchmark_model_candidates_exportjson_phase3.yaml `
    --reuse-index true `
    --resume `
    --prefetch-mode local `
    --timeout-sec $TimeoutSec
}

"DONE :: $(Get-Date -Format o)" | Tee-Object -FilePath $LogPath -Append
"Outputs:" | Tee-Object -FilePath $LogPath -Append
"- reports/benchmark_exportjson_phase1_results.csv" | Tee-Object -FilePath $LogPath -Append
"- reports/benchmark_exportjson_phase2_results.csv" | Tee-Object -FilePath $LogPath -Append
"- reports/benchmark_exportjson_phase3_results.csv" | Tee-Object -FilePath $LogPath -Append
"- $LogPath" | Tee-Object -FilePath $LogPath -Append

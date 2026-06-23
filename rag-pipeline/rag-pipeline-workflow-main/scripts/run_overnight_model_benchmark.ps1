# Chay MOT LAN — khong can agent goi nhieu lenh terminal.
# PowerShell (tu thu muc repo):
#   .\scripts\run_overnight_model_benchmark.ps1
# Hoac:
#   .\scripts\run_overnight_model_benchmark.ps1 -EnableRagas

param(
    [string]$Lane = "company_public_dev",
    [int]$TimeoutSec = 0,
    [switch]$EnableRagas,
    [int]$RagasTopN = 3,
    [int]$RagasMaxQuestions = 10,
    [switch]$PrefetchOnly
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $RepoRoot

function Import-DotEnvFile {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return }
    Get-Content $Path | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            if (-not [string]::IsNullOrEmpty($name)) {
                [Environment]::SetEnvironmentVariable($name, $value, "Process")
            }
        }
    }
}

# Uu tien .env (local, khong commit). Fallback .env.example neu ban dat key tam o day.
if (Test-Path ".env") {
    Import-DotEnvFile ".env"
} elseif (Test-Path ".env.example") {
    Write-Host "Note: dang doc .env.example — nen copy thanh .env va xoa key khoi .env.example truoc khi commit." -ForegroundColor Yellow
    Import-DotEnvFile ".env.example"
}

$pyArgs = @(
    "-u", "src/run_model_candidate_benchmark.py",
    "--lane", $Lane,
    "--timeout-sec", $TimeoutSec,
    "--reuse-index", "true"
)

if ($PrefetchOnly) {
    $pyArgs += "--prefetch-only"
    python @pyArgs
    exit $LASTEXITCODE
}

$pyArgs += @("--enable-ragas", "false")
Write-Host "=== Phase 1: model candidates (RAGAS off) ===" -ForegroundColor Cyan
# Prebuild index 1 lan cho cac embedding chinh de giam timeout ingest lap lai
python -u src/prebuild_benchmark_index.py `
    --lane $Lane `
    --vector-store chroma `
    --embedding-list "sentence-transformers/all-MiniLM-L6-v2,BAAI/bge-m3,intfloat/multilingual-e5-base"

python @pyArgs
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$key = [Environment]::GetEnvironmentVariable("OPENAI_API_KEY", "Process")
$ragasEnv = [Environment]::GetEnvironmentVariable("RAGAS_ENABLED", "Process")
$doRagas = $EnableRagas -or ($ragasEnv -match '^(1|true|yes)$') -or (-not [string]::IsNullOrWhiteSpace($key))

if ($doRagas -and -not [string]::IsNullOrWhiteSpace($key)) {
    Write-Host "=== Phase 2: RAGAS top configs only (khong lap 9 case) ===" -ForegroundColor Cyan
    python -u src/run_model_candidate_benchmark.py `
        --lane $Lane `
        --ragas-only `
        --enable-ragas true `
        --ragas-top-n $RagasTopN `
        --ragas-max-questions $RagasMaxQuestions
    exit $LASTEXITCODE
}

if ($doRagas -and [string]::IsNullOrWhiteSpace($key)) {
    Write-Host "RAGAS skipped: OPENAI_API_KEY missing trong .env" -ForegroundColor Yellow
}

Write-Host "Done. See reports/model_candidate_benchmark_summary.md" -ForegroundColor Green
exit 0

# Tiep tuc sau mat dien: chi chay lai case failed/timeout, roi RAGAS top-3.
#   .\scripts\resume_model_benchmark.ps1

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
if (Test-Path ".env") { Import-DotEnvFile ".env" }

Write-Host "=== Resume failed/timeout cases ===" -ForegroundColor Cyan
python -u src/run_model_candidate_benchmark.py `
    --lane company_public_dev `
    --resume `
    --reuse-index true `
    --enable-ragas false

if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$key = [Environment]::GetEnvironmentVariable("OPENAI_API_KEY", "Process")
if (-not [string]::IsNullOrWhiteSpace($key)) {
    Write-Host "=== RAGAS top-3 (ragas-only) ===" -ForegroundColor Cyan
    python -u src/run_model_candidate_benchmark.py `
        --lane company_public_dev `
        --ragas-only `
        --enable-ragas true `
        --ragas-top-n 3 `
        --ragas-max-questions 10
    exit $LASTEXITCODE
}

Write-Host "Done (no RAGAS: missing OPENAI_API_KEY in .env)" -ForegroundColor Yellow
exit 0

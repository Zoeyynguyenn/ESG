# Doi phase 1 (script khac dang chay) xong roi chay RAGAS top-3 — khong lap 9 case.
# Chay song song khi ban da bat run_overnight_model_benchmark.ps1 (phase 1 only tu ban cu):
#   .\scripts\wait_then_ragas.ps1

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

$csv = "reports\model_candidate_results.csv"
$expected = 9
Write-Host "Waiting for phase 1 -> $csv ($expected rows)..." -ForegroundColor Cyan

while ($true) {
    if (Test-Path $csv) {
        $rows = @(Import-Csv $csv)
        if ($rows.Count -ge $expected) { break }
        Write-Host "  $($rows.Count)/$expected cases in CSV, waiting..."
    } else {
        Write-Host "  (no CSV yet)..."
    }
    Start-Sleep -Seconds 120
}

$key = [Environment]::GetEnvironmentVariable("OPENAI_API_KEY", "Process")
if ([string]::IsNullOrWhiteSpace($key)) {
    Write-Host "RAGAS skipped: no OPENAI_API_KEY in .env" -ForegroundColor Yellow
    exit 0
}

Write-Host "Phase 1 done. Starting RAGAS-only..." -ForegroundColor Green
python -u src/run_model_candidate_benchmark.py `
    --lane company_public_dev `
    --ragas-only `
    --enable-ragas true `
    --ragas-top-n 3 `
    --ragas-max-questions 10
exit $LASTEXITCODE

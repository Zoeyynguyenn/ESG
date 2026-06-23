# Zip rieng index cache de upload len pod (neu bundle thieu cache)
$OutZip = "E:\Documents\rag-pipeline-workflow\artifacts\c2_index_cache_only.zip"
$src = "E:\Documents\rag-pipeline-workflow\artifacts\benchmark_cache"
if (-not (Test-Path "$src\index_cache")) { throw "Missing $src\index_cache" }
$staging = Join-Path $env:TEMP "c2_index_cache_staging"
if (Test-Path $staging) { Remove-Item $staging -Recurse -Force }
New-Item -ItemType Directory -Path "$staging\rag-pipeline-workflow\artifacts" -Force | Out-Null
Copy-Item $src "$staging\rag-pipeline-workflow\artifacts\benchmark_cache" -Recurse -Force
if (Test-Path $OutZip) { Remove-Item $OutZip -Force }
Compress-Archive -Path "$staging\rag-pipeline-workflow" -DestinationPath $OutZip
Write-Host "Created: $OutZip ($([math]::Round((Get-Item $OutZip).Length/1MB,1)) MB)"
Write-Host "Upload vao /workspace, Tab 2:"
Write-Host "  cd /workspace && unzip -o c2_index_cache_only.zip"

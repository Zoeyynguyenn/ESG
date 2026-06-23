# Tunnel free — LangGraph truy cap qua HTTPS khong can cung LAN
# Can: cloudflared — https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
#
# Terminal 1: python scripts/run_langgraph_evidence_api.py --host 127.0.0.1 --port 8787
# Terminal 2: .\scripts\run_langgraph_tunnel.ps1

$cloudflared = Get-Command cloudflared -ErrorAction SilentlyContinue
if (-not $cloudflared) {
    Write-Host "ERROR: chua cai cloudflared. Tai ve tu Cloudflare downloads." -ForegroundColor Red
    exit 1
}

Write-Host "Dang mo tunnel toi http://127.0.0.1:8787 ..."
Write-Host "Copy URL https://....trycloudflare.com gui cho LangGraph (Swagger: /docs)"
cloudflared tunnel --url http://127.0.0.1:8787

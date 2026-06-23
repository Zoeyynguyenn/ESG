# Mo port 8787 inbound tren Windows Firewall cho LangGraph API staging
# Chay PowerShell Administrator:
#   .\scripts\open_langgraph_api_firewall.ps1

$ruleName = "RAG LangGraph Evidence API 8787"
$existing = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "Rule da ton tai: $ruleName"
} else {
    New-NetFirewallRule -DisplayName $ruleName `
        -Direction Inbound `
        -Action Allow `
        -Protocol TCP `
        -LocalPort 8787 `
        -Profile Private,Domain | Out-Null
    Write-Host "Da tao firewall rule: $ruleName (Private + Domain)"
}

$ip = (Get-NetIPAddress -AddressFamily IPv4 |
    Where-Object { $_.IPAddress -notlike '127.*' -and $_.PrefixOrigin -ne 'WellKnown' } |
    Select-Object -First 1).IPAddress
Write-Host ""
Write-Host "Kiem tra tu may khac (cung WiFi/LAN):"
Write-Host "  curl http://${ip}:8787/health"
Write-Host "  Swagger: http://${ip}:8787/docs"

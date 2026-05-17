$ErrorActionPreference = "Stop"

$baseUrl = if ($args.Count -gt 0 -and $args[0]) { $args[0].TrimEnd("/") } else { "http://127.0.0.1:3210" }
$healthUrl = "$baseUrl/api/health"

Invoke-WebRequest -Uri $healthUrl -UseBasicParsing | Out-Null

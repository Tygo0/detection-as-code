<#
  record.ps1 - record ONE technique's telemetry, cleanly.
  Run after setup.ps1 has finished. Exports trimmed .evtx to C:\out.

  Example:
    C:\lab\scripts\record.ps1 -TechniqueId T1053.005 -TestGuid 42f53695-ad4a-4546-abb6-7d837f644a71
#>
param(
    [Parameter(Mandatory)] [string]$TechniqueId,
    [Parameter(Mandatory)] [string]$TestGuid,
    [hashtable]$InputArgs,              # optional: override Atomic input args, e.g. @{process_to_execute='cmd.exe'}
    [string]$Out = 'C:\out'
)
$ErrorActionPreference = 'Stop'

Import-Module 'C:\AtomicRedTeam\invoke-atomicredteam\Invoke-AtomicRedTeam.psd1' -Force

# Splatted onto every Invoke-AtomicTest call so -InputArgs is passed only when given.
$ia = @{}
if ($InputArgs) { $ia['InputArgs'] = $InputArgs }

Write-Host "[*] $TechniqueId / $TestGuid" -ForegroundColor Cyan
Write-Host "[*] Review what will run:" -ForegroundColor Yellow
Invoke-AtomicTest $TechniqueId -TestGuids $TestGuid -ShowDetailsBrief @ia

# --- prerequisites while the network is still up ---
Write-Host "[*] Fetching prerequisites (network on)..."
Invoke-AtomicTest $TechniqueId -TestGuids $TestGuid -GetPrereqs @ia

# --- network OFF before the attack runs ---
Write-Host "[*] Disabling network..." -ForegroundColor Yellow
Get-NetAdapter | Disable-NetAdapter -Confirm:$false

# --- run, timestamped so we export only the attack window ---
$start = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ss.fffZ')
Write-Host "[*] Running test at $start ..."
Invoke-AtomicTest $TechniqueId -TestGuids $TestGuid @ia
Start-Sleep -Seconds 6

# --- export the three logs, filtered to events at/after $start ---
if (-not (Test-Path $Out)) { New-Item -ItemType Directory $Out -Force | Out-Null }
$q = "*[System[TimeCreated[@SystemTime>='$start']]]"
$base = "$Out\$TestGuid"
wevtutil epl 'Microsoft-Windows-Sysmon/Operational'     "$base.evtx"            "/q:$q" /ow:true
wevtutil epl 'Security'                                 "$base-security.evtx"   "/q:$q" /ow:true
wevtutil epl 'Microsoft-Windows-PowerShell/Operational' "$base-powershell.evtx" "/q:$q" /ow:true

# --- cleanup (harmless if it errors, e.g. missing notepad) ---
Write-Host "[*] Cleanup..."
try { Invoke-AtomicTest $TechniqueId -TestGuids $TestGuid -Cleanup @ia } catch { Write-Warning "cleanup: $_" }

# --- per-recording metadata ---
@{
    technique         = $TechniqueId
    atomic_test_guid  = $TestGuid
    recorded_utc      = $start
    exported          = @("$TestGuid.evtx", "$TestGuid-security.evtx", "$TestGuid-powershell.evtx")
} | ConvertTo-Json | Set-Content "$base-metadata.json" -Encoding UTF8

Write-Host ""
Write-Host "[+] Done. Files in C:\out (host: C:\dac-lab\out):" -ForegroundColor Green
Get-ChildItem "$base*" | Select-Object Name, Length
Write-Host "    Copy the primary .evtx into the repo under recordings/attack/$TechniqueId/"

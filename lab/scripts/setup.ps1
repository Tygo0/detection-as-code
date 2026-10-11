<#
  setup.ps1 - provisions a fresh Windows Sandbox for recording.
  Runs once via lab.wsb LogonCommand (through bootstrap.cmd). Needs networking ON.

  The Sandbox LogonCommand runs headless (no reliable visible window), so progress
  is written to the shared folder instead:
    C:\out\setup.log            <- live transcript (open it on the host to watch)
    C:\out\SETUP-COMPLETE.txt   <- appears when setup finished OK
    C:\out\SETUP-FAILED.txt     <- appears with the error if setup failed
  On the host these are in C:\dac-lab\out\.

  Pinned versions (keep in sync with repo metadata):
    Sysmon config : olafhartong/sysmon-modular, release tag 'configs-082cba578667'
    Atomic Red Team: redcanaryco @ 8af478b
#>
$ErrorActionPreference = 'Stop'
$SYSMON_CONFIG_TAG = 'configs-082cba578667'
$SYSMON_CONFIG_URL = "https://github.com/olafhartong/sysmon-modular/releases/download/$SYSMON_CONFIG_TAG/sysmonconfig.xml"
$ART_COMMIT        = '8af478b'
$OUT = 'C:\out'

if (-not (Test-Path $OUT)) { New-Item -ItemType Directory $OUT -Force | Out-Null }
Remove-Item "$OUT\SETUP-COMPLETE.txt", "$OUT\SETUP-FAILED.txt" -ErrorAction SilentlyContinue
Start-Transcript -Path "$OUT\setup.log" -Force | Out-Null

try {
    Write-Host "=== DAC Sandbox setup ===" -ForegroundColor Cyan

    # --- 1. Sysmon (binary downloaded, never committed) ---
    Write-Host "[*] Downloading Sysmon..."
    $sysmonZip = "$env:TEMP\Sysmon.zip"
    Invoke-WebRequest 'https://download.sysinternals.com/files/Sysmon.zip' -OutFile $sysmonZip -UseBasicParsing
    Expand-Archive $sysmonZip -DestinationPath "$env:TEMP\Sysmon" -Force

    Write-Host "[*] Downloading pinned sysmon-modular config (release $SYSMON_CONFIG_TAG)..."
    $cfg = "$env:TEMP\sysmonconfig.xml"
    Invoke-WebRequest $SYSMON_CONFIG_URL -OutFile $cfg -UseBasicParsing

    Write-Host "[*] Installing Sysmon..."
    & "$env:TEMP\Sysmon\Sysmon64.exe" -accepteula -i $cfg | Out-Null

    # --- 2. PowerShell Script Block Logging (off by default) ---
    Write-Host "[*] Enabling PowerShell Script Block Logging..."
    $k = 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ScriptBlockLogging'
    New-Item $k -Force | Out-Null
    Set-ItemProperty $k -Name EnableScriptBlockLogging -Value 1

    # --- 3. Audit policy (GUID, not translated name - this host is tr-TR) ---
    Write-Host "[*] Ensuring account-management auditing..."
    auditpol /set /subcategory:"{0CCE9235-69AE-11D9-BED3-505054503030}" /success:enable | Out-Null

    # --- 4. Atomic Red Team (NuGet + PSGallery pre-provisioned so nothing prompts) ---
    Write-Host "[*] Preparing package providers (NuGet, PSGallery)..."
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Install-PackageProvider -Name NuGet -MinimumVersion 2.8.5.201 -Force -Scope CurrentUser | Out-Null
    Set-PSRepository -Name PSGallery -InstallationPolicy Trusted

    Write-Host "[*] Installing Atomic Red Team ($ART_COMMIT)... (a few minutes)"
    Set-ExecutionPolicy Bypass -Scope Process -Force
    IEX (IWR 'https://raw.githubusercontent.com/redcanaryco/invoke-atomicredteam/master/install-atomicredteam.ps1' -UseBasicParsing)
    Install-AtomicRedTeam -getAtomics -Force

    # --- 5. Base metadata for this session ---
    @{
        windows_build     = [string][System.Environment]::OSVersion.Version
        system_language   = (Get-Culture).Name
        sysmon_config_tag = $SYSMON_CONFIG_TAG
        art_commit        = $ART_COMMIT
        attack_version    = 'v19'
        defender          = 'realtime+tamper disabled (Sandbox default)'
        session_utc       = (Get-Date).ToUniversalTime().ToString('o')
    } | ConvertTo-Json | Set-Content "$OUT\session-metadata.json" -Encoding UTF8

    (Get-Date).ToUniversalTime().ToString('o') | Set-Content "$OUT\SETUP-COMPLETE.txt" -Encoding UTF8

    Write-Host ""
    Write-Host "=== Ready. Now record a technique, e.g.: ===" -ForegroundColor Green
    Write-Host '  C:\lab\scripts\record.ps1 -TechniqueId T1053.005 -TestGuid 42f53695-ad4a-4546-abb6-7d837f644a71'
}
catch {
    Write-Host "SETUP FAILED: $_" -ForegroundColor Red
    ($_ | Out-String) | Set-Content "$OUT\SETUP-FAILED.txt" -Encoding UTF8
}
finally {
    Stop-Transcript | Out-Null
}

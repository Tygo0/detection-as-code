# Recording telemetry

How to reproduce the attack and benign recordings this repo tests against. All attacks are
harmless [Atomic Red Team](https://github.com/redcanaryco/atomic-red-team) simulations run
only inside a disposable **Windows Sandbox**.

## Prerequisites (host)
- Windows 11 Pro / Enterprise / Education with **Windows Sandbox** enabled
  (Windows Features -> "Windows Sandbox").
- A clone of this repo.
- An output folder on the host for exported logs: create `C:\dac-lab\out`.
- In `lab/lab.wsb`, set the first mapped `HostFolder` to the `lab/` directory of your clone.
  (The second mapping, `C:\dac-lab\out`, is the only writable path back to the host.)

## One run = one technique
Each recording is made in a fresh Sandbox so it is free of leftovers and reproducible.

1. Double-click `lab/lab.wsb`. The `LogonCommand` runs `setup.ps1` headless; watch the host
   folder `C:\dac-lab\out\` for `SETUP-COMPLETE.txt` (and `setup.log` for live progress).
   `setup.ps1` installs Sysmon (pinned sysmon-modular config), enables PowerShell script-block
   logging and account auditing, sets the execution policy, and installs Atomic Red Team.
2. When setup is complete, open PowerShell in the Sandbox and record one technique:
   ```powershell
   C:\lab\scripts\record.ps1 -TechniqueId <Txxxx> -TestGuid <guid>
   ```
   `record.ps1` fetches prerequisites (network on), disables the network, runs the test, and
   exports the Sysmon/Security/PowerShell logs (trimmed to the attack window) to `C:\out`.
3. Close the Sandbox. The exported files are in `C:\dac-lab\out\` on the host.
4. Copy the primary Sysmon `.evtx` (named `<guid>.evtx`) into
   `recordings/attack/<Txxxx>/` and commit it.

### Benign baseline
Launch the Sandbox, let setup finish, then do ordinary things (open built-in apps, browse,
run routine PowerShell) **without** running `record.ps1`. Export and copy as
`recordings/benign/workstation-baseline.evtx`. Every rule must stay silent on it.

## Techniques and test GUIDs (v1)
Reference Atomic tests by GUID (test numbers are unstable; some low numbers are non-Windows).

| Technique | Atomic test | GUID | Notes |
|---|---|---|---|
| T1059.001 | PowerShell Command Execution | `a538de64-1c74-46ed-aa60-b995ed302598` | emits `powershell.exe -e <base64>` |
| T1047 | Create a Process using obfuscated Win32_Process | `10447c83-fc38-462a-a936-5102363b1c43` | run with `-InputArgs @{process_to_execute='cmd.exe'}` |
| T1053.005 | Scheduled task Local | `42f53695-ad4a-4546-abb6-7d837f644a71` | |
| T1547.001 | Reg Key Run | `e55be3fd-3521-4610-9d1a-e210e42dcf05` | |
| T1136.001 | Create a new user in PowerShell | `bc8be0ac-475c-4fbf-9b1d-9fffd77afbde` | admin |
| T1218.011 | Rundll32 execute JavaScript (GetObject) | `57ba4ce9-ee7a-4f27-9928-3c70c489b59d` | |
| T1218.005 | Mshta used to Execute PowerShell | `8707a805-2b76-4f32-b1c0-14e558205772` | |
| T1685.005 | Clear Logs | `e6abb60e-26b8-41da-8aae-0c35174b0967` | admin |
| T1003.001 | Dump LSASS via comsvcs.dll | `2536dee2-12fb-459a-8c37-971844fa73be` | admin |
| T1105 | certutil download (urlcache) | `dd3b61dd-7bbc-48cd-ab51-49ad1a776df0` | download fails with net off; command line still logged |

Example (the WMI technique, which needs the non-default argument):
```powershell
C:\lab\scripts\record.ps1 -TechniqueId T1047 -TestGuid 10447c83-fc38-462a-a936-5102363b1c43 -InputArgs @{process_to_execute='cmd.exe'}
```

## Notes
- **Windows Sandbox has no Notepad** - tests that spawn/clean up notepad may log a harmless
  cleanup error; the recording itself is unaffected.
- Scripts use ATT&CK v19 IDs and locale-independent GUIDs/SIDs (the reference host is tr-TR).
- Each recording folder also has a `metadata.json` capturing the pinned versions used.

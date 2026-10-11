# Recordings: benign baseline

Normal activity with **no attack run**, used to measure false positives.
Every rule must stay silent here (`must_not_fire: "*"` in `tests/expectations.yml`).

Expected file: `workstation-baseline.evtx`

To record: launch `lab/lab.wsb`, let `setup.ps1` finish, then spend a few minutes doing
ordinary things (open built-in apps, browse, run routine admin PowerShell) with the
network left ON. Do **not** run `record.ps1`. Export the Sysmon log manually:

```powershell
wevtutil epl "Microsoft-Windows-Sysmon/Operational" C:\out\workstation-baseline.evtx /ow:true
```

Copy it here and commit. If any rule fires on this baseline, that is a finding: document
it or narrow the rule.

# Recordings: T1053.005

Drop the exported `.evtx` here after recording in Windows Sandbox.

Expected primary file (referenced by `tests/expectations.yml`):

```
42f53695-ad4a-4546-abb6-7d837f644a71.evtx
```

Plus (optional, same run): `-security.evtx`, `-powershell.evtx`, and `-metadata.json`.

To record:
1. Launch `lab/lab.wsb`, let `setup.ps1` finish.
2. Run: `C:\lab\scripts\record.ps1 -TechniqueId T1053.005 -TestGuid 42f53695-ad4a-4546-abb6-7d837f644a71`
3. Close the Sandbox. Files are at `C:\dac-lab\out\`.
4. Copy the primary `.evtx` here and commit it.

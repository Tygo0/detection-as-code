# Repo layout (v1)

```
detection-as-code/                  repo root
├── README.md                       what it is, how to reproduce, status
├── LICENSE                         MIT (code)
├── .gitattributes                  marks *.evtx binary (no EOL normalization)
├── .gitignore                      ignores fetched binaries, scratch, local-only docs
│
├── rules/                          THE DELIVERABLE — Sigma rules, one file per detection (flat)
│   ├── t1059_001_encoded_powershell.yml
│   ├── t1047_wmi_process_creation.yml
│   ├── t1053_005_scheduled_task_creation.yml
│   ├── t1547_001_registry_run_key.yml
│   ├── t1136_001_local_account_creation.yml
│   ├── t1218_011_rundll32_proxy_execution.yml
│   ├── t1218_005_mshta_proxy_execution.yml
│   ├── t1685_005_clear_event_logs.yml
│   ├── t1003_001_lsass_comsvcs_dump.yml
│   └── t1105_certutil_download.yml
│
├── recordings/                     captured telemetry (small, trimmed Sysmon .evtx)
│   ├── attack/
│   │   └── <Txxxx>/
│   │       ├── <guid>.evtx          Sysmon Operational log, trimmed to the attack window
│   │       └── metadata.json        pinned versions used for this recording
│   └── benign/
│       ├── workstation-baseline.evtx
│       ├── metadata.json
│       └── README.md
│
├── lab/                            everything that runs INSIDE Windows Sandbox
│   ├── lab.wsb                     Sandbox config (net/clipboard off, folder maps)
│   └── scripts/
│       ├── bootstrap.cmd           LogonCommand wrapper that launches setup.ps1
│       ├── setup.ps1               exec policy + Sysmon + logging + audit + ART install
│       └── record.ps1              one technique: prereqs → net off → run → export → cleanup
│                                   (the Sysmon config and Sysmon binary are downloaded, not committed)
│
├── chainsaw/                       replay tool config (binary fetched, not committed)
│   ├── mapping.yml                 pinned Sigma→EVTX field mapping
│   └── VERSION                     pinned Chainsaw release tag
│
├── tests/                          proves every rule works
│   ├── expectations.yml            recording → rule titles that MUST / MUST NOT fire
│   ├── run_chainsaw.py             wrapper: run Chainsaw, parse --json (not exit code)
│   ├── conftest.py                 locates binary, loads expectations
│   └── test_detections.py          pytest: assert fire-on-attack + silent-on-benign
│
├── tools/
│   ├── lint_rules.py               Sigma YAML + required-field linter
│   └── coverage.py                 reads PASSING rules' `tags:` → verified ATT&CK layer
│
├── coverage/
│   └── navigator-layer.json        generated ATT&CK Navigator layer (verified rules only)
│
├── docs/
│   ├── recording.md                how to reproduce the recordings in Windows Sandbox
│   ├── repo-layout.md              this file
│   ├── adr/
│   │   └── 0001-replay-tool.md     the Chainsaw decision log
│   └── ads/                        Alerting & Detection Strategy, one per rule (t*.md)
│
└── .github/workflows/
    └── ci.yml                      on push: sigma lint → fetch Chainsaw → pytest → build coverage
```

> Not committed: `docs/mvp.md` and `docs/walkthrough.md` are local planning notes (gitignored);
> the fetched Chainsaw and Sysmon binaries; and the Sysmon config (downloaded by `setup.ps1`).

## Key design choices (and the principles they encode)

### Coverage is driven by rule content, not folders
Rules sit flat in `rules/`. Tactic and technique come from each rule's Sigma `tags:` field
(`attack.t1053.005`, …), which `tools/coverage.py` reads. The coverage map is built **only from
rules whose tests pass**, so "claimed" coverage can never drift from "verified" coverage.

### One manifest links recording ↔ rule (`tests/expectations.yml`)
```yaml
- recording: recordings/attack/T1053.005/42f53695-....evtx
  must_fire:
    - Scheduled Task Creation via schtasks.exe   # the rule's Sigma `title:`
- recording: recordings/benign/workstation-baseline.evtx
  must_not_fire: "*"          # no rule may fire on benign telemetry
```
Rules are referenced by their Sigma `title:` (what Chainsaw reports), not by filename, so the
link between an attack log and the rule it should trigger is explicit and reviewable.

### Every recording carries reproducibility metadata (`metadata.json`)
```json
{
  "technique": "T1053.005",
  "atomic_test_guid": "42f53695-ad4a-4546-abb6-7d837f644a71",
  "art_commit": "8af478b",
  "sysmon_config_tag": "configs-082cba578667",
  "windows_build": "10.0.26100",
  "attack_version": "v19",
  "system_language": "tr-TR",
  "defender": "realtime+tamper disabled",
  "networking": "off during attack",
  "recorded_utc": "2026-10-10T20:00:00Z",
  "notes": "comsvcs used for T1003.001; procdump path is access-denied in Sandbox"
}
```

### Binaries and the Sysmon config are never committed
The Chainsaw executable, `Sysmon64.exe`, and the sysmon-modular config are fetched, not
committed: `chainsaw/VERSION` pins the Chainsaw release, and `setup.ps1` pins the Sysmon
config by its release tag (`configs-082cba578667`) and downloads it. CI fetches Chainsaw the
same way. This keeps the repo small, license-clean, and reproducible.

### CI mirrors local exactly
`ci.yml` runs the same `pytest` you run locally: lint Sigma → download pinned Chainsaw → replay
every recording via `run_chainsaw.py` → assert against `expectations.yml` → regenerate coverage.
Nothing in CI is special, so a green badge means a stranger can reproduce your results.

## Licensing note
- Code (`lab/`, `tools/`, `tests/`) → MIT (`/LICENSE`).
- Rules (`rules/`) → authored here under the same license. If you ever adapt SigmaHQ rules you
  must honor their DRL; add a separate `rules/LICENSE` if that boundary is ever needed.

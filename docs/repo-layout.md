# Repo layout (v1)

```
detection-as-code/                  repo root
├── README.md                       what it is, results, how to reproduce, demo GIF
├── LICENSE                         code license (MIT or Apache-2.0)
├── .gitignore                      ignores the Chainsaw binary, scratch, local evtx exports
│
├── rules/                          THE DELIVERABLE — Sigma rules, one file per detection
│   ├── LICENSE                     (optional) separate license for the rules
│   ├── t1059_001_powershell_encoded_command.yml
│   ├── t1047_wmi_process_creation.yml
│   ├── t1053_005_scheduled_task_creation.yml
│   ├── t1547_001_registry_run_key.yml
│   ├── t1136_001_local_account_creation.yml
│   ├── t1218_011_rundll32_proxy_execution.yml
│   ├── t1218_005_mshta_proxy_execution.yml
│   ├── t1685_005_clear_event_logs.yml
│   ├── t1003_001_lsass_access.yml
│   └── t1105_ingress_tool_transfer.yml
│
├── recordings/                     captured telemetry (small, trimmed .evtx)
│   ├── attack/
│   │   └── T1053.005/
│   │       ├── 42f53695-....evtx           sysmon / security / powershell logs
│   │       └── metadata.json               full pinning info (see below)
│   └── benign/
│       ├── workstation-baseline.evtx
│       └── metadata.json
│
├── lab/                            everything that runs INSIDE Windows Sandbox
│   ├── lab.wsb                     Sandbox config (net/clipboard off, folder maps)
│   ├── scripts/
│   │   ├── setup.ps1               Sysmon + logging + audit + ART install + metadata
│   │   └── record.ps1              one technique: prereqs → net off → run → export → cleanup
│   └── sysmon/
│       └── sysmonconfig.xml        pinned sysmon-modular @ 082cba57 (binary NOT committed)
│
├── chainsaw/                       replay tool config
│   ├── mapping.yml                 pinned Sigma→EVTX field mapping
│   └── VERSION                     pinned Chainsaw release tag (binary fetched, not committed)
│
├── tests/                          proves every rule works
│   ├── expectations.yml            recording → rules that MUST / MUST NOT fire
│   ├── run_chainsaw.py             wrapper: run Chainsaw, parse --json (not exit code)
│   ├── conftest.py                 locates binary, loads expectations
│   └── test_detections.py          pytest: assert fire-on-attack + silent-on-benign
│
├── tools/
│   └── coverage.py                 reads PASSING rules' `tags:` → ATT&CK layer + README table
│
├── coverage/
│   └── navigator-layer.json        generated ATT&CK Navigator layer (verified rules only)
│
├── docs/
│   ├── mvp.md                      (moved from HQ)
│   ├── walkthrough.md              (moved from HQ)
│   ├── adr/
│   │   └── 0001-replay-tool.md     (the Chainsaw decision log)
│   └── ads/                        Alerting & Detection Strategy, one per rule
│       └── t1053_005.md
│
└── .github/workflows/
    └── ci.yml                      on push: sigma lint → fetch Chainsaw → pytest → build coverage
```

## Key design choices (and the principles they encode)

### Coverage is driven by rule content, not folders
Rules sit flat in `rules/`. Tactic and technique come from each rule's Sigma `tags:` field
(`attack.t1053.005`, …), which `tools/coverage.py` reads. The coverage map is built **only from
rules whose tests pass**, so "claimed" coverage can never drift from "verified" coverage.

### One manifest links recording ↔ rule (`tests/expectations.yml`)
```yaml
- recording: recordings/attack/T1053.005/42f53695-....evtx
  must_fire:
    - t1053_005_scheduled_task_creation
- recording: recordings/benign/workstation-baseline.evtx
  must_not_fire: "*"          # no rule may fire on benign telemetry
```
Tests read this, not filenames, so the link between an attack log and the rule it should trigger
is explicit and reviewable.

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

### Binaries are never committed
The Chainsaw executable and `Sysmon64.exe` are platform binaries with their own licenses.
`chainsaw/VERSION` and `lab/sysmon/sysmonconfig.xml` pin *what* to use; CI and the user fetch the
actual binaries. This keeps the repo small, license-clean, and reproducible.

### CI mirrors local exactly
`ci.yml` runs the same `pytest` you run locally: lint Sigma → download pinned Chainsaw → replay
every recording via `run_chainsaw.py` → assert against `expectations.yml` → regenerate coverage.
Nothing in CI is special, so a green badge means a stranger can reproduce your results.

## Licensing note
- Code (`scripts/`, `tools/`, `tests/`) → MIT or Apache-2.0 (`/LICENSE`).
- Rules (`rules/`) → decide separately; if you ever adapt SigmaHQ rules you must honor their DRL.
  Keeping a `rules/LICENSE` makes the boundary explicit even if you write all rules yourself.
```

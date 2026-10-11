# Detection-as-Code

Sigma detection rules where **every rule is proven to catch its attack and measured for
false positives**, re-checked automatically on every push.

Attack telemetry is recorded in a disposable **Windows Sandbox** with
[Atomic Red Team](https://github.com/redcanaryco/atomic-red-team) and
[Sysmon](https://learn.microsoft.com/sysinternals/downloads/sysmon), then replayed against
the rules with [Chainsaw](https://github.com/WithSecureLabs/chainsaw). No SIEM, no real
malware, no cloud cost.

## How it works

```
Windows Sandbox                         This repo + CI
──────────────                          ──────────────
setup.ps1   → Sysmon + logging
record.ps1  → run 1 Atomic test
            → export trimmed .evtx  ──►  recordings/
                                         rules/*.yml   (Sigma)
                                         Chainsaw replays recordings vs rules
                                         pytest asserts: fires on attack,
                                                         silent on benign
                                         coverage.py → ATT&CK layer (verified only)
```

A rule counts as "covered" **only if its test passes**, so claimed coverage can never
drift from verified coverage.

## Reproduce

Prereqs: Windows 11 Pro/Enterprise/Education (for Windows Sandbox), Python 3.11+.

```bash
# 1. record telemetry  (see lab/ and docs/walkthrough.md)
#    launch lab/lab.wsb, then inside: C:\lab\scripts\record.ps1 -TechniqueId ... -TestGuid ...
#    copy the exported .evtx into recordings/attack/<technique>/

# 2. get Chainsaw (pinned in chainsaw/VERSION) and run the tests
pip install pytest pyyaml
pytest -v tests/
python tools/coverage.py
```

## Layout
See [docs/repo-layout.md](docs/repo-layout.md). Key dirs: `rules/` (the deliverable),
`recordings/` (telemetry + metadata), `lab/` (Sandbox scripts), `tests/` (the proof),
`docs/` (MVP, walkthrough, decisions, ADS per rule).

## Status
First vertical slice: T1053.005 (scheduled task). Pipeline end-to-end; more techniques
being added (target: 10 across 6 tactics).

## Scope and ethics
All "attacks" are harmless Atomic Red Team simulations run only inside a disposable
Sandbox with networking disabled during execution. This repo contains detection rules and
recorded telemetry, not malware.

## Licenses
- Code (`lab/`, `tests/`, `tools/`): see [LICENSE](LICENSE).
- Rules (`rules/`): authored here; if you adapt SigmaHQ rules, honor their DRL.

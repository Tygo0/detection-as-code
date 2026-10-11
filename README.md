# Detection-as-Code

[![detections](https://github.com/Tygo0/detection-as-code/actions/workflows/ci.yml/badge.svg)](https://github.com/Tygo0/detection-as-code/actions/workflows/ci.yml)

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

The recordings are already committed, so you can verify the detections without a Sandbox:

```bash
pip install pytest pyyaml

# fetch the pinned Chainsaw (version in chainsaw/VERSION) for your OS from
# https://github.com/WithSecureLabs/chainsaw/releases and put the binary on PATH,
# in ./chainsaw/, or point $CHAINSAW at it. Then:
pytest -v tests/            # every rule: fires on attack, silent on benign
python tools/coverage.py    # rebuild the verified-only ATT&CK layer
```

To record new telemetry yourself (Windows 11 + Windows Sandbox), see
[docs/recording.md](docs/recording.md).

## Layout
See [docs/repo-layout.md](docs/repo-layout.md). Key dirs: `rules/` (the deliverable),
`recordings/` (telemetry + metadata), `lab/` (Sandbox scripts), `tests/` (the proof),
`docs/` (recording guide, decisions, ADS per rule).

## Status
**v1 complete:** 10 techniques across 6 tactics, each verified (fires on its attack
recording, silent on the benign baseline), enforced in CI.

| Tactic | Techniques |
|---|---|
| Execution | T1059.001, T1047 |
| Persistence | T1053.005, T1547.001, T1136.001 |
| Defense Evasion / Stealth | T1218.011, T1218.005 |
| Defense Impairment | T1685.005 |
| Credential Access | T1003.001 |
| Command and Control | T1105 |

## Scope and ethics
All "attacks" are harmless Atomic Red Team simulations run only inside a disposable
Sandbox with networking disabled during execution. This repo contains detection rules and
recorded telemetry, not malware.

## Licenses
- Code (`lab/`, `tests/`, `tools/`): see [LICENSE](LICENSE).
- Rules (`rules/`): authored here; if you adapt SigmaHQ rules, honor their DRL.

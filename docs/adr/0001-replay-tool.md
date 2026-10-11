# Decision log: replay tool

**Status:** Decided — **Chainsaw** (2026-10-10)
**Context:** Detection-as-code pipeline. Need a tool to replay recorded `.evtx` logs against our Sigma rules, both locally (Windows) and in CI (Linux GitHub Actions), and report per-rule hits that `pytest` can assert on.

## What does NOT matter here
Published benchmarks compare speed/memory on multi-GB log sets. Our recordings are ~1 MB each, so every tool finishes in well under a second. **Speed and memory are irrelevant to this decision.**

## What matters
1. Consume our Sigma rules with minimal friction (the rules are the deliverable — keep them as clean Sigma YAML).
2. Clear, machine-readable per-rule output (tests assert "rule R fired on attack log A, stayed silent on benign log B").
3. Runs on Windows (dev) and Linux (CI).

## Comparison

| | Chainsaw | Zircolite | Hayabusa |
|---|---|---|---|
| Language / install | Rust, single static binary | Python 3 or binary | Rust, single binary |
| Uses our Sigma YAML | Directly (`-s` + `--mapping`) | Converts first (pySigma) | Own rule format; converts Sigma |
| Per-rule result | Yes | Yes | Yes (timeline-oriented) |
| JSON output | Yes | Yes (JSONL) | Yes |
| Best known for | DFIR hunting over EVTX | Fast standalone Sigma-on-EVTX | Forensic timelines |
| Learning resources | Many, English | Good, smaller | Large, Japanese-first |
| CI gotchas | Exit codes need care | Python packaging to pin | Rule-conversion step |
| Fit for "test my own rules" | Strong | Strong | Weak |

## Decision: Chainsaw
- Reads Sigma YAML **directly** — the repo's headline artifact (the rules) stays in standard format, no converted copies.
- **One pinned release binary**, no dependency chain → trivial, reproducible CI.
- Best-documented of the three for Sigma-over-EVTX, which helps while learning.
- Lightest memory; its only weakness (slow on huge logs) never bites at our sizes.

## Consequences / things to handle
- Chainsaw needs a **mapping file** with `--sigma` (translates Sigma field names to the EVTX structure). WithSecure ships examples (e.g. `mappings/sigma-event-logs-all.yml`); we pin one in the repo.
- **CI must not trust the exit code alone.** A non-zero exit can coexist with valid matches (e.g. one unreadable file). Robust pattern: write `--json` to a fresh path, then parse that JSON to decide pass/fail.
- Pin the Chainsaw release version in both docs and CI.

## Reversibility
Low lock-in. Rules and recordings are tool-independent; switching to Zircolite later would change only the replay step. Zircolite is the documented fallback if we ever want an all-Python harness.

## Rejected
- **Zircolite** — equally capable, but converts rules (extra build step + second representation) and adds a Python env to reproduce. Kept as fallback.
- **Hayabusa** — own rule format fights "rules as Sigma YAML"; timeline focus is a different job.

## Sources
- https://github.com/WithSecureLabs/chainsaw
- https://github.com/wagga40/Zircolite
- https://github.com/calebevans/mulder/pull/95 (CI exit-code / mapping pitfalls)

"""Build an ATT&CK Navigator layer from VERIFIED rules only.

A technique counts as covered only if a rule tagged with it actually fires on its
attack recording (per tests/expectations.yml). Rules with no recording yet, or that
don't fire, are not counted - so the coverage map can never overstate reality.

Degrades gracefully: if Chainsaw or recordings are absent, those rules are simply
"unverified" and left out; the script still succeeds and writes an honest (possibly
empty) layer.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))
from run_chainsaw import run as chainsaw_run  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
RULES = REPO / "rules"


def rule_index() -> dict[str, list[str]]:
    """title -> list of attack technique IDs (e.g. T1053.005)."""
    idx: dict[str, list[str]] = {}
    for f in sorted(RULES.glob("*.yml")):
        doc = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        title = doc.get("title")
        techs = [
            str(t).split("attack.")[1].upper()
            for t in (doc.get("tags") or [])
            if str(t).startswith("attack.t")
        ]
        if title and techs:
            idx[title] = techs
    return idx


def verified_titles() -> set[str]:
    """Rule titles that actually fired on an existing attack recording."""
    exp = yaml.safe_load((REPO / "tests" / "expectations.yml").read_text(encoding="utf-8")) or []
    fired: set[str] = set()
    for e in exp:
        must = e.get("must_fire")
        if not must:
            continue
        evtx = REPO / e["recording"]
        if not evtx.exists():
            continue
        try:
            hits = chainsaw_run(evtx)
        except Exception as ex:  # chainsaw missing / unreadable -> unverified
            print(f"  (skip {e['recording']}: {ex})", file=sys.stderr)
            continue
        fired |= {r for r in must if r in hits}
    return fired


def build_layer(out: Path) -> None:
    idx = rule_index()
    verified = verified_titles()
    techniques = sorted({t for title in verified for t in idx.get(title, [])})

    layer = {
        "name": "Verified detection coverage",
        "versions": {"layer": "4.5", "navigator": "4.9.1", "attack": "19"},
        "domain": "enterprise-attack",
        "description": "Techniques with a rule proven to fire on recorded telemetry.",
        "techniques": [
            {"techniqueID": t, "score": 100, "color": "#2e7d32",
             "comment": "verified: rule fires on recording"}
            for t in techniques
        ],
        "gradient": {"colors": ["#ffffff", "#2e7d32"], "minValue": 0, "maxValue": 100},
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(layer, indent=2), encoding="utf-8")

    print(f"Verified rules : {len(verified)}")
    print(f"Techniques     : {', '.join(techniques) or '(none yet)'}")
    print(f"Layer written  : {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=REPO / "coverage" / "navigator-layer.json")
    build_layer(ap.parse_args().out)

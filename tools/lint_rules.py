"""Lint Sigma rules: valid YAML + the fields this project requires.
Exits non-zero (fails CI) if any rule is malformed."""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
RULES = REPO / "rules"

REQUIRED = ["title", "id", "logsource", "detection", "tags"]


def lint() -> int:
    errors: list[str] = []
    rule_files = sorted(RULES.glob("*.yml"))
    if not rule_files:
        print("no rules found"); return 1

    for f in rule_files:
        try:
            doc = yaml.safe_load(f.read_text(encoding="utf-8"))
        except yaml.YAMLError as e:
            errors.append(f"{f.name}: invalid YAML: {e}"); continue
        if not isinstance(doc, dict):
            errors.append(f"{f.name}: not a mapping"); continue

        for field in REQUIRED:
            if field not in doc:
                errors.append(f"{f.name}: missing '{field}'")

        det = doc.get("detection")
        if isinstance(det, dict) and "condition" not in det:
            errors.append(f"{f.name}: detection has no 'condition'")

        tags = doc.get("tags") or []
        if not any(str(t).startswith("attack.t") for t in tags):
            errors.append(f"{f.name}: no ATT&CK technique tag (attack.tXXXX)")

    for e in errors:
        print("FAIL:", e)
    print(f"\n{len(rule_files)} rule(s) checked, {len(errors)} problem(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(lint())

"""The core test: every rule must fire on its attack recording, and no rule may
fire on a benign recording. Driven entirely by tests/expectations.yml.

A recording whose .evtx file is missing is SKIPPED, not failed, so the harness is
usable before every recording exists (record them in Windows Sandbox, drop them in).
"""
from pathlib import Path

import pytest

from conftest import REPO, load_expectations
from run_chainsaw import run

EXPECTATIONS = load_expectations()


def _ids(e):
    return e.get("description", e.get("recording", "?"))


@pytest.mark.parametrize("exp", EXPECTATIONS, ids=[_ids(e) for e in EXPECTATIONS])
def test_recording(exp):
    evtx = REPO / exp["recording"]
    if not evtx.exists():
        pytest.skip(f"recording not captured yet: {exp['recording']}")

    fired = run(evtx)

    must_fire = exp.get("must_fire", [])
    for rule in must_fire:
        assert rule in fired, (
            f"rule '{rule}' did NOT fire on {exp['recording']} (fired: {sorted(fired)})"
        )

    must_not_fire = exp.get("must_not_fire")
    if must_not_fire == "*":
        assert not fired, (
            f"benign recording {exp['recording']} triggered rules: {sorted(fired)}"
        )
    elif isinstance(must_not_fire, list):
        for rule in must_not_fire:
            assert rule not in fired, (
                f"rule '{rule}' wrongly fired on {exp['recording']}"
            )

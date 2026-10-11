"""Shared pytest fixtures: load expectations.yml and expose the repo root."""
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]


def load_expectations() -> list[dict]:
    data = yaml.safe_load((REPO / "tests" / "expectations.yml").read_text(encoding="utf-8"))
    return data or []


@pytest.fixture(scope="session")
def repo() -> Path:
    return REPO

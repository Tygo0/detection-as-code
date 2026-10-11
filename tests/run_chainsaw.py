"""Thin wrapper around Chainsaw: run it against one .evtx with our Sigma rules,
and return the set of rule titles that fired.

Design note (see docs/adr/0001-replay-tool.md): we do NOT trust Chainsaw's exit
code to mean "found / not found". A non-zero exit can coexist with valid matches
(e.g. one unreadable file), and a zero exit with an empty output file is possible.
So we always write --json to a fresh path and decide from the parsed JSON.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RULES = REPO / "rules"
MAPPING = REPO / "chainsaw" / "mapping.yml"


def find_chainsaw() -> str:
    """Locate the Chainsaw binary: $CHAINSAW env, PATH, or repo-local ./chainsaw/."""
    import os

    env = os.environ.get("CHAINSAW")
    if env and Path(env).exists():
        return env
    for name in ("chainsaw", "chainsaw.exe"):
        found = shutil.which(name)
        if found:
            return found
        local = REPO / "chainsaw" / name
        if local.exists():
            return str(local)
    raise FileNotFoundError(
        "Chainsaw binary not found. Set $CHAINSAW, add it to PATH, or place it in ./chainsaw/. "
        "Pinned version is in chainsaw/VERSION."
    )


def run(evtx: Path) -> set[str]:
    """Return the set of Sigma rule titles that fired on this evtx file."""
    evtx = Path(evtx)
    if not evtx.exists():
        raise FileNotFoundError(f"Recording not found: {evtx}")

    chainsaw = find_chainsaw()
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "hits.json"
        cmd = [
            chainsaw, "hunt", str(evtx),
            "--sigma", str(RULES),
            "--mapping", str(MAPPING),
            "--json", "--output", str(out),
        ]
        # encoding/errors are explicit: Chainsaw's stderr can contain bytes that a
        # non-UTF-8 system locale (e.g. tr-TR cp1254) cannot decode.
        proc = subprocess.run(
            cmd, capture_output=True, text=True, encoding="utf-8", errors="replace"
        )

        # Exit code is advisory only. Decide from the JSON file instead.
        if not out.exists():
            raise RuntimeError(
                f"Chainsaw produced no output file (exit {proc.returncode}).\n"
                f"stderr:\n{proc.stderr}"
            )
        text = out.read_text(encoding="utf-8").strip()
        if not text:
            return set()  # ran cleanly, nothing matched
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Chainsaw JSON was not parseable: {e}\n{text[:500]}")

    titles: set[str] = set()
    for hit in data:
        # Chainsaw groups detections under the matched rule's name.
        name = hit.get("name") or hit.get("group")
        if name:
            titles.add(name)
        for d in hit.get("document", {}).get("data", {}).get("detections", []) or []:
            if isinstance(d, str):
                titles.add(d)
    return titles


if __name__ == "__main__":
    import sys

    for f in sys.argv[1:]:
        print(f, "->", sorted(run(Path(f))))

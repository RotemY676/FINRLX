#!/usr/bin/env python3
"""PROGRAM LEAP state-drift check (C1 prep, gate G9.1-lite).

Fails when a PHASE_LEAP_* report exists in DOCS/handoff that the living
STATE_OF_THE_PRODUCT ledger never references — the exact drift failure mode
the plan's risk register calls this project's chronic risk.
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
STATE = ROOT / "DOCS" / "STATE_OF_THE_PRODUCT.md"
HANDOFF = ROOT / "DOCS" / "handoff"


def main() -> int:
    if not STATE.exists():
        print("STATE-DRIFT: FAIL — STATE_OF_THE_PRODUCT.md missing")
        return 1
    state = STATE.read_text(encoding="utf-8")
    reports = sorted(p.name for p in HANDOFF.glob("PHASE_LEAP_*.md"))
    # A report is "referenced" if its filename OR its phase token (e.g. F1, S8)
    # appears in the ledger.
    missing = []
    for name in reports:
        m = re.match(r"PHASE_LEAP_([A-Z]\d+[A-Z]?)_", name)
        token = m.group(1) if m else None
        if name in state or (token and re.search(rf"\b{token}\b", state)):
            continue
        missing.append(name)
    if missing:
        print("STATE-DRIFT: FAIL — reports unreferenced in the ledger:")
        for n in missing:
            print(f"  - {n}")
        return 1
    print(f"STATE-DRIFT: PASS ({len(reports)} phase reports referenced)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

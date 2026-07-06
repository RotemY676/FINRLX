#!/usr/bin/env python3
"""PROGRAM LEAP gate U9 — Question-Zero linter (QZ-2).

Scans phase reports (and any text passed as arguments) for interrogative
sentences addressed to the operator. The program's acceptance test is a
full run with zero questions directed at the operator; this linter makes
that mechanical.

Heuristic: a line is a violation when it ends with '?' AND contains a
second-person operator address ("you", "your", "do we", "should we",
"shall", "please confirm", "approve"). Rhetorical/user-facing '?' strings
inside quoted UI copy are exempt via the QZ-OK marker on the same line.
"""
from __future__ import annotations
import re, sys
from pathlib import Path

ADDRESS = re.compile(
    r"\b(you|your|do we|should (we|i)|shall (we|i)|please (confirm|approve|advise)|"
    r"let me know|which (do|would) you|can you)\b",
    re.I,
)

def violations(text: str, name: str) -> list[str]:
    out = []
    for i, line in enumerate(text.splitlines(), 1):
        s = line.strip()
        if not s or "QZ-OK" in s:
            continue
        if s.rstrip("*_`).\u201d\"'").endswith("?") and ADDRESS.search(s):
            out.append(f"{name}:{i}: {s[:120]}")
    return out

def main(paths: list[str]) -> int:
    vio: list[str] = []
    for p in paths:
        path = Path(p)
        files = (
            [f for f in path.rglob("*.md") if "LEAP" in f.name.upper() or "council" in str(f)]
            if path.is_dir() else [path]
        )
        for f in files:
            try:
                vio += violations(f.read_text(encoding="utf-8", errors="replace"), str(f))
            except OSError:
                continue
    if vio:
        print("QUESTION-ZERO: FAIL")
        print("\n".join(vio))
        return 1
    print("QUESTION-ZERO: PASS")
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] or ["DOCS/handoff"]))

#!/usr/bin/env python3
"""PROGRAM LEAP Question-Zero linter (QZ-2, gate U9).
Scans given files (phase reports / PR bodies) for interrogative sentences
addressed to the operator. Exit 1 on violation."""
import re, sys, pathlib

OPERATOR_QUESTION = re.compile(
    r"(?i)\b(should (we|i)|do you (want|prefer|need)|would you like|"
    r"please (confirm|advise|decide)|let me know (if|whether|which)|"
    r"which (option|approach) (do you|would you))\b[^.\n]*\??")
BARE_QUESTION = re.compile(r"(?m)^(?!.*\|).*\?\s*$")  # ?-terminated lines outside tables

ALLOW_MARKER = "<!-- qz-allow -->"  # for rhetorical/doc questions, must be justified in report

def check(path: pathlib.Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    hits = []
    for m in OPERATOR_QUESTION.finditer(text):
        line = text[:m.start()].count("\n") + 1
        if ALLOW_MARKER not in text.splitlines()[line - 1]:
            hits.append(f"{path}:{line}: operator-directed question: {m.group(0)[:80]!r}")
    for m in BARE_QUESTION.finditer(text):
        frag = m.group(0).strip()
        if ALLOW_MARKER in frag or frag.startswith(("#", ">", "-", "*", "`")):
            continue
        line = text[:m.start()].count("\n") + 1
        hits.append(f"{path}:{line}: unanswered question line: {frag[:80]!r}")
    return hits

def main(argv: list[str]) -> int:
    targets = [pathlib.Path(a) for a in argv[1:]] or list(
        pathlib.Path("DOCS/handoff").glob("PHASE_LEAP_*.md"))
    problems: list[str] = []
    for t in targets:
        if t.exists():
            problems += check(t)
    if problems:
        print("QUESTION-ZERO: FAIL")
        print("\n".join(problems))
        return 1
    print("QUESTION-ZERO: PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

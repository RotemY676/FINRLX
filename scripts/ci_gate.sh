#!/usr/bin/env bash
# PROGRAM LEAP F0 — the universal merge gate (U1).
# Runs backend + frontend verification. Exit 0 = mergeable.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FAIL=0
step() { echo; echo "=== $1 ==="; }

step "Backend: pytest"
(cd "$ROOT/backend" && python3 -m pytest tests/ -q) || FAIL=1

step "Frontend: typecheck"
(cd "$ROOT/frontend" && npx tsc --noEmit) || FAIL=1

step "Frontend: lint"
(cd "$ROOT/frontend" && npx eslint . --max-warnings=0 --quiet) || FAIL=1

step "Frontend: unit tests"
(cd "$ROOT/frontend" && npx vitest run --reporter=dot) || FAIL=1

step "Frontend: production build"
(cd "$ROOT/frontend" && npx next build) || FAIL=1

step "Question-zero linter"
(cd "$ROOT" && python3 scripts/question_zero_check.py DOCS/handoff) || FAIL=1

if [ "$FAIL" -ne 0 ]; then echo; echo "CI GATE: FAIL"; exit 1; fi
echo; echo "CI GATE: PASS"

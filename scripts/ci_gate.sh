#!/usr/bin/env bash
# PROGRAM LEAP universal CI gate (U1). Exit 0 = pass.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
echo "== LEAP CI GATE =="
echo "-- backend: pytest --"
cd "$ROOT/backend"
python -m pytest -q --maxfail=5
echo "-- frontend: typecheck + lint + unit + build --"
cd "$ROOT/frontend"
npx tsc --noEmit
npx eslint . --max-warnings=0 || npx next lint --max-warnings=0
npx vitest run --reporter=dot
npx next build
echo "== LEAP CI GATE: PASS =="

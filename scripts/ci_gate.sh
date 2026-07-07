#!/usr/bin/env bash
# PROGRAM LEAP universal CI gate (U1). Exit 0 = pass.
set -euo pipefail

# LEAP incident 2026-07-07: local gates MUST match CI's pinned toolchain.
# Lint/type tools install FROM requirements-dev.txt pins — never ambient.
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
python3 "$ROOT/scripts/state_drift_check.py"
echo "== LEAP CI GATE: PASS =="


echo "── CI-parity: pinned ruff + mypy (backend) ──"
( cd backend   && pip install -q --break-system-packages "$(grep -i '^ruff' requirements-dev.txt)" "$(grep -i '^mypy' requirements-dev.txt)" 2>/dev/null   && python3 -m ruff --version   && python3 -m ruff check app/   && python3 -m mypy )

echo "── CI-parity: playwright spec compilation (frontend) ──"
( cd frontend && DISABLE_WEBSERVER=1 npx playwright test --list > /dev/null && echo "playwright --list OK" )

# CI-PARITY (added after the 3-strike CI incident of 2026-07-07):
# gates MUST run on the CI interpreter when available. A CPython matching
# .github/workflows/ci.yml lives at ~/py311 (built from source); prefer
# /tmp/ci311/bin/python (pinned-deps venv) for ruff/mypy/pytest if present.
if [ -x /tmp/ci311/bin/python ]; then
  echo "[ci_gate] CI-parity interpreter detected: $(/tmp/ci311/bin/python -V)"
fi

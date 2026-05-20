#!/usr/bin/env bash
# Phase MVP-7 — Deploy smoke test.
#
# Run AFTER a Railway deploy to confirm the live service is answerable.
# Usage:
#   FINRLX_BACKEND_URL=https://your-backend.up.railway.app \
#   FINRLX_FRONTEND_URL=https://your-frontend.up.railway.app \
#   bash scripts/deploy_smoke.sh
#
# Exits 0 if every check passes, 1 on any failure. Each check logs to stdout
# so the operator can paste the output into the deploy notes.

set -u

BACKEND="${FINRLX_BACKEND_URL:-}"
FRONTEND="${FINRLX_FRONTEND_URL:-}"

if [[ -z "$BACKEND" || -z "$FRONTEND" ]]; then
  echo "ERROR: set FINRLX_BACKEND_URL and FINRLX_FRONTEND_URL" >&2
  exit 1
fi

PASSED=0
FAILED=0

check() {
  local name="$1"
  local url="$2"
  local expected_status="$3"
  local extra_grep="${4:-}"

  printf "  %-32s " "$name"
  local response
  response=$(curl -s -o /tmp/finrlx_smoke_body -w "%{http_code}" --max-time 30 "$url" || echo "000")
  if [[ "$response" != "$expected_status" ]]; then
    echo "FAIL (expected $expected_status, got $response)"
    FAILED=$((FAILED + 1))
    return
  fi
  if [[ -n "$extra_grep" ]] && ! grep -q "$extra_grep" /tmp/finrlx_smoke_body; then
    echo "FAIL (body missing pattern: $extra_grep)"
    cat /tmp/finrlx_smoke_body | head -c 200
    echo
    FAILED=$((FAILED + 1))
    return
  fi
  echo "OK"
  PASSED=$((PASSED + 1))
}

echo
echo "FINRLX deploy smoke — $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "backend:  $BACKEND"
echo "frontend: $FRONTEND"
echo
echo "Backend checks"
check "GET /healthz"            "$BACKEND/healthz"            "200" '"status"'
check "GET /api/health"         "$BACKEND/api/health"         "200" "ok"
check "GET /api/v1/flags"       "$BACKEND/api/v1/flags"       "200" "feature_"
check "GET /openapi.json"       "$BACKEND/openapi.json"       "200" "openapi"

echo
echo "Frontend checks"
check "GET /"                   "$FRONTEND/"                  "200" "FINRLX"
check "GET /disclaimer"         "$FRONTEND/disclaimer"        "200" "Not investment advice"
check "GET /terms"              "$FRONTEND/terms"             "200" "Terms"
check "GET /privacy"            "$FRONTEND/privacy"           "200" "Privacy"

echo
echo "Backend security headers"
HEADERS=$(curl -sI --max-time 30 "$BACKEND/healthz" || echo "")
for hdr in "x-frame-options" "x-content-type-options" "referrer-policy" "strict-transport-security"; do
  printf "  %-32s " "$hdr"
  if echo "$HEADERS" | grep -qi "^$hdr:"; then
    echo "OK"
    PASSED=$((PASSED + 1))
  else
    echo "FAIL (missing)"
    FAILED=$((FAILED + 1))
  fi
done

echo
echo "Summary: $PASSED passed, $FAILED failed"
exit $FAILED

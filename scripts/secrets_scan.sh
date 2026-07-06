#!/usr/bin/env bash
# PROGRAM LEAP secrets scan (F0.4). Full available history + worktree.
# Allowlist: scripts/secrets_allowlist.txt (documented false positives only).
set -uo pipefail
cd "$(dirname "$0")/.."
PATTERNS='github_pat_[A-Za-z0-9_]{20,}|ghp_[A-Za-z0-9]{30,}|AKIA[0-9A-Z]{16}|sk-ant-[A-Za-z0-9-]{20,}|xox[baprs]-[A-Za-z0-9-]{10,}|-----BEGIN (RSA|EC|OPENSSH) PRIVATE KEY-----'
ALLOW="scripts/secrets_allowlist.txt"
TMP="$(mktemp)"
{ git rev-list --all | while read -r c; do git grep -EI "$PATTERNS" "$c" -- . 2>/dev/null; done
  git grep -EI "$PATTERNS" -- . 2>/dev/null; } \
  | grep -v "secrets_scan.sh\|secrets_allowlist.txt" \
  | { if [ -f "$ALLOW" ]; then grep -vFf <(grep -v '^#' "$ALLOW" | sed '/^$/d'); else cat; fi; } \
  | sed 's/^[0-9a-f]\{40\}://' | sort -u > "$TMP"
if [ -s "$TMP" ]; then echo "SECRETS SCAN: FINDINGS"; cat "$TMP"; rm -f "$TMP"; exit 1
else echo "SECRETS SCAN: CLEAN (allowlisted: $(grep -cv '^#' "$ALLOW" 2>/dev/null || echo 0) documented)"; rm -f "$TMP"; exit 0; fi

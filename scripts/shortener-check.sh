#!/usr/bin/env bash
# One-shot local validation for FZBypassBot shortener handlers.
set -Eeuo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
TMP_LOG="$(mktemp)"
trap 'rm -f "$TMP_LOG"' EXIT

stage="python-compile"
if ! python3 -W error::SyntaxWarning -m compileall -q FZBypass tests >"$TMP_LOG" 2>&1; then
  echo "RESULT=FAIL | stage=$stage"
  tail -n 3 "$TMP_LOG"
  exit 1
fi

stage="pytest"
if ! python3 -m pytest -q >"$TMP_LOG" 2>&1; then
  echo "RESULT=FAIL | stage=$stage"
  tail -n 3 "$TMP_LOG"
  exit 1
fi
TEST_SUMMARY="$(grep -E '[0-9]+ passed|[0-9]+ failed|[0-9]+ error' "$TMP_LOG" | tail -n 1 || true)"
TEST_SUMMARY="${TEST_SUMMARY:-pytest completed}"

# DNS is diagnostic, not a unit-test gate: third-party CDN DNS can be transient.
DNS_OK=0
DNS_FAIL=0
for host in cuttty.com cdn.cuty.io exeygo.com gplinks.co; do
  if getent ahosts "$host" >/dev/null 2>&1; then
    DNS_OK=$((DNS_OK + 1))
  else
    DNS_FAIL=$((DNS_FAIL + 1))
  fi
done

echo "RESULT=PASS | compile=PASS | tests=${TEST_SUMMARY} | dns_ok=$DNS_OK/4 | dns_unresolved=$DNS_FAIL/4"

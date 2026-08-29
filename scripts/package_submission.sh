#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

# Packages the submission zip: code + data + eval + results + trajectories +
# docs, excluding anything that shouldn't leave the repo (.git, .env,
# __pycache__, the LedgerGuard archive's raw pilot data is fine to keep --
# it's synthetic evidence, not a secret). Enforces the 50MB cap and runs a
# basic secret scan before writing the zip.

OUT="submission.zip"
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

echo "Staging files..."
tar --exclude='.git' --exclude='.env' --exclude='__pycache__' \
  --exclude='*.pyc' --exclude='submission.zip' \
  -cf - . | tar -xf - -C "$STAGE"

echo "Secret scan (best-effort grep for common key patterns)..."
if grep -rlE '(sk-ant-[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----)' \
    "$STAGE" --exclude-dir=.git 2>/dev/null; then
  echo "ERROR: possible secret found above -- aborting. Review and re-run." >&2
  exit 1
fi
if [ -f "$STAGE/.env" ]; then
  echo "ERROR: .env present in staged files -- aborting." >&2
  exit 1
fi
echo "No secrets found."

echo "Zipping..."
( cd "$STAGE" && zip -qr "$OLDPWD/$OUT" . -x '.env' )

SIZE_MB=$(du -m "$OUT" | cut -f1)
echo "Wrote $OUT (${SIZE_MB}MB)"
if [ "$SIZE_MB" -gt 50 ]; then
  echo "ERROR: $OUT is ${SIZE_MB}MB, exceeds the 50MB submission cap." >&2
  exit 1
fi
echo "Under the 50MB cap. Ready for the submission form."

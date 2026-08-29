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
# grep -o to extract just the matches, then filter out degenerate matches
# (e.g. "AKIAAAAAAAAAAAAAAAAA") that are base64-encoded binary padding
# (repeated null bytes in embedded video/audio data: URIs) coincidentally
# matching the AWS-key shape, not real keys -- a real key has high char
# diversity, a padding run does not.
MATCHES=$(grep -rnoE '(sk-ant-[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----)' \
    "$STAGE" --exclude-dir=.git 2>/dev/null || true)
if [ -n "$MATCHES" ]; then
  REAL_HITS=$(echo "$MATCHES" | python3 -c '
import sys, re
for line in sys.stdin:
    line = line.rstrip("\n")
    m = re.search(r"(sk-ant-[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----)", line)
    if not m:
        continue
    token = m.group(1)
    if len(set(token)) <= 3:
        continue  # degenerate repeat (base64 padding artifact), not a real key
    print(line)
')
  if [ -n "$REAL_HITS" ]; then
    echo "$REAL_HITS"
    echo "ERROR: possible secret found above -- aborting. Review and re-run." >&2
    exit 1
  fi
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

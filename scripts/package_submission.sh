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
# grep -n (no -o) so the Python filter sees each full matching line, not just
# the isolated token -- two independent, narrow false-positive filters, both
# checked per-match (a single long line, e.g. a flattened JSONL trajectory
# entry, can carry several matches, so every match is checked on its own via
# finditer, not just the first):
#   1. Degenerate token (e.g. "AKIAAAAAAAAAAAAAAAAA"): <=3 distinct chars --
#      base64-encoded binary padding coincidentally matching the AWS-key
#      shape, not a real key (real keys have high char diversity).
#   2. Unbroken base64 run: the 40 chars on each side of the match are pure
#      base64 alphabet (no quotes/spaces/punctuation at all) -- this only
#      happens sitting inside a continuous data: URI (embedded video/audio),
#      never in real code/config, which always has syntax near an actual
#      credential assignment. Verified against this repo's own
#      video/demo_page_v3.html and every trajectories/**/*.jsonl file before
#      shipping this filter, so it narrows false positives without
#      narrowing real-secret detection.
MATCHES=$(grep -rnE '(sk-ant-[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----)' \
    "$STAGE" --exclude-dir=.git 2>/dev/null || true)
if [ -n "$MATCHES" ]; then
  REAL_HITS=$(echo "$MATCHES" | python3 -c '
import sys, re
PATTERN = re.compile(r"(sk-ant-[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----)")
CONTEXT = 40
# EXACT-value allowlist, not a file/line/pattern exemption -- every entry here
# was individually verified (2026-08-29) to be either AWS'"'"'s own documented
# public example key, or a synthetic string this same recorded session typed
# solely to test this scanner'"'"'s filter logic, confirmed to appear nowhere
# else in the repo. Any other AKIA/sk-ant/private-key-shaped value, in any
# file, on any line, still fails packaging -- this list grows only by exact
# value, one confirmed-safe token at a time, never by relaxing the regex or
# widening scope to a path.
ALLOWLISTED_TOKENS = {
    "AKIAIOSFODNN7EXAMPLE",                    # AWS docs'"'"' own public placeholder key
    "AKIA3XZ9QK7M2LPWYRTB",                    # synthetic scanner-test token (this session)
    "AKIAABABABABABABABAB",                    # synthetic scanner-test token (this session)
    "sk-ant-api03-abc123XYZ789defGHI456jkl",   # synthetic scanner-test token (this session)
    "-----BEGIN RSA PRIVATE KEY-----",         # bare PEM header only, no key body (this session'"'"'s test)
}
for line in sys.stdin:
    line = line.rstrip("\n")
    hits = []
    for m in PATTERN.finditer(line):
        token = m.group(1)
        if token in ALLOWLISTED_TOKENS:
            continue  # individually verified non-secret, see ALLOWLISTED_TOKENS above
        if len(set(token)) <= 3:
            continue  # degenerate repeat (base64 padding artifact)
        start, end = max(0, m.start() - CONTEXT), min(len(line), m.end() + CONTEXT)
        if re.fullmatch(r"[A-Za-z0-9+/=]*", line[start:end]):
            continue  # inside an unbroken base64 run, not real code/config
        hits.append(token)
    if hits:
        # Print the file:line prefix plus just the surviving tokens, not the
        # (possibly multi-million-character, for a flattened trajectory
        # line) raw line itself.
        prefix = line.split(":", 2)
        loc = ":".join(prefix[:2]) if len(prefix) >= 2 else "?"
        print(f"{loc}: {hits}")
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

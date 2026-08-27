#!/usr/bin/env bash
set -euo pipefail

# If the stack ends up needing API keys/secrets (external model APIs, etc.),
# load them from a local .env (see .env.example, gitignored) so the same
# script works locally and in CI (where the equivalent vars come in as
# GitHub Actions secrets, already present in the environment -- no .env
# needed there):
#   if [ -f .env ]; then set -a; source .env; set +a; fi
# Then fail fast with a clear message if something required is missing, e.g.:
#   : "${SOME_API_KEY:?Set SOME_API_KEY (see .env.example) before running setup}"

# TODO once the problem + stack are known: pin exact versions here
# (requirements.txt / package.json / go.mod / Cargo.toml — whatever applies)
# so `make setup` reproduces the same environment on a clean machine.
echo "Add environment setup here (dependency install, env vars, service checks)."

#!/usr/bin/env sh
set -eu

# Portable POSIX wrapper for Jenkins, Forgejo/Gitea Actions, Woodpecker CI, or local runs.
if [ ! -f "scripts/sdd_cli.py" ]; then
  printf '%s\n' "[FAIL] Run this script from the repository root (scripts/sdd_cli.py not found)." >&2
  exit 1
fi

if command -v uv >/dev/null 2>&1; then
  exec uv run python scripts/sdd_cli.py ci-verify --mode auto --run-stack-if-approved --format text "$@"
elif command -v python3 >/dev/null 2>&1; then
  exec python3 scripts/sdd_cli.py ci-verify --mode auto --run-stack-if-approved --format text "$@"
elif command -v python >/dev/null 2>&1; then
  exec python scripts/sdd_cli.py ci-verify --mode auto --run-stack-if-approved --format text "$@"
else
  printf '%s\n' "[FAIL] Neither 'uv', 'python3', nor 'python' was found in PATH." >&2
  exit 127
fi

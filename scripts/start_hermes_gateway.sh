#!/usr/bin/env bash
set -euo pipefail

HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
CONFIG_FILE="${HERMES_CONFIG:-$HERMES_HOME/config/hermes.yaml}"
ENV_FILE="${HERMES_ENV:-$HERMES_HOME/.env}"

if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

export HERMES_HOME
export HERMES_CONFIG="$CONFIG_FILE"

if [[ ! -f "$CONFIG_FILE" ]]; then
  echo "ERROR: missing Hermes config: $CONFIG_FILE" >&2
  echo "Run: python scripts/apply_local_hermes_config.py --target $HERMES_HOME --force" >&2
  exit 2
fi

if command -v hermes >/dev/null 2>&1; then
  echo "starting=hermes gateway"
  echo "hermes_home=$HERMES_HOME"
  echo "config=$CONFIG_FILE"
  exec hermes gateway --config "$CONFIG_FILE"
fi

if command -v gateway >/dev/null 2>&1; then
  echo "starting=gateway"
  echo "hermes_home=$HERMES_HOME"
  echo "config=$CONFIG_FILE"
  exec gateway --config "$CONFIG_FILE"
fi

echo "ERROR: neither 'hermes' nor 'gateway' executable was found in PATH." >&2
echo "Install or expose your local Hermes gateway binary, then rerun:" >&2
echo "  HERMES_HOME=$HERMES_HOME scripts/start_hermes_gateway.sh" >&2
exit 127

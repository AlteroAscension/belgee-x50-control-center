#!/usr/bin/env bash
set -euo pipefail

options=/data/options.json
refresh=2
if [[ -f "$options" ]]; then
  refresh="$(jq --raw-output '.refresh_seconds // 2' "$options")"
fi

export X50_REFRESH_SECONDS="$refresh"
exec python3 /app/server.py

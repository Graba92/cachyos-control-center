#!/usr/bin/env bash
# ==============================================================================
# CachyOS Control Center — Universal Launcher
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Falls ein lokales .venv existiert, dieses vorziehen
if [ -d "$SCRIPT_DIR/.venv" ] && [ -f "$SCRIPT_DIR/.venv/bin/python3" ]; then
    exec "$SCRIPT_DIR/.venv/bin/python3" "$SCRIPT_DIR/app.py" "$@"
else
    exec python3 "$SCRIPT_DIR/app.py" "$@"
fi

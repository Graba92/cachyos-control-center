#!/usr/bin/env bash
# ==============================================================================
# CachyOS Control Center — Universal Launcher
# ==============================================================================

SCRIPT_PATH="$(realpath "${BASH_SOURCE[0]}" 2>/dev/null || readlink -f "${BASH_SOURCE[0]}" 2>/dev/null || echo "${BASH_SOURCE[0]}")"
SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_PATH")" && pwd)"

# Falls das interaktive TUI-Cockpit ohne Terminal aufgerufen wird (z. B. Doppelklick in Dolphin/KDE),
# automatisch das Standardterminal mit dem Cockpit öffnen. Headless CLI-Befehle bleiben direkt.
if [ $# -eq 0 ] && { [ ! -t 0 ] || [ "${TERM:-}" = "dumb" ] || [ -z "${TERM:-}" ]; } && [ -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ]; then
    for term in konsole alacritty kitty ptyxis xfce4-terminal gnome-terminal xterm; do
        if command -v "$term" &>/dev/null; then
            exec "$term" -e "$0" "$@"
        fi
    done
fi

# Falls ein lokales .venv existiert, dieses vorziehen
if [ -d "$SCRIPT_DIR/.venv" ] && [ -f "$SCRIPT_DIR/.venv/bin/python3" ]; then
    exec "$SCRIPT_DIR/.venv/bin/python3" "$SCRIPT_DIR/app.py" "$@"
else
    exec python3 "$SCRIPT_DIR/app.py" "$@"
fi


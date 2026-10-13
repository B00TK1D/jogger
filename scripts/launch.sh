#!/usr/bin/env bash
set -u

CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_DIR="$(cd "$CURRENT_DIR/.." && pwd)"
PY_SCRIPT="$CURRENT_DIR/jogger.py"

pane_id="${1:-}"

# Dependency checks.
if ! command -v python3 >/dev/null 2>&1; then
    tmux display-message "tmux-jogger: python3 is required" 2>/dev/null || true
    exit 1
fi
if ! command -v tmux >/dev/null 2>&1; then
    echo "tmux-jogger: tmux is required" >&2
    exit 1
fi

get_opt() {
    local opt="$1" def="$2"
    local val
    val="$(tmux show-options -gqv "$opt" 2>/dev/null || true)"
    if [ -z "$val" ]; then printf '%s' "$def"; else printf '%s' "$val"; fi
}

# Popup state file for toggle support.
state_file="${TMPDIR:-/tmp}/tmux-jogger-popup-${UID:-$(id -u)}.pid"

# If a previous popup helper is running, kill it (close popup) and exit.
if [ -f "$state_file" ]; then
    old_pid="$(cat "$state_file" 2>/dev/null || true)"
    if [ -n "$old_pid" ] && kill -0 "$old_pid" 2>/dev/null; then
        # Popup already open; do nothing. Close with Ctrl-C inside the popup.
        exit 0
    fi
    rm -f "$state_file"
fi

# Validate pane id.
case "$pane_id" in
    %*) ;;
    *) tmux display-message "tmux-jogger: invalid pane id" 2>/dev/null || true; exit 1 ;;
esac

# Dimensions with sensible minimums.
width="$(get_opt @jogger_popup_width 60)"
height="$(get_opt @jogger_popup_height 10)"
# enforce minimums
[ "$width" -lt 40 ] 2>/dev/null && width=40
[ "$height" -lt 8 ] 2>/dev/null && height=8

tmux display-popup -E -T 'jogger' -w "$width" -h "$height" "PYTHONPATH='$PLUGIN_DIR' python3 '$PY_SCRIPT' --pane '$pane_id' --state-file '$state_file'"
#!/usr/bin/env bash
# TPM entry point for tmux-jogger

CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS_DIR="$CURRENT_DIR/scripts"
LAUNCHER="$SCRIPTS_DIR/launch.sh"

# Read a tmux option, returning empty when unavailable.
get_tmux_option() {
    local option="$1"
    local default="${2:-}"
    local value
    value="$(tmux show-options -gqv "$option" 2>/dev/null || true)"
    if [ -z "$value" ]; then
        printf '%s' "$default"
    else
        printf '%s' "$value"
    fi
}

# Dependency check: tmux 3.2+
tmux_version="$(tmux -V 2>/dev/null | sed -n 's/^tmux \([0-9][0-9.]*\).*/\1/p')"
major="${tmux_version%%.*}"
rest="${tmux_version#*.}"
minor="${rest%%.*}"
if [ -z "$tmux_version" ] || [ "${major:-0}" -lt 3 ] 2>/dev/null || { [ "${major:-0}" -eq 3 ] && [ "${minor:-0}" -lt 2 ]; }; then
    tmux display-message "tmux-jogger: tmux 3.2+ is required (found: ${tmux_version:-none})" 2>/dev/null || true
    exit 0
fi

KEY="$(get_tmux_option @jogger_key u)"

# Register binding. The launcher captures the pane id at invocation.
tmux bind-key "$KEY" run-shell -b "\"$LAUNCHER\" '#{pane_id}'"
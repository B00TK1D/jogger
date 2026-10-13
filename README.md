# tmux-jogger

Jog your memory: turn a short natural-language description into a shell command
inside tmux. Press a key, type a request, get a debounced command suggestion,
press Enter to insert it (never executed).

## Requirements

- tmux 3.2+ (uses `display-popup`)
- Python 3 (standard library only)
- An OpenAI-compatible Chat Completions endpoint and API key

## Install (TPM)

Add to `~/.tmux.conf`:

```tmux
set -g @plugin 'OWNER/tmux-jogger'
set -g @jogger_model 'gpt-4o-mini'
# optional:
# set -g @jogger_api_base 'https://api.openai.com/v1'
# set -g @jogger_key 'u'
```

Ensure `run '~/.tmux/plugins/tpm/tpm'` remains at the end of `~/.tmux.conf`.
Reload: `tmux source-file ~/.tmux.conf`, then press `prefix + I` to install.
Set the API key in the environment that starts tmux:

```sh
export OPENAI_API_KEY=sk-...
# or, for a running server:
tmux set-environment -g OPENAI_API_KEY sk-...
```

## Manual install

```sh
git clone https://github.com/OWNER/tmux-jogger ~/.tmux/plugins/tmux-jogger
# add to ~/.tmux.conf:
run-shell ~/.tmux/plugins/tmux-jogger/jogger.tmux
tmux source-file ~/.tmux.conf
```

## Configuration

| Option | Default | Description |
|---|---|---|
| `@jogger_key` | `u` | Key under the tmux prefix |
| `@jogger_api_base` | `https://api.openai.com/v1` | OpenAI-compatible base URL |
| `@jogger_api_key` | (env) | API key (prefer `OPENAI_API_KEY`) |
| `@jogger_model` | (required) | Model name |
| `@jogger_debounce_ms` | `400` | Typing debounce |
| `@jogger_timeout_seconds` | `20` | Request timeout |
| `@jogger_system_prompt` | (built-in) | System-prompt override |
| `@jogger_max_tokens` | (unset) | Output limit |
| `@jogger_cache_max_entries` | `1000` | Max cached entries |
| `@jogger_cache_dir` | (XDG) | Cache directory override |
| `@jogger_popup_width` | `60` | Popup width (min 40) |
| `@jogger_popup_height` | `10` | Popup height (min 8) |

## First use

1. Press `prefix + u` (or configured key).
2. Type a request. A command suggestion appears after a short debounce;
   cached results appear instantly.
3. Press `Enter` to insert the current suggestion into the pane that was
   focused when the plugin opened. The command is inserted, not executed.
4. Press `Ctrl-C` or `prefix + u` again to close without inserting.
5. Empty input never generates or inserts a command.

## Cache

Stored in `${XDG_CACHE_HOME:-$HOME/.cache}/tmux-jogger/cache.json`
(directory `0700`, file `0600`). SHA-256 keyed on the trimmed description plus
model, API base, and a hash of the effective system prompt. Local only;
clear it manually:

```sh
rm -rf "${XDG_CACHE_HOME:-$HOME/.cache}/tmux-jogger"
```

Descriptions and uncached commands are sent to the configured API provider.

## Tests

```sh
python3 -m unittest discover -s tests
```

## Uninstall

Remove the plugin line from `~/.tmux.conf`, run `prefix + alt + u` (TPM uninstall)
or delete `~/.tmux/plugins/tmux-jogger`, reload tmux, and remove the cache dir.

## Privacy / security

- Commands are never executed automatically; they are inserted as literal text.
- API keys are never logged or shown.
- No pane history or environment data is sent unless explicitly configured.

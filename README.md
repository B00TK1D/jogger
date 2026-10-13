# jogger

A tmux plugin that turns a short natural-language description into a shell
command. Press the key, type your request, get a suggestion, press Enter to
insert it (never executed).

## Quickstart

1. Install with TPM by adding to `~/.tmux.conf`:

   ```tmux
   set -g @plugin 'B00TK1D/jogger'
   set -g @jogger_model 'gpt-4o-mini'   # required
   ```

2. Set your API key in the environment that starts tmux:

   ```sh
   export OPENAI_API_KEY=sk-...
   ```

3. Reload and install:

   ```sh
   tmux source-file ~/.tmux.conf
   # then press prefix + I
   ```

4. Press `prefix + Ctrl-u`, type a request, press Enter to insert the command.

## Manual install

```sh
git clone https://github.com/B00TK1D/jogger ~/.tmux/plugins/jogger
# add to ~/.tmux.conf:
run-shell ~/.tmux/plugins/jogger/jogger.tmux
tmux source-file ~/.tmux.conf
```

## Configuration

| Option | Default |
|---|---|
| `@jogger_key` | `u` |
| `@jogger_api_base` | `http://127.0.0.1:1234` |
| `@jogger_api_key` | (env `OPENAI_API_KEY`) |
| `@jogger_model` | required |
| `@jogger_debounce_ms` | `400` |
| `@jogger_timeout_seconds` | `20` |
| `@jogger_system_prompt` | built-in |
| `@jogger_max_tokens` | unset |
| `@jogger_cache_max_entries` | `1000` |
| `@jogger_cache_dir` | XDG cache |
| `@jogger_popup_width` | `60` |
| `@jogger_popup_height` | `10` |

## Keys

- `Enter`: insert current suggestion
- `Ctrl-C`: close without inserting
- `Ctrl-I`: capture currently displayed target-pane text as context
- `Ctrl-N`: regenerate (marks last command wrong; keeps appending history)
- `Up` / `Down`: cycle through previously entered requests

## Cache

Stored in `${XDG_CACHE_HOME:-$HOME/.cache}/tmux-jogger/cache.json`.
Clear with `rm -rf "${XDG_CACHE_HOME:-$HOME/.cache}/tmux-jogger"`.

## Requirements

tmux 3.2+, Python 3 (standard library only).

## Tests

```sh
python3 -m unittest discover -s tests
```
EOF
cd /root/jogger && python3 -m unittest discover -s tests >/dev/null 2>&1 && echo ok
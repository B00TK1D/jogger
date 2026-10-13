# DESIGN.md — tmux Natural-Language Command Helper

## Goal

Build a tmux plugin that turns a short natural-language description into a shell command. The user presses a configurable tmux key (default: `prefix + u`), types a request into a small prompt, sees a command suggestion update as they type, and presses Enter to insert the current suggestion into the pane that was focused when the plugin opened. The command is **typed, never executed automatically**.

## User experience

1. The user invokes the configured key binding (default `prefix + u`).
2. A compact prompt opens in a tmux popup (or the best supported equivalent). It contains:
   - A single-line or compact multi-line description input.
   - A live-generated command suggestion, with a clear loading/error state.
   - Brief key hints: `Enter: insert`, `Ctrl-C: close`, `prefix + u: close`.
3. As the description changes, request a fresh suggestion after a short debounce. Keep the most recent useful suggestion visible while a replacement is loading.
4. On Enter, if a valid suggestion exists, close the prompt and send that command as literal text to the originally captured pane, without appending Enter. The user can inspect, edit, or run it.
5. Ctrl-C or invoking the same plugin key binding again closes the prompt without inserting anything.
6. Empty input must not generate or insert a command. If no suggestion is ready, Enter should not insert stale or partial output; show a brief status and keep the prompt open.

## Architecture

Implement as a portable tmux plugin, preferably shell-based, with a small helper program for prompt state and API calls if needed. Keep responsibilities separate:

- **Plugin entry point:** installs/removes the key binding and launches the prompt.
- **Prompt UI/controller:** manages input, suggestion display, key handling, debounce, and request lifecycle.
- **API client:** calls an OpenAI-compatible Chat Completions endpoint and extracts the assistant's command.
- **Pane handoff:** captures the target pane ID at launch and inserts text into that exact pane on confirmation.

Use tmux's popup support when available (`display-popup`); document a fallback or minimum tmux version. The popup must not steal the identity of the target pane: capture `#{pane_id}` before opening it and retain it for the session.

## Configuration

Document these options and sensible defaults in the plugin's README:

- `@jogger_key` — key binding, default `u` under the tmux prefix.
- `@jogger_api_base` — OpenAI-compatible API base URL; default may target the provider's standard `/v1` base.
- `@jogger_api_key` — API key, preferably read from an environment variable such as `OPENAI_API_KEY` rather than stored in tmux config.
- `@jogger_model` — required model name.
- `@jogger_debounce_ms` — typing debounce, default around 400 ms.
- `@jogger_timeout_seconds` — request timeout.
- `@jogger_system_prompt` — optional system-prompt override.
- `@jogger_max_tokens` — optional output limit.
- `@jogger_cache_max_entries` — maximum persistent cache entries, default 1,000.
- `@jogger_cache_dir` — optional cache-directory override.
- `@jogger_popup_width` / `@jogger_popup_height` — popup sizing, with compact defaults and sensible minimums.

Allow users to configure the binding and API settings without editing plugin source. Avoid logging secrets. Fail clearly if the API key or model is missing.

## Persistent cache

- Store cache data in `${XDG_CACHE_HOME:-$HOME/.cache}/tmux-jogger/cache.json`; create the directory with user-only permissions (`0700`) and the file with `0600`. If XDG variables are unavailable, use the stated home-directory fallback.
- Use a versioned JSON structure, for example `{ "version": 1, "entries": { "<key>": { "description": "...", "command": "...", "created_at": "...", "model": "...", "api_base": "..." } } }`. This is a design example, not a required literal schema.
- Cache key must be a SHA-256 digest of the exact description after only trimming leading/trailing whitespace, plus model, API base URL, and a hash/version of the effective system prompt. Do not lowercase, rewrite, or aggressively normalize descriptions; different wording can change intent. Do not include the API key in the key or cache.
- On each edit, check the cache synchronously before starting a network request. A hit should display instantly and count as a current, valid suggestion. A miss follows the debounce/API flow.
- Cache only successful, non-empty, validated command responses. Never cache errors, loading states, or malformed output. Write atomically: write a temporary file in the same directory, flush/close it, then rename over the cache file. Handle corrupt/unreadable cache files gracefully (warn if useful, ignore and recreate); cache failure must not prevent command generation.
- Keep the cache bounded (e.g. maximum 1,000 entries) and prune oldest entries when over limit. Add a documented `@jogger_cache_max_entries` setting and optional cache-clear command or documented manual deletion path. Cache is persistent across tmux sessions and plugin restarts.
- Do not send cached descriptions or commands to any service. The cache is local. Since commands may contain sensitive paths or arguments, document where it is stored and how to clear it.
- Only insert a cache result when its cache key matches the current input and current generation settings. If a request is in flight and the user edits to a cache hit, discard any later response for the previous input.

## API behavior

Use an OpenAI-compatible `POST {base}/chat/completions` request with JSON containing `model`, `messages`, and appropriate generation parameters. Normalize the base URL so the path is not accidentally duplicated. Send the user's description as untrusted task input, not as instructions that can override the system prompt.

The system prompt must request exactly one best-effort shell command, with no Markdown fences, prose, or surrounding quotes. Tell the model to prefer commands appropriate to the current shell/OS when known, avoid destructive actions unless explicitly requested, and ask for clarification only when a safe useful command cannot be inferred. Since the plugin may not know the pane's shell, provide a configurable prompt and optionally include a small, explicitly labeled context hint; do not scrape pane history by default.

Use a normal non-streaming response for implementation simplicity, unless the chosen client architecture supports streaming robustly. “Live” means a new debounced request on input changes, not necessarily token-by-token streaming. If streaming is implemented, only publish a suggestion once it is safe to treat as a complete command. Cancel or ignore obsolete requests; responses for older input must never overwrite the suggestion for newer input.

Handle HTTP errors, timeouts, invalid JSON, missing response content, rate limits, and network failures in the UI. Keep the last successful suggestion visible on transient failure but mark it as potentially out of date; do not silently insert it for a different current input.

## Pane targeting and insertion

- Capture the focused pane ID before opening the popup.
- On confirmation, verify the pane still exists. If it no longer exists, report the error and do not send text elsewhere.
- Insert with a tmux command targeting the captured pane, such as `send-keys -t "$pane_id" -l -- "$command"` (or an equivalently safe mechanism). Do not send the Enter key.
- Treat model output as data, never as shell code to execute inside the plugin. Preserve spaces and punctuation exactly. Account for tmux command parsing and argument boundaries; do not interpolate untrusted command text into an `eval` or a constructed shell command.
- Ensure literal insertion works for commands containing quotes, semicolons, dollar signs, backticks, backslashes, Unicode, and leading hyphens.
- The popup's own input must not be sent to the target pane. Closing or cancellation must leave the target pane untouched.

## Concurrency and state

Maintain a monotonically increasing request/input revision. Each request records the revision and input that produced it. Apply a response only if both still match the current state. Debounce rapid typing and prevent overlapping requests where practical; cancellation may be best-effort, but stale responses must always be discarded. Enter is enabled only when the displayed suggestion corresponds to the current non-empty input and its request has completed successfully.

## Security and privacy

- Never execute generated commands automatically.
- Never expose API keys in popup text, logs, errors, process arguments, or debug output. Prefer environment variables or a protected config file.
- Send only the user's typed description and explicitly configured context to the API. Do not transmit pane history or environment data by default.
- Escape and validate all data passed through tmux and shell boundaries. Avoid `eval`.
- Make clear in documentation that descriptions are sent to the configured API provider.

## Repository layout and implementation sequence

Use a conventional, easy-to-understand repository layout:

```text
tmux-jogger/
  jogger.tmux             # TPM entry point; registers the configurable binding
  scripts/jogger.py       # prompt controller, cache, API client, pane handoff
  README.md              # copy-paste installation, setup, configuration, troubleshooting
  DESIGN.md
  LICENSE
  tests/                 # cache, request-race, parsing, and command-insertion tests
```

Implement in this order so each layer can be tested independently:

1. **Bootstrap and key binding:** `.tmux` entry point finds its own directory, reads tmux user options, and registers the configured key with `run-shell`. Avoid overriding a binding unless the user configured that key. Explain how to reload tmux config.
2. **Capture and popup:** capture `#{pane_id}` before opening `display-popup`; pass it to the helper as a validated argument or environment variable. Use a popup title and compact configurable dimensions. Set a minimum supported tmux version that includes `display-popup` (recommend tmux 3.2+); fail with a useful message rather than silently breaking on older versions.
3. **Input UI:** implement a small terminal UI inside the popup. Keep rendering separate from state transitions. Handle Enter, Ctrl-C, and the trigger key explicitly; ensure the trigger key can close the popup while the popup is active, using a popup-specific key handler or a documented tmux mechanism.
4. **Cache layer:** implement and test cache lookup/write/pruning before adding API calls.
5. **API layer:** implement request timeouts, error handling, response validation, and revision IDs to discard stale results.
6. **Safe insertion:** test the pane handoff with metacharacters and verify it never sends Enter.
7. **Docs and release:** test a clean install on a fresh tmux config, then write the README and tag a release only after acceptance criteria pass.

## Installation and GitHub setup

Publish as a normal GitHub repository that TPM can install. The README must start with a short description and a copy-paste quick start, and include the following:

1. **Requirements:** tmux 3.2+ (or the actual tested minimum), Python 3, and no third-party Python packages if using the standard-library approach.
2. **TPM install:** users add `set -g @plugin 'OWNER/tmux-jogger'` to `~/.tmux.conf`, add configuration and secrets as described below, ensure `run '~/.tmux/plugins/tpm/tpm'` remains at the end, reload with `tmux source-file ~/.tmux.conf`, then press `prefix + I` to install.
3. **Configuration example:** show `@jogger_api_base`, `@jogger_model`, and key binding options. Recommend setting `OPENAI_API_KEY` in the environment that starts tmux, not committing it to `.tmux.conf` or the repository. Explain that tmux server environment inheritance may mean users need `tmux set-environment -g OPENAI_API_KEY ...` or to restart the server; never print the key in diagnostics.
4. **First use:** explain the key sequence, typing, cached suggestion behavior, Enter-to-insert semantics, and cancellation.
5. **Manual install:** provide `git clone` and `run-shell` instructions for users who do not use TPM.
6. **Troubleshooting:** include checks for tmux/Python versions, missing API key/model, invalid base URL, permissions/corrupt cache, network/API errors, and key-binding conflicts.
7. **Uninstall and privacy:** explain how to remove the plugin line, uninstall via TPM, clear the local cache, and note that uncached descriptions are sent to the configured API provider.
8. **Repository hygiene:** include a license, `.gitignore` for Python bytecode and local test artifacts, and tests runnable with one documented command. Never commit API keys, real prompts, or personal cache files.

Keep setup to a few copy-paste steps; do not require users to edit plugin source or install a virtual environment.

## Compatibility and dependencies

Check dependencies at startup and show actionable errors if tmux or Python is unavailable. Keep the helper compatible with the documented Python baseline. Prefer the standard library for JSON, HTTP, hashing, file locking where available, and atomic writes. If concurrent popup instances are supported, protect cache writes with a lock or make atomic last-writer-wins behavior explicit. Provide a clean uninstall path that removes only this plugin's binding and files.

## Acceptance criteria

- The configurable default binding opens a compact prompt and captures the correct pane.
- Suggestions refresh after debounced edits; a slow response for older input never replaces a newer result.
- Enter inserts only the current successful suggestion into the pane originally focused, without executing it.
- The inserted text is exact for shell metacharacters and Unicode.
- Ctrl-C and the configured trigger key close the prompt without insertion.
- Empty input, missing configuration, API errors, timeouts, deleted panes, and missing dependencies fail safely with useful feedback.
- Re-entering the same description with unchanged generation settings prefills the last successful command immediately without an API call, including after tmux/plugin restarts.
- Cache entries are isolated by model/API base/system-prompt version; corrupt cache files do not crash the plugin, and the cache remains bounded.
- No API key or pane history is leaked, and no generated command is automatically run.
- A new user can install from the GitHub README using TPM or the documented manual method without modifying plugin source.


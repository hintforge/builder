# Build PTT for Mac or Linux -- agent prompt

> ⚠️ **UNTESTED.** This build-me prompt is on-demand, agent-driven, and has not been validated by the maintainer on Mac or Linux. The first non-Windows user who runs it produces the first port. Successful build-me runs can be contributed back into the framework as `mac/` or `linux/` tested subfolders (open a PR). Until then, expect to debug. If you don't have spare tokens to iterate, skip the voice features and use prose-only -- the framework's full guide functionality works without them.

This file is an **agent prompt**. The setup wizard invokes it when a non-Windows user opts into PTT. The agent reads it, then reads the Windows source under `windows/`, then builds an equivalent under `mac/` or `linux/` mirroring the Windows folder shape.

## Reading order (for the agent)

1. **Read `windows/README.md` first.** It's the source of truth for the module's contract: file map, prerequisites, install steps, customization knobs.
2. **Read every file under `windows/`** -- `ptt_daemon.py`, `ptt.ahk`, `start_ptt.bat`, `ptt_control.ps1`, `commands/ptt.md`. Understand each file's job before translating.
3. **Read this file** for translation guidance and known pitfalls.
4. **Detect target platform tools** on the user's machine before writing anything (e.g., `which say`, `which xdotool`, `which AutoKey`, check for Karabiner-Elements installation, check Wayland vs X11). Surface what's missing to the user before proceeding.
5. **Emit a port subfolder** named `mac/` or `linux/` at `templates/ptt/<platform>/` (or directly into the user's per-game folder if the wizard is operating in scaffold mode). Mirror the Windows structure: top-level scripts + `commands/` subfolder + a platform README.

## Source file map

The Windows module has five files. Each has a logical equivalent on Mac/Linux:

| Windows file | Job | Mac equivalent | Linux equivalent |
|---|---|---|---|
| `windows/ptt_daemon.py` | Long-running Whisper daemon. Loads `faster-whisper` once, watches flag files in `%TEMP%`. | **Same file, unchanged.** Python is portable; only the temp dir path differs (`/tmp` instead of `%TEMP%` -- already cross-platform via `tempfile.gettempdir()` if used; if hardcoded, fix). | **Same file, unchanged.** Same as Mac. |
| `windows/ptt.ahk` | AutoHotkey v2 hotkey. Holds `Numpad+`, signals daemon, pastes transcript into Claude Code. | **Karabiner-Elements JSON** (system-wide hotkey) calling a small shell script that touches the start/stop flag files; OR **Hammerspoon** Lua script (lighter weight, scriptable). | **AutoKey** (Python-scriptable, X11 + partial Wayland) OR **`xbindkeys`** + shell script (X11 only) OR a `sway`/`hyprland` keybind config snippet (Wayland). |
| `windows/start_ptt.bat` | Launcher. Starts daemon (windowless) + AHK script. Path-relative via `%~dp0`. | **`start_ptt.sh`** -- bash launcher. Use `$(dirname "$0")` for path-relative, `nohup` or `&` to background the daemon, `open -a` (or direct invocation) for the hotkey component. | **`start_ptt.sh`** -- same shape. `nohup` / `setsid` for daemon, then launch the hotkey tool. |
| `windows/ptt_control.ps1` | Status / start / stop controller. `Get-CimInstance Win32_Process` for process detection. | **`ptt_control.sh`** -- bash. Use `pgrep -f` for process detection; `kill` for stop. | **`ptt_control.sh`** -- same as Mac. |
| `windows/commands/ptt.md` | `/ptt` slash command. Calls `ptt_control.ps1` via relative path. | **Same file with two adjustments:** the example commands inside change from `.ps1` to `.sh`, and the example process names change. The Markdown shape stays identical. | Same as Mac. |

## Translation guidance

### PowerShell idioms → bash / zsh

- `Get-Content $path` → `cat "$path"` or `< "$path"`.
- `Set-Content $path $value` → `printf '%s\n' "$value" > "$path"`.
- `Test-Path $path` → `[ -e "$path" ]`.
- `Get-CimInstance Win32_Process | Where-Object { $_.Name -eq "python.exe" }` → `pgrep -f "ptt_daemon.py"`.
- `Stop-Process -Id $pid` → `kill "$pid"` (then `kill -9 "$pid"` if it ignores).
- Backticks for line continuation in PowerShell → backslash `\` in bash.
- `$env:TEMP` → `${TMPDIR:-/tmp}`.

### AHK hotkey grammar → Mac / Linux equivalents

**On Mac:**
- AHK's `*Numpad+::` (held key) → Karabiner-Elements `to_if_held_down` rule, or Hammerspoon `hs.hotkey.bind` with a long-press detector.
- AHK's `Send` (paste) → Hammerspoon `hs.eventtap.keyStrokes(text)` or shell `osascript -e 'tell application "System Events" to keystroke "..."'`.
- AHK's `WinActivate` (refocus a window) → `osascript -e 'tell application "X" to activate'` or Hammerspoon `hs.window.find(...):focus()`.
- Karabiner JSON sits at `~/.config/karabiner/karabiner.json` and requires accessibility permissions in System Settings → Privacy & Security → Accessibility.

**On Linux:**
- AutoKey (recommended): write a Python phrase that triggers on the chosen hotkey, runs the start/stop logic, then uses `keyboard.send_keys` to paste. Works on X11; Wayland support is partial / desktop-environment-specific.
- `xbindkeys` (X11 only): bind the key to a shell script in `~/.xbindkeysrc`. Use `xdotool key ctrl+v` for paste, `xdotool windowactivate` for refocus.
- Wayland: native compositor keybinds (e.g., `sway` config, `hyprland` `bind=`) calling a shell script. Pasting on Wayland often requires `wtype` instead of `xdotool`.

### Clipboard differences

| Operation | Windows | Mac | Linux X11 | Linux Wayland |
|---|---|---|---|---|
| Read clipboard | `Get-Clipboard` | `pbpaste` | `xclip -o -selection clipboard` | `wl-paste` |
| Write clipboard | `Set-Clipboard $text` | `pbcopy` | `xclip -selection clipboard` | `wl-copy` |
| Synthetic paste keystroke | AHK `Send "^v"` | `osascript -e 'tell app "System Events" to keystroke "v" using command down'` | `xdotool key ctrl+v` | `wtype -M ctrl v -m ctrl` |

The PTT flow uses synthetic paste (write to clipboard, then send Ctrl+V / Cmd+V) -- keep that pattern, just swap the tool.

## Known pitfalls

- **Audio-device permission prompts.** On macOS, the first time the Whisper daemon opens the mic, the OS shows a permission prompt. The daemon must be launched in a context where it can surface that prompt (a terminal that has Microphone access in System Settings → Privacy & Security → Microphone). On Linux, PulseAudio / PipeWire usually permits without prompting, but Flatpak'd terminals are sandboxed.
- **`chmod +x` on shell scripts.** Newly-written `.sh` files default to non-executable. The agent's port must explicitly `chmod +x start_ptt.sh ptt_control.sh` (or document it in the README) or the launcher silently fails.
- **Karabiner-Elements requires accessibility permissions.** First run prompts the user via System Settings; Karabiner won't intercept keys until the user clicks through. Document this in the install steps explicitly -- it's the #1 cause of "the hotkey does nothing."
- **Wayland vs X11 hotkey-binding differences.** On X11, `xdotool` and `xbindkeys` work everywhere. On Wayland (default on recent Fedora, GNOME 45+, Ubuntu 24.04+), they don't -- use compositor-native keybinds + `wtype`. Detect with `echo "$XDG_SESSION_TYPE"`.
- **Hardcoded `%TEMP%` in `ptt_daemon.py`.** If the Windows daemon hardcodes `os.environ["TEMP"]`, change to `tempfile.gettempdir()` for cross-platform behavior. Same for any other Windows-only path assumptions.
- **Whisper model download path.** `faster-whisper` caches the model under `~/.cache/huggingface/` on Mac/Linux. First run takes ~30s to download (~150 MB). Tell the user this so they don't think the script is hung.
- **AHK's window-match is Win32 HWND-based.** The Mac/Linux ports identify the Claude Code window differently -- by app bundle ID on Mac, by `WM_CLASS` or window title on Linux. Pull the current window match logic from `ptt.ahk`'s `CLAUDE_MATCHES` array and translate.

## Verification checklist (run after the agent finishes building)

The user runs these manual tests to confirm the port works. Each step should succeed before moving on.

1. **Daemon starts cleanly.** Run `./start_ptt.sh` (or the platform equivalent). The daemon process should be visible in `ps aux | grep ptt_daemon` (or Activity Monitor / `htop`). No tracebacks in the terminal output.
2. **Whisper model loads.** First run downloads the model (~30s). Subsequent runs should print "model loaded" within ~5 seconds.
3. **Hotkey is registered.** In a non-Claude window (e.g., a text editor), press and hold the configured hotkey. Nothing should happen there (the hotkey only fires when Claude Code is focused), but verify there's no error in the hotkey-tool's log.
4. **Trigger PTT, speak, see expected output.** Focus the Claude Code window. Hold the hotkey, say "hello world" out loud, release. Within ~1-2 seconds, the text "hello world" (or close to it) should appear in the Claude Code input box, followed by Enter.
5. **Window refocus.** After the paste, the previously-focused window (e.g., the game) should regain focus automatically. If it doesn't, the window-match logic needs adjustment.
6. **Status / stop work.** Run `./ptt_control.sh status` -- should report "running" and show the PID. Run `./ptt_control.sh stop` -- should kill the daemon and the hotkey listener cleanly. Re-run `status` to confirm stopped.
7. **Restart cycle.** Stop, then start again. Should work identically without manual cleanup of stale flag files or pid files.

If any step fails, capture the error and iterate with the agent -- that's the "expect to debug" tax flagged at the top of this file.

## Promoting a successful port back into the framework

If the user's port works end-to-end, the maintainer can promote `<user>/<game>/ptt/` (or wherever the port landed) into `templates/ptt/mac/` or `templates/ptt/linux/`. That removes the "untested" disclaimer for that platform on the next framework release.

The promotion criteria: clean install on a fresh machine of the same platform + all 7 verification steps pass + no platform-specific assumptions about the user's setup beyond what the README documents.

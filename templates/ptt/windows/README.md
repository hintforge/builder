# PTT (Push-to-Talk) Module -- opt-in

> ⚠️ **AutoHotkey v2 required.** This template will not run on AHK v1 -- `ptt.ahk` opens with `#Requires AutoHotkey v2.0` and v1 will reject it with a parse error before doing anything. If you have AHK v1 installed, uninstall it (or install v2 alongside it via the v2 installer) before proceeding. Download v2 at [autohotkey.com/v2](https://www.autohotkey.com/v2/).

A long-running Whisper daemon + AutoHotkey hotkey that lets you hold **Numpad+** to talk into Claude Code instead of typing. Spoken text gets transcribed locally (no cloud upload), pasted into the active Claude Code window, and Enter is pressed. The previously-focused window (e.g. the game) gets refocused automatically afterward.

Pairs naturally with the **TTS module** (`../tts/`) for full voice in + voice out.

## What's in this template

| File | Where it goes in a per-game folder | Purpose |
|---|---|---|
| `ptt_daemon.py` | `<game>/ptt/ptt_daemon.py` | Long-running daemon. Loads `faster-whisper` once, watches flag files in `%TEMP%`. |
| `ptt.ahk` | `<game>/ptt/ptt.ahk` | AutoHotkey v2 hotkey. Holds `Numpad+`, signals daemon, pastes transcript into Claude Code. |
| `start_ptt.bat` | `<game>/ptt/start_ptt.bat` | Launcher. Starts both daemon (windowless) + AHK script. Path-relative via `%~dp0`. |
| `ptt_control.ps1` | `<game>/.claude/ptt_control.ps1` | Status / start / stop controller. Self-resolves its own path; safe to move. |
| `commands/ptt.md` | `<game>/.claude/commands/ptt.md` | `/ptt` slash command for Claude Code. Calls `ptt_control.ps1` via relative path. |

## Prerequisites (Windows; the only verified-running OS today)

- **Python 3.10+** with these packages:
  - `faster-whisper` (Whisper model + transcription)
  - `sounddevice` (mic capture)
  - `numpy` (audio buffer math)
- **AutoHotkey v2** (NOT v1) -- [autohotkey.com/v2](https://www.autohotkey.com/v2/). Required for the hotkey layer; v1 will fail to parse `ptt.ahk`.

First daemon run downloads the `small.en` Whisper model (~244 MB). This happens transparently on first start.

## Installation (manual)

1. Copy the five files into the per-game folder per the table above. If you've never run AHK v2 before, double-click `ptt.ahk` once standalone -- if you see a v1-vs-v2 mismatch error, you have v1 installed and need v2.
2. From the per-game folder, run `.claude/ptt_control.ps1 start` (or use `/ptt` in Claude Code if you've also installed `commands/ptt.md`).
3. Wait ~30s on first run for the model download. The script polls a ready-flag and tells you when it's done.
4. Hold `Numpad+` and speak. Release to transcribe + paste.

## Installation (via the wizard)

The setup wizard (Step 6.5) can scaffold this for you on opt-in. See `../optional_modules.md` for the opt-in flow.

## What's portable, what's not

- **Whisper daemon** (`ptt_daemon.py`): cross-platform Python. Works on Linux/Mac with the same package set; just need a different launcher than `.bat`.
- **AHK hotkey** (`ptt.ahk`): Windows-only. Mac/Linux equivalents exist (`Hammerspoon` on macOS; `xdotool` on Linux X11; nothing clean on Wayland) but aren't templated yet.
- **`.bat` launcher**: Windows-only. A `.sh` equivalent is trivial; just hasn't been written.
- **`.ps1` controller**: Windows-only. Process detection (`Get-CimInstance Win32_Process`) is Win32-specific.

Cross-platform launchers are on the framework roadmap.

## Customization knobs

- **Hotkey:** the default `Numpad+` is a niche choice -- it only works on full-size keyboards. **Open `ptt.ahk` and change the `PTT_HOTKEY := "NumpadAdd"` line near the top** to whatever key you actually want to hold.
  - **Known-good keys** (verified to work with AHK v2 + this template): `NumpadAdd`, `CapsLock`, `F13`-`F24`, `ScrollLock`, `RAlt`, `AppsKey`, `MButton`, `XButton1`, `XButton2`.
  - **Anything else:** valid in principle but unverified by us. AHK v2 supports a much larger key list at [autohotkey.com/docs/v2/KeyList.htm](https://www.autohotkey.com/docs/v2/KeyList.htm) -- if your choice isn't in the known-good list above and AHK fails to parse on first run, you'll get a clear error pointing at the offending line.
  - **Avoid:** keys you use in-game; bare modifier keys (Ctrl/Alt/Shift/Win -- they break combos); regular letters/numbers (you'll trigger PTT every time you type).
- **Whisper model:** `ptt_daemon.py` uses `small.en` (English-only, ~244 MB, ~1.5-2 s transcription). Swap to `base.en` for faster but lower-quality results, or `large-v3` for max accuracy if you have a GPU.
- **Window match:** `ptt.ahk` line `CLAUDE_MATCHES := [...]` controls which window gets the paste. Default matches Claude Code Desktop. Adjust if you've renamed the executable or use a different Claude variant.

## Token cost honesty (Principle #13)

Setting up PTT manually is **0 token cost** -- it's all local Python + AHK, no Claude messages. The slash command (`/ptt`) is Claude-driven but only fires on user invocation; it doesn't increase token usage during normal play.

The wizard's PTT-opt-in path costs ~3-5 messages (copy files, install Python deps if missing, verify daemon launches). Cheaper than the original 30-60-message rebuild-from-scratch path that the in-tree reference impl required.

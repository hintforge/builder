# Optional Modules

Three opt-in modules extend the core with voice in, voice out, and live game-state awareness. All **off by default**.

| Module | Folder | What it does | Setup cost (token) | OS support |
|---|---|---|---|---|
| **PTT** (push-to-talk) | [`ptt/`](ptt/) | Hold Numpad+ to talk into Claude Code via local Whisper transcription | 0 manual / ~3-5 wizard | Windows tested + maintained (`ptt/windows/`); Mac/Linux experimental via `ptt/_build_for_other_platforms.md` (untested agent build) |
| **TTS** (read-aloud) | [`tts/`](tts/) | Stop hook speaks each Claude reply through your speakers in a persona-aware voice via edge-tts | 0 manual / ~3-5 wizard | Windows tested + maintained (`tts/windows/`); Mac/Linux experimental via `tts/_build_for_other_platforms.md` (untested agent build) |
| **save-watcher** | [`save_watcher/`](save_watcher/) | Reads game's save file at session start to populate location/inventory/state into Claude's context | 0 manual *if format known* / 10-30 wizard | Cross-platform Python; per-game parser required |

## Hard rules for all optional modules

1. **Off by default.** A guide instantiated from the standard templates must work fully without any module. Modules add ergonomics; they never gate functionality.
2. **OS-quarantined.** Each module declares its supported OS list. PTT and TTS ship a tested Windows tier (PowerShell + AHK + WPF MediaPlayer / SAPI / edge-tts dependencies, in `ptt/windows/` and `tts/windows/`); Mac and Linux ports are agent-built on demand from `_build_for_other_platforms.md` and carry an untested-disclaimer until promoted back into the framework as `mac/` / `linux/` subfolders. save-watcher is cross-platform Python but the per-game parser is the user's job.
3. **Self-contained.** A module's files live in known locations within `<game>/` (per the module's README). Removing those files removes the module cleanly.
4. **Prereqs documented up front.** Each module's README lists every dependency (system installs, Python packages, model downloads with sizes) before the user touches anything.
5. **Token-cost honest.** Per Principle #13, every module's README states real token cost -- manual install vs. wizard-assisted, normal-use cost vs. setup cost.
6. **Transparent operations.** Per Principle #12 / Hard Rule #6, no covert behavior, no telemetry, no out-of-scope writes. Local processes only. The only network call any module makes is TTS's call to Microsoft's Edge TTS endpoint (documented in `tts/README.md`).

## Wizard opt-in flow

The setup wizard's relevant steps:

- **Step 3** asks about save-watcher. Default: skip. If the user opts in, the wizard copies `save_watcher/skeleton.py` to `<game>/save_watcher.py` and walks the user through filling in the parsing logic. Long path; defaults to skip on Pro tier.
- **Step 6** asks about TTS. Default: skip. If the user opts in on Windows, the wizard copies `tts/windows/` files into `<game>/.claude/`, adds the per-game folder to `~/.claude/tts_game_folders.txt`, and asks for persona → voice mappings (writes `<game>/tts_voices.txt`). On Mac/Linux, the wizard invokes `tts/_build_for_other_platforms.md` as an agent prompt and surfaces the untested-disclaimer before proceeding.
- **Step 6.5** asks about PTT. Default: skip. If the user opts in on Windows, the wizard copies `ptt/windows/` files into `<game>/ptt/` and `<game>/.claude/`, runs the prereq check (Python + faster-whisper + sounddevice + AHK v2), and offers to install missing packages. On Mac/Linux, the wizard invokes `ptt/_build_for_other_platforms.md` as an agent prompt and surfaces the untested-disclaimer before proceeding.

A guide can have any combination installed -- none, one, two, or all three. PTT and TTS pair particularly well (voice in + voice out → hands-free game companion).

## Why these three, why now

These three emerged from a fully-equipped reference guide built during framework development -- PTT for voice in, TTS for voice out, save-watcher for live state. Templates capture the working patterns so new guides don't rebuild from scratch.

Future module candidates (see `../distribution.md`):
- **Screenshot-by-command** (`/screenshot` slash command + vision model interpretation of focused-window capture)
- **Cross-platform TTS** (macOS `say` + Linux `piper` variants of the Stop hook)
- **GPU Whisper** (PTT module variant for users with CUDA, faster transcription)

These are not yet templated. Add to this catalog when promoted.

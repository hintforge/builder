# PTT (Push-to-Talk) Module -- opt-in

A long-running Whisper daemon + a hotkey daemon that lets you hold a key to talk into Claude Code instead of typing. Spoken text is transcribed locally (no cloud upload), pasted into the active Claude Code window, and Enter is pressed. The previously-focused window (e.g. the game) gets refocused automatically afterward.

Pairs naturally with the **TTS module** (`../tts/`) for full voice in + voice out.

## Supported platforms

| Platform | Status | Where to look |
|---|---|---|
| **Windows 10/11** | Tested + maintained by the framework. | [`windows/`](windows/) -- full install steps, files, customization. |
| **macOS / Linux** | **Experimental, untested.** Built on demand by an agent from the Windows source. | [`_build_for_other_platforms.md`](_build_for_other_platforms.md) -- agent prompt the wizard invokes for non-Windows users. |

## Hardline requirements (Windows)

Check these before starting setup. PTT will not run without all three.

- **Windows 10 or 11.** The PowerShell controller and AHK hotkey layer are Win32-specific.
- **Python 3.10+**, with `faster-whisper`, `sounddevice`, and `numpy` installable via pip.
- **AutoHotkey v2** (NOT v1). Download at [autohotkey.com/v2](https://www.autohotkey.com/v2/). If you have v1 installed, AHK will refuse to parse `ptt.ahk` -- install v2 alongside or in place of v1.

## Install steps (Windows)

The full Windows install lives in [`windows/README.md`](windows/README.md). Quick summary:

1. Read [`windows/README.md`](windows/README.md) for the file map (which file goes where in a per-game folder) and prerequisite install commands.
2. Copy the five files from `windows/` into the per-game folder per the table in that README.
3. From the per-game folder, run `.claude/ptt_control.ps1 start` (or `/ptt` in Claude Code if you've installed `commands/ptt.md`).
4. Wait ~30s on first run for the Whisper model download (~150 MB).
5. Hold `Numpad+` (the default hotkey -- customizable) and speak. Release to transcribe and paste.

The setup wizard's PTT-opt-in step (Step 6.5) can scaffold all of this automatically. See `../optional_modules.md`.

## Other platforms

> ⚠️ **UNTESTED.** This build-me prompt is on-demand, agent-driven, and has not been validated by the maintainer on Mac or Linux. The first non-Windows user who runs it produces the first port. Successful build-me runs can be contributed back into the framework as `mac/` or `linux/` tested subfolders (open a PR). Until then, expect to debug. If you don't have spare tokens to iterate, skip the voice features and use prose-only -- the framework's full guide functionality works without them.

If you're on macOS or Linux and want PTT anyway, the agent can build a port for you on demand. See [`_build_for_other_platforms.md`](_build_for_other_platforms.md). The wizard invokes this automatically when a non-Windows user opts into voice features.

The reading order the agent follows: (1) the canonical Windows source under `windows/`, (2) the build-me prompt, (3) target-platform tools (`say`, `espeak`, AutoKey, Karabiner, etc.), (4) emit a `mac/` or `linux/` subfolder mirroring the Windows structure.

## Token cost honesty (Principle #13)

Setting up PTT manually on Windows is **0 token cost** -- it's all local Python + AHK, no Claude messages.

The wizard's Windows PTT-opt-in path costs ~3-5 messages (copy files, install Python deps if missing, verify the daemon launches).

The non-Windows build-me path costs more -- the agent has to read the Windows source, translate idioms, write a port, and walk you through verification. Budget ~20-40 messages for a first run, plus debugging cycles. Use prose-only if your token budget is tight.

# TTS (Text-to-Speech / Read-Aloud) Module -- opt-in

Stop-hook based TTS that speaks each Claude Code reply through your speakers in a persona-aware voice. Pairs naturally with the **PTT module** (`../ptt/`) for full voice in + voice out.

## Supported platforms

| Platform | Status | Where to look |
|---|---|---|
| **Windows 10/11** | Tested + maintained by the framework. | [`windows/`](windows/) -- full install steps, files, voice list, persona detection. |
| **macOS / Linux** | **Experimental, untested.** Built on demand by an agent from the Windows source. | [`_build_for_other_platforms.md`](_build_for_other_platforms.md) -- agent prompt the wizard invokes for non-Windows users. |

## Hardline requirements (Windows)

Check these before starting setup. TTS will not run without all three.

- **Windows 10 or 11.** The Stop hook is a PowerShell script using WPF MediaPlayer for playback.
- **PowerShell** (built-in on Windows; no separate install).
- **SAPI / `edge-tts` voices.** The hook synthesizes through `edge-tts` (Microsoft's free neural endpoint, no API key) and falls back to SAPI voices if needed. Install via `pip install edge-tts` (requires Python 3.10+).

## Install steps (Windows)

The full Windows install lives in [`windows/README.md`](windows/README.md). Quick summary:

1. Read [`windows/README.md`](windows/README.md) for the file map (which file goes where in a per-game folder) and prerequisite install commands.
2. Copy the five files from `windows/` into the per-game folder per the table in that README.
3. Add the per-game folder's absolute path to `~/.claude/tts_game_folders.txt` (the allowlist the Stop hook checks before speaking).
4. Edit `<game>/tts_voices.txt` to map your game's persona names to `edge-tts` voice IDs.
5. Restart Claude Code (the Stop hook is loaded at session start).
6. Ask Claude anything in the per-game folder. The reply should be spoken aloud. Toggle with `/voice`.

The setup wizard's TTS-opt-in step (Step 6) can scaffold all of this automatically. See `../optional_modules.md`.

## Other platforms

> ⚠️ **UNTESTED.** This build-me prompt is on-demand, agent-driven, and has not been validated by the maintainer on Mac or Linux. The first non-Windows user who runs it produces the first port. Successful build-me runs can be contributed back into the framework as `mac/` or `linux/` tested subfolders (open a PR). Until then, expect to debug. If you don't have spare tokens to iterate, skip the voice features and use prose-only -- the framework's full guide functionality works without them.

If you're on macOS or Linux and want TTS anyway, the agent can build a port for you on demand. See [`_build_for_other_platforms.md`](_build_for_other_platforms.md). The wizard invokes this automatically when a non-Windows user opts into voice features.

The reading order the agent follows: (1) the canonical Windows source under `windows/`, (2) the build-me prompt, (3) target-platform tools (`say` on Mac, `espeak` / `piper` on Linux, etc.), (4) emit a `mac/` or `linux/` subfolder mirroring the Windows structure.

## Token cost honesty (Principle #13)

Setting up TTS manually on Windows is **0 token cost** -- install once, runs locally on every assistant turn end. No per-message Claude charges.

The wizard's Windows TTS-opt-in path costs ~3-5 messages (copy files, install `edge-tts`, register in allowlist, verify the hook fires).

The non-Windows build-me path costs more -- the agent has to read the Windows source, translate idioms, write a port, and walk you through verification. Budget ~20-40 messages for a first run, plus debugging cycles. Use prose-only if your token budget is tight.

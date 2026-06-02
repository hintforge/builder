# TTS (Text-to-Speech / Read-Aloud) Module -- opt-in

Stop-hook based TTS that speaks each Claude Code reply through your speakers in a persona-aware voice. Pairs naturally with the **PTT module** (`../ptt/`) for full voice in + voice out.

## What's in this template

| File | Where it goes in a per-game folder | Purpose |
|---|---|---|
| `tts_hook.ps1` | `<game>/.claude/tts_hook.ps1` | Stop hook. Reads transcript, strips markdown, synthesizes via `edge-tts`, plays MP3. Path-guards against running outside allowlisted game folders. |
| `toggle_tts.ps1` | `<game>/.claude/toggle_tts.ps1` | Toggle script for `/voice`. Self-resolves its own path; safe to move. |
| `tts_voices.txt` | `<game>/tts_voices.txt` | Persona → voice mapping. Edit per game. |
| `commands/voice.md` | `<game>/.claude/commands/voice.md` | `/voice` slash command. |
| `settings.json` | `<game>/.claude/settings.json` | Claude Code settings to register the Stop hook. If `<game>/.claude/settings.json` already exists, **merge** (don't overwrite); the hook block goes under the `hooks` key. |

## Prerequisites (Windows)

- **Python 3.10+** with the `edge-tts` package: `pip install edge-tts`
- **PowerShell** (built-in on Windows)

Edge-TTS uses Microsoft's free neural voices via a public endpoint -- no API key, no cloud account.

## Installation (manual)

1. Copy the five files into the per-game folder per the table above.
2. Add the per-game folder's absolute path to `~/.claude/tts_game_folders.txt` (one per line). Create the file if it doesn't exist. Example:
   ```
   C:\Users\me\Documents\Claude\Guides\my_game
   ```
   This is the allowlist the Stop hook checks before speaking. Without this entry, the hook silently no-ops.
   **While you're in this file, sweep for stale entries.** Any path here that no longer exists on disk (renamed, moved, deleted guide) should be removed in the same edit -- confirm with the user before deleting, but don't leave broken entries in place. The allowlist is shared cross-game state; reconciling it with reality is part of touching it.
3. Edit `<game>/tts_voices.txt` to map your game's persona names to edge-tts voice IDs. The default `en-US-AvaNeural` is used when no mapping matches.
4. Restart Claude Code (the Stop hook is loaded at session start).
5. Ask Claude anything in the per-game folder. The reply should be spoken aloud.
6. Toggle off with `/voice` if you need silence; same command toggles back on.

## Installation (via the wizard)

The setup wizard's Step 6 (TTS opt-in) can scaffold this for you. See `../optional_modules.md` for the opt-in flow.

## How persona detection works

The hook reads `<game>/persona.md` looking for the line:

```
## Current active persona

**PersonaName**
```

It extracts `PersonaName` and looks up the corresponding voice in `<game>/tts_voices.txt`. The persona.md format is set by the framework's persona template -- if you keep that template, persona switching automatically swaps voices.

## Listing available voices

```
python -m edge_tts --list-voices
```

Returns a JSON list of every voice (name, locale, gender, description). Pick voices that match your game's personas. Recommended starting picks:

| Voice ID | Description |
|---|---|
| `en-US-AvaNeural` | US English female, neutral, "Copilot" voice (Microsoft default) |
| `en-US-AndrewNeural` | US English male, warm |
| `en-GB-RyanNeural` | UK English male, measured |
| `en-GB-SoniaNeural` | UK English female |
| `en-AU-NatashaNeural` | Australian English female |

## What's portable, what's not

- **Stop hook + persona-aware voice selection:** the *pattern* is portable; the implementation is Windows-only via PowerShell + WPF MediaPlayer.
- **Mac:** `say` is the equivalent built-in TTS; doesn't have direct edge-tts integration but can be wrapped similarly. Not yet templated.
- **Linux:** `espeak` (basic) or `piper` (neural, local). Not yet templated.

Cross-platform TTS is on the framework roadmap.

## Token cost honesty (Principle #13)

Setting up TTS manually is **0 token cost** -- install once, runs locally on every assistant turn end. No per-message Claude charges.

The wizard's TTS-opt-in path costs ~3-5 messages (copy files, install `edge-tts`, register in allowlist, verify the hook fires). Cheaper than the original 30-60-message build-from-scratch path.

## Known sharp edges

- **Stop hook needs a fresh session start.** Claude Code reads `.claude/settings.json` once at session start. If you `/resume` an old session, the hook won't be active -- start a new chat instead. (This is also why we recommend registering the hook in `~/.claude/settings.json` globally rather than per-game `<game>/.claude/settings.json`: the global registration survives `/resume` reliably, and the path-guard in `tts_hook.ps1` keeps it from speaking outside game folders. The framework's `windows/settings.json` template ships as a project-level example, but for daily-driver use, global is more reliable.)
- **Schema gotcha (silent failure).** The hooks JSON schema only accepts `type`, `command`, `timeout`, `statusMessage`, `once`. Fields like `shell: "powershell"` and `async: true` look reasonable but are silently dropped; `command` must contain the full shell invocation, e.g. `powershell -NoProfile -ExecutionPolicy Bypass -File "..."`. Don't write `command: "& '...\\script.ps1'"` -- cmd.exe doesn't understand `&` and the hook will silently fail with no log entries.
- **The hook is global.** It fires on every assistant turn in every project, but path-guards itself to allowlisted folders. The path-guard is the security boundary; do not remove it.
- **Long replies speak the first line only.** Replies over 300 characters are truncated to the first non-empty line -- voice is meant as a quick lead-in, not a recital. Adjust the cutoff in `tts_hook.ps1` if you prefer different behavior.
- **Speech is preempted on new replies.** If Claude answers a follow-up before the previous reply finishes speaking, the in-progress speech is killed. Look for `tts_hook.pid` in the per-game `.claude/` to track this.
- **PTT cuts off TTS.** If the PTT module is also installed, pressing the PTT key immediately kills any active TTS playback before recording starts. This prevents the mic from picking up TTS audio and lets you interrupt long speech. The hook writes its PID to `%TEMP%\tts_active.pid` for this purpose.
- **Persona-output rules tighten when TTS is on.** Onomatopoeia and em dashes in written text both speak badly through neural voices. The persona template's "When TTS is on" section spells out the two constraints -- see `../../persona.md`. The bot detects TTS state by checking for this hook script + the `tts_disabled.flag` file.

---
description: Start, stop, toggle, or check the TTS voice for this session
allowed-tools: Bash, PowerShell
argument-hint: [start|stop|toggle|status]
---

Run this command via the **Bash tool** (the PowerShell tool has been observed to fail silently with exit 1 and no output -- Bash is the reliable path):

```
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".claude/voice_control.ps1" -Action "$ARGUMENTS"
```

Report the script's stdout to the user verbatim in one short sentence -- do not speak in persona, do not add commentary.

If `$ARGUMENTS` is empty, the script defaults to `toggle` (the historical /voice behavior). Valid values: `start`, `stop`, `toggle`, `status`. The script is idempotent -- `/voice start` when already on returns "Voice already on" without side effects (except silencing any in-progress speech, which is always done so /voice doubles as a "shut up now" button).

**TTS firing is independent of this command.** The TTS Stop hook is registered globally in `~/.claude/settings.json` and fires on every assistant turn unless `.claude/tts_disabled.flag` exists in the game folder. A failed `/voice` invocation tells you nothing about whether speech will play -- speech may still work even if the toggle command errors. Do NOT tell the user "TTS is not running" based on a tool failure. To actually check whether TTS will fire, use `/voice status` or look at `test -f .claude/tts_disabled.flag` (present = disabled, absent = enabled).

**Do not infer state from a tool failure.** If the command returns no output or a non-zero exit, do NOT tell the user "voice is off" or "the script doesn't exist." Tool failures are not authoritative -- only the script's own stdout is. On failure: say "the script invocation failed" and probe with `pwd` and `test -f .claude/voice_control.ps1` to diagnose.

> **Path note:** the relative path `.claude/voice_control.ps1` resolves against the Claude Code session's current working directory, which should be the per-game folder. If `test -f` confirms the script is missing, verify the session is opened in `Guides/<game>/`, not somewhere else.

---
description: Start, stop, restart, or check the push-to-talk daemon (Numpad+ to talk into Claude Code)
allowed-tools: Bash, PowerShell
argument-hint: [start|stop|restart|status]
---

Run this command via the **Bash tool** (the PowerShell tool has been observed to fail silently with exit 1 and no output -- Bash is the reliable path):

```
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".claude/ptt_control.ps1" -Action "$ARGUMENTS"
```

Report the script's stdout to the user verbatim in one short sentence -- do not speak in persona, do not add commentary.

If `$ARGUMENTS` is empty, the script defaults to `start`. Valid values: `start`, `stop`, `restart`, `status`. The script is idempotent -- running `/ptt` twice in a row will not double-launch the daemon. Use `/ptt restart` when the AHK file has changed and you need hotkeys re-registered against the new code.

**Do not infer state from a tool failure.** If the command returns no output or a non-zero exit, do NOT tell the user "PTT is not running" or "the script doesn't exist." Tool failures are not authoritative -- only the script's own stdout is. On failure: say "the script invocation failed" and probe with `pwd` and `test -f .claude/ptt_control.ps1` to diagnose whether it's a cwd issue or a real missing file.

> **Path note:** the relative path `.claude/ptt_control.ps1` resolves against the Claude Code session's current working directory, which should be the per-game folder. If `test -f` confirms the script is missing, verify the session is opened in `Guides/<game>/`, not somewhere else.

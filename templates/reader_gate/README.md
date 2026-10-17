# Reader safeguard (reader gate)

An optional hook for a guide folder. Without the reader skill loaded, an AI can answer from the guide's files with no spoiler rules. The gate makes it load the skill first. Setup offers it at Step 6.6 (default yes); a player can also ask the builder to add it to an existing guide.

## What it does

- **Blocks** the first read of this guide's files in a session when no hintforge skill (the reader, or the builder for maintenance) has loaded yet. The AI gets a message telling it to load the matching skill.
- **Never blocks** `CLAUDE.md`, `AGENTS.md`, `README.md` or `DISCLAIMER.md`, files outside the guide, or anything after a hintforge skill has loaded.
- **Blocks once.** The second attempt in the same session goes through, so a session where the skill truly cannot load still works.
- **Fails open.** Any error, or a machine that cannot run the script, lets the call through. A shared guide never stops someone else's session.

Deny message (the last two sentences matter: deciding a task "isn't a hintforge task" is not a way past it):

> HINTFORGE GATE: this is a hintforge guide folder and no hintforge skill has loaded this session. Do not answer a game question or change the guide from a direct file read. FIRST load the hintforge skill that matches the task -- hintforge-reader for play help, or the hintforge builder for guide maintenance (doctor, ingestion, stitch, fixing or updating the guide) -- then proceed. If the Skill tool reports that no hintforge skill is installed, re-issue this call to proceed. Deciding that this task is not a hintforge task is not a reason to skip: any read of this guide's files needs the matching skill first.

## Files

| Template file | Goes to | Notes |
|---|---|---|
| `claude-code/reader_gate.ps1` | `<game>/.claude/reader_gate.ps1` | Reference implementation (Windows PowerShell). |
| `claude-code/settings.json` | merged into `<game>/.claude/settings.json` | Registers the PreToolUse hook. Merge, never overwrite. |
| `claude-code/reader_gate.ps1` | `<game>/.codex/reader_gate.ps1` | Same script for Codex. |
| `codex/hooks.json` | merged into `<game>/.codex/hooks.json` | Codex reads files through its shell tool, so the hook matches `Bash`. Codex loads project hooks only after the folder is trusted, and asks the player to review a new hook. **Untested on Codex.** |
| `self_test.ps1` | not copied | Run once after install; see below. |
| `_build_for_your_setup.md` | not copied | Agent prompt for building the gate on another runtime or shell. |

## Self-test (required before reporting it built)

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File <builder>/templates/reader_gate/self_test.ps1 -Gate <game>/.claude/reader_gate.ps1
```

Add `-Tool Bash` for the Codex copy. Ten checks: the first guide read is blocked with the message above; the second is allowed; a session with a hintforge skill loaded is allowed; a shim read is allowed; a read outside the guide is allowed; a session where only the player's message names a hintforge `SKILL.md` is still blocked; a session whose transcript records a tool call reading that file is allowed; a session where the AI's own text names that file beside an unrelated tool call is still blocked; a session whose shell calls only echo the path is still blocked; a session whose transcript records a Codex shell call reading that file is allowed.

Only a recorded tool call counts as loading the skill: a `Skill` call naming `hintforge` or `hintforge-reader`, a `Read` of a hintforge `SKILL.md`, or a Codex shell call whose command reads that file (`cat`, `Get-Content` and the like). The gate parses each transcript line rather than searching it for the path. If any check fails, remove the registration and report the gate as not built.

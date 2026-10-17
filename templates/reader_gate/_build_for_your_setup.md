# Build the reader safeguard for this player's setup -- agent prompt

This file is an **agent prompt**. Setup Step 6.6 runs it when the player says yes to the reader safeguard; a player can also ask for it in an existing guide folder. You are building a hook that makes the AI load the hintforge reader before it reads the guide's files. Build it for the runtime and shell this player actually uses, prove it with the self-test, and report the result in one line.

## Reading order

1. `README.md` in this folder: the gate's contract and the deny message. Every port keeps both exactly.
2. `claude-code/reader_gate.ps1`: the reference implementation. Understand each branch (read tools, shell reads, shim files, guide-root check, satisfied-if, block-once, fail-open) before translating anything.
3. `claude-code/settings.json` and `codex/hooks.json`: the registration shapes.

## 1. Detect the runtime

- **Claude Code** (you have a `Skill` tool and `.claude/` settings): registration file `<game>/.claude/settings.json`.
- **Codex** (skills load from `.agents/skills/`, hooks from `.codex/hooks.json`): registration file `<game>/.codex/hooks.json`. Codex reads files through its shell tool; match `Bash`. Codex loads a project hook only after the folder is trusted and the player reviews the hook; tell the player that once.
- **Anything else** (no PreToolUse-style hook the folder can register): record `unsupported`, tell the player in one line that their tool has no way to run the safeguard, and continue setup. Do not invent a hook format.

## 2. Detect the shell

Check what can run the script on this machine: `powershell` (Windows PowerShell, on every Windows PC), `pwsh` (PowerShell 7, any OS), or `bash` / `zsh`.

- **Windows, any runtime:** copy `claude-code/reader_gate.ps1` unchanged. No translation.
- **`pwsh` on Mac or Linux:** copy the script unchanged and change the registration command from `powershell` to `pwsh`.
- **Only `bash` / `zsh`:** translate the script to `reader_gate.sh`, keeping every branch and the deny message word for word. Read the JSON payload from stdin (`jq` if present; otherwise a small `python3 -c` reader if Python exists; if neither exists, record `unsupported`). Write the deny message to stderr and exit 2; exit 0 everywhere else, including on any error.

## 3. Install

- Write the script to `<game>/.claude/reader_gate.<ext>` (Claude Code) or `<game>/.codex/reader_gate.<ext>` (Codex).
- **Merge the registration, never overwrite.** If the settings or hooks file exists, add the PreToolUse entry beside the existing ones and keep everything else byte-for-byte. If an identical gate entry is already there, do not add a second one.

## 4. Self-test (required)

Windows or `pwsh`: run `self_test.ps1` from this folder against the installed script (`-Tool Bash` for a Codex install) and show its output to the player. For a `.sh` port, run the same seven checks by piping the same payloads into the script yourself:

1. first read of `<game>/CHECKPOINT.md`, empty transcript -> exit 2 and the deny message;
2. the same call again in the same session -> exit 0;
3. a new session whose transcript contains a hintforge `Skill` call -> exit 0;
4. a read of `<game>/README.md` -> exit 0;
5. a read of a file outside the guide -> exit 0;
6. a new session whose only mention of a hintforge `SKILL.md` path is in the player's message -> exit 2 (naming the skill is not loading it);
7. a new session whose transcript records a tool call that read a hintforge `SKILL.md` -> exit 0.

Delete the test's block-once flags and temporary transcripts afterward.

**If any check fails:** remove the registration entry you added (leave the rest of the file as it was), delete the script, record `unsupported`, and tell the player in one line that the safeguard could not be built on this machine. A guide never ships a gate nobody has seen work.

## 5. Record

Set `[READER_GATE]` to `built-claude-code`, `built-codex`, `built-other` (a working port on another hook-capable runtime), `unsupported`, or `skipped`. Tell the player in plain words what was added and where, and that the safeguard only nudges the AI to load the reader; it never stops their own use of the files.

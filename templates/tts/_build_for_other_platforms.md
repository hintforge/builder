# Build TTS for Mac or Linux -- agent prompt

> ⚠️ **UNTESTED.** This build-me prompt is on-demand, agent-driven, and has not been validated by the maintainer on Mac or Linux. The first non-Windows user who runs it produces the first port. Successful build-me runs can be contributed back into the framework as `mac/` or `linux/` tested subfolders (open a PR). Until then, expect to debug. If you don't have spare tokens to iterate, skip the voice features and use prose-only -- the framework's full guide functionality works without them.

This file is an **agent prompt**. The setup wizard invokes it when a non-Windows user opts into TTS. The agent reads it, then reads the Windows source under `windows/`, then builds an equivalent under `mac/` or `linux/` mirroring the Windows folder shape.

## Reading order (for the agent)

1. **Read `windows/README.md` first.** It's the source of truth for the module's contract: file map, prerequisites, install steps, persona detection, voice-list mechanics.
2. **Read every file under `windows/`** -- `tts_hook.ps1`, `toggle_tts.ps1`, `tts_voices.txt`, `commands/voice.md`, `settings.json`. Understand each file's job before translating.
3. **Read this file** for translation guidance and known pitfalls.
4. **Detect target platform tools** on the user's machine before writing anything (e.g., `which say`, `which espeak`, `which piper`, check that `edge-tts` Python package is installable, confirm an audio output device exists). Surface what's missing to the user before proceeding.
5. **Emit a port subfolder** named `mac/` or `linux/` at `templates/tts/<platform>/` (or directly into the user's per-game folder if the wizard is operating in scaffold mode). Mirror the Windows structure: hook script + toggle script + voices file + `commands/` subfolder + `settings.json` + a platform README.

## Source file map

The Windows module has five files. Each has a logical equivalent on Mac/Linux:

| Windows file | Job | Mac equivalent | Linux equivalent |
|---|---|---|---|
| `windows/tts_hook.ps1` | Stop hook. Reads transcript, strips markdown, synthesizes via `edge-tts`, plays MP3 via WPF MediaPlayer. Path-guards against running outside allowlisted folders. | **`tts_hook.sh`** (bash) -- read transcript, strip markdown, then either: (a) shell out to `say -v <voice> "$text"` (built-in, no `edge-tts` needed); OR (b) call `edge-tts --voice ... --text ... --write-media out.mp3 && afplay out.mp3` for parity with Windows. **Recommend (a) for first-run simplicity, (b) for voice parity with Windows.** | **`tts_hook.sh`** -- same pattern, but tools change: `espeak "$text"` for built-in (basic quality) OR `piper --model <path> < text \| aplay` for neural local OR `edge-tts ... && mpg123 out.mp3` for cloud-neural. **Recommend `piper` for quality, `espeak` for zero-setup.** |
| `windows/toggle_tts.ps1` | Toggle script for `/voice`. Touches/removes a `tts_disabled.flag` file. | **`toggle_tts.sh`** -- same logic, `touch` / `rm` for the flag. | **`toggle_tts.sh`** -- same as Mac. |
| `windows/tts_voices.txt` | Persona → voice mapping. Default `en-US-AvaNeural`. | **Same file with adjusted voice IDs.** If using `say`: voice IDs come from `say -v ?` (e.g., `Samantha`, `Daniel`, `Karen`). If using `edge-tts`: same Microsoft voice IDs as Windows. | **Same file with adjusted voice IDs.** If using `espeak`: voice IDs from `espeak --voices` (e.g., `en`, `en-us`, `en-gb-x-rp`). If using `piper`: model file paths. If using `edge-tts`: same as Windows. |
| `windows/commands/voice.md` | `/voice` slash command. | **Same file with two adjustments:** the example commands inside change from `.ps1` to `.sh`, and the example `pwsh` invocation becomes `bash`. The Markdown shape stays identical. | Same as Mac. |
| `windows/settings.json` | Claude Code settings registering the Stop hook. | **Same shape**, but the hook command changes from `pwsh -File ...tts_hook.ps1` to `bash .../tts_hook.sh`. **If the user already has a `~/.claude/settings.json` or `<game>/.claude/settings.json`, MERGE -- don't overwrite.** | Same as Mac. |

## Translation guidance

### PowerShell idioms → bash / zsh

- `Get-Content $path` → `cat "$path"`.
- `Set-Content $path $value` → `printf '%s\n' "$value" > "$path"`.
- `Test-Path $path` → `[ -e "$path" ]`.
- `$env:USERPROFILE` → `$HOME`.
- WPF `MediaPlayer` for MP3 playback → `afplay file.mp3` (Mac, built-in) / `mpg123 file.mp3` or `mpv --no-video file.mp3` (Linux).
- PowerShell regex via `-replace` → `sed` or bash parameter expansion. The markdown-stripping logic is the most regex-heavy part of the hook -- port carefully.
- PowerShell `Start-Process -NoNewWindow` (background async playback) → `& \!` (bash background job) plus `disown` if the parent will exit before playback finishes.

### SAPI / edge-tts voice list → Mac / Linux equivalents

**On Mac (`say`):**
- `say -v ?` lists every installed voice. Format: `Name (locale) -- sample sentence`.
- Default English voices: `Samantha`, `Alex`, `Daniel`, `Karen`, `Moira`, `Tessa`, `Veena`.
- For neural quality, install Premium / Enhanced voices via System Settings → Accessibility → Spoken Content → System Voice → Manage Voices.
- Usage: `say -v "Samantha" -r 200 "Hello world"`.

**On Mac (`edge-tts`, optional, for parity with Windows):**
- Same voice IDs as Windows: `en-US-AvaNeural`, `en-US-AndrewNeural`, etc.
- `python -m edge_tts --list-voices` works identically.
- Synthesis: `edge-tts --voice en-US-AvaNeural --text "Hello" --write-media out.mp3`. Play with `afplay out.mp3`.

**On Linux (`espeak`):**
- `espeak --voices` lists every voice. Format: `Pty Language Age/Gender VoiceName File`.
- Default English voices: `en`, `en-us`, `en-gb`, `en-gb-x-rp`, `en-gb-scotland`.
- Quality is robotic -- fine as a fallback, not for immersion.
- Usage: `espeak -v en-us "Hello world"`.

**On Linux (`piper`, recommended for quality):**
- Local neural TTS, downloadable models from [github.com/rhasspy/piper](https://github.com/rhasspy/piper).
- Voice IDs are model file paths (e.g., `~/.local/share/piper/en_US-amy-medium.onnx`).
- Usage: `echo "Hello" | piper --model en_US-amy-medium.onnx --output-raw | aplay -r 22050 -f S16_LE -t raw -`.

**On Linux (`edge-tts`, optional):** same as Mac.

### Markdown stripping

The Windows hook strips markdown before synthesis (otherwise voices read backticks, asterisks, link URLs aloud, and it's terrible). Port the regex carefully. Common stripping rules:

- Inline code: `` `foo` `` → `foo`.
- Bold/italic: `**foo**` / `*foo*` / `_foo_` → `foo`.
- Links: `[text](url)` → `text` (drop the URL).
- Headings: `### Heading` → `Heading`.
- Code blocks: ```` ```...``` ```` → drop entirely (don't read code aloud).
- Lists: `- item` → `item` (or `, item, ` for flow).

The Windows hook also truncates replies over 300 characters to the first non-empty line. Preserve that behavior.

## Known pitfalls

- **Audio-device permission prompts (Mac).** First time a script triggers TTS on macOS, the system may prompt for output-device access if the terminal doesn't already have it. Less common than the mic prompt for PTT, but possible -- document it.
- **`chmod +x` on shell scripts.** Newly-written `.sh` files default to non-executable. The agent must explicitly `chmod +x tts_hook.sh toggle_tts.sh` (or the hook will silently fail to fire -- Claude Code's hook runner just logs `permission denied` and moves on).
- **Stop hook needs a fresh session start.** Claude Code reads `.claude/settings.json` once at session start. After installing the hook, the user must start a NEW session -- `/resume`-ing an old one won't pick up the hook. Same caveat as Windows.
- **Hook is global, path-guard is the security boundary.** The hook fires on every assistant turn in every project. The path-guard (checking `~/.claude/tts_game_folders.txt`) is what prevents it from speaking in unrelated projects. **Do not remove the path-guard during the port.** Translate it faithfully.
- **Speech preemption.** When Claude answers a follow-up while the previous reply is still speaking, the in-progress speech should be killed (otherwise replies stack). The Windows hook tracks `tts_hook.pid`; on Mac/Linux, do the same -- write the playback PID, and on each new fire, `kill` the old one if alive.
- **Wayland audio routing.** On some Wayland desktop environments, scripts launched as Stop hooks may inherit a different audio session than the user's normal terminal -- output goes to the wrong device or nowhere. Test with `paplay /usr/share/sounds/alsa/Front_Center.wav` from inside the hook to confirm the audio session is correct.
- **`edge-tts` rate limiting.** Microsoft's free endpoint is rate-limited. Heavy TTS use can trigger throttling. If the user opts for the `edge-tts` path, document the fallback (switch to `say` / `piper`).
- **`say` voice install size (Mac).** High-quality `say` voices are large (~500 MB each) and require manual install via System Settings. The default voices work but are noticeably lower quality. Surface this trade-off to the user.

## Verification checklist (run after the agent finishes building)

The user runs these manual tests to confirm the port works.

1. **Hook script is executable and parses cleanly.** Run `bash -n tts_hook.sh` -- no syntax errors. `ls -la tts_hook.sh` shows the executable bit.
2. **Synthesis works in isolation.** Manually run `echo "Hello world" | bash tts_hook.sh` (or whatever the manual-trigger interface is). You should hear "Hello world" through the default audio output. If silent, debug audio routing first.
3. **Allowlist enforcement.** Add the per-game folder absolute path to `~/.claude/tts_game_folders.txt`. From a folder NOT on the allowlist, trigger Claude -- should NOT speak. From a folder ON the allowlist, trigger Claude -- SHOULD speak. The path-guard is the single most important behavior to verify.
4. **Persona detection.** Edit `<game>/persona.md` and set the active persona to `Persona1`. Edit `<game>/tts_voices.txt` and map `Persona1` to a distinctive voice. Trigger Claude -- verify that voice is used. Switch persona, trigger again -- verify voice changes.
5. **`/voice` toggle.** In Claude Code, type `/voice`. Confirm a `tts_disabled.flag` file appears in `.claude/`. Trigger Claude -- should be silent. Type `/voice` again -- flag goes away, speech resumes.
6. **Markdown stripping.** Ask Claude something that produces a code-heavy reply (with backticks, lists, headings). Verify the spoken version sounds clean -- no "asterisk asterisk", no read-aloud URLs, no code-block contents.
7. **Speech preemption.** Trigger Claude with a long reply, then trigger again before the first finishes. The first should cut off; the second should start cleanly.

If any step fails, capture the error and iterate with the agent -- that's the "expect to debug" tax flagged at the top of this file.

## Promoting a successful port back into the framework

If the user's port works end-to-end, the maintainer can promote `<user>/<game>/.claude/tts_hook.sh` (and friends) into `templates/tts/mac/` or `templates/tts/linux/`. That removes the "untested" disclaimer for that platform on the next framework release.

The promotion criteria: clean install on a fresh machine of the same platform + all 7 verification steps pass + no platform-specific assumptions about the user's setup beyond what the README documents + the path-guard logic survives the port intact.

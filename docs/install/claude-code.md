# Install on Claude Code

1. Clone this repo straight into your Claude Code skills folder, so the clone itself is the skill:

   ```
   git clone https://github.com/hintforge/builder ~/.claude/skills/hintforge
   ```

   On Windows, `~` is your user folder (`%USERPROFILE%`). The repo root carries its own `SKILL.md` next to the procedure files it links to (`setup_wizard.md`, `ingestion.md`, `doctor.md`, `templates/`), so install the whole repo. The `.agents/skills/hintforge/` folder holds only the manifest.
2. Start a new Claude Code session. Skills load when a session starts, so a session that was already open won't see the builder.
3. Open that session in the workspace where you keep (or want to keep) your guide folders.

**Updating.** Run `git pull` inside `~/.claude/skills/hintforge`. Because the clone is the skill, you don't need to copy anything or create links. A copied install goes stale silently on every update.

**Verification.** Ask "build a guide for [game name]" or "set up a new Hintforge corpus". The builder should greet you and start the setup wizard -- collecting game name, persona cast, dial defaults, and vector-extension choices before scaffolding any files.

## Runtime caveats

These are Claude-Code-specific or Cowork-specific notes that don't belong in the OS portability matrix (see [`../../os_compatibility.md`](../../os_compatibility.md)) but matter for anyone running the builder on this runtime.

### Claude Code specifics

- **`.claude/settings.json` hook configs.** SessionStart, PreCompact, Stop hooks are a Claude Code feature. Other AI runtimes have analogous mechanisms (system prompts, custom instructions, MCP server integrations), but the wiring is runtime-specific.
- **Slash commands** (e.g. `/loop`, `/schedule`). Claude-Code-specific; the framework doesn't currently rely on any, but instantiated guides may want them.
- **Skill files** (`.skill` archives). Claude Code-specific packaging.

### Cowork

- **Telegram dispatch + scheduled tasks.** Cowork-specific; the framework doesn't require them. Instantiated guides may use them for "remind me about my open thread weekly" style ergonomics, but it's optional.
- **`SessionStart` hook auto-printing CHECKPOINT.md.** Useful but not required -- without it, the user just opens CHECKPOINT.md manually. The AI agent follows the same startup sequence either way.
- **Persistence caveat.** Cowork is session-scoped and files don't persist locally between sessions, which breaks the framework's storage model for active guide work. Cowork tends to *hallucinate* framework rules instead of loading the per-folder `CLAUDE.md`. The setup wizard detects this and warns before doing any work. Cowork is fine for short triage or single-session tasks; it is not the right runtime for building or maintaining a guide.

### Browser claude.ai

- Same persistence problem as Cowork without a filesystem connector: files don't persist locally between sessions. Not the right runtime for building or maintaining a guide.

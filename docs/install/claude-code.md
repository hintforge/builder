# Install on Claude Code

1. Clone this repo to any local path.
2. Run `/plugin add <path-to-clone>/.agents/skills/hintforge/` from inside Claude Code.
3. Open a session in the workspace where you keep (or want to keep) your guide folders.

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

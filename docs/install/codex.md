# Install on Codex (CLI or desktop)

1. Clone this repo straight into your Codex skills folder, so the clone itself is the skill:

   ```
   git clone https://github.com/hintforge/builder ~/.codex/skills/hintforge
   ```

   The repo root carries its own `SKILL.md` next to the procedure files it links to (`setup_wizard.md`, `ingestion.md`, `doctor.md`, `templates/`), so install the whole repo. The `.agents/skills/hintforge/` folder holds only the manifest plus `agents/openai.yaml` (optional display metadata), and on its own it cannot run a single procedure.
2. For Codex desktop, point the Skill Picker at that clone.
3. Start a new session in the workspace where you keep your guide folders.

**Updating.** Run `git pull` inside `~/.codex/skills/hintforge`. You don't need to re-copy anything.

**Verification.** Ask "build a guide for [game name]". The builder should start the setup wizard.

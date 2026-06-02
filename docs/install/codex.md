# Install on Codex (CLI or desktop)

Codex CLI auto-discovers `.agents/skills/` from your working directory up to the repo root, so the easiest install is:

1. Clone this repo to a parent directory of where you keep your guide folders (e.g. clone next to your `Guides/` directory).
2. Inside that parent (or any subfolder under it), run `codex` -- the skill loads automatically.

For Codex desktop, use the Skill Picker to point at `.agents/skills/hintforge/` from the cloned repo; the `agents/openai.yaml` metadata supplies the display name and trigger phrasing.

For a global install, copy `.agents/skills/hintforge/` to `~/.codex/skills/hintforge/`.

**Verification.** Ask "build a guide for [game name]". The builder should start the setup wizard.

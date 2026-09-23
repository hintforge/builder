# Install on OpenClaw

1. Clone this repo straight into your OpenClaw skills directory, so the clone itself is the skill: `git clone https://github.com/hintforge/builder ~/.openclaw/skills/hintforge` (user-wide), or into `<workspace>/skills/hintforge/` (workspace-local). Install the whole repo: its root `SKILL.md` links to procedure files that sit beside it. The `.agents/skills/hintforge/` folder holds only the manifest.
2. Open a session in the workspace where you keep (or want to keep) your guide folders.

**Updating.** Run `git pull` inside the clone.

The skill's description is what ClawHub matches author intent against; trigger it with phrases like "build a guide for [game]" or "set up a new Hintforge corpus".

**Verification.** Ask "build a guide for [game name]". The builder should start the setup wizard.

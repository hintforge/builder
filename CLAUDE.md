# hintforge -- Game-Guide Framework

This repository is the **Hintforge builder** skill -- a setup-side framework for authoring spoiler-controlled video game guides in Hintforge format.

## Skill location

The skill's manifest lives at [`.agents/skills/hintforge/SKILL.md`](.agents/skills/hintforge/SKILL.md). Codex CLI and OpenClaw scan `.agents/skills/` folders, but that folder alone cannot run a procedure: the root `SKILL.md` links to procedure files beside it, so every runtime installs the whole repo. Claude Code does not read `.agents/skills/` at all: clone the repo into `~/.claude/skills/hintforge` as described in [`docs/install/claude-code.md`](docs/install/claude-code.md). Install steps for every runtime: [`docs/install/`](docs/install/).

## Neutral homes for load-bearing content

- **All behavioral rules, triggers, and procedures:** [`SKILL.md`](SKILL.md)
- **Universal runtime principles (17 principles, reader-side by design):** [reader skill's `principles.md`](https://github.com/hintforge/reader/blob/main/.agents/skills/hintforge-reader/principles.md)
- **On-disk corpus format contract:** [`docs/corpus-format.md`](docs/corpus-format.md)
- **Folder structure and framework overview:** [`README.md`](README.md)

## Companion skill

The corresponding *reader* skill (used at runtime, when a player wants hints) is at [`hintforge-reader`](https://github.com/hintforge/reader). The two skills together replace what was previously a single monolithic framework.

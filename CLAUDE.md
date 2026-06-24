# hintforge -- Game-Guide Framework

This repository is the **Hintforge builder** skill -- a setup-side framework for authoring spoiler-controlled video game guides in Hintforge format.

## Skill location

The skill lives at [`.agents/skills/hintforge/SKILL.md`](.agents/skills/hintforge/SKILL.md). This path is read identically by Claude Code, Codex CLI (which scans `.agents/skills/` from cwd up), and OpenClaw.

## Neutral homes for load-bearing content

- **All behavioral rules, triggers, and procedures:** [`SKILL.md`](SKILL.md)
- **Universal runtime principles (17 principles, reader-side by design):** [reader skill's `principles.md`](https://github.com/hintforge/reader/blob/main/.agents/skills/hintforge-reader/principles.md)
- **On-disk corpus format contract:** [`docs/corpus-format.md`](docs/corpus-format.md)
- **Folder structure and framework overview:** [`README.md`](README.md)

## Companion skill

The corresponding *reader* skill (used at runtime, when a player wants hints) is at [`hintforge-reader`](https://github.com/hintforge/reader). The two skills together replace what was previously a single monolithic framework.

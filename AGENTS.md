# Agents

This repository is the **Hintforge builder** skill -- a setup-side framework for authoring spoiler-controlled video game guides in Hintforge format.

## Skill location

The skill lives at [`.agents/skills/hintforge/SKILL.md`](.agents/skills/hintforge/SKILL.md). This path is read identically by Claude Code, Codex CLI (which scans `.agents/skills/` from cwd up), and OpenClaw.

## Companion skill

The corresponding *reader* skill (used at runtime, when a player wants hints) is at [`hintforge-reader`](https://github.com/dtiger1889-ops/hintforge-reader). The two skills together replace what was previously a single monolithic framework.

## Domain vocabulary

Hintforge uses domain-specific terms (corpus, universal core, vector extension, stitch, zipper, dial, claim format, manifest, `corpus-core-version`, etc.). See [`CONTEXT.md`](CONTEXT.md) for a plain-language glossary. The on-disk format contract is specified separately in [`docs/corpus-format.md`](docs/corpus-format.md).

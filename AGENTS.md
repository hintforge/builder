# Agents

This repository is the **Hintforge builder** skill -- a setup-side framework for authoring spoiler-controlled video game guides in Hintforge format.

## Skill location

The skill's manifest lives at [`.agents/skills/hintforge/SKILL.md`](.agents/skills/hintforge/SKILL.md). Codex CLI and OpenClaw scan `.agents/skills/` folders, but that folder alone cannot run a procedure: the root `SKILL.md` links to procedure files beside it, so every runtime installs the whole repo. Claude Code does not read `.agents/skills/` at all: clone the repo into `~/.claude/skills/hintforge` as described in [`docs/install/claude-code.md`](docs/install/claude-code.md). Install steps for every runtime: [`docs/install/`](docs/install/).

## Companion skill

The corresponding *reader* skill (used at runtime, when a player wants hints) is at [`hintforge/reader`](https://github.com/hintforge/reader). The two skills together replace what was previously a single monolithic framework.

## Domain vocabulary

Hintforge uses domain-specific terms (corpus, universal core, vector extension, stitch, zipper, dial, claim format, manifest, `corpus-core-version`, etc.). See [`CONTEXT.md`](CONTEXT.md) for a plain-language glossary. The on-disk format contract is specified separately in [`docs/corpus-format.md`](docs/corpus-format.md).

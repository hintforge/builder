---
name: hintforge
description: Build OR maintain a Hintforge-format game guide. Use when starting a new spoiler-controlled companion for a published video game, ingesting research results, running stitch/zipper synthesis, or running the doctor procedure for post-instantiation maintenance (format bumps, game updates, targeted repair). Activates on triggers like "build a guide for X", "ingest the research", "run stitch", or "doctor hintforge" (post-instantiation maintenance).
license: CC-BY-NC-SA-4.0
version: 68
---

# Hintforge builder

A framework for authoring a spoiler-controlled video-game guide. Walks an author through scaffolding a new corpus from setup answers, generates research-cascade briefs, ingests research results into corpus files, and synthesizes cross-system edges via stitch-and-zipper passes.

The corpora this builder produces are consumed at runtime by the **hintforge-reader** skill. The two skills together replace what was previously a single monolithic framework.

## Where corpus files get written -- read first

This skill runs on behalf of a corpus living in the **user's workspace** (their cwd, the path in `setup_answers.txt:workspace_root`, or their Documents folder) -- **never inside the skill's own installation directory.** When you see `Base directory for this skill: ...` injected by the skill loader at the top of this payload, treat it as **read-only metadata**: it tells you where to read framework files from (`setup_wizard.md`, templates, etc.), not where to write corpus files. All Write/mkdir paths resolve from `[WORKSPACE_ROOT]` per [`setup_wizard.md`](setup_wizard.md) Step 1.9 (strict cascade: setup_answers → cwd → OS Documents default). Writing corpus content under `~/.claude/skills/` (or platform equivalent) is a bug -- see [`setup_wizard.md`](setup_wizard.md) Step 1.9 for the workspace-root cascade.

## Activation

Activate on author-style intents:

- "I want to build a guide for [game]"
- "Set up a new Hintforge corpus"
- "Ingest the research in research_inbox"
- "Run stitch" / "run zipper"
- **"Doctor hintforge"** (primary trigger for post-instantiation maintenance: format bumps, game updates, targeted repair). Aliases that also work: "doctor my guide", "doctor the corpus". **Do not** trigger on the bare "run the doctor" -- that phrasing collides with Claude Code's built-in `/doctor` CLI health-check command and routes to the wrong place.
- **"Hintforge doctor, reddit sweep"** (the community-knowledge sweep; canonical phrase, runs via the doctor anchor). Optionally scoped: "hintforge doctor, reddit sweep for the [patch / DLC / gap]". Routes to [`reddit_sweep.md`](reddit_sweep.md) as a dedicated session. There is no standalone "run the reddit sweep" trigger -- the `hintforge doctor` anchor is what reliably loads the skill.
- "Generate a research brief for [game / topic]"

Do not activate for runtime player questions ("where do I go?", "hint for this puzzle"). Those belong to the `hintforge-reader` skill.

## Setup flow

When any build / setup / "guide for X" intent fires:

- **If `../Guides/<game>/` already exists with corpus content from a prior wizard run**, the wizard has already run for that (user, game) pair -- answer the user's actual question directly using the guide's contents. The wizard runs once per pair.
- **If the folder is empty or missing**, the first action is to **read [`setup_wizard.md`](setup_wizard.md) end-to-end**, then run the wizard from Step -1. Do not infer answers, do not scaffold files, do not write personas, do not skip Step 8. The wizard's Hard rule (every step DONE / DONE-VIA-PREFILL / ASKED ABOUT) is binding.

1. **Setup wizard.** [`setup_wizard.md`](setup_wizard.md) collects game name, persona cast, dial defaults, game-type classification (which vector extensions to scaffold), source-language set, and other per-game answers. Output: a populated corpus root with the universal core plus the selected vector extensions, all files in `scaffold` state.
2. **Manual alternative.** [`instantiation.md`](instantiation.md) documents the manual step-by-step alternative for authors who prefer not to run the wizard. Same end state.

## Research cascade

3. **Brief generation.** The builder generates research briefs (P1, P2, ..., P<N>) keyed to corpus structure. Brief format and scope decisions are documented inside the wizard and in [`ingestion.md`](ingestion.md).
4. **Research execution.** The author runs the briefs externally (Deep Research, Claude Code, etc.) and drops results into `research_inbox/p<N>/`.
5. **Ingestion.** Author triggers "ingest the research" -- the builder runs the [`ingestion.md`](ingestion.md) procedure, populating corpus files, updating status fields, and moving processed briefs to `_processed/`.

## Synthesis

6. **Stitch and zipper.** After ingestion, the author runs [`stitch_and_zipper.md`](stitch_and_zipper.md). Stitch writes cross-system edges into `dependencies.md`. Zipper reconciles overlaps where two passes wrote about the same topic. Both run in dedicated sessions.

## Templates

Corpus scaffolds live in [`templates/`](templates/). The wizard copies the universal-core templates into every new corpus and conditionally copies vector-extension templates based on setup answers. Templates include `checkpoint.md`, `claude_md.md`, `persona.md` (cast scaffolding only -- universal persona discipline lives in the reader skill), `architecture.md`, `nav_index.md`, `nav_zone.md`, `localization.md`, `warning_tiers.md`, `claim_format.md`, `limitations.md`, `dependencies.md`, and `folder_structure.md`. Optional modules (`ptt/`, `tts/`, `save_watcher/`) are also under `templates/`; the wizard installs them only on opt-in.

## Corpus format contract

The on-disk shape of a corpus -- universal core, vector extensions, runtime discovery mechanism, claim format, architecture-level structures, status field discipline, spoiler tier annotation syntax -- is specified at [`docs/corpus-format.md`](docs/corpus-format.md). The builder is what produces this format; the reader expects it. Maintainers editing either skill should treat the format spec as the authoritative contract between them.

## What this skill does NOT do

- It does not provide runtime hint behavior to players. That is the `hintforge-reader` skill.
- It does not commit, push, or publish a corpus. The author owns those decisions.
- It does not generate persona voices from thin air; the author supplies cast research as part of setup.
- It does not invent claims. If research yields no answer on a topic, the corpus records the gap in `limitations.md` and the file stays in `scaffold` state until real research lands.

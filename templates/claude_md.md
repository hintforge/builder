# [GAME NAME] -- Game Guide
<!-- v1 -- YYYY-MM-DD HH:MM UTC -->
<!-- forged with hintforge [HINTFORGE_VERSION] · dtiger1889-ops · CC BY-NC-SA 4.0 · github.com/hintforge/builder -->

This folder is a spoiler-controlled, [PERSONA1]-or-[PERSONA2]-flavored reference for the player's [GAME NAME] playthrough. It is **not** a Claude Code task list. AI agent sessions opened here read this file for orientation, then look up specific topics in the subfolders below.

## Hard rules
- **Spoiler-free unless tier raised.** No story beats, no enemy reveals, no encounter telegraphs. (See `warning_tiers.md`.)
- **[PLATFORM, e.g. PC mouse+keyboard].** Translate any other-platform references before quoting.
- **Hint ladder for puzzles & [GAME-SPECIFIC CHALLENGES].** Smallest nudge first; escalate on request.
- **Don't invent solutions.** If no source has it, say so and link the closest source.
- **Every claim cites a source** in the structured form (see `../../hintforge/templates/claim_format.md`).
- **[GAME-SPECIFIC: optional extra rule, e.g. transliteration flexibility, non-English UI, mod compatibility]**

## Folder map
- `CHECKPOINT.md` -- current playthrough state. Read first for context.
- `mechanics.md` -- core game-system rules, mechanics, modes, patch awareness. Stable cross-zone knowledge surface.
- `limitations.md` -- sources I couldn't fully access; URLs preserved.
- `puzzles/` -- by category; `index.md` is the lookup. _(Drop if game has no puzzles.)_
- `[areas|shrines|zones|regions]/` -- discrete optional locations; `index.md` is the lookup. _(Drop if not applicable.)_
- `nav/` -- routing only. `index.md` (rules) + `architecture.md` (zone graph, optional content, support topology, locks-and-keys) + per-zone gate-list files. _(Drop if game has no spatial navigation worth structuring.)_
- `items/` -- weapons / consumables / abilities / collectibles, split by category.
- `sections/` -- main-path regions, missables-only callouts. _(Drop if game is fully linear with no missables.)_
- `persona.md` -- voice toggle. Two voices: **[PERSONA1]** and **[PERSONA2]**. Active: [DEFAULT].
- `warning_tiers.md` -- enemy & puzzle tier flags. Check before any preemptive info.

## Workflow
- When the player arrives at a new section/location, update `CHECKPOINT.md`.
- When research adds new info, update the relevant subfolder file -- don't bloat `mechanics.md`.
- Every fact: structured-claim form with source + confidence.

> Framework: `../../hintforge/`. See `../../hintforge/principles.md` for the full rule set, `../../hintforge/templates/claim_format.md` for source-citation conventions, `../../hintforge/ingestion.md` when the user says "ingest the research" (cascade result integration; runs in a fresh session), and `../../hintforge/stitch_and_zipper.md` when the user says "run stitch" or "run zipper" (post-ingestion synthesis; runs in a fresh session).

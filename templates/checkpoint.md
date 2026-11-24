# [GAME NAME] -- CHECKPOINT
Last updated: YYYY-MM-DD HH:MM UTC
Last played: YYYY-MM-DD
<!-- `Last played:` = the date the player last played (bump at session end); `Last updated:` = last edit of this file. Stale-session rule: `setup_wizard.md` Step 10. Size limit and changelog archive: `docs/corpus-format.md` §1. -->

## Status
[1-2 lines: where the player is right now. Map / area / quest / save state. Be specific -- a fresh session resumes from this.]

## Player
- **Name:** [PLAYER_NAME -- what the persona calls them; default "Player"]

game_window_process:
<!-- The game's program name without .exe, for the reader's Windows screenshot tool. Leave blank at setup: the reader fills it on the player's first screenshot request (it can differ by store, so it is per-player). -->

run: 1
<!-- Name of the current run (playthrough); the reader shelves the old run to `runs/<name>.md` when the player starts a new one. -->


## Goal
Spoiler-controlled playthrough on [PLATFORM]. Cowork acts as live reference for [puzzles, items, missables, areas, ...] -- no story, no enemy reveals (unless tier raised).

## Key decisions
- [Platform + control scheme]
- Spoiler tier settings (see `warning_tiers.md`)
- [Game-specific constraints -- e.g. "no DLC", "Hardcore mode", "100% run", "permadeath"]

## Open threads
- [Things the player is stuck on, tracking, flagged for follow-up. One bullet each. Include the question + the closest known answer + what's still uncertain.]

## Session intent
<!-- The player's own note to themselves, newest line first, at most three lines. Written ONLY from the player's answer to the single closeout question the reader asks at session end; the reader never authors a line here and never infers one from the session. Surfaced on a resume opener ("where was I", "pick up where I left off"). Delete a line once the player says it is done. Full contract: the reader skill's `persona_universal.md`, "Session-goal closeout". -->
- [YYYY-MM-DD -- what the player said they wanted to do next -- what it belongs with (a character, a build, an area, an open thread)]

## Inventory (if relevant)
- **Carried:** [...]
- **Stored:** [...]
- **Loadout / build:** [...]

## Player position (omit if `localization-mechanism class` in `nav/architecture.md` is `none` -- e.g., procedural roguelikes with abstract level structure, narrative-only games, puzzle games. This file survives any wipe-and-regen of the guide; never auto-overwritten.)

```yaml
player_position:
  current_zone: unknown      # zone-id from nav/architecture.md; "unknown" until first session
  last_known_gate: unknown   # gate name from nav/<zone>.md sequential gates list
  reachable_zones: []        # computed from zone graph + current position; update at session end
  last_updated: YYYY-MM-DD
  confidence: unknown        # high=just told/witnessed · medium=last session · low=inferred · unknown=no data
  # lookahead_n: 2           # uncomment + tune if persona Rule 2 fires too early (lower) or misses warnings (raise)
  lookahead_cache:
    computed_at_position: unknown   # snapshot of last_known_gate when this cache was last computed; "unknown" until first wrap
    computed_at: unknown            # YYYY-MM-DD of the `checkpoint`/wrap that wrote this cache
    next_gates: []                  # gates within lookahead_n forward steps from computed_at_position
    pnr_warnings: []                # spoiler-safe one-line warnings (e.g. "next gate is one-way -- finish missables here first")
    notes: ""                       # optional author/maintainer context for next session
```
<!-- `lookahead_cache` contract (fresh when `computed_at_position == last_known_gate`; written at checkpoint/wrap): the reader skill's `lookahead_cache.md`. -->

## Progress timeline
- [x] [Major milestone reached]
- [x] [Next major milestone reached]
- [ ] **NEXT:** [What's queued up]

## Files that matter
- `warning_tiers.md` -- spoiler tiers; `persona.md` -- voice; `CLAUDE.md` / `AGENTS.md` -- optional platform shims pointing at the hintforge-reader skill (no rules of their own)
- `mechanics.md` -- core game-system rules, mechanics, modes (stable)
- `limitations.md` -- blocked sources
- `puzzles/index.md` / `[areas]/index.md` / `items/` / `sections/` -- lookup hubs

## Next step
[1 line: bot-orientation marker for session resume -- area name, quest stage, structural position. NOT a preview of upcoming game content. The player doesn't see this as guidance; the bot reads it to re-orient. See Principle #2.]

## Phase state
<!-- Builder phase tracking, updated by setup, ingestion, stitch and zipper. Readiness check, preconditions and `stitch_stale`: `stitch_and_zipper.md` "Phase-readiness check" and "`stitch_stale` flag". -->
setup: complete YYYY-MM-DD
p1_brief: written YYYY-MM-DD | not started
p1_ingestion: complete YYYY-MM-DD | pending | skipped (reason)
p2_brief: written YYYY-MM-DD | not started
p2_ingestion: complete YYYY-MM-DD | pending | skipped (reason)
p3_brief: written YYYY-MM-DD | not started
p3_ingestion: complete YYYY-MM-DD | pending | skipped (reason)
zipper: complete YYYY-MM-DD | not run
stitch: complete YYYY-MM-DD | not run
stitch_stale: false
stitch_scope: full | [comma-separated subdirectory list if scoped]
# Module-sweep fields -- supplemental research sweeps that ingest into the corpus alongside the standard phase cascade.
# Each module-sweep procedure shipped by the framework adds its own `module_sweep_<kind>` line. Doctor reads any
# `module_sweep_*` field for drift detection (re-sweep cadence after patches / DLC / long gaps since last sweep).
# Re-runs preserve history (new artifact files with incremented same-day suffix); the field tracks the most-recent
# successful ingestion date.
module_sweep_reddit: not run | complete YYYY-MM-DD | partial YYYY-MM-DD (reason)
gitforge_handle: none
aggregation_opt_in: false

## Harness changelog
<!-- Newest first; keep the newest 3, older ones move to `archive/harness_changelog.md` (docs/corpus-format.md §1). -->
### v1 -- YYYY-MM-DD HH:MM UTC
- Project created from [`templates/`](https://github.com/hintforge/builder/tree/main/templates). Subfolders chosen: [list]. Personas chosen: [PERSONA1] / [PERSONA2], active: [DEFAULT]. Warning tiers: enemies [N], puzzles [N].

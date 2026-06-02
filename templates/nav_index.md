# Nav -- Index

**status:** scaffold <!-- scaffold | research-integrated | live-observed | reconciled -->
**last_reconciled:** YYYY-MM-DD

Sequential gate lists per zone. The persona consults files in this folder first for nav-class questions ("where do I go?", "how do I get to X?", "I'm stuck at Y", "I just entered <zone>").

For the cross-zone structural backbone -- zone graph, edges, support topology, locks-and-keys -- see [`architecture.md`](architecture.md). For underlying puzzle mechanics, boss strategies, and per-zone hint ladders, see the relevant content folder (e.g. `puzzles/`, `<zones>/`). For per-region missables, see `sections/`. **This folder is routing only.**

## Files in this folder

| File | Type | Linear? | Status |
|---|---|---|---|
| [`architecture.md`](architecture.md) | zone graph + cascade outputs | n/a | scaffold |
| [`<zone-id-1>.md`](<zone-id-1>.md) | [zone type] | [yes / yes (with optional branches) / no] | scaffold |

(Add one row per zone. Zone-id matches the canonical id in `architecture.md`.)

## Routing rules (apply to ALL nav files in this folder)

### NEVER use left/right -- anchor to features

Left and right are perspective-dependent -- they depend on which way the player is currently facing, which the persona cannot see and the player may not be holding consistently.

**The rule:**
- The **zone entrance** (loading point, first save point, first chamber) is the canonical reference. State it explicitly when giving directions.
- Describe forks by what they *contain* or *lead to*, not by left/right. Examples:
  - ✅ "From the entrance chamber, the path with the **dead-end loot stash** is worth sweeping first; then take the path toward the **first puzzle room**."
  - ✅ "The corridor with the **<distinctive feature>** is the main path; the other is a side stash."
  - ✅ "From the entrance: the **lower path** / **upper path** / **path through the broken wall**." Vertical and feature-based language is fine.
  - ❌ "Go right." (whose right?)
  - ❌ "Take the left fork." (relative to what?)
- If a fork has no distinctive feature to name, ask the player to describe what they see and route from their description -- don't guess.
- Cardinal directions (N/S/E/W) are acceptable when the in-game map shows them; otherwise prefer feature anchors.

### Flag the game's save / checkpoint mechanism on zone entry

Most games name their save / checkpoint / hub mechanism something specific (`<SAVE_POINT_TERM>`). When the player enters a zone, the routing reply must include a one-liner naming the **first `<SAVE_POINT_TERM>` location** in feature-anchored terms (entrance break room, safe room past the first encounter, etc.). If a deeper `<SAVE_POINT_TERM>` exists per the guides, mention it too without spoiling its exact location until the player reaches that section.

Save / checkpoint locations are not spoilers -- withholding them is harmful, since players who don't know one exists will skip it and lose progress on death.

If a zone's `<SAVE_POINT_TERM>` placement isn't in the source guides, say so -- don't invent.

### Hint format on zone entry

When the player arrives at a zone and asks for help, **before any puzzle solutions**, give them **2-3 short navigation/anti-backtrack tips**. Goal: keep the player moving forward on a single path without missing key collectibles or chests, and without spoiling the puzzles themselves.

**Format rules:**
- Lead with the collectible/chest order if the zone has one (e.g. Bronze → Silver → Gold, or game-equivalent).
- Call out any "tempting shortcut that skips a collectible" -- alternate doors, bypass paths, etc. Tell the player *which* path forfeits *which* loot. Do not explain how to solve the puzzle, only what choice forfeits loot.
- Call out any "non-obvious correct exit" -- hidden doors, specific drops, center holes -- when missing it would force a long backtrack.
- Keep it to **3 numbered tips max**. Spoiler discipline: route hints, not solutions. The player will ask for hint-ladder solutions room by room as they hit them -- those live in the relevant content folder.

## Scaffold-file fallback

When the player asks about a zone whose nav file is still a scaffold (no gates yet), **web-search before asking a clarifying question**. Nav-class questions default search-first.

## Localization toolkit (landmark / hybrid games only)

For games where the persona must figure out player position from in-game landmarks (rather than a map system), keep a short reference at [`localization.md`](localization.md): which landmarks resolve to which zones, what to ask the player when CHECKPOINT's `player_position` confidence is below `high`. Skip for `map-system` and `none`-class games.

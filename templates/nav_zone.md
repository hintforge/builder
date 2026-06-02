# Nav -- [ZONE NAME]

**status:** scaffold <!-- scaffold | research-integrated | live-observed | reconciled -->
**last_reconciled:** YYYY-MM-DD
**research_run:** none

**Type:** [polygon | main-story zone | DLC zone | hub]
**Linear?:** [yes | yes (with optional branches) | no]
**Chapter:** [chapter name from architecture.md Chapter ↔ Zone Mapping]

## Entry

From `[source-zone-id]` via edge `([source-zone-id], [this-zone-id])` -- see `architecture.md`. [Optional: one sentence on what arrival looks like in-game.]

## Exit

To `[target-zone-id]` via edge `([this-zone-id], [target-zone-id])`.
**Type:** [story-gate | one-way | optional | hub-spoke | conditional]
**Point of no return:** [none | permanent | chapter-bound | missable-trigger | point-of-divergence]
[If non-`none`: one sentence on what's lost or locked out.]

## Outgoing edges

- `([this-zone-id], [target-1])` -- [type], [condition if any]
- `([this-zone-id], [target-2])` -- [type], [condition if any]

[List all exits from this zone, including optional and conditional. Every edge here must match a row in `architecture.md`'s edge table.]

## Entry tips (3 max)

Show before any puzzle solutions when the player arrives at this zone. Anchor to features, never left/right (see `index.md` routing rules). Lead with chest/collectible order if the zone has one; call out any shortcut that forfeits loot; call out any non-obvious correct exit.

1. [tip -- feature-anchored, no left/right]
2. [tip]
3. [tip]

## Sequential gates

1. **[short gate name]** -- [one sentence: what the player does to pass this gate]. [optional: one sentence on what not to miss or what this unlocks].
   - `point_of_no_return:` [none | permanent | chapter-bound | missable-trigger]
   - `lock:` [key required, if gate is item-keyed -- cross-references architecture.md locks-and-keys table]
2. **[next gate]** -- ...

[Gate granularity guide: 5-15 gates per zone, or 5-15 per branch for branching zones. One gate = one room-to-room transition or one decisive action that opens the next path. Nav-only: if a gate contains a puzzle or enemy encounter, name it as a pointer (e.g. `<puzzle name>` puzzle here -- see `puzzles/<puzzle_name>.md`) rather than solving inline. Use feature anchors, not left/right.]

## Optional branches / shortcuts

- **[branch name]** -- [when it appears, what it skips or costs, e.g. "forfeits a chest"].

## Common confusions

- "[typical wrong path or stuck point]" -- [correction. If confusion involves a wrong exit, reference the edge ID from Outgoing edges.]

## Sources

- [walkthrough URL]
- [wiki URL or forum thread]

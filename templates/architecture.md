# [GAME NAME] -- Architecture

**status:** scaffold <!-- scaffold | research-integrated | live-observed | reconciled -->
**last_reconciled:** YYYY-MM-DD
**research_run:** none

Cross-zone structural primitives. The persona reads this file for all cross-zone reasoning -- lookahead warnings (Rule 2), backtrack queries (Rule 3), reachability checks (Rule 4), locks-and-keys notifications (Rule 5). Per-zone gate lists live in `nav/<zone>.md` and reference this file's graph by edge ID. Drift between this file and per-zone files is a bug; run a consistency pass after each ingestion.

## Hintforge manifest

<!-- Read by the reader at session start (see docs/corpus-format.md §3). Bump corpus-core-version only when a change to docs/corpus-format.md would break an older reader; see the Versioning subsection in that doc. game-version-* fields describe the game build the corpus was authored against (player-supplied at setup; required as of v3); they are orthogonal to corpus-core-version (which is the schema axis). -->

```
corpus-core-version: 5
game-version: "[freeform version string the player named at setup -- semver, patch name, build number, all acceptable]"
game-version-platform: "[platform the player named at setup, e.g. PC / Steam, PS5, Switch -- required even for single-platform-today games]"
game-version-as-of: YYYY-MM-DD
vector-extensions: [comma-separated list of extension folders this corpus uses, e.g. puzzles, npcs, factions, optional_zones]
```

## Vector extensions

<!-- Wizard populates from Step 7 conditional-creation decisions. One entry per extension created. Reader uses this list to route topical questions to the right folder. Semantics are one line each; folders may be absent if the game does not need them. -->

- `puzzles/` -- discrete puzzle files with hint ladders, indexed by `puzzles/index.md`
- `npcs/` -- named individual NPCs (any `entity-status`: hostile, friendly, convertible, party, neutral), indexed by `npcs/index.md`. At `corpus-core-version: 5` and later this replaces the legacy `enemies/` folder; hostility is a state via `entity-status: hostile`, not a class identity. Generic-mob combat content continues to route via the `enemy` vector to `mechanics.md` (no folder needed for that).
- `factions/` -- group entities the player has a relationship with, indexed by `factions/index.md`
- `crew/` -- role-aggregated entities for run-bound / party-bound contexts (run-based roguelikes with persistent role slots, ship-crew sims), indexed by `crew/index.md`
- `reputation/` -- reputation tracks / alignment surfaces, indexed by `reputation/index.md`
- `endings/` -- multiple-endings files indexed by `endings/index.md`
- `paths/` -- branching-narrative path files indexed by `paths/index.md`
- `optional_zones/` -- side content keyed to parent zone IDs from the zone graph
- `mechanics/` -- per-system mechanic files (only when the universal-core `mechanics.md` is split into a directory; see `docs/corpus-format.md` §1)

## Zone Graph

**Game-type label:** [dungeon-linear | hub-and-spoke-with-dungeons | open-world-with-distinct-dungeons | open-world-explorative-only | procedural | on-rails | narrative-no-nav]
**Localization-mechanism class:** [map-system | landmark | hybrid | none]
**Entry node:** [zone-id where a new game starts]
**Hub nodes:** [list of zone-ids serving as hubs, or "none"]
**Source-language set:** [dev-country language + top-3 player-region languages -- drives the internationalization rule's non-English source mandate at research time]

**Nodes:**
- [zone-id] -- [canonical name]

**Edges:**

| From | To | Type | Direction | Condition | Point of no return | Notes |
|---|---|---|---|---|---|---|
| [zone-id] | [zone-id] | story-gate \| one-way \| optional \| hub-spoke \| fast-travel \| conditional | bidirectional \| one-way src→tgt | [unlock condition or leave blank] | none \| permanent \| chapter-bound \| missable-trigger \| point-of-divergence | [one-line context] |

**Edge types:**
- `story-gate` -- passing this edge advances the story; usually one-way at time of passing
- `one-way` -- direction is permanently fixed
- `optional` -- player's choice; access is permanent
- `hub-spoke` -- connection between hub node and a dungeon/zone; usually bidirectional
- `fast-travel` -- fast-travel network edge
- `conditional` -- access depends on a flag (item, story progress, NG+)

**Point-of-no-return subtypes:**
- `permanent` -- passing locks out the source zone forever
- `chapter-bound` -- access ends at chapter transition, may resume later
- `missable-trigger` -- passing locks out a missable item or quest in another zone
- `point-of-divergence` -- choice gate; alternative branch becomes unreachable

## Chapter ↔ Zone Mapping

| Chapter | Zones | Notes |
|---|---|---|
| [Chapter name] | [zone-id-1, zone-id-2] | [e.g., sequential -- no backtrack between zones] |

## Optional Content

| Name | Unlock condition | Access window | Parent zone | Recommended chapter | Failure mode |
|---|---|---|---|---|---|
| [name] | [story flag, item, level, NG+] | permanent \| chapter-bound \| one-shot | [zone-id you launch into it from] | [chapter from walkthroughs] | missable \| always-available \| NG+-only |

## Support Topology

### Save stations

| Zone | Locations |
|---|---|
| [zone-id] | [description of location in-zone] |

### Fast-travel network

[Describe the game's fast-travel system. List accessible nodes if applicable. Write "None -- no fast-travel in this game." if absent.]

### Hub access

[Describe hub nodes and how the player returns to them from dungeons/zones. E.g. "Return-to-hub trigger: exit elevator at polygon exit."]

## Locks and Keys

| Lock location | Key required | Key source | Visible before key? | Notes |
|---|---|---|---|---|
| [zone + description of gate] | [item or ability] | [zone where key is obtained] | yes \| no | [optional one-liner] |

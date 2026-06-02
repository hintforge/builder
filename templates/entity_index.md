# [GAME NAME] -- [Class display name, e.g. NPCs / Factions / Crew / Reputation]

**status:** scaffold <!-- scaffold | research-integrated | live-observed | reconciled -->
**deferred-to:** P1
**deferred-reason:** auto-aggregation target. Ingestion populates the roster from every claim carrying an `entity:` overlay whose id binds to this class. Per-entity files (`<class>/<entity-id>.md`) are scaffolded the first time the class folder is created and filled in as claims accumulate. See [`../ingestion.md`](../ingestion.md) step 8 for the aggregation contract and step 2.5 for the scaffold-check.
**last_reconciled:** YYYY-MM-DD
**class:** [npcs | factions | crew | reputation -- which class this index governs]

## Why this file exists

This file is the corpus's roster for the named entities in this class -- the player-facing index of "who / what is in this class, and where do I read about each one." For `npcs/`, the class covers any named individual NPC regardless of `entity-status` (hostile, friendly, convertible, party, neutral); hostility is a state, not a class identity. For `factions/`, the class covers group entities the player has a relationship with. For `crew/`, role-aggregated entities in run-bound or party-bound contexts. For `reputation/`, reputation tracks or alignment surfaces that warrant their own aggregation.

The reader consults this file when the player asks roster-shaped questions ("who can I recruit," "what factions are there"); per-entity detail lives in `<class>/<entity-id>.md`.

## Roster

One row per entity. Columns: `entity-id` (the slug used by the `entity:` overlay), `display name`, `entity-status` (for `npcs/` only -- `unspecified` otherwise), `status` (scaffold | research-integrated), `first-encounter zone`, `missable` (yes | no | scenario-locked). The roster reflects the corpus's current entity coverage; new entries get appended at ingestion-time.

| entity-id | display name | entity-status | status | first-encounter zone | missable |
|---|---|---|---|---|---|
| [populated by ingestion] | | | | | |

## Pointer rules

- Per-entity detail lives in `<class>/<entity-id>.md`. The reader opens those files for entity-shaped questions; this file is the index, not the answer surface.
- Claims about an entity continue to route to their primary-vector destination (per [`../ingestion.md`](../ingestion.md) step 4). The entity overlay aggregates the claim into the per-entity file in parallel.
- Hidden entities (`entity-hidden: yes`) keep their full content in the per-entity file; read-time tier gating handles concealment.

## Sources

- [Per-entity source citations live in the per-entity files, not here.]

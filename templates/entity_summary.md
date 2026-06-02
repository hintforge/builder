# [Entity display name]

**entity-id:** [slug used by the `entity:` overlay]
**class:** [npcs | factions | crew | reputation]
**entity-status:** [hostile | friendly | convertible | party | neutral | unspecified] <!-- required when class is npcs/; defaults to unspecified for other classes -->
**entity-hidden:** [yes | no] <!-- defaults to no; yes when the entity's name itself is a spoiler -->
**first-encounter-zone:** [zone-slug or "unknown" until ingestion populates]
**status:** scaffold <!-- scaffold | research-integrated | live-observed | reconciled -->
**deferred-to:** P[N] <!-- which phase is expected to populate this -->
**last_reconciled:** YYYY-MM-DD

## Current status

[One sentence reflecting the entity's current relationship-state in the corpus, e.g. "Recruited party member as of Ch3," "Hostile encounter zone X," "Convertible -- pre-recruitment combat documented; post-recruitment behavior pending P2." Updated as the corpus grows; status changes during play get appended as Status history entries below rather than a rewrite.]

## Recruitment / Access

[How the player encounters or recruits this entity. Source claims appear here as forward-pointers to their primary-vector destinations. Populated by ingestion from `entity:`-tagged claims with `vector: nav` or `vector: structure`.]

## Capabilities

[Build-adjacent content: abilities, equipment slots, party synergies, faction-level mechanics, etc. Forward-pointers to `items/abilities.md`, `items/builds.md`, etc. as appropriate.]

## Quests

[Quests, story beats, missions tied to this entity. Forward-pointers to `sections/<area>.md` or `paths/<id>.md`.]

## Achievements

[Platform achievements bound to this entity, populated from claims carrying both `entity:` and `achievement:` overlays. Forward-pointers to `achievements.md` entries.]

## Combat

<!-- Present when entity-status is hostile or convertible. Omit when not applicable. -->

[Combat-phase mechanics, weaknesses, tactics. Forward-pointers to `mechanics.md` or `warning_tiers.md`. For convertible entities, pre-conversion combat and any post-conversion hostile-state combat both live here.]

## Missability

[Whether this entity can be missed, the point-of-no-return window, and conditions that lock the player out. Forward-pointers to `sections/missables.md`.]

## Status history

<!-- Present when entity-status is convertible, party, or neutral and the relationship state changes during play. Omit for stable hostile/friendly entities. -->

[Chronological log of relationship-state changes: when the entity converted, betrayed, was recruited, shifted alignment, etc. Each entry: date or chapter marker, prior state, new state, trigger condition. Status changes do not relocate the file; they add an entry here.]

## See also

[Back-pointers to the canonical claim homes for each fact aggregated above. Populated by ingestion.]

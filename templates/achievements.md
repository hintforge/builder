# [GAME NAME] -- Achievements

**status:** scaffold <!-- scaffold | research-integrated | live-observed | reconciled -->
**deferred-to:** P1
**deferred-reason:** auto-aggregation target. Ingestion populates from every claim carrying an `achievement:` overlay field. Until P1 ingestion runs, this file is the achievement-stub skeleton -- a flat list of every achievement the game ships, pulled from the platform's canonical list during Stage 0. The skeleton's job is to be the completeness check P1 fills in against: every achievement here must resolve to at least one corpus claim by end of P1 ingestion, OR be recorded in `limitations.md` as a research gap.
**last_reconciled:** YYYY-MM-DD
**stub_source:** [Steam | PSN | Xbox | other -- recorded at Stage 0] <!-- Which platform's canonical list was fetched. Cite the URL in Sources at end of file. -->
**stub_fetched:** YYYY-MM-DD

## Why this file exists

This file is the corpus's single source of truth for "what achievements does this game have, and what do I need to do for each one." The reader consults it when the player asks any achievement-class question -- by name, by category, or by "what am I about to miss." The aggregator (future) uses it as the completeness skeleton: developer-authored achievement lists are exhaustive, so they double as the minimum claim count for a complete guide.

The reader treats this file as authoritative for **trigger conditions**, **point-of-no-return windows**, and **missability**. It does NOT re-derive these from per-zone files at read-time; ingestion is the moment of aggregation, and this file carries the synthesized result.

## Structure

The file is organized by `trigger_type`. One H2 per type, with achievement entries as H3s under each:

- `## Progression` -- story beats, chapter completes, level milestones
- `## Branch` -- mutually-exclusive choices, endings, faction picks
- `## Mastery` -- skill-bound and restriction-bound challenges
- `## Collection` -- finite, enumerable sets the player completes in full
- `## Threshold` -- cumulative counts without a finite-set ceiling
- `## Discovery` -- non-obvious mechanics or specific-action triggers (often hidden)

A trigger type with no achievements in this game is omitted from the file (not left as an empty section). If the game has zero achievements of a type, the absence is the answer.

## How to classify an achievement into a trigger type

Ask these questions in order; the first "yes" wins. The order matters because some achievements plausibly fit two categories, and the primary classification is what the player has to do *first* to unlock the achievement.

1. **Progression.** Does every player who reaches a certain point in the game get this? If yes, `progression`. (Reaches a story beat, completes a chapter, hits a level milestone, unlocks the default tier of a class.)
2. **Branch.** Does getting this exclude another achievement, or require a non-default choice no other player has to make? If yes, `branch`. (Side with one faction over its mutually-exclusive rival; pick one romance partner over others; pursue one ending that locks out the others.)
3. **Mastery.** Did the player demonstrate skill or accept a restriction beyond normal play? If yes, `mastery`. (Complete without dying; complete on the hardest difficulty; finish under a time limit; complete with a self-imposed loadout restriction.)
4. **Collection.** Is there a finite, enumerable set the player must complete in full? If yes, `collection`. (Find all collectible items of a named type; record every creature in a journal; donate every required item to a museum.)
5. **Threshold.** Is the trigger a cumulative count of any kind of action or state, without a finite-set ceiling? If yes, `threshold`. (Kill N enemies of a class; catch N fish total; read N books in one playthrough; ship N units of a single crop.)
6. **Discovery.** Was the player likely to find this only by deliberate exploration of a non-obvious mechanic, or by following an obscure hint? If yes, `discovery`. Often carries the platform's hidden flag.

Discovery comes last because it's the residual bucket. If any earlier category fits, the achievement isn't really about discovery; it's about whatever the earlier category named.

### Disambiguation rules at the boundaries

Three boundaries carry the highest mislabel risk. These rules resolve them.

**Mastery vs discovery.** Both can apply to "weird-thing-with-the-game-system" achievements. The distinction: `discovery` is when *the fact that the trigger exists* is the achievement (hidden mechanic, easter-egg interaction, weird emergent system). `mastery` is when *executing the trigger well* is the achievement (skill, restriction, time-bound). Shape examples:

- "Kill N enemies of a type within S seconds" -> mastery. The mechanic is obvious; the skill is the trigger.
- "Use a specific enemy's ability against itself" -> discovery. The interaction isn't obvious; finding it is the trigger.
- "Use one enemy as an improvised weapon against another" -> discovery. The interaction is non-obvious.
- "Complete the game without acquiring any of class X's powers" -> mastery. The restriction is the achievement; the mechanics are known.

**Threshold vs collection.** Both can apply to "count-up-to-N" achievements. The distinction: `collection` is when the *set members* are finite, named, and discoverable in advance (the corpus must enumerate them). `threshold` is when the *count* is the achievement; any unit satisfying the action class counts. Shape examples:

- "Catch every distinct species of fish" -> collection. There is a finite known list; the corpus enumerates them.
- "Catch 100 fish" -> threshold. Any fish counts toward the count; the set isn't bounded.
- "Donate every accepted item to the museum" -> collection. The accepted-items list is a finite set.
- "Kill 666 enemies of a class" -> threshold. Any enemy of that class counts.

**Progression vs branch.** Both can apply to "completed-a-chapter" achievements. The distinction: `progression` is the *default path* every player takes; `branch` is when the player had to *choose* this path over another mutually-exclusive one. Shape examples:

- "Complete chapter 5" -> progression. Every player who reaches the end of chapter 5 gets it.
- "Complete chapter 5 the empathetic way" -> branch. Required a non-default choice; excludes the unempathetic-way achievement.
- "Reach level 20" -> progression. Every player who plays long enough hits it.
- "Multiclass into every class in one playthrough without using the in-game respec NPC" -> branch. Required a non-default constraint that excludes the usual play pattern.

When a boundary call is non-obvious, record the reasoning in the entry's `notes:` field so future maintainers and the aggregator have the audit trail.

Within each H2, entries are ordered by the game's natural sequence: chapter order for progression, story-beat order for branch, difficulty order for mastery (easier first), platform-list order for collection and threshold, and platform-list order for discovery. This is convention, not contract -- a corpus may reorder within a section when a different order serves the reader better, and document the choice in the entry-level `notes:` field.

## Per-achievement entry format

Each achievement gets one entry under the H2 for its `trigger_type`. Format:

```markdown
### [Achievement name -- verbatim from platform list]

- **id:** [API name from platform if known; else display name slugified]
- **hidden:** [yes | no -- from platform's hidden flag]
- **trigger_type:** [progression | branch | mastery | collection | threshold | discovery -- see "How to classify an achievement into a trigger type" above]
- **genre:** [optional, repeatable. Conventional vocabulary: social | roguelike | mission | multiplayer | meta | class. See Genre vocabulary section below; corpora may add their own values with a one-line definition.]
- **trigger:** [paraphrased trigger condition in maintainer's own words -- never reproduce the platform's description verbatim]
- **missable:** [yes | no | only-on-difficulty | scenario-locked]
- **ponr-window:** [the latest gate / chapter / scenario beat where the trigger is still reachable; "n/a" if not missable]
- **prereqs:** [other achievements, items, story flags, or build states that must be in place first]
- **vector-binding:** [the corpus location where the trigger condition is documented in detail -- e.g. `nav/theatre.md` gate 4, `items/weapons.md` "Lord of War" claim, `paths/order.md` golden-path constraint]
- **enemy-tier:** [0-5]
- **puzzle-tier:** [0-3]
- **spoiler:** [none | progression | late-game | story | dlc:<name>]
- **notes:** [maintainer notes -- common gotchas, contested triggers, boundary calls between trigger types, version-specific bugs. Optional.]
```

**On hidden achievements.** A hidden achievement's *name* may itself be a spoiler. Treat the entry's `enemy-tier` and `puzzle-tier` as gating the entire entry (heading included) for hidden achievements, not just the trigger description. The reader hides the heading entirely at read-time when the player's dials are below the threshold.

**On the developer's description.** Steam, PSN, and Xbox achievement descriptions are publisher IP. Cite the achievement *name* verbatim (it's the lookup key the player types when they see the popup). Paraphrase the trigger condition in your own words. Never reproduce the full developer-authored description text. This is the same posture the framework takes toward all third-party-authored source material: names, identifiers, and short factual labels travel verbatim; descriptive prose is paraphrased.

**On `trigger_type` and the boundary cases.** The six trigger types are universal across the genres the framework has tested against. Most achievements classify cleanly; some sit at the boundary between two types (most often mastery <-> discovery, threshold <-> collection, or progression <-> branch). The "How to classify" section above covers the three disambiguation rules. When a boundary call is non-obvious even after applying those rules, record the reasoning in the entry's `notes:` field so future maintainers and the aggregator have the audit trail.

## Genre vocabulary

The `genre:` field is an optional overlay that tags genre-specific structural patterns the universal `trigger_type` doesn't capture. Conventional values shared across corpora:

- **social** -- NPC relationship, romance, friendship, companion-bond. Strong in RPGs, sims, life-games.
- **roguelike** -- character/ship-bound, run-condition, meta-progression. The roguelike-specific "what unit owns this achievement" structure.
- **mission** -- per-level mastery; achievements bind to individual missions or levels rather than to story beats. Common in stealth-action and arcade-racing games where the level is the unit.
- **multiplayer** -- online, co-op, PvP, server-social interaction. Live-service tag.
- **meta** -- fourth-wall, filesystem-poking, easter-egg, ARG. Used when the achievement's trigger reaches outside the game's diegetic world.
- **class** -- class/subclass-acquisition patterns; achievements bind to the player's class or build identity rather than to story progression.

Corpora may add their own values when none of the conventional values fit. New values get a one-line definition in this section. The reader treats unknown `genre:` values as opaque tags rather than as errors.

[Add corpus-specific genre values here as they're declared.]

## Sources

- [Platform's canonical achievement list URL -- e.g. https://steamcommunity.com/stats/<APPID>/achievements]
- [Mirror used during Stage 0 if the canonical URL was unreachable -- exophase.com, steamhunters.com, truesteamachievements.com, strategywiki.org. Cite the mirror but key the entries off the canonical names.]
- [Per-achievement guide sources cited in individual entries' `vector-binding` references]

## Coverage check (P1 ingestion contract)

End of P1 ingestion, every achievement in the stub list above must be in one of three states:

1. **Resolved** -- a corpus claim somewhere carries this achievement's id as an `achievement:` overlay, and this file's entry has populated all fields above with `status: research-integrated`.
2. **Deferred** -- entry is marked `deferred-to: P3` in its body with a one-line reason (e.g. "DLC-locked; P3 covers DLC content"). The deferral is logged in CHECKPOINT's harness changelog.
3. **Unreachable** -- recorded in `limitations.md` with the achievement name and what blocked research. The entry here stays `status: scaffold` with `deferred-to: limitations`.

Silent scaffold at end of P1 -- an achievement entry with no resolution path -- is the forbidden state. The aggregation file must end P1 with every entry resolved against at least one corpus claim, or with the entry recorded in `limitations.md` as a research gap with the platform list URL as the citation.

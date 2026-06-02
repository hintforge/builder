# Claim Format -- Structured Facts for Aggregation

Every fact in a per-game guide exposes: source, capture method, contributor, confidence, last-verified, two spoiler dials (enemy-tier and puzzle-tier), and a category. This makes prose readable for humans AND parseable by the future aggregator agent (see `../distribution.md`).

**Born-structured beats retrofitted-structured.** Once thousands of facts exist across multiple games, retrofitting metadata is brutal. Apply the convention from claim #1.

## The minimum unit: a claim

A claim is any factual statement that could be wrong. Examples:
- "The keypad code in the lower vault is 4719"
- "The hidden chest in the riverside cottage sits behind the false wall, not in the cellar"
- "The Aegis Talisman costs 60 mana shards to craft"
- "Fire arrows do 2x damage to wooden enemies"

Opinions, recommendations, and tier rankings are **not** claims in this sense -- they're advice / interpretation, no truth-value to aggregate. Don't structure them.

## The convention -- two acceptable formats

Pick whichever reads better for the context.

### Inline (lightweight, for prose-flowing facts)

> The hidden chest in the riverside cottage sits behind the false wall, not in the cellar.
> _source: comrade-7 live observation 2026-03-12 · capture: manual_paste · confidence: high · enemy-tier: 0 · puzzle-tier: 0 · category: mainline · spoiler: none · conflicts: community-wiki page_

The metadata line is italicized and starts with `_source:` -- easy to scan, doesn't break prose flow.

### Block (heavyweight, for high-stakes facts where the metadata is itself worth surfacing)

```
### Code 4719 -- Lower-vault keypad
- **claim:** the keypad in the lower vault opens with `4719`
- **source:** audio log near the corpse, mumbled "four... seven... one nine"
- **capture-method:** manual_paste
- **contributor:** guidekeeper
- **confidence:** medium (mumbles can mislead -- sometimes the audible numbers are a red herring and the real code is on a poster nearby)
- **last-verified:** 2026-03-12
- **enemy-tier:** 0 (no enemy info)
- **puzzle-tier:** 1 (gives the answer to a side puzzle)
- **category:** easter-egg (hidden behind an optional side-objective vault)
- **conflicts-with:** none yet
```

## Field meanings

- **claim** -- the factual statement, exact and testable. Avoid hedging language ("probably", "I think") -- uncertainty goes in `confidence`, not in the claim text.
- **source** -- where it came from. URL is best; in-game observation is acceptable; "vibes" is not. For in-game observations, include what was observed and when. **Always cite the canonical URL** (the one a player would visit) even if the actual capture went through a mirror or archive -- the canonical URL is what the aggregator dedupes against. The capture path is recorded separately in `capture-method`.
- **capture-method** -- how this claim entered the corpus. One of `web_fetch | special_export | mediawiki_parse | breezewiki | archive_ph | manual_paste`. Required at `corpus-core-version: 2`. See [`../ingestion.md`](../ingestion.md) "Blocked-source recovery" for when each rung applies. Default for research-cascade-sourced claims is `web_fetch` (the deep-research tool fetches its own pages); override when the contributor walked the Fandom or Reddit ladder for this claim specifically. Inline-format short form: `capture: <value>`.

  **Value semantics (provenance is load-bearing -- pick the value that names where the bytes actually came from, not a semantically-similar rung):**
  - `web_fetch` -- generic HTTP GET of a canonical URL (Fandom direct, walkthroughs.games, etc.). The deep-research tool's default path.
  - `special_export` -- MediaWiki Special:Export interface, whether via the HTML form (`/wiki/Special:Export/<Page>`) or its `api.php?action=query&export=1` equivalent. Returns wikitext XML. First-party to the wiki being captured.
  - `mediawiki_parse` -- MediaWiki Parse API (`api.php?action=parse&page=<Page>`) on the wiki being captured. Returns rendered HTML. First-party to the wiki, distinct from any third-party front-end. Use this value, not `breezewiki`, when the capture went through the wiki's own Parse API even if a BreezeWiki attempt failed first.
  - `breezewiki` -- third-party BreezeWiki front-end (`breezewiki.com` or a known mirror such as `antifandom.com`, `bw.artemislena.eu`, etc.). Different host, different operator, different ToS surface from the underlying Fandom wiki. Do NOT use this value for captures that ultimately resolved against `<wiki>.fandom.com/api.php` -- those are `mediawiki_parse` (if `action=parse`) or `special_export` (if `action=query&export=1`).
  - `archive_ph` -- archive.ph snapshot of a canonical URL. Use when the original URL is dead, gated, or has changed since the claim was first established and the archive captures the version the claim references.
  - `manual_paste` -- human pasted the content (from a browser, a screenshot OCR, a local game-asset extraction tool like FModel, etc.). Default fallback when none of the above applies.

  An auditor reading these values should be able to trace each value back to an identifiable capture path; the rule is "name the host and interface that actually served the bytes, not the rung the contributor originally tried to walk."
- **contributor** -- who added or last-verified the claim. GitHub identity once published; local handle until then.
- **confidence** -- `high` / `medium` / `low`. Use the binary `verified` / `unverified` if a graded scale is overkill for the project.
- **last-verified** -- date the claim was last re-checked against reality. Stale claims (>1 game version old) flagged for re-verification.
- **enemy-tier** -- `0`-`5`. Minimum enemy-spoiler warning tier (from `warning_tiers.md`) the reader must be at to see this claim. `0` = no enemy info revealed. Higher tiers gate enemy abilities, boss mechanics, late-game roster, etc.
- **puzzle-tier** -- `0`-`3`. Minimum puzzle-spoiler tier the reader must be at. `0` = no puzzle solution revealed (location-only is fine). Higher tiers gate hints, partial solutions, and full answers to puzzles / codes / sequences.
- **category** -- `mainline` | `easter-egg` | `lore`. Defaults to `mainline` if omitted. See "Category and lore opt-in" below.
- **spoiler** -- `none` | `progression` | `late-game` | `story` | `dlc:<name>`. Optional but recommended for any claim originating from a research cascade pass -- the cascade's spoiler-classification sub-agent assigns this tag at ingestion time (see `setup_wizard.md` Step 8 ingestion procedure). The display-time renderer can re-filter against the reader's current dials without re-running research. Tier mapping (the ingestion sub-agent applies this to derive `enemy-tier` / `puzzle-tier`):
  - `none` → tier 0 (mechanics, item names, location names visible from start)
  - `progression` → tier 1 (gated behind early-mid game milestones)
  - `late-game` → tier 2 (boss-room contents, late mechanics, faction-reveal-dependent)
  - `story` → tier 3 (narrative beats, character fates, ending branches)
  - `dlc:<name>` → tier-of-dlc-content + DLC flag (gated independently)
- **conflicts-with** -- other claims this contradicts. If the aggregator sees a conflict, it picks the higher-weighted side and surfaces the alternative.
- **achievement** -- optional, repeatable. The platform's achievement API name when known (e.g. Steam's API name like `NEW_ACHIEVEMENT_1_1` or the developer-set string), or the display name slugified when the API name is unavailable. May appear multiple times on a single claim; comma-separated on the inline form. Presence of this field means: "this claim documents the trigger condition (or a prerequisite) for the named achievement." Added at `corpus-core-version: 4`. See [`achievements_spec.md`](achievements_spec.md) for the universal-core aggregation contract. Inline-format short form: `ach: <id>`.
- **achievement-hidden** -- `yes | no`. Required when `achievement:` is present, otherwise omitted. Surfaces the platform's hidden flag so the reader knows whether to gate the *name* of the achievement, not just the trigger. A hidden achievement's name may itself be a spoiler. Added at `corpus-core-version: 4`.
- **trigger_type** -- one of `progression | branch | mastery | collection | threshold | discovery`. Required when `achievement:` is present, otherwise omitted. The primary trigger classification per the decision questions and disambiguation rules in [`achievements_spec.md`](achievements_spec.md) §4. Multi-achievement claims (where `achievement:` repeats) carry one `trigger_type:` per achievement in the same comma-separated order. Added at `corpus-core-version: 4`.
- **genre** -- optional overlay, repeatable. Open vocabulary, free-form-but-conventional. Tags the achievement with genre-specific structural patterns the universal `trigger_type` doesn't capture. Conventional values: `social | roguelike | mission | multiplayer | meta | class`. Corpora may declare their own values when a genuinely novel pattern appears; new values get a one-line definition in the corpus's `achievements.md` "Genre vocabulary" section. Multiple tags permitted (e.g. `genre: social, multiplayer` for an online co-op friendship achievement). Added at `corpus-core-version: 4`.
- **entity** -- optional, repeatable. Names the subject the claim is about: a specific NPC, faction, crew role, or reputation track (e.g. `entity: companion_a`, `entity: faction_north`). Presence of this field means "this claim concerns the named entity"; the claim still routes to its primary vector destination (per [`../ingestion.md`](../ingestion.md) Step 4), and the entity overlay also aggregates the claim into the per-entity file under a class folder (`npcs/<id>.md`, `factions/<id>.md`, `crew/<role>.md`, `reputation/<track>.md`). Aggregation contract in [`../ingestion.md`](../ingestion.md) Step 8. The named-individual rule below decides when this field applies. Added at `corpus-core-version: 5`. Inline-format short form: `ent: <id>`.
- **entity-hidden** -- `yes | no`. Optional; defaults to `no` when `entity:` is present. Surfaces a per-entity hidden flag so the reader knows whether the *name* of the entity is itself a spoiler (secret companions, late-reveal factions, hidden romance tracks). Parallels `achievement-hidden:`. The renderer gates the heading and name below the appropriate tier; the integrator writes the content in full regardless of current tier per the "write content, gate display" rule. Added at `corpus-core-version: 5`.
- **entity-status** -- one of `hostile | friendly | convertible | party | neutral | unspecified`. Required when the entity's class folder is `npcs/`; optional for `factions/`, `crew/`, `reputation/` (defaults to `unspecified`). The status describes the relationship state at the point of the claim, not a permanent identity. Values:
  - `hostile` -- the NPC fights the player; combat content is the primary surface. Named hostile NPCs aggregate to `npcs/<id>.md`; generic-mob combat content continues to route via the `enemy` vector to `mechanics.md` (the two are orthogonal -- vector handles generic combat, overlay handles named-NPC aggregation).
  - `friendly` -- non-combat interaction (questgivers, merchants, narrative NPCs).
  - `convertible` -- status can change during play (recruitable-enemy pattern). Pre-conversion combat claims and post-conversion party claims aggregate into the SAME entity file; the convertibility is the entity's defining property, not the current state.
  - `party` -- currently recruited; capability/build/quest content is the primary surface. Companions who betray and leave keep `party` as the file-defining status and gain a status-history entry rather than a file relocation.
  - `neutral` -- state-machine NPC the player shifts (reputation tracks, romance tracks, alignment-sensitive interactions).
  - `unspecified` -- default fallback for non-individual classes (factions, crew, abstract reputations).

  Added at `corpus-core-version: 5`.

### When `entity:` applies -- the named-individual rule

The framework needs a rule for when a combat NPC gets its own `npcs/<id>.md` file vs when it stays generic and routes via the `enemy` vector to `mechanics.md`. Without a rule, ingestion makes the call inconsistently and the same encounter can land in two different shapes across phases.

**The rule:** an NPC is named-individual (gets `entity: <id>`) if and only if the corpus would benefit from a per-entity file. The test is "would a player ever ask 'tell me about <name>' as a standalone question," not "does the entity have a proper noun."

Worked cases:

- **Recurring named companion or recurring named antagonist.** Named, returns across multiple zones/chapters, player tracks them by name across sessions. Named-individual. Gets `npcs/<id>.md` with `entity-status: party` (or `convertible`, depending on the mechanic).
- **Single-encounter named boss significant enough to remember by name.** Named, one-encounter, but the encounter carries enough mechanical or narrative weight that players reliably ask about it by name. Named-individual. Gets `npcs/<id>.md` with `entity-status: hostile`.
- **Named-but-forgettable role-NPC** (e.g. "the squad leader at the third checkpoint encounter"). Has a role, has dialogue, has no retainable name. Generic. Routes via `enemy` vector to `mechanics.md`; no entity overlay.
- **Procedurally-named NPCs in roguelikes.** The role is what the player tracks across runs; the name is ephemeral. Route to the `crew/` class (role-aggregated), not `npcs/` (individual-aggregated). Same NPC type across runs aggregates as one role file.
- **Generic mobs** (grunts, mooks, environmental hazards-with-HP). Never named-individual, regardless of whether the species carries a proper-noun in-fiction designation. A species name is a mob type; it routes via `enemy` vector to `mechanics.md`, no entity overlay.

The maintainer judgment call sits at the boundary between single-encounter named bosses and named-but-forgettable encounters. Disambiguation rule: if research surfaced the encounter as worth a paragraph of strategy detail, the player will probably ask about it by name -- promote to named-individual. If the encounter shows up in one line of a chapter walkthrough with no follow-on detail, leave it generic.

### Category and lore opt-in

`mainline` claims are visible to any reader past the spoiler dials. `easter-egg` claims cover hidden / optional / side-objective content and are visible by default but tagged so the aggregator can group them. `lore` claims (worldbuilding, codex entries, narrative backstory not required for play) are **hidden by default** -- the reader must explicitly opt in (e.g., "show me the lore stuff") before the renderer surfaces them. Authors don't need to set `category: mainline` explicitly; it's the default.

Optional fields once distribution ships:
- **game-version** -- which patch/version this was verified against (e.g. `1.5.0`, `pre-DLC2`, `post-launch-patch-2`).
- **platform** -- if the claim is platform-specific (e.g. PC-only mod compatibility).

## What the aggregator will do (preview -- not built yet)

When multiple contributors push claims about the same fact:
1. Group claims by topic (the slug / heading they're attached to).
2. Compare evidence weights: live in-game observation > known wiki > social media > vibes.
3. Compare contributor track records (claims they made that survived contradiction).
4. Compute percentage-of-truth: e.g. "5 of 7 contributors say `4719`; 2 say `0719` -- surface `4719` as canonical, `0719` as conflict, with confidence delta."
5. Tag the canonical claim with consensus metadata.
6. Filter rendered output by reader's enemy-tier and puzzle-tier independently -- claims above either dial are hidden entirely. `category: lore` claims are hidden unless the reader opts in.

The aggregator does NOT do this today. The convention exists now so claims born in early per-game guides can be aggregated when the aggregator ships.

## Why prose still works for the reader

A reader doesn't need to see metadata to use the guide. The aggregator parses metadata; the reader reads prose. Both can coexist -- markdown footnotes / italics / blockquotes hide structure cleanly. A static-site renderer (planned) can strip metadata entirely, leaving only the prose claim.

## When NOT to add claim metadata

- **Persona-flavored intros / outros** -- voice, not facts.
- **Hint-ladder Lvl 1 nudges** -- interpretive, not factual ("look at the floor pattern" isn't falsifiable).
- **Section overviews** -- descriptive, not falsifiable.
- **Build recommendations** -- opinion, not claim ("the Iron Mace is the best melee weapon" -- that's a community-consensus tier ranking, not a verifiable fact).
- **Workflow / procedural advice** -- "open the wheel with Tab" is platform doc, not a claim worth aggregating.

When in doubt: **if the claim could be falsified by another contributor's observation, structure it.** Otherwise, prose is fine.

## Evolution

This is v5 of the convention (`corpus-core-version: 5`). v5 adds three claim-level overlay fields for named-entity aggregation: `entity:` (optional, repeatable, names the subject the claim is about; aggregates into per-entity files under class folders such as `npcs/`, `factions/`, `crew/`, `reputation/` while the claim itself still routes to its primary vector destination), `entity-hidden:` (`yes | no`, optional; surfaces a hidden flag so the renderer can gate the entity's name itself, parallel to `achievement-hidden:`), and `entity-status:` (one of `hostile | friendly | convertible | party | neutral | unspecified`; required when the class is `npcs/`, optional for the parallel non-individual classes). v5 also retires the half-broken `enemies/` folder: v4 corpora migrating to v5 rename `enemies/` to `npcs/` and annotate existing content with `entity-status: hostile` at first touch; new v5 corpora skip `enemies/` entirely. Generic-mob combat content continues to route via the `enemy` vector to `mechanics.md`, unchanged -- the `enemy` vector and the `npcs/` entity class are orthogonal axes. Class-folder scaffolding is driven by Stage 0 §5 NPC/faction/crew/reputation density signals in [`../setup_wizard.md`](../setup_wizard.md) Step 6.7, and late-emerging classes are scaffolded at ingestion time per [`../ingestion.md`](../ingestion.md) Step 2.5. v4 added four claim-level fields covering platform achievement coverage: `achievement:` (optional, repeatable, names a platform achievement this claim documents the trigger for), `achievement-hidden:` (required when `achievement:` is present; surfaces the platform's hidden flag), `trigger_type:` (required when `achievement:` is present; one of `progression | branch | mastery | collection | threshold | discovery` per the decision questions in [`achievements_spec.md`](achievements_spec.md) §4), and `genre:` (optional, repeatable, open-vocabulary overlay for genre-specific structural patterns). v4 also added the universal-core aggregation file `achievements.md` at corpus root -- see [`achievements.md`](achievements.md) and [`achievements_spec.md`](achievements_spec.md). v3 added three required manifest-level fields in `nav/architecture.md`'s `## Hintforge manifest` block -- `game-version`, `game-version-platform`, `game-version-as-of` -- captured from the player at setup and surfaced by the reader at session start as a drift-detection prompt. v3 did NOT change the per-claim format; the per-claim `game-version` and `platform` fields documented further down in this file remain optional and continue to serve their existing per-claim purpose. v2 added the required per-claim `capture-method` field; v1 corpora predate both. A v5-capable reader handles v1-v4 corpora by silently skipping the fields they don't carry (no warning -- v1 through v4 stay inside the supported range during the catch-up window). Likely future revisions once an aggregator parses real claims:
- Confidence scale (binary vs. graded, or numeric 0.0-1.0)
- Conflict format (free-text vs. ID references)
- Contributor identity scheme (GitHub username vs. signed cryptographic identity)
- Game-version tagging granularity
- ~~Spoiler-tier sub-fields (enemy-tier vs. puzzle-tier vs. story-tier)~~ -- resolved in v1: split into independent `enemy-tier` (0-5) and `puzzle-tier` (0-3) dials, plus a `category` field (`mainline | easter-egg | lore`). Now canonical, see above.
- ~~Capture-method audit-trail~~ -- resolved in v2: required `capture-method` field with value vocabulary `web_fetch | special_export | mediawiki_parse | breezewiki | archive_ph | manual_paste`. Now canonical, see above. (`mediawiki_parse` added 2026-05-20 same-day-as-v2-launch after a corpus backfill surfaced a provenance-labeling problem: the MediaWiki Parse API and BreezeWiki are different rungs and need different values; conflating them is dishonest. Additive vocab change, no corpus-core-version bump needed -- v2 readers handle the new value transparently since they don't validate against a fixed enum.)

When revising, propose changes via PR and propagate to existing per-game guides.

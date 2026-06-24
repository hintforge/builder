# Hintforge corpus format

This document specifies the on-disk shape of a Hintforge corpus -- the contract between the **builder** (which produces corpora) and the **reader** (which consumes them at runtime). It is an internal reference for framework maintainers and future contributors; end users never read it. They run the builder, which produces the right shape automatically, and run the reader, which expects that shape automatically.

The format has three normative layers: a **universal core** that every corpus has, a set of **vector extensions** that vary by game, and a **runtime discovery mechanism** that lets the reader figure out which extensions exist in the current corpus.

## 1. Universal core

A directory is a Hintforge corpus if and only if it contains the four universal published directories and nine universal files listed below. The reader can assume every corpus has these and route to them by name. (For cheap corpus *detection* the reader checks only a subset of always-present markers rather than all nine -- see the reader skill's session-start step 1 -- but the full set below is what a complete corpus carries. This document is the authority for the universal-file list; the reader's detection subset points back here.)

**No platform-branded file is required.** As of `corpus-core-version: 6` the required set carries no file named after any one agent host. A corpus authored and consumed entirely outside Claude Code is a valid corpus with no `CLAUDE.md`. See the v6 history note in §3 and "Optional host shims" below.

**Universal directories** (always present, always populated unless the game genuinely lacks content for them):

| Directory | Purpose |
|---|---|
| `nav/` | Per-zone routing files plus the architecture-level `architecture.md` (zone graph, optional content registry, support topology, locks-and-keys, vector list). Source of truth for routing (Rule 1), lookahead (Rule 2), backtrack (Rule 3), reachability (Rule 4), and locks (Rule 5). |
| `items/` | Item index plus per-item or per-category files (weapons, consumables, crafting materials, etc.). |
| `sections/` | Per-chapter or per-region narrative-walkthrough files. Lookup target for "what happens in section X?" |
| `_overflow/` | Catch-all for content that doesn't fit cleanly elsewhere. May be empty. **Scaffold status is permitted at distribution time** because `_overflow/` is a runtime catch-all, not a research target -- content accumulates here during live play when players encounter content that doesn't fit other folders, not during research ingestion. The no-silent-scaffold rule in [`../ingestion.md`](../ingestion.md) step 8 exempts `_overflow/` for this reason. |

**Universal files** (always present at the corpus root):

| File | Purpose |
|---|---|
| `CHECKPOINT.md` | Live session state: `player_position` block (current zone, last gate, confidence, last updated), spoiler-dial settings, open threads, phase tracking. Reader reads at session start; updates on every position update. |
| `controls.md` | Game's control scheme; lookup target for "what button does X?". |
| `settings.md` | Game's in-engine settings menu structure mirrored verbatim from the game (NOT industry-category labels). |
| `mechanics.md` | Game systems and rules that operate independently of any specific zone, item, or chapter -- stat tracking, dialogue weight, stamina, fling physics, turret detection, ship power allocation, affinity counters, NG+ modifiers. Single file at root, same shape as `controls.md` and `settings.md`. For narrative-only games with no systems-level mechanics, ships with an explicit one-line statement ("no system-level mechanics -- pure narrative; routing/locks/keys live in `nav/architecture.md`") at `status: research-integrated` so the reader gets a definite answer rather than treating it as absent. **Optional split:** if the file grows unwieldy in a systems-heavy game, the maintainer can convert it to a `mechanics/` subdirectory (`mechanics/index.md` + per-system siblings). This is an opt-in split, not a default -- same pattern as `items/`, which doesn't require sub-files unless content depth warrants. |
| `limitations.md` | Blocked sources, rejected sources, known research gaps. |
| `warning_tiers.md` | Per-game enemy-tier (0-5) and puzzle-tier (0-3) definitions plus the breach log. |
| `persona.md` | Voice cast for the game-specific persona (cast names, examples, toggle phrases). The voice-agnostic, game-agnostic discipline lives in the reader skill's `persona_universal.md` -- this file declares the cast the discipline applies to. |
| `dependencies.md` | Cross-system edges written by the stitch pass (e.g. "this puzzle solution requires an item from a later zone"). Ships at status `scaffold` from the builder template; populated by stitch and reconciled by zipper. Reader treats scaffold-status as absent per the §6 status discipline. |
| `achievements.md` | Per-`trigger_type` aggregation of the game's platform achievement list (Steam / PSN / Xbox), bound back to canonical claim homes via `vector-binding`. Required as of `corpus-core-version: 4`. Wizard creates the scaffold from the Stage 0 stub fetch; P1 ingestion classifies each entry into one of six `trigger_type` sections (`Progression | Branch | Mastery | Collection | Threshold | Discovery`) and writes a coverage check against `research_briefs/achievement_stubs.md`. See [`../templates/achievements.md`](../templates/achievements.md). |

**Optional host shims (not required, not part of the universal core).** A corpus MAY carry thin per-platform auto-load files that an agent host reads on entry and that do nothing but point at the reader skill: `CLAUDE.md` (Claude Code), `AGENTS.md` (Codex CLI / OpenClaw). They are **optional** -- a corpus is valid with neither, one, or both. They carry **no unique corpus data**: an identity line + "this is a Hintforge corpus, load the hintforge-reader skill" + pointers to the neutral homes where the real content lives (`warning_tiers.md`, `persona.md`, the manifest, the reader skill's `principles.md`). The reader does not require them for detection and does not read them by name as corpus data. Before v6, `CLAUDE.md` was a *required* universal-core file carrying per-game harness rules; v6 dissolved that role and relocated its content to the neutral homes (see §3 history). On v1-v5 corpora the reader still reads a present `CLAUDE.md` as the harness file (back-compat).

**Excluded from the published corpus by definition.** These exist in some directories on disk during authoring or runtime, but are not part of the corpus format and the reader does not look for them:

- **Builder-only paths:** `research_briefs/`, `research_inbox/` (including its `p1/`, `p2/`, ..., `_processed/` subfolders). These are scratch space the builder uses while authoring.
- **Platform/runtime paths:** `ptt/`, `save_state/`, `.claude/`. These are local runtime infrastructure, not corpus content.

A reader scanning a directory for "is this a corpus?" checks the universal directories and files. The presence of builder-only or platform/runtime paths does not affect the answer.

## 2. Vector extensions

In addition to the universal core, a corpus may carry one or more **vector extensions** -- top-level directories whose presence depends on the game's content shape. These are not universal: a narrative-only game has no `npcs/`; a linear puzzle game has no `optional_zones/`. Forcing every corpus to ship every extension as an empty folder is unworkable, so the builder creates only the extensions the game needs (decided at setup-wizard time from game-type answers) and the reader discovers them at runtime.

**Canonical vector extensions (broadly applicable across observed game types).** These are the wizard's standard vocabulary; the setup wizard's Step 7 conditionally creates each based on Stage 0 game-type classification and user confirmation. At `corpus-core-version: 5` and later, the entity-class extensions (`npcs/`, `factions/`, `crew/`, `reputation/`) are auto-populated by ingestion from claims carrying an `entity:` overlay.

| Extension | Used when | Example game types |
|---|---|---|
| `puzzles/` | Game has discrete puzzles with hint ladders and solutions | Puzzle-platformers, immersive sims with discrete puzzles |
| `npcs/` (v5+) | Game has named individual NPCs worth aggregating per-entity (any `entity-status`: hostile, friendly, convertible, party, neutral). At v5 this replaces the legacy `enemies/` folder; generic-mob combat content continues to route via the `enemy` vector to `mechanics.md` (no folder needed). | CRPGs, JRPGs, party-driven action-RPGs |
| `factions/` (v5+) | Game has group entities the player has an ongoing relationship with | Faction-driven RPGs, 4X games, strategy games with diplomacy |
| `crew/` (v5+) | Game has role-aggregated entities (run-bound or party-bound) where individual identity is ephemeral but the role persists | Run-based roguelikes with persistent role slots, ship-crew sims |
| `reputation/` (v5+) | Game carries enough reputation-track / alignment content to warrant its own aggregation surface separate from `factions/` | Multi-faction-reputation RPGs, alignment-sensitive immersive sims |
| `endings/` | Game has multiple endings worth indexing separately | Branching-narrative games with multiple endings |
| `paths/` | Game has branching narrative paths worth indexing | Branching-narrative games |
| `optional_zones/` | Open-world game with side content keyed to zones | Open-world action/adventure games |
| `mechanics/` | Systems-heavy game where `mechanics.md` outgrows a single file (opt-in split, not a default) | Systems-heavy tactics/strategy games |

**Corpus-declared extensions (one-off shapes).** Beyond the canonical set, a corpus may declare extensions specific to its own game's shape. These are not wizard-supported -- the maintainer creates the folder manually and lists it in `architecture.md`. The reader treats them as unknown-semantic vector extensions per §3. Example: a corpus might declare `testing_grounds/` for a game's isolated challenge spaces, distinct enough from `optional_zones/` content to warrant their own folder but too game-specific to belong in the canonical list.

The canonical list above reflects what has been observed as broadly applicable across multiple game corpora spanning distinct game types. New canonical entries are added only when a vector shape proves broadly applicable across multiple game types, not on the first observation.

**File counts vary by more than an order of magnitude across vectors and games.** `nav/` ranges from a couple of files to several dozen; `puzzles/` ranges from zero to a dozen-plus. The reader must handle empty-or-near-empty universal-core folders and variable populations within extensions.

## 3. Runtime discovery mechanism

Because the vector-extension set varies per corpus, the reader cannot enumerate them in its body. It discovers them at session start using a two-tier mechanism:

**Primary: vector list in `nav/architecture.md`.** The corpus's `architecture.md` carries a `Vector extensions` section listing the extension folders this corpus uses and a one-line semantic for each. Format:

```markdown
## Vector extensions

- `puzzles/` -- discrete puzzle files with hint ladders, indexed by `puzzles/index.md`
- `npcs/` -- named individual NPCs (any `entity-status`), indexed by `npcs/index.md`
- `optional_zones/` -- side content keyed to parent zone IDs from the zone graph
```

The reader reads this section at session start, registers each extension and its semantic, and routes topical questions accordingly.

**Fallback: filesystem listing.** If `architecture.md` has no `Vector extensions` section (corpus is mid-construction, or the maintainer hasn't populated the list), the reader lists top-level directories in the corpus, excludes the four universal-core directories (`nav/`, `items/`, `sections/`, `_overflow/`) plus the optional `mechanics/` split directory if present, and known platform/runtime directories (`ptt/`, `save_state/`, `.claude/`), and treats the remainder as vector extensions with unknown semantics. The reader still routes to them on best-guess name matching but flags the missing manifest to the maintainer.

**Mismatch tolerance.** When the manifest lists an extension but the folder is absent (or vice versa), the reader logs a diagnostic and prefers what is actually on disk. Manifest drift is a maintenance bug, not a runtime failure.

### Versioning

`corpus-core-version` is an integer stamped in the `## Hintforge manifest` block of `nav/architecture.md`. It increments only when a change to this document (`docs/corpus-format.md`) would break an older reader -- new required fields, removed fields, renamed fields, or any change to the universal-core directory/file set that the reader hard-codes. New vector extensions, new content within existing files, persona iteration, prose edits, and other non-format-breaking work do not bump the version.

**Version history:**

- **v1** -- initial published format (Phase 3 launch). Universal core of four directories and nine files; claim fields `claim`, `source`, `contributor`, `confidence`, `last-verified`, `enemy-tier`, `puzzle-tier`, `category`; optional `spoiler`, `conflicts-with`, `game-version`, `platform`.
- **v2** -- adds required `capture-method` field on every claim (value vocabulary `web_fetch | special_export | breezewiki | archive_ph | manual_paste`); adds the "Blocked-source recovery" section to [`../ingestion.md`](../ingestion.md) defining the Fandom and Reddit ladders the field records. A v2-capable reader keeps `MIN_SUPPORTED_CORE: 1` so v1 corpora read cleanly without a warning (the reader silently skips `capture-method` lookups on them). Old v1 readers that hard-coded `MAX_SUPPORTED_CORE: 1`, by contrast, will see a v2 corpus as outside their range and fire the "newer Hintforge format than I fully understand" session-start warning per `SKILL.md`'s mismatch-behavior rules; the maintainer's path forward is to update the reader skill. See the reader's `MIN_SUPPORTED_CORE`/`MAX_SUPPORTED_CORE` constants for which versions a given reader accepts.
- **v3** -- adds three required manifest fields in the `## Hintforge manifest` block of `nav/architecture.md`: `game-version` (freeform version string the player named at setup -- semver, patch name, or build number; whatever the game actually ships), `game-version-platform` (the platform the player is on -- e.g. `PC / Steam`, `PS5`, `Switch`; required for every corpus, including single-platform-today games, because games frequently expand to additional platforms post-launch and the corpus must declare which platform it was authored against from day one), and `game-version-as-of` (`YYYY-MM-DD` -- the date the corpus was last reconciled against that game-version+platform pair; drifts independently of the top-of-file `last_reconciled` since corpus refreshes can happen without a game patch, and patches can ship without a corpus refresh). The wizard captures all three at setup (new prompt block in [`../setup_wizard.md`](../setup_wizard.md) Step 1) and stamps them into the manifest. The manifest is a **build-time snapshot**: the reader surfaces these values at session start so the player can react to drift, and may periodically ask the player to reconfirm, but **the reader never updates the manifest** -- corpus rev-bumps remain a builder-side action. A v3-capable reader keeps `MIN_SUPPORTED_CORE: 1` so v1 and v2 corpora read without a warning (the reader treats missing game-version-* fields on v1/v2 corpora as "version unknown, no surface" rather than as an error). Old v2 readers that hard-coded `MAX_SUPPORTED_CORE: 2` will fire the newer-format warning on v3 corpora; the maintainer's path forward is to update the reader skill.
- **v4** -- adds the universal-core file `achievements.md` at corpus root and the optional claim-level overlay fields `achievement:` (repeatable), `achievement-hidden:` (required when `achievement:` is present), `trigger_type:` (required when `achievement:` is present; one of six values `progression | branch | mastery | collection | threshold | discovery`), and `genre:` (optional, repeatable, open vocabulary). The wizard captures the achievement stub list at Stage 0 (new sub-step in [`../setup_wizard.md`](../setup_wizard.md) Step 6.7) and writes it to `achievements.md`'s scaffold body as a flat list; P1 ingestion classifies each entry's `trigger_type` per the decision questions in [`../ingestion.md`](../ingestion.md) step 8 and reorganizes the file into the six trigger-type sections. A v4-capable reader keeps `MIN_SUPPORTED_CORE: 1` so v1-v3 corpora read cleanly (missing `achievements.md` treated as "no achievement tracking in this corpus" rather than as an error). Old v3 readers that hard-coded `MAX_SUPPORTED_CORE: 3` will fire the newer-format warning on v4 corpora; the maintainer's path forward is to update the reader skill.
- **v5** -- adds the optional claim-level overlay fields `entity:` (repeatable, names the subject the claim is about), `entity-hidden:` (`yes | no`, optional; gates the entity's name itself at read-time the way `achievement-hidden:` does for achievements), and `entity-status:` (one of `hostile | friendly | convertible | party | neutral | unspecified`; required when the entity's class folder is `npcs/`, optional for `factions/`, `crew/`, `reputation/`). Adds a per-class aggregation contract: claims carrying an `entity:` overlay route to their primary-vector destination AND aggregate into `<class>/<entity-id>.md` (one file per entity, under a class folder such as `npcs/`, `factions/`, `crew/`, or `reputation/`). The wizard surfaces NPC, faction, crew, and reputation density signals at Stage 0 (new sub-bullets in [`../setup_wizard.md`](../setup_wizard.md) Step 6.7) and auto-pops the relevant class folders at Step 7; late-emerging classes are scaffolded at ingestion time per [`../ingestion.md`](../ingestion.md) step 2.5. v5 also retires the half-broken `enemies/` folder: v4 corpora migrating to v5 rename `enemies/` to `npcs/` and annotate existing content with `entity-status: hostile` at first touch (mechanical, one-time); new v5 corpora skip `enemies/` entirely. The `enemy` vector continues to route generic-mob combat content to `mechanics.md` -- the `enemy` vector and the `npcs/` class are orthogonal axes (vector handles generic combat structure; entity overlay handles named-NPC aggregation). A v5-capable reader keeps `MIN_SUPPORTED_CORE: 1` so v1-v4 corpora read cleanly (missing class folders treated as "no entity aggregation in this corpus" rather than as an error). Old v4 readers that hard-coded `MAX_SUPPORTED_CORE: 4` will fire the newer-format warning on v5 corpora; the maintainer's path forward is to update the reader skill.
- **v6** -- removes the per-game `CLAUDE.md` from the universal-core file set (universal core drops from ten files to nine). `CLAUDE.md` was a platform-branded required file whose content was redundant with neutral homes; its required-data-carrier role dissolves and `CLAUDE.md`/`AGENTS.md` become **optional** per-platform auto-load shims (see "Optional host shims" in §1). Per-game harness facts relocate to homes that already hold them: platform is the `game-version-platform` manifest field (v3), persona default is `persona.md`, per-game spoiler-tier semantics are `warning_tiers.md`, and spoiler/hint/cite discipline is reader-side (`principles.md` / `persona_universal.md`). No new required file is introduced. A v6-capable reader keeps `MIN_SUPPORTED_CORE: 1`: on v1-v5 corpora it still reads a present `CLAUDE.md` as the harness file, and on v6 corpora it neither requires nor reads one (it sources those facts from the neutral homes). The reader also drops `CLAUDE.md` from its cheap corpus-detection marker set -- back-compatible across all versions, since the remaining always-present markers (`CHECKPOINT.md`, `controls.md`, `settings.md`, `limitations.md`, `warning_tiers.md`) appear in every version. Old v5 readers that hard-coded `MAX_SUPPORTED_CORE: 5` will fire the newer-format warning on v6 corpora; the maintainer's path forward is to update the reader skill. **Migration (doctor Branch A):** for an existing v1-v5 corpus, relocate any unique `CLAUDE.md` content to the neutral homes above, convert `CLAUDE.md` to the optional shim shape, and optionally add an `AGENTS.md` twin; the per-version migration steps live in `CHANGELOG.md`.

## 4. Claim format

Every fact in a corpus that could be falsified is structured as a **claim** with metadata. This makes prose readable by humans AND parseable by the future aggregator agent. Two acceptable formats: **inline** (italicized metadata line beneath the prose claim) and **block** (heading + bullet metadata) -- pick whichever reads better.

**Required fields:**

- `claim` -- the factual statement, exact and testable. Uncertainty goes in `confidence`, not in the claim text.
- `source` -- where it came from. URL preferred; in-game observation acceptable. Cite the canonical URL even when the actual capture path went through a mirror or archive -- the canonical URL is what the aggregator dedupes against.
- `capture-method` -- how this claim entered the corpus. One of `web_fetch | special_export | breezewiki | archive_ph | manual_paste`. New required field as of `corpus-core-version: 2`. The value vocabulary maps to the rungs of the Fandom and Reddit recovery ladders in [`../ingestion.md`](../ingestion.md); `web_fetch` is the default for research-cascade-sourced claims that did not need a ladder. Inline-format short form: `capture: <value>`.
- `contributor` -- who added or last-verified.
- `confidence` -- `high` / `medium` / `low`.
- `last-verified` -- date the claim was last re-checked against reality.
- `enemy-tier` -- `0`-`5`. Minimum enemy-spoiler tier required to see this claim.
- `puzzle-tier` -- `0`-`3`. Minimum puzzle-spoiler tier required to see this claim.
- `category` -- `mainline` | `easter-egg` | `lore`. Defaults to `mainline`.

**Recommended:**

- `spoiler` -- `none` | `progression` | `late-game` | `story` | `dlc:<name>`. The ingestion sub-agent assigns this tag and derives `enemy-tier` / `puzzle-tier` from it via:
  - `none` → tier 0
  - `progression` → tier 1
  - `late-game` → tier 2
  - `story` → tier 3
  - `dlc:<name>` → tier of DLC content + DLC flag

**Optional (post-distribution):**

- `conflicts-with` -- other claims this contradicts.
- `game-version` -- patch/version verified against.
- `platform` -- platform-specific notes.

**Achievement overlay (`corpus-core-version: 4` and later):**

- `achievement` -- optional, repeatable. Platform achievement API name when known, display name slugified otherwise. Presence binds this claim to the named achievement as the trigger or a prerequisite. Aggregated up into [`../templates/achievements.md`](../templates/achievements.md) at corpus root via `vector-binding`.
- `achievement-hidden` -- `yes | no`. Required when `achievement:` is present. Surfaces the platform's hidden flag; a hidden achievement's name may itself be a spoiler.
- `trigger_type` -- one of `progression | branch | mastery | collection | threshold | discovery`. Required when `achievement:` is present. Decision questions and disambiguation rules at category boundaries live in [`../ingestion.md`](../ingestion.md) step 8.
- `genre` -- optional, repeatable. Open-vocabulary overlay; conventional values `social | roguelike | mission | multiplayer | meta | class`. Corpora may declare their own values with a one-line definition in their `achievements.md` "Genre vocabulary" section.

Opinions, recommendations, tier rankings, hint-ladder Lvl 1 nudges, section overviews, and procedural advice are **not** claims and should not carry metadata. Prose is fine.

The authoritative working version of this convention lives at [`templates/claim_format.md`](../templates/claim_format.md).

## 5. Architecture-level structures

`nav/architecture.md` is the corpus's structural spine. It carries five primitives the reader depends on:

1. **Zone graph** -- nodes (zones) and edges (transitions). Each edge has `type` (`story-gate | one-way | optional | hub-spoke | fast-travel | conditional`), `direction` (`bidirectional | one-way src→tgt`), `condition`, `point_of_no_return` (`none | permanent | chapter-bound | missable-trigger | point-of-divergence`), and notes. Also includes a **game-type label**, **localization-mechanism class**, **entry node**, **hub nodes**, and **source-language set**.
2. **Chapter ↔ zone mapping** -- links narrative structure to spatial structure.
3. **Optional content registry** -- table of optional content (items, quests, challenges) with unlock condition, access window, parent zone, recommended chapter, failure mode.
4. **Support topology** -- connections between hub zones and the services they offer (vendors, fast-travel, save points, upgrade stations).
5. **Locks-and-keys** -- table mapping every lockable element to the key item that opens it, plus a `lock_visible_before_key` flag for Rule 5 notifications.

Plus the **vector list** described in §3.

The authoritative template lives at [`templates/architecture.md`](../templates/architecture.md).

## 6. Status field and update discipline

Every per-zone file (and every claim-bearing file produced by ingestion) carries a `status` field at the top with one of these values:

- `scaffold` -- placeholder, no substantive content yet. The reader treats scaffolds as "not yet researched" and falls through to web search for the topic.
- `research-integrated` -- content populated from a research cascade pass.
- `live-observed` -- content corrected from live play observation (highest authority).
- `reconciled` -- multiple sources merged with conflicts resolved.

The reader uses `status` to decide whether to answer from the file or fall through to web search. A file with `status: scaffold` and no substantive content is treated as if absent.

**Update discipline.** Live observation > research cascade > web search. When live play contradicts a research-integrated file, the live observation wins and the status moves to `live-observed`. Stitch-and-zipper passes (post-ingestion synthesis) may move a file from `research-integrated` or `live-observed` to `reconciled` once cross-system edges are written and conflicts resolved.

## 7. Spoiler tier annotation syntax

Beyond the per-claim `enemy-tier` / `puzzle-tier` fields, file-level spoiler annotation appears at the top of any file whose **entire** contents sit above a particular tier (e.g., a boss-strategy file that should be invisible at tier 0). Format:

```markdown
---
min-enemy-tier: 2
min-puzzle-tier: 0
---
```

The reader checks this header before routing to the file. If the reader's current dials are below the minimums, the file is treated as if it does not exist for that session.

Per-game `warning_tiers.md` defines what each tier number means for that game's specific enemy roster and puzzle catalog.

The authoritative template lives at [`templates/warning_tiers.md`](../templates/warning_tiers.md).

## 8. Where this document lives

This file is `docs/corpus-format.md` inside the **builder** repo. The builder is what produces the format, so the format spec lives with the producer. The [reader repo](https://github.com/hintforge/reader) links here for anyone who wants the detail. There is no separate corpus-format repo; an internal contract reference with no end-user audience does not warrant one.

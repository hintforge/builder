# Context: Hintforge glossary

Plain-language definitions for the project-specific vocabulary. This is a glossary, not a specification -- for the on-disk format contract, see [`docs/corpus-format.md`](docs/corpus-format.md); for the runtime behavior, see the [`hintforge/reader`](https://github.com/hintforge/reader) skill.

## Core concepts

- **Corpus.** A single game's guide. A folder of markdown files in Hintforge format. Produced by the builder, consumed by the reader.
- **Universal core.** The four directories (`nav/`, `items/`, `sections/`, `_overflow/`) and nine files (`CHECKPOINT.md`, `controls.md`, `settings.md`, `mechanics.md`, `limitations.md`, `warning_tiers.md`, `persona.md`, `dependencies.md`, `achievements.md`) that every corpus has, regardless of game type. The reader can assume these exist (some -- `dependencies.md`, `_overflow/` -- may ship at status `scaffold`). A corpus may *also* carry optional `CLAUDE.md` / `AGENTS.md` platform auto-load shims (thin pointers to the reader skill), but those are not required and not part of the core -- since `corpus-core-version: 6` the per-game `CLAUDE.md` is no longer a required file.
- **Vector extension.** A per-game-type folder added on top of the universal core: `puzzles/`, `npcs/`, `factions/`, `crew/`, `reputation/`, `endings/`, `paths/`, `optional_zones/`, `mechanics/`. A corpus declares which extensions it carries in `architecture.md`'s manifest section; the reader discovers them at session start. At `corpus-core-version: 5` and later, `npcs/` / `factions/` / `crew/` / `reputation/` are auto-populated by ingestion from claims carrying an `entity:` overlay; at v4 and earlier, the (now-retired) `enemies/` folder served a similar role for named hostile NPCs.
- **Manifest.** The `## Hintforge manifest` section in `architecture.md` declaring `corpus-core-version` and `vector-extensions:`. Tells the reader what format era and shape the corpus is in.
- **`corpus-core-version`.** A single integer the corpus declares; bumped only when a universal-core change would break an older reader. The reader warns once and proceeds on mismatch.

## Authoring vocabulary

- **Research cascade.** The phased research plan (P1, P2, ..., P<N>) the builder generates and the author executes. Each phase fills a different slice of the corpus.
- **Research brief.** A self-contained prompt the builder writes to `<game>/research_brief.txt` (or a per-phase variant). The author hands it to an external research agent and drops the result into `research_inbox/p<N>/`.
- **Ingestion.** The procedure that takes raw research results out of `research_inbox/` and distributes them into corpus files with source-tagged metadata, updating status fields and moving processed briefs to `_processed/`.
- **Stitch.** A post-ingestion synthesis pass that writes cross-system edges into `dependencies.md` (e.g. "this puzzle solution requires an item from a later zone").
- **Zipper.** A reconciliation pass that resolves overlaps where two phases wrote about the same topic, merging or selecting per the freshness / confidence rules.

## Runtime vocabulary

- **Dial.** A graduated spoiler control the player sets at session start. Two axes: the spoiler dial (how much to reveal about a given lookup) and the vector dial (which extension folders the reader is allowed to draw from).
- **Persona.** The voice cast the reader speaks in. Game-specific cast members live in the corpus's `persona.md`; voice-agnostic discipline (player-pull rule, honest-ambiguity rule, file-first rule) lives in the reader skill's `persona_universal.md`.

## Format vocabulary

- **Claim format.** The tagged-claim syntax every corpus fact uses: a source link, a contributor handle, a confidence score, a last-verified date, plus tier and category tags. Defined in `templates/claim_format.md`. Born-structured beats retrofitted-structured.
- **Claim tag.** The inline annotation (`{claim:...}`) that marks a piece of prose as a structured claim, allowing the aggregator and reader to parse it without re-running NLP.
- **Status field.** A YAML field on every corpus file declaring whether it's a `scaffold`, partially populated, or full. Drives ingestion routing and lets the reader avoid surfacing empty files as if they were authoritative.

## Architecture primitives

- **Zone graph.** The directed graph of game zones, declared in `nav/architecture.md`. The substrate for routing, lookahead, and backtrack queries.
- **Optional content registry.** The list of side content keyed to zones, also in `architecture.md`. Lets the reader notify a player when they're about to leave a zone with missables behind.
- **Support topology.** The map of which systems support which gameplay arcs (combat, navigation, puzzle, narrative). Lets the reader route a question to the right corpus folder.
- **Locks and keys.** The list of gated content -- what's locked, what unlocks it, in what zone the key lives. The reader uses this for reachability checks.

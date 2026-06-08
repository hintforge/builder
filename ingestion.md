# Ingestion -- Research Cascade Result Integration

This procedure runs in a **fresh session, separate from setup**, when research result files (P1 / P2 / P3 from the cascade in [`setup_wizard.md`](setup_wizard.md) Step 8) are ready to integrate into a game guide. Triggered by the user typing "ingest the research" or attaching a result file directly.

> ⚠️ **Spoiler heads-up -- read before triggering ingestion.** Ingestion produces large LLM-visible output: the model prints fact text, file contents, table rows, and tier-tagged claims as it writes them. The *guide files* respect spoiler tiers via gating, but the *ingestion process* does not -- anything in the result file (boss names, late-game mechanics, missable timings, character fates) will scroll past in the terminal. There is no clean fix for this -- it's a structural property of running an LLM over spoiler-rich content. If you're spoiler-averse and haven't played the game yet, **shrink the terminal window to a sliver** -- wide enough to see the status line ("Incubating… Nm Ns") so you know when it finishes, narrow/short enough that fact text is clipped off.

> 🧠 **Run ingestion on a mid-tier model with extended thinking OFF.** Ingestion is structural: read result, validate spoiler tags, route facts to files by vector, update CHECKPOINT, refresh downstream briefs. None of those steps benefit from extended-thinking reasoning chains. If `[RESEARCH_MODE]` is `handoff`, the deep reasoning has already been externalized to the deep-research tool that produced the result file -- paying for thinking locally too is double-billing. Top-tier models (Opus-class) are also overkill; mid-tier (Sonnet-class) handles the work. Verify before triggering: most CLIs surface the model name and "thinking" status in their model picker or status line.

> **Why this is its own file.** Ingestion is the largest single context load this guide will see. Loading the full setup wizard alongside the result file wastes context on first-run setup steps (environment check, player name, tier dials, persona research, TTS/PTT, subfolder shape) that ingestion doesn't care about. This file carries only what the ingestion session needs.

> **Compaction expectation:** EXPECTED at CRPG scale (P2/P3 with many files; P1 with large achievement sets). See [`compaction_policy.md`](compaction_policy.md) for handler discipline. Step 8's Index re-derivation sub-pass is one of this procedure's compaction handlers (it catches index/entity-file drift introduced when post-compact recomposition pulls from a lossy summary).

## Pre-flight

- The session is **fresh** -- Step 10 of the setup wizard tells the user to start a new chat before saying "ingest the research." If the current session shows wizard-setup activity above, ask the user to restart in a fresh session before continuing.
- The session is **opened inside the game folder** (`Guides/<game>/`), not at workspace root or inside `hintforge/`. The agent's working directory determines which game's research gets ingested.
- Framework files this procedure reads (e.g. `templates/claim_format.md`) come from the running skill, not a path relative to the game folder.

## Blocked-source recovery

Some source domains return 403 / empty responses to direct fetches because they protect against automated traffic. Two cases are common enough to bake into the workflow:

- `*.fandom.com` -- Cloudflare-fronted game wikis. Direct `web_fetch` from a cloud-hosted Claude runtime (e.g. claude.ai Cowork, the API, anywhere on a datacenter IP) fails ~100% of the time because the datacenter IP range is on Cloudflare's automated-traffic block list. A local user's browser-session fetches sometimes succeed; that does not mean the framework can rely on `web_fetch` for Fandom from a runtime that talks over a hosted IP.
- `reddit.com` / `old.reddit.com` -- progressively closed off since 2023, with `robots.txt` disallowing almost all automated access and the Internet Archive's Wayback Machine blocked from indexing post detail pages as of 2025-08.

The ladders below replace direct `web_fetch` against these domains with a sequence of working paths. Whichever rung succeeds, **record the rung in the claim's `capture-method` field** (value vocabulary defined in [`templates/claim_format.md`](templates/claim_format.md)).

### Fandom ladder (try in order, stop at first success)

1. **`Special:Export` via api.php** (the API form, NOT the `/wiki/Special:Export` HTML form). URL pattern: `https://<wiki-name>.fandom.com/api.php?action=query&export=1&titles=<Page>` (URL-encode the page title; comma-separate multiple titles). Returns wikitext XML. **The HTML form at `/wiki/Special:Export` is Cloudflare-gated and fails from cloud-hosted runtimes -- use the api.php form only.** Wikitext is cleaner for corpus ingestion than HTML stripped to text (preserves structure, links, templates). Record `capture-method: special_export`.
2. **`api.php` Parse API.** URL pattern: `https://<wiki-name>.fandom.com/api.php?action=parse&page=<Page>&format=json`. Returns rendered HTML wrapped in JSON. Same Cloudflare bypass as the export endpoint; complementary because the Parse API returns templates already expanded (more readable for direct quote extraction; export returns raw wikitext with templates unexpanded). Pick this rung when the page's information density is in template-rendered content (infoboxes, tables) rather than prose. Record `capture-method: mediawiki_parse`.
3. **BreezeWiki mirror.** Alternative front-end that serves Fandom content as clean HTML without ads, JavaScript, or the Cloudflare gate. URL substitution: `https://<wiki-name>.fandom.com/wiki/<Page>` becomes `https://breezewiki.com/<wiki-name>/wiki/<Page>`. Public instances rotate -- pick a live one at fetch time rather than hard-coding a host. Some wikis with heavy template usage render incompletely on BreezeWiki; if the page is missing structural elements, drop to the next rung. Record `capture-method: breezewiki`. Always cite the canonical Fandom URL in the claim's `source` field, not the BreezeWiki mirror URL.
4. **`archive.ph` lookup** (a.k.a. `archive.today`). Distinct from the Internet Archive's Wayback Machine, and not affected by either Reddit's Wayback block or Fandom's Cloudflare config. If no snapshot exists for the URL, submit one via `archive.ph` first, wait for the snapshot to complete (usually seconds), then fetch the resulting archive URL. Record `capture-method: archive_ph`. Cite the canonical URL plus the archive snapshot URL in the claim's `source` field.
5. **Manual paste from a browser session.** Open the page in a normal browser, select-all, paste into the ingestion file or working chat. For typical ingestion volumes (dozens of pages per game) this is faster than any of the above. Record `capture-method: manual_paste`.

A direct `web_fetch` on `*.fandom.com` is not a numbered rung. From a cloud-hosted runtime it 403s reliably; promoting it back into the ladder hides the working rung (`Special:Export`) below a rung that does not work. Local-browser users who notice that `web_fetch` sometimes succeeds in their own runtime should not edit it back into the ladder for that reason.

### Reddit

Manual paste from a browser session is the default; `archive.ph` is the fallback for threads that have been deleted or are otherwise gone. The historical `old.reddit.com/.../.json` workaround is intentionally omitted -- it works rarely enough that codifying it invites future contributors to over-engineer Reddit ingestion when the right answer is that ingestion should not exceed what a human reading the thread does anyway. Record `capture-method: manual_paste` (or `archive_ph` if the snapshot path was used).

The autonomous Reddit module sweep (see [`reddit_sweep.md`](reddit_sweep.md)) is the framework's structured path for post-P1 community-knowledge harvesting via the `reddit-mcp-buddy` MCP server. The ladder above remains the right tool for individual Reddit-thread citations encountered during P2 / P3 result-file ingestion (a single thread URL that appears as a source in a deep-research result); the sweep is the right tool for systematic community-knowledge coverage scoped to a subreddit. Different shapes of capture, different recovery flows.

### When the ladder is irrelevant

Any source that is not Fandom or Reddit and that returns content cleanly via the deep-research tool or direct `web_fetch` records `capture-method: web_fetch`. The ladder above is specifically for blocked-source recovery, not a generic capture-method picker.

## Procedure

### 1. Find the result file

Check `<game>/research_inbox/` for numbered subdirectories (`p1/`, `p2/`, `p3/`, etc.) and the `module/` subdirectory. The wizard creates the initial set based on the planned research cascade; additional folders (e.g., `p4/`) are created as subsequent briefs are written. The `module/` folder is created on demand by autonomous-sweep procedures (currently [`reddit_sweep.md`](reddit_sweep.md); future supplemental sweeps land here too). Pick up any file that isn't `.gitkeep`. Ingest in phase order -- lowest number first, since earlier phases create the scaffold that later phases extend; module-sweep artifacts can ingest in any order relative to phases (typically after P1).

**Frontmatter-aware routing.** Before routing to the standard phase pipeline, read the file's frontmatter. If `kind: reddit_sweep` (or another module-sweep `kind:` value), route to **step 4b "Ingesting a reddit_sweep artifact"** below instead of the standard step 3 -> step 4 flow. Reddit-sweep artifacts have their own structure (Findings + Recurring questions + appendix) that step 4b is built for; routing them through standard phase ingestion would fail at vector-tag distribution.

If the user attached a file directly, use that instead and ask which phase or module it belongs to. If all inboxes are empty and no file was attached, ask the user where the result is.

### 2. Read the brief and result

Read the corresponding phase brief from `<game>/research_briefs/` -- match by phase number (e.g., `p1.txt`, `p2.txt`, `p4_weapons_enemies.md`). File extension and descriptive suffixes may vary; match on the `p<N>` prefix. Read the brief first (so the bot knows what was asked), then the result file(s).

**Large result files (>25k tokens) must be read in chunks.** Check the file size first -- if Read errors with "exceeds maximum allowed tokens," fall back to repeated Read calls with `offset` and `limit` (e.g., lines 0-499, 499-998, …) to walk the whole file. Result files from external deep-research tools regularly land in the 30-50k-token range; treat single-Read success as a happy path, not the default.

Read [`templates/claim_format.md`](templates/claim_format.md) to confirm the metadata convention before writing.

### 2.5. Entity-scaffold check (mandatory at `corpus-core-version: 5` and later)

Read `<game>/research_briefs/stage0_priors.md` for the NPC / faction / crew-system / reputation-system signals captured at Stage 0 §5 (see [`setup_wizard.md`](setup_wizard.md) Step 6.7). For each named-entity class flagged at Stage 0 as high-dependency or `yes`:

1. **Verify the class folder exists at corpus root.** Classes the framework recognizes by default: `npcs/`, `factions/`, `crew/`, `reputation/`. A corpus may carry additional classes when Stage 0 surfaced a genuinely-novel category; treat them with the same rules.
2. **If the folder is absent**, scaffold `<class>/index.md` from [`templates/entity_index.md`](templates/entity_index.md) before distributing facts. Per-entity files are scaffolded later (step 4) as entity-tagged claims surface; the index is the gating artifact for the class.
3. **Migration: v4 corpora with an existing `enemies/` folder.** Rename `enemies/` to `npcs/` (one-time, mechanical). Existing files inside the renamed folder get `entity-status: hostile` added to their frontmatter at first touch. Record the rename in the step 12 recap. Subsequent ingestions are no-ops for the rename. If the corpus carries both `enemies/` AND `npcs/` (mid-migration state from an earlier touch), reconcile under `npcs/`; do not leave `enemies/` orphaned.

Then **scan the just-read result file for entity-tagged claims whose class folder does not yet exist** (late-emerging class Stage 0 did not predict -- e.g. P3 introduces a new faction). Scaffold the missing class folders the same way and record the late emergence in step 12's recap; if the late-emerging class doesn't fit any framework-recognized name, leave a one-line note in `limitations.md` flagging the new class.

This step runs **every phase**. P1 typically catches Stage-0-known classes; P2 / P3 catch late-emerging classes the deeper-cascade phases surface. At `corpus-core-version: 4` and earlier this step is a no-op (no `entity:` overlay exists yet).

### 3. Spoiler classification pass (mandatory, runs as a separate sub-agent)

Deep research is generated unfiltered; spoiler scoping happens here. Spawn a `general-purpose` Agent with the result file(s) plus the user's current `enemy_tier` and `puzzle_tier`. The sub-agent's job:

1. Read every fact in the result. Validate or assign a per-fact `spoiler:` tag -- `none` / `progression` / `late-game` / `story` / `dlc:<name>`. Untagged content is unsafe; the sub-agent must classify everything.
2. **Combat content has three sub-vectors that classify differently -- tag at the fact level, not the section level.** This split mirrors the tier rules in [`templates/warning_tiers.md`](templates/warning_tiers.md) Tier 0, which gates "Boss existence hidden" and "Permitted: post-encounter help on request" as separately enforced rules:
    - **Tactics** (weakness, phase breakdown, weapon recommendation, missable-achievement preconditions): `progression` for mainline bosses, `late-game` for chapters past the global PoNR, `story` only for final-boss specifics tied to a narrative reveal. Persona delivers post-encounter on request. When a tactics fact is the trigger for a platform achievement, also carry the `achievement:` overlay (and required `trigger_type:` / `achievement-hidden:` per [`templates/claim_format.md`](templates/claim_format.md)) so the aggregation pass in step 8 can route it to [`achievements.md`](templates/achievements.md). At `corpus-core-version: 4` and later.
    - **Lore / cutscene** (who the boss is, narrative role, character relationships): `story`, regardless of where in the game it appears. Persona delivers only on explicit opt-in.
    - **Existence** (the fact a boss appears in zone X): `progression`. The persona enforces "Boss existence hidden" from `warning_tiers.md` Tier 0 at read-time -- the integrator still writes the fact into the destination file (zone files, architecture's locks-and-keys table, encounter index) so the persona has it when the player encounters the boss and asks for help.

    Common error: collapsing all three into `story` because a cutscene sits next to a fight in the result. A research line that combines a cutscene narrative reveal with the boss's existence-in-zone and a tactical weakness in the same sentence carries lore (`story`), existence (`progression`, gated by Tier 0 at read-time), and tactics (`progression`, available post-encounter). Tag each separately.
3. For each fact, derive the metadata `enemy-tier` and `puzzle-tier` from its spoiler tag. `none` → tier 0; `progression` → 1; `late-game` → 2; `story` → 3; `dlc:<name>` → tier-of-dlc-content + dlc flag.
4. **Entity overlay emission (at `corpus-core-version: 5` and later).** When a fact concerns a named entity that lives under a class folder scaffolded in step 2.5 (`npcs/`, `factions/`, `crew/`, `reputation/`), emit the entity overlay alongside the spoiler tag: `entity: <id>` (required), `entity-status: <status>` (required when the class is `npcs/`; values per [`templates/claim_format.md`](templates/claim_format.md)), and `entity-hidden: yes` when the entity is secret or conditionally-revealed (default `no`). Apply the named-individual rule in [`templates/claim_format.md`](templates/claim_format.md) ("When `entity:` applies") when deciding whether a combat NPC gets its own entity file vs stays generic. The vector tag and the entity overlay are NOT in competition: a hostile-NPC fact carries `vector: enemy` (routing generic-mob combat to `mechanics.md`) AND `entity: <id>, entity-status: hostile` (aggregating to `npcs/<id>.md`) when the NPC qualifies as named-individual.
5. Output a classified version of the result with each fact prefixed by its tags, preserving original wording verbatim. No omissions; high tiers get tagged for gated display, not deleted.
6. Surface ambiguous calls in a short report -- facts where the spoiler tier wasn't clear from context -- for the main agent to confirm with the user before appending.

**Why a separate agent:** holding "go maximum depth" and "filter by spoiler tier" in the same context produces shallow research; classification needs the full result in front of it without the depth-pressure that produced the result. The split also makes tier raises cheap later -- the user advances, the main agent re-runs the *display* filter against already-classified content, no re-research needed.

### 4. Distribute classified facts by vector tag

Do not overwrite existing content; append or create per-file. **When editing an existing claim-bearing file, also update its top-line `last_reconciled:` frontmatter to today's date.** Newly-created files get the date via the template; edits to existing files don't, and the field would silently drift across phases without this rule.

| Vector tag | Destination |
|---|---|
| `nav` | `nav/<zone>.md` -- create from `templates/nav_zone.md` if the file doesn't exist |
| `structure` | `nav/architecture.md` -- zone-graph edges, optional content registry entries, support topology, locks-and-keys |
| `puzzle` | `puzzles/<puzzle_name>.md` |
| `item` | `items/<category>.md` |
| `boss` | per-game mapping (optional-zone boss → discrete-zone file; main-story boss → `sections/<area>.md`) |
| `enemy` | `mechanics.md` or `warning_tiers.md` |
| `lore` | `sections/<area>.md` |
| `controls` | `controls.md` (game-folder root) -- create if absent |
| `settings` | `settings.md` (game-folder root) -- create if absent |
| `build` | `items/builds.md` -- create if absent; or merge into existing `items/<category>.md` (e.g. `items/abilities.md`) when the build is ability-focused |
| `missable` | primary-vector destination + index entry in `sections/<area>.md` |
| `achievement` | primary-vector destination + aggregated entry in `achievements.md` (one entry per `achievement:` value on the claim). Overlay tag, not a primary vector -- combine with the claim's primary vector, e.g. `vector: nav, achievement: ach_id_1` or `vector: item, achievement: ach_id_2, missable: yes`. Required at `corpus-core-version: 4` and later when a claim documents the trigger or a prerequisite for a platform achievement. See [`templates/claim_format.md`](templates/claim_format.md) for the four fields (`achievement:`, `achievement-hidden:`, `trigger_type:`, `genre:`) and step 8 below for the aggregation contract and trigger-type classification rules. |
| `mechanic` | `mechanics.md` or `meta_explainer.md` (only when no more-specific vector applies) |

**For `nav` and `structure` facts:** if `nav/` doesn't exist, create it (stub `index.md` + scaffold `architecture.md` from templates). Set `status: research-integrated` on each newly written file. After writing all per-zone files, run a consistency pass: every edge declared in a zone file must appear in `architecture.md`'s edge table, and vice versa. Drift between them is a bug.

**For `landmark` and `hybrid` localization-mechanism classes:** also write the P2 brief's localization-toolkit output to `nav/localization.md` (create from `templates/localization.md` if absent). Skip for `map-system` and `none`-class games.

**For `settings` facts:** organize `settings.md` by the game's actual in-game menu tabs (one `##` heading per tab), not by industry categories like "Graphics" / "Audio" / "Accessibility." Games structure their settings menus differently and reorganize them across patches. Each setting entry must include its exact menu path so the persona can direct the player accurately. If the research doesn't confirm exact tab names, flag them as unverified.

**For all other vectors:** preserve tabular structure; don't flatten tables to prose.

**For claims carrying an `entity:` overlay (at `corpus-core-version: 5` and later):** after writing the claim to its primary-vector destination, append a one-line cross-ref to the destination section: `> see <class>/<entity-id>.md for full summary`. Mechanical and predictable; no judgment call. The cross-ref points readers from the primary-vector home (e.g. a recruitment fact in `nav/<zone>.md`) to the entity's per-entity file. The `enemy` vector and the entity overlay are orthogonal axes: generic-mob combat content continues to route via the `enemy` vector to `mechanics.md` or `warning_tiers.md`, unchanged. Named-NPC combat facts ALSO carry `entity: <id>, entity-status: hostile` and aggregate to `npcs/<id>.md`. The two destinations describe different axes of the same claim, not duplicate writes.

### 4b. Ingesting a reddit_sweep artifact (alternate to step 4)

This step replaces step 4's standard P1 / P2 / P3 distribution when the result file is a reddit-sweep module artifact (frontmatter `kind: reddit_sweep`). Step 1's routing branch directs here. Step 5 (inline metadata) and step 6+ (phase-specific behavior, reconciliation, coverage check, CHECKPOINT, recap, move-aside) apply unchanged after this step.

**1. Read the artifact.** File lives at `<game>/research_inbox/module/reddit_sweep.<game>.<ISO-date><N>.md`. If multiple artifacts are present in `module/`, ingest in suffix order (lowest `<N>` first); same-day re-runs share the date stamp. Read frontmatter:

- `auth_tier`, `subreddits.primary.name`, `subreddits.broader.name` (if present): informational, record in CHECKPOINT recap.
- `status`: if `partial-mcp-failure` or `partial-budget-exhausted`, surface to the user and ask whether to proceed before continuing. The user may opt to wait for a re-sweep instead.
- `scope_query` (present only for doctor-invoked sweeps): record in CHECKPOINT recap so future maintainers know the sweep was scoped.

**2. Run the spoiler-classification sub-agent (step 3) with reddit-specific evidence.** Spawn the standard `general-purpose` Agent per step 3, but pass two additional pieces of evidence beyond the raw text:

- The artifact's `subreddits.*` context (the originating sub is a weak signal for content shape -- a sub dedicated to a single game's competitive PvP carries different default tier expectations than a lore-discussion sub).
- The per-source `reddit_spoiler_tag: yes | no` field on each Source. The sub-agent treats `reddit_spoiler_tag: yes` as a strong signal toward `progression` / `late-game` / `story` tiers and downgrades only if surrounding text makes a `none` classification defensible.

The sub-agent classifies every Finding and every Recurring-question entry. Recurring-question claims carry **no default tier** -- they classify like any other claim.

**3. Map each Finding to a corpus claim.** The artifact's per-Finding `claim_kind` enum maps to the corpus's vector tag taxonomy:

| Artifact `claim_kind` | Corpus vector + overlays | Notes |
|---|---|---|
| `mechanic` | `vector: mechanic` | Standard step 4 routing (`mechanics.md` or `meta_explainer.md`). |
| `bug` | `vector: mechanic` + `confidence: medium` floor | Community-flagged bug status drifts patch-to-patch; cap confidence. Record dev-confirmation status in the claim's `notes:` field. |
| `build` | `vector: build` | Routes to `items/builds.md` or `items/<category>.md` per step 4. |
| `interaction` | `vector: mechanic` | Game-system interaction; routes to `mechanics.md`. |
| `strategy` | `vector: boss` if the Finding's summary names a specific boss / encounter; else `vector: mechanic` | Judgment call on the Finding's scope. |
| `dev-confirmation` | Primary vector inferred from the Finding summary (`mechanic` / `lore` / etc.) | Record dev-flair in the source-attribution `notes:` field as authority signal. |
| `lore-question` | `vector: lore` | Routes to `sections/<area>.md` or the appropriate lore destination. |
| `other` | Run the step 3 sub-agent's vector judgment | If still unclassified, write to `_overflow/` per ingestion.md's lazy-classification model. |

**4. Map each Recurring-question to a corpus claim.** Recurring questions become individual claims via the same spoiler-classification pass. Vector assignment:

- Narrative-shaped question (representative threads carry lore-question or story-spoiler signals) -> `vector: lore`.
- Mechanically-shaped question (about systems, builds, drops) -> `vector: mechanic`.

The recurring nature lives in the claim's `notes:` field, verbatim shape: `Recurring question across <comma-separated windows>; <K> supporting threads. The guide should answer this.` Do not introduce a new vector for question-class content; the existing taxonomy covers routing. (Whether to aggregate recurring questions into a corpus-level `sections/open_questions.md` is left open for future consideration.)

**5. Populate per-claim source fields.** Use the artifact's per-Finding fields verbatim:

- `source:` -- the canonical Reddit thread URL (one source row per supporting thread).
- `capture-method: manual_paste` -- per [`templates/claim_format.md`](templates/claim_format.md) and the Blocked-source recovery Reddit policy. The sweep itself is the capture pathway, but the per-thread evidence is functionally manual-paste-equivalent.
- `confidence:` -- per the step 5 confidence rules; community-consensus threads cap at `medium` unless dev-flair corroborates.
- Reddit-specific attribution -- Subreddit, Window, Sort-position, OP-flair, Supporting-comments -- compress into the claim's `notes:` field as a one-line summary for downstream auditability.

**6. The "Threads scanned but not surfaced as findings" appendix is INBOX-ONLY.** Never ingested. Leave it in the artifact file for re-run reference (future sweeps or doctor invocations avoid re-evaluating known dead ends). No claims derive from this appendix.

**7. Route the prepared claims into step 4's distribution.** Once each Finding and Recurring-question has been classified (step 2 above) and mapped to a vector + overlays (steps 3-4), the claims feed into step 4's destination table normally. Step 5 (inline metadata), step 6 (phase-specific behavior -- this is a module sweep, so the `module_sweep_<kind>` Phase state field (e.g. `module_sweep_reddit` -- one field per shipped module-sweep procedure) is the relevant marker rather than `p[N]_ingestion`), and step 7+ apply unchanged.

**8. CHECKPOINT update for module sweep.** Step 9 below covers the standard CHECKPOINT changelog write. For reddit-sweep artifact ingestion, also set `module_sweep_reddit: complete YYYY-MM-DD` in `## Phase state` (add the field if absent at the corpus's CHECKPOINT). The recap entry names the artifact file, total findings ingested, originating sub(s), and any `status: partial-*` caveat carried in the artifact frontmatter.

**9. Move-aside on completion.** Apply the **Dated move-aside** rules from step 11: rename and move the ingested artifact to `research_inbox/module/_processed/` (create the subfolder if absent) with the research date embedded in the filename. The "Threads scanned" appendix moves with the file; it stays accessible for re-run reference inside `_processed/`.

### 5. Tag each new section with inline metadata

`_source: <tool> <date> · capture: <method> · confidence: <high|medium|low> · enemy-tier: <N> · puzzle-tier: <N> · category: mainline · spoiler: <tier>_`

- **`capture`** -- the `capture-method` value (`web_fetch | special_export | mediawiki_parse | breezewiki | archive_ph | manual_paste`) for how this fact entered the corpus. Required at `corpus-core-version: 2` and later (see [`templates/claim_format.md`](templates/claim_format.md) and the Blocked-source recovery section above for the value vocabulary). For research-cascade-sourced claims, the default is `web_fetch` -- the deep-research tool fetches its own pages and the ingestion session is not the capture moment. Override only when the contributor walked one of the ladder rungs above (Fandom or Reddit) for this fact specifically and the rung is reflected in the original brief or result file.

- **Confidence:** `high` if a verifiable fact corroborated by ≥2 independent sources (separate authors / publications, not the same wiki mirrored elsewhere); `medium` if (a) value may vary by patch (item weights, exact damage numbers), or (b) only one source corroborates, or (c) all sources are forum-thread / community-consensus rather than walkthrough / wiki / dev statement; `low` if inferred from indirect evidence. **Source count beats source authority** -- a single high-authority claim is `medium`, not `high`. If the spoiler-classification sub-agent flagged a fact as single-source or contested in its report, the integrator must downgrade confidence regardless of how the source phrased itself.
- **`enemy-tier` and `puzzle-tier`** come from the classification pass, not the user's current settings -- that way display-time filtering can compare the user's *current* tier against the *content's* tier and gate accordingly.
- **Default `category` is `mainline`;** use `easter-egg` for hidden / side-objective content and `lore` for worldbuilding (hidden until the reader opts in).
- **Write content, gate display.** Classification tags are read-time display filters, not write-time skip switches. When a fact classifies as `enemy-tier: 3` or `spoiler: story`, write the content into its destination file with inline metadata; the persona handles tier-based reveal at read-time. Do **not** write placeholder stubs (e.g. `_[hidden at current tier -- raise tier to access]_`) in lieu of real content -- placeholders strand content the user opted into seeing once they raise a tier. The only exception is `dlc:<name>` content from a phase not yet ingested (no content exists to write).
- **No inline meta-confirmation language.** Confidence and corroboration are recorded on the `_source: … · confidence: <tier>_` metadata line and the trailing `[Confirmed: <sources>]` line. Don't repeat it as parenthetical "(CONFIRMED -- …)" inside table cells, sentence bodies, or gate-condition descriptions -- the metadata lines already carry that signal, and the inline form creates reader noise. Same rule for "(verified)", "(SOURCED)", "(updated)", etc. -- keep meta out of the prose.

### 6. Phase-specific behavior

- **P1 ingestion.** First run -- creates `nav/architecture.md` scaffold (zone graph, chapter↔zone mapping, optional content registry, source-language set) plus all per-chapter content distributed by vector. Most content lands here.
- **P2 ingestion.** Extends an existing `nav/architecture.md` (adds support topology + locks-and-keys sections); creates per-zone gate-list files (`nav/<zone>.md`); writes `nav/localization.md` for `landmark` and `hybrid` games. P1 must be ingested first.
- **P3 ingestion.** Patches gaps + DLC. May extend the zone graph (DLC-introduced zones), optional content registry (DLC quests), and locks-and-keys table (DLC items unlocking base-game content). Merges into existing `architecture.md`; doesn't replace.

### 7. Corpus reconciliation (P2 / P3 only -- skip for P1)

For every gap-fill resolution this phase produced that **drops, contradicts, supersedes, or rewords** prior-phase content, locate the orphaned content in the corpus and edit it. Grep the destination subfolders (`sections/`, `items/`, `nav/`, `puzzles/`, `optional_zones/`, `controls.md`, `settings.md`, plus any entity-class folders that exist -- `npcs/`, `factions/`, `crew/`, `reputation/` at `corpus-core-version: 5` and later; the legacy `enemies/` folder no longer exists in v5 corpora since the v4 → v5 migration renamed it to `npcs/`) for the original claim -- search anchors include distinctive phrases, the `[Single source -- verify]` flag, and the section heading the prior phase wrote it under. For each match:

- **Drop:** delete the entry. Do not leave a "DROPPED -- see CHECKPOINT" note in the corpus; the persona reads only the corpus at runtime, not CHECKPOINT.
- **Contradict:** rewrite with the new resolution and an updated `_source:` line. Strip the prior `[Single source -- verify · class:<class>]` flag.
- **Supersede:** replace the old value (e.g. canonical crafting-cost numbers replacing earlier range estimates).
- **Reword:** rewrite to match the resolution's phrasing.

**Source-class informs partial vs. full drops.** If the prior-phase verify-flag carried `class:editorial-non-en` (VGTimes.ru, StopGame.ru, DTF.ru, 4Gamer.net, gry-online.pl, etc.) and this phase's gap-fill could not corroborate the claim from English sources, the default is **partial drop** -- keep the underlying mechanic with a translation-conflation caveat, drop only the unsupported sub-claim. Non-Anglophone editorial sources for non-Anglophone-developed games disproportionately carry mechanics English coverage misses; that is the entire reason the cascade has an internationalization rule. A full drop on a single `editorial-non-en` source requires a positive contradiction from another source, not just absence of English corroboration.

**Why this step exists.** Resolutions captured only in `CHECKPOINT.md` leak past read-time gating: the persona reads from `sections/`, `items/`, `nav/`, etc., not from CHECKPOINT. A "DROPPED" entry in the CHECKPOINT changelog with the original claim still in `sections/<chapter>.md` means the player gets the dropped claim served at read-time without any of the contradiction context. **Corpus state must reflect the resolution, not just metadata.**

### 8. Universal-core coverage check (mandatory)

**Motivation.** When `status: scaffold` appears on a corpus file, the maintainer and reader currently can't distinguish three very different states: "wizard created the stub and nobody touched it yet," "ingestion deferred this on purpose with a plan," or "ingestion considered the topic and concluded there's nothing here." The reader treats all three identically -- file absent, fall through to web search. For the deferred and intentionally-empty cases that's wrong: the answer exists, it's just "not yet" or "intentionally nothing." This step forces the corpus state to encode which case applies, so silent scaffold can't ship.

**Rule.** At end of phase pass, every claim-bearing universal-core file must end in exactly one of:

1. **`research-integrated` with content** -- the pass produced substantive content for this file. Promote and move on.
2. **`research-integrated` with an explicit honest empty-statement one-liner** -- the pass considered this universal target and concluded there's nothing for it in this game. Example for `sections/missables.md` in a game with no missables: "No missable content in this game -- all collectibles are always-available or absent." The promotion records that the question was *answered*, even if the answer is "nothing." Use the template strings in the table below where applicable.
3. **`scaffold` AND a `[deferred to phase N -- reason]` CHECKPOINT changelog entry** -- the pass is not yet done with this file; later phase will fill it. Scaffold-with-deferral is a valid state; the deferral note is the contract.
4. **Post-pass evolution states** -- `live-observed` or `reconciled`. Already past the check; leave as-is.

Silent scaffold at end of pass -- no deferral note, no honest empty-statement -- is the forbidden state. The check fires only after all writes (steps 4-7) are complete; mid-pass scaffolds are fine.

**Scope.** The check applies to claim-bearing files only. Per [`docs/corpus-format.md`](docs/corpus-format.md) §6 ("Every per-zone file and every claim-bearing file produced by ingestion carries a status field"), config and state files don't carry status and aren't checked: `CHECKPOINT.md`, `CLAUDE.md`, `limitations.md`, `warning_tiers.md`, `dependencies.md`. The check covers:

- **Universal claim-bearing root files:** `controls.md`, `settings.md`, `mechanics.md`, `achievements.md` (the last only at `corpus-core-version: 4` and later -- aggregation rule below)
- **Universal directory indices:** `nav/index.md`, `items/index.md`, `sections/index.md`. (Not `_overflow/index.md` -- see exemption below.)
- **Every per-zone or per-content file written during this pass:** `nav/<zone>.md`, `items/<category>.md`, `sections/<chapter>.md`, etc.

**`_overflow/` is exempt from this check.** `_overflow/` is a runtime catch-all, not a research target -- content accumulates there during live play when the player encounters something that doesn't fit other folders, not during ingestion. The wizard creates `_overflow/index.md` at scaffold with a "(Empty -- will fill during research ingestion and live play as needed.)" note and that scaffold status persists by design until live play promotes it. See [`docs/corpus-format.md`](docs/corpus-format.md) §1 for the rationale.

**Procedure.** For each file in scope:

1. Read the current `status:` field.
2. If `research-integrated` / `live-observed` / `reconciled` → pass.
3. If `scaffold` → check whether the file has substantive content beyond the wizard stub. If yes, the status is stale (case 1 -- promote). If no, check whether this file is on the deferred list for a later phase (case 3 -- leave scaffold, ensure CHECKPOINT changelog has the `[deferred to phase N]` note). If neither, this is the forbidden silent-scaffold state -- either populate from accumulated content (aggregation rules below) or write the honest empty-statement (case 2).

**Aggregation rules for universal-core summary files.** When ingestion has been routing claims by vector tag (per step 4) but no claims routed to a universal-core summary target, check whether content elsewhere in the corpus should be aggregated up. Specifically:

- `sections/missables.md` -- auto-built from all `missable: yes` overlay claims in the corpus, grouped by zone or chapter. If zero such claims exist, write the honest empty-statement.
- `achievements.md` (at `corpus-core-version: 4` and later) -- auto-built from all claims carrying an `achievement:` overlay, organized into the six `trigger_type` H2 sections (`Progression | Branch | Mastery | Collection | Threshold | Discovery`). The completeness target is `research_briefs/achievement_stubs.md` (the Stage 0 stub fetch). For each stub entry: verify the aggregation file has a populated entry with `trigger`, `missable`, `ponr-window`, and `vector-binding` fields. Three end-states are valid: **resolved** (a corpus claim carries the achievement id; aggregation entry promoted to `status: research-integrated`), **deferred** (entry stays `scaffold` with `deferred-to: P3` and a one-line reason -- typical for DLC achievements held over from P1), or **unreachable** (entry recorded in `limitations.md` with what blocked research; aggregation entry stays `scaffold` with `deferred-to: limitations`). Silent scaffold at end of phase is forbidden, same shape as the universal-core rule above. Classify each entry's `trigger_type` per the **Trigger-type classification rules** sub-section below and reorganize the file's flat stub list into the six trigger-type sections (omitting sections with no entries). If `research_briefs/achievement_stubs.md` does not exist (Stage 0 was skipped, or this is a v1-v3 corpus migrating to v4), write the honest empty-statement: "No achievement stub list captured at Stage 0; achievement coverage deferred to maintainer-initiated refetch." Hidden achievements (`achievement-hidden: yes`) keep their name in the aggregation file but the read-time renderer gates the heading entirely below `progression`-tier; the integrator writes them in full regardless of current tier per the "write content, gate display" rule in step 5.
- `<entity-class>/<entity-id>.md` (at `corpus-core-version: 5` and later) -- aggregated from all claims carrying an `entity: <id>` overlay, one file per entity. **Compose by Grep'ing the just-written corpus for `entity: <id>` matches and aggregating from those claims, not by re-reading the source research result.** Per-entity files are downstream of the primary-vector destinations they aggregate from; composing in parallel from the source result risks the entity file disagreeing with the primary-vector files the same session wrote (e.g. a zone file correctly states a recruitment-gate trigger and an independently-composed entity file states a different version of the same trigger). Each entity-tagged claim ALSO routes to its primary-vector destination (step 4); the per-entity file holds back-pointers + a tier-appropriate summary row per claim. Scaffold per-entity files from [`templates/entity_summary.md`](templates/entity_summary.md). Three end-states are valid: **populated** (entity has 1+ corpus claims; file promoted to `status: research-integrated`), **stub** (entity scaffolded but no claims yet; honest empty-statement "No facts gathered for <entity> at <phase>; expected in P<N>" with `deferred-to:` tag), or **unreachable** (entity scaffolded but research couldn't locate sources; recorded in `limitations.md` with what blocked research; per-entity file stays `status: scaffold` with `deferred-to: limitations`). Silent scaffold at end of phase is forbidden, same shape as the universal-core rule above. Hidden entities (`entity-hidden: yes` -- secret companions, secret-faction reveals, hidden romance tracks) keep their full content; read-time tier gating handles concealment via the same rule as hidden achievements. For `npcs/` files, the `entity-status` value appears in frontmatter and the file's first H2 reflects the current relationship state (e.g. "Current relationship: party member as of Ch3 recruitment"); status changes during play get appended as Status history entries, not file rewrites or relocations, so the corpus carries the lifecycle history. For convertible NPCs, the same file carries both pre-conversion combat content and post-conversion party content -- the convertibility is the entity's defining property. Also refresh `<class>/index.md`'s roster table to reflect the entity files now present in the class. If a class folder exists but contains zero entity-tagged claims at end of phase (Stage 0 over-predicted), write the honest empty-statement at the class index: "No <class> facts captured at <phase>; class folder retained pending downstream-phase research."
- `sections/story_notes.md` -- auto-built from all `vector: lore` claims, grouped by chapter. If zero, honest empty-statement.
- `sections/index.md` -- references whatever sections-files now exist (chapter walkthroughs for narrative games; cross-cutting summaries like `missables.md`/`story_notes.md` for puzzle-shaped games; both for hybrid games).
- `nav/index.md` -- references `architecture.md` plus every per-zone file written. Routing rules content already in the file stays; the "Files in this folder" table gets refreshed to current state.
- `items/index.md` -- references every per-category file (`items/weapons.md`, `items/abilities.md`, etc.) that exists.

**Trigger-type classification rules (v4+ only -- applies to the `achievements.md` aggregation above).**

Six values, asked in order. First yes wins. Order matters because some achievements plausibly fit two categories; the primary classification is what the player has to do *first* to unlock the achievement, not what most distinguishes it. `discovery` comes last because it is the residual bucket.

1. **progression** -- Does every player who reaches a certain point in the game get this? (Story beat, chapter complete, level milestone, default-path subclass unlock.)
2. **branch** -- Does getting this exclude another achievement, or require a non-default choice no other player has to make? (Mutually-exclusive endings, faction picks, romance forks, restrictive multiclass.)
3. **mastery** -- Did the player demonstrate skill or accept a restriction beyond normal play? (No-death run, S+ rank, difficulty tier, no-X playthrough, speedrun.)
4. **collection** -- Is there a finite, enumerable set the player must complete in full? (All 27 radios, every codex entry, all museum donations.)
5. **threshold** -- Is the trigger a cumulative count, without a finite-set ceiling? (Kill 666 demons, catch 100 fish, ship 300 of one crop.)
6. **discovery** -- Was the player likely to find this only by deliberate exploration of a non-obvious mechanic or obscure hint? Often carries the platform's hidden flag.

Three disambiguation rules at the highest-mislabel-risk boundaries:

- **Rule A: mastery vs discovery.** Both can apply to "weird-thing-with-the-game-system" achievements. `discovery` is when *the fact that the trigger exists* is the achievement (hidden mechanic, easter-egg interaction). `mastery` is when *executing the trigger well* is the achievement (skill, restriction). "Kill 5 Mimics in 5 seconds" → mastery (mechanic obvious, skill is the trigger). "Mimic a Mimic" → discovery (interaction non-obvious, finding it is the trigger). "Complete the game without acquiring any Typhon power" → mastery (known restriction). "Use one enemy as an improvised weapon" → discovery (non-obvious interaction).
- **Rule B: threshold vs collection.** Both can apply to "count-up-to-N" achievements. `collection` is when set members are finite, named, and discoverable in advance (the corpus must enumerate them). `threshold` is when the *count* is the achievement; any unit satisfying the action class counts. "Catch 24 different fish" → collection (finite known list). "Catch 100 fish" → threshold (any fish counts). "Donate 40 different items to the museum" → collection. "Kill 666 demons" → threshold.
- **Rule C: progression vs branch.** Both can apply to "completed-a-chapter" achievements. `progression` is the *default path* every player takes; `branch` is when the player had to *choose* this path over another mutually-exclusive one. "Complete chapter 5" → progression. "Complete chapter 5 the empathetic way" → branch (non-default choice; excludes the unempathetic-way achievement). "Reach level 20" → progression. "Multiclass into every class without using Withers" → branch (non-default constraint).

**Genre overlay (independent of `trigger_type`).** The `genre:` field tags genre-specific structural patterns. Open vocabulary; conventional values: `social` (NPC relationship, romance, friendship -- strong in RPGs/sims), `roguelike` (character/ship-bound, run-condition, meta-progression), `mission` (per-level mastery -- Hitman/Forza pattern), `multiplayer` (online/co-op/PvP -- live-service tag), `meta` (fourth-wall, easter-egg, ARG -- DDLC pattern), `class` (class/subclass-acquisition -- Destiny 2 pattern). Corpora may declare their own values; add a one-line definition in the corpus's `achievements.md` "Genre vocabulary" section. The reader treats unknown `genre:` values as opaque tags, not errors.

**Per-`trigger_type` completeness contracts.** Each value imposes a different ingestion contract:

- **progression** -- one claim per achievement, on the zone/chapter the trigger sits in.
- **branch** -- one claim per achievement plus a `branch-excludes:` reference on the claim noting which other achievements (or branches) this excludes. The P1 brief generator must surface decision-tree topology.
- **mastery** -- one claim describing the constraint plus at least one claim describing the recommended strategy. Mastery achievements without a strategy claim ship `status: scaffold` with `deferred-to: P3`.
- **collection** -- *every set member* must be a claim, individually, with the `achievement:` overlay referencing the same achievement id. The aggregation file's entry references the set as a whole; per-member detail lives in the canonical claim homes.
- **threshold** -- one claim describing the count mechanic. Known efficient routes (e.g. high-spawn-rate fishing spots) may be surfaced as additional claims; not required.
- **discovery** -- one claim describing the trigger interaction. The P1 brief's "what mainstream guides miss" standing prompt specifically targets this category.

**Index-currency check (paired with status check).** When this pass wrote new files into a universal directory, that directory's `index.md` must be updated to reference them. A new corpus's `nav/index.md` listing only `architecture.md` despite 27 P2-written nav files existing alongside it is the failure mode this clause prevents. If the index was at scaffold AND its file-list table doesn't reference the just-written files, both halves are stale; fix both.

**Cross-file consistency sweep (gated -- do not declare ingestion complete until this passes).** Identifiers and overlay flags written into multiple files this pass must agree across the corpus. The failure mode this catches: the session writes a primary-vector file (e.g. `nav/<zone>.md`) correctly stating a gate trigger or status flag, then writes a per-entity aggregation file (`crew/<id>.md`, `npcs/<id>.md`) from the same source result minutes later with a different account of the same fact -- both composed independently, never cross-checked. Or: the session updates a status flag on one file (e.g. `entity-status: confirmed`) while leaving the same entity's flag stale in another file (`entity-status: suspected`). The aggregation rules above (entity, achievement, missable) push files toward agreement at write-time; this sweep verifies it at end-of-pass.

For each shared identifier or overlay flag this pass wrote, Grep the corpus for all occurrences and verify the references agree:

- **Entity overlays.** For every `entity: <id>` claim, Grep the corpus for that id. Every match should agree with the aggregated per-entity file: recruitment-window claim in `<class>/<id>.md` matches the gate trigger in zone files; status-history entries align with zone-file gate descriptions; named-individual rule applied consistently across files referencing the entity.
- **Achievement overlays** (at `corpus-core-version: 4` and later). For every `achievement: <id>` claim, Grep the corpus for that id. The `trigger`, `missable`, `ponr-window`, and `vector-binding` fields in `achievements.md` must match the per-claim metadata in the primary-vector destination file.
- **Missable flags.** Every claim with `missable: yes` overlay in a primary-vector file must have a corresponding entry in `sections/missables.md`. Every entry in `sections/missables.md` must reference back to a primary-vector claim. One-way drift in either direction is a defect.
- **Status-flag overlays** (e.g. `entity-status: confirmed/suspected/hostile/convertible/party`, `[std-variant: confirmed/suspected]`). Grep for the flag and verify the value agrees across every file that references the same entity. When `entity-status` changes during a pass (e.g. NPC promoted from `suspected` to `confirmed`), every file mentioning the entity must reflect the new value.

**Disagreement is a stitch-shaped defect.** Reconcile before recap: re-read the source result and the conflicting files, pick the authoritative claim (usually the primary-vector file the entity file should aggregate from, or the higher-confidence source), and rewrite the disagreeing file. Do not declare ingestion complete with unreconciled cross-file disagreement. If reconciliation requires research the result file doesn't support, flag in `limitations.md` with the conflict and the two source values; do not silently leave the corpus disagreeing with itself.

**Cost.** Grep is cheap: ~1 call + 1 short reasoning step per identifier (~600 tokens). For typical P2 / P3 scale (5-15 entities + handful of achievements), the sweep adds ~3-15k tokens to the recap phase. For P1-scale ingestion (80+ achievements, 10+ entity classes), the sweep adds ~50-80k tokens but catches a class of bug that cross-game datapoints confirm is real and that the analyze-skill procedure catches by gate -- this sub-step ports that gate into ingestion itself.

#### Index re-derivation

For every `<category>/index.md` this ingestion session edited, AND every `<category>/index.md` whose corresponding entity files were written/updated this session (even if the index itself wasn't touched): re-read the index file from disk and re-read each entity file it references. Verify cell-by-cell:

- **Roster/file tables:** does each row's data (recruitment zone, status, missability, etc.) match what the entity file at the row's path actually says?
- **Counts in prose** ("All N companion files", "M factions", etc.): does the number match the row count of the relevant table?
- **File-existence claims:** does every file the index links actually exist on disk? Does every entity file in the directory appear in the index?

Mismatches: edit the index to match the entity files (entity files are authoritative -- they were written from research; index cells may be inherited from earlier-phase stubs). If the entity file is wrong and the index is right, edit the entity file instead. Flag any ambiguous case in the step 12 recap.

**Why this is a separate sub-pass from the grep sweep.** The grep sweep catches "entity Y referenced in 3 files with conflicting status" -- identifier-aware checks. This sub-pass catches "index file's roster row for entity Y says zone X; entity Y's own file says zone Z" -- index-file-aware checks. Different failure mode, complementary detection. Grep can't catch index/entity drift because index cells and prose numerals aren't ambiguous identifiers; re-reading the actual files is the only way to surface them.

**Compaction note.** This sub-pass is one of the post-compaction handlers prescribed by [`compaction_policy.md`](compaction_policy.md) for ingestion. Even if the session did not compact, run the sub-pass -- it catches inherited-stub errors and post-summary-recomposition errors alike. If the session DID compact, the read-from-disk discipline is non-negotiable; the compaction summary is lossy on counts and table cells, and any post-compact edit that quotes a count or cell from the summary instead of re-reading the source file is a bug.

**Honest empty-statement template strings.** Use these verbatim where applicable so the corpus's "intentionally empty" markers are uniform and grep-able:

| File | Empty-statement template |
|---|---|
| `mechanics.md` (narrative-only game with no systems-level mechanics) | "No system-level mechanics -- pure narrative; routing/locks/keys live in `nav/architecture.md`." |
| `sections/missables.md` (game with no missable content) | "No missable content in this game -- all collectibles are always-available or absent." |
| `sections/story_notes.md` (game with no story-beat content above tier 0) | "No story-beat content separated from per-zone narrative; all story content lives in `nav/<zone>.md` or `sections/<chapter>.md` per zone." |

**Changelog requirement.** The CHECKPOINT harness changelog entry for this pass (written in step 9 below) must record every honest empty-statement promotion ("`sections/missables.md` → honest empty (game lacks missable content)") and every deferral ("`sections/<chapter>.md` deferred to P2 -- chapter walkthroughs require zone-id finalization from P1's architecture pass"). The corpus state plus the changelog entry together let a maintainer reading either source reconstruct what happened. **For v4 corpora**, the entry also reports the achievement-coverage outcome: total stub count, resolved count, deferred count, unreachable count (e.g. `achievements.md → 47 stubs / 42 resolved / 3 deferred (DLC) / 2 unreachable`). **For v5 corpora**, also report the cross-file consistency sweep outcome: identifiers checked, disagreements found, disagreements reconciled (e.g. `consistency sweep → 12 entities / 47 achievements / 0 disagreements`, or `consistency sweep → 5 entities / 0 achievements / 1 disagreement reconciled (per-entity file disagreed with primary-vector file)`).

### 9. Update `CHECKPOINT.md`

- `Research preferences: cascade-handoff (P1 ingested YYYY-MM-DD from <source-tool>; P2: ingested/pending/skipped; P3: ingested/pending/skipped)`
- Add a `## Harness changelog` entry: which phase was ingested, which subfolders received content, approximate token count, any caveats. **For P2/P3, also list each gap-fill resolution and the corpus file/line it acted on** (e.g. "<claim short-name> -- DROPPED, removed `sections/<chapter>.md` lines 42-44") so the changelog and corpus stay legible against each other.
- **Include step 8's coverage-check results:** every honest empty-statement promotion and every deferral, per that step's "Changelog requirement" clause.

### 10. Refresh downstream briefs (mandatory)

After CHECKPOINT is updated and before the file is moved aside, re-read every `<game>/research_briefs/p<N>.txt` for N greater than the just-ingested phase. For each one:

1. **Hard-code now-established facts.** Anything the just-ingested phase confirmed (zone-id list, chapter ↔ zone mapping, content categories present, localization-mechanism class, NORA / save-station / fast-travel inventory) should be written into the downstream brief verbatim, not left as an open question.
2. **Remove resolved hedges.** Any `if X is true` / `assuming the game has Y` / `confirm whether…` clause whose answer is now known gets deleted or rewritten as a stated fact.
3. **Sharpen open questions.** Questions the downstream brief asked are now scoped against the established context -- researchers should not be asked to re-derive what's already known.
4. **Skip if no downstream brief exists** (e.g. P3 ingested without P2/P3 successors). Skip with a one-line note in the recap.

This step exists because researchers receiving a stale downstream brief will redo upstream work and miss the actual gap. The cascade is only as good as the downstream-brief refresh between phases.

### 11. Move the ingested file aside

Move the ingested file out of `research_inbox/<phase>/` into `research_inbox/<phase>/_processed/` (create the subfolder if needed), renaming it to embed the research date per the **Dated move-aside** rules below. Step 4b bullet 9 (module artifacts) uses the same rules.

#### Dated move-aside

The filename carries the date the research was captured, not the date ingestion ran -- a future maintainer reading `_processed/` should see a snapshot date, not a processing date.

**Destination filename form:** `<original-stem>.<YYYY-MM-DD>.<ext>` (e.g. `compass_artifact_wf-0583e73b.2026-05-08.md`). Appending the date to the existing stem preserves the original name as a grep anchor and keeps files unique when multiple result files share one phase folder.

**Date resolution -- stop at the first rung that yields a date:**

1. **YYYY-MM-DD token already in the filename.** Test against `\d{4}-\d{2}-\d{2}`. If found, extract and re-use it -- the file is already-stamped. Do **not** append a second date token. Re-running ingestion must be a no-op on the name (idempotency).
2. **Research-as-of date from `_source:` lines.** Use the date ingestion already stamps into the `_source: <tool> <YYYY-MM-DD>` metadata of the claims minted from this file -- that is the research-as-of date the operator supplied or the result file carried.
3. **File's last-write timestamp (pre-move).** Read with PowerShell: `(Get-Item "<path>").LastWriteTime.ToString("yyyy-MM-dd")`. Uses the OS-recorded modification date, not the current time.
4. **Processing date (`Get-Date -Format "yyyy-MM-dd"`)** -- last-resort only. If this rung is reached, flag it explicitly in the step-12 recap: "move-aside date fell back to processing time -- may not match research-as-of date."

**Recap requirement:** the step-12 recap must name the move-aside destination filename (including the date token) so the operator can verify the stamped date is correct. Flag any processing-time fallback.

### 12. Show the user a recap

One-screen summary: subfolders touched, sections added per subfolder, any `confidence: medium` flags, downstream briefs refreshed (with a one-line summary of changes per brief), corpus reconciliation actions (which prior-phase claims were dropped / rewritten / superseded -- with file paths), anything the brief asked for that the result didn't cover, and the move-aside destination filename (including the date token; flag if the processing-time fallback was used). **At `corpus-core-version: 5` and later**, also report: entity classes scaffolded this pass (list, or `none`), entity files written or promoted this pass (count + classes), late-emerging classes Stage 0 did not predict (list or `none`), v4 → v5 migration outcomes (`enemies/ → npcs/` rename: yes / no / n-a), and the cross-file consistency sweep outcome from step 8 (identifiers checked, disagreements found, disagreements reconciled). Also sanity-check the first line of every newly-created file to confirm the H1 header rendered cleanly (a class of Write-tool collision artifact that's invisible until a reader opens the file).

**On Windows, run the multi-file sanity-check loop via PowerShell, not Bash.** Git Bash on Windows passes commands through cmd.exe escaping, which strips `$f`-style variable expansion in `for f in ...; do head -1 "$base/$f"; done` recipes -- the loop runs but every iteration reads the literal path `...$f` and errors. Use PowerShell instead: ``$base = "<corpus-path>"; foreach ($f in @("puzzles/chamber_00.md", …)) { Get-Content "$base/$f" -TotalCount 1 }``. (Linux/macOS Bash handles the original recipe fine; this constraint is Windows-only.)

**Update `## Phase state` in CHECKPOINT.** Set the ingested phase's field to `complete YYYY-MM-DD` (e.g. `p1_ingestion: complete 2026-05-12`). If the corresponding brief field is still `not started`, set it to `written YYYY-MM-DD` (the brief existed if ingestion ran). If stitch was previously complete and this ingestion adds new `live-observed` claims, set `stitch_stale: true`.

**Recommended next (conditional on cascade position).** The next step depends on whether this was the final brief in the configured cascade. Check CHECKPOINT's `## Phase plan` / phase-state fields for the configured plan (standard cascade: P3 is the final brief; some games are P1-only or P1+P2).

- **If this was the FINAL brief in the cascade:** append explicitly:

  > **Next:** This was the final research brief. Open a new session in this game folder and run `zipper` and then `stitch` to complete the build. **Stitch is the cascade's audit pass** -- it verifies per-edge convergence across systems and surfaces intra-corpus inconsistencies that ingestion can't see on its own. The build is not done until stitch completes. See [`stitch_and_zipper.md`](stitch_and_zipper.md) for the full procedure. For content-light games with few interacting systems, both passes will be short and cheap; for open-world or mechanic-heavy games, stitch is the difference between a corpus that can answer cross-system questions and one that cannot.

  Then ALSO append the optional pre-stitch sweep pointer:

  > **Optional pre-stitch step:** An additional community-knowledge sweep is available -- start a fresh session at `<game>/` and type `hintforge doctor, reddit sweep` BEFORE running stitch. See [`reddit_sweep.md`](reddit_sweep.md) for the procedure. (Skip if the deep-research cascade already covers your needs; the sweep is most useful when the game has an active subreddit with undocumented interactions, dev posts, or recurring-question signals the cascade missed.) Running the sweep here -- after the final research phase, before stitch -- means stitch's cross-file audit pass operates on the sweep-augmented corpus and catches any propagation gaps the sweep introduces.

  Do NOT invoke the sweep automatically. The pointer is informational; the user runs it manually in a fresh session if they want it. This is the only sweep-invocation path from ingestion -- there is no in-session prompt and no proceed/skip branch.

- **If MORE ingestion is pending** (P1 with P2/P3 still to come; P2 with P3 still to come): do NOT prompt stitch/zipper yet. Stitch on an incomplete corpus wastes a pass -- the next-phase ingestion will add new live-observed claims that re-stale stitch (`stitch_stale: true`). Instead append:

  > **Next:** More research briefs pending in this cascade (check `## Phase state` in CHECKPOINT). Generate / handoff / ingest the next brief before running stitch.

  **Do NOT advertise the reddit sweep in mid-cascade recaps.** Running the sweep between cascade phases (post-P1 with P2 pending, post-P2 with P3 pending) sets up a corpus state where the next phase's step-7 reconciliation must propagate supersessions across files that already carry `status: research-integrated` from a prior phase + sweep mix. The sweep belongs at one of two points: (a) post-final-research-phase, pre-stitch (advertised by the FINAL-brief branch above), or (b) doctor Branch B/C (post-cascade top-ups). Both keep the sweep-augmented corpus out of the mid-cascade ingestion-against-prior-phase-content path.

## Integration discipline (applies across all phases)

- **Research fills empty gates; live-observed wins on conflicts about embodied detail.** When research output and user-flagged live-observed content disagree, embodied detail (in-game text the user transcribed, witnessed sequence, recorded gameplay) wins. Research only fills gaps.
- **Per-file `status:` field is required.** Each output file carries `status: scaffold | research-integrated | live-observed | reconciled` in top-line frontmatter, so the persona and future integrator know what authority the file carries.
- **Architecture-vs-zone-file consistency.** Per-zone files reference the zone graph by edge ID. Edge declarations in zone files must match `architecture.md`'s graph. Drift is lint-checkable; integration includes a consistency pass at step 4.
- **One brief writes to ~5 destination files.** Integration is route-and-distribute, not dump-into-one-file.

## Regeneration safety

When the guide is wiped and regenerated from a refreshed cascade pass, the preservation rule from [`instantiation.md`](instantiation.md) applies: `CHECKPOINT.md`, loadouts, user-flagged live-observed truths, and infrastructure (`.claude/`, PTT/TTS, save-watcher, persona customization) survive. Everything else gets regenerated. Ingestion is the regen path's main mechanism -- it's how the new content lands in the wiped folder.

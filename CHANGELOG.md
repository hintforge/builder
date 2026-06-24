# Changelog

All notable, user-visible changes to the hintforge builder land here.

## Unreleased

### Per-game `CLAUDE.md` dissolved from the universal core; optional platform shims; corpus-core-version 6 (v70, 2026-06-24)

**Format change (`corpus-core-version: 5 → 6`).**

- The universal-core file set no longer includes a per-game `CLAUDE.md`. It drops from ten required files to nine: `CHECKPOINT.md`, `controls.md`, `settings.md`, `mechanics.md`, `limitations.md`, `warning_tiers.md`, `persona.md`, `dependencies.md`, `achievements.md`. A corpus is now agent-agnostic on disk -- no required file is named after any one host.
- `CLAUDE.md` (Claude Code) and `AGENTS.md` (Codex CLI / OpenClaw) become **optional** per-platform auto-load shims: thin pointers that say "this is a Hintforge corpus, load the hintforge-reader skill," with no rules of their own. A corpus is valid with neither, one, or both.
- The per-game harness facts the old `CLAUDE.md` carried already live in neutral homes and stay there: platform in the `game-version-platform` manifest field, persona default in `persona.md`, spoiler-tier semantics in `warning_tiers.md`, spoiler/hint/cite discipline in the reader skill (`principles.md` / `persona_universal.md`). No new required file is introduced.
- The forge watermark (`<!-- forged with hintforge ... -->`) is removed from the shim template; the guide's own `<!-- vN -- date -->` version stamp stays. The `[HINTFORGE_VERSION]` extraction/fill apparatus in the wizard and the instantiation flow is removed with it.
- `docs/corpus-format.md` §1 reconciled: states nine universal files, names the reader's cheap-detection subset, and is the single authority for the universal-file list.

**Builder changes.**

- `templates/claude_md.md` rewritten as the optional Claude Code shim; new `templates/agents_md.md` is the Codex/OpenClaw twin. `setup_wizard.md` and `instantiation.md` copy both, fill `[GAME NAME]`/`[PERSONA1]`/`[PERSONA2]` only, and no longer extract a framework-version watermark. The post-write absolute-path scan covers both shims.
- `templates/checkpoint.md`, `templates/folder_structure.md`, and `CONTEXT.md` updated to describe `CLAUDE.md`/`AGENTS.md` as optional shims and the universal core as nine files.

**Existing corpus impact + migration (doctor Branch A, v5 → v6).** A v1-v5 corpus stays fully readable -- the reader keeps `MIN_SUPPORTED_CORE: 1` and still reads a present `CLAUDE.md` as the harness file on those corpora. To bring an existing corpus to v6, run `doctor hintforge` (Branch A) or migrate by hand:

1. Relocate any unique content from the per-game `CLAUDE.md` to its neutral home -- platform → the `game-version-platform` manifest field; persona default → `persona.md`; any game-specific spoiler-tier note → `warning_tiers.md`. Spoiler/hint/cite discipline needs no relocation (it is reader-side).
2. Replace the `CLAUDE.md` body with the optional-shim shape from `templates/claude_md.md` (identity line + "load the hintforge-reader skill" + neutral-home pointers), and strip the forge watermark from line 3.
3. Optionally add an `AGENTS.md` twin from `templates/agents_md.md` so non-Claude hosts auto-activate the reader too.
4. Bump `corpus-core-version` to 6 in the `## Hintforge manifest` block.

A corpus that skips migration simply stays a readable v5 corpus; nothing breaks.

### Platform-agnostic load-bearing files; version stamp relocated to SKILL.md frontmatter (v68, 2026-06-08)

**Builder changes.**

- `CLAUDE.md` is now a thin platform shim (matches the shape of `AGENTS.md`): identity line, skill location pointer, pointers to neutral homes (`SKILL.md` for all behavioral rules, reader's `principles.md` for universal runtime principles, `docs/corpus-format.md` for the format contract). All behavioral content that was in `CLAUDE.md` -- the setup-wizard routing rule, the "wizard already ran" guard, and the hard-rules block -- has been relocated to the neutral `SKILL.md` where it reaches all bots equally.
- `SKILL.md` frontmatter now carries a `version:` field (`version: 68`). This is the canonical framework version home; the previous HTML comment on `CLAUDE.md` line 2 is retired. Both working-repo copies (`SKILL.md` and `.agents/skills/hintforge/SKILL.md`) are byte-identical.
- `SKILL.md` "Setup flow" section now carries the two routing rules that were only in `CLAUDE.md`: (1) if the guide folder already exists, the wizard has already run -- answer directly; (2) if the folder is empty/missing, read `setup_wizard.md` end-to-end before acting, then run from Step -1.
- Four stale bare references to `principles.md` (a file that lives in the reader skill, not the builder) are repointed to the reader's `principles.md` by full GitHub URL, matching the pattern already correct in `README.md`. Numbered `Principle #N` citations replaced with the rule name. Sites fixed: `os_compatibility.md` (inline prose), `setup_wizard.md` lines 36 and 301, `README.md` lines 207 and 233 and 330. `CLAUDE.md`'s folder-map entry was removed with the thinning.
- `CONTRIBUTING.md` gains a "Platform-agnostic load-bearing files" section so outside contributors inherit the rule.

**Existing corpus impact.** None. No `corpus-core-version` bump and no change to corpus structure. Guides built before this version are unaffected; the relocated rules govern future framework sessions, not corpus content.

### Framework path convention updated to `../../hintforge/builder/`; packaged SKILL.md trigger parity (v66 + v66.1 + v66.2, 2026-06-05)

**Builder changes.**

- The guide→framework breadcrumb convention -- the relative paths written into each guide's `CLAUDE.md` from `templates/claude_md.md` -- now resolves to `../../hintforge/builder/` rather than `../../hintforge/`, reflecting the builder repo living in a `builder/` subdirectory of the framework checkout (alongside the reader at `reader/`). The stale `principles.md` breadcrumb (that file is now reader-side) is repointed to the builder's `CLAUDE.md`, which carries the framework rule set.
- `templates/checkpoint.md`, `instantiation.md`, and `setup_wizard.md` (literal-path-discipline notes, incident reference, and the absolute-path leak-scanner's "correct form" guidance) updated to the `../../hintforge/builder/` convention so the wizard's self-checks stay consistent with what it writes.
- The packaged skill entry point at `.agents/skills/hintforge/SKILL.md` (the copy Codex / OpenClaw / Claude Code install from) was missing the "Hintforge doctor, reddit sweep" activation trigger that the rest of the skill carries; restored so every install path exposes the same triggers.
- `templates/dependencies.md` carried the same breadcrumb in the older single-`../` form (`../hintforge/stitch_and_zipper.md`, stale since guides moved under `Guides/<game>/`); corrected to `../../hintforge/builder/stitch_and_zipper.md` so both guide-facing templates use one convention (v66.1).
- `doctor.md` and `ingestion.md` referenced their own framework files via a stale single-segment `../hintforge/...` path (a leftover from the pre-`Guides/` layout). The operative reads -- `doctor.md` format-bump branch (`docs/corpus-format.md`, `CHANGELOG.md`) and `ingestion.md`'s claim-format read -- are now skill-relative, matching how the rest of the skill references its bundled files; orientation prose in both reworded to state framework files come from the running skill, not a guide-relative path. Two markdown links with stale display text (`ingestion.md`, `setup_wizard.md`) cleaned (v66.2).
- `CHANGELOG.md` now ships with the installed skill (was repo-only). `doctor.md`'s format-bump branch reads it at runtime to find the per-version migration for each `corpus-core-version` step, so it must be present in the deployed skill, not only the source repo (v66.2).
- `CLAUDE.md` line 2 bumped v65→v66→v66.1→v66.2.

**Existing corpus impact.** No `corpus-core-version` bump and no change to corpus structure. Guides built before this version carry the old `../../hintforge/` breadcrumb in their `CLAUDE.md`; if your framework checkout places the builder under `hintforge/builder/`, update those breadcrumb paths to `../../hintforge/builder/...` (the `principles.md` reference becomes `../../hintforge/builder/CLAUDE.md`). Guides built after this version ship the corrected paths.

### Setup wizard: manifest-artifact gate, player-name prose enforcement, deterministic handoff (v65, 2026-06-02)

**Builder changes.**

- `setup_wizard.md` Step 9 gains a **manifest-artifact gate**: after the file writes, setup verifies on disk that the architecture manifest (carrying `corpus-core-version`) exists -- `nav/architecture.md` when nav is created, `architecture_manifest.md` when nav is skipped -- and refuses to print the Step 10 handoff if it is missing, writing it from `templates/architecture.md` instead. Previously the nav-skip fallback manifest could be dropped silently, leaving a corpus with no machine-readable core-version / game-version. A `Manifest:` row is added to the Step 9 confirmation summary so the target is a visible commitment.
- `setup_wizard.md` enforces the existing no-substitution rule for the player name in corpus prose. A new "Literal-prose discipline" note states the name is written only to `CHECKPOINT.md`'s `**Name:**` field; the post-write sanity scan is extended from a `CLAUDE.md`-only absolute-path check to a corpus-wide scan that rewrites any stray player-name substitution back to "the player" before the handoff.
- `setup_wizard.md` Step 10 handoff is made deterministic: the "show verbatim" directive becomes a required-blocks checklist (a)-(h) the wizard self-verifies before sending, and a canonical "What was built" table -- built deterministically from the actual scaffold -- becomes a required block in every run. Folder-reference wording is frozen.
- `setup_wizard.md` Manifest-section instruction no longer hardcodes a `corpus-core-version` literal; it draws the value from `templates/architecture.md` instead (documentation correction only).
- Documentation + templates: scrubbed internal development references (private-workspace paths, benchmark/session notes, a build-specific incident) and replaced game-title examples with game-type descriptors across `docs/corpus-format.md`, `compaction_policy.md`, `ingestion.md`, `templates/claim_format.md`, `setup_wizard.md` rationale, and prior changelog entries, per the game-agnostic content rule.
- `CLAUDE.md` line 2 bumped v64→v65.

**Existing corpus impact.** Setup-time behavior only; no structural change to existing corpora and no `corpus-core-version` bump (templates are unchanged). Guides built after this version always ship an architecture manifest, keep the player's name out of corpus prose, and receive a complete, consistent fresh-session handoff. Existing guides are unaffected until rebuilt -- the manifest and player-name checks run at setup, not retroactively.

### Ingestion: Fandom ladder rung 1 corrected (api.php form) + Parse API rung added + vocab synced (v64, 2026-06-01)

**Builder changes.**

- `ingestion.md` Fandom ladder rung 1 URL pattern corrected to `api.php?action=query&export=1&titles=<Page>`. The prior `/wiki/Special:Export` HTML form is Cloudflare-gated and fails ~100% from cloud-hosted runtimes; the api.php form is not. Rung text now carries an explicit warning so a maintainer does not re-discover the block by hitting the HTML form first.
- `ingestion.md` Fandom ladder gains a new rung 2 ("`api.php` Parse API", `api.php?action=parse&page=<Page>`); existing BreezeWiki / archive.ph / manual-paste rungs renumbered 2-4 → 3-5. First-party endpoints (export + parse) now walk before the third-party BreezeWiki front-end.
- `ingestion.md` capture-method vocab list (step 5 inline-metadata field meanings) synced to include `mediawiki_parse` -- six values, matching the authoritative list in `templates/claim_format.md`.
- `setup_wizard.md` Step 8 P1 brief generation gains a one-line maintainer note: expected Fandom fetch failures from cloud runtimes route to the `ingestion.md` ladder, not direct fetch.
- `CLAUDE.md` line 2 bumped v63→v64.

**Existing corpus impact.** Procedure change for future Fandom captures; no historical-corpus impact and no `corpus-core-version` bump (the `mediawiki_parse` value already shipped in `claim_format.md` 2026-05-20). Maintainers running ingestion against Fandom-sourced content after this version use the working URL forms and have the Parse API rung available. Closes hintforge#7.

### Reddit sweep: cap raised to 300, skip-without-counting filter for memes/fan-art/cosplay, browse-to-search pivot heuristic (v60, 2026-05-27)

**Builder changes.**

- `reddit_sweep.md` -- posts-evaluated hard cap raised from 100 to 300. The original 100-post cap was sized presuming most browse-scanned titles would be at least finding-candidate; in practice on meme-heavy or sequel-heavy subs ~60-75% of the budget was structurally wasted on top-sort feeds dominated by content L188 ("does not qualify") rejects. 300 gives breathing room; the per-window floors (15 / 10 / 7 / 0-5) and MCP-pacing math are unchanged.
- `reddit_sweep.md` -- NEW §"Skip-without-counting (browse-scan time filter)" section under §Sweep traversal. Defines an explicit list of OP-flair labels (`Memeposting`, `Fan Art`, `Cosplay`, `Screenshot`, `Art`, `Gif`, `Video`, plus game-specific variants of the same intent) and title patterns (`i made` / `i drew` / `my cosplay` / `[OC]` / `[Fan Art]` / `[Cosplay]` / pure-opinion titles ending in `?` / rant-shaped titles) that are filtered at browse-scan time and DO NOT count against the cap. Edge-case openers documented (memeposts with build-discussion content in OP body or top comment; dev-flair posts; posts with build/mechanic/patch/bug/interaction keywords) -- the rule is conservative, opens-on-doubt.
- `reddit_sweep.md` -- NEW §"Browse-to-search pivot heuristic". When 5+ consecutive titles in a single browse-list batch are skipped under §Skip-without-counting, terminate the browse-list and pivot to `search_reddit` with mechanical-content queries. Per-browse-list trigger, not per-window; multiple batches within a window each evaluate independently. The heuristic operationalizes a manual browse-to-search pivot observed on meme-heavy and sequel-heavy subreddits.
- `reddit_sweep.md` user-facing messages -- budget envelope L73 now surfaces "300 posts evaluated, ~45-90 MCP requests typical, ~12-15 min anonymous / ~3-5 min app-only / ~2-3 min authenticated"; Start message names the skip-without-counting filter + browse-to-search pivot; Budget exhaustion message reports `<S>` titles skipped without counting; new "Browse-to-search pivot" progress marker.
- `reddit_sweep.md` template frontmatter -- new field `posts_skipped_without_counting: <S>` (informational; counts browse-scan-time filters); `posts_evaluated: <N> / 300` (was `/ 100`).
- `CLAUDE.md` line 2 bumped v59→v60.

**Existing corpus impact.** Next reddit sweep will run against the 300-post cap with the skip-without-counting filter applied at browse-scan time. Previously-written sweep artifacts (`research_inbox/module/_processed/reddit_sweep.<game>.*.md`) carry the old `posts_evaluated: <N> / 100` frontmatter -- harmless; the value is informational. Doctor's Phase state field `module_sweep_reddit: complete <date>` is unaffected (the flag tracks completion, not budget shape). The two finding-qualification layers (browse-scan-time skip + finding-acceptance-time exclusion) are independent; corpora that already absorbed reddit sweep findings see no change to those findings. The fallthrough rule (main sub <=20 findings → broader sub) remains gated on findings count, not cap consumption -- a 300-post cap means more headroom for fallthrough to complete within the same sweep.

### Reddit community sweep phase + module-sweep phase-state + doctor wiring (v53, 2026-05-24)

**Builder changes.**

- `reddit_sweep.md` -- NEW top-level procedure file. Autonomous post-P1 community-knowledge harvest via the `reddit-mcp-buddy` MCP server. Covers MCP-reachability pre-flight (CC runtime, not Desktop -- distinct configs), auth-tier detection + pacing (anonymous 10/min, app-only 60/min, authenticated 100/min), subreddit identification with main-then-broader fallthrough (single pass, no chaining), four-window top-sorted traversal (all-time -> year -> month -> week) with per-window floors 15/10/7/0-5, dual-budget model (100-post hard cap on attention; MCP-requests pace against the tier), recurring-question signal across windows, user-confirmed ingestion gate. Findings file lands at `<game>/research_inbox/module/reddit_sweep.<game>.<ISO-date><N>.md`; never overwrites (re-runs increment same-day suffix). First framework procedure with an external MCP dependency -- transparent-operations rule applied (abort cleanly if MCP unreachable; never crawl silently).
- `ingestion.md` -- gains step 12b "P1-only: Reddit community sweep" between step 12 (recap) and Integration discipline. Invokes `reddit_sweep.md` after P1 recap with user consent + budget envelope surfaced up front; skip path leaves a one-line recap note. Also gains step 4b "Ingesting a reddit_sweep artifact" between step 4 and step 5 -- alternate distribution path for `kind: reddit_sweep` artifacts. Maps the artifact's `claim_kind` enum onto corpus vector tags + overlays (mechanic / bug-with-medium-confidence-floor / build / interaction / strategy-by-Finding-shape / dev-confirmation / lore-question / other). Routes per-source `reddit_spoiler_tag` evidence to step 3's spoiler-classification sub-agent. Recurring-question entries become claims under `vector: lore` (narrative-shaped) or `vector: mechanic` (mechanically-shaped) with recurring nature captured in `notes:` -- no new vector introduced. Threads-scanned appendix is inbox-only (never ingested). Step 1 gains a frontmatter-aware routing branch for `kind: reddit_sweep` files. Reddit blocked-source paragraph gains a one-line cross-ref distinguishing per-thread-citation ladder from autonomous-sweep path.
- `doctor.md` -- Branch B section 1 gains a fourth bullet (community-knowledge-shaped game-update content) that offers `reddit_sweep.md` invocation with a `scope-query` parameter as a supplement to (not substitute for) the targeted-brief path. Section 2 notes DLC sweeps should run AFTER architectural extension lands so findings have homes to route to. Branch C section 2 gains a fourth depth-of-fix option (community-knowledge-shaped gap) routing to the same scope-queried sweep. Doctor falls back to brief-only if `reddit-mcp-buddy` is unreachable.
- `templates/folder_structure.md` -- documents `research_inbox/module/` (sibling to `p1/`, `p2/`, `p3/`) as the home for autonomous-sweep artifacts. Names the distinction: phase folders consume external-research-tool result files; module folders consume framework-internal sweep artifacts.
- `templates/checkpoint.md` -- adds `module_sweep_<kind>` family of Phase state fields. First member: `module_sweep_reddit`. Future supplemental research modules (YouTube transcripts, currently-inaccessible-wiki sweeps, etc.) add their own `module_sweep_<kind>` line as they ship. Doctor reads any `module_sweep_*` field for drift detection.

**Existing corpus impact.** P1 ingestion sessions now offer (not auto-run) a Reddit community sweep at the end of P1 recap. Existing corpora are unaffected until the user opts into a sweep -- gated behind explicit consent at MCP-reachability check + budget-envelope surface + post-sweep ingestion confirmation. Corpora carrying `research_inbox/p<N>/` continue working unchanged; `research_inbox/module/` is created on demand. Existing CHECKPOINT files without the `module_sweep_<kind>` fields work fine -- ingestion's step 4b adds the field for the relevant `<kind>` on first ingestion of a module-sweep artifact. Doctor's Branch B and Branch C now offer the sweep as a supplemental retrieval path for patch / DLC / community-knowledge-shaped gaps; user chooses brief, sweep, or both. Reachability of the `reddit-mcp-buddy` MCP server in the Claude Code runtime (not just Claude Desktop) is a prerequisite for the sweep path; absent that, doctor and ingestion both gracefully decline and route to the brief-only path.

### Stitch adversarial gates: post-write contradiction check + propagation check (v52, 2026-05-24)

**Builder changes.**

- `stitch_and_zipper.md` Phase B step 4 "Find new edges" -- gains a mandatory **post-write contradiction check**. After writing a new edge, model extracts the edge's specific claim values and `grep -rn` for each one across the whole corpus (not just cited sources). Matches in uncited files are classified: supporting source -> add to source column; contradiction -> add to `## Corpus inconsistencies`; different legitimate use -> noted and skipped. Catches the inverse defect class where an edge agrees with cited sources but disagrees with non-cited ones.
- `stitch_and_zipper.md` Phase B step 5 -- new sub-step **5c "Propagation check"** between 5b (resolve) and 5d (write run log + CHECKPOINT; was 5c, renumbered). After every edge-text correction in 5b, model must `grep -rn "<old-value>"` and classify every match as updated / different-legitimate-use / new-inconsistency. Tracked in the audit trail. Completion gate (5a) extends to cover `propagation-done == edge-text-corrections-in-5b`.

**Existing corpus impact.** Next stitch run will: (1) post-write grep new edges against the corpus, potentially expanding source columns or surfacing fresh `## Corpus inconsistencies` rows; (2) propagation-grep each edge-text correction in step 5b, potentially fixing old wrong values living in inline cross-refs that prior stitch passes did not catch. Both gates are additive -- existing edges/values are not disturbed.

### Doctor inherited-state audit + stitch column-count lint (v51, 2026-05-24)

**Builder changes.**

- `doctor.md` -- §6 gains a mandatory "Audit inherited state" sub-step. Before declaring §6 complete, doctor scans the last 5 CHECKPOINT changelog entries against the §6 flag-decision rules table; backfills Phase state flags for any prior finding that would warrant one under current rules but doesn't have one set. Mechanical, not judgment-based. Closes the gap where procedure changes apply only to new doctor findings; inherited recommendations made under retired rules stayed misclassified.
- `stitch_and_zipper.md` -- Phase B operational sequence gains step 3b "Dependencies-file structural lint" between corpus size check and per-edge audit. Verifies `|`-delimited table integrity in `dependencies.md` (column count per table); surfaces mismatched rows (typically edges written under the wrong table's schema) with file:line. Does not auto-fix; flags for user/doctor branch C repair.

**Existing corpus impact.** Next doctor run will backfill any missing Phase state flags from recent changelog entries (additive only -- no flag removed). Next stitch run reports any column-count mismatches in `dependencies.md` before the per-edge audit; legacy corpora with misplaced edge rows get a one-shot visible signal at the next stitch invocation.

### Doctor: Phase state authority (v50, 2026-05-23)

**Builder changes.**

- `doctor.md` -- Section 6 rewritten. Doctor can now set any Phase state flag (`stitch_stale`, `stitch_scope`, `p[N]_ingestion`, `zipper`, `stitch`) when findings warrant re-running a cascade process. Includes a decision table mapping finding types to flags, and the run-vs-flag rule. Prior version only covered running stitch directly.

**Existing corpus impact.** Next doctor run may set Phase flags in the corpus CHECKPOINT, signaling that a cascade process should re-run. No manual migration -- doctor's expanded authority activates automatically.

### Stitch: procedure hardening -- re-audit scope, surface-not-resolve, completion gate, Phase C removal (v46-v49, 2026-05-23)

**Builder changes.**

- `stitch_and_zipper.md` -- v46: re-run scope made explicit (re-audit covers all existing edges in `dependencies.md`, not just new candidates). v48: audit surfaces inconsistencies without resolving during the walk (surface-not-resolve discipline); mandatory completion gate added (enumerate edge IDs from disk, reconcile against audit-done list before writing run-log row). v49: Phase C ("resolve inconsistencies" as separate trigger) removed; resolution now auto-runs after the completion gate passes.
- `templates/dependencies.md` -- v47: line-3 comment rewritten from "re-running stitch adds new rows; it does not re-evaluate old ones" to match the re-audit-all scope established in v46.

**Existing corpus impact.** Next stitch run will: (1) re-audit every edge in `dependencies.md`, not just newly discovered candidates; (2) surface inconsistencies to `## Corpus inconsistencies` without auto-resolving during the audit walk; (3) run a completion gate before writing the run-log row. Existing `dependencies.md` files carrying the pre-v47 line-3 comment are rewritten on next stitch run.

### Cascade audit: dependencies.md columns + ingestion index re-derivation (v45, 2026-05-23)

**Builder changes.**

- `templates/dependencies.md` -- Run-log table gains an `Inconsistencies surfaced` column. New `## Corpus inconsistencies` section for contradictions found during stitch audit (rows added by audit, cleared by resolution).
- `ingestion.md` -- Step 8 gains `#### Index re-derivation` sub-pass: re-reads each touched `index.md` + its referenced entity files, verifies roster cells, prose counts, and file-existence claims. Step 12's stitch-and-zipper prompt is now conditional: if final brief in the cascade, frames stitch as "the audit pass"; if more ingestion pending, says so instead of prompting stitch prematurely.
- `stitch_and_zipper.md` -- Phase B write threshold extended from "convergence on topic mention" to "convergence on the specific value being written." Stitch summary derives counts from disk (re-grep `dependencies.md`), not from memory.

**Existing corpus impact.** Next stitch run creates the `## Corpus inconsistencies` section in `dependencies.md` if absent. Future run-log rows include the `Inconsistencies surfaced` column; existing rows stay as-is, no backfill required.

### Wizard + templates: `player_address` retirement + game-name scrub (v43, 2026-05-23)

**Builder changes.**

- `setup_wizard.md` -- Step 1.5's "Are you a boy/girl/something else?" question removed; `[PLAYER_ADDRESS]` plumbing removed from variable table, batching, skip rule, and Step 9 summary. Game-specific names scrubbed from normative text across 9 files.
- `templates/checkpoint.md` -- "Address style" bullet removed from player profile section.
- `setup_answers.txt` -- `player_address` block removed.

**Existing corpus impact.** Existing corpora may carry a `player_address` key in `setup_answers.txt` and an "Address style" bullet in their CHECKPOINT. Both are dead fields -- harmless to leave, safe to remove at next doctor run or manually. Persona address-style defaulting falls back to `persona.md` / `persona_universal.md`.

### Ingestion: `last_reconciled` bump on edits + cross-file consistency sweep (v42, 2026-05-23)

**Builder changes.**

- `ingestion.md` -- Step 4: one-sentence rule added -- when editing an existing claim-bearing file, also update `last_reconciled:` to today's date. Step 8: new gated sub-step "Cross-file consistency sweep" -- grep entity-ids, achievement-ids, missable flags, and status-flag overlays across the corpus and reconcile disagreements before declaring the step complete.

**Existing corpus impact.** Both rules activate automatically at next ingestion run. No manual migration needed.

### Wizard: drop dead "hand off to someone else" option from handoff closer (v40, 2026-05-22)

**Builder changes.**

- `setup_wizard.md` -- Step 8 handoff sub-procedure, Step 3 verbatim closing message: removed Option B ("Hand off to someone else") entirely. The remaining single path is the "Run it yourself" steps with the claude.ai Filesystem-connector shortcut refolded underneath as a sub-bullet. Also dropped two minor sloppiness items in the same block: the wizard-meta parenthetical "(Recommendations as of May 2026 -- benchmarks shift; substitute freely.)" and the "Recommended *external* tool" wording.

**Reasoning.**

- **Option B posited a workflow nobody uses.** "Send p1.txt to a friend, they go run deep research on your video game, drop the result file in your `research_inbox/`." For hobby game guides this is not a realistic path; it's an artifact of "handoff mode" being conceived as "wizard hands off to *someone*" rather than "user runs the brief through a deep-research tool." Keeping it as a coequal option diluted the actual operational instructions on the most important screen the user sees on session exit.
- **Visual placement matters here.** The claude.ai Filesystem-connector shortcut was wedged *between* Options A and B in the prior layout, so it visually belonged to neither. With B gone, the shortcut sits cleanly as a sub-bullet under the single path of numbered steps.
- **No corpus-version bump.** This is user-facing wizard copy only; no template, claim format, or universal-core change.

**Migration.** None. Briefs already generated against the prior wizard are unaffected -- the closing message is a one-shot session-exit instruction, not a referenced artifact.

### Brief: Reddit fetch ladder for blocked deep-research backends (v40, 2026-05-22, no corpus-version bump)

**Builder changes.**

- `setup_wizard.md` -- Step 8 P1 brief generator gains a new `Blocked-source access -- Reddit fetch ladder` sub-block between `Source diversity floor` and `Output format`. Tells the deep-research tool that `www.reddit.com` is 403'd from datacenter-IP backends, and gives a four-rung ladder to walk on a Reddit URL failure: `old.reddit.com/.../` -> `old.reddit.com/.../.json` -> `archive.ph` snapshot -> explicit unreachable flag. Try once per rung; no retry loops, no header rotation, no paid scrapers. Citation rule: record the canonical `reddit.com` URL regardless of which rung returned content.

**Reasoning.**

- **Why a research-phase fix, not an ingestion-phase fix.** The v1->v2 milestone's Reddit policy (manual paste default; `archive.ph` fallback; `.json` workaround intentionally omitted) was about how a *contributor* captures Reddit content during ingestion. That remains correct. This is a different failure surface: external deep-research tools (Gemini DR, Claude Research, Perplexity, ChatGPT) have no human-paste fallback, get 403'd on `www.reddit.com` from their hosted backends, and silently drop the source-class (b) requirement instead of routing around the block. The brief is the only place we can instruct them.
- **Why `.json` is reinstated here despite being dropped from the ingestion ladder.** The over-engineering concern that justified dropping `.json` from the ingestion ladder ("invites future contributors to write retry loops") does not apply: the brief is consumed once per research run by a tool that does not retain workflow. There is no maintainer process to over-engineer. The rung is also single-shot by construction -- "try once, do not retry" is in the brief text.
- **Why explicit unreachable flag instead of silent skip.** Source-class (b) is a research-quality contract. Silently failing on Reddit lets the deep-research tool satisfy "minimum 5 sources" with five wiki / editorial-only sources, drifting away from the diversity floor without flagging it. The explicit flag preserves the diversity floor's enforceability downstream.

**Migration.** None. Briefs generated against the prior `setup_wizard.md` produce result files that ingest cleanly under the existing `claim_format.md` rules; nothing in the claim format or universal core changes. Re-running the wizard for a new game guide picks up the new brief language automatically.

### Template: `lookahead_cache:` slot in `player_position` block (2026-05-21, no corpus-version bump)

**Builder changes.**

- `templates/checkpoint.md` -- adds a nested `lookahead_cache:` block inside `player_position` with five fields (`computed_at_position`, `computed_at`, `next_gates`, `pnr_warnings`, `notes`) plus a short prose paragraph explaining the contract. Lets the reader skip the zone-graph walk at session start by caching N-gate lookahead results during `checkpoint`/wrap and reading them back on next session entry. Block is additive and optional; absence on existing CHECKPOINTs is treated as "stale -- recompute on first nav-relevant turn" by the reader.

**Reasoning.**

- **Why no version bump.** This is a CHECKPOINT-format addition, not a corpus-core-format change. The universal-core file count, the manifest contract, and the claim-tag syntax are unchanged. Readers that don't understand the cache block treat the absence as the "stale" case and compute lookahead lazily anyway -- the optimization simply doesn't trigger.
- **Why a slot in the template, not just in the reader's docs.** New corpora scaffolded by the wizard need the block present from creation so the reader's cache-write step on first wrap doesn't have to also know how to insert YAML structure into an arbitrary CHECKPOINT. Slot-present-but-empty is cheaper for the reader than slot-absent.

**Migration.** Existing CHECKPOINTs continue to work. Maintainers who want session-entry-fast behavior on an existing guide can add the empty block under `player_position` manually; the next `checkpoint`/wrap will populate it. No coordinated upgrade is required -- reader and builder roll independently. See the reader CHANGELOG's matching entry for the runtime contract.

### `corpus-core-version: 4 → 5` -- entity overlay as named-NPC aggregation skeleton; `enemies/` folded into `npcs/` (2026-05-22)

**Builder changes.**

- `templates/claim_format.md` -- adds three optional claim-level overlay fields for named-entity aggregation: `entity:` (repeatable, names the subject the claim is about), `entity-hidden:` (`yes | no`, optional; surfaces a per-entity hidden flag so the renderer can gate the entity's name at read-time the way `achievement-hidden:` does for achievements), and `entity-status:` (one of `hostile | friendly | convertible | party | neutral | unspecified`; required when the entity's class folder is `npcs/`, optional for the parallel non-individual classes). Adds a new "When `entity:` applies -- the named-individual rule" section covering when a combat NPC qualifies for its own per-entity file vs stays generic and routes via the `enemy` vector to `mechanics.md`. Evolution section bumped to v5.
- `templates/entity_index.md` -- new template, scaffold for `<class>/index.md` (per-class roster index). Carries class definition, roster table (entity-id, display name, entity-status, status, first-encounter zone, missable), and pointer rules. One file per entity class.
- `templates/entity_summary.md` -- new template, scaffold for `<class>/<entity-id>.md` (per-entity summary file). Carries entity frontmatter (entity-id, class, entity-status, entity-hidden, first-encounter zone) and sections for Recruitment/Access, Capabilities, Quests, Achievements, Combat (when status is hostile or convertible), Missability, Status history (when status is convertible / party / neutral), and See also back-pointers.
- `templates/architecture.md` -- `corpus-core-version` stamp bumped from `4` to `5`. New corpora produced by the wizard will carry the v5 stamp from creation.
- `setup_wizard.md` -- Step 6.7 (Stage 0 §5) gains four new structural-priors signals: `Named-NPC density` (high/medium/low; cheap proxy = proper-noun count in walkthrough chapter summaries; structural signal = party-size + recruit/companion system presence), `Faction density` (high/medium/low), `Crew-system signal` (yes/no), and `Reputation-system signal` (yes/no). Step 7's subfolder checklist replaces the prior `[ ] Enemies / combat encounters worth indexing (creates enemies/)` checkbox with `[ ] Named entities worth aggregating individually -- NPCs, factions, crew roles, reputation systems` (creates `npcs/`, `factions/`, `crew/`, or `reputation/` per Stage 0 §5 signals). The auto-pop rule for `enemies/` is replaced with a `<entity-class>/` auto-pop rule driven by the four Stage 0 §5 signals, including a v4-to-v5 migration note (existing `enemies/` folders are renamed to `npcs/` at ingestion step 2.5; existing content gets `entity-status: hostile`).
- `ingestion.md` -- new Step 2.5 (entity-scaffold check) between Step 2 (read brief + result) and Step 3 (spoiler classification): verify each Stage-0-flagged entity class has its `<class>/` folder; scaffold from `templates/entity_index.md` if absent; rename `enemies/` to `npcs/` for v4-migrated corpora (one-time, mechanical) and annotate existing content with `entity-status: hostile`; scan the just-read result for late-emerging classes Stage 0 did not predict and scaffold them too. Step 3's spoiler-classification sub-agent gains a new job item (entity-overlay emission): when a fact concerns a named entity scaffolded under a class folder, emit `entity:`, `entity-status:` (required when class is `npcs/`), and `entity-hidden:` alongside the spoiler tag, applying the named-individual rule from `claim_format.md`. Step 4 gains a forward-pointer rule: claims with an `entity:` overlay append a one-line `> see <class>/<entity-id>.md` cross-ref to the primary-vector destination, with explicit clarification that the `enemy` vector and the entity overlay are orthogonal axes (vector handles generic-mob combat, overlay handles named-NPC aggregation). Step 7's reconciliation grep destinations gain `<entity-class>/` folders alongside `sections/`, `items/`, `nav/`, etc. Step 8's universal-core aggregation rules gain `<entity-class>/<entity-id>.md` -- auto-built from `entity:` overlay claims, three end-states (populated / stub / unreachable), hidden-entity rule (full content written, read-time gating), status-history rule for `npcs/` entries so status changes during play append rather than rewrite. Step 12's recap reports entity classes scaffolded, entity files written, late-emerging classes Stage 0 missed, and v4-to-v5 migration outcomes.
- `docs/corpus-format.md` -- §3 Versioning gains a v5 entry covering the three new overlay fields, the per-class aggregation contract, the `enemies/ → npcs/` migration, and the `MIN_SUPPORTED_CORE: 1` posture that keeps v1-v4 corpora reading cleanly under v5-capable readers.

**Reasoning.**

- **Why overlay, not vector extension.** Vector extensions (puzzles, endings, paths) work when content has one obvious vector home; a puzzle fact IS the puzzle. Entity content competes: a companion-recruitment fact is plausibly `nav`, `missable`, AND `entity`. Making `entity` a primary vector would force ingestion into a routing judgment call per claim, and different ingestion runs would route the same claim differently -- producing exactly the per-entity fragmentation across 10-12 files that this version exists to fix. Overlay preserves the primary-vector routing and attaches `entity:` alongside; one claim, one primary home, one tier tag, plus aggregation. This is the same architecture as the v3 → v4 `achievement:` overlay.
- **Why fold `enemies/` into `npcs/` instead of leaving them as separate classes.** Game-designer-shaped naming treats hostility as a state on an NPC, not a class identity. Conversion mechanics (recruitable-enemy patterns common across CRPGs and party-based RPGs) and companion-betrayal mechanics (companions who become hostile under specific choices) both require one entity file per NPC with status as a field; separate `enemies/` and `companions/` classes would re-fragment the very entities the version exists to consolidate. The existing `enemies/` folder also lacked a formal aggregation rule (sparse-handwritten `index.md`); folding it into `npcs/` with the entity-overlay aggregation contract finishes the work that folder was halfway through. Cost is small -- a one-time rename in ingestion step 2.5 plus the `entity-status: hostile` annotation rule on first touch.
- **Why bump the version.** New claim-level fields, new universal-core-adjacent ingestion contract (per-class folders auto-built from overlay claims), and a structural change to where `enemies/`-class content lives. Older readers don't know to route entity queries to `<class>/<entity-id>.md` and don't recognize the new fields. Per the v3 → v4 precedent (new universal-core file + new required-when-present claim fields), both conditions qualify as breaking for older readers.

**Migration.** Existing corpora at `corpus-core-version: 1`, `2`, `3`, or `4` continue to work with v5-capable readers (the reader treats absent entity overlays and missing class folders as "no entity aggregation in this corpus" rather than as an error; no warning fires because v1-v4 stay inside the supported range). Maintainers updating a corpus to v5 must: bump the `corpus-core-version` stamp in `nav/architecture.md`'s manifest block to `5`; for each entity class Stage 0 flagged as high-dependency, scaffold `<class>/index.md` from the new template; rename any existing `enemies/` folder to `npcs/` (mechanical; ingestion step 2.5 performs this automatically at next phase ingestion) and annotate existing files with `entity-status: hostile` on first touch; optionally backfill `entity:` overlays on existing claims as time allows. Backfill is not required for the corpus to validate at v5, only for the per-entity files to be useful. The Coverage check in [`ingestion.md`](ingestion.md) step 8 recognizes an empty-scaffold `<class>/index.md` paired with zero entity-tagged claims as "v4-to-v5 migration in progress" and writes the honest empty-statement rather than firing the silent-scaffold-forbidden error.

### `corpus-core-version: 3 → 4` -- achievements as universal-core completeness skeleton (2026-05-21)

**Builder changes.**

- `templates/achievements.md` -- new template, universal-core scaffold for the new root file. Organized by `trigger_type` (six H2 sections: `Progression | Branch | Mastery | Collection | Threshold | Discovery`). Stamped with `stub_source:` / `stub_fetched:` frontmatter so corpora carry an honest provenance trail back to the platform list they were built against.
- `templates/claim_format.md` -- adds four optional claim-level fields: `achievement:` (repeatable, names a platform achievement the claim documents the trigger for), `achievement-hidden:` (required when `achievement:` is present; surfaces the platform's hidden flag), `trigger_type:` (required when `achievement:` is present; one of six values), and `genre:` (optional, repeatable, open vocabulary). Evolution section bumped to v4.
- `templates/architecture.md` -- `corpus-core-version` stamp bumped from `3` to `4`. New corpora produced by the wizard will carry the v4 stamp from creation.
- `setup_wizard.md` -- Step 6.7 (Stage 0) gains a new sub-step 4 fetching the platform's canonical achievement list and writing it twice (to `<game>/achievements.md` as scaffold body, and to `<game>/research_briefs/achievement_stubs.md` as a flat fetch-time artifact). New captured variable `[ACHIEVEMENT_STUB_COUNT]`. Step 7's manifest description updated to stamp `corpus-core-version: 4`. Step 8 P1 brief generator gains Standing prompt #9 (Achievement coverage) inside the chapter-organized-facts section and adds an `[ACHIEVEMENT_STUB_COUNT]` field to the brief's Architecture Summary so the researcher knows the size of the coverage problem upfront. Step 9 always-created file list gains `achievements.md`; Step 9 summary table gains the `Achievement stubs:` row as an enforcement-gate variable.
- `ingestion.md` -- step 4 vector tag taxonomy gains `achievement` as an overlay tag (same shape as `missable`), combinable with primary vectors via `vector: nav, achievement: <id>` or `vector: item, achievement: <id>, missable: yes`. Step 8 universal-core coverage check gains `achievements.md` with aggregation-from-overlays logic (the three valid end-states: resolved / deferred / unreachable), trigger-type classification of stub entries into the six H2 sections, and the honest-empty-statement fallback when Stage 0 was skipped. The step 9 changelog requirement extends to report achievement coverage outcome (stub count, resolved, deferred, unreachable). The combat-tactics line in step 3's spoiler-classification pass now cross-references the new overlay so missable-achievement preconditions route to `achievements.md` rather than orphan.
- `docs/corpus-format.md` -- §1 universal-core file list gains `achievements.md` (file count bumped from nine to ten). §3 Versioning gains v4 entry. §4 Claim format gains the new "Achievement overlay" subsection covering the four new fields.

**Reasoning.**

- **Why universal-core, not vector extension.** Achievement triggers bind to existing corpus structures (zones, chapters, items, scenarios); a `/achievements/` folder would duplicate content. A root-level aggregation file pointing back to canonical claim homes via `vector-binding` avoids the duplication while still giving the reader a single source of truth for achievement-class queries.
- **Why universal, not opt-in.** Nearly every shipped video game on a major platform has an achievement list. The exceptions (some indie titles without Steam achievements, some older console releases) handle gracefully via the scaffold-with-honest-empty-statement path -- the file is created universally, and Stage 0 records `[ACHIEVEMENT_STUB_COUNT] = 0` for the rare game that genuinely lacks them. Making it opt-in produces partial guides for the median game.
- **Why two-part (overlay + file), not just file.** The aggregation file is a synthesis; the overlay field is the source. Editing only the file loses the connection between achievement and its canonical claim home (the reader could not answer "where in the guide is the trigger detail?"). Editing only claims requires the reader to walk the entire corpus to answer any achievement-class query. Both layers are load-bearing.
- **Why six `trigger_type` values, not three or twelve.** The six categories (`progression | branch | mastery | collection | threshold | discovery`) emerged from a survey of 18 games across 12 genres. Each value drives a distinct reader response and imposes a distinct ingestion contract; merging any pair hides those distinctions. Compression to fewer types was tested and rejected because it would hide the completeness contracts the spec exists to enforce. Vocabulary-size risk is mitigated by ordered decision questions and three explicit disambiguation rules at the boundaries with highest mislabel risk (rules live inline in [`ingestion.md`](ingestion.md) step 8).
- **Why bump the version.** New universal-core file the reader hard-codes; new required-when-present claim fields. Both are breaking conditions for older readers per [`docs/corpus-format.md`](docs/corpus-format.md) §3.

**Migration.** Existing corpora at `corpus-core-version: 1`, `2`, or `3` continue to work with v4-capable readers (the reader treats a missing `achievements.md` as "no achievement tracking in this corpus" rather than as an error; no warning fires because v1-v3 stay inside the supported range). Maintainers updating a corpus to v4 must: bump the `corpus-core-version` stamp in `nav/architecture.md`'s manifest block to `4`; create `achievements.md` from the v4 template; fetch the platform's achievement list manually (Stage 0's auto-fetch only runs at initial setup -- this is the migration path); optionally backfill `achievement:` overlays on existing claims as time allows. Backfill is not required for the corpus to validate at v4, only for the aggregation file to be useful. The Coverage check in [`ingestion.md`](ingestion.md) step 8 will recognize an empty-scaffold `achievements.md` paired with a missing stubs file as "v3-to-v4 migration in progress" and write the honest empty-statement rather than firing the silent-scaffold-forbidden error.

### `corpus-core-version: 2 → 3` -- required `game-version`, `game-version-platform`, `game-version-as-of` manifest fields (2026-05-20)

**Builder changes.**

- `templates/architecture.md` -- `corpus-core-version` stamp bumped from `2` to `3`. The `## Hintforge manifest` block gains three new required fields stamped immediately under `corpus-core-version`: `game-version` (freeform string -- semver, patch name, build number, all acceptable; whatever the game actually ships), `game-version-platform` (required even for games that ship on a single platform today, since post-launch platform expansions are common), and `game-version-as-of` (`YYYY-MM-DD`, the date the corpus was last reconciled against that game-version+platform pair).
- `setup_wizard.md` -- Step 1 expanded with three new questions captured immediately after `[GAME_FOLDER]`: `[GAME_PLATFORM]`, `[GAME_VERSION]`, and `[GAME_VERSION_AS_OF]` (the last is auto-set to today's date, not asked). Wizard variable table, batching policy, fallback-list template, and Step 9 summary all updated to include the new vars. Step 7's manifest-section description now writes the four new manifest lines into `nav/architecture.md` alongside the existing `corpus-core-version` and `vector-extensions` declarations. `setup_answers.txt` template gains matching `game_platform` and `game_version` keys (no `game_version_as_of` -- always today).
- `docs/corpus-format.md` -- §3 Versioning subsection gains a v3 entry documenting the three new manifest fields, the build-time-snapshot semantics (the reader surfaces and may ask the player to reconfirm, but never updates the manifest -- corpus rev-bumps remain builder-side), and the `MIN_SUPPORTED_CORE: 1` posture that lets v1 and v2 corpora read without warning.

**Reasoning.**

- **Why required, not optional.** Player can defer game updates; DLCs add content without bumping base version; corpus refreshes can happen without a game patch; games can patch without a corpus refresh. Without an explicit build-time anchor, drift cannot be detected. The corpus needs an honest snapshot of what it was authored against.
- **Why platform is required for every corpus.** Single-platform-today games frequently expand to other platforms post-launch (PS5 exclusives gaining PC ports, Switch games getting Switch 2 enhanced editions, etc.). A corpus built without a platform stamp is permanently ambiguous; a corpus that stamps platform from day one stays honest as the game's distribution shape evolves.
- **Why freeform version, not normalized.** Real-world game versions show up as semver, patch names, build numbers, console-vs-PC splits, and DLC-named eras within the same week. Forcing normalization would lie about what the game actually ships. Freeform string + the player's actual input is the honest move.
- **Why a snapshot, not a live document.** The reader is a runtime; the corpus is an artifact. Letting the reader rewrite the manifest would conflate authorship and consumption, and would make the manifest's drift-detection purpose self-defeating (the thing that's supposed to detect drift would silently absorb it). Reader-side reconfirmation prompts the player; the player or maintainer decides whether to re-run setup or hand-edit.

**Migration.** Existing corpora at `corpus-core-version: 1` or `2` continue to work with v3-capable readers (the reader treats missing game-version-* fields as "version unknown, no surface" rather than as an error; no warning fires because v1 and v2 stay inside the supported range). Maintainers updating a corpus to v3 must: bump the `corpus-core-version` stamp in `nav/architecture.md`'s manifest block to `3`, and add the three game-version-* fields. The version, platform, and as-of date should reflect the build the corpus was last meaningfully reconciled against -- not "today" blindly. For corpora where the original build version is no longer recoverable, use `unknown` for `game-version` and pick the best-guess platform; `game-version-as-of` should be the date of the actual reconciliation, not the date you set the stamp.

### `corpus-core-version: 1 → 2` -- blocked-source recovery + required `capture-method` field (2026-05-20)

**Builder changes.**

- `ingestion.md` -- new "Blocked-source recovery" section between Pre-flight and Procedure. Defines the Fandom ladder (`Special:Export` → BreezeWiki → `archive.ph` → manual paste) and the one-sentence Reddit policy (manual paste default, `archive.ph` fallback). Step 5's inline metadata template gains a `capture: <method>` field and a per-field note explaining the default (`web_fetch` for cascade-sourced claims) and override conditions.
- `templates/claim_format.md` -- `capture-method` added as a required field with value vocabulary `web_fetch | special_export | breezewiki | archive_ph | manual_paste`. Inline and block format examples updated. `source` field now explicitly requires citing the canonical URL even when capture went through a mirror or archive. Evolution section records v2 as canonical.
- `templates/architecture.md` -- `corpus-core-version` stamp bumped from `1` to `2`. New corpora produced by the wizard will carry the v2 stamp from creation.
- `docs/corpus-format.md` -- §3 gains a "Versioning" subsection with the version history (v1, v2 with what changed). §4 (Claim format) adds the `capture-method` required-field entry.

**Migration.** Existing corpora at `corpus-core-version: 1` continue to work with v2-capable readers (the reader silently skips `capture-method` lookups on v1 corpora; no warning fires because v1 is inside the supported range). Maintainers updating a corpus to v2 must: bump the `corpus-core-version` stamp in `nav/architecture.md`'s manifest block, and backfill `capture-method` on every existing claim (default `web_fetch` for any claim that originated from a research-cascade pass and did not need a recovery-ladder rung).

### Conventions for this file

Two classes of entry belong here. Doctor reads this file to detect what existing corpora need.

**1. Format bumps** (`corpus-core-version` changes). Full entry: `### corpus-core-version: N -> M` heading + **Builder changes** (files touched, fields added/removed) + **Reasoning** (why the bump) + **Migration** (what existing corpora must do). These guide doctor Branch A.

**2. Template and procedure changes that affect existing corpora.** Lighter entry: `### <short title> (<framework vN>, YYYY-MM-DD)` heading + **Builder changes** (files touched) + **Existing corpus impact** (what existing corpora need to update, or "None -- forward-only" if only new corpora pick it up). These guide doctor's template-sync scan. Examples: new columns/sections in `templates/dependencies.md`, retired CHECKPOINT fields, procedure changes that alter how existing edges or content should be audited.

**What does NOT need an entry:** persona iteration, prose edits, wizard copy changes, new framework files that don't affect existing corpora (e.g. `compaction_policy.md`), internal procedure refinements that don't change corpus artifacts. The `corpus-core-version` in [`docs/corpus-format.md`](docs/corpus-format.md) §3 only bumps for format-breaking changes; this file is broader than that -- it tracks anything an existing corpus maintainer needs to act on.

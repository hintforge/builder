# Doctor -- Corpus Health, Updates, and Targeted Repair

This procedure runs on an existing, instantiated guide when something is wrong, stale, or incomplete and the user wants the guide patched up without rerunning full setup. Triggered by the user typing **"doctor hintforge"** (primary), or aliases **"doctor my guide"** / **"doctor the corpus"**, optionally with a hint about why (e.g. "doctor hintforge, the reader is complaining about a version mismatch" or "doctor hintforge, new DLC dropped").

> **Trigger-phrase note.** Avoid the bare "run the doctor" -- Claude Code's built-in `/doctor` CLI health-check command collides with that phrasing and the agent will route to the wrong place. The "doctor hintforge" verb-plus-skill-name form is the unambiguous primary; the reader skill's mismatch-warning text uses it.

> **Why this is its own file.** Setup, ingestion, and stitch-and-zipper each assume a clean entry point: setup assumes nothing exists, ingestion assumes a fresh research result, stitch-and-zipper assumes a finished P1-P3 pass. None of them handle "the guide has populated state and something is wrong, stale, or incomplete." Doctor is the catch-all for that case -- before, during, or after the research cascade. Most doctor runs happen post-instantiation (a finished guide drifting against a new framework version or game patch), but mid-cascade use is supported: a format bump landing between P1 and P2, or a structural repair (e.g. scaffolding an entity-class folder for fragmented companion content) before the next phase compounds the debt.

> **What this file is not.** Not a setup rerun, not a full ingestion, not stitch-and-zipper. Doctor dispatches to those when warranted but never replays them blindly.

> **Compaction expectation:** UNEXPECTED by default -- most doctor branches are targeted (a specific stale file, a single format-bump field, a known drift). A compacting doctor run means the branch is too broad for the scope label. EXPECTED only for Branch C full-corpus migrations (e.g. v4 → v5 entity-overlay migration), which legitimately need ingestion-class handling. See [`compaction_policy.md`](compaction_policy.md).

## Pre-flight

- The session is **fresh** and opened **inside the game folder** (`Guides/<game>/`), not at workspace root or inside the framework folder. Framework files this procedure reads (`docs/corpus-format.md`, `CHANGELOG.md`, templates) come from the running skill, not a path relative to the guide.
- The guide has already been instantiated (`architecture.md` exists, `CHECKPOINT.md` exists, at least one content subfolder has been populated). If those aren't present, redirect the user to `setup_wizard.md` or `ingestion.md` and stop.
- Run on a mid-tier model with extended thinking off. This is structural work, not reasoning-chain work.

## Procedure

### Manifest check

Read the corpus manifest before triage -- it tells you what game state the corpus was last reconciled against.

Read `nav/architecture.md` -> `## Hintforge manifest`. Extract `game-version`, `game-version-platform`, and `game-version-as-of`.

**Fire the manifest-and-triage question (mandatory, structured).** Surface the manifest fields, then ask via a structured `AskUserQuestion` call with `multiSelect: true` -- never an inline prose question. An inline question gets self-answered under task momentum; a structured call physically separates "question fired" from "answer received." Question text: "Corpus manifest: game-version `<value>` on `<platform>`, as of `<date>`. Has anything changed in the game since then, and what prompted this doctor run?" Options (plain language, one idea each):

1. **Nothing has changed in the game** -> Route 2 below, then continue to any other selected branch.
2. **A patch, DLC, or game update shipped** -> Branch B.
3. **Something in the guide is wrong or missing** -> Branch C.
4. **The reader showed a version warning** -> Branch A.

This one call doubles as §1 Triage for bare invocations. Multiple selections are legal and run in A -> B -> C order per §1. Selections 1 and 2 contradict each other; if both arrive, re-ask.

Two routes for the date field:

1. **"A patch, DLC, or game update shipped" selected.** Do not touch `game-version-as-of` here; Branch B owns the manifest update (its step 3).
2. **"Nothing has changed in the game" selected.** Accept and bump: update `game-version-as-of` to today in `nav/architecture.md`. No other content edits. Log one line in CHECKPOINT's harness changelog: "manifest date bumped <today>, maintainer confirmed no game change since <prior date>".

**The bump is downstream of the fired question -- no exceptions.** `game-version-as-of` may be edited, and the "maintainer confirmed" changelog line written, ONLY after the `AskUserQuestion` call above actually fired and the maintainer selected "Nothing has changed in the game." "Nothing in front of me indicates a change" is an inference, not a maintainer answer -- self-answering this gate is the exact defect this rule exists to block. The field means "the game build this corpus was authored against," not "last touched"; moving it without a human answer silently reconciles a possibly-stale corpus to "current." If the question cannot fire or goes unanswered, leave the date untouched and surface the manifest state in the recap instead.

If `game-version-as-of` is missing or unparseable, say so and route to Branch A before triage.

**Sweep bypass.** If the trigger phrase is `hintforge doctor, reddit sweep`, skip this step and proceed to §1 below, where the sweep trigger routes directly to [`reddit_sweep.md`](reddit_sweep.md).

**Directed-invocation bypass.** If the trigger phrase already names the work (a specific repair, a format bump, generating a research brief, any cascade-continuation task), skip the question and route directly to the named branch -- and leave `game-version-as-of` untouched. A directed run has no authority over the manifest date: only Route 2's human "nothing changed" answer or Branch B's step 3 may move that field. "The maintainer named the work" licenses skipping triage, not self-answering the manifest gate.

### 1. Triage -- pick the branch

For bare invocations, the Manifest check's structured question has already collected the answer -- the maintainer's selections pick the branch(es). For directed invocations, infer the branch from the trigger phrase. Do not start any branch's work until the branch is confirmed by one of those two signals.

| Branch | Trigger | Scope |
| --- | --- | --- |
| **A. Format bump** | Reader warned about `corpus-core-version` mismatch; or the user updated the framework and wants the corpus brought current | Migrate corpus to a newer `corpus-core-version`. Mechanical. |
| **B. Game update** | A patch, DLC, or major content drop has shipped since the guide was built | Extend or refresh corpus to cover new game content. May require a research handoff. |
| **C. Targeted repair** | The user (or playtest) found a gap, misclassification, or wrong fact in the existing corpus | Patch a specific area. May require a small targeted research brief. |

If the maintainer's answer doesn't resolve to a branch, ask three diagnostic questions: (1) Did the reader show a version warning? (2) Has the game itself been updated since the guide was built? (3) Did you hit something wrong or missing during play? First "yes" wins; multiple "yes" answers run branches sequentially in A -> B -> C order. (These are the same three ideas as the Manifest check's options 4/2/3 -- the structured question usually settles this before §1 is reached.)

**Reddit sweep is a recognized doctor invocation.** When the trigger phrase includes "reddit sweep" (canonical: **`hintforge doctor, reddit sweep`**, optionally `... for the <patch/DLC/gap>`), route directly to [`reddit_sweep.md`](reddit_sweep.md) and run the sweep as this session's dedicated task -- do not wrap a triage of branches A/B/C around it. The `hintforge doctor` anchor is simply what loads the skill; the `reddit sweep` qualifier is the work. The sweep procedure detects its own phase window (post-final-research/pre-stitch initial harvest, or post-cascade top-up) per `reddit_sweep.md` §Trigger conditions. If a Branch B game-update / DLC pass needs to scaffold architecture before the sweep can route findings to home files, that scaffolding is its own prior `hintforge doctor` session; the sweep is the subsequent `hintforge doctor, reddit sweep` session (the architectural-extension-before-sweep ordering in Branch B step 2 still holds -- across two sessions, not one).

### 2. Baseline fetch (branch-conditional)

| Branch | Fetch target |
| --- | --- |
| **A** | None online. Read `CHANGELOG.md` and `docs/corpus-format.md` (from the running skill) to identify what changed between the corpus's current `corpus-core-version` and the framework's target. |
| **B** | Web fetch: patch notes, DLC announcement page, dev blog, or wiki version-history section. Establish what changed in the game world. Single source minimum, two preferred. |
| **C** | Web fetch only if the gap is factual and existing corpus sources don't cover it. For misclassification or structural issues, no fetch needed -- the gap is in our handling, not in the world. **For achievement gaps:** use the source ladder in [`setup_wizard.md`](setup_wizard.md) Step 6.7 sub-step 4 (WebSearch first, not URL crawling). |

Show the user what was fetched and a one-line summary of the change before continuing.

### 3. Branch A -- Format bump

1. Read the corpus's current `corpus-core-version` from `nav/architecture.md`'s `## Hintforge manifest` block.
2. Read the framework's target `corpus-core-version` from `docs/corpus-format.md` §3 (Versioning).
3. For each intermediate version step between them, apply the migration the `CHANGELOG.md` entry describes for that step. Migrations are additive; earlier-version corpora remain valid under the reader's `MIN_SUPPORTED_CORE` / `MAX_SUPPORTED_CORE` bounds, so the goal is "bring format current," not "rescue an unreadable corpus."
4. Update `nav/architecture.md`'s `corpus-core-version` field. This is the only doctor branch that touches the manifest version.
5. Enumerate any newly-scaffolded files or fields and offer to queue branch C to fill them. Phrasing: "Branch A scaffolded these empty: X, Y, Z. Want to run branch C now to fill them?" Yes proceeds; no logs the deferred work in CHECKPOINT as pending.
6. Log the migration in `CHECKPOINT.md`'s `## Harness changelog` with from-version, to-version, and which files were touched.

Branch A does not invent content. If a bump introduced a new universal-core field or file, branch A scaffolds it empty per the changelog's migration instructions; filling it is branch C.

### 4. Branch B -- Game update

1. Classify the change from the fetched patch notes:
   - **New content** (new zones, quests, enemies, items, mechanics) -> generate a targeted brief at `<game>/research_briefs/doctor_<YYYY-MM-DD>.txt`, scoped only to the new content. Use the structure of an existing P-brief (research_briefs/p1.txt etc.) but bound the scope to the patch's diff, not the full game. The user runs the brief through their deep-research tool. Result lands in `<game>/research_inbox/doctor/` (create the subfolder if absent). The user then types "ingest the research" and `ingestion.md`'s normal procedure handles it. Doctor does not extend ingestion; ingestion already knows what to do once a result file is in the inbox.
   - **Balance / stat changes** (existing entities, new values) -> edit relevant corpus files directly with updated `_source:` lines. No research run needed.
   - **Removed content** (devs cut a feature) -> strike corresponding corpus entries. No tombstones in the corpus (the persona reads only the corpus, not CHECKPOINT). Note removals in CHECKPOINT's harness changelog.
   - **Community-knowledge-shaped content** (interaction patterns, "is this a bug" categories, build implications, undocumented changes the patch notes do not name) -> the [`reddit_sweep.md`](reddit_sweep.md) sweep covers this, but doctor does NOT run it in this session. Recommend the user run **`hintforge doctor, reddit sweep for the <patch/DLC>`** in a fresh session (the sweep runs in its own session per `reddit_sweep.md` -- isolates the reddit-MCP failure surface and keeps context scoped). Supplemental to the deep-research brief above, not a substitute -- community sweeps surface findings the brief systematically misses (community-knowledge shape); briefs surface findings the sweep misses (structural coverage). Surface brief / sweep / both as options; the sweep is always a separate subsequent session, never chained from this doctor run.
2. If the update is a DLC large enough to warrant architectural footprint (new zone graph edges, new chapter, new locks-and-keys entries), extend `nav/architecture.md` in place and tag DLC content with the `dlc:<name>` spoiler vector so reader filtering works correctly. **If a Reddit sweep will cover the DLC** (per the community-knowledge-shaped path above), it runs as a separate `hintforge doctor, reddit sweep` session AFTER this architectural extension lands (and after any targeted brief is ingested) -- so finding ingestion has the new zones / edges / chapter scaffolding to route claims to. A sweep run before the architectural extension would surface findings that have no home file to land in. Recommend the sweep to the user at the end of this branch; do not run it in this session.
3. Update `nav/architecture.md`'s game-version manifest fields (`game-version`, `game-version-platform`, `game-version-as-of`, plus the DLC list if the manifest tracks one) to reflect the new state.
4. Log in `CHECKPOINT.md`'s harness changelog with a one-line description, files touched, and any pending follow-ups (e.g. "ingestion run pending for `doctor_<date>.txt`").

### 5. Branch C -- Targeted repair

1. Characterize the gap with the user: symptom, file, fact. Read the affected files before proposing anything.
2. Pick depth of fix:
   - **Wrong fact / single claim** -> edit in place with corrected `_source:` line.
   - **Missing facts, scope <= one file** -> web fetch if needed, write corrections, run the spoiler-classification sub-agent from [`ingestion.md`](ingestion.md) step 3 over the new facts.
   - **Missing facts, scope > one file or genuinely under-researched area** -> generate a targeted brief at `<game>/research_briefs/doctor_<YYYY-MM-DD>.txt` (same mechanism as branch B), hand off to deep research, user ingests via normal ingestion.
   - **Community-knowledge-shaped gap** (build math, weapon / item interaction patterns, "is this a bug" categories, undocumented mechanics the deep-research cascade missed) -> the [`reddit_sweep.md`](reddit_sweep.md) sweep covers this, but doctor does NOT run it in this session. Recommend the user run **`hintforge doctor, reddit sweep for the <gap>`** in a fresh session (the gap being the specific mechanic, build, or interaction; the sweep runs in its own session per `reddit_sweep.md`). The sweep produces a findings file in `research_inbox/module/`; the user ingests it per ingestion.md's step 4b "Ingesting a reddit_sweep artifact." If the gap is also factually under-researched at the deep-research level (not just community-shaped), pair the sweep with a targeted brief -- sweep covers community knowledge, brief covers structural / wiki / dev-doc coverage. If the `reddit-mcp-buddy` MCP is unreachable, fall back to the targeted-brief path alone.
   - **Misclassification** (right facts, wrong vector tags or wrong spoiler tier) -> run the spoiler-classification sub-agent on the affected facts, move content per `ingestion.md` step 4's vector table.
3. Reconcile downstream per `ingestion.md` step 7: grep destination subfolders (`sections/`, `items/`, `nav/`, `puzzles/`, `optional_zones/`, `controls.md`, `settings.md`, plus entity-class folders that exist -- `npcs/`, `factions/`, `crew/`, `reputation/` at `corpus-core-version: 5` and later) for orphans, fix them. No "DROPPED -- see CHECKPOINT" stubs in the corpus.
4. Log each repair in `CHECKPOINT.md`.

**Branch C never touches the `## Hintforge manifest` fields.** `game-version`, `game-version-platform`, and `game-version-as-of` are not repair targets: the date moves only via the Manifest check's Route 2 (human-confirmed "nothing changed") or Branch B step 3 (game update), and `corpus-core-version` only via Branch A. A repair fixes content; it does not re-stamp what game state the corpus was reconciled against.

### 6. Phase state updates + cascade re-runs

Doctor has authority to read and set any `## Phase state` flag in CHECKPOINT when its findings warrant re-running a cascade process. This includes `stitch_stale`, `stitch_scope`, `zipper`, `stitch`, and the `p[N]_ingestion` completion flags -- any flag whose current value no longer reflects corpus reality after the doctor run.

**When to update flags:**

| Doctor finding | Phase state action |
| --- | --- |
| Template structure changed (new columns, new sections, renamed fields in `dependencies.md` or other template-derived files) | `stitch_stale: true` |
| Content moved across files (branch A migration, branch C repair) | `stitch_stale: true`; note zipper may also be warranted |
| New architecture edges or zones added (branch B) | `stitch_stale: true` |
| Framework procedure changes affect how existing edges/content should be audited | `stitch_stale: true`; `stitch_scope: full` |
| Prior ingestion results invalidated (branch B game update contradicts existing content, branch C reveals systematic research error) | Reset relevant `p[N]_ingestion` to `pending (reason)` |

**Audit inherited state (mandatory).** Before declaring step 6 complete, scan the last 5 `## Harness changelog` entries in CHECKPOINT against the rules table above. For each prior entry whose finding *would* warrant a Phase state flag under current rules but doesn't have one set, backfill the flag and add a one-line changelog entry: `vN+1 -- backfill: <flag> set per <rule> (inherited from vX recommendation)`. This is mechanical, not judgment-based -- if the prior finding matches a current rule and the flag is missing, set it. **Why this step exists:** procedure changes that retire a workflow (e.g., "changelog entry sufficient" → "Phase state flag required") would otherwise apply only to new doctor findings; inherited recommendations made under the old procedure stay misclassified. Without this backfill pass, every rule change creates a one-session gap on the first invocation post-change.

**Run vs flag.** If the re-run is small and scoped (touched files only, <5 files), run it in this session per [`stitch_and_zipper.md`](stitch_and_zipper.md). If the re-run would be a full re-audit or the session is already long, set the flags and defer. **A CHECKPOINT changelog entry alone is not sufficient** -- flags in Phase state are what future sessions scan; changelog entries are archaeology.

Skip this step entirely (no flags, no re-run) only if doctor edited values inside existing entries without changing file structure, template shape, or cross-file relationships.

### 7. Update CHECKPOINT and surface a recap

- Add a dated `## Harness changelog` entry per branch that ran: branch letter, one-line description, files touched, pending follow-ups (e.g. "ingestion run pending for `doctor_<date>.txt`", "branch C deferred -- scaffolded fields not yet filled"). Don't merge branches into a single ambiguous entry.
- One-screen recap to the user: which branches ran, what changed, what research handoffs need to happen, any reconciliation actions taken.

## Discipline rules

- **Doctor is incremental, not a regen.** Edits the corpus in place. The regeneration path (instantiation wipe + research-cascade replay) is a separate procedure for corpora too broken to repair.
- **Live-observed wins on conflicts.** If a doctor fetch contradicts a `status: live-observed` claim in the corpus, the live-observed claim wins by default. Doctor flags the conflict in CHECKPOINT and asks the user before overwriting. Same rule as ingestion.
- **Spoiler discipline is non-negotiable.** Any new content doctor introduces routes through the spoiler-classification sub-agent in `ingestion.md` step 3. Doctor does not classify facts itself; it delegates.
- **Branch order is fixed: A -> B -> C.** Format first so later writes use the current format. Content updates before targeted repair because new content may render the repair unnecessary, or may be where the gap will be filled anyway.
- **One doctor run, one branch primary, but multiple branches allowed.** Each branch gets its own CHECKPOINT entry.
- **Mid-cascade doctor runs are legal.** The pre-flight gates on populated state (architecture.md + at least one content subfolder), not on cascade completion. Branches A and C are common between phases (format bumps, structural repairs that would compound if deferred). Branch B is rare mid-cascade (the game shipping a patch during a multi-day build) but not forbidden. The same discipline rules apply -- doctor still delegates classification to `ingestion.md` step 3 and cross-refs to `stitch_and_zipper.md`, whether or not the cascade has finished.

## Regeneration safety

Same rule as ingestion. `CHECKPOINT.md`, loadouts, user-flagged live-observed truths, and infrastructure (`.claude/`, PTT/TTS, save-watcher, persona customization) survive any doctor run. Doctor never touches those files.

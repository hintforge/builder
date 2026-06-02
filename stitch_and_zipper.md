# Stitch and Zipper -- Post-Ingestion Synthesis Pass
<!-- hintforge · post-ingestion synthesis · two phases: zipper (reconciliation) then stitch (edge synthesis) -->

This procedure runs in a **fresh session inside the game folder** after at least P1 ingestion is complete. Triggered by the user typing "run stitch", "run zipper", or "run stitch and zipper."

> 🧠 **Run on a mid-tier model (Sonnet-class) with extended thinking OFF.** Same cost discipline as ingestion. Each phase targets $0.50-1.00; both together under $2.

> **Compaction expectation:** EXPECTED for stitch on large corpora (100+ files); UNEXPECTED for zipper (zipper is short by design -- compacting zipper means scope is wrong). See [`compaction_policy.md`](compaction_policy.md). Stitch's count-from-disk summary rule (Stitch session sub-step 5) is one of this procedure's compaction handlers; the per-edge convergence audit in Phase B is the other (it catches sources-cited-but-contradicting bugs that survive post-compact recomposition).

## Two separate passes, two separate triggers

Stitch and zipper are triggered independently. Running them together is the default recommendation, but either can run alone:

- `"run stitch"` -- edge synthesis only
- `"run zipper"` -- redundancy reconciliation only
- `"run stitch and zipper"` -- both, **zipper first then stitch**

**Why separate.** Cost isolation: a stitch run on a large corpus may use most of a session budget. Zipper on a clean corpus may cost almost nothing. Keeping them independent lets the user break up cost and re-run either without paying for both.

**Ordering when run together: zipper first, then stitch.** Zipper's role-split and merge resolutions clean up structural redundancy before stitch counts source files. If stitch runs first, a duplicated file reads as two independent sources and inflates confidence artificially. Zipper deduplicates first so stitch's source-count is a real signal.

---

## Phase A -- Zipper (reconciliation)

### What it does

Surveys the corpus for content written redundantly along different axes -- two files with substantially overlapping data organized differently. Operates on file structure, headings, metadata lines, and vector tags. Does not read substantive claim content to characterize overlap; uses each file's section headings and `_source:` metadata to determine what dimension it covers.

Focus targets:
- Two index files covering the same content category (e.g., a `paths/index.md` and `endings/index.md` documenting the same per-ending data along different axes)
- Per-zone NPC lists that duplicate `npcs/`-folder per-entity files (at `corpus-core-version: 5` and later; the legacy `enemies/`-folder catalog this rule originally targeted was retired at v5 in favor of the entity-overlay-built `npcs/` aggregation)
- Per-section item drops that duplicate `items/`-folder entries
- Any two files where heading structure and vector tags substantially overlap

### Spoiler discipline

Zipper reads headings, metadata lines, and vector tags only. When characterizing a file's contents in a proposal, it uses the file's own headings and vector tags -- not the content beneath them. If a heading is itself spoiler-tagged (e.g., a boss name as an H2 with `spoiler: late-game`), zipper redacts it in the proposal using the same tier-gating the persona uses at read-time: `[late-game content -- heading redacted at current tier]`. Read the user's current tier setting from CHECKPOINT before surfacing anything.

### Output: autonomous resolution

Zipper decides and executes the best resolution for each overlap. For each overlap found, zipper:

1. Evaluates the overlap using heading structure, vector tags, and content population state (scaffold-only vs populated).
2. Picks the resolution class:
   - **Merge** when one file is scaffold-only or strictly a subset of the other. Consolidate into the populated/primary file, remove the redundant file, update cross-refs.
   - **Sharpen role split** when both files are populated but organized along genuinely different axes (e.g., per-chapter vs per-system). Each file keeps its axis; shared content moves to the primary owner; cross-refs added both ways.
   - **Accept as design** when the duplication is intentional and serves different reader entry points. Add a note to each file explaining the design choice so future passes do not re-flag it.
3. Executes the resolution (file edits, deletions, cross-ref updates).
4. Reports what it did in a one-line summary per overlap:

```
Resolved: [file-path-A] ↔ [file-path-B] -- [merge into A / role-split / accepted as design]. [one-sentence rationale].
```

No interactive prompts. If the user disagrees with a resolution after the fact, they say so and zipper reverts or re-resolves.

### Zipper facilitates stitch

After role-split or merge resolutions, each fact has one canonical home. Stitch's source-count for high-confidence edges then reflects genuinely independent documentation, not echoes of the same data in two files.

---

## Phase B -- Stitch (edge synthesis)

### What it does

Reads the corpus and writes additive cross-reference edges between separately-documented systems. Does not rewrite existing claims, does not invent facts, does not pull from external sources. If an edge requires content the corpus does not have, that is a P3 gap, not a stitch finding.

Focus categories:
- PoNR / lockout / missable / sequencing dependencies (action in System A affects state in System B)
- Recurrence of the same NPC or resource across topic files
- Mechanic-stack interactions (item interacts with status interacts with enemy class)

### Corpus size check (mandatory first step)

Before reading any file content, stitch scans the file list and reports:

```
Corpus inventory: [N] files, approximately [X] KB total.
```

**How to gather the numbers.** Use a single-line shell command -- multi-line PowerShell blocks fail the harness pre-parser ("command line is too long" / "malformed syntax"). Newlines are only safe inside quoted strings or here-strings, not between statements. Portable recipes:

- **PowerShell (one line, semicolons):**
  `$f = Get-ChildItem <corpus-path> -Recurse -Filter *.md | Where-Object { $_.FullName -notmatch '_processed|research_inbox|research_briefs|\.claude' }; "Files: $($f.Count), KB: $([math]::Round(($f | Measure-Object Length -Sum).Sum/1KB,1))"`
- **Bash/git-bash:** `find <corpus-path> -name '*.md' -not -path '*_processed*' -not -path '*research_inbox*' -not -path '*research_briefs*' -not -path '*.claude*' -printf '%s\n' | awk '{s+=$1; n++} END {printf "Files: %d, KB: %.1f\n", n, s/1024}'`

If multi-statement logic is genuinely needed, write a `.ps1` file and invoke it -- don't try to inline newlines.

If total corpus size exceeds 150 KB, stitch notes the size in the inventory line and proceeds with a full pass by default. If context-limit compaction occurs mid-pass, stitch resumes per `compaction_policy.md` -- the scoped-pass fallback exists but is not the default recommendation. CHECKPOINT carries a `stitch_scope:` field so a scoped pass can be resumed without re-reading already-processed directories. Only recommend scoping if the user explicitly asks or a prior full-pass attempt compacted and lost edge state.

### Write threshold

Stitch writes only edges where the corpus already documents the dependency clearly enough that no judgment call from the user is needed. The criterion is **corpus convergence:** 2+ files in 2+ different topic directories independently describe both endpoints. Neither file needs to name the dependency explicitly -- convergence is enough.

Example: a mechanics file documents that overloading a relay system disrupts nearby electrical systems. A separate navigation file documents that a generator sequence requires uninterrupted electrical state. Two files, different directories, overlapping state-space -- write the edge.

### Per-edge convergence audit (mandatory)

Convergence on topic is not the same as convergence on value. Two files may both mention "Solomorne's recruitment zone" and one says zone X while the other says zone Y -- the topic converges, the value does not. Stitch must check the values, not just the topics. This makes stitch the cascade's audit pass: not just an edge writer, but the procedure that surfaces intra-corpus inconsistencies that ingestion can't see.

For each edge -- both new candidates and existing edges already in `dependencies.md`:

1. **Identify the specific factual claim the edge text makes** -- a zone name, a chapter, an item, a sequence, a PoNR trigger -- the actionable content of the edge, not the topic.
2. **For each source file cited:** open it (or re-open if already read) and locate the passage that supports the specific claim. The passage must state the same value the edge claims, not just mention the same topic.
3. **If a cited source contradicts the edge text** (e.g., source says "zone X" but edge says "zone Y"), this is a **corpus inconsistency**, not an edge failure. Do NOT silently use the value the model believes is correct. Surface the contradiction explicitly:
   - Add a row to `dependencies.md` under the `## Corpus inconsistencies` section: "File A says X; File B says Y; suspected authoritative source: [the entity file if one exists, else leave blank for user to resolve]."
   - For new edges: skip writing the edge until the inconsistency is resolved.
   - For existing edges: leave the edge row in place but add the inconsistency row. The edge text may be correct even when a cited source is wrong -- the inconsistency flags the source for repair, not the edge for removal.
4. **If all cited sources agree on the specific value, write the edge (new) or confirm it (existing).**

**Re-run scope: always full.** Every stitch run re-audits all existing edges in `dependencies.md`, not just new candidates. A game patch, DLC, or new ingestion phase can change facts that existing edges cite -- the only way to catch that is to re-verify everything. "Existing edge" does not mean "verified edge." Treating already-written edges as done defeats the audit.

**Audit surfaces, does not resolve -- during the walk.** When the re-audit finds a contradiction between an edge and its cited sources, the audit adds the inconsistency row to `## Corpus inconsistencies` and moves on to the next edge -- it does not edit the source file, does not rewrite the edge text, does not chain into resolution work mid-walk. Resolution happens after the completion gate confirms the audit is exhaustive (see Stitch session sub-step 5b). **Why:** mixing audit and resolution mid-walk is what caused the pass 3 selective-audit failure -- finding the first inconsistency pulled the model into resolution work, and the systematic walk over the remaining edges silently stopped. Surface-only during the walk keeps the audit cheap, fast, and complete. The completion gate then catches any gaps before resolution begins.

The build is not done until stitch has either written all eligible edges or surfaced every detected inconsistency for resolution. A stitch run that writes edges citing self-contradicting sources is laundering bad data into authoritative-looking output -- the inverse of an audit. The `## Phase state` `stitch: complete YYYY-MM-DD` field carries the implicit claim that this audit ran.

**Everything else is skipped silently.** Single-source mentions; two mentions within the same directory; dependencies inferable only from a shared named entity (same NPC, same currency); proximity-only co-occurrence -- none of these are surfaced to the user as proposals. The prior "medium confidence -- ask the user" flow produced rubber-stamp confirmations that did not actually screen for edge quality, and surfacing the proposal text leaks gameplay spoilers in chat (see Chat output discipline below). If a borderline case becomes important later, a future stitch pass over a richer corpus will pick it up at the write threshold.

Skipped edges are not logged in `dependencies.md` or in chat. The harness changelog in CHECKPOINT may carry a one-line aggregate ("N borderline candidates skipped -- single-source") if the contributor would benefit from knowing the corpus is close but not converged. Never enumerate skipped edges individually; that re-introduces the spoiler-leak the threshold was raised to prevent.

### Output: `dependencies.md` + inline cross-refs

Stitch writes two things per high-confidence or user-confirmed edge:

1. A row in `dependencies.md` at game-folder root (created on first stitch run from [`templates/dependencies.md`](templates/dependencies.md) if absent).
2. An inline cross-ref appended to the relevant section in each endpoint file:

```
> **Cross-system dependency** -- see `dependencies.md` DEP-[NNN]: [one-sentence summary of the dependency].
```

### Chat output discipline

Stitch is a builder operation, but the builder is often also a future player who has not seen the rest of the corpus yet. Edge descriptions are full strategy spoilers (boss kill orders, achievement requirements, ability counters, missable lockouts). Stitch must not surface them in chat.

**Allowed in chat:**
- Corpus inventory line (file count + approximate KB) before reading begins.
- Procedural blockers that genuinely require user input (e.g., scope decision when corpus > 150 KB).
- A bare completion line: `Stitch complete. N edges written: DEP-[A] through DEP-[B]. See dependencies.md.` IDs only -- no titles, no rationales, no tables of contents.

**Prohibited in chat:**
- Edge titles, summary descriptions, or content of any kind. No "DEP-018: Kill Natasha first to clear Owl spawns" style line -- that's a strategy spoiler shoved at someone who may be mid-playthrough.
- Tables, lists, or per-edge before/after diffs that include any portion of the edge body.
- Re-reading the rationale for a written edge into chat at the end of the run.

All edge content lives in `dependencies.md` and in the harness changelog inside CHECKPOINT -- both files the contributor can open deliberately. The chat surface is for procedural status only.

### When the persona references `dependencies.md`

The persona does not scan `dependencies.md` on every response. Triggers:

- **Explicit cross-system query.** Player asks something naming or implying two systems ("does X affect Y", "will doing A break B", "can I still get [item] if I already [action]"). Persona checks dependencies before answering from corpus or web.
- **Zone entry with pending gates.** When orienting to a new zone at session start via `player_position` in CHECKPOINT, persona checks the `## PoNR / lockout edges` table for any edge where that zone is an endpoint and a precondition is unmet.
- **Lookahead proximity.** When `last_known_gate` is within `lookahead_n` steps of a PoNR edge endpoint, persona surfaces the warning at the appropriate tier.
- **On-request.** "What should I know before I do X?" -- explicit permission to surface all relevant dependency edges without the player having named them.

---

## CHECKPOINT -- Phase state and readiness

### Phase-readiness check

Any natural-language query that implies "what should I do next" or names a phase triggers a readiness check. The model reads `## Phase state` from CHECKPOINT and responds with: what is complete, what is next and whether its preconditions are met, and if preconditions are not met, what is blocking and what the user can do (run the missing phase, or explicitly skip it with a reason recorded in the `skipped (reason)` field).

Preconditions:
- P2 requires P1 ingested or explicit skip-acknowledge.
- P3 requires P2 ingested or skip-acknowledge.
- Stitch requires at least P1 ingested.
- Zipper has no hard precondition but is most useful post-P1.

This handles re-entry cleanly. A player who skipped P2 and wants to run it later says "I want to go back and do P2 ingestion" -- the check reads CHECKPOINT, confirms P1 is complete, and starts the P2 ingestion session. A player returning after a break says "what's next" and gets a one-line status read.

### `stitch_stale` flag

Set to `true` automatically when any corpus file receives a new `live-observed` claim after the `stitch:` date. The persona reads this flag at session start and surfaces a one-time notice:

> Heads up -- the corpus has had new live-observed facts added since the last stitch run. Cross-system hints may be incomplete. Say "run stitch" to update, or ignore this if the additions were minor.

The flag resets to `false` when stitch completes.

---

## Session shapes

### Zipper session

1. User opens a fresh session inside the game folder and says "run zipper" (or "run stitch and zipper").
2. Model reads CHECKPOINT: confirms at least P1 is ingested. Reads `## Phase state`. Reads user's current tier for spoiler discipline.
3. Model scans file list (headings, metadata, vector tags only -- no content reads yet). Reports files surveyed.
4. For each overlap detected: picks the best resolution, executes it, reports one line per overlap (see Autonomous resolution above).
5. Updates `## Phase state` in CHECKPOINT: `zipper: complete YYYY-MM-DD`. Adds `## Harness changelog` entry listing overlaps found and resolutions applied.

### Stitch session

1. User opens a fresh session inside the game folder and says "run stitch" (or continues from zipper in the same session if running both and corpus is small enough).
2. Model reads CHECKPOINT: confirms zipper has run (or user has explicitly accepted running stitch on an un-zippered corpus). Reads `stitch_scope:` if set.
3. **Corpus size check (mandatory).** Scans file list, reports total count and approximate KB. Proceeds with full pass by default regardless of size.
3b. **Dependencies-file structural lint (mandatory).** Before reading corpus content, verify `dependencies.md` table integrity. For each `|`-delimited markdown table in the file, count cells in the header row and confirm every data row has the same cell count. Mismatched rows are usually edges written under the wrong table's schema (e.g., a 6-column cross-system edge appended into a 5-column missable/sequencing table). Surface mismatches in chat with file:line and the column-count delta; do not auto-fix during stitch -- flag for the user or a doctor branch C repair. **Why this step exists:** stitch's per-edge audit reads edge *content* but not table *structure*; a structurally misplaced row can survive multiple stitch passes silently. A one-shot column-count check at read-time catches this class of defect before it propagates into the audit.

   Implementation recipe (bash/git-bash, one line per table):
   ```
   awk -F'|' 'BEGIN{h=0} /^\|/{n=NF; if(h==0){h=n; next} if(n!=h) print FILENAME":"NR": "n" cells (header has "h")"}' dependencies.md
   ```
   PowerShell equivalent uses `Get-Content | ForEach-Object` with `Split('|').Count`. Run per `## ` section to scope each table; tables in different sections legitimately have different schemas.

4. Model reads corpus files per scope. Two sub-passes:
   - **Re-audit existing edges:** For each row already in `dependencies.md`, run the per-edge convergence audit (open cited sources, verify specific values). Surface contradictions to `## Corpus inconsistencies`.
   - **Find new edges:** For each new convergence meeting the **write threshold** (2+ files, 2+ topic directories): run the per-edge convergence audit, then write to `dependencies.md` and inline cross-refs, no chat surface. Edges that do not meet the threshold are skipped silently -- never proposed in chat.

     **Post-write contradiction check (mandatory for each new edge).** After writing the edge, extract the edge's specific claim values (the actionable nouns: zone IDs, item names, achievement names, mod names, NPC names, sequence triggers) and `grep -rn "<value>" <corpus>` for each one across the whole corpus, NOT just the cited sources. For every match in a file NOT listed in the edge's source column:
       - If the match supports the claim, add the file to the source column (an uncited supporting source strengthens the edge -- audit miss).
       - If the match contradicts the claim, treat as a corpus inconsistency: add a row to `## Corpus inconsistencies` per step 5b discipline and leave the edge in place pending resolution.
       - If the match is a different legitimate use of the same string (same NPC name appearing in a non-related context), note it inline in the audit trail and move on.
     **Why this step exists.** The per-edge audit confirms the edge agrees with its cited sources; it does NOT check whether the broader corpus disagrees. A high-confidence edge can ship with a contradiction lurking one file away. The grep is mechanical, cheap (one query per claim value), and catches the inverse defect class.
5. **Completion gate (mandatory).** Before writing the run-log row or CHECKPOINT entry, reconcile audits-done vs edges-in-dependencies:
   - Re-read `dependencies.md` and extract every edge ID (e.g. `grep -oE '^\| [A-Z][A-Z][A-Z]-[0-9]+' dependencies.md`).
   - Compare that list against the edges the re-audit sub-pass actually opened sources for. The model must be able to enumerate which edge IDs were audited; if any edge in dependencies.md is missing from the audit list, the audit is incomplete.
   - If mismatch: **return to the re-audit sub-pass** and audit the missing edges. Do not proceed to step 6 until the lists match.
   - Track this with explicit per-edge audit lines (internal thinking is fine; chat surface follows the discipline below) so the reconciliation is mechanical, not memory-based.

   Then derive counts from disk: **Counts in the recap, the run-log row, and the CHECKPOINT changelog entry must be derived from `dependencies.md` by re-reading it (e.g. `grep -c '^| [A-Z][A-Z][A-Z]-[0-9]' dependencies.md` or equivalent for each table), not recalled from memory.** This is stitch's instance of the read-from-disk discipline that [`compaction_policy.md`](compaction_policy.md) requires of compaction-accept procedures -- it also catches recall errors when no compaction occurred.

   5b. **Resolve inconsistencies (if any).** If the `## Corpus inconsistencies` section has rows after the completion gate passes, resolve them now -- do not defer to a separate session. For each inconsistency row:
   - Re-read the cited sources to confirm the contradiction is still live.
   - Identify the authoritative source (entity files > index files > narrative files; explicit P3 research > inherited P2 stub).
   - Edit the wrong source to match the authoritative value. If the edge text itself is wrong, edit the edge text and propagate to inline cross-refs.
   - Remove the inconsistency row from `## Corpus inconsistencies`.

   **Why auto-resolve instead of deferring.** The completion gate (sub-step 5a) is the structural fix that guarantees audit exhaustiveness -- not the phase separation. Once the gate confirms every edge was audited, resolution can proceed safely because the walk is already done. Deferring to a separate trigger adds a user round-trip with no decision value; the authoritative source is almost always clear from the inconsistency description, and the user reviews the diff after the fact either way.

   5c. **Propagation check (mandatory after every edge-text correction in 5b).** When step 5b edits an edge's text (not just a source file) to replace a wrong value with the authoritative one, the wrong value may live in inline cross-refs, sibling-file summaries, and unrelated-looking cross-references scattered across the corpus. The audit cannot reach these because its read scope is `(edge × cited-source)` -- inline propagation surfaces are not part of any edge's cited list. For each edge-text correction:
   - Capture the literal old value being replaced (e.g. `"Cluster bolt"`, `"Polymer Jelly scarcer"`, `"E39 permanently locks"`).
   - `grep -rn "<old-value>" <corpus-root>` -- exclude `_processed/`, `research_inbox/`, `research_briefs/`, `.claude/`.
   - For every match: classify as (a) update to new value (the same wrong claim propagated -- fix it), (b) different legitimate use of the same string (leave alone, note the disambiguation in the audit trail), or (c) corpus inconsistency that needs its own row in `## Corpus inconsistencies` (when the match exposes a second contradiction the original audit didn't catch).
   - Track every match + classification in the per-edge audit trail. The classification IS the discipline -- "I greppped and found nothing" without showing the matches is not sufficient.

   **Propagation completion gate.** Before proceeding to 5d, the completion gate (5a) extends: in addition to `audits-done == edges-in-dependencies`, the model must enumerate `propagation-done == edge-text-corrections-in-5b`. Every 5b edit that changed an edge's text must have a corresponding grep run with classified matches. If any 5b edit lacks a propagation grep, return to 5c for that edit. Do not proceed to 5d until both lists match.

   **Why this step exists.** The "propagate to inline cross-refs" clause was previously buried as a comma-clause inside 5b. Empirically dropped in multiple stitch sessions where an edge text was corrected but the wrong value continued to live in inline cross-refs across the corpus. The cooperative read mode of the per-edge audit does not naturally transition into the adversarial read mode propagation requires; promoting it to a mandatory mechanical sub-step with its own completion gate is the structural fix.

   5d. **Write run log + CHECKPOINT.** Add a row to `dependencies.md` stitch run log -- include the count from step 4's audit in the `Inconsistencies surfaced` column (count the inconsistencies found, even if they were resolved in 5b). Update `## Phase state` in CHECKPOINT: `stitch: complete YYYY-MM-DD`, `stitch_stale: false`, `stitch_scope: full` (or scoped list). Add `## Harness changelog` entry listing DEP-IDs written (IDs only -- no descriptions), inconsistencies found and resolved, plus an optional aggregate skip count if borderline candidates were common.

6. Chat reply at end of session: bare completion line per **Chat output discipline** above. No edge tables, titles, or rationales.

---

## Builder/reader split

Stitch and zipper are builder tasks. The reader-side persona (the skill a player downloads to use a pre-built guide) does not run either pass. A reader who downloads a pre-built guide and wants to extend or update it needs the builder skill.

The reader persona carries this disclaimer:

> Running stitch, zipper, ingestion, or aggregation contributions requires the builder skill. If you downloaded a pre-built guide and want to update or extend it, see the hintforge framework.

A player who runs hintforge in week 1 (sparse external knowledge base) and wants to re-run ingestion + stitch in month 2 (richer knowledge base) needs the builder skill for the re-run. The `## Phase state` block in CHECKPOINT makes re-running any phase from natural language straightforward.

---

## What is out of scope

- **New research.** If an edge requires content the corpus does not have, that is a P3 gap or a fresh research run, not stitch.
- **Unpromoted live-observed truths.** Player narration that remains only in CHECKPOINT or session context is not read by stitch. Once a live-observed truth is promoted to a corpus file edit with a `contributor:` tag, it is in scope.
- **Rewriting existing claims.** Stitch adds connections; zipper restructures redundancy. Neither rewrites facts.
- **`persona.md`, `warning_tiers.md`, and hint-ladder logic.** Stitch does not modify these files. The persona's reference behavior expands -- it now has `dependencies.md` to consult -- but its voice, tier rules, and escalation logic are untouched.

# Compaction policy

How the hintforge builder handles context-window compaction during multi-step procedures.

**Framing.** Compaction is harness-driven, not model-controlled -- the agent CLI auto-compacts when the context window fills, and the running model cannot decline it. This policy is therefore not a list of "do" and "don't" actions against compaction itself. It is:

1. A per-procedure stance on whether compaction is **expected** for that procedure or not.
2. A discipline for what to do when compaction happens in a procedure where it's expected.
3. A discipline for what to do when compaction happens (or is imminent) in a procedure where it's not.

The expectation label drives a diagnostic reading. Compaction in a procedure where it's expected is normal operation -- run the handlers and move on. Compaction in a procedure where it's not expected is a scope or model-choice failure that needs to be surfaced in the recap, because post-compact output for those procedures is structurally fragile (scaffolded files, table cells, and verification artifacts get damaged by the lossy summary).

## Per-procedure expectation

| Procedure | Compaction expectation | What an observed compaction means | Operational handler |
|---|---|---|---|
| `setup_wizard.md` | UNEXPECTED | Setup is short, deterministic, and produces structurally fragile output (scaffolded corpus + briefs). Compaction before step 9 = wrong model (Sonnet minimum), scope creep, or a sub-step that looped. Compaction approaching step 9 = the file-verification + execution block is at risk; a recoverable handoff is required. | Stop early; print the step 9 summary table as a copy-paste handoff for a fresh session; advise the user to resume there. See setup_wizard.md step 9 failsafe. |
| `ingestion.md` | EXPECTED (P2/P3 at CRPG scale; P1 at large scale also expected) | Normal operation; no diagnostic signal. | Run handlers: step 8 Index re-derivation + read-from-disk discipline for every count and table cell. |
| `stitch_and_zipper.md` -- stitch | EXPECTED on 100+ file corpora | Normal operation. | Per-edge convergence audit (Phase B) + count-from-disk summary (sub-step 5). |
| `stitch_and_zipper.md` -- zipper | UNEXPECTED | Zipper is short by design. Compaction = scope is wrong (too many candidate overlaps queued, or the corpus is far larger than zipper assumes). | Stop; narrow scope; restart in a fresh session. |
| `doctor.md` | UNEXPECTED by default; EXPECTED for Branch C full-corpus migrations only (e.g. v4 → v5 entity-overlay migration) | Targeted doctor branches should not compact. A compacting doctor run signals a branch that's too broad for the scope label. Branch C full-corpus migrations legitimately need ingestion-class handling. | Default: stop; narrow the branch; restart. Branch C: apply ingestion's EXPECTED discipline. |

## Discipline when EXPECTED

When a procedure with EXPECTED stance experiences (or is likely to experience) a compaction event:

1. **Treat the compaction summary as lossy.** Summaries reliably preserve high-level intent and broad action history, and reliably lose counts, table cells, prose numerals, list lengths, and small details. Any post-compact work that quotes a count or cell from the summary instead of re-reading the source file is a bug.
2. **Read from disk, not from the summary, for any factual claim** the procedure will report, embed, or write. This applies to file counts, row counts, table cell values, prose numerals, and any other discrete value.
3. **Run the procedure's compaction-handler steps regardless of whether compaction was observed.** Steps designed as compaction handlers (e.g., ingestion step 8 Index re-derivation, stitch's count-from-disk summary) also catch non-compaction-induced failures -- inherited stubs, recall errors, write-order races. Don't gate them on "did we compact?"
4. **If the harness exposes a compaction signal, log it in CHECKPOINT.** The harness changelog entry for the session should note "session compacted at step N" so future analysis can correlate bugs to compaction events.

## Discipline when UNEXPECTED

When a procedure with UNEXPECTED stance is approaching or has experienced compaction:

1. **Diagnostic reading.** Observed compaction is a scope or usage failure to surface in the recap, not normal operation. Note it explicitly with a likely cause and a recommendation, e.g.: *"This procedure compacted, which is unexpected for zipper. Likely cause: corpus contains far more candidate overlaps than zipper was scoped to handle. Recommend: re-run with a narrower scope (one subdirectory at a time) in a fresh session."*
2. **Behavioral discipline (before compaction hits).** When context usage approaches the limit mid-procedure, stop voluntarily and hand back to the user with what's done so far, rather than producing post-compact output. Post-compact output for these procedures is structurally fragile -- the lossy summary will damage scaffolded files, table cells, or verification artifacts in ways that don't always surface until much later (e.g. a prose miscount baked into an aggregation index file during P3 ingestion, surviving every later phase).
3. **Hard limit.** The model cannot prevent harness-triggered auto-compact. The discipline is about (a) when to stop voluntarily before the harness forces a compact, and (b) how to read the situation if it happens anyway. There is no enforcement mechanism inside the skill files -- the discipline is a behavioral rule the model applies based on its own context-usage signal.

## Procedure-specific handlers (cross-refs)

- **`setup_wizard.md` step 9 file-verification failsafe.** Before composing the verification block, the builder checks remaining context space. If insufficient (or if earlier steps burned excess context for any reason -- looping research, scope creep, repeated re-asks), the builder hands the user the captured step 1-8 parameters plus the verification block as a copy-paste prompt for a fresh session. This is a general failsafe -- compaction pressure is one trigger, but the same handoff applies if earlier steps fell apart for unrelated reasons. It keeps setup recoverable from arbitrary mid-procedure failure.
- **`ingestion.md` step 8 Index re-derivation.** Handles index / entity-file drift introduced by post-compact recomposition from summary (and inherited-stub errors from earlier phases).
- **`stitch_and_zipper.md` Phase B per-edge convergence audit + count-from-disk summary.** Handles per-edge convergence (cited sources must contain the specific value the edge claims) and recall-based count errors (the v4 RT stitch run's "claimed 17 edges, actual 19" math error).
- (More to be added as future compaction-driven failure modes are documented.)

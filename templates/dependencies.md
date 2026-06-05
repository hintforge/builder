# Dependencies -- [Game Name]
<!-- hintforge · stitch pass · last run: YYYY-MM-DD -->
<!-- Every stitch run re-audits ALL existing edges + adds new ones. The per-edge convergence audit (open each cited source, verify the specific value) applies to every row in this file on every run, not just new candidates. A game patch, DLC, or new ingestion phase can change facts that existing edges cite -- only a full re-audit catches that. See `stitch_and_zipper.md` Phase B "Re-run scope: always full." Inconsistencies (cited source contradicts edge text) land in the `## Corpus inconsistencies` section; the edge row stays in place. -->

## Cross-system edges

| Edge ID | System A | System B | Dependency description | Confidence | Source files |
|---------|----------|----------|------------------------|------------|--------------|
| DEP-001 | [system name] | [system name] | [one sentence: action/state in A affects state/outcome in B] | high | [file-A.md], [file-B.md] |

## PoNR / lockout edges

| Edge ID | Trigger | Locked out | Notes | Source files |
|---------|---------|------------|-------|--------------|
| PON-001 | [action or zone entry] | [what becomes inaccessible] | [timing window if known] | [file.md] |

## Missable / sequencing dependencies

| Edge ID | Action | Window | Consequence | Source files |
|---------|--------|--------|-------------|--------------|
| SEQ-001 | [action] | [before/after what] | [what is missed or altered] | [file.md] |

## Stitch run log

| Date | Scope | Edges written | Edges proposed (pending) | Inconsistencies surfaced | Model |
|------|-------|---------------|--------------------------|--------------------------|-------|
| YYYY-MM-DD | full | [N] | [N] | [N] | sonnet-class |

<!-- Inconsistencies surfaced: count from the per-edge convergence audit (stitch_and_zipper.md Phase B). Counts must be derived by reading this file, not recalled. A non-zero count requires an explicit chat call-out and at least one populated row in the Corpus inconsistencies section below. -->

## Corpus inconsistencies

Stitch's per-edge convergence audit (see [`../../hintforge/builder/stitch_and_zipper.md`](../../hintforge/builder/stitch_and_zipper.md) Phase B) populates this section when a candidate edge's cited sources contradict each other. Each row records the contradiction; resolving it is the user's call (or a follow-up doctor / ingestion run). Edges blocked on an unresolved entry are NOT written to the tables above until the inconsistency is closed.

| Detected | Files | Conflicting values | Suspected authoritative source | Status |
|----------|-------|--------------------|--------------------------------|--------|
| YYYY-MM-DD | [file-A.md], [file-B.md] | A says "[X]"; B says "[Y]" | [entity-or-primary-vector file, or blank for user to resolve] | open |

<!-- Status vocabulary: open (just surfaced) | resolved (user picked authoritative value + corrected the other file) | accepted (user accepted both -- rare; usually means the claim is genuinely ambiguous in-game). When status flips to resolved, the next stitch run can re-evaluate the edge. -->


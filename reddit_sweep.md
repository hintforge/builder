# Reddit Sweep -- Manual Community Knowledge Harvest (MCP module)

This procedure runs as a **manual module sweep** at one of two phase-bounded entry points: **(a) post-final-research-phase, pre-stitch** (initial harvest after the deep-research cascade completes); **(b) doctor Branch B/C** (post-cascade top-ups for patches, DLC, or targeted gap repair). It browses the game's subreddit(s) via the `reddit-mcp-buddy` MCP server, surfaces community-confirmed gameplay findings (mechanics, dev posts, undocumented interactions, "is this a bug" threads, build discussions), and writes them to a findings file in the research inbox at `<game>/research_inbox/module/reddit_sweep.<game>.<ISO-date><N>.md`. The file does not auto-ingest -- it is gated behind explicit user confirmation. The user triggers the sweep manually ("run the reddit sweep") or invokes it via doctor with an optional `scope-query` parameter.

> **Why this is its own file + own session.** Setup, ingestion, stitch-and-zipper, and doctor all assume the corpus is the unit of work; this is the first framework procedure where an external **MCP server** is the unit of work, with its own reachability prereqs, auth-tier pacing, and budget shape. Folding it into ingestion would conflate two failure surfaces -- a partial reddit-sweep file (MCP rate limit, sub doesn't exist) is a different recovery situation than a partial ingestion (claim format violation, missing brief). Beyond the file separation, the sweep runs in its **own session** (not chained from P1 ingestion): a fresh context window keeps the sweep's MCP-pacing and crawl-budget reasoning uncontaminated by the ingestion session's token load, and a sweep failure (MCP unreachable, sub gone) doesn't taint a successful ingestion's state.

> **Compaction expectation:** UNEXPECTED during the sweep itself -- it's a single bounded crawl, capped at 300 posts evaluated, with no sub-agent calls. A compacting sweep (before the findings file is written) means either the cap is wrong or the traversal logic is looping. The combined sweep + user-confirmed ingestion flow that follows (user types `yes` at the ingestion gate, triggering the spoiler-classification sub-agent + corpus distribution) is denser; a compaction during that downstream ingestion phase is acceptable -- the sweep's findings file is on disk before the ingestion gate fires, so the artifact survives any compaction in the post-write phase. See [`compaction_policy.md`](compaction_policy.md).

> **First framework procedure with an external dependency.** All prior framework procedures are file-based; this one requires `reddit-mcp-buddy` to be reachable from the **Claude Code runtime** (not just Claude Desktop -- the two carry distinct MCP configs). Per the transparent-operations hard rule in [`CLAUDE.md`](CLAUDE.md), the sweep aborts cleanly before crawling if MCP is unreachable; it does not silently fall back to direct web fetch or any other path.

## Trigger conditions

**Canonical trigger phrase (all sweep runs):** the user types **`hintforge doctor, reddit sweep`** inside `Guides/<game>/` in a fresh session. The `hintforge doctor` anchor is what loads the skill; the `reddit sweep` qualifier routes here. This is the single phrase for both windows below -- the windows differ by corpus phase, not by trigger phrase. There is no standalone phrase, no automatic / chained / in-session invocation from any caller; the user always invokes the sweep deliberately via this anchor, and that session is dedicated to the sweep.

The sweep has exactly two valid invocation windows. Triggers outside these windows are rejected with a redirect to the appropriate window.

- **(a) Initial harvest, post-final-research-phase, pre-stitch:** the user types `hintforge doctor, reddit sweep` AFTER the final brief in the cascade has been ingested and BEFORE `stitch` runs. The final brief is whichever phase the cascade configuration ends at (P3 for standard P1+P2+P3 cascades; P2 for `[SKIP_P3]` cascades; P1 for `[SKIP_P2]`+`[SKIP_P3]` cascades). After the final brief's ingestion completes, [`ingestion.md`](ingestion.md) step 12's FINAL-brief recap surfaces a one-line pointer to this trigger -- the user opens a fresh session and types it. No `scope-query`; the sweep runs against the full game. The separate-session pattern is deliberate: it isolates the sweep's failure surface (MCP reachability, rate-limit pacing) from the ingestion session and keeps each session's context window scoped to one bounded task.
- **(b) Post-cascade top-up:** the user types `hintforge doctor, reddit sweep` (optionally with a scope phrase, e.g. `hintforge doctor, reddit sweep for the <patch/DLC/gap>`) after the initial cascade-+-stitch ship, to pull post-patch / post-DLC / gap-fill community findings. An optional `scope-query` (the patch name, DLC name, or gap description) constrains finding criteria to scope-query-relevant content; everything else in the traversal logic stays intact. This is the path for any top-up sweep, including when a prior `doctor` session has already scaffolded architecture for a DLC (see [`doctor.md`](doctor.md) Branch B) -- the architectural extension and the sweep are separate dedicated sessions.

### Invalid invocation windows (and why)

- **Mid-cascade (post-P1 with P2/P3 pending; post-P2 with P3 pending):** the sweep deposits findings into corpus files that the NEXT cascade phase will then encounter as `status: research-integrated` prior-phase content. The next phase's step-7 reconciliation has to distinguish "stale prior-phase claim needing supersession" from "sweep-augmented claim already at current state" with no in-corpus marker for the difference. In practice the model collapses step 7's content-propagation audit into step 8's status-field check and skips supersession propagation for files the sweep touched -- a `status: research-integrated` value carried over from a prior phase reads as "this file is done" even when the new phase's result contains supersessions that affect the file's content. Phase guard prevents the failure mode by keeping the corpus in a clean "prior-phase only" state through cascade end.
- **Post-stitch, no doctor branch:** stitch's audit is the gate that locks in cross-file consistency. Running the sweep AFTER stitch (outside doctor) lands findings into a corpus that stitch has already audited; the new findings get no audit pass at all unless stitch is re-run. Doctor exists precisely to handle "the corpus is shipped, but new community knowledge needs to land" -- it scopes the change + invokes the sweep + queues the reconciliation work without bypassing the audit layer.

If the user triggers the sweep outside these windows, surface a one-line refusal naming the current phase state + the correct path. Example: "Sweep can't run here -- corpus shows `p2_ingestion: complete, p3_ingestion: not started`. Run P3 ingestion first; the sweep pointer will appear in P3's recap. (Or, if P3 is intentionally skipped, set `p3_ingestion: skipped` in the corpus's CHECKPOINT phase state, then re-trigger.)"

### Design rationale: why separate-session, not in-session continuation

Three converging reasons:

1. **Failure surface isolation.** The sweep's failure modes (MCP server unreachable, subreddit gone / private / banned, rate-limit hit, auth-tier misdetected) are operationally distinct from ingestion's failure modes (claim format violations, missing brief, spoiler-classification sub-agent errors, vector routing ambiguity). Running both in the same session means one failure can leave the other's state in an awkward intermediate position -- a sweep that aborts on MCP-unreachable mid-traversal doesn't taint a successful ingestion's state if it never started; an ingestion that hits a sub-agent error mid-distribution doesn't strand a successful sweep's artifact if the sweep finished cleanly first. Separate sessions enforce that "one task per session" boundary.
2. **Context-window scoping.** The combined sweep + spoiler-classification + multi-file ingestion flow is dense enough to push a single session past compaction boundaries on real corpora. A fresh session for each phase keeps the model's working context bounded by the actual task scope, not the cumulative scope of two tasks chained back-to-back. The findings artifact is the handoff (on disk, durable); the session boundary aligns with that handoff.
3. **Prompt-design lesson, generalizable.** This procedure went through three earlier ships where the post-P1 invocation was an in-session prompt (Reddit-specific, then generic-resource-module, then anti-presupposition tightening). The model consistently collapsed the generic framings back into a specific-Reddit framing or otherwise elaborated past the spec's intended shape. The defect class turned out not to be "the prompt is badly phrased" but "the prompt should not exist." When a procedure's prompt resists mechanical tightening across multiple ships, the question to ask is not "what's the right prompt shape?" but "should there be a prompt at all?" The answer here was no: a memorable manual trigger in a fresh session beat every in-session prompt variant. This pattern likely applies to other framework prompts that have required multiple tightening passes.

The trade-off: discoverability. A user who doesn't read the final-brief recap may not learn about the sweep. Mitigation: the recap pointer names the trigger phrase literally (`hintforge doctor, reddit sweep`), so the user only needs to remember the procedure exists, not its exact invocation. The trigger is the same string referenced throughout this file, making it findable by grep or memory. The `hintforge doctor` anchor doubles as the skill-load trigger, so the phrase reliably loads the skill even from a cold session.

## Pre-flight (mandatory)

Before any crawl runs, verify all four conditions. If any fail, abort and surface the failure to the user; do not crawl silently.

### 1. Session location

The session is **opened inside the game folder** (`Guides/<game>/`), not at workspace root or inside `hintforge/`. The agent's working directory determines which game's research inbox receives the artifact.

### 2. MCP reachability (Claude Code runtime, not Desktop)

Verify `reddit-mcp-buddy` is reachable from the current Claude Code runtime. CC and Claude Desktop carry **distinct MCP configs**; reachability from one does not imply reachability from the other. Verification:

1. Confirm the MCP server is listed in CC's available tools. If absent, the server is not wired into CC's config.
2. Attempt a low-cost ping call (e.g. `browse_subreddit` against a known-existent sub like `r/announcements` with a small page size). If the call errors with a connection / not-found / unavailable response, the server is unreachable.

**On unreachable, abort and instruct.** Surface to the user:

- The server is not reachable from this CC runtime.
- Common causes: (a) MCP server not running on this machine; (b) wired into Claude Desktop's config but not CC's config (two distinct files); (c) sandbox CC instance that did not inherit the user-level MCP config (sandbox instances inherit only when explicitly wired).
- How to verify: have the user list CC's available MCP tools and confirm `reddit-mcp-buddy` is among them. Refer to the `reddit-mcp-buddy` documentation for the CC-side config path.
- Offer: retry (after user confirms wiring) or skip the phase (proceed to the next step of the caller without running the sweep).

Do not fall back to direct `web_fetch` against `reddit.com` -- the Reddit ladder in [`ingestion.md`](ingestion.md) is for per-thread citations during P2/P3 result-file ingestion, not for autonomous community-knowledge harvest.

### 3. Auth-tier detection

`reddit-mcp-buddy` supports three tiers; read the configured tier at startup and pace MCP calls accordingly so the per-minute request rate stays under the ceiling:

- **Anonymous:** 10 requests / minute. Default. No credentials required.
- **App-only:** 60 requests / minute. Requires Reddit app client ID + secret.
- **Authenticated:** 100 requests / minute. Requires full user credentials on a "script" app type, used by the same account that created the script app.

Record the detected tier in the artifact frontmatter at file-write time so the artifact is self-explaining on later review. Pacing math: sleep `60 / <ceiling>` seconds between MCP calls (e.g. 6s anonymous, 1s app-only, 0.6s authenticated).

### 4. Budget envelope surface (token-aware execution)

Before any crawl call, surface the cost shape to the user:

> Reddit sweep budget: 300 posts evaluated (hard cap), ~45-90 MCP requests typical, paced against the configured `<tier>` tier (~`<wallclock-estimate>` wallclock; ~12-15 min at anonymous tier, ~3-5 min at app-only, ~2-3 min at authenticated). Proceed?

User can decline ("skip the sweep" / "do it later"). On decline, leave a one-line note in the caller's recap and stop. On proceed, continue to subreddit identification.

## Subreddit identification

The order favors a focused main-game sub first; broader coverage is the fallback, not the default.

1. **Primary candidate: main game sub.** Build `r/<gamename>` with normalization (strip spaces, lowercase, remove punctuation, try common abbreviations / known nicknames).
2. **Verify existence.** Call `browse_subreddit` against the candidate; the server returns a clear error or empty result for non-existent subs, and the subreddit sidebar / community-info confirms a real community vs. a squatted name. Record the verification outcome.
3. **If the main game sub does not exist:** fall through directly to a broader-coverage sub. Candidates in order:
   - (a) franchise sub if the game is part of a multi-game franchise;
   - (b) developer sub if one exists and is active;
   - (c) genre / platform-aggregator sub if neither (a) nor (b) applies.
   Run the full sweep against the broader sub instead.
4. **If the main game sub exists but is inactive:** run the full sweep on it first, then check total findings count. If the main-sub full sweep produces **20 or fewer findings**, **fall through to a broader sub** (per the candidate order above) and run a second full sweep against it, continuing until the global 300-posts-evaluated cap is hit. Findings from both sweeps accumulate in the same output file with the originating sub recorded per finding.
5. **Confirmation (structured).** State the chosen primary sub, then confirm the fallthrough policy via a structured `AskUserQuestion` call -- never an inline free-text prompt. Question text: "Fallthrough plan for the `<game>` sweep: `r/<sub>` runs first; if it produces 20 or fewer findings, the sweep continues against a broader sub within the same 300-post budget. Which fallthrough?" Options (closed set, exactly three):
   - **Use `r/<sub2>`** -- the broader-sub candidate chosen per step 3's order. The default.
   - **Pick a different broader sub** -- on selection, ask the user to name it. Do not propose further candidates yourself.
   - **No fallthrough** -- accept a thin sweep if the main sub comes up short.

   If the main game sub does not exist (step 3), the same three-option shape applies with the broader sub as the primary: run `r/<sub2>` / name a different sub / skip the sweep. **Do not ad-lib alternative subs inline if the user declines a candidate** -- only the user can judge whether a sub matches the corpus's purpose, and inline counter-proposals turn one closed decision into a multi-message back-and-forth. This is the only required user touch during the autonomous sweep until the post-sweep ingestion gate.

### Activity check (informational)

Before committing to the primary candidate, sample recent activity (post frequency, comment volume on top posts) and note `active | moderate | quiet` in the artifact. The activity note is **informational only** -- the fallthrough trigger is post-pass findings count (<=20), not the pre-crawl activity sample. A pre-crawl "quiet" reading sets user expectations but does not preempt the main-sub sweep.

## Sweep traversal

Four time windows, traversed in order, sorted by **top** in each:

1. All-time
2. Year
3. Month
4. Week

Within each window, scan post titles, open promising threads via `get_post_details`, evaluate content, record findings.

### Per-window floors (must-have unique gameplay findings)

- All-time: 15
- Year: 10
- Month: 7
- Week: 0-5

These are floors, not ceilings. Exceed a floor when findings are coming readily. Fall short when the window is genuinely thin (a 12-year-old game's week window may have zero findings; that is expected, not a failure).

### Two-budget model

Two budgets, distinct because `reddit-mcp-buddy` does not consume one API request per post.

- **Posts-evaluated cap: 300 posts across the entire sweep.** A "post evaluated" is one post the procedure considered (title scanned in a returned list AND not skipped under the §Skip-without-counting rules below, or thread opened via `get_post_details`). This is the attention cap -- it bounds how many threads get real attention, regardless of how the underlying MCP packs them into requests. Titles skipped at browse-scan time per §Skip-without-counting (memes, fan art, cosplay, screenshots, pure opinion posts) do NOT count against the cap; they are filtered out before attention is spent.
- **MCP-requests budget: derived from the configured auth tier.** A `browse_subreddit` call returns many posts in **one** MCP request (typical Reddit page sizes around 25). A `get_post_details` call is 1 MCP request (2 if subreddit auto-detection is needed -- always pass `subreddit` to keep it at 1). With per-page browse calls + per-opened-thread detail calls, a 300-post-evaluated sweep typically consumes ~45-90 MCP requests, within the per-minute pacing for any tier (the floor is set by browse-page count, not by cap size).

When the posts-evaluated cap (300) is hit, the sweep terminates. The MCP-requests budget never terminates the sweep on its own; it informs **pacing** (sleep between calls to stay under the per-minute ceiling for the configured tier).

The fallthrough-to-broader-sub case (main sub <=20 findings -> broader sub) shares the same posts-evaluated cap: 300 total, not 300-per-sub.

### Skip-without-counting (browse-scan time filter)

Titles encountered in a browse-list return that match the patterns below are skipped at browse-scan time and **do not count against the posts-evaluated cap**. The procedure recognizes these patterns as structurally incapable of producing a finding (per §What counts as a finding) and refuses to spend attention budget on them. This is distinct from §What counts as a finding's exclusion rules, which apply at finding-acceptance time after a thread has already been opened.

Skip-without-counting patterns:

- **OP flair (when present in browse-list returns):** `Memeposting`, `Meme`, `Memes`, `Fan Art`, `Fanart`, `Fan-Art`, `Cosplay`, `Screenshot`, `Screenshots`, `Art`, `Gif`, `Video` (when video-only with no OP body text). Game-specific flair variants follow the same intent (any flair whose label maps to "non-analytical user-generated content").
- **Title patterns (regardless of flair):** titles starting with `i made` / `i drew` / `i painted` / `i sculpted` / `i printed` / `i cosplayed` / `my cosplay` / `my fan art` / `my drawing` / `my painting` / `my [character name] cosplay` / `[OC]` / `[Fan Art]` / `[Cosplay]`; titles ending in `?` that are pure opinion (`best class?`, `favorite character?`, `who's better?`, `am i the only one?`); pure screenshot share titles (`screenshot from`, `look at this`, `caught this moment`); rant / vent titles (`why does the game`, `am i the only one who hates`).

Edge cases that do NOT skip (open the thread despite surface match):

- A "memepost" that's actually a build-discussion in meme format (low frequency but real -- the post body or top comment contains mechanical content). The rule is conservative: if the title alone signals memepost, skip; if the OP body or top comment surfaces mechanical content during the brief title-scan, open and evaluate.
- Dev-flair posts (e.g. `Dev Response`, `Official`, or any flair carrying the developer studio's name): never skip regardless of other surface match.
- Posts with explicit "build" / "mechanic" / "patch" / "bug" / "interaction" keywords in the title, even with a meme-adjacent flair.

Record the skip decision in the per-window stop-condition tally as `<N> skipped without counting` (informational; not required in the artifact frontmatter unless the count is high enough that it explains a window's apparent thin yield).

### Browse-to-search pivot heuristic

When **5 or more consecutive titles in a single browse-list batch are skipped** under §Skip-without-counting (memes + fan art + screenshots dominating the top-sort feed), terminate that browse-list early and pivot to `search_reddit` with mechanical-content queries (`tips guide mechanics build strategy <game-specific term>`; `<game-specific mechanic name> <build-or-bug-or-interaction>`; etc.). The pivot is a fall-forward, not a fall-back -- the sub is healthy, but its top-sort feed is dominated by non-finding-candidate content and targeted search bypasses that. Search results count against the cap normally (each result-list title is one "post evaluated" subject to the same §Skip-without-counting filtering).

The heuristic is a **per-browse-list** trigger, not a per-window trigger. A window may run multiple browse-list batches (loop-back expansion, fallthrough); each batch evaluates the 5-consecutive-skip threshold independently. Once a pivot fires within a window, prefer search for the remainder of that window unless a follow-up browse-list returns finding-candidate content readily.

### Per-window stop conditions

A window's traversal ends when any of these is true:

1. Window floor met and no further findings appearing readily.
2. Window floor met and reasonable license to expand exercised.
3. Global 300-posts-evaluated cap hit (terminates the whole sweep).
4. Window's top-sort feed exhausted.

When (3) terminates inside a window, the sweep ends entirely. When (1), (2), or (4) ends a window, advance to the next.

### Loop-back rule

After the week window finishes (or aborts at floor 0 if the sub is too quiet), check per-window floor status.

- If a window finished with **zero or near-zero findings** specifically because the game is old or the sub is quiet for that window, loop back to expand the previous window. Week empty -> return to month. Month also dry -> return to year. Year insufficient -> return to all-time.
- Loop-back consumes the same global 300-posts-evaluated budget.
- Loop-back is **one expansion pass per earlier window**. Do not oscillate.
- Loop-back triggers on **dryness in the later window**, not on total-count shortfall. Total-target stopping is the ingestion handoff's call (see Stopping the whole sweep).

### Sequel-dominance escalation

When a recent window (year, month, or week) finishes with zero or near-zero findings because the sub is **active but absorbed by a different game-version** -- the sub hosts a sequel, predecessor, or sibling title whose recent posts crowd out the target version's content -- the standard loop-back rule won't help. Looping back to earlier windows hits the same sub-dominance pattern; the dryness has a different cause than "old game" or "quiet sub" and needs a different escalation.

**Detection signal:** a recent window has many posts but they evaluate as off-target-version after content scan. Generalizable pattern: the game series shares a subreddit across multiple titles (per-game subs that map 1:1 to a single corpus are rare for established series). When the corpus is for one title and a different title in the same series shipped recently enough to absorb sub activity, the recent windows fill with the wrong title's content. Common shapes: a sequel crowding out a predecessor (corpus = predecessor); a long-running series subreddit where multiple titles compete for window share by recency; a sibling title (spin-off, remaster, expansion treated as a separate release) absorbing discussion. The model identifies the pattern via the per-thread content scan: when a window's posts predominantly reference titles, characters, mechanics, or scenarios that don't belong to the target version, sequel-dominance is the diagnosis.

**Escalation procedure:** run a date-bounded `search_reddit` pass against the target version's content. Bound the search to the target version's lifespan -- between its own release date and the release date of the version that's crowding it out (when corpus is the predecessor, upper-bound to the sequel's release; when corpus is the sequel, lower-bound to the predecessor's last major patch or the sequel's own release). Use query terms specific to the target version: titles, mechanic names, scenario names, NPC or location names that are unique to the target. The pass consumes the same global 300-posts-evaluated budget. **One pass per sequel-dominance trigger; do not oscillate.** Findings attribute to the originating window with a `(sequel-filter)` suffix (e.g. `first surfaced in window: year (sequel-filter)`) and dedupe against existing findings normally.

This is distinct from loop-back: loop-back expands an earlier window when later windows are dry from age or quietness; sequel-dominance escalation jumps to a different query mode (date-bounded search) when later windows are dry from version-fragmentation. Both can fire in the same sweep if both causes apply (e.g. a year window dominated by a different game-version AND an all-time week sub-sample that's thin -- sequel-dominance handles the version-dominance; loop-back handles the week thinness).

### Design rationale: dryness causes aren't interchangeable

The loop-back rule's two original causes (old game / quiet sub) assume the sub's content maps 1:1 to the corpus's target version. Expanding to an earlier window helps because earlier windows are samples from the same target-version-relevant pool, just older. Version-fragmentation breaks that assumption -- the sub matches the franchise, not the specific game, so earlier windows are sampling the same franchise-wide pool with the same off-target-version saturation. Looping back doesn't help; the dominance hits every window. The escalation mode has to change, not just the window.

The bidirectional handling (predecessor-vs-sequel symmetric) reflects the same root cause from either direction: corpus-targets-one-version, sub-spans-many-versions, recent activity is from whichever-version-is-most-current. When corpus is the predecessor, upper-bound to the sequel's release. When corpus is the sequel, lower-bound to the predecessor's release (or the sequel's own release, whichever is older relative to the sub's current activity peak). The bound direction inverts but the procedure stays one rule.

Generalizable lesson: any future module-sweep procedure that browses a shared resource (a YouTube channel covering multiple games, a wiki spanning series content, a Discord with cross-game channels) likely needs the same shape of taxonomy: dryness causes aren't interchangeable, and the escalation mode depends on which cause applies. A single "loop-back" pattern works only when the resource maps 1:1 to the target.

### Fallthrough to broader sub

After all four windows finish on the main game sub (including any loop-back expansion), check total findings count. If the main-sub total is **20 or fewer findings** AND the global cap has not been hit, restart the four-window traversal against a broader sub per the candidate order above. Subsequent findings append to the same output file with each finding tagged by its originating sub. The 300-posts-evaluated cap remains the hard stop.

The fallthrough is a single pass: main sub -> broader sub. If the broader sub also returns thin coverage, accept the thin sweep; do not chain further fallthroughs.

### Recurring-question signal

Across windows, track recurring questions (the same gameplay question appearing in multiple threads across time spans). These do not count toward floors but are surfaced in a dedicated section in the output file. A question recurring in all-time, year, and month is a strong signal the guide must answer.

## What counts as a finding

A finding is a unique gameplay result, tip, or gem. Qualifies:

- Dev-flair posts (almost always in).
- High-score top-level mechanics explanations.
- Confirmation-by-correction patterns (a reply correcting the OP that gets upvoted past the OP).
- Undocumented interactions, build math, weapon / item interactions not in official docs.
- "Is this a bug?" threads with dev confirmation or strong community consensus.
- Specific encounter, puzzle, or boss strategies that are not obvious from the game's UI.

Does not qualify:

- Pure opinion threads (tier lists, "best class," "favorite character") unless they reveal mechanics.
- Memes, fan art, screenshots without analytical content. (When these are recognizable at browse-scan time from title or flair alone, they are also skipped-without-counting per §Skip-without-counting -- the cap is not spent on attention to content that is never finding-eligible.)
- Discussion threads with no convergent answer.
- Threads that duplicate a finding already captured (dedupe applies).

Two runs against the same sub may produce non-identical findings; that is expected.

### Dedupe

Dedupe operates on **findings**, not posts. A mechanic discussed in three threads across three time windows is one finding with three supporting sources. The all-time pass establishes the canonical finding entry; subsequent windows add supporting sources to the existing entry rather than creating new entries. Findings from the fallthrough broader-sub sweep dedupe against findings already captured from the main sub.

## Stopping the whole sweep

The sweep terminates when any of these is true:

1. All four windows completed on the main sub (including loop-back expansion), AND either total findings >20 OR no broader-sub fallthrough is sensible.
2. All four windows also completed on the broader sub (when fallthrough triggered), including loop-back expansion.
3. Global 300-posts-evaluated cap hit.

The procedure does **not** stop based on a total-findings count. Total-findings sufficiency is the ingestion-handoff's decision when the user reviews the post-sweep summary.

## User-facing messages

### Start

> Identified `r/<sub>` as the primary subreddit for `<game>`. Activity level: `<active | moderate | quiet>`. [If main sub doesn't exist:] Main game sub not found; the sweep would run against broader sub `r/<sub2>` instead.

Then fire the structured fallthrough confirmation (Subreddit identification step 5) -- the closed three-option `AskUserQuestion`, not an inline "confirm or override" sentence. After the user answers:

> Starting Reddit sweep. Traversing top-sorted posts across all-time, year, month, and week windows. Cap: 300 posts evaluated (meme/fan-art/cosplay titles skipped without counting; browse-to-search pivot after 5+ consecutive skips). Per-window floors: 15 / 10 / 7 / 0-5. Auth tier: `<anonymous | app-only | authenticated>` (paced for `<N>` req/min). I'll surface findings as I go and write the full results file when done.

### During (optional progress markers)

Brief progress notes at window boundaries:

> All-time complete: 16 findings, 23 posts evaluated. Moving to year window.

Informational, not strictly required.

### Window shortfall

> Year window: 6 findings against a floor of 10. Subreddit appears to lack deeper coverage for this window. Continuing to month.

### Loop-back

> Week window produced 0 findings. Looping back to month window to pull additional findings within remaining budget.

### Browse-to-search pivot

> 5 consecutive titles skipped under §Skip-without-counting in this browse-list batch (meme/fanart/cosplay-heavy top-sort). Pivoting to `search_reddit` with mechanical-content queries for the remainder of this window.

### Fallthrough to broader sub

> Main sub `r/<sub>` produced `<N>` findings (<=20) across all four windows. Falling through to broader sub `r/<sub2>` within the remaining budget (`<M>` posts available).

### Budget exhaustion

> Hit 300-posts-evaluated cap during `<window>` on `r/<sub>`. Stopping sweep. `<N>` total findings collected (`<S>` titles skipped without counting under §Skip-without-counting). Writing results.

### Completion + ingestion gate

> Reddit sweep complete. `<N>` findings across `<M>` posts evaluated (`<R>` MCP requests). Window summary: all-time `<a>`/15, year `<b>`/10, month `<c>`/7, week `<d>`/`<floor>`. `<K>` recurring questions noted. [If fallthrough triggered:] Broader sub `r/<sub2>` contributed `<X>` findings. Writing results to `<game>/research_inbox/module/reddit_sweep.<game>.<ISO-date><N>.md`.
>
> Ready to ingest into the corpus? (yes / review file first / skip ingestion)

The ingestion gate is **user-confirmed**, not automatic. Write the file and wait for explicit consent before invoking ingestion.

## Output

### File location

`<game>/research_inbox/module/reddit_sweep.<game>.<ISO-date><N>.md`. The `module/` subdir is a sibling to `p1/`, `p2/`, `p3/` and is created on demand (not at wizard scaffold time). See [`templates/folder_structure.md`](templates/folder_structure.md).

### File naming + same-day suffix

`<N>` is a same-day re-run integer suffix starting at **1**. First run on a given date: `reddit_sweep.<game>.<ISO-date>1.md`. Second same-day run: `reddit_sweep.<game>.<ISO-date>2.md`. Different-date runs each start their own `1`. The suffix is always present (no bare-no-suffix first run) so file shape is consistent.

### Re-run semantics

A second sweep against the same game **does not overwrite** the previous file. Each run writes a new artifact with an incremented suffix. The phase is built for periodic top-ups (doctor invocations months later, post-DLC re-sweeps); preserving history matters more than directory tidiness.

Findings carried into the corpus during prior ingestion are unaffected; the inbox file is treated as a fresh artifact each run.

### File structure

Frontmatter block + body. Template at the bottom of this file.

## Ingestion handoff

1. Write the findings file to `<game>/research_inbox/module/`.
2. Surface the completion message + summary (per Completion message above).
3. Ask the user: "Ready to ingest into the corpus? (yes / review file first / skip ingestion)"
4. **On `yes`:** invoke the **"Ingesting a reddit_sweep artifact"** subsection in [`ingestion.md`](ingestion.md) against the new artifact. Per-claim routing follows the rules in that subsection.
5. **On `review file first`:** stop. The user reads the file, then issues a separate "ingest the research" trigger when ready.
6. **On `skip ingestion`:** stop. File remains in `research_inbox/module/` for future ingestion.

### Spoiler-classification discipline (mandatory)

Every claim that lands in the corpus from this sweep -- including Findings AND Recurring-questions entries -- routes through the spoiler-classification sub-agent pass at [`ingestion.md`](ingestion.md) step 3. Many reddit threads carry spoiler markers (Reddit's native `spoiler:` post tag, "[Spoiler]" in title, in-body `>! ... !<` tagging); the sweep preserves these as-is in the findings file (`reddit_spoiler_tag: yes | no` per source), and the ingestion sub-agent uses them as evidence when assigning per-claim spoiler tiers. Recurring-question claims carry **no default tier** -- the sub-agent classifies them like any other claim. No claim ships to the corpus with an unset `spoiler:` tag.

The "Threads scanned but not surfaced as findings" appendix is **inbox-only** -- not ingested. It exists as a re-run aid (avoid re-evaluating known dead ends) and stays in the inbox file when the corpus ingestion runs.

## Failure modes and recovery

- **MCP server unreachable.** Abort before crawling per Pre-flight step 2. Tell the user how to verify the server is running, that it's wired into the Claude Code runtime (not just Desktop), and offer to retry or skip.
- **Subreddit doesn't exist.** Report this; fall through to the broader-sub candidate per Subreddit identification step 3. If no broader sub is sensible, ask the user for an override or skip.
- **Subreddit is private / quarantined / banned.** Report the status; treat the same as "doesn't exist" for fallthrough purposes (broader sub if sensible, otherwise user override or skip).
- **Rate limit hit.** Pacing is designed to keep request rate under the configured tier's per-minute ceiling. If a rate-limit response comes back anyway, wait and retry; if the wait exceeds a reasonable threshold (~2 minutes), pause the sweep and tell the user.
- **Mid-sweep MCP failure.** Write a partial results file with whatever findings exist, mark the file as `status: partial-mcp-failure` in frontmatter, surface the failure to the user. The ingestion gate still applies (the partial file is the user's to decide on).

## Caller contracts

This procedure is called by:

The sweep has a single canonical trigger -- the user types **`hintforge doctor, reddit sweep`** inside `Guides/<game>/` in a fresh session. It is never invoked automatically, chained, or run in-session from another caller. The two windows below differ by corpus phase, not by phrase:

- **Initial harvest, post-final-research-phase, pre-stitch** -- typed after the cascade's final brief has been ingested and before `stitch` runs. No `scope-query`; the sweep runs against the full game. [`ingestion.md`](ingestion.md) step 12's FINAL-brief recap surfaces a pointer to this trigger; the user starts a fresh session at `Guides/<game>/` and types it.
- **Post-cascade top-up** -- typed after the initial ship, optionally with a scope phrase. An optional `scope-query` (a patch name, DLC name, or gap description) constrains finding criteria to scope-query-relevant content. The rest of the traversal logic -- subreddit identification, four-window walk, budget, fallthrough, sequel-dominance escalation -- stays intact. The scope-query narrows what counts as a finding; it does not change how the sweep traverses. When a [`doctor.md`](doctor.md) Branch B (game update / DLC) or Branch C (targeted repair) session has scaffolded architecture for the new content, the sweep is the subsequent dedicated `hintforge doctor, reddit sweep` session -- not chained inside the scaffolding session.

Other callers (stitch, zipper, wizard, ingestion mid-cascade) are out of scope. The sweep is never invoked automatically from setup, the wizard, ingestion, or doctor branch work -- the user's deliberate `hintforge doctor, reddit sweep` invocation is the only entry point. The separate-session pattern (sweep runs in its own session, not chained from any caller) is deliberate per the §Trigger conditions rationale. Mid-cascade invocation (post-P1 with P2/P3 pending; post-P2 with P3 pending) is rejected -- see §Trigger conditions "Invalid invocation windows" for the failure mode that motivates the phase guard.

---

# Template: Reddit Sweep Findings File

```markdown
---
kind: reddit_sweep
game: <game-name>
sweep_date: <ISO 8601 timestamp>
auth_tier: <anonymous | app-only | authenticated>
scope_query: <optional -- present only for doctor invocations>
subreddits:
  primary:
    name: r/<sub>
    coverage_tier: main
    fallthrough_triggered: <yes | no>
  broader:        # present only when fallthrough triggered
    name: r/<sub2>
    coverage_tier: broader
activity_level: <active | moderate | quiet>
posts_evaluated: <N> / 300
posts_skipped_without_counting: <S>     # informational; titles filtered at browse-scan time per §Skip-without-counting
mcp_requests: <R>     # informational
status: <complete | partial-budget-exhausted | partial-mcp-failure | partial-other>
window_summary:
  all_time: <count> / 15
  year: <count> / 10
  month: <count> / 7
  week: <count> / <floor>
loop_backs: [<window-name>, ...]
total_findings: <N>
recurring_questions_count: <K>
---

# Reddit Sweep: <game>

## Sweep notes

<Brief prose: any shortfalls, loop-backs, fallthrough trigger, notable subreddit characteristics, anything the next reader of this file should know about how the sweep went.>

## Findings

### Finding 1: <short title>

- **Claim kind:** <mechanic | bug | build | interaction | strategy | dev-confirmation | lore-question | other>
- **Summary:** <one-to-three-sentence description of the finding>
- **First surfaced in window:** <all-time | year | month | week>
- **Originating sub:** r/<sub>   <!-- which sub surfaced it; matters when fallthrough triggered -->
- **Sources:**
  - Thread: <URL>
    - Subreddit: r/<sub>
    - Window: <window>
    - Sort position: <ordinal rank in window's top-sort, e.g., "3 of top 50">
    - OP flair: <flair text or none>
    - Reddit spoiler tag: <yes | no>   <!-- preserved as evidence for spoiler-classification pass -->
    - Supporting comments:
      - Comment by <author>, rank <ordinal in thread>, flair <flair or none>: <brief summary or paraphrase>
      - <repeat as needed>
  - <additional threads supporting the same finding>
- **Dev-confirmed:** <yes | no>
- **Notes:** <any caveats, conflicting claims, version-dependence, etc.>

### Finding 2: <short title>

<same structure>

<...continue for all findings...>

## Recurring questions

Questions that appeared in multiple threads across multiple windows. These are not findings themselves but signal what the guide must answer. Each entry ingests as a corpus claim via the spoiler-classification sub-agent pass; no default tier.

### Recurring question 1: <question text>

- **Windows seen in:** [all-time, year, month]
- **Thread count:** <N>
- **Representative threads:**
  - <URL> (window, rank, reddit-spoiler-tag: yes/no)
  - <URL> (window, rank, reddit-spoiler-tag: yes/no)
- **Apparent community answer:** <if convergent; otherwise "no convergent answer">

### Recurring question 2: ...

<same structure>

## Threads scanned but not surfaced as findings

Inbox-only appendix -- not ingested into the corpus. Useful for re-runs: records near-misses (high-upvote threads that didn't meet finding criteria, threads that looked promising but turned out to be opinion-only) so a future re-run or doctor invocation avoids re-evaluating the same dead ends.

- <URL>: <one-line reason for exclusion>
- <URL>: <one-line reason for exclusion>
```

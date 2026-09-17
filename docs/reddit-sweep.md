# Reddit sweep (optional module)

> **Status: not currently working as described.** The sweep ran successfully twice, in late
> May 2026, both times against Reddit's anonymous JSON API. That API now returns HTTP 403 to
> unauthenticated clients, so those runs are not reproducible today. Running it now requires
> the MCP server below configured with your own registered Reddit app credentials, which has
> not been exercised end to end. Treat this document as the module's design and its
> prerequisites, not as a feature you can expect to switch on.

This module is deliberately out of the main [README](../README.md): it is an optional,
external-dependency side path, and the rest of the framework is file-based and works without
it. Nothing else depends on it.

The Reddit sweep ([`reddit_sweep.md`](../reddit_sweep.md)) is an optional post-build module that browses a game's subreddit and surfaces community-confirmed findings: undocumented interactions, dev-confirmed bugs, build math, strategies for specific encounters, recurring questions that signal guide gaps.

It runs in its own fresh session, after the research cascade has completed and before stitch, triggered by saying: `hintforge doctor, reddit sweep` inside the game folder. (The `hintforge doctor` anchor is what loads the skill; the `reddit sweep` qualifier selects this module. There is no standalone trigger.)

**External dependency: reddit-mcp-buddy.** The sweep uses the `reddit-mcp-buddy` MCP server. The sweep checks for reachability before crawling and aborts cleanly if the server is not available.

**Rate limits and auth tiers.** Reddit's anonymous JSON API is no longer usable for the sweep -- it returns HTTP 403 to unauthenticated clients -- so reddit-mcp-buddy must be configured with a registered Reddit "script" app before the sweep can run. Create one at reddit.com/prefs/apps and set its client ID/secret in reddit-mcp-buddy for app-only OAuth (60 req/min); add a username/password for the higher authenticated rate (100 req/min). The sweep surfaces the detected tier and estimated wallclock before crawling and asks for confirmation; if no working credential is configured it aborts cleanly rather than crawling.

**Why a separate session.** The sweep's failure modes (MCP unreachability, rate-limit hits, subreddit gone private) are distinct from ingestion's failure modes. Running both in the same session risks one failure contaminating the other's state. The sweep writes its findings file before asking whether to ingest, so a sweep failure after file-write doesn't block ingestion from running against a completed file.

**Output and ingestion gate.** The sweep writes findings to `<game>/research_inbox/module/reddit_sweep.<game>.<ISO-date>1.md` and pauses before ingesting. You can review the file first, ingest immediately, or skip ingestion and ingest later. Every claim from the sweep routes through the same spoiler-classification pass as P1/P2/P3 claims.

**Doctor integration.** Doctor recommends a sweep; it never runs one itself. When a patch, DLC, or a specific gap calls for community findings, doctor tells you to type `hintforge doctor, reddit sweep for the <patch/DLC/gap>` in a fresh session. The sweep always runs in its own session, never chained from the doctor run that recommended it -- that keeps the Reddit-MCP failure surface isolated and the context scoped. See `reddit_sweep.md` for the full procedure and `doctor.md` Branches B and C for when doctor raises the recommendation.

# Hintforge

**An agentic framework for spoiler-controlled, activity-tracking game guides.**

A guide for any game, on any system, where you choose how much help you want and it logs your progress so you can pick up easily even after a long time away. It's a loyal sidekick -- customized to your spoiler preferences and interaction style -- that tags along and helps you out. Markdown + structured-claim convention, OS- and agent-agnostic, consumed by a local AI agent that reads and writes files you control.

> Want to **use** an existing guide rather than build one? Go to [`hintforge-reader`](https://github.com/dtiger1889-ops/hintforge-reader) -- the runtime hint-companion skill that pairs with any Hintforge-format guide.
>
> [Pre-built guides coming soon.]

## Install

Paste this into Claude Code, Codex, or OpenClaw:

> Install the hintforge skill from github.com/dtiger1889-ops/hintforge

Per-runtime details in [`docs/install/`](docs/install/).

## Get started

1. **Install the skill on your AI runtime.** Pick your runtime:
   - [Claude Code](docs/install/claude-code.md)
   - [Codex (CLI + desktop)](docs/install/codex.md)
   - [OpenClaw](docs/install/openclaw.md)
2. **In your runtime,** ask: "build a guide for [GAME]". The wizard walks you through ~10 questions, then scaffolds `~/Documents/Guides/<game>/` with the universal core directories, the vector extensions your game needs, and a `research_brief.txt` ready for a deep-research handoff.
3. **Install the [`hintforge-reader`](https://github.com/dtiger1889-ops/hintforge-reader) skill** to play with the guide once it's built.

**You'll know it's working when** the wizard greets you and starts asking setup questions (game name, persona cast, dial defaults) before touching any files.

> **Model recommendation.** Use a mid-tier model (Sonnet-class or equivalent) with extended thinking off for all builder operations: setup, ingestion, stitch, zipper, doctor, and reddit sweep. The builder's work is structural: reading files, routing facts, writing formatted output. It does not benefit from extended reasoning chains, and top-tier models add cost without improving outcomes. The only exception is the research cascade itself (P1, P2, P3 brief generation), which is the one builder step that benefits from depth, and for which the handoff path to an external deep-research tool is the recommended default anyway. Verify your model and thinking settings in your agent's status line or model picker before starting a session.

---

## Why hintforge exists

Fan-wiki pages dump every spoiler on you the moment you land -- assuming you can see the page through the ads. There's no setting for "I want a hint about *this* puzzle but not the boss fight in two hours."

hintforge inverts that: **information is opt-in.** Want more? Ask. Want less? Lower the tier back down.

**Remembering where you left off can be difficult.** Complex games demand a lot up front: crafting systems, skill trees, gear builds, hotkey layouts you spent an hour customizing. Then life happens. Come back six weeks later and you're staring at a skill tree you don't recognize, a control layout you've half-forgotten, and quest context that's gone cold. The usual workaround is Googling "how do I play X again" and landing on a five-year-old forum post that's slightly wrong for the current patch. hintforge keeps that context alongside your save -- when you tell it you're returning after a break, it reconstructs what you had going without spoiling where the story goes. No plot hints. No boss previews. Just "here's your build, here's what you were doing, and here are the four buttons you always forget."

### "Couldn't I just put a wiki into NotebookLM?"

It is the obvious objection, and answering it is the cleanest way to see what Hintforge is for. NotebookLM is the best-known source-grounded research assistant: you upload documents, it answers from them instead of from open-web training data, and it cites as it goes. Point it at a game wiki and it will happily answer questions about that game.

The catch is that NotebookLM and Hintforge are built toward opposite goals. NotebookLM exists to surface everything in your sources as fast as possible; that is the entire value proposition of a research assistant. Hintforge exists to withhold, to hand you exactly as much as you asked for and not one beat more. Feeding a full game wiki into NotebookLM does not give you a spoiler-safe companion; it gives you a faster way to get spoiled, because the tool has no concept of where you are in the game or what you have not reached yet.

| Dimension | Google NotebookLM | Hintforge |
|---|---|---|
| Design goal | Surface everything in your sources, fast | Withhold by default; reveal only what you request |
| Spoiler control | None; any answer can spoil | Two graduated dials (enemy 0-5, puzzle 0-3) plus a request-based hint ladder |
| Progress awareness | Stateless; no concept of where you are in the game | Tracks your position, open threads, and build; reconstructs context after a break |
| Conflicting sources | Answers over raw uploads; contradictions surface unresolved | Ingestion, stitch, and zipper reconcile conflicts; every claim is source-weighted with confidence metadata |
| Voice and character | Custom personas and selectable host voices and tones | Game-themed persona bound by the spoiler rules; it flavors how an answer is delivered, never what gets revealed |
| What you own | A notebook locked inside your Google account | Plain markdown files you own, fork, edit, and merge |
| Where it runs | Google web and mobile only | Claude Code, Codex, OpenClaw; an OS- and agent-agnostic markdown core |
| Cost model | Tied to a Google AI subscription; usage-limited tiers, cannot be bought standalone | Runs on your own LLM tokens; the framework itself is free under CC BY-NC-SA |
| Privacy | Closed cloud product | Local files you control; no telemetry, no daemons, inspectable in plain language |
| Shareability | A notebook is not a mergeable community format | Corpus is designed to be shared and merged into consensus guides (roadmap) |

To be fair to it, NotebookLM is genuinely better at some things: polished multimedia output, a large context window, a clean mobile app, and zero setup. If your goal is to study a document you have already finished, it is excellent. If your goal is to play a game you have not finished without being told how it ends, the design is working against you. That gap is the reason Hintforge exists.

It's also designed as a framework for **multi-contributor truth aggregation** -- players' agents push observations to a shared repo, an aggregator merges them into percentage-based truth, and a static HTML wiki gets generated. Not there yet, but guides created with this framework are meant to be not only shareable but mergeable.

---

## What hintforge does -- today and planned

**Working today** (verified on Windows 11 + Claude Desktop and Claude Code, Pro/Max tier):

- Two-dial, user-controlled assistance: enemy tier 0-5 + puzzle tier 0-3, set at setup, changeable any time.
- Spoiler-free defaults with a request-based hint ladder (Lvl 1 nudge -> Lvl 2 -> Lvl 3 step-by-step).
- Persona-flavored delivery -- a game-themed voice layer that flavors *how* information is delivered, never *what*.
- Structured-claim citation format -- every fact carries source, contributor, confidence, last-verified, and tier metadata. Plain markdown, parseable by any markdown-aware agent and by a future aggregator.
- Ships as a [SKILL.md-spec](.agents/skills/hintforge/SKILL.md) agent skill, consumable by Claude Code, Codex CLI, and OpenClaw. Per-runtime install paths in [`docs/install/`](docs/install/). The markdown core is OS- and agent-agnostic; runtime-specific add-ons are quarantined.
- One-paste setup wizard with optional pre-fill (`setup_answers.txt`) -- answer in a text file ahead of time for the cheapest possible setup, or leave it blank and the wizard asks you live.
- Three opt-in capability modules:
  - **PTT** (push-to-talk) -- hold a hotkey to talk to the agent via local Whisper transcription.
  - **TTS** (read-aloud) -- Stop hook speaks each agent reply through your speakers in a persona-aware voice.
  - **save-watcher** -- reads the game's save file at session start to populate location / inventory / state into the agent's context.
- Transparent file-scope design -- the framework instructs the agent to confine writes to the framework folder and the per-game folder; no telemetry, no daemons, no privilege elevation, no auto-commits.
- Token-heavy operations (research, content sweeps) are opt-in and flagged before they run; the default is "ask as questions arise" rather than batching research up front. Deep-research handoff works with Claude's built-in Research, Gemini Deep Research, ChatGPT Deep Research, or Perplexity -- the wizard writes a brief to `<game>/research_brief.txt`, you run it in whichever tool, drop the result into `<game>/research_inbox/`, and a fresh session ingests it.
- Stale-session detection -- when a fresh session opens on a guide last played >30 days ago, the bot offers a controls + open-thread refresher before resuming. Default threshold 30 days, configurable; safe default is "yes refresh" if the user gives no answer.

**Roadmap:**

- Multi-contributor aggregator with percentage-based truth -- multiple players' agents push observations to a per-game repo; the aggregator weighs claims by source quality and contributor track record and emits a canonical guide. See [`distribution.md`](distribution.md) for the full vision.
- Static HTML wiki generator with reader-side tier filters -- replaces fan-wiki sites with consensus-merged, spoiler-controlled output.
- Pluggable persona library + cross-platform TTS (macOS `say`, Linux `piper`).
- Screenshot-by-command (`/screenshot` slash command + vision-model interpretation of the focused window).
- Mobile / hands-free voice loop -- extend PTT/TTS so a player can walk around with phone + headphones and talk to the guide.
- Offline + local-LLM mode with periodic deep-research drip-feed from generous online free tiers.
- Mod awareness & suggestions -- optional, token-heavy add-in. Recommends mods by category (QOL, cosmetic, add-ins); surfaces community picks on demand; contextually checks for QOL mods when a player flags something in the game as annoying. Complete-overhaul mods are out of scope (they make the guide itself obsolete).
- Steam integration (opt-in, privacy-first) -- supply your own Steam Web API key to mine your owned-games + playtime + achievement history into a personal playstyle profile, ground recommendations in what you actually play, and track achievement progress alongside the active guide. Key stays on your machine; no third-party server, no telemetry, no account linkage beyond the calls you authorize. Read-only against the public Steam Web API; off by default.

---

## How the tiers work

Two independent dials. Set at setup, changed any time by saying "set my puzzle tier to 2" or similar.

### Enemy help tier (0-5)

| Tier | What you'll see |
|---|---|
| **0** | No warnings before fights. Surprises stay surprises. |
| **1** | Mob types named in route hints. Bosses still hidden. |
| **2** | Boss-fight existence flagged. No boss details. |
| **3** | Boss generically named + loadout suggestions. |
| **4** | + Crafting materials to stock before the fight. |
| **5** | Full move-by-move boss strategy. |

### Puzzle help tier (0-3)

| Tier | What you'll see |
|---|---|
| **0** | Silent until you ask. |
| **1** | On entry, the agent names the *kind* of puzzle. Doesn't volunteer hints. |
| **2** | + Automatic Lvl-1 nudge on entry. |
| **3** | + Automatic full step-by-step on entry. |

Independent of tiers, you can always escalate a specific puzzle by asking: "Lvl 1 hint please" -> "Lvl 2" -> "Lvl 3 step-by-step." That's a one-off, not a tier change.

---

## The builder/reader split

Hintforge ships as two separate skills in two separate repos.

**This repo (hintforge) is the builder.** It handles everything involved in creating and maintaining a guide: the setup wizard, the research cascade, ingestion of results into the corpus, stitch-and-zipper cross-referencing, doctor corpus maintenance, and the reddit sweep optional module. You run the builder when you are building or updating a guide, not when you are playing.

**The reader (hintforge-reader) is a separate repo and a separate skill.** It is the session-time companion: it reads the corpus you built, enforces your spoiler dials, tracks your position, and fires point-of-no-return warnings. You install it once and open it when you sit down to play.

The split matters for a few reasons. Each skill can be installed independently and updated on its own cadence. A reader update does not require a builder rebuild. A corpus-format change (tracked by `corpus-core-version` in `architecture.md`) is the only event that requires coordination across both, and even then the reader will warn rather than hard-stop on a mismatch.

### How to confirm the builder skill triggered

When you open a session in a folder where the skill is installed, your agent loads it on startup. You can verify it loaded by asking "what are your active framework rules" or "what skill is running" at the start of any session. The agent should describe hintforge's scope constraints, spoiler-discipline rules, and file-scope limits. If it cannot, the session is running without the skill, and any work done in that session will not follow framework conventions.

If the skill did not trigger, check that you opened the session inside the hintforge repo or a game folder that has the skill installed. See [`docs/install/`](docs/install/) for per-runtime install and troubleshooting.

### How to confirm the reader skill triggered

The same check applies. Open a session inside your game guide folder and ask "what skill is running." The reader skill should be installed per the reader's install instructions. See the [hintforge-reader repo](https://github.com/dtiger1889-ops/hintforge-reader) for install details.

## Deep-research handoff

The research cascade (P1, P2, P3) is the most token-intensive part of building a guide. P1 alone for a large open-world game can run to tens of thousands of tokens if handled locally. The recommended default is to hand this off to an external deep-research tool and bring the result back in.

Supported handoff targets: Claude's built-in Research mode, Gemini Deep Research, ChatGPT Deep Research, Perplexity. Any tool that accepts a structured brief and returns a detailed result file works.

**Why this is the recommended path:** External deep-research tools are optimized for broad multi-source synthesis. Running P1, P2, and P3 inside a local agent session using a top-tier model is significantly more expensive for equivalent or worse coverage. Use the handoff path. Use a mid-tier model (Sonnet-class) locally for everything except the research itself.

**Round-trip:**
1. The setup wizard generates a research brief and writes it to `<game>/research_brief.txt`.
2. You paste the brief into your external deep-research tool of choice.
3. Save the result file into `<game>/research_inbox/p1/` (or p2, p3 as appropriate).
4. In a fresh session inside the game folder, say: `ingest the research`.
5. The agent (running Sonnet-class, thinking off) distributes facts from the result file into the corpus with source tags, spoiler classification, and structured-claim metadata.

The ingestion step is handled by `ingestion.md`. It runs best on a mid-tier model with extended thinking off: the work is structural routing, not reasoning.

## Research phases: P1, P2, P3

Building a guide for a new game runs through three research phases. The setup wizard scaffolds all three briefs; you run them in order, with ingestion between each.

**P1 -- Foundation.** Zone map, chapter structure, achievement list, one-way transitions, game-version manifest, DLC flags. P1 produces the skeleton the rest of the corpus hangs from. The P1 brief is generated by the setup wizard and is the file you hand to your deep-research tool first.

**P2 -- Per-zone detail.** Gate lists, navigation topology, locks-and-keys table, collectible locations, missable flags per zone. P2 is scoped to what the reader needs to navigate the game without spoilers: can I go here, what will I miss if I do, what do I need before I go.

**P3 -- Gap fill and validation.** Resolves P1/P2 disputes, fills coverage gaps surfaced during ingestion, and integrates DLC content that was not part of the base-game briefs. P3 is also where multi-source conflicts (two wikis giving different values for the same stat) get a resolution call and a source weight.

After each phase, run ingestion in a fresh session: say `ingest the research` with the result file present in `research_inbox/`. Each ingestion pass is independent. A failed or partial P2 ingestion does not invalidate P1.

**Model for ingestion: Sonnet-class, extended thinking off.** Ingestion is the most context-heavy local session you will run. A top-tier model adds cost without improving file routing or spoiler classification. Confirm your model before triggering ingestion.

The setup wizard (`setup_wizard.md`) manages brief generation for all three phases and tracks which phases have completed via `CHECKPOINT.md`. Refer to `ingestion.md` for the full ingestion procedure.

## Reddit sweep (optional)

The reddit sweep (`reddit_sweep.md`) is an optional post-build module that browses a game's subreddit and surfaces community-confirmed findings: undocumented interactions, dev-confirmed bugs, build math, strategies for specific encounters, recurring questions that signal guide gaps.

It runs in its own fresh session, after the research cascade has completed and before stitch, triggered by saying: `hintforge doctor, reddit sweep` inside the game folder. (The `hintforge doctor` anchor is what loads the skill; the `reddit sweep` qualifier selects this module. There is no standalone trigger.)

**External dependency: reddit-mcp-buddy.** The sweep uses the `reddit-mcp-buddy` MCP server. The sweep checks for reachability before crawling and aborts cleanly if the server is not available.

**Rate limits and auth tiers.** The sweep paces itself against the configured Reddit auth tier: anonymous (10 req/min), app-only (60 req/min), authenticated (100 req/min). Anonymous is the default and works without credentials. If you want faster sweeps, configure an app-only or authenticated credential in reddit-mcp-buddy. The sweep surfaces the detected tier and estimated wallclock before crawling and asks for confirmation.

**Why a separate session.** The sweep's failure modes (MCP unreachability, rate-limit hits, subreddit gone private) are distinct from ingestion's failure modes. Running both in the same session risks one failure contaminating the other's state. The sweep writes its findings file before asking whether to ingest, so a sweep failure after file-write doesn't block ingestion from running against a completed file.

**Output and ingestion gate.** The sweep writes findings to `<game>/research_inbox/module/reddit_sweep.<game>.<ISO-date>1.md` and pauses before ingesting. You can review the file first, ingest immediately, or skip ingestion and ingest later. Every claim from the sweep routes through the same spoiler-classification pass as P1/P2/P3 claims.

**Doctor integration.** Doctor (see below) can invoke the reddit sweep with a scope-query parameter for targeted top-ups: post-patch, post-DLC, or gap-fill sweeps. See `reddit_sweep.md` for the full procedure and `doctor.md` for how doctor passes the scope-query.

## Corpus integrity: why discrepancies happen and how to fix them

Research across multiple sources run at different times by a model that is probabilistic by nature will produce discrepancies. Two wikis give different cooldown values for the same ability. A P2 zone file names a weapon by a slightly different name than the P1 achievement file. A stat from a P3 sweep contradicts a claim ingested in P1 without either being obviously wrong. This is expected, not a sign something went wrong.

The framework's response to this is structural, not instructional. Three tools exist specifically to find and resolve cross-file inconsistencies:

**Stitch** (`stitch_and_zipper.md`) weaves confirmed facts across files. When the same entity (a weapon, a zone, a mechanic) appears in multiple corpus files, stitch checks that the claims are consistent: same name, same stats, same tier tag. Discrepancies get flagged for resolution rather than silently propagated. Run stitch after major ingestion passes or when you suspect a naming inconsistency is causing the reader to return incomplete results. Trigger: `run stitch` in a fresh session inside the game folder.

**Zipper** (`stitch_and_zipper.md`) reconciles branching structures: player-choice paths, multiple endings, content that differs based on decisions made earlier in the game. Where stitch handles flat fact consistency, zipper handles conditional consistency. A claim that is true on path A and false on path B needs to be tagged for both, not just whichever path the researcher happened to follow. Trigger: `run zipper` in a fresh session inside the game folder.

**Doctor** (`doctor.md`) is the corpus maintenance tool for everything else. It diagnoses stale claims after a patch, flags version-locked content after a DLC, repairs coverage gaps, and handles corpus-format migrations when the builder framework updates. Doctor is the tool you reach for when something in the guide is probably wrong but you are not sure where. Trigger: `hintforge doctor` in a fresh session inside the game folder. See the "Maintaining your guide" section below for the full list of doctor use cases.

These three tools exist because the principles in `principles.md` require that every claim carry structured metadata (source, confidence, last-verified, tier) and that the corpus not contradict itself silently. Stitch and zipper enforce the non-contradiction requirement actively rather than relying on ingestion discipline alone. Doctor enforces temporal correctness: a claim that was accurate at the time of ingestion may not be accurate after a patch.

**Model for stitch, zipper, and doctor: Sonnet-class, extended thinking off.** All three are structural operations: read files, compare values, flag or resolve conflicts. None of them benefit from extended reasoning. Confirm your model before running any of them.

---

## Principles -- what shapes the framework

Load-bearing rules summarized. Full set (16 principles + rationale) in the [reader skill's `principles.md`](https://github.com/dtiger1889-ops/hintforge-reader/blob/main/.agents/skills/hintforge-reader/principles.md).

**User-controlled assistance is the backbone, not a feature.** The two tiers are first-class state, not a setting hidden in a config screen. Every other rule (spoiler discipline, the hint ladder, persona constraints) only makes sense in service of reader agency over information flow. Inverting the fan-wiki "spoil-everything-by-default" model is what hintforge exists to do.

**Spoiler-free defaults + a request-based hint ladder.** Until the reader raises a tier, the guide names puzzle types only when the reader is staring at one, names enemies only post-encounter, and never reveals story beats or boss existence. When the reader asks for help, the agent delivers the smallest possible nudge first (Lvl 1) and escalates only on request. The reader's curiosity ceiling is the only one that escalates.

**Every claim cites a source, in a structured form.** Sources have weight: live in-game observation > known-good wiki > YouTube comment > Reddit thread > vibes. Every fact links back to where it came from, and the metadata (source, contributor, confidence, last-verified, tier) is structured even when the prose reads naturally. This is load-bearing for the future aggregator -- claims born structured beat claims retrofitted later, because once the framework has thousands of claims across games, retrofitting metadata is a nightmare.

**Median preferences + harm reduction.** Defaults serve the most common player; opt-ins and tier controls protect the minority who want a different experience. Defaults never degrade to accommodate an edge case -- gate the edge case instead. This is the *why* behind the spoiler-free defaults: the median reader wants to be surprised by the game, and the minority who want maximum guidance can lift the floor without imposing it on anyone else. When two reader populations are in tension, the resolution is always the same shape: pick the default that serves the larger group, then build an opt-in for the other.

**Transparent operations -- no sneaking.** The non-technical user who pastes a setup command into their AI bot must be able to trust the framework. That trust comes from two layers:

What the framework code itself contains (verifiable by reading the repo):
- No hidden dependencies installed by setup scripts.
- No background processes, daemons, or "phone home" behavior.
- No privilege elevation -- no UAC, no `sudo`, no admin rights. Everything in user-writable space.
- No silent auto-commit / auto-push baked into any script. Git is only used at explicit request.

What the framework instructs the agent to do (relies on the agent following the rules in the [framework definition](CLAUDE.md)):
- Confine filesystem changes to the declared scope (`~/Documents/hintforge/` and the per-game folder it creates).
- Announce web fetches before running them.
- Announce file-touching actions before doing them.

The reader is non-technical and trusts the framework by trusting the link they were sent. The framework earns that trust by being inspectable in plain language. Easter-egg flavor text is fine; covert behavior is not.

**Token-aware execution.** Token-heavy operations (game research, content sweeps, multi-source fetching) are opt-in and flagged before they run. The primary users are paid AI-bot subscribers on capped plans -- if setup auto-launches a research burst on day one, the reader hits their cap before getting any guide value. Research and guide-use are separable so the reader can budget across both. The setup wizard is lightweight by default; heavy optional steps (save-watcher, read-aloud / TTS, batch research) default to skipped on Pro tier.

**OS-portable + bot-portable by design.** The markdown core (templates, principles, claim format, tier logic) is portable anywhere. What's locked to a specific environment is quarantined: TTS hook (Windows SAPI), default file paths (Windows-flavored), PowerShell snippets in some scripts, and Claude-Code-specific hook configs in the optional modules. A non-Windows reader, or a non-Claude AI bot, can consume the markdown layer directly; OS-specific add-ons need contributor adaptation. The minimum capability bar for a useful agent: read markdown, write markdown, fetch URLs, run a script, take user input across multiple turns. See the [reader skill's `os_compatibility.md`](https://github.com/dtiger1889-ops/hintforge-reader/blob/main/.agents/skills/hintforge-reader/os_compatibility.md) for the player-facing compatibility disclosure, or [`os_compatibility.md`](os_compatibility.md) here for the full portability matrix and porting roadmap.

---

## Status & compatibility

Verified-running on Windows 11 + Claude Desktop / Claude Code, Pro/Max tier. The markdown core is OS- and agent-agnostic; Windows-specific add-ons (TTS hook, save-game default paths, PowerShell snippets) need adaptation for Mac / Linux. Cowork and browser claude.ai are not the right runtimes for building or maintaining a guide -- both lack the local-file persistence the framework relies on.

Full portability matrix in [`os_compatibility.md`](os_compatibility.md). Per-runtime install caveats (Claude Code hooks, Cowork session-scoping, browser claude.ai) live with the install docs at [`docs/install/`](docs/install/). The player-facing OS-compatibility view ships with the reader at the [reader skill's `os_compatibility.md`](https://github.com/dtiger1889-ops/hintforge-reader/blob/main/.agents/skills/hintforge-reader/os_compatibility.md).

---

## Folder map

This repo is the **builder** skill (authoring side). The runtime **reader** skill is a sibling repo at [`hintforge-reader`](https://github.com/dtiger1889-ops/hintforge-reader).

| File | Purpose |
|---|---|
| [`.agents/skills/hintforge/SKILL.md`](.agents/skills/hintforge/SKILL.md) | The skill manifest -- conventional path discovered by Claude Code, Codex CLI, and OpenClaw |
| [`AGENTS.md`](AGENTS.md) | Repo-level agent pointer (cross-runtime convention) |
| [`CLAUDE.md`](CLAUDE.md) | Framework definition + hard rules (the file your AI agent reads on startup) |
| [`CONTEXT.md`](CONTEXT.md) | Glossary of Hintforge domain terms (corpus, vector extension, stitch, zipper, etc.) |
| [`setup_wizard.md`](setup_wizard.md) | First-run prompt-flow spec -- the wizard your AI walks you through |
| [`instantiation.md`](instantiation.md) | Manual setup flow (for advanced users who want to skip the wizard) |
| [`ingestion.md`](ingestion.md) | Research-ingestion procedure (populates corpus files from `research_inbox/`) |
| [`stitch_and_zipper.md`](stitch_and_zipper.md) | Post-ingestion synthesis -- cross-system edges + overlap reconciliation |
| [`reddit_sweep.md`](reddit_sweep.md) | Optional module for community-knowledge harvest via reddit-mcp-buddy MCP server |
| [`doctor.md`](doctor.md) | Post-instantiation maintenance: format bumps, game updates, targeted repair (triggered by "doctor hintforge") |
| [`os_compatibility.md`](os_compatibility.md) | Maintainer-facing portability matrix + porting roadmap |
| [`distribution.md`](distribution.md) | GitHub + aggregator + wiki-gen long-term vision |
| [`docs/corpus-format.md`](docs/corpus-format.md) | The on-disk corpus format contract (the builder produces it; the reader consumes it) |
| [`docs/install/`](docs/install/) | Per-runtime install instructions (Claude Code, Codex, OpenClaw) |
| [`templates/`](templates/) | Skeletons the wizard copies + fills when you instantiate a new game (includes `ptt/`, `tts/`, `save_watcher/` optional modules) |
| [`OPEN ME if new to AI - How to prompt claude code.txt`](./OPEN%20ME%20if%20new%20to%20AI%20-%20How%20to%20prompt%20claude%20code.txt) | Plain-text onboarding for users who got a ZIP-share instead of cloning |

---

## Maintaining your guide

A guide built from the research cascade reflects the game as it existed at research time. Games patch. DLC ships. The reader framework updates. This section describes the ongoing use cases for `doctor.md` and how to handle each.

**Model for all maintenance operations: Sonnet-class, extended thinking off.** Doctor, stitch, zipper, and ingestion are all structural. Confirm your model before starting.

### After a game patch

Patches can change stat values, fix or break mechanics, alter drop rates, or rename items. Claims in the corpus that reference patched content become stale without any visible signal. Doctor's Branch B handles this:

Trigger: `hintforge doctor` in a fresh session inside the game folder, then tell it a patch shipped and give it the patch notes or patch version. Doctor reads `architecture.md` for the current game-version manifest, flags claims that reference content the patch notes touch, and produces a repair plan before changing anything. You confirm the plan before repairs run.

If the patch is large, doctor may invoke the reddit sweep with a scope-query to pull post-patch community findings. That sweep runs in its own subsequent session.

### After a DLC ships

DLC adds zones, mechanics, characters, and achievements that don't exist in the base corpus. Doctor's Branch B handles DLC as a game-update variant:

Trigger: `hintforge doctor`, tell it the DLC name. Doctor flags what's missing (no zone files for DLC zones, achievement list incomplete, architecture.md missing DLC entries) and produces a scaffold plan. After scaffolding, you run the DLC research cascade (P1 brief scoped to DLC content, P2 if needed) through the same handoff path and ingest the results.

DLC zone IDs follow the same prefix convention as base-game zones. DLC achievements are added to the existing achievements file, not a separate file. Doctor handles both.

### Filling coverage gaps

When the reader returns "I don't have reliable data on that" for something that should be in the corpus, it usually means a gap in P2 coverage, a stitch failure that left a claim unresolved, or a P3 dispute that landed as unresolved rather than settled. Doctor's Branch C handles targeted repair:

Trigger: `hintforge doctor`, describe the gap ("the reader can't answer questions about the second boss's loot table"). Doctor reads the relevant corpus files, diagnoses whether the gap is a missing claim, a broken cross-reference, or an unresolved dispute, and either repairs it directly or generates a targeted research brief for a narrow handoff sweep.

Small gaps can often be filled without a full deep-research handoff: tell doctor what you know and it will write the claim directly with appropriate source metadata and confidence flags.

### After a reader (hintforge-reader) update

Reader updates occasionally change how the corpus is interpreted: new dial behavior, new warning tiers, updated persona rules. These changes do not invalidate the corpus unless the `corpus-core-version` increments.

`corpus-core-version` is a single integer in `architecture.md`. The reader declares `MIN_SUPPORTED_CORE` and `MAX_SUPPORTED_CORE`. If your corpus version falls outside the reader's supported range, the reader will warn you at session start and describe what changed. It will not hard-stop; it will proceed and behave as well as it can under the mismatch.

To bring a corpus up to a new version, run `hintforge doctor` and tell it the corpus format migrated to version N. Doctor reads the migration notes for that version bump and applies the required structural changes. Migration notes for each version increment are in `CHANGELOG.md`.

Reader-only updates (persona changes, dial behavior changes, warning-tier changes) that do not bump `corpus-core-version` require no corpus action. Update the reader skill and resume play.

### Periodic check-ins

Even without a patch or DLC, a corpus built from a snapshot of web sources drifts over time as wikis correct errors and community knowledge accumulates. There is no required maintenance cadence. Each time you run `hintforge doctor` for any reason, it opens by reading the manifest and asking whether anything in the game has changed since the corpus was last reconciled -- a patch, a DLC, anything noticed in play. Your answer routes to a targeted patch (Branch B or C) or a manifest-date bump with no content edits. This makes each doctor invocation a natural check-in point, whether triggered by a reader complaint, a known patch, or a periodic review.

---

## Contributing

A full `CONTRIBUTING.md` lands alongside the multi-contributor aggregator -- see [`CONTRIBUTING.md`](CONTRIBUTING.md) for the current stub (license inheritance + pointer back here). For now:

- Found a missing template field, an OS that doesn't work for you, or a content-discipline gap? Open an issue.
- PRs welcome -- the framework's hard rules (in the [framework definition](CLAUDE.md) and the [reader skill's `principles.md`](https://github.com/dtiger1889-ops/hintforge-reader/blob/main/.agents/skills/hintforge-reader/principles.md)) are the bar. Anything that violates spoiler discipline, transparent operations, or token-aware execution is a regression.

---

## License

Licensed under [CC BY-NC-SA 4.0](LICENSE). Free for personal, non-commercial, and creator use -- share, remix, and adapt with attribution; derivatives must use the same license.

Commercial licensing available on request -- see [`LICENSE`](LICENSE) for contact details.

# hintforge -- Game-Guide Framework
<!-- v67 -- 2026-06-08 -->

Framework + templates for spoiler-controlled, persona-flavored, GitHub-distributable game guides. Per-game guides instantiated from these templates live in **`../Guides/<game>/`** (a sibling `Guides/` folder next to `hintforge/`), not inside this folder. hintforge contains only the framework -- no project state, no dev artifacts.

## Long-term vision (drives template design today)
- Each game's guide → its own **GitHub repo**, multi-contributor.
- Aggregator agent merges commits into **percentage-based truth**; static HTML wikis generated off the canonical repo replace fan-wiki sites.

## Folder map
- `principles.md` -- 16 universal rules; #1 is user-controlled assistance levels (the backbone)
- `templates/architecture.md` -- zone graph + chapter-zone mapping + optional content + support topology + locks-and-keys scaffold
- `templates/nav_index.md` -- per-game `nav/index.md` scaffold (universal nav discipline: no left/right, save-point flagging, 3-tip entry format)
- `templates/nav_zone.md` -- per-zone gate-list scaffold (entry, exit, sequential gates, optional branches, common confusions)
- `templates/localization.md` -- landmark→zone resolution + ask-the-player prompts (required for `landmark` / `hybrid` localization classes)
- `instantiation.md` -- manual step-by-step for spinning up a new game guide; includes regeneration-discipline rule (what survives a wipe-and-regen)
- `setup_wizard.md` -- first-run prompt-flow spec for an AI-bot-driven setup
- `ingestion.md` -- research-cascade result integration; runs in a fresh session triggered by "ingest the research"
- `stitch_and_zipper.md` -- post-ingestion synthesis pass (cross-system edge detection + redundancy reconciliation)
- `doctor.md` -- post-instantiation maintenance; runs in a fresh session triggered by "doctor hintforge" (aliases: "doctor my guide", "doctor the corpus"). Avoid bare "run the doctor" -- collides with Claude Code's `/doctor` CLI command.
- `templates/dependencies.md` -- cross-system dependency table (stitch output; created at game-folder root on first stitch run)
- `os_compatibility.md` -- verified-running setup, OS+bot portability roadmap
- `distribution.md` -- GitHub-first publishing + aggregator + wiki-gen vision
- `templates/` -- copy these into a new game folder and fill in placeholders

## When this folder is opened in a new session

If the user's first message asks to **build / make / create / set up a guide** for a game (any phrasing -- "build me a guide for X", "make me a guide for X", "I want to play X with this framework", "make hintforge work for X", "start a new guide", "set up X", "add game X"), the **first action** is to read `setup_wizard.md` end-to-end and run that wizard from Step -1. Do not infer answers, do not scaffold files, do not write personas, do not skip Step 8. The wizard's Hard rule (every step DONE / DONE-VIA-PREFILL / ASKED ABOUT) is binding.

If `../Guides/<game>/` already exists with content from a prior wizard run, the wizard's already been run -- answer the user's actual question directly using the guide's contents. The wizard runs once per (user, game) pair.

## Hard rules (apply to every guide built with this framework)
- **User chooses assistance level.** Two tiers (enemy 0-5, puzzle 0-3) set at setup, changeable any time. Backbone, not feature.
- **Spoiler-free by default.** Until tier raised, no story / boss / encounter info.
- **Hint ladder is request-based**, not auto-delivered. Smallest nudge first.
- **Every claim cites a source** in structured form (`templates/claim_format.md`).
- **Persona is voice-only**, never affects content discipline.
- **Transparent operations.** No hidden dependencies, no out-of-scope file writes, no background processes, no privilege elevation, no silent network activity. A non-tech user must be able to trust pasted commands.
- **Token-aware execution.** Heavy ops (research, content sweeps) are opt-in with cost estimates. Setup never auto-runs research.
- **OS-portable, bot-portable, environment-aware** -- markdown core works anywhere, but session-scoped envs (Cowork, claude.ai web) get an explicit user confirm before setup writes files. Target env: Claude Code Desktop / Claude Code, where files persist locally.

> Verified-running setup: Windows 11 + Claude Code. See `os_compatibility.md` for the OS+bot portability roadmap.

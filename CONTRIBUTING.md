# Contributing

This is a stub. A full `CONTRIBUTING.md` lands with the multi-contributor aggregator design (merge model, claim-format conventions, CI checks).

For now, see [`README.md`](README.md) for issue/PR norms.

## Platform-agnostic load-bearing files

Load-bearing content — rules, triggers, version stamps, format contracts — must not live uniquely in a platform-specific file (`CLAUDE.md`, `AGENTS.md`, `.claude/`). Those files are shims that catch one tool's auto-load and redirect to the neutral core; they carry zero unique authority. New behavior lands in a neutral file (`SKILL.md`, a procedure `.md`, `docs/`) that ships on every platform. A shim is at most a pointer to those homes.

The rationale: hintforge advertises bot-portability. A load-bearing file under a Claude-only name quietly breaks that promise — a Codex or OpenClaw user never gets that content auto-loaded. Keeping shims as thin pointers removes the asymmetry and eliminates silent drift between platforms.

## Issue routing

This is the **builder** repo. Open issues here for:

- Setup wizard behavior, research-brief generation
- Ingestion, stitch, zipper procedures
- Corpus format spec (`docs/corpus-format.md`) questions or ambiguities
- Templates (universal core, vector extensions, persona cast scaffolding)
- Domain vocabulary (`CONTEXT.md`) gaps or wording

Open issues at [`hintforge-reader`](https://github.com/hintforge/reader) for:

- Dial behavior (graduated spoilers, escalation)
- Runtime rules (lookahead, backtrack, reachability, locks-and-keys notifications)
- Persona discipline (player-pull rule, honest-ambiguity rule, file-first rule)
- Vector-extension discovery, corpus-core-version mismatch warnings
- Reader-side install / discovery problems on a specific runtime

**Edge case.** A bug that looked like a corpus-format spec ambiguity but turns out to be a reader-side runtime rule should land in `hintforge-reader` instead. Move the issue across repos rather than re-filing -- triage labels and cross-repo references work fine.

Game-specific guide content lives in the corresponding guide repo (e.g. `hintforge-<game-name>`), not here.

## License inheritance

Contributions to this repository are licensed under [CC BY-NC-SA 4.0](LICENSE) -- matching the project license -- unless explicitly noted otherwise in the PR.

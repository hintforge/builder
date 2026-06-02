# Contributing

This is a stub. A full `CONTRIBUTING.md` lands with the multi-contributor aggregator design (merge model, claim-format conventions, CI checks).

For now, see [`README.md`](README.md) for issue/PR norms.

## Issue routing

This is the **builder** repo. Open issues here for:

- Setup wizard behavior, research-brief generation
- Ingestion, stitch, zipper procedures
- Corpus format spec (`docs/corpus-format.md`) questions or ambiguities
- Templates (universal core, vector extensions, persona cast scaffolding)
- Domain vocabulary (`CONTEXT.md`) gaps or wording

Open issues at [`hintforge-reader`](https://github.com/dtiger1889-ops/hintforge-reader) for:

- Dial behavior (graduated spoilers, escalation)
- Runtime rules (lookahead, backtrack, reachability, locks-and-keys notifications)
- Persona discipline (player-pull rule, honest-ambiguity rule, file-first rule)
- Vector-extension discovery, corpus-core-version mismatch warnings
- Reader-side install / discovery problems on a specific runtime

**Edge case.** A bug that looked like a corpus-format spec ambiguity but turns out to be a reader-side runtime rule should land in `hintforge-reader` instead. Move the issue across repos rather than re-filing -- triage labels and cross-repo references work fine.

Game-specific guide content lives in the corresponding guide repo (e.g. `hintforge-<game-name>`), not here.

## License inheritance

Contributions to this repository are licensed under [CC BY-NC-SA 4.0](LICENSE) -- matching the project license -- unless explicitly noted otherwise in the PR.

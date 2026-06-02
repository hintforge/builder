# Localization toolkit -- [GAME NAME]

**status:** scaffold <!-- scaffold | research-integrated | live-observed | reconciled -->
**last_reconciled:** YYYY-MM-DD
**research_run:** none

The persona reads this file when CHECKPOINT.md's `player_position.confidence < high`. It tells the persona how to ask the player where they are, and how to map their answer to a `current_zone` in `architecture.md`.

For `landmark` and `hybrid` localization-mechanism classes only. Skip for `map-system` and `none`-class games.

## Landmark → zone resolution

| Landmark / feature | Resolves to zone-id | Notes |
|---|---|---|
| [distinctive in-game feature -- statue, signage, equipment, environmental hazard, named save-point] | [zone-id from architecture.md] | [disambiguate if a similar landmark exists in another zone] |

## Ask-the-player prompts

When `confidence < high` and the player asks a nav-class question, ask one of these before answering. Pick the prompt that fits what the player has volunteered.

- [game-specific prompt -- e.g. "What's the last big landmark you remember? A <example type>, a <example type>?"]
- [game-specific prompt -- e.g. "Which <save-point term> did you last use?"]
- [fallback: "Roughly which area or chapter are you in? If you're not sure, what was the last cutscene or named room?"]

Match the player's response against the table above to resolve `current_zone`. If multiple landmarks could match, ask one disambiguating follow-up -- don't guess.

## Map-element prompts (`hybrid` games only)

For zones that carry an in-game map:

- [game-specific map prompt -- e.g. "What region does your map show?"]
- [game-specific map prompt -- e.g. "Any active quest markers, and where?"]

Skip this section for `landmark`-only games.

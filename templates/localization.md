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

- [game-specific prompt -- e.g. "What's the last big landmark you remember? A <example type>, a <example type>?"] (tier: [none | progression | late-game | story])
- [game-specific prompt -- e.g. "Which <save-point term> did you last use?"] (tier: [none | progression | late-game | story])
- [fallback: "Roughly which area or chapter are you in? If you're not sure, what was the last cutscene or named room?"] (tier: none)

**Every prompt carries a tier**, in the `spoiler:` vocabulary (`none | progression | late-game | story | dlc:<name>`): the strictest tier of any zone, landmark or term the prompt NAMES. A prompt that names a later zone is written at that zone's tier (a prompt asking about a late zone's landmark is a late-game prompt), and the persona asks only the prompts whose tier the player's dials already cover. The prompt is spoken in chat, so naming the zone is the leak.

Match the player's response against the table above to resolve `current_zone`. If multiple landmarks could match, ask one disambiguating follow-up -- don't guess.

## Map-element prompts (`hybrid` games only)

For zones that carry an in-game map:

- [game-specific map prompt -- e.g. "What region does your map show?"]
- [game-specific map prompt -- e.g. "Any active quest markers, and where?"]

Skip this section for `landmark`-only games.

# Warning / hint tiers ([GAME NAME])

Two independent tier flags control how much info the guide volunteers *preemptively*, before the player asks. Higher tiers include everything from lower. Each set independently.

## the player's current settings

- **Enemies: Tier [N]** -- set [DATE]
- **Puzzles: Tier [N]** -- set [DATE]

To change: "set enemy warning to tier N" / "set puzzle tier to N." Update this section with the date.

---

# Enemy tiers (0-5)

### Tier 0 -- No warning
- No mention of enemies before encounter.
- No "watch out for X". Any line naming the enemy types in a place or on a route is tier 1, even for an early, common enemy, and even when the name is a map label or mission title the game shows. A line saying only that enemies are there is tier 1 too.
- Boss existence hidden. No boss prep.
- Permitted: post-encounter help on request.

### Tier 1 -- Mobs only
- Regular enemy types named in route hints when relevant.
- Boss existence still hidden.
- Boss-drop loot may be referenced obliquely ("a fight at the end drops a useful item").

### Tier 2 -- Mobs + boss-drop heads-up
- Tier 1 + explicit warning that a boss fight is coming at the end of an area.
- No boss name, no mechanics, no recommended loadout.

### Tier 3 -- Boss prep
- Tier 2 + name the boss and recommend loadout swaps. This is the first tier at which a boss's own name may be said; a boss the game gives no name gets a generic description ("a heavy mech," "a mutant cluster").
- No mechanics walkthrough, no phase descriptions.

### Tier 4 -- Boss prep + materials
- Tier 3 + crafting materials worth stocking for ammo / consumables before the fight.
- Still no mechanics walkthrough during the fight.

### Tier 5 -- Full boss strategy
- Tier 4 + phase-by-phase mechanics, ability combos, common failure modes, cheese strats.

### A name a boss shares with a common enemy
Some games give a boss the same name as an ordinary enemy. Where the player meets the boss first, the shared name is a boss name everywhere: tag any line that says it at Tier 3 (the boss-name tier), whatever file it is in and whatever fight it describes.
- To warn about the ordinary enemy at a lower tier, write the warning without the name ("organic enemies roam the bridge") and put the name in its own claim at Tier 3.
- A file's place in the story never lowers the name's tier. The player can ask about places they have not reached.
- Where the ordinary enemy comes before the boss, its name is an ordinary-enemy name. Only boss-fight lines take the boss tiers.
- If the guide does not say which comes first, treat the name as a boss name and correct the facts.

---

# Puzzle tiers (0-3)

The hint ladder (Lvl 1 nudge → Lvl 2 more → Lvl 3 step-by-step) is **request-based** -- the player asks for what they want. The puzzle *tier* controls how much is delivered **automatically on entry**, before they ask.

### Tier 0 -- Silent
- No puzzle info preempted. Player asks for everything via the Lvl 1/2/3 ladder.

### Tier 1 -- Mechanic identified (suggested default)
- On entry to a puzzle room, name the puzzle type and core mechanic in one short sentence: "this is a rotation puzzle with two cranks," "this is a polarity-flip relay."
- Don't deliver Lvl 1 nudge unless asked.

### Tier 2 -- Auto-nudge
- Tier 1 + deliver the **Lvl 1 nudge automatically** on entry.

### Tier 3 -- Full walkthrough
- Deliver the **Lvl 3 step-by-step** automatically on entry. Use sparingly -- for sections the player wants to blow through.

### Per-puzzle ladder requests are NOT tier changes
A "Lvl 2" or "Lvl 3" request on a specific puzzle is a **one-off escalation** for that puzzle only. The tier flag does NOT change. Next puzzle resets to whatever the flag says. To change permanently, the player says "set puzzle tier to N."

---

## Implementation note

Before delivering preemptive info, check **both** tier settings here. When in doubt between tiers, err stricter. the player can always raise.

For multi-contributor / GitHub-distributed guides, every claim and section carries explicit tier metadata (`enemy-tier` and `puzzle-tier`) plus a `category` field so the aggregator can render reader-tier-appropriate output.

## Breach log

[Record any time the tier was breached unintentionally. Format: `YYYY-MM-DD -- what happened, what should have happened, what changed to prevent recurrence.`]

# Setup Wizard -- First-Run Prompt Flow

Structured spec any markdown-aware AI agent executes when a user first instantiates hintforge for a new game. Not yet wrapped in an installer -- a future installer milestone will ship the wrapper (Claude Code skill, Python CLI, or slash command).

> **Compaction expectation:** UNEXPECTED. See [`compaction_policy.md`](compaction_policy.md). Setup produces structurally fragile output (scaffolded corpus + briefs). If you observe context pressure mid-wizard -- or if earlier steps burned excess context for any reason -- follow the step 9 handoff failsafe (hand the user the captured parameters + verification block for a fresh session) rather than proceeding into post-compact file writes.

> 🧠 **Run the wizard on a mid-tier model with extended thinking OFF.** The wizard is structural: gather answers, write files from templates, generate research briefs from a fixed schema. None of the steps benefit from extended-thinking reasoning chains, and `[RESEARCH_MODE] = handoff` already externalizes the deep reasoning to whichever deep-research tool the user routes the brief through. Top-tier models (Opus-class) are overkill; mid-tier (Sonnet-class) handles the work. Verify before triggering: most CLIs surface the model name and "thinking" status in their model picker or status line.

## When the wizard runs

Once per (user, game) pair -- when a user adds a new game to their workspace. Not every session.

## Trigger conditions (future)

Any of:
- User runs an installer command and hasn't yet picked a game
- User opens the hintforge folder in their AI bot and types any of: **"set up a new game"**, **"add game"**, **"build me a guide for [X]"**, **"make me a guide for [X]"**, **"create a guide for [X]"**, **"start a new guide"**, **"I want to play [X] with this framework"**, **"set up [X]"** -- or any natural-language variant whose intent is "instantiate the framework against a new game"
- A `setup_complete` flag in the hintforge folder doesn't yet exist for the named game

Until the installer milestone implements the trigger plumbing, the AI bot uses common sense: **if the user names a game and `../Guides/<game>/` is empty or missing, the wizard MUST run before any other action -- including casual answers like "I'll write you a persona" or "I'll scaffold the folder for you." Skipping the wizard to be helpful is a bug.**

## The user's expected entry path (future target)

The first-user test: a non-technical user receives a single pastable message from someone they trust. They paste it into their Claude Code Desktop chat.

**The pastable trigger is natural language**, not a shell command. A non-tech-friendly example:

> Hi Claude -- please clone `https://github.com/hintforge/builder` into my Documents folder and walk me through setting up a guide for [GAME NAME]. Ask me what I need to answer; otherwise use sensible defaults. Don't change anything outside that folder.

The AI bot then:
1. Clones the framework repo
2. Reads `hintforge/setup_wizard.md` and starts walking the user through steps
3. After setup, runs the auto-research bootstrap to populate game-specific content
4. Hands off to normal use: "ask me anything about [GAME NAME]"

Constraints derived from the first-user test (codified in [`principles.md`](principles.md) Principle #12 -- Transparent Operations):
- **No shell required.** The user never opens a terminal. Everything happens through the AI bot's filesystem tools.
- **No Python install required.** Save-watcher and similar Python optional add-ons are scaffolded only if the user has Python; otherwise skipped with a clear note.
- **No UAC / sudo / admin elevation.** Everything writes to user-writable space (`~/Documents/`, `%USERPROFILE%\Documents\`).
- **Plain-language prompts.** No "snake_case folder name" -- instead "what should the folder be called? (default: `[guess]`)". No "save game directory" -- "where does the game store your progress? (you can usually skip this; we'll work without it)".
- **Announce before acting.** Each major action ("I'm going to clone X to Y", "I'm about to write the following 6 files") is surfaced before execution. The user can say "wait" or "skip" at any step.
- **No covert behavior.** No telemetry, no auto-push, no background processes, no scheduled tasks.

## Wizard steps -- required order

The wizard prompts the user one question at a time (or grouped logically). Don't dump the full questionnaire at once -- that overwhelms. Don't skip a step because of an assumption -- confirm.

### Hard rule for the AI bot running this wizard

**Every step below must be either DONE, DONE-VIA-PREFILL, or ASKED ABOUT -- never silently skipped, never inferred, never collapsed into another step.**

- Some steps default to "skip" (Step 3 save-watcher, Step 6 TTS, Step 8 research). Those defaults are still **asked or pre-filled** -- the user picks "skip" out loud or writes it in `setup_answers.txt`. The bot does not pre-select skip on the user's behalf.
- "I assumed you'd want X" is a bug. Even if the inference is obvious, surface it as a confirmation: *"Default is X -- keep it? (yes / change)"*.
- Renaming/relabeling a step's content to fit a specific game (e.g. asking about "threats" instead of "enemies" if the game's vocabulary calls for it) is fine and encouraged -- but the underlying question still has to be asked or pre-filled, and the captured variable still has to be recorded.
- If you finish the wizard and any `[VARIABLE]` from the spec below is unset, that's a bug. Back up, ask, and record it before writing files.
- The Step 9 summary is the enforcement point: it must list every captured variable by name with its source (live answer or `(from setup_answers.txt)`). If you can't fill one in, you skipped a step -- go back.

### Step -1 -- Read pre-filled answers (REQUIRED -- do this before Step 0)

Before any other step, check whether the user has filled in `hintforge/setup_answers.txt`. This is the new pre-fill ingestion path. The file is a plain `key = value` text file the user can edit in Notepad before pasting the setup prompt.

**Procedure:**

1. Read `hintforge/setup_answers.txt`. If the file doesn't exist, treat all variables as unset and run the full live wizard. Skip the rest of this step.
2. For each line in the file:
   - Skip blank lines and lines starting with `#`.
   - Split on the first `=` and trim whitespace from both sides.
   - Map the key to the corresponding wizard variable per the table below.
   - If the value is empty, the literal string `ask`, or the user wrote a question mark, treat the variable as unset (ask live in the right step).
   - Otherwise record the value and mark the corresponding step as DONE-VIA-PREFILL.
3. If you encounter an unrecognized key or a clearly-invalid value (e.g. `enemy_tier = 9`), quote the offending line back to the user and ask live for that step. Do NOT abort the wizard -- just degrade that one entry to live.

**Key → variable mapping:**

| Key in file | Wizard variable | Step |
|---|---|---|
| `game_name` | `[GAME_NAME]` | 1 |
| `game_folder` | `[GAME_FOLDER]` | 1 |
| `game_platform` | `[GAME_PLATFORM]` | 1 |
| `game_version` | `[GAME_VERSION]` | 1 |
| `player_name` | `[PLAYER_NAME]` | 1.5 |
| `workspace_root` | `[WORKSPACE_ROOT]` | 2 |
| `save_dir` | `[SAVE_DIR]` | 3 |
| `game_install_dir` | `[GAME_INSTALL_DIR]` | 3 |
| `enemy_tier` | `[ENEMY_TIER]` | 4 |
| `puzzle_tier` | `[PUZZLE_TIER]` | 4 |
| `personas` | `[PERSONA1]`, `[PERSONA2]`, `[DEFAULT_PERSONA]` | 5 |
| `tts` | `[TTS_ENABLED]`, `[TTS_STYLE]` | 6 |
| `ptt` | `[PTT_ENABLED]` | 6.5 |
| `ptt_hotkey` | `[PTT_HOTKEY]` | 6.5 |
| `stage0` | `[STAGE0]` | 6.7 |
| `research` | `[RESEARCH_MODE]` | 8 |
| `run_p2` | `[RUN_P2]` | 8 |
| `run_p3` | `[RUN_P3]` | 8 |

**Special handling:**

- `personas = you pick` → mark Step 5 as needing live persona research, even though the file had a value. Do the research, propose two options, confirm with the user.
- `personas = none` → record all three persona vars as `none`; **`persona.md` MUST be written via Step 5 Branch B (plain-assistant body). Wizard MUST NOT propose, research, or substitute character voices when prefill is `none` -- that's a prefill-override bug.**
- `personas = NameA / NameB` → split on `/`, trim, treat first as `[PERSONA1]` and `[DEFAULT_PERSONA]`, second as `[PERSONA2]`. Confirm in Step 9.
- `tts = skip` → `[TTS_ENABLED] = false`, `[TTS_STYLE] = n/a`.
- `tts = persona-matched` or `tts = generic` → `[TTS_ENABLED] = true`, `[TTS_STYLE]` set accordingly. Step 6 still runs to do the OS detection / voice selection live.
- `save_dir = skip` and `game_install_dir = skip` → Step 3 fully skipped; record as `skipped (from setup_answers.txt)`.
- `research = deep` → still announce the cost estimate and confirm before running, even though pre-filled. Heavy ops always get one final live confirmation.
- `run_p2 = skip` → `[RUN_P2] = false`. `run_p2 = yes` → `[RUN_P2] = true`. Ignored when `[RESEARCH_MODE]` is not `handoff` or `deep`.
- `run_p3 = skip` → `[RUN_P3] = false`. `run_p3 = yes` → `[RUN_P3] = true`. Ignored when `[RESEARCH_MODE]` is not `handoff` or `deep`.

**Prefill precedence (CRITICAL -- read before any later step):**

When a variable is DONE-VIA-PREFILL with a valid value from `setup_answers.txt`, that value is **authoritative for the rest of the wizard**. Do not re-derive it from any default, OS-aware path, current working directory, or skill installation location at any later step. The prefill wins. This applies especially to `workspace_root` → `[WORKSPACE_ROOT]`: a prefilled absolute path is the final answer, not a hint to be combined with anything else.

**Skip rule for the rest of the wizard:**

For each step where every variable is DONE-VIA-PREFILL with a valid value, do not ask the user that step's question(s). Move on. Tell the user what you used: *"Using `puzzle_tier = 1` from your setup_answers.txt -- moving on."*

For steps where the pre-fill is partial (e.g. `personas = you pick`), run the live interaction normally; you can use the pre-fill to skip leading sub-questions.

**The user always sees a final summary at Step 9** showing every variable. Pre-filled values from `setup_answers.txt` are annotated `(from setup_answers.txt)` so the user can catch typos in the file; values answered live or via popup are unannotated. That's where typos get caught.

### Batching policy (REQUIRED -- applies to all unanswered batchable steps)

After Step -1 reads pre-fills and Step 0 confirms environment, the wizard collects **all unanswered batchable variables into a single ask**. Do NOT walk Steps 1-8 sequentially when batching is available -- that defeats the point and burns round-trips.

**Batchable steps (collect into one call):**
- Step 1 -- `game_name`, `game_folder`, `game_platform`, `game_version` (`game_version_as_of` is auto-set to today, never asked)
- Step 1.5 -- `player_name`
- Step 2 -- `workspace_root`
- Step 3 -- `save_dir`, `game_install_dir`
- Step 4 -- `enemy_tier`, `puzzle_tier`
- Step 6 -- `tts`
- Step 6.5 -- `ptt`, `ptt_hotkey`
- Step 6.7 -- `stage0` (yes/skip)
- Step 8 -- `research`

**Live-only steps (sequential, after the batched ask):**
- Step 5 -- persona research (when `personas = you pick`); needs bot reasoning between turns
- Step 6.7 -- Stage 0 pre-research (when `stage0 = yes`); web search runs after the batched ask, output written to `stage0_priors.md` before Step 7
- Step 7 -- subfolder shape; bot pre-populates from Stage 0 priors, user confirms/edits
- Step 9 -- confirmation summary; always live, always one final yes/no
- Step 10 -- fresh-session handoff; verbatim closing message

**Tool selection -- primary: `AskUserQuestion`.** If the bot has the `AskUserQuestion` tool available (Claude Code Desktop and most Claude Code variants do), use it. One call, all batchable unanswered questions, structured form-style popup. Multi-choice for tiers and TTS/research; text fields for game name and player name.

**Fallback when `AskUserQuestion` is unavailable** (Cowork, claude.ai web, third-party bots): one chat message containing a numbered list of the unanswered questions, asking the user to answer them all in a single reply. Still a 1-round-trip improvement over sequential. Template:

```
A few quick questions to finish setup. Please answer them all
in one reply (numbered, in any format) and I'll process them
together:

1. Game name?
2. Folder name? (default: derived from game name)
3. Platform? (e.g. PC / Steam, PS5, Switch -- required even if single-platform today)
4. Game version? (semver like 1.10.5.0, patch name like "Annihilation Instinct", build number, or "unknown" if you can't find it)
5. What should I call you? (default: "Player")
6. Enemy tier 0-5? (0 = surprises stay surprises, 5 = full strategy)
7. Puzzle tier 0-3? (0 = silent, 3 = full solutions on entry)
8. Save-watcher? (skip / set up -- skip recommended on Pro)
9. Read-aloud? (skip / persona-matched / generic -- skip recommended on Pro)
10. Research mode? (none / minimal / standard / deep / handoff -- none recommended on Pro; handoff externalizes cost to Gemini/ChatGPT/Perplexity)
```

(Omit lines for variables already pre-filled in `setup_answers.txt`.)

**Tool schema adaptation:** if `AskUserQuestion` doesn't support free-text fields in the bot's environment, downgrade gracefully -- multi-choice questions go in the popup, text questions (game name, player name) go in one chat message. Two round-trips instead of one is still a win over nine.

**The hard rule still holds.** Every variable must be DONE, DONE-VIA-PREFILL, or ASKED (now via popup or batched-list). Step 9's enforcement gate runs unchanged: any literal `[VARIABLE]` token in the summary means the wizard isn't done.

**Shell tool selection -- Windows note.** When running on Windows, the `Bash` tool is Git Bash (POSIX), not PowerShell. PowerShell-style cmdlets like `New-Item`, `Out-Null`, `Write-Output` will fail there with `command not found`. For filesystem operations on Windows, prefer the dedicated `PowerShell` tool. POSIX commands (`mkdir -p`, `cp`, `mv`, `echo`, `cat`) work in either tool. macOS / Linux: Bash is bash; no special handling needed.

**For file content writes -- always use the `Write` tool, never a shell.** Templates, `research_briefs/p*.txt`, persona / brief / section files -- anything multi-paragraph -- must be written with the `Write` tool (path + content), not `pwsh -Command "..."` or `bash -c "cat <<EOF..."` with the body inlined. Windows' command-line max is ~8191 chars and long markdown blows past it, surfacing as `pwsh exited with code 1: The command line is too long`. This rule applies on all platforms; it's just most likely to bite on Windows. Shells are for filesystem ops (mkdir, cp, mv, ls); `Write` is for content.

### Step 0 -- Environment check (REQUIRED -- do this before anything else)

> **For the AI bot reading this wizard:** before running Step 1 or any other step below, verify the environment supports persistent local filesystem access. This framework writes files to the user's Documents folder and assumes those files persist between sessions. Some environments don't.

Decision matrix:

| Environment | Verdict | What to do |
|---|---|---|
| **Claude Code Desktop** with Files connector enabled | ✅ Proceed | Files persist on the user's local disk between sessions. Continue to Step 1. |
| **Claude Code** (CLI / IDE) | ✅ Proceed | Same as above. |
| **Cowork** (Anthropic collaborative workspace) | ⚠️ STOP and confirm | Files written by this wizard land in Cowork's session output, not the user's actual Documents folder. The setup will appear to "work" but won't persist between Cowork sessions -- the user will have to redo the whole thing every time they come back. |
| **claude.ai web** (no filesystem connector) | ⚠️ STOP and confirm | Same problem as Cowork -- no persistent local filesystem. Files don't make it to the user's disk. |
| **Other AI bots** | ❓ Verify first | Confirm the bot has genuinely persistent local filesystem access (writes survive session restart) before proceeding. |

**If you are running in Cowork or claude.ai web, surface this to the user verbatim BEFORE doing any work:**

> Heads up -- I'm running in [Cowork / the claude.ai browser tab] right now, but this hintforge framework is designed for environments where files persist on your actual computer between sessions (like Claude Code Desktop or Claude Code). If we keep going here, the files I create will live in this chat's output area and won't be on your disk for next time. You'd have to redo the whole setup every session.
>
> If you can, the smoother path is to download **Claude Code Desktop** from claude.ai/download, sign in with the same account, and re-run this there. The setup is shorter, and the guide is permanent.
>
> Want me to (a) pause here so you can switch to Claude Code Desktop, or (b) keep going in this environment knowing it won't persist?

Only proceed to Step 1 after the user explicitly picks (b), OR after confirming the environment is Claude Code / Claude Code Desktop with persistent filesystem access.

This step exists because of a real failed test (2026-04-29): a non-tech user ran the framework in Cowork by mistake. The wizard ran end-to-end and *appeared* to work, but the files never reached their disk. Auto-detecting and pausing prevents the same false-success.

### Step 1 -- Game identification (REQUIRED)

**Ask:**
- "What game is this guide for?"

**Capture:**
- `[GAME_NAME]` (free-form; user types whatever they call it)
- `[GAME_FOLDER]` (suggest a snake_case version of the name; let user override)

**Then ask, in this order (REQUIRED for `corpus-core-version: 3` manifest):**

1. **"What platform are you playing on?"** -- examples: `PC / Steam`, `PC / GOG`, `PC / Epic`, `PS5`, `PS4`, `Xbox Series X|S`, `Xbox One`, `Switch`, `Switch 2`. Required even when the game is single-platform-today; games frequently expand to additional platforms post-launch, and the corpus must declare which platform it was authored against from day one. If the user is unsure, ask them to name the device they actually play on; do not auto-guess. Capture as `[GAME_PLATFORM]`.

2. **"What version of the game are you on?"** -- freeform string. The wizard does NOT normalize. Acceptable shapes: semver (`1.10.5.0`), patch names (`Annihilation Instinct`, `Phantom Liberty 2.1`), build numbers (`Build 12345`), DLC-named eras (`pre-DLC2`, `post-launch-patch-2`), or `unknown -- haven't checked` when the user can't find it. If the user doesn't know how to check, tell them where to look (Steam library version field, console game-info menu, in-game settings/about screen) but do not block setup -- `unknown` is a valid answer and the reader will surface it as-is. Capture as `[GAME_VERSION]`.

3. **`[GAME_VERSION_AS_OF]`** -- set automatically to today's date in `YYYY-MM-DD` form. Do not ask. This stamps the date the corpus is being built against the version the user just named, which becomes the reader's drift-detection reference point.

**Why these three are required at setup, not deferred.** The reader surfaces all three at session start so the player can react if the game has patched / they're on a different platform than the corpus was authored for. Players can defer game updates, DLCs add content without bumping the base version, and corpus refreshes happen without game patches -- the corpus needs an explicit anchor to compare drift against, and the player is the only honest source. The manifest is a **build-time snapshot**: the reader periodically asks the player to reconfirm during play, but the reader never updates the manifest. Corpus rev-bumps remain a builder-side action triggered by the maintainer re-running setup or hand-editing the manifest, not a side-effect of reader sessions.

**Don't yet:**
- Ask about platform-specific game details (storefront-level installer paths, save dir, etc.) -- that comes in Step 3 if save_watcher is wanted. `[GAME_PLATFORM]` captured here is the corpus-level "what device is this guide for" stamp, not the install-path question.

### Step 1.5 -- What to call the player (REQUIRED)

This step captures what the persona should call the player. Friendly and game-native, not clinical.

**One question, optional. A default is fine if the user shrugs.**

1. **"What should I call you?"**
   - If a name is inferable from prior session context (the user typed their name earlier, or the AI bot has a memory of it), suggest it as the default: *"What should I call you? (I'd guess **[INFERRED]** based on what you've said -- say a different name or 'use that' if it's right.)"*
   - If no inference is possible, default suggestion: *"Player"* (or the in-game default name for [GAME] if the AI knows it).
   - Capture as `[PLAYER_NAME]`.

**Skip rules:**
- If the user says "skip" or "don't care," capture `[PLAYER_NAME] = "Player"` and move on.
- Don't insist. Don't repeat the question.

**Where it's stored:**
- `[PLAYER_NAME]` goes into the per-game `CHECKPOINT.md` under a "Player" section. The rest of the wizard can use it for friendlier prompts ("Got it, [PLAYER_NAME] -- next question…").

### Step 1.9 -- Resolve and announce `[WORKSPACE_ROOT]` (REQUIRED -- runs before any Write)

This step is a deterministic precondition. It runs after Step 1 captures `[GAME_FOLDER]` and **before any Write tool call against any corpus file** -- including `research_briefs/stage0_priors.md` written in Step 6.7.

**Procedure (strict cascade -- first match wins):**

1. **Prefill from setup_answers.txt.** If Step -1 captured `workspace_root` from `setup_answers.txt` with a non-empty, non-`ask` value, set `[WORKSPACE_ROOT]` to that absolute path. Source tag: `setup_answers`. **Stop here -- do not consult any other signal.**
2. **Current working directory.** Else, capture cwd (PowerShell: `Get-Location`; Bash: `pwd`). If cwd contains a `hintforge/` subdirectory OR cwd's basename looks like a hintforge test sandbox (matches `hintforge_test_*`), set `[WORKSPACE_ROOT]` to cwd. Source tag: `cwd`.
3. **OS Documents default.** Else, use the OS-appropriate user-Documents path: Windows `%USERPROFILE%\Documents\Claude\`, macOS/Linux `~/Claude/`. Create the directory if it doesn't exist. Source tag: `default`.

**Hard rule -- skill base is not a path source.** The skill loader injects a line like `Base directory for this skill: C:\Users\<user>\.claude\skills\hintforge` (or the macOS/Linux equivalent under `~/.claude/skills/`). That path is **read-only metadata** describing where the framework files live for `Read` operations. It MUST NOT be used as `<parent of hintforge>`, MUST NOT anchor `[WORKSPACE_ROOT]`, and MUST NOT appear in any Write/mkdir target. Corpus files NEVER write into `~/.claude/skills/`. If the resolution cascade above somehow yields a path under `~/.claude/skills/` (it shouldn't -- cwd and Documents won't ever be there), treat it as a bug and halt for live confirmation.

**Announcement (REQUIRED, even in AUTO-CONFIRM mode):**

Before the first Write of any corpus file, print exactly one line:

```
[WORKSPACE_ROOT] = <resolved path> (source: setup_answers | cwd | default)
First Write target: <[WORKSPACE_ROOT]>/Guides/<[GAME_FOLDER]>/<filename>
```

AUTO-CONFIRM mode does not suppress this announcement -- it is a path-resolution trace, not a question. If the source is anything other than `setup_answers` AND the path doesn't end in a sandbox-style (`hintforge_test_*`) or Documents-style directory, halt and ask the user to confirm before proceeding.

### Step 2 -- Workspace location (REQUIRED -- confirm default)

> Step 1.9 has already resolved `[WORKSPACE_ROOT]` via the strict cascade. This step exists to **confirm** that resolution with the user when no prefill was used. If `[WORKSPACE_ROOT]` was set via `setup_answers` source, skip this step entirely.

**Ask (only when source is `cwd` or `default`):**
- "I'll create the per-game folder at `[WORKSPACE_ROOT]/Guides/[GAME_FOLDER]/`. OK, or pick a different location?"

**Capture:**
- `[WORKSPACE_ROOT]` -- already resolved in Step 1.9. The actual guide folder lands at `[WORKSPACE_ROOT]/Guides/[GAME_FOLDER]/`.

**Why `Guides/` and not as a workspace sibling of hintforge?** The framework is published as a public git repo and each guide will eventually be its own public repo. Grouping all guides under one `Guides/` folder keeps the workspace clean as guides accumulate, without nesting guides inside the public framework repo.

If `Guides/` doesn't exist yet, create it as part of this step.

### Step 3 -- Game install / save locations (REQUIRED to ASK -- answer is usually "skip"; ⚠️ token-intensive)

> **⚠️ Heads-up for Claude Pro users -- strongly consider skipping this step.**
> Setting up the save-watcher (a small script that reads your save file so the guide knows where you are in the game) typically takes **10-30 messages** to get right. Save-file formats vary per game and often need trial-and-error reads. On the Pro tier (~45 messages per 5-hour window), this can eat most of your budget before you even start playing.
> The guide works fine without save-watcher integration -- you'll just tell it where you are when it matters. Skip unless you're on Max / Team or you specifically want live save-state awareness.

**Ask (optional -- and clearly marked as skippable):**
- "Want me to set up a save-file watcher? It lets me know where you are in the game without you telling me, but it takes 10-30 messages to set up and many games make this hard. Most users should skip. (yes / **skip**)"
- If user chooses skip → record `[SAVE_DIR] = skipped` and move on.
- If user chooses yes → "Where does the game save your progress?" and "Where is the game installed (optional, helps research)?"

**Capture (only if not skipped):**
- `[GAME_INSTALL_DIR]` -- research hint when looking up game-specific data
- `[SAVE_DIR]` -- used to scaffold `save_watcher.py` in the per-game folder

**OS-aware default suggestions (only shown if user opts in):**
- Windows: `C:\Users\<user>\AppData\Local\<GAME>\` or `%APPDATA%\<GAME>\`
- Mac: `~/Library/Application Support/<GAME>/`
- Linux native: `~/.local/share/<GAME>/`
- Linux via Proton/Steam: `~/.steam/steam/steamapps/compatdata/<id>/pfx/drive_c/users/steamuser/...`

**Default for the first-user test:** skipped.

### Step 4 -- Assistance tier preferences (REQUIRED)

This is the backbone (see `principles.md` Principle #1). Don't skip; don't default silently.

**Explain first** (one short sentence each, then the question):
- "Two independent dials control how much the guide volunteers before you ask. Higher = more help up-front; lower = more discovery on your own."

**Enemy help tier (0-5):**
- 0 = no warning ever (encounters are surprises)
- 1 = mob types named in route hints; bosses still hidden
- 2 = boss-fight existence flagged; no boss details
- 3 = boss generically named + loadout suggestions
- 4 = + crafting materials to stock
- 5 = full phase-by-phase boss strategy

**Ask:**
- "Pick an enemy help tier 0-5. Default: 0."

**Puzzle help tier (0-3):**
- 0 = silent until you ask
- 1 = on entry, name the puzzle type and core mechanic
- 2 = + auto-deliver a Lvl-1 nudge on entry
- 3 = + auto-deliver full step-by-step on entry

**Ask:**
- "Pick a puzzle help tier 0-3. Default: 1."

**Capture:**
- `[ENEMY_TIER]`, `[PUZZLE_TIER]`

**Note:** the user can change tiers any time after setup with "set enemy tier to N" / "set puzzle tier to N". This is a starting point, not a lock.

### Step 5 -- Persona / voice preferences (REQUIRED)

> **Hard rule -- `persona.md` is unconditional.** Every game guide gets a `persona.md` at the game-folder root, regardless of the answer below. The file is the integration point for PTT/TTS modules and the future `add a persona` toggle; skipping it leaves voice modules with no hook to register against. **Skipping `persona.md` is a bug** -- incidents on file: prior wizard runs ignored `personas = none` and picked two characters anyway, or skipped the file entirely. Step 5 has two branches (A and B); both write `persona.md`.
>
> **`personas = none` prefill is authoritative.** When Step -1 set `personas = none`, the wizard MUST take Branch B without proposing or researching character voices. Do not "helpfully" override the prefill.

**Ask (skip when `personas = none` was set in Step -1 -- take Branch B directly):**
- "Want the guide to speak in the voice of an in-game character? (yes / no / not sure)"

#### Branch A -- character voices (only when user said yes and named/approved characters)
- "Pick two characters from the game whose voices you'd want -- one will be active, the other available as a toggle. Or say 'you pick' and the AI agent will research candidates from the game."
- Capture `[PERSONA1]`, `[PERSONA2]`, `[DEFAULT_PERSONA]`
- Copy `templates/persona.md` to `<game>/persona.md`; substitute placeholders.

#### Branch B -- plain assistant (user said no / not sure, OR `personas = none` prefill, OR game has no suitable in-world voice)
- Capture `[PERSONA1] = none`, `[PERSONA2] = none`, `[DEFAULT_PERSONA] = none`.
- **Write `<game>/persona.md` with the body below -- verbatim, substituting `[GAME]` only.** Do not copy `templates/persona.md` for this branch; the character template's placeholders don't apply.

```markdown
# Persona -- plain assistant

This guide is currently in **plain assistant** mode for [GAME]. No in-character persona is active. Responses use the standard assistant voice while honoring all hintforge spoiler-tier, citation, and hint-ladder rules.

## Reserved hook

`persona.md` is the integration point for PTT (push-to-talk voice input) and TTS (read-aloud) modules. Both register against the active voice declared in this file; the plain-assistant mode is a valid registration target.

## Switching on a character voice later

Say "add a persona" or "switch to a character voice" in a session opened against this guide. The assistant will research two suitable characters from [GAME], propose them, and rewrite this file with the two-voice toggle structure from `templates/persona.md` once confirmed.

## Universal rules (do not edit here)

The voice-agnostic discipline that applies to every persona in every corpus -- player-pull rule, honest-ambiguity rule, behavioral bedrock, research cascade order, navigation runtime rules, TTS spoken-text constraints -- lives in the **hintforge-reader skill**, not in this file. The reader loads it at session start.
```

- After writing: confirm to user with "Plain assistant mode active. Say 'add a persona' later to switch on character voices."

### Step 6 -- Read aloud / Text-to-Speech (REQUIRED to ASK -- answer is usually "skip"; ⚠️ token-intensive)

> **What this step is about:** "Text-to-Speech" (TTS) means the assistant reads its responses out loud through your computer's speakers, instead of (or in addition to) showing them as text. Some people like this for an immersive game-companion vibe; most people skip it.

> **⚠️ Heads-up for Claude Pro users -- strongly consider skipping this step.**
> Setting up read-aloud takes **5-15 messages** for a basic in-wizard SAPI hook, or **30-60 messages** for the full persona-aware Edge TTS / Whisper PTT setup specced in [`templates/optional_modules.md`](templates/optional_modules.md). Either way, voice availability varies by OS and matching a specific in-character voice is approximate at best. On Pro, those messages are better spent on actual gameplay questions.
> You can always add read-aloud later by saying "set up read-aloud for this guide" once you're more familiar with the framework.

> **For technical users who want the full setup** (TTS + push-to-talk voice input): see [`templates/optional_modules.md`](templates/optional_modules.md) -- the spec for three opt-in capability modules (PTT, TTS, save-state). Code-intensive (requires Python + pip + manual settings edits) but produces a hands-free voice-conversation experience. The wizard does NOT install these; the spec describes the contract that future drop-in templates will fulfill, with the in-tree reference impl as the worked example.

**Ask:**
- "Want me to read responses out loud through your speakers? Most users skip this. (yes / **skip**)"

**If skip (default):**
- Record `[TTS_ENABLED] = false`. Move on.

**If yes:**
- "Match the persona voice as closely as possible (game-themed character voice), or just use your computer's default voice?"
- OS-detect: Windows → SAPI available; Mac → `say` available; Linux → check for `espeak` / `festival`. If none available: "Read-aloud isn't available on your system right now -- skipping."
- If persona-matching: "Voice matching is approximate -- your computer's voices won't sound exactly like the game character. OK to try anyway?"
- **Add the new game folder's absolute path to `~/.claude/tts_game_folders.txt`** (one path per line; create the file if it doesn't exist).
- **Stale-entry sweep -- required, not optional.** Before writing the new line, read every existing path in `~/.claude/tts_game_folders.txt` and check whether it resolves on disk. For any path that doesn't exist (e.g., a guide that was renamed, moved, or deleted), surface it to the user once: *"`<stale path>` in your TTS allowlist no longer exists -- remove it? (yes / keep)"* -- and act on the answer in the same step. Do NOT leave stale entries in place "just to be safe": they're dead weight at best, and worse, they signal to future agents that working around stale state is acceptable. The user-global allowlist is shared cross-game state, and reconciling it with reality is part of touching it.

**Capture (only if enabled):**
- `[TTS_ENABLED]`, `[TTS_STYLE]` (`persona-matched` / `generic`)

**Note on portability:** the Windows + PowerShell + SAPI pattern is what's documented today. Mac (`say`) and Linux (`espeak` / `festival`) variants are a roadmap deliverable, alongside a richer pluggable persona library with iconic AI voices.

**Default for the first-user test:** skipped.

### Step 6.5 -- Push-to-talk / PTT (REQUIRED to ASK -- answer is usually "skip"; ⚠️ token-intensive)

> **What this step is about:** Push-to-talk lets the user hold a key to speak into Claude Code. Audio is captured and transcribed locally via Whisper (no cloud upload), pasted into the active Claude window, and Enter is pressed. Pairs naturally with TTS (Step 6) for a hands-free voice-conversation experience.

> **⚠️ Heads-up for Claude Pro users -- strongly consider skipping this step.**
> Setting up PTT requires Python + faster-whisper + sounddevice + numpy + AutoHotkey v2. The wizard's PTT-opt-in path costs ~3-5 messages assuming all dependencies are already installed; up to 10-15 if Python packages need installing. Save it for later if you're not sure.

**Ask:**
- "Want me to set up push-to-talk? Hold a key to talk; release to transcribe and send. Most users skip; you can add it later. (yes / **skip**)"

**If skip (default):**
- Record `[PTT_ENABLED] = false`. Move on.

**If yes:**
- Confirm prereqs: Python, faster-whisper, sounddevice, numpy, AutoHotkey v2. If any missing, ask whether to install (Python packages via `pip install`; AHK requires user-level install from autohotkey.com -- surface the URL).
- Ask for the hotkey: *"What key do you want to hold to talk? Default Numpad+ only works on full-size keyboards. Common picks for laptops: CapsLock, F13, ScrollLock. Or a mouse side button: XButton1, XButton2."*
- Capture `[PTT_HOTKEY]`. Sanity-check against the known-good starter list in `templates/ptt/windows/README.md` (`NumpadAdd`, `CapsLock`, `F13`-`F24`, `ScrollLock`, `RAlt`, `AppsKey`, `MButton`, `XButton1`, `XButton2`). If the user's choice is in that list, accept it silently. If it's outside the list, accept it but warn: *"I haven't verified that key name against AHK's full v2 key list -- if it's wrong, AHK will fail to parse `ptt.ahk` on first run with a clear error. The full list is at [autohotkey.com/docs/v2/KeyList.htm](https://www.autohotkey.com/docs/v2/KeyList.htm). Continue?"* The full AHK v2 key list is too large to vendor; runtime failure is the validator.
- **On Windows:** copy `templates/ptt/windows/` files into `<game>/ptt/` and `<game>/.claude/`. Edit the new `<game>/ptt/ptt.ahk`'s `PTT_HOTKEY := "..."` line to use `[PTT_HOTKEY]`.
- **On macOS or Linux:** invoke `templates/ptt/_build_for_other_platforms.md` as an agent prompt -- it reads the Windows source under `templates/ptt/windows/` and constructs a native-tool port (Karabiner / Hammerspoon / AutoKey / xbindkeys / Wayland-native keybinds). Carries an "untested, expect to debug" disclaimer; surface that to the user before proceeding.

**Capture (only if enabled):**
- `[PTT_ENABLED]`, `[PTT_HOTKEY]`

**Default for the first-user test:** skipped.

### Step 6.7 -- Stage 0 pre-research (REQUIRED -- runs before Step 7; ⚠️ token-aware)

**Why this exists.** Asking the user to classify content categories (Step 7) without internet context creates a catch-22: classification needs research, research is shaped by classification. The result of skipping pre-research is that the P1 brief (later) inherits whatever the user happened to guess, and gameplay fundamentals -- weapons, abilities, controls, settings -- get under-covered because the brief never knew they existed in the form they take in this game. The failure this step prevents: a prior P1 produced a 46-zone graph but only documented 3 of 12+ weapons; no controls.md, no settings.md, no abilities.md, no upgrades.md.

**Cost.** 1-3 messages -- one or two web queries (Wikipedia / IGDB / Steam description / one or two top guides), one summarization message. Announced before running; user can skip.

**Ask:**
- "Quick web search before I ask you about subfolders -- costs ~1-3 messages and lets me suggest specific content categories instead of asking you to guess. (yes / **skip**)"

**If skip:**
- Record `[STAGE0] = skipped`. Step 7 falls back to the generic checklist with default subfolders. Continue.

**If yes -- procedure:**

1. Run a web search on `[GAME_NAME]` (Wikipedia + Steam page + one community guide if available). Pull a description, genre tags, and any easily-visible content signals (weapon list length, ability tree presence, settings-menu coverage, control-rebind notoriety).

2. Produce a **structural-priors block** with these required outputs:

   - **Game-type signal:** one of `dungeon-linear` / `hub-and-spoke-with-dungeons` / `open-world-with-distinct-dungeons` / `open-world-explorative-only` / `procedural` / `on-rails` / `narrative-no-nav`. One-line rationale.
   - **Localization-mechanism signal:** one of `map-system` / `landmark` / `hybrid` / `none`. One-line rationale.
   - **Content categories inventory** -- for each category below, mark `present` / `absent` / `uncertain` with a one-line source-citing rationale and (when present) a coverage estimate (rough item count or system complexity):
     - `weapons` (and whether weapons split into meaningful subcategories -- melee vs. ranged vs. magic, etc.)
     - `cartridges` / `ammo` (only when ammo types are meaningfully distinct, not generic "bullets")
     - `consumables` (heals, buffs, throwables)
     - `crafting_materials`
     - `abilities` (skills, spells, glove-style mechanics, talents)
     - `upgrades` (skill trees, augmentations, perks, attribute progression)
     - `support_items` (utility items, traps, deployables)
     - `builds` / `loadouts` (whether the game supports meaningful build choice -- multiple viable playstyles, weapon synergies, ability combinations)
     - `controls` (note any signals that the game has a notorious control scheme, common remap recommendations, or accessibility-rebind community discussion) -- **always present; the question is depth, not existence**
     - `settings` (note any signals about graphics/audio/accessibility settings that affect difficulty perception -- motion blur tolerance, FOV gating, HDR issues, colorblind mode quality, subtitle behavior) -- **always present for any PC/console game**
   - **Source-language signal:** dev-country language + top player-region languages (used to seed P1's non-English source floor).
   - **Cross-system dependency density:** one of `high` / `medium` / `low`. High = many interacting systems (open-world RPGs, immersive sims, Metroidvanias with gated progression). Medium = moderate system interaction (linear action games with upgrades, hub-and-spoke games). Low = minimal cross-system interaction (linear narratives, single-mechanic puzzle games, roguelikes with independent runs). Informs stitch-and-zipper recommendation strength at post-ingestion handoff.
   - **Named-NPC density:** one of `high` / `medium` / `low`. Cheap proxy: count proper-noun NPC mentions across a typical walkthrough chapter summary. Structural signal: party-size + presence of recruit/companion/persuade systems. High = recruitable companions, named questgivers across multiple zones, named recurring antagonists (CRPGs, JRPGs, party-driven action-RPGs). Medium = a handful of named recurring NPCs (linear story-driven action games). Low = generic mob-shaped enemies and crowd NPCs only (most arcade, roguelite, abstract-strategy, pure-puzzle games). Feeds Step 7's `npcs/` auto-pop rule (high = scaffold; medium = optional; low = skip).
   - **Faction density:** one of `high` / `medium` / `low`. Group entities the player has an ongoing relationship with (not one-off enemy units). High = multi-faction reputation systems, faction-driven quest gating, faction-specific endings. Medium = a few named factions with stable but non-mechanical relationships. Low = no meaningful faction layer. Feeds Step 7's `factions/` auto-pop rule.
   - **Crew-system signal:** `yes` / `no`. Yes when the game has role-aggregated, run-bound, or party-bound entities where individual identity is ephemeral but the role persists across runs (run-based roguelikes with persistent role slots, ship-crew sims). Feeds Step 7's `crew/` auto-pop rule.
   - **Reputation-system signal:** `yes` / `no`. Yes when faction reputation, alignment, or relationship-track meters carry enough mechanical weight to warrant their own aggregation surface separate from `factions/` (multi-tier rep systems, romance-track NPCs, alignment-sensitive interactions). Feeds Step 7's optional `reputation/` auto-pop rule.

3. Write the structural-priors block to `<game>/research_briefs/stage0_priors.md` AND show it inline in chat. The user can edit this file before Step 7 -- the file is the canonical input to Step 7's pre-population.

4. **Fetch the achievement stub list** (required at `corpus-core-version: 4` and later). Platform achievement lists are exhaustive and missability-flagged -- they function as a completeness skeleton for P1 ingestion.

   - **Fetch the list using the ranked source ladder below.** If the user named a non-Steam platform in Step 1 (`[GAME_PLATFORM]`), prefer that platform's list (PSN trophy list, Xbox achievement schema, etc.). Cite the canonical URL in the `Sources` section of `<game>/achievements.md` regardless of which ladder rung served the bytes (same posture as `capture-method` for Fandom).

     **Source ladder (try in order, stop at first success):**
     1. **Steam API `GetSchemaForGame`** -- `https://api.steampowered.com/ISteamUserStats/GetSchemaForGame/v2/?appid=<APPID>&key=<KEY>`. Requires a Steam Web API key. Skip if no key is configured.
     2. **WebSearch** -- query `"<game title> steam achievements full list"`. Produces working URLs that bypass Cloudflare-gated domains. Empirically the fastest path when rung 1 is unavailable.
        - **Result-selection rule.** From the WebSearch results, prefer in this order: (a) official platform pages (Steam Community / PSN / Xbox achievement pages); (b) game-specific wikis EXCLUDING Fandom; (c) sites named in rung 3 (`vgtimes.com`, `gamingbolt.com`, `daynglsgameguides.com`). Do NOT fetch any URL that doesn't match (a)/(b)/(c) -- third-party aggregators not on rung 3 (e.g. `corrosionhour.com`, `achievementstats.com`) are off-ladder. Do NOT fetch Fandom from rung 2 results; Fandom is rung 5 and is only attempted after rungs 1-4 have all failed.
     3. **Accessible aggregator sites** -- `vgtimes.com`, `gamingbolt.com`, `daynglsgameguides.com`. These reliably serve content without Cloudflare challenge pages as of 2026-05.
     4. **Canonical Steam stats page** -- `https://steamcommunity.com/stats/<APPID>/achievements`. Frequently Cloudflare-blocked for automated fetchers. Try once; do not retry.
     5. **Cloudflare-prone mirrors** -- `exophase.com`, `steamhunters.com`, `truesteamachievements.com`, `strategywiki.org`, `<game>.fandom.com/wiki/Achievements`. Try at most one. Do not loop through this rung -- cycling through blocked mirrors is the single biggest time waste in achievement fetch runs.

     **If rungs 1-4 all fail,** log the gap in `limitations.md` with manual-fetch instructions and move on. A human browser session will succeed where automated fetchers cannot.
   - **Fetch.** For each achievement capture: display name (verbatim), API name if available, hidden flag, platform's global completion percentage if surfaced. **Do NOT capture the developer's description text** -- the trigger condition is researched in P1, not lifted from the platform. Developer-authored descriptions are publisher IP; names and ids are factual lookup keys and travel verbatim.
   - **Write the stub list twice.** (a) Write to `<game>/achievements.md` as the initial scaffold's stub body -- flat list, no trigger-type grouping yet; P1 ingestion classifies each entry and reorganizes the file into the six `trigger_type` H2 sections (see [`templates/achievements.md`](templates/achievements.md) and the aggregation rule in [`ingestion.md`](ingestion.md) step 8). (b) Write the same raw list to `<game>/research_briefs/achievement_stubs.md` as a flat fetch-time artifact. The stubs file is P1's completeness check input; it does not change after Stage 0. Stamp `stub_source:` and `stub_fetched:` in the `achievements.md` frontmatter.
   - **Skip rule.** If the user picked `[STAGE0] = skip`, achievement-stub fetch also skips. `achievements.md` is still created at scaffold (per Step 9 universal-core list) with an empty stub body; the P1 brief generator falls back to instructing the researcher to fetch the list themselves as the first step. Note the skip in CHECKPOINT.

**Capture:**
- `[STAGE0]` -- `done` / `skipped`
- `[STAGE0_GAME_TYPE]` -- game-type signal (or `unknown` if skipped)
- `[STAGE0_LOC_CLASS]` -- localization-mechanism signal (or `unknown`)
- `[STAGE0_CATEGORIES]` -- list of present categories (or `unknown`)
- `[ACHIEVEMENT_STUB_COUNT]` -- integer count of fetched achievements (or `unknown` if Stage 0 was skipped, or `0` if the game has no platform achievements -- some indie or older console releases). Recorded in CHECKPOINT for downstream sanity.

**Why a separate file.** `stage0_priors.md` is the canonical artifact the P1 brief generator reads later (Step 8). Keeping it on disk means re-running Step 8 doesn't redo the web search, and the user can correct any wrong inferences before they propagate downstream.

**Default for the first-user test:** yes (run it). The cost is small and it raises the floor on every downstream step.

### Step 7 -- Subfolder shape (REQUIRED)

**Pre-population from Stage 0 (REQUIRED when `[STAGE0] = done`):** read `<game>/research_briefs/stage0_priors.md` and pre-populate the subfolder checklist with the categories Stage 0 marked `present`. Frame the question as "here's what I found -- confirm or correct" rather than "figure this out from scratch."

**Ask** (with Stage 0's suggestions checked, when available):
- "Based on the pre-research, this game has the following content categories. Confirm, edit, or skip and let it emerge during play."
  - [ ] Puzzles / logic challenges (creates `puzzles/`)
  - [ ] Named entities worth aggregating individually -- NPCs, factions, crew roles, reputation systems (creates `npcs/`, `factions/`, `crew/`, or `reputation/` as applicable; facts also route to their primary vector). At `corpus-core-version: 5` and later this replaces the old `enemies/` folder -- named hostile NPCs go to `npcs/` with `entity-status: hostile`; generic-mob combat content continues to route via the `enemy` vector to `mechanics.md` (no folder needed).
  - [ ] Multiple endings worth indexing separately (creates `endings/`)
  - [ ] Branching narrative paths worth indexing (creates `paths/`)
  - [ ] Discrete optional zones (shrines / dungeons / side areas) keyed to parent zones (creates `optional_zones/`)
  - [ ] Systems-heavy game where `mechanics.md` will outgrow a single file (creates `mechanics/` directory split)
  - [ ] Navigation routing (zone-based dungeon layout, points of no return, hub-and-spoke structure) (creates `nav/`)
  - [ ] Items split -- weapons / abilities / upgrades / consumables / cartridges / materials / support / builds (per Stage 0; check those marked present)
  - [ ] Region-based main path with missable collectibles
  - [ ] Other (free-form -- corpus-declared vector extension. Use sparingly; the six canonical extensions above cover the observed game-type space. A corpus-declared extension like `testing_grounds/` is fine for one-off shapes but doesn't get wizard-level support.)

**Capture:**
- Subfolder list to create.
- **Minimal scaffold (always created, regardless of answers):** `items/`, `sections/`, `_overflow/` plus `controls.md`, `settings.md`, and `mechanics.md` at game-folder root. `_overflow/` is the staging area for content that doesn't fit existing folders yet -- see `templates/folder_structure.md` for the collision-based promotion pattern. `controls.md`, `settings.md`, and `mechanics.md` are universal core files at root (per `docs/corpus-format.md` §1).
- **Stage-0-gated files:** `items/<category>.md` files are only created for categories Stage 0 marked `present` (weapons.md, abilities.md, upgrades.md, etc.). No empty stubs for absent categories.
- **Vector extensions** (each created conditionally; the six broadly-applicable extensions per `docs/corpus-format.md` §2):
  - **`puzzles/`** -- when Stage 0 marks puzzles present, or the user checks the box.
  - **`<entity-class>/`** (at `corpus-core-version: 5` and later) -- when Stage 0 §5 flags named-NPC density, faction density, crew-system presence, or reputation-system presence as high (or `yes`), scaffold the matching class folder(s): `npcs/` is the default class for any game with named individual NPCs; `factions/`, `crew/`, `reputation/` are parallel classes for non-individual entity aggregation. Multiple flagged classes get one folder each. Scaffolds `<class>/index.md` from `templates/entity_index.md`; per-entity files are scaffolded later at ingestion time from `templates/entity_summary.md`. For corpora migrating from v4 with an existing `enemies/` folder, that folder is renamed to `npcs/` at ingestion step 2.5 (one-time, mechanical), and existing content gets `entity-status: hostile` annotated on first touch.
  - **`endings/`** -- when Stage 0's game-type signal is branching-narrative or the user checks the box.
  - **`paths/`** -- when Stage 0's game-type signal is branching-narrative, or the user checks the box.
  - **`optional_zones/`** -- when Stage 0's game-type signal is open-world / hub-and-spoke and the user confirms (or checks the box).
  - **`mechanics/`** directory split -- only when Stage 0 marks `cross-system dependency density: high` AND the user opts in; otherwise `mechanics.md` ships as a single root file per the universal-core default.
  - **`nav/`** -- per the nav skip rule below.
- **`nav/`** creation rules: as below.
- **Manifest section:** the wizard writes a `## Hintforge manifest` block into the new corpus's `nav/architecture.md` declaring `corpus-core-version` (use the value declared in [`templates/architecture.md`](templates/architecture.md), never a hardcoded literal), `game-version: "[GAME_VERSION]"`, `game-version-platform: "[GAME_PLATFORM]"`, `game-version-as-of: [GAME_VERSION_AS_OF]`, and `vector-extensions:` listing exactly the extensions created above. The reader's session-start discovery reads this manifest (see [`docs/corpus-format.md`](docs/corpus-format.md) §3). If `nav/` is skipped, the wizard writes the manifest into the corpus root's `architecture_manifest.md` instead.
- **Vector extensions prose section:** alongside the manifest block, the wizard writes a `## Vector extensions` section into `nav/architecture.md` (or `architecture_manifest.md` when nav is absent) with a one-line semantic per extension, populated from the template at [`templates/architecture.md`](templates/architecture.md).
- "Navigation routing" creates `nav/` with a stub `index.md` (from `templates/nav_index.md`) and a scaffold `nav/architecture.md` (from `templates/architecture.md`). Per-zone files (`nav/<zone>.md`) are created later during P2 research ingestion -- not at setup.

**Skip rule for nav/:** do NOT recommend or create `nav/` when the game's game-type label is `narrative-no-nav` (Tetris-likes, pure visual novels, games with no meaningful spatial orientation), or when the game uses a rich in-game map system (`localization-mechanism class: none`) and nav questions are rare enough that per-question web-search covers them. If `[RESEARCH_MODE]` is `handoff` or `deep`, the game-type label may not be known until P1 ingestion -- in that case, defer the nav/ decision to ingestion: skip the `nav/` checkbox at setup, and let the ingestion step create `nav/` only if P1's Architecture Summary classifies the game as nav-bearing. When `[STAGE0] = done`, prefer `[STAGE0_GAME_TYPE]` over deferring -- Stage 0's signal is good enough to drive the nav/ decision at setup.

### Step 8 -- Research preference (REQUIRED -- token-aware; see Principle #13)

**Critical:** the wizard does NOT auto-trigger research. Heavy research can burn 30-50 messages, which would blow a Claude Pro user's 5-hour cap on day one.

**Ask:**
- "Setup is almost done. Want me to research the game now, or save your messages for actual gameplay questions?"
  - **None (default)** -- folder will be mostly empty; I'll look things up as you ask. ~0 messages now.
  - **Minimal** -- 1 top source per category, stub a few claims. ~5 messages. Skips source-diversity floor and non-English sources.
  - **Standard** -- apply the brief's source-diversity floor (3 source classes, non-English when applicable) at one source per class per category; flag conflicts. ~20 messages.
  - **Deep** -- apply the full handoff-brief spec in-house: 5+ sources per topic, exception-finding, mechanism-not-inventory, video transcription, datamining sweep. Spoiler-classification pass still runs after. ~50+ messages. (Only pick this on Max/Team or if you're OK with heavy spend.)
  - **Handoff** -- I write you a research brief to paste into Gemini Deep Research / ChatGPT Deep Research / Perplexity. You bring the results back; I ingest them. ~2 messages here, ~5-10 to ingest results later. Cost externalized off your Pro cap.

**Capture:**
- `[RESEARCH_MODE]` -- one of `none` / `minimal` / `standard` / `deep` / `handoff`
- Stored in `<game>/CHECKPOINT.md` under "Research preferences" so future sessions know what's been done

**Handoff sub-procedure (only if `[RESEARCH_MODE] = handoff`):**

> **Don't declare Step 8 done until the brief files are written.** Step 9 will refuse to print the Step 10 handoff if `<game>/research_briefs/p1.txt` doesn't exist on disk (and `p2.txt` / `p3.txt` if `[RUN_P2]` / `[RUN_P3]` were yes). Capturing `[RESEARCH_MODE] = handoff` in the summary table is not the same as having written the brief; the artifact is the gate.
>
> **How to verify the gate -- per-file Read, never directory enumeration.** Check each brief by known filename: `p1.txt` always; `p2.txt` if `[RUN_P2] = true`; `p3.txt` if `[RUN_P3] = true`. For each, call `Read` on `<game>/research_briefs/<filename>`. A successful Read confirms the file exists; a Read error means the gate fails -- name the missing file and halt before Step 10. Do **NOT** call `Glob('research_briefs/*', path='<game>')` or any directory-listing tool for this gate: Glob returns 0 results when the pattern carries a literal subdirectory prefix relative to `path` (known tool defect), the Bash `ls "...\"` recovery has a Windows trailing-backslash escape bug, and you already know every brief's filename from `[RUN_P2]` / `[RUN_P3]`. Enumeration burns 2-3 turns on fallback attempts and adds no value over reading each known file. Same discipline as Step 9 sub-step 3's "do not enumerate `templates/`" rule -- read by name, never by listing.

1. **Generate the brief.** After Step 9 file-writing completes, write a research prompt to `<game>/research_briefs/p1.txt` AND show it inline in chat. The brief is a one-page research request that works whether the reader is the user themselves, a third party they handed it to, or an external tool with no surrounding context.

   > **Maintainer note.** If the deep-research backend reports Fandom fetch failures, that is expected from cloud-hosted runtimes -- use the Fandom ladder in [`ingestion.md`](ingestion.md), not direct fetch.

   **Stage 0 input (REQUIRED when `[STAGE0] = done`).** Before generating the brief, read `<game>/research_briefs/stage0_priors.md`. The brief MUST hard-code Stage 0's content-categories inventory into a "Content Categories -- research these explicitly" section so the researcher does not have to discover what the game has from scratch. For each category Stage 0 marked `present`, the brief lists the category by name and asks for claim-format-ready coverage. For `uncertain` categories, the brief asks the researcher to confirm presence/absence as part of P1. For `absent` categories, the brief explicitly notes "absent -- do not research" so the researcher does not waste budget. When `[STAGE0] = skipped`, the brief falls back to the generic taxonomy below and the researcher does the category discovery themselves; surface this trade-off to the user when generating the brief.

   **Effort allocation guidance (REQUIRED in every brief).** Include a top-level note: "Architecture Summary (zone graph, chapters, etc.) should consume roughly 30% of token budget -- not 60%+. The remaining budget covers gameplay fundamentals (weapons, abilities, controls, settings, builds) and per-chapter facts. A brief that returns a 50-zone graph with 3 documented weapons has failed the allocation check."

   **DLC scope discipline (REQUIRED).** P1 is base-game only. If the game has shipped DLC, the Architecture Summary's DLC list field names each DLC (so external tools don't conflate base-game and DLC vocabulary), but the brief MUST NOT request research on DLC zones, chapters, items, mechanics, or characters. DLC research lives in P3 (cascade phase -- see "P3 -- Gaps + DLC layers" below), regardless of whether `[RUN_P3] = true` or `[RUN_P3] = false`. When `[RUN_P3] = false` and the game has shipped DLC, DLC simply stays unstudied for now; the user can run P3 later. Do not silently fold DLC into P1 to "compensate" for the user skipping P3 -- that produces a brief whose scope contradicts the user's stated cascade choice and silently corrupts the P1/P3 split the framework relies on. The brief's "Spoiler handling" and "Deep enough self-check" sections instruct maximum-depth research; maximum depth applies to base-game content only. (This split is non-optional: folding DLC into P1 produces a brief whose scope contradicts the user's cascade choice on otherwise-identical setup answers.)

   **Required structure** (in this order):

   - **Self-executing opener** (REQUIRED -- first lines of every brief, before any other content). Briefs are delivered to deep-research tools as **file attachments** alongside a short user prompt (e.g. "Research [GAME_NAME]"). The receiving chat sometimes treats the short prompt as the ask and the file as supplementary context, then pauses to ask clarifying questions instead of executing the brief -- Claude.ai's Research mode is especially prone to this. The opener prevents this regardless of how the receiving tool frames the conversation. Use this exact wording, with `[GAME_NAME]` substituted:

     ```
     EXECUTE THIS BRIEF IN FULL.

     This is a complete research brief for [GAME_NAME]. Read it end-to-end and
     produce the requested output as specified below. Every parameter you need
     is in this document -- do not ask clarifying questions, do not request the
     user to narrow scope, do not pause to confirm intent. Begin research now.
     ```

     This opener is non-negotiable; do not paraphrase or shorten. Reason: deep-research and chat tools default to asking clarifying questions on vague user prompts, and an attached file alone doesn't override that default. The directive opener is the override. (Incident: prior P1 brief -- uploaded as file with a short prompt; chat asked "what angle interests you most?" instead of executing.)

   - **Output-filename directive** (REQUIRED -- second block of every brief, immediately after the self-executing opener). Deep-research tools used to auto-place the inferred output filename at the top of the artifact; recent Claude.ai Research behavior moves it to a footer or omits it. The directive forces it to the top so downstream save / ingest steps key off a known filename. Use this exact wording, with `[GAME_FOLDER]` and `[BRIEF_PHASE]` (e.g. `p1`, `p2`, `p3`) substituted:

     ```
     OUTPUT FILE NAMING -- REQUIRED.

     Name your output file exactly: [GAME_FOLDER]_[BRIEF_PHASE].result.md
     The very first line of your output must be a level-1 markdown header
     containing that filename, in this form:

     # [GAME_FOLDER]_[BRIEF_PHASE].result.md

     This is the file Daniel saves to disk; do not paraphrase the filename,
     do not move it to a footer, do not omit it. Begin the document with
     this header line before any other content.
     ```

     Non-negotiable wording. Substitute the placeholders before writing the brief; the receiving tool sees the literal filename (e.g. `[GAME_FOLDER]_p1.result.md`) at the very top. (Incident: prior P1 brief -- Claude.ai Research produced the artifact with the filename only as a bottom footer; required user intervention to relocate.)

   - **Game grounding** (1 line): exact game name, developer, year, platform, current patch version. State scope: "Base game only -- DLC content is researched separately in P3 (cascade phase)." Name shipped DLC by title so external tools don't conflate base-game and DLC vocabulary, but do not request research on them.

   - **Location/world disambiguation** (mandatory; do this before topic research). List in-game location names that share words across distinct areas -- two "underwater" zones, a base-game and DLC area sharing a theme, repeated faction names. The researcher keeps them strictly separate. Conflating distinct locations is the most common failure mode and silently corrupts everything downstream; surface it up front so the researcher cannot skip it.

   - **Architecture Summary** (required at top of the researcher's output, before any chapter-organized facts):
     - **Game-type label** -- one of: `dungeon-linear` / `hub-and-spoke-with-dungeons` / `open-world-with-distinct-dungeons` / `open-world-explorative-only` / `procedural` / `on-rails` / `narrative-no-nav`
     - **Localization-mechanism class** -- one of: `map-system` / `landmark` / `hybrid` / `none`
     - **Chapter / area / mission list** -- canonical names + alias set + ordering; disambiguation for shared-name pairs (two "underwater" zones, base-game and DLC areas sharing a theme, repeated faction names)
     - **Zone list** -- every navigable zone (chapter, dungeon, polygon, side-area) with canonical zone-id
     - **Chapter ↔ zone mapping** -- which chapter contains which zones (one chapter may span multiple zones; declare each zone-id separately)
     - **Zone graph** -- nodes (zones + hubs) + typed edges; **required for any game where game-type-label ≠ `narrative-no-nav`**. Edge columns: From / To / Type / Direction / Condition / Point-of-no-return / Notes. Types: `story-gate` / `one-way` / `optional` / `hub-spoke` / `fast-travel` / `conditional`. Point-of-no-return subtypes: `permanent` / `chapter-bound` / `missable-trigger` / `point-of-divergence`.
     - **DLC list** -- names only. List each shipped DLC by title. Do not include DLC chapter or zone facts in this brief -- DLC chapter/zone mapping is P3 scope (cascade phase). Stub form: `- <DLC name> -- out of P1 scope; covered in P3.`
     - **Optional content registry** -- cross-zone optional content with unlock conditions, access windows, parent zones, recommended chapter, failure modes (`missable` / `always-available` / `NG+-only`)
     - **Source-language set** -- dev-country language + top-3 player-region languages (used to enforce the non-English source floor below)
     - **Achievement stub count** -- REQUIRED at `corpus-core-version: 4` and later. State the `[ACHIEVEMENT_STUB_COUNT]` from Stage 0 -- the integer count of platform achievements the game ships, captured from the Stage 0 stub fetch and written to `research_briefs/achievement_stubs.md`. The researcher uses this count as the coverage target for Standing prompt #9 (Achievement coverage, below). When `[STAGE0] = skipped`, this field reads "stub list deferred to researcher -- fetch the platform's canonical achievement list as the first step of P1 research." When the game has no platform achievements (`[ACHIEVEMENT_STUB_COUNT] = 0`), state "no platform achievements -- skip Standing prompt #9 and write `achievements.md` at status: research-integrated with the honest empty-statement."
     - **Content categories inventory** -- REQUIRED. For each of the categories below, mark `present` / `absent` / `uncertain` with a one-line rationale and (when present) a coverage estimate (item count or system complexity): `weapons`, `cartridges/ammo`, `consumables`, `crafting_materials`, `abilities`, `upgrades`, `support_items`, `builds`, `controls`, `settings`. When `[STAGE0] = done`, this section is hard-coded from `stage0_priors.md`; the researcher confirms / corrects rather than re-deriving. Categories marked `present` get dedicated coverage in the chapter-organized facts section; categories marked `absent` are explicitly skipped so budget isn't wasted.

   - **Chapter-organized facts** (rest of the researcher's output; after Architecture Summary): per chapter -- 1-2 lines of context, then facts as bullets. Each fact carries: `vector:` tag + `spoiler:` tag + per-fact source attribution. **Vector tag taxonomy** (twelve tags): `nav` (gate/area-traversal) · `puzzle` (solutions, mechanics) · `item` (weapons, consumables, key items) · `boss` (strategies, weaknesses) · `enemy` (non-boss patterns) · `lore` (story beats) · `controls` (keybindings, control remaps -- routes to `controls.md`) · `settings` (graphics/audio/accessibility -- routes to `settings.md`) · `build` (loadout strategies, weapon/ability combinations -- routes to `items/builds.md`) · `structure` (zone-graph edges, optional content registry entries, support topology, locks-and-keys -- integrator routes these to `nav/architecture.md`) · `missable` (overlay tag; combine as `vector: item, missable: yes`) · `mechanic` (FALLBACK only -- game-system rules not specific to one of the above; do not absorb `controls`/`settings`/`build` into this bucket). Standing prompts on every chapter: (1) What do mainstream English guides miss? (2) What exceptions exist to apparent rules? (3) Mechanism not inventory -- *why* and *what triggers*, not just *what is here*. (4) What tapes, documents, weapon schematics, or key items have a limited pickup window? Mark each `missable: yes` with the latest safe chapter. **(5) Builds: what recommended loadouts/playstyles do mainstream guides converge on, and where do they disagree? Cover at least one ability-focused, one weapon-focused, and one hybrid build when the game supports them. (6) Controls: what control remaps (PC keyboard/mouse and controller) are commonly recommended, and why? Include accessibility-rebind discussion when sources cover it. (7) Settings: which graphics/audio/accessibility settings meaningfully affect difficulty or perception? (Motion blur, FOV, HDR, colorblind mode, subtitle behavior, controller deadzones, etc.) (8) Unlock chains -- for every unlockable item (weapon, mod, ability, upgrade, consumable schematic, key item, cosmetic), capture the *complete* acquisition sequence at container-level granularity: the specific container or source (named chest, NPC trade, drop pool, blueprint pickup, quest reward), its tier/state where containers are tiered (bronze/silver/gold chest, common/rare drop, weighted table), the access conditions inside the parent location (which gate / puzzle / sub-zone reached), AND every alternate path if more than one source exists. "X is from Polygon 10" / "X drops in the Forest" is insufficient -- required form is "X is in Polygon 10 silver chest, accessed after the magnetic-platform puzzle" or "X drops from Forest Wolf-variant rare table, ~3% rate." Unlock-chain granularity is structurally absent from item-organized sources (weapon upgrade tables, build guides, gear lists) -- those organize "what does this item do?" not "what is in this container?" The chest-tier / container-tier data lives on location-organized sources (per-dungeon walkthroughs, in-game collection-UI tabs, Fandom location pages, completion-percentage guides). For every unlockable item, route at least one source through a location-organized guide. If a container's tier or sub-location cannot be recovered, mark it explicitly as `[unlock-chain incomplete -- container/tier unknown]` rather than emitting the looser "from location X" form as if complete. Every permutation matters: if a mod can be acquired from Chest A in Zone 10 OR a separate world-pickup in Zone 6, both must be captured. (9) Achievement coverage (required at `corpus-core-version: 4` and later). The corpus's `<game>/research_briefs/achievement_stubs.md` lists every achievement the game ships, fetched at Stage 0 from the platform's canonical list. For each achievement: (a) capture the trigger condition at the same container-level granularity required for unlock chains in Standing prompt #8 -- not "complete the side quest" but "complete side quest X via dialogue branch Y at NPC Z, requires item W from chest in Zone 10 silver tier"; (b) capture the PoNR window if missable -- the latest gate/chapter/scenario beat where the trigger is still reachable; (c) capture prerequisites -- other achievements, items, story flags, build states that must be in place first; (d) flag achievement-name spoilers when the platform's hidden flag is set. Achievement names cited verbatim are acceptable (they're factual lookup keys); developer-authored description text must be paraphrased (publisher IP). The researcher's output must include an "Achievement Coverage" section near the end of the result file listing every stub-file entry with one of three resolutions: **resolved** (paragraph-grade trigger captured with prereqs and PoNR window), **deferred** (entry name + reason, e.g. "DLC-locked, P3 scope" or "online-only, single-player corpus"), or **unreachable** (entry name + what blocked research). DLC scope discipline preserved per the existing P1 brief's DLC rule: DLC achievements stay in P3 scope; the Stage 0 stub fetch captures them but P1's coverage check covers base-game only. The researcher does not need to know the trigger-type taxonomy; classification happens at ingestion (see [`ingestion.md`](ingestion.md) step 8). The researcher's job here is to capture the trigger / PoNR / prereqs / hidden-name-flag for each stub.**

   - **Source diversity floor** (per topic, not per brief):
     - **Minimum 5 independent sources** before any fact is marked confirmed.
     - At least one source from each of three classes: (a) reference wiki, (b) community forum / Reddit / Steam Community guide, (c) video walkthrough or speedrun route (transcribe relevant segments).
     - **Non-English sources required** when the game's developer is non-Anglophone, when the game's primary community is non-Anglophone, or when English coverage is known-thin. Russian StopGame.ru / DTF.ru / VK groups for Russian-developed games; Japanese 2ch / wiki.gg-jp for Japanese; gry-online.pl for Polish; etc.
     - Datamining and modding-community sources (Nexus Mods comments, modder Discords, deep Reddit threads beyond top-voted) when the topic is mechanic-level.
     - Top-3 English search hits are the floor, never the ceiling.

   - **Blocked-source access -- Reddit fetch ladder.** Direct fetches to `www.reddit.com` / `reddit.com` are 403'd or login-walled from automated-research backends because Reddit's anti-bot stack flags datacenter IP ranges and non-browser TLS fingerprints. Reddit is nevertheless a required source class (b) above for many topics: build interactions, edge-case mechanics, "bug or intended" judgments, undocumented late-game behavior, dev-team replies in r/<game>. When a Reddit URL returns 403 / empty / a login interstitial, walk this ladder in order and stop at the first success. **Try each rung exactly once. Do not retry, do not rotate headers, do not chain proxies, do not invoke paid scraping services.** If the whole ladder fails, the source is honestly unreachable -- flag and move on.
     1. `old.reddit.com/r/<sub>/comments/<id>/` -- lighter front-end, fewer client-side gates; often returns content where `www.reddit.com` 403s.
     2. `old.reddit.com/r/<sub>/comments/<id>/.json` -- raw JSON dump of the thread (top-level post, comment scores, OP edits, chain shape). Especially useful when comment scoring or OP follow-ups are load-bearing for the claim.
     3. `archive.ph` / `archive.today` snapshot of the canonical URL. Distinct service from the Internet Archive's Wayback Machine; not affected by Reddit's Wayback block. If no snapshot exists, submit one at `archive.ph` first, wait for completion (usually seconds), then fetch the resulting snapshot URL.
     4. If none of the above succeed, skip the source and explicitly flag it inline: `[Reddit source unreachable -- canonical URL: <reddit.com/...>]`. Do not silently omit; the gap is a data point. If the thread was load-bearing for a specific claim, downgrade that claim's source-attribution to `[Single source -- verify · class:forum]` or `[Hypothesis -- unverified]` depending on whether any other source corroborates.

     **Citation rule:** record the **canonical `reddit.com` URL** in the per-fact source list regardless of which rung actually returned the content. The fetch path is an implementation detail; the canonical URL is what a human reader visits and what downstream deduplication keys against. Do not cite `old.reddit.com` or `archive.ph` URLs as the primary source -- they are workarounds, not provenance.

   - **Output format**:
     - Markdown tables for tabular content (specs, tiers, comparison charts, drop tables, location inventories).
     - Prose for narrative and mechanism explanation.
     - **Per-fact source attribution**, one of: `[Confirmed: N sources, M languages]` / `[Single source -- verify · class:<class>]` / `[Contradicted across sources -- see notes]` / `[Hypothesis -- unverified]`. The `class:<class>` tag on single-source flags records the source's authority class so downstream gap-fill (P3) can decide drop / translate / keep without re-litigating credibility from URL guesswork. Enum: `forum` (user-generated -- Steam Community threads, Reddit posts, Discord) · `community-wiki` (Fandom, gamepedia mirrors, open-edit) · `editorial-en` (English editorial -- GameRant, PC Gamer, Eurogamer, IGN, GamesRadar, Polygon, etc.) · `editorial-non-en` (non-English editorial -- VGTimes.ru, StopGame.ru, DTF.ru, 4Gamer.net, GameWatch.jp, gry-online.pl, etc.) · `datamining` (extracted from game files, mod-exposed internals, modder-Discord deep-dive) · `official-pr` (developer / publisher statements, patch notes, official social).
     - Source URLs at the end of each section, with language and date for each.
     - Text only -- no images.

   - **Spoiler handling -- go to maximum depth; tag, do not omit.** Handoff research is the one chance to get a deep external pass; self-censoring during research permanently loses content. Include everything reachable **within base-game scope**: late-game mechanics, story beats, character fates, faction reveals, boss strategies, ending branches. DLC content is excluded from P1 by the DLC scope discipline above -- it's P3's scope. Spoiler-tier filtering is a separate agent pass run at ingestion time (see "Spoiler classification pass" below) -- the brief's job is to produce raw maximal coverage with per-fact spoiler tags, not to pre-filter.

   - **Per-fact spoiler tag** (mandatory on every fact, fact-level not section-level): one of
     - `spoiler: none` -- mechanics, item names, location names visible from start
     - `spoiler: progression` -- content gated behind early-mid game milestones
     - `spoiler: late-game` -- boss-room contents, late mechanics, faction-reveal-dependent info
     - `spoiler: story` -- narrative beats, character fates, ending branches
     - `spoiler: dlc:<name>` -- content unique to a paid expansion
     Tag at the smallest meaningful unit -- a row in a drop table, a sentence in prose, a single bullet. A section may contain mixed tags; that's expected and correct.

   - **"Deep enough" self-check** (the researcher confirms before declaring the brief satisfied; missing items get noted explicitly rather than silently skipped):
     1. Went past the top 3 hits on every English search.
     2. Checked at least one non-English source per topic when the rule above applies.
     3. Transcribed at least one video segment per topic.
     4. Found at least one fact that contradicts or extends the mainstream English wiki.
     5. Flagged at least one common-knowledge rule that has documented exceptions.
     6. Covered late-game base-game content where it exists; did not stop at the early game. (DLC content is out of P1 scope by the DLC scope discipline -- it's covered in P3.)
     7. Every unlockable item has an unlock chain captured at container-level granularity (specific chest/tier/drop-pool -- not just parent location). Items where only the looser "from location X" form survived sources are explicitly marked `[unlock-chain incomplete]`, not silently emitted as complete. (Standing prompt 8.)

   - **Internationalization rule** -- ≥1 non-English source per chapter area; drawn from the source-language set declared in the Architecture Summary. LLM translation is acceptable; flag translated facts with `[translated from: <lang>]`. "Checked, nothing English missed" is a valid positive finding. Padding with low-quality sources to hit a quota is not.

   **Brief content constraint -- no filesystem paths or save instructions.** The brief is sent verbatim to deep-research tools (Gemini Deep Research, Claude Research, ChatGPT, Perplexity) that have **no filesystem access**. Embedding sandbox-style paths like `<game>/research_inbox/p1/` or instructions like "save output to..." causes those tools to halt and ask "where?" before running the actual research, blocking the handoff. The brief must end after the deep-enough self-check / output format / spoiler handling sections. Filesystem paths, drop-zone meta, and "where to put the result" instructions live ONLY in Step 10's user-facing handoff message -- not in the brief file itself.

   No pronouns referring to "the wizard," "the framework," or "an AI agent" -- the recipient doesn't need that context to act on the request.

2. **Create directories.** Create `<game>/research_briefs/` (for briefs) and `<game>/research_inbox/p1/` (for P1 results). Write a `.gitkeep` in each containing the literal text: `Drop research result files here.` If `[RUN_P2] = true`, also create `<game>/research_inbox/p2/`. If `[RUN_P3] = true`, also create `<game>/research_inbox/p3/`.

3. **Tell the user how to operate the handoff.** Show this verbatim closing message:

   ```
   P1 brief:      <game>/research_briefs/p1.txt
   P1 drop zone:  <game>/research_inbox/p1/

   Recommended tool by your Claude tier:
     Max / Team / Enterprise   Claude Research on claude.ai
     Pro                       Gemini Deep Research (free tier)
     Free / no Claude sub      Perplexity Deep Research (5/day free)

   Steps:
     1. Upload p1.txt to the tool above. The brief is self-executing --
        no clarifying questions needed. If the tool still asks, reply:
        "Execute the brief in the attached file in full. Do not ask
        clarifying questions -- every parameter is in the file."
     2. Save the output to <game>/research_inbox/p1/ as
        <game_folder>_p1.result.md (the filename the brief specifies
        at the top of the artifact).
     3. In a fresh Claude Code session here: "ingest the research".

     Shortcut (claude.ai Max/Team/Enterprise): if you have Research
     mode + the Filesystem connector, paste the brief into a
     Research-mode chat with Filesystem enabled and give it the
     absolute path to <game>/research_inbox/p1/. Result file is
     written directly -- no manual save. Add "don't summarize,
     only put it in the brief file" to keep the chat clean.

   Use a fresh session for ingestion -- it's the largest single context
   load this guide will see. Run P1 ingestion before P2 (P1 creates the
   architecture.md scaffold that P2 extends).
   ```

4. **Mark CHECKPOINT.md** with `Research preferences: cascade-handoff (P1 brief generated YYYY-MM-DD; P2: [generated/skipped]; P3: [generated/skipped]; awaiting results in research_inbox/p1/)` so a fresh session knows where to look.

**Cascade phases (P2 and P3 -- only when `[RESEARCH_MODE] = handoff` or `deep`):**

After P1 brief is generated, explain the optional cascade phases and ask:

> **P2 -- Localization toolkit + support topology + locks-and-keys** (recommended for most games): three coupled outputs that answer "how does the persona reason about player location at runtime?" -- landmark / map prompts for localization, save-point and fast-travel topology per zone, and item-keyed gate annotations on the zone graph. Strongly recommended for dungeon-heavy or landmark-navigated games. Less critical for map-system games (named-region map UI) where named regions are sufficient.
>
> Runtime: once `nav/architecture.md` exists, the persona applies five nav rules (routing, lookahead, backtrack queries, reachability check, locks-and-keys notifications -- see `templates/persona.md`). Lookahead defaults to **N=2 gates forward** from `last_known_gate`; tunable per game in `CHECKPOINT.md` if it fires too early or too late.
>
> **P3 -- Gaps + DLC layers** (recommended if game has shipped DLC): patches thin coverage from P1 and adds DLC zones to the zone graph. Safe to skip initially and run later if in-play sessions surface gaps.

Ask:
- "Run P2? (**recommended** for most games / skip)"
- "Run P3? (yes if game has shipped DLC / **skip**)"

Capture `[RUN_P2]` and `[RUN_P3]`.

**If `[RUN_P2] = true`:** Generate P2 brief to `<game>/research_briefs/p2.txt`. P2 brief requests:
- **Per-zone gate-lists** (one subsection per zone): ordered sequential gates (5-15 per zone, or 5-15 per branch for branching zones); entry / exit / outgoing edges referencing `architecture.md` by edge `(from, to)` pair; optional branches, common confusions, soft-lock warnings, sources. Nav-only -- puzzles and enemies referenced by name as pointers, not solved inline.
- **Support topology augmentation** for `architecture.md`: save stations per zone with in-zone location descriptions; fast-travel network nodes; hub access points.
- **Locks-and-keys table** for `architecture.md`: every item-keyed gate -- lock location (zone + description), key required, key source zone, whether lock is visible before key, notes.
- **Localization toolkit** for `nav/localization.md` -- **only when P1's `localization-mechanism class` is `landmark` or `hybrid`; skip for `map-system` and `none`.** Per zone: 3-6 distinctive in-game landmarks (statues, signage, equipment, environmental hazards, named save-points) that uniquely resolve to that zone, with disambiguation notes for landmarks that look similar across zones. Plus a short list of game-appropriate ask-the-player prompts for when CHECKPOINT's `player_position.confidence` drops below `high` ("what's the last big landmark you remember?", "which save-point did you last use?", etc.). For `hybrid` games, also list map-element prompts ("what region does your map show?") for zones that have map coverage.

Drop zone: `<game>/research_inbox/p2/`. Ingest P1 before P2 -- P1 creates the `architecture.md` scaffold that P2 extends.

**If `[RUN_P3] = true`:** Generate P3 brief to `<game>/research_briefs/p3.txt`. Scope explicitly: list the thin chapters from P1 results and any DLC zones. Same cascade output shape as P1 (Architecture Summary section for DLC-introduced zones + chapter-organized vector-tagged facts). DLC-introduced zone nodes and edges extend the zone graph; DLC-keyed locks extend the locks-and-keys table.

**Gap-fill rubric for prior-phase `[Single source -- verify · class:<class>]` flags** -- the P3 brief must instruct the researcher to decide drop / keep / rewrite per item based on source class, not by uniform "is there a 2nd English source" treatment:

- `class:forum` / `class:community-wiki` → drop unless a 2nd independent source confirms during P3 research.
- `class:editorial-en` → keep with caveat unless directly contradicted by a higher-credibility source.
- `class:editorial-non-en` → **translate the original source verbatim before deciding.** Do not drop solely because no English source corroborates -- the cascade's internationalization rule explicitly expects non-Anglophone editorial sources (RU / JP / PL / etc.) to carry mechanics English coverage misses, especially for non-Anglophone-developed games. Quote the relevant claim text from the original-language source and assess on the underlying mechanic, not the English-sourcing gap. If the original-language claim looks like a localization-conflation candidate (e.g. Russian "матка"/queen mapped onto an existing entity rather than a unique one), the resolution is partial-drop / rephrase, not full drop.
- `class:datamining` → keep with caveat; high credibility on internals.
- `class:official-pr` → treat as ground truth.

If the original P1 / P2 brief did not stamp source-class (pre-v24 briefs predate this taxonomy), the researcher infers from the URL host on the source citation and proceeds with the rubric above.

Drop zone: `<game>/research_inbox/p3/`.

---

**Ingestion procedure** runs in a **fresh session** (per Step 10's handoff message) when the user types "ingest the research" or attaches a result file. The procedure lives in [`../hintforge/ingestion.md`](ingestion.md) -- its own file so the ingestion session loads only what it needs, not the wizard's first-run setup steps. Briefs are written here at setup; ingestion runs there later.

**Note for the user:**
- The default `none` is fine. You can run research later by saying "research the puzzles" / "research everything you can" / etc.
- Per-question research happens automatically and is cheap (1-3 messages per question) -- that's normal use.
- Pick `handoff` if you have access to a separate deep-research tool (Gemini, ChatGPT, Perplexity) and want to spend its tokens instead of yours.

### Step 9 -- Confirmation + execution (REQUIRED)

**Show the user a summary of all answers before doing anything. This summary is the enforcement gate for the "every step done or asked" rule -- every variable below must have a real value or the explicit string `skipped (user choice)`. The string `[unset]`, `[unknown]`, or a placeholder like `[PLAYER_NAME -- fill in later]` means you skipped a step; back up and ask.**

**Source annotation:** values pre-filled from `setup_answers.txt` are tagged `(from setup_answers.txt)` so the user can catch typos in the file. Values answered live (popup, batched list, or chat) are unannotated -- telling the user "you typed this in the popup" is noise.

```
About to set up:
  Game name:        [GAME_NAME]
  Folder name:      [GAME_FOLDER]
  Platform:         [GAME_PLATFORM]                                       ← Step 1
  Game version:     [GAME_VERSION]                                        ← Step 1
  Version as of:    [GAME_VERSION_AS_OF]                                  ← Step 1 (auto, today's date)
  Workspace root:   [WORKSPACE_ROOT]         (from setup_answers.txt)
  Player name:      [PLAYER_NAME]            (from setup_answers.txt)     ← Step 1.5
  Save dir:         [SAVE_DIR]               (from setup_answers.txt)     ← Step 3 (often "skipped")
  Game install:     [GAME_INSTALL_DIR]       (from setup_answers.txt)     ← Step 3 (often "skipped")
  Enemy tier:       [ENEMY_TIER]             (from setup_answers.txt)     ← Step 4
  Puzzle tier:      [PUZZLE_TIER]            (from setup_answers.txt)     ← Step 4
  Persona 1:        [PERSONA1]                                            ← Step 5 (or "none")
  Persona 2:        [PERSONA2]                                            ← Step 5 (or "none")
  Default persona:  [DEFAULT_PERSONA]                                     ← Step 5 (or "none")
  TTS enabled:      [TTS_ENABLED]            (from setup_answers.txt)     ← Step 6
  TTS style:        [TTS_STYLE]              (from setup_answers.txt)     ← Step 6 (or "n/a")
  PTT enabled:      [PTT_ENABLED]            (from setup_answers.txt)     ← Step 6.5
  PTT hotkey:       [PTT_HOTKEY]             (from setup_answers.txt)     ← Step 6.5 (or "n/a")
  Stage 0 priors:   [STAGE0]                                              ← Step 6.7 ("done" / "skipped")
  Achievement stubs:[ACHIEVEMENT_STUB_COUNT]                              ← Step 6.7 (integer / "0" / "unknown" if Stage 0 skipped)
  Subfolders:       [list]                                                ← Step 7
  Manifest:         [nav/architecture.md | architecture_manifest.md]      ← Step 7 (root file if nav skipped)
  Research mode:    [RESEARCH_MODE]          (from setup_answers.txt)     ← Step 8
  Run P2:           [RUN_P2]                 (from setup_answers.txt)     ← Step 8 (n/a if research ≠ handoff/deep)
  Run P3:           [RUN_P3]                 (from setup_answers.txt)     ← Step 8 (n/a if research ≠ handoff/deep)

Proceed? (yes / no / edit)
```

(Example shows a partially-pre-filled run. Live-only runs have no tags; fully-pre-filled runs tag every batchable line.)

If the user picks `edit`, ask which line to change and re-run that step. If any line shows a literal `[VARIABLE]` token instead of a value, do not present this summary -- the wizard isn't done. Go back to the missing step.

**Context-pressure failsafe -- check before any file writes.** Before running sub-steps 1-12 below, estimate remaining context headroom. Rough heuristic: how many files were read this session (a Stage 0 pre-research pass that pulled 20+ wiki pages eats a lot), how long the persona-research transcript ran, whether any sub-step looped or re-asked, whether `[RESEARCH_MODE] = deep` queued large research output. If headroom looks insufficient to safely complete the file writes + brief generation + the sanity scan + the handoff message, **stop and hand the user a recoverable resume prompt rather than proceeding into post-compact writes** (per [`compaction_policy.md`](compaction_policy.md) -- setup is UNEXPECTED-compaction, post-compact scaffolding is structurally fragile).

The handoff:

1. Print the entire "About to set up:" summary table above to chat (with all variable values filled), clearly marked as the resume payload.
2. Print a one-block resume prompt the user can paste into a fresh session at the workspace root:

   > **Resume hintforge setup.** A prior setup session for `[GAME_NAME]` (folder `[GAME_FOLDER]`) stopped before file writes to avoid post-compact damage. The captured parameters are in the summary table above. Re-run the wizard with those parameters pre-confirmed (treat the summary as if the user already answered `yes` to "Proceed?") and continue from sub-step 1 of Step 9's execution list (create the folder, copy templates, scaffold subfolders, etc.).

3. Stop the current session. Do NOT print the Step 10 handoff message; the wizard isn't done.

This failsafe is broader than compaction. If earlier steps fell apart for any reason -- looping research, scope creep, repeated re-asks, persona-research transcript bloat, accidental large reads -- the same handoff applies. Setup must remain recoverable from arbitrary mid-procedure context exhaustion; the summary table is the recovery checkpoint. The Sonnet-minimum + extended-thinking-OFF rule + `[RESEARCH_MODE] = handoff/none` defaults exist partly to make this failsafe rarely needed, but the failsafe exists for the cases where they're not enough.

If yes (and headroom is sufficient), the AI agent:
1. Creates `[WORKSPACE_ROOT]/[GAME_FOLDER]/`
2. **Extracts `[HINTFORGE_VERSION]` from `hintforge/CLAUDE.md`.** Read the second line of that file and pull the version token via the regex `v(\d+)`. Set `[HINTFORGE_VERSION]` to the matched `v<N>` string (e.g. `v14`). If the file is missing, the line is malformed, or the regex doesn't match, fall back to `v?` and warn the user once: *"Couldn't read the hintforge framework version -- your guide will be stamped `v?`. File an issue at github.com/hintforge/builder so we can fix the framework."* Don't block setup. The breadcrumb is set once at instantiation and is never updated by future framework version bumps.
3. Copies + fills templates from `hintforge/templates/`:

   > **Do not enumerate `templates/`.** Read each template by name as listed in this sub-step (`claude_md.md`, `checkpoint.md`, `persona.md`, `warning_tiers.md`, `limitations.md`, and the universal-core files referenced in sub-step 4). Do NOT call `Glob('templates/**/*', path='<skill-root>')`, `Bash(ls templates/)`, or similar enumeration steps -- the template list is fixed by this spec, not discovered at runtime. The Glob tool also does not resolve patterns with a literal subdirectory prefix relative to `path` (e.g. `templates/*.md` with `path='<skill-root>'` returns zero results); if a future step legitimately needs to list a subdirectory, set Glob's `path` argument to that subdirectory directly and use `*.md` or `**/*.md` as the pattern, or use PowerShell `Get-ChildItem`. Enumeration-via-Glob in this step burns 2-3 turns on fallback attempts (Bash `ls` has a Windows trailing-backslash escape bug; PowerShell `Get-ChildItem` works) and adds no value over the named-list approach.

   > **Literal-path discipline.** When copying any template, the strings `../../hintforge/` are **literal content**, not placeholders to resolve. Do NOT substitute them with absolute paths (e.g. `C:\Users\<name>\.claude\skills\hintforge\` or `~/.claude/skills/hintforge/`), even when the wizard is running from an installed-skill location. The skill base directory is metadata for `Read` operations, never a path source for content written into the guide. Published per-game guides must reference the framework via relative path so cloned repos remain portable on machines that don't have the maintainer's skill install. Only `[BRACKETED_PLACEHOLDERS]` get substituted; everything else in templates is verbatim content. Same discipline class as the v33 `[WORKSPACE_ROOT]` cascade -- both surfaces enforce "skill base is read-only metadata."
   >
   > **Incident reference.** A prior wizard run transformed `../../hintforge/templates/claim_format.md` in CLAUDE.md line 12 into an absolute path like `C:\Users\<name>\.claude\skills\hintforge\templates\claim_format.md`, baking the maintainer's username + skill-install path into a guide that's supposed to be cleanly publishable. A parallel run on the same input copied verbatim. Non-deterministic. The sanity scan in sub-step 11 catches this post-write.
   >
   > **Literal-prose discipline (the player's name is not a slot).** The phrase "the player" in templates is **verbatim content, not a slot.** Do NOT substitute `[PLAYER_NAME]` for it anywhere in prose, headings, or section titles. The ONLY place the player's name is written is `CHECKPOINT.md`'s `**Name:** [PLAYER_NAME]` field (the single sanctioned `[PLAYER_NAME]` insertion site). Every other "the player" stays literal -- substituting it binds the guide to one player and is the prose analogue of the absolute-path leak above. The sub-step 11 player-name scan catches strays post-write.

   - `claude_md.md` → `<game>/CLAUDE.md` with **`[BRACKETED_PLACEHOLDERS]` filled** (including `[HINTFORGE_VERSION]` from the previous step -- line 3 of the rendered file is the framework breadcrumb, immutable). `../../hintforge/` references stay verbatim per the discipline rule above.
   - `checkpoint.md` → `<game>/CHECKPOINT.md` (records research preference)
   - `persona.md` → `<game>/persona.md` (**unconditional** -- see Step 5 branch logic. Branch A: copy `templates/persona.md` and fill `[PERSONA1]`/`[PERSONA2]`/`[DEFAULT_PERSONA]`. Branch B: write the inline plain-assistant body verbatim from Step 5 Branch B; do NOT copy `templates/persona.md` for this branch. Skipping the file is a bug.)
   - `warning_tiers.md` → `<game>/warning_tiers.md` with the chosen tiers
   - `limitations.md` → `<game>/limitations.md`
4. Creates the minimal scaffold + chosen subfolders:
   - **Always created:** `items/`, `sections/`, `_overflow/` (each with a stub `index.md`); `controls.md`, `settings.md`, `mechanics.md`, `achievements.md`, **`persona.md`** at game-folder root (seeded from Stage 0 priors when `[STAGE0] = done`, otherwise minimal stubs noting "populate via per-question lookup or research"; `persona.md` body per Step 5 branch logic -- unconditional). `achievements.md` is copied from [`templates/achievements.md`](templates/achievements.md); the Stage 0 stub-fetch sub-step (Step 6.7 sub-step 4) populates its body when `[STAGE0] = done`, otherwise it ships with the empty scaffold and the P1 brief instructs the researcher to fetch the list as the first step. Required at `corpus-core-version: 4` and later -- see [`docs/corpus-format.md`](docs/corpus-format.md) §1.
   - **`sections/` also gets two deferred-scaffold aggregation targets:** `sections/missables.md` (from [`templates/sections_missables.md`](templates/sections_missables.md)) and `sections/story_notes.md` (from [`templates/sections_story_notes.md`](templates/sections_story_notes.md)). Both ship with `status: scaffold` + `deferred-to: P1` + `deferred-reason:` frontmatter so the coverage check in [`ingestion.md`](ingestion.md) step 8 sees them at scaffold-with-deferral (a valid state) and knows ingestion's aggregation rules need to populate them OR write honest empty-statements per the step 8 template table. Pre-creating the files makes the aggregation targets impossible for the ingestion agent to overlook -- the file's presence is itself the prompt.
   - **`mechanics.md` seeding from Stage 0.** Per `docs/corpus-format.md` §1, `mechanics.md` is a universal file at root -- same shape as `controls.md` and `settings.md`. When `[STAGE0] = done` and pre-research surfaces phrases like "mechanic-driven", "physics-based", "systems-heavy", "puzzle mechanic", "stat tracking", "stamina", or names specific systems (heat, evasion, ship power, dialogue weight, affinity, etc.), pre-populate `mechanics.md` with a section header per named system at `status: scaffold` so ingestion has clear write targets. For games Stage 0 classifies as `narrative-no-nav` with no surfaced systems, pre-populate `mechanics.md` at `status: research-integrated` with the explicit one-line statement: "no system-level mechanics -- pure narrative; routing/locks/keys live in `nav/architecture.md`". When `[STAGE0] = skipped`, scaffold `mechanics.md` with a minimal stub and let ingestion populate it. The optional `mechanics/` subdirectory split (see corpus-format.md §1) is a maintainer-time decision triggered by content overflow, not a wizard-time choice -- the wizard always creates the single-file form.
   - **Stage-0-gated:** for each item category Stage 0 marked `present`, create `items/<category>.md` (e.g. `items/weapons.md`, `items/abilities.md`, `items/upgrades.md`). Skip absent categories -- no empty stubs.
   - **Other subfolders from Step 7:** `puzzles/`, `nav/`, game-specific `[areas]/` per the user's confirmed Step 7 selection
5. If `[SAVE_DIR]` provided: scaffolds `<game>/save_watcher.py` from the documented pattern
6. If TTS enabled and Windows: scaffolds `<game>/.claude/tts_hook.ps1`
7. Adds the project to the workspace ledger (`<WORKSPACE_ROOT>/CLAUDE.md`)
8. **Only if `[RESEARCH_MODE]` ≠ `none`:** runs the chosen research bundle (in-house) or generates the handoff briefs (handoff mode), announcing each URL or brief file as it's written. For in-house modes (`minimal` / `standard` / `deep`) stops when the budget is consumed.
9. **Brief-artifact gate (handoff/deep modes only).** If `[RESEARCH_MODE]` is `handoff` or `deep`, verify on disk that `<game>/research_briefs/p1.txt` exists and is non-empty. If `[RUN_P2]` is yes, verify `<game>/research_briefs/p2.txt`. If `[RUN_P3]` is yes, verify `<game>/research_briefs/p3.txt`. **If any required brief is missing, do NOT print the Step 10 handoff message. Stop and report the missing artifact, then back up to the brief-generation sub-procedure of Step 8.** A handoff-mode setup that doesn't ship a P1 brief has not completed Step 8 even if the Step 9 summary table looks fully filled -- the variable-must-have-value enforcement catches missing answers but not missing artifacts; this gate catches the latter.
10. **Update `## Phase state` in CHECKPOINT.** Set `setup: complete YYYY-MM-DD`. If P1 brief was generated (sub-step 8), set `p1_brief: written YYYY-MM-DD`. If P2/P3 briefs were generated, set their fields likewise. All other fields remain at their template defaults (`not started` / `not run`).
11. **Post-write sanity scans (required gate).** Two scans run after all template Writes complete and before the Step 10 handoff -- an absolute-path scan (v37) and a player-name scan (v65). Either failing blocks the handoff.

    **Absolute-path scan.** Read `<game>/CLAUDE.md` and scan for any of these absolute-path patterns: `C:\Users\`, `/Users/`, `/home/`, `~/.claude/`, `.claude/skills/`. If any pattern matches, **the wizard has not completed sub-step 3's literal-path discipline** -- stop, do NOT print the Step 10 handoff message. Surface every match to the user with file + line number, e.g.:

    > ⚠️ Absolute-path leak detected in `<game>/CLAUDE.md`:
    >   line 12: `C:\Users\<name>\.claude\skills\hintforge\templates\claim_format.md`
    >   line 34: `C:\Users\<name>\.claude\skills\hintforge\`
    >
    > These should be `../../hintforge/...` (relative). Rewriting now.

    Then rewrite the offending lines using the relative form (`../../hintforge/<path>`) and re-scan. If a second scan still surfaces matches, escalate to the user with: *"Couldn't resolve the absolute-path leak automatically. Please file an issue at github.com/hintforge/builder with the contents of your generated CLAUDE.md."* Don't block setup at this point -- the guide will work locally, it just isn't cleanly publishable. Note the leak in `<game>/CHECKPOINT.md` under a "Setup warnings" line so the maintainer can fix before any publish flip.

    The absolute-path scan covers `CLAUDE.md` only -- other generated files (CHECKPOINT.md, persona.md, warning_tiers.md, limitations.md) don't reference framework paths.

    **Player-name scan (corpus-wide).** After all writes, scan every wizard-authored corpus file for the literal `[PLAYER_NAME]` value occurring **outside** `CHECKPOINT.md`'s `**Name:**` field. Templates use the literal phrase "the player" and are already name-neutral, so any baked-in name is an unsanctioned substitution (see the Literal-prose discipline note in sub-step 3). Surface each hit with file + line number -- same escalation shape as the absolute-path branch above -- then rewrite the offending occurrence back to "the player" before printing the Step 10 handoff. The player's name belongs in exactly one place, the `**Name:**` field; a guide that bakes one player's name into prose, headings, or section titles is bound to that player and isn't cleanly shareable.

12. **Manifest-artifact gate (required gate).** After all template Writes complete, verify on disk that EITHER `<game>/nav/architecture.md` OR `<game>/architecture_manifest.md` exists and contains a `corpus-core-version:` line. Read the file by its known path -- per the nav decision, `nav/architecture.md` if `nav/` was created, `architecture_manifest.md` if `nav/` was skipped (same read-by-known-name discipline as the brief gate; do NOT enumerate the directory). If neither exists, **the manifest write was skipped -- do NOT print the Step 10 handoff message. Stop, report the missing manifest, and write it now** from [`templates/architecture.md`](templates/architecture.md) into the correct location. A nav-skip setup that ships no manifest has not completed the Step 7 Manifest section even if the Step 9 summary looks complete -- same "the artifact is the gate" discipline as the brief gate and the absolute-path scan above. The reader's session-start discovery reads this manifest; without it the corpus has no machine-readable core-version / game-version.

13. Prints the setup-complete message + fresh-session handoff (see Step 10).

**Output formatting -- backtick filenames and paths.** When the wizard prints any "what was installed" recap or refers to created files in chat, every filename and path must be wrapped in backticks: write `` `CLAUDE.md` `` and `` `.claude/settings.json` ``, not bare `CLAUDE.md` or `.claude/settings.json`. Reason: Claude Code's chat renderer (and several other markdown renderers) auto-linkifies bare `name.ext` strings as if they were domain names -- `CLAUDE.md` becomes a clickable `http://CLAUDE.md` link in the rendered output, which is broken and confusing for non-tech users. Backticks defuse the auto-linkifier. The same rule applies to file tables: wrap each filename cell in backticks.

### Step 10 -- Fresh-session handoff (REQUIRED -- show verbatim at end of setup)

After the files are written, the wizard's final message to the user is the handoff below. Don't paraphrase, don't shorten -- non-tech users need the full explanation or they'll keep going in the same session and hit a confusing "compacting…" pause mid-gameplay.

**Required blocks (self-verify before sending) -- the handoff MUST contain all of these, in order; do not omit any of (a)-(h), and do not shorten the message for runs that "look experienced":** (a) the "Setup complete" line; (b) the compacting explainer; (c) the "start inside the guide's folder" paragraph; (d) the **In Claude Code Desktop** block; (e) the **In Claude Code (CLI)** block; (f) the paste-this-if-unsure line; (g) the "Have fun, [PLAYER_NAME]." sign-off; (h) the **What was built** table (built deterministically -- see below). Keep folder references literal: the phrase is "not the hintforge folder or your Documents folder" -- do not improvise variants like "sandbox folder."

> ✅ Setup complete! Your guide for **[GAME_NAME]** is ready at `[WORKSPACE_ROOT]/[GAME_FOLDER]/`.
>
> **One important next step: please close this chat and start a brand-new one before you start playing.**
>
> Here's why: walking through this setup used up a chunk of this chat's "memory" (the space the AI uses to keep track of what you're doing). If we keep going in this same chat, sooner or later the AI will pause to do something called **compacting** -- basically squishing the older parts of our conversation down to a summary so it can keep going. Compacting works fine, but it takes a minute, it can lose small details, and it's an annoying interruption right when you're trying to play.
>
> A fresh chat starts with a clean memory and reads only your finished guide files -- no setup baggage. Everything we just set up is saved to your disk; the new chat will pick it all up automatically.
>
> **What to do -- and this part matters:** start the new chat **inside the guide's folder**, not the hintforge folder or your Documents folder. That way the AI automatically picks up your guide's instructions and your tier/persona settings without you having to explain anything.
>
> **In Claude Code Desktop:**
> 1. Close this chat (or just hit the "New chat" / + button).
> 2. Before sending your first message, look for the folder/working-directory selector (usually near the top of the chat or in the chat's settings) and point it at: `[WORKSPACE_ROOT]/[GAME_FOLDER]/`
> 3. Then say something like: *"I'm ready to play [GAME_NAME] -- what should I know to get started?"*
>
> **In Claude Code (CLI):** `cd` into `[WORKSPACE_ROOT]/[GAME_FOLDER]/` and run `claude` from there. The new session will read the guide automatically.
>
> If you're not sure how to switch folders, just paste this into the new chat and the AI will help: *"Please open the folder `[WORKSPACE_ROOT]/[GAME_FOLDER]/` and read the CLAUDE.md there -- that's my guide for [GAME_NAME]."*
>
> Have fun, [PLAYER_NAME].
>
> ---
>
> 📦 **What was built** -- the files now in your guide folder:
>
> | File / folder | What it's for |
> |---|---|
> | `CLAUDE.md` | The guide's instructions -- the AI reads this first, every session. |
> | `CHECKPOINT.md` | Tracks where you are and what you've done; updates as you play. |
> | `persona.md` | How the AI talks to you (voice / character settings). |
> | `warning_tiers.md` | Your spoiler-control settings. |
> | `limitations.md` | What this guide does and doesn't cover. |
> | `controls.md` | Controls reference. |
> | `settings.md` | Recommended game settings. |
> | `mechanics.md` | How the game's systems work. |
> | `achievements.md` | Achievement / trophy reference. |
> | `items/` | Item, weapon, and equipment notes. |
> | `sections/` | Area-by-area walkthrough notes. |
> | `_overflow/` | Staging area for notes that don't fit elsewhere yet. |
> [+ one row per optional folder this setup created -- see the canonical descriptions below the handoff]

If `[PLAYER_NAME]` was skipped, drop the trailing comma+name. If the bot is running somewhere without a "new chat" / per-folder concept, substitute the equivalent action for that environment.

**Building block (h) -- the "What was built" table -- deterministically.** The rows above (the core files plus the always-created `items/`, `sections/`, `_overflow/` folders) are fixed and ship in every run. Append exactly one row for each optional top-level entry this setup actually created in sub-step 4, in scaffold order, using the canonical descriptions below so two runs of the same game produce identical tables. Do not free-compose descriptions, do not list entries that weren't created, and roll nested files (e.g. `items/weapons.md`) up under their parent folder row rather than listing each:

- `nav/` -- Navigation and map routing for the game's areas.
- `puzzles/` -- Puzzle solutions and hints.
- `endings/` -- Branching endings and how to reach them.
- `paths/` -- Branching story paths and the choices behind them.
- `optional_zones/` -- Optional areas and side content.
- `npcs/` / `factions/` / `crew/` / `reputation/` -- Named characters and the groups they belong to.
- `mechanics/` (folder form) -- Detailed per-system mechanics notes.
- `save_watcher.py` -- Auto-detects your latest save so the guide knows your progress.

Keep every filename in backticks (per the output-formatting rule above). The table is block (h) of the required-blocks checklist -- present in every run, never optional.

#### Stale-session detection (runs at session entry, not first-time setup)

When a fresh session opens on a guide that's already set up -- i.e., `<game>/CHECKPOINT.md` exists for the game and the wizard is not running first-time setup -- the AI bot reads `CHECKPOINT.md` first (per Principle #9) and checks the `Last played:` field. If `Last played` is more than **30 days** before today's date, the bot offers a controls refresher before resuming gameplay assistance:

> It's been [N] days since you last played [GAME_NAME]. Want a quick refresher on the controls and where you left off, or just dive back in?

**Default if the user gives no answer or an unclear one: yes (run the refresher).** Better to spend ~30 seconds re-orienting a returning player than to drop them into a context they've half-forgotten.

The refresher reads:
- `CHECKPOINT.md`'s `Status` and `Open threads` sections -- the where-you-left-off summary.
- The per-game controls reference (`controls.md` or equivalent -- file name varies by game; pick whichever the guide uses).

The bot summarizes both in plain language ("You were in [LOCATION] working on [OPEN THREAD]. Controls: [...]") and asks the user to confirm before continuing into normal gameplay assistance.

If `CHECKPOINT.md` lacks a `Last played:` field -- typically because the guide was set up before the field was added, or the user hasn't played yet -- treat as not-stale and skip the check. The check only fires when the field is present and the date is older than 30 days. The user (or any session) updates `Last played:` when they end a play session, the same way `Last updated:` is bumped when CHECKPOINT is rewritten.

## Last-mile fallbacks

The "last mile" is anything game-specific the AI agent doesn't have data on. Design principle: **the framework doesn't have to ship pre-baked content for every game.** When the user asks about a specific puzzle / item / location and the per-game guide is empty:

1. The AI agent says: "I don't have content for this yet. Let me look it up."
2. Fetches sources, applies the principles (cite sources, hint ladder, spoiler tier).
3. Writes the structured claim into the appropriate per-game file.
4. Answers the user's original question.

This is normal use, not a wizard step. The wizard scaffolds the empty house; gameplay fills it in.

## Open implementation questions

These are unresolved questions for the future installer milestone. The wizard spec above is bot-agnostic enough that any installer mechanism can implement it.

- **Installer mechanism:** Claude Code skill? Python CLI (`hintforge-init`)? Slash command? GitHub template repo with a setup script?
- **Multi-game in one workspace:** if the user already has 3 game folders, does the wizard offer to update tiers across all of them? (Probably not -- per-game tiers are deliberately independent.)
- **Re-running the wizard for an existing game:** does it overwrite, refuse, or offer a "reconfigure" mode? (Probably "reconfigure": preserve content, update tier/persona/TTS only.)
- **OS detection:** how does the wizard know the OS? `os.name` in Python is universal; `process.platform` in Node; relying on the AI agent's environment introspection is simpler if the agent knows.
- **Saving wizard answers:** should the answers persist (so re-running is non-destructive)? Probably a `<game>/setup_answers.json` for re-config purposes.

## Iteration

This wizard spec is v1. The next per-game instantiation will surface gaps -- questions we forgot to ask, defaults that were wrong for the user's actual preferences. Revise here; contributors can open a PR with the change.

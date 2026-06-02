# Distribution Model -- GitHub-First

Long-term vision. The current implementation treats per-game guides as local folders the bot reads on every session. Everything below is **not yet built** -- captured so future work has a reference target and today's templates encode the right constraints.

## The vision

Players play. Players with AI agents push their guide commits to a per-game GitHub repo. An aggregator agent merges contributors' commits and decides percentage-based truth per claim. Static HTML wikis generated off the canonical repo replace traditional fan-wiki sites.

## Why this matters

Current fan wikis (Fandom, IGN, etc.) suffer from:
- **Spoiler firehose by default** -- no spoiler controls; everything dumped on page-load.
- **Single-editor truth** -- first contributor wins, even when wrong; corrections take social capital.
- **Stale at scale** -- popular games get 100s of edits in week 1, then nothing for years.
- **Ad-laden, slow, ugly** -- UX hostile to actual reference use.

A hintforge-style guide flips all four:
- **Tier-aware** -- reader sets two independent dials (enemy-tier 0-5, puzzle-tier 0-3); rendered output filters claims accordingly.
- **Multi-contributor consensus** -- facts weighted across contributors; percentage-of-truth surfaced.
- **Live verification** -- contributor agents push fresh observations from their own save state.
- **Static HTML, no ads** -- generated off the canonical repo.

## Architecture sketch (subject to change)

```
[Player A's local guide]  ──┐
[Player B's local guide]  ──┤  fork/PR  ──> [Central per-game GitHub repo]
[Player C's local guide]  ──┘                       │
                                                    │  aggregator agent reads commits,
                                                    │  weighs claims by source +
                                                    │  contributor track record
                                                    ▼
                                       [Canonical guide repo]
                                                    │
                                                    │  wiki generator reads claims,
                                                    │  filters by reader's enemy + puzzle tiers
                                                    ▼
                                       [Static HTML wiki site]
```

## Open architectural questions

These are real research-level questions. None have committed answers yet.

### Authentication
How do we verify a contributor isn't a bot or troll?
- Initial cheap answer: GitHub identity (commits signed by the GitHub account).
- Long-term: maybe signed save-state hashes prove the contributor actually played the game.
- Open: how do we handle a contributor whose AI agent hallucinated a claim?

### Contribution model: PR vs. fork
- **PRs** are auditable but high-friction; aggregator reviews each.
- **Forks** are low-friction but the aggregator must do more work to find divergent claims.
- Probably a hybrid: contributors fork freely; the aggregator pulls forks periodically and emits a "merged canonical" branch.

### Conflict resolution / claim weighting
When two contributors disagree on a fact, who wins? Probably **the one with the better source** -- but encoding "better source" mechanically requires:
- A source-quality lattice (live observation > known wiki > comment > vibes)
- A contributor track record (claims they made that survived contradiction → reputation)
- A confidence field on every claim
- A conflicts-with field linking contradictory claims

`templates/claim_format.md` has v1 of this. Will need real-world iteration.

### Game-version drift
A fact true in v1.0 may be false in v1.5 (patches, balance changes, content additions). Every claim should be tagged with the game version it was verified against. The aggregator can:
- Surface only claims verified at-or-near the reader's game version
- Flag claims older than N versions for re-verification

### Spoiler discipline upstream (CRITICAL)
If Contributor A pushes a spoiler-laden commit, the aggregator must NOT propagate it into the spoiler-free canonical guide. Required:
- Every claim tagged with its `enemy-tier` (0-5), `puzzle-tier` (0-3), and `category` (`mainline` / `easter-egg` / `lore`) -- matches `templates/claim_format.md`.
- Every section tagged with the minimum tiers required to read it (one threshold per dial).
- Aggregator-side filtering: a claim renders only if the reader's enemy-tier ≥ the claim's enemy-tier AND the reader's puzzle-tier ≥ the claim's puzzle-tier; lore-category claims are hidden unless the reader has explicitly opted in.

This is the single largest risk to the multi-contributor model. Solve in template evolution before opening repos to outside contributors.

### Contributor weighting
Does a long-time accurate contributor's claim outweigh a first-timer's? If yes:
- How do we measure accuracy? (Claims they made that survived contradiction.)
- How do we prevent gaming? (Sock-puppets that all agree won't help if claims still need source-quality evidence.)
- Does weighting compound? (A new contributor who mirrors a trusted contributor's claims -- do they get free reputation?)

## Concrete first steps

Three coupled deliverables -- publish, install, auto-research:

### Publish hintforge to a public GitHub repo
1. Scrub-check that no specific-game references remain in shared docs.
2. Add a top-level `README.md` aimed at non-technical readers (what hintforge is, the user-test entry path, the trust/transparency promise).
3. Push a public repo. Solo contributor, no aggregator yet.

### Turnkey installer for the wizard
The acceptance bar (the "first-user test"): a non-technical user receives a single pastable natural-language message from someone they trust, pastes it into their Claude Desktop, and gets a working tier-aware guide for an arbitrary game. No terminal. No UAC. No Python install. No covert behavior. See [`setup_wizard.md`](setup_wizard.md) for the trigger flow.

Mechanism options to evaluate:
- **Natural-language paste only** -- relies on the AI bot's existing filesystem + git tools. Lowest friction. Works wherever the AI bot can `git clone` and read markdown.
- **Claude Desktop slash command** -- registered when the repo is opened. Discoverable but Claude-Desktop-specific.
- **Claude Code skill** -- packaged `.skill` archive. Discoverable in Claude Code but not Claude Desktop.
- **Python CLI** -- `pip install hintforge && hintforge init`. Cross-bot but requires Python install (violates the "no install" bar for non-tech users).
- **GitHub template repo + first-run prompt detection** -- hybrid; works if the AI bot is told to look for `setup_wizard.md` after clone.

Lean toward natural-language paste as the primary mechanism -- it asks the least of the user's environment. The other mechanisms can be added as discoverability sugar.

### Research is opt-in, separated from setup (token-aware)

**Why this matters:** a Claude Pro account has roughly 45 messages per 5-hour window. Auto-research that burns 30-50 messages on day one blows the user's entire cap before they get any guide value. So research and guide-use are separable: the wizard ends with the per-game folder scaffolded but **mostly empty**, and the user invokes research explicitly, sized to their token budget.

#### Research command modes
The framework offers three research sizes the user can invoke by name:
- **Minimal research (~5 messages):** 1 top source per category. Stubs claims per subfolder. Skips source-diversity and non-English requirements.
- **Standard research (~20 messages):** applies the handoff brief's source-diversity floor (3 source classes per topic, non-English sources when the game's primary community is non-Anglophone), flags conflicts, populates a working baseline.
- **Deep research (~50+ messages):** full handoff-brief spec run in-house -- 5+ sources per topic, mechanism-not-inventory questions, exception-finding, video transcription, datamining sweep. Populates `limitations.md` with anything blocked. Recommended only for Claude Max / Team or users who don't mind heavy spend.

All three modes emit raw research; the spoiler-classification pass (separate sub-agent) runs at ingestion regardless of mode, so spoiler scoping is decoupled from research depth.

The user can also do **per-topic research on demand**: "research the puzzles", "research the chest locations in the second area", "look up what the [item] does". These cost 1-3 messages each and are how the guide naturally fills in during normal play.

#### Setup wizard's role re research
- The wizard does **not** trigger research at completion.
- The final wizard step asks: "Want me to do any research now? (none / minimal / standard / deep -- or just answer questions as they come up)". Default: **none**.
- The wizard surfaces the rough message-cost estimate next to each option.
- The user's choice is recorded in CHECKPOINT under "Research preferences" so future sessions know.

#### Goals (preserved from earlier draft)
- Every fetched URL is announced (transparent operations principle).
- Tier-appropriate filtering applied at write time so claims above the user's enemy-tier or puzzle-tier are not stored.
- Blocked sources logged to `limitations.md` with URL preserved.

#### Open questions
- How are licensing/copyright considerations handled when ingesting wiki/guide content? (Probably: cite source URL, don't reproduce verbatim, paraphrase the fact.)
- How is research re-run when the game patches? (Manual user invocation: "refresh my [GAME] guide.")
- Should research progress be persistable across sessions so a Pro user can do `minimal` today and `add another 10 messages of research` tomorrow without restarting? (Probably yes -- track a `research_log.md` in the per-game folder with what's been covered.)

### After publish + installer + research

4. Wait for / recruit a second contributor; observe friction points firsthand.
5. Build the aggregator only after we've felt the pain of doing manual reconciliation for ≥1 month.

## Pluggable persona library + cross-platform TTS + voice input

Currently personas are a per-game two-voice toggle defined in the per-game `persona.md`. The TTS/PTT patterns are specced in [`templates/optional_modules.md`](templates/optional_modules.md) as opt-in modules (with the in-tree reference impl as the worked example). The roadmap generalizes both into a wizard-installable, cross-platform feature set:

### Persona registry
A pluggable list where users register any number of voices. Each persona has:
- **Name** (displayed to the user)
- **Voice description** (tone, address style, signature tics)
- **TTS engine binding** (which voice on which platform -- SAPI on Windows, `say` voice on macOS, `espeak` voice profile on Linux)
- **Source/origin** (original creation / public-domain figure / user's own -- so the registry can honor copyright stance)

### Shipped library: original or non-copyrighted only
The public hintforge repo's persona library ships only:
- Original characters created for hintforge
- Public-domain figures (e.g. ELIZA-style historical chatbot voices)
- Generic archetypes ("formal assistant", "noir detective", "warm guide")

### User-added copyrighted personas (private forks only)
Users may register additional personas in their own private forks -- game-character AIs, sci-fi AI archetypes, film-AI voices, custom creations. The framework supports this via the registry but does not endorse, ship, or distribute copyrighted voice configurations. This stance keeps the public library clear of takedown targets.

### Cross-platform TTS engine
- **Windows:** SAPI via PowerShell (basic) or `edge-tts` neural voices via Stop hook (premium reference pattern specced in `templates/optional_modules.md`)
- **macOS:** `say` command with voice argument
- **Linux:** `espeak` or `festival`, configurable per persona
- Fallback for users without TTS: text-only output, persona name shown as a label.

### Voice input (push-to-talk)
The roadmap also wraps the PTT pattern from `templates/optional_modules.md` into a wizard-installable feature:
- **Windows:** AutoHotkey v2 + `faster-whisper` Python daemon (today's reference pattern)
- **macOS:** Hammerspoon + same Python daemon
- **Linux:** `xbindkeys` (X11) or compositor keybindings (Wayland) + same Python daemon
- All platforms: hotkey writes flag → daemon records → Whisper transcribes → text typed into Claude
- Transcription runs locally (offline) -- no audio leaves the user's machine

### When this matters
Not for the initial publish. The simple two-voice toggle and the manual-setup spec in `templates/optional_modules.md` cover immediate needs; the persona/voice generalization lands once the framework has multiple games and users want voice consistency across them without per-machine Python configuration.

## Screenshot-by-command (visual lookup)

**Concept:** the player asks "what am I looking at?" (via voice or slash command) -- the framework grabs the focused game window, sends the image to a vision-capable AI, and answers based on what's in frame plus the per-game guide content.

**Why this is interesting:**
- Eliminates the "describe what you see" friction. The player doesn't have to type or speak a careful description; they just point and ask.
- Closes the loop between visual game state and text guide content.
- Combined with PTT (roadmap) and TTS, gives a fully hands-free "look-ask-listen" loop without leaving the game.

### Two activation paths

The feature has two entry points; both arrive at the same screenshot-and-ask pipeline:

**(a) Slash command -- `/screenshot` (recommended v1)**
- User types `/screenshot what am I looking at?` in Claude Code.
- The slash-command handler (a small script in `<game>/.claude/commands/screenshot.md` + a backing `.ps1` / `.sh`) captures the focused window, attaches the image to the next message, and submits.
- Simpler to ship -- no PTT daemon required. Anyone with Claude Code Desktop and the framework installed can use it.
- Argument after the command name becomes the question. Default question if none provided: "What am I looking at?"

**(b) Voice trigger via PTT (v2 -- builds on the wizard-installable PTT)**
- The PTT daemon recognizes trigger phrases: `screenshot`, `what am I looking at`, `read this`, `look at this`.
- Same pipeline as slash command, but the trigger is voice instead of typed.
- Requires PTT to be working as a wizard-installable feature first.

Slash command is the right v1 because it works without the PTT infrastructure and can be tested standalone. Voice trigger gets built once PTT is solid.

### Window detection -- focused window only, not full screen

**The framework captures the foreground (focused) window, not the full desktop.** This matters because:

- Multi-monitor setups: with foreground-window capture, the OS handles which monitor -- you get the game, not the wrong screen.
- Privacy: other windows (Discord, browser, email) are not captured, so chat overlays / notifications / sensitive content stays out of the screenshot.
- Cropping: the captured image is exactly the game's window contents, not letterboxed by the desktop.

**Game-mode caveat:** the game must be running in **borderless-windowed** or **windowed** mode for window-handle-based capture to work. Fullscreen-exclusive (DirectX exclusive mode) games bypass the window manager -- the screenshot tool will likely capture the desktop instead. Per-game workarounds exist (DXGI Desktop Duplication API for fullscreen exclusive on Windows, but it's heavier code). The pragmatic guidance: ask players to use borderless-windowed; this is also what the PTT module already requires for its window-focus dance.

### Tools -- built-in OS APIs, no third-party install

Per the Hard Rule "Transparent operations" (#6), no surprise installs. Screenshot-by-command uses what ships with the OS:

| Platform | Tool | How |
|---|---|---|
| Windows | PowerShell + `System.Drawing` (built-in .NET) | `Add-Type` with the Win32 interop: `GetForegroundWindow()` + `GetWindowRect()` to get the HWND and bounds, then `[System.Drawing.Bitmap]` + `Graphics.CopyFromScreen` to capture the rect. Saves a PNG to a temp path. |
| macOS | `screencapture -W -o <path>` | `-W` captures the focused window interactively; `-o` removes shadow/border. Built into macOS, no install. |
| Linux (Wayland) | `grim -t <output>` (focused-output) or `slurp \| grim -g -` (window region) | `grim` ships with most Wayland compositors. |
| Linux (X11) | `import -window $(xdotool getactivewindow) <path>` | ImageMagick + xdotool, both standard on most distros. |

For Windows specifically, the PowerShell snippet looks roughly like:

```powershell
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class Win32 {
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hwnd, out RECT lpRect);
    public struct RECT { public int Left, Top, Right, Bottom; }
}
"@
$hwnd = [Win32]::GetForegroundWindow()
$rect = New-Object Win32+RECT
[Win32]::GetWindowRect($hwnd, [ref]$rect) | Out-Null
$w = $rect.Right - $rect.Left; $h = $rect.Bottom - $rect.Top
$bmp = New-Object System.Drawing.Bitmap $w, $h
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($rect.Left, $rect.Top, 0, 0, $bmp.Size)
$bmp.Save($outPath, [System.Drawing.Imaging.ImageFormat]::Png)
```

Zero dependencies. Roughly 30 lines of PowerShell wraps the whole capture path. Falls back to full-desktop if no foreground window is detected.

### Architecture (slash-command path)

```
User types "/screenshot what am I looking at?"
   │
   ▼
Slash command handler (in <game>/.claude/commands/screenshot.md)
  + backing screenshot.ps1
   │
   ▼
1. Detect foreground window via Win32 (or OS equivalent)
2. Announce: "I'm capturing the focused window -- [game name if detectable]"
3. Capture window contents to %TEMP%/hintforge_screenshot_<timestamp>.png
4. Optionally: blur or crop sensitive UI overlays (configurable per game)
5. Attach image to next message, with the user's question as text
   │
   ▼
Claude (with vision) reads the image + question, cross-references the
per-game guide content (puzzles/, items/, sections/, areas/), and answers
applying tier discipline (nothing above the user's enemy-tier or puzzle-tier; lore hidden unless opted in)
   │
   ▼
Screenshot deleted from temp after successful response (default;
configurable to keep with per-game logging if user opts in)
```

### Open design questions

- **Privacy disclosure.** The "I'm capturing the focused window" announce-before-act is required (transparent ops principle). Should also disclose if the captured image is being uploaded to a cloud AI -- Claude Pro vs. self-hosted vision models have different surfaces.
- **Screenshot lifetime.** Default: deleted after the AI reads it. Opt-in: keep in a `<game>/screenshots/` folder for later cross-reference. Never automatic.
- **Vision-model availability.** Not all Claude tiers / configurations have vision. The slash command should detect and surface "vision isn't available in this session" before attempting capture.
- **Token cost.** Vision calls are heavier than text (~2-5x cost per message depending on image size). Per-question lookup is fine; auto-screenshot-on-every-question would burn the Pro budget. Activation discipline: voice/slash-command only, never automatic.
- **Sensitive UI overlays.** Some games show real-name lobbies, chat windows, user-handle overlays. Per-game config could mark regions to blur before sending. v2 concern.
- **Multi-window games** (e.g. game + companion app). Capturing the foreground window means whichever has focus. If the player wants both, they take two screenshots.

### When this matters

The voice-trigger version follows the wizard-installable PTT module. The slash-command version (`/screenshot`) can ship earlier -- anytime after the framework publishes, since it doesn't require the PTT daemon. **Prioritize the slash command** as the v1; it's a self-contained feature that proves the screenshot-and-ask pipeline before adding voice on top.

## Save-watcher industry-push hypothesis

Note (2026-04-29): over 5+ years, the existence of save-watcher bots may push studios toward stabilizing / documenting save formats -- similar to how API-friendly platforms emerged once enough integrations existed. Studios that make agent-friendly saves get better community guides, which drives engagement.

Worth a long-running log of which games make this easy vs. hard, so the demand signal is visible to anyone going looking. Tracking file: `hintforge/save_watcher_log.md` -- created when ≥2 per-game watchers exist.

## Status

**Templates shipped.** Further milestones blocked on a second per-game instantiation.

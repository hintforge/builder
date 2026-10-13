# [GAME NAME] -- Limitations & Blocked Sources

Sources I found that look useful but couldn't fully fetch -- paywalls, Cloudflare, age gates, video-only content, etc. URLs preserved so the player (or another contributor) can open them in a real browser.

## How to read this file
- Each entry: topic, URL, block type, what I could glean, best alternative I did get to.
- Each per-topic file (in `puzzles/`, `[areas]/`, `items/`, `sections/`) also lists its own blocked sources at the bottom -- the player rarely needs to come hunting here.
- This file is the catch-all for sources that didn't fit a specific topic.

## Block types
- **paywall** -- content gated behind a subscription or article limit
- **cloudflare** -- Cloudflare bot challenge / 403 / 503 from WebFetch
- **video-only** -- YouTube or other video where the answer is shown visually; no readable text equivalent
- **age-gate** -- content blocked behind age verification
- **cookie-wall** -- popup or consent flow that broke the fetch
- **search-snippet-only** -- search engine returned a snippet but the page itself wasn't reachable
- **dead-link** -- URL was in another source but no longer resolves

- **robots-restriction** -- the external research runtime reports a robots access restriction
- **terms-restriction** -- a stated retrieval restriction was reported; preserve the actual evidence
- **javascript-dependent** -- useful content requires page execution the available tool did not perform
- **login-required** -- a signed-in session is required
- **access-not-checked** -- no content/access check was performed; never call this robots-blocked

## Companion tools

For every useful map, tracker, database or completion tool supplied, recalled or found:

- Name and URL if verified (otherwise mark unknown/unverified)
- Apparent coverage, evidence for it, and uncertainty; unread coverage is not confirmed game data
- Reason not read, access-check result, policy evidence if available, and check date
- How a person could use it, best readable alternative, and wider-spoiler warning where relevant

Merge repeated URLs with dated evidence retained. Read tools can also be recorded here when they offer a useful location fallback. Record an honest empty statement when no candidates were found; do not imply exhaustive discovery.

## Entries

[One per blocked source as encountered. Template:]

### [Source name] -- [topic]
- Source: [URL]
- Block type: [from list above]
- Why I think it has the answer: [1-2 lines]
- What I could glean before the block: [snippet info, if any -- even partial information helps]
- Best alternative I did get to: [other source / file in this guide]

## Always-blocked categories

[Things no source can give us -- e.g. randomized content per save (if applicable), visual-only puzzle solutions where text guides don't exist, in-game UI elements that aren't documented anywhere. Document the pattern so future research doesn't keep hitting the wall, and so contributors know to manually transcribe rather than search.]

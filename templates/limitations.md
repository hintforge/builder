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

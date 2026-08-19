# Save-Watcher Module -- opt-in (game-specific implementation required)

A small Python script that reads the most-recently-modified save file from your game's save directory and prints a spoiler-safe summary of your current state -- location, equipped gear, collectibles count, etc. Optionally writes a JSON snapshot to `<game>/save_state/latest.json` so Claude can reason about your current state at session start without you typing it.

**Unlike PTT and TTS, save-watcher is not a copy-paste template** -- every game's save format is different. This template provides a *skeleton* and *patterns*; you have to fill in the per-game parsing.

## What's in this template

| File | Where it goes | Purpose |
|---|---|---|
| `skeleton.py` | `<game>/save_watcher.py` (after filling in) | Skeleton with the boilerplate (find latest save, dataclass for summary, JSON snapshot output) and TODO markers for the parsing. |
| `README.md` | (read; don't copy) | This file -- patterns + reference impl pointer. |

## When this is worth doing

**Skip it on Pro tier unless you really want it.** The hintforge wizard's Step 3 explicitly recommends "skip" because save-format reverse-engineering is the highest-token-cost optional module -- typically 10-30 messages of trial-and-error reads.

Worth doing when:
- Your game's save format is well-documented (community wiki, `.json` saves, etc.)
- You play long sessions and don't want to re-tell Claude your location every time
- You're on Max/Team and have message budget to spend

Skip when:
- You're on Pro (especially first-time hintforge user)
- The save format is encrypted/proprietary
- You prefer just telling Claude your location at session start

## Save format patterns (reference)

### Pattern 1 -- JSON / plaintext

The easiest case. Some games store saves as readable JSON or XML:

```python
import json
data = json.loads(path.read_text(encoding="utf-8"))
current_map = data["world"]["currentLevel"]
```

Examples: many Unity games using PlayerPrefs JSON exports, many indie roguelikes, anything saving via standard JSON.

### Pattern 2 -- UE binary header with FString fields

Unreal Engine games typically save a binary blob, but the first few KB are usually plain -- file version, slot label, world name, sublevel list, equipped items. Encrypted/compressed payload starts later. Parse the plain header without touching the rest:

```python
import struct
with open(path, "rb") as f:
    header = f.read(8192)  # plain bytes before encryption

# UE FString: 4-byte length prefix + UTF-8 bytes (or UTF-16 if length is negative)
def find_strings(buf):
    strings = []
    i = 0
    while i < len(buf) - 4:
        (length,) = struct.unpack_from("<i", buf, i)
        if 1 <= length <= 256:
            try:
                s = buf[i+4:i+4+length].decode("utf-8").rstrip("\x00")
                if s.isprintable() and len(s) >= 3:
                    strings.append((i, s))
            except UnicodeDecodeError:
                pass
        i += 1
    return strings
```

Then look for known keys (`World`, `Sublevel_*`, persona names, equipped slot names) by string prefix. This is the most common pattern for UE4/UE5 single-player titles.

### Pattern 3 -- Encrypted / proprietary binary

**Run these four checks before you classify a save as Pattern 3.** "No readable strings in the first N KB, and the header matches no compression magic" is the usual reason a save gets filed here, and it is not sufficient: it separates *not plaintext* from *plaintext*, and says nothing about encrypted vs obfuscated vs compressed. Obfuscation (a fixed XOR keystream, a byte rotation, a counter) is far more common than encryption in single-player games, and it is readable in an afternoon. Each check is minutes of work and any one of them can settle it:

1. **Does the whole file decode as UTF-8 (or ASCII)?** A multi-megabyte file that decodes cleanly is a *text* file -- the game wrote its payload as a string. Real ciphertext and compressed data fail this almost immediately.
2. **XOR two different saves together.** If the result is overwhelmingly below `0x80` and uses far fewer than 256 distinct values, you have two 7-bit-ASCII plaintexts sharing one keystream -- obfuscation, and crackable. Independent encryption or compression gives ~50% of bytes at or above `0x80` and all 256 values.
3. **Compare two saves byte for byte.** Long identical runs mean there is no per-save key material (no IV, no nonce). Encryption worth the name never does that; a fixed keystream always does.
4. **If the plaintext is 7-bit ASCII, the top bit of each stored byte IS the keystream's top bit.** Autocorrelate that bit sequence to recover the key period, then solve one key byte per column by maximizing printable characters. A perfect correlation spike at multiples of some N hands you the key length directly.

A save that passes all four -- no text decode, no shared keystream, no identical runs, no periodicity -- is genuinely Pattern 3. Then, and only then:
- **Skip.** Just tell Claude your location at session start. This is the recommended answer for this case -- the cost/benefit rarely justifies the other two options.
- **Find a community decrypter.** Mod scenes for popular games often have one. Cite the source in your save_watcher.py.
- **Reverse-engineer.** Big project. Don't do this for a guide -- only if you're already modding the game.

## Avoid these traps

- **Playtime fields are usually wrong.** Many games store `wall-clock-since-first-save` or `time-since-game-launched`, not active gameplay time. UE titles in particular often expose `PlayedTime` and `SlotPlayedTime` fields in the .sav header that overshoot real playtime by several multiples. Cross-reference with Steam playtime if you need a real number, and **never quote a save-derived playtime as authoritative**.
- **Strings can be UTF-16, not UTF-8.** UE games sometimes use UTF-16 for non-ASCII characters. The FString length is negative in that case.
- **Slot indexing varies.** Some games use slot-based filenames (`save_001.dat`); others use a single rolling save (`autosave.sav`). The "find latest by mtime" approach in skeleton.py works for both but may not be ideal for slot-based games where the user wants a specific slot.

## Patterns worth carrying into your own implementation

A well-built save-watcher tends to include:
- `os.environ.get("GAME_SAVE_DIR", default)` -- env var override for users with non-default install paths
- Snapshot diffing (compares latest save against prior snapshot to flag what changed)
- A `META_FILES` set to exclude settings/config saves from "find latest" logic
- An `--all` flag for inspecting every slot (debugging)
- An honest playtime-warning in the docstring (see "Avoid these traps" above)

## Token cost honesty (Principle #13)

Manual implementation: **0 token cost** if you can find the format documented somewhere. Just write the parser and run.

Wizard-assisted implementation: **10-30 messages**, primarily because the bot has to read save bytes back from your game, guess at offsets, and iterate. This is why the wizard defaults to skip.

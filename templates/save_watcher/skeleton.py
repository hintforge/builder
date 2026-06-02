"""<GAME_NAME> save watcher -- SKELETON.

Reads the most-recently-modified save file and prints a spoiler-safe summary
of useful state (location, equipped gear, key flags). Optionally writes a
JSON snapshot to <game>/save_state/latest.json for session-start ingestion.

This is a SKELETON. Every game has a different save format -- fill in the
parsing logic for your specific game. See README.md in this template
folder for design patterns.

Usage:
    python save_watcher.py            # print summary of latest save
    python save_watcher.py --snapshot # also write save_state/latest.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path

# === CONFIGURE PER GAME ===

# Default save directory. Override via env var <GAME>_SAVE_DIR for portability.
SAVE_DIR = Path(os.environ.get(
    "GAME_SAVE_DIR",
    # TODO: replace with the game's typical save location
    r"C:/Users/<user>/AppData/Local/<GameName>/Saved/SaveGames",
))

# File pattern for actual save files (vs. settings/config files).
# Examples: "*.sav", "savegame*.dat", "slot*.bin"
SAVE_GLOB = "*.sav"  # TODO: adjust per game

# Files to exclude (settings, metadata, config -- not actual gameplay saves).
EXCLUDE = {"SavedSettings.sav"}  # TODO: adjust per game

# Snapshot output (read by Claude at session start).
SNAPSHOT_DIR = Path(__file__).parent / "save_state"


@dataclass
class SaveSummary:
    """Spoiler-safe save state summary. Add/remove fields per game."""
    slot_path: str
    modified: str
    # TODO: add game-specific fields, e.g.:
    # current_area: str
    # equipped_weapon: str | None
    # collectibles_count: int


def find_latest_save() -> Path | None:
    """Return the most-recently-modified save file in SAVE_DIR."""
    if not SAVE_DIR.exists():
        return None
    candidates = [
        p for p in SAVE_DIR.glob(SAVE_GLOB)
        if p.name not in EXCLUDE and p.is_file()
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def parse_save(path: Path) -> SaveSummary:
    """Extract spoiler-safe state from a save file.

    Most game saves are one of:
      - JSON / plaintext (easy: json.loads or text parsing)
      - Binary with a known header (medium: struct.unpack on offsets)
      - Encrypted / compressed (hard: usually only the outer header is plain)

    For UE-based games, the first ~few KB after the header is often
    plain UTF-8 strings (FString format: 4-byte length prefix + bytes).
    For Unity ES3/PlayerPrefs, the format is documented and parseable.
    For proprietary binary formats, you'll need to reverse-engineer or
    find a community spec.

    See README.md in this template folder for parsing patterns.
    """
    mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()

    # === FILL IN: parse the save file and extract spoiler-safe fields ===
    # Example pattern for binary header parsing:
    #
    #   with open(path, "rb") as f:
    #       header = f.read(8192)  # plain bytes before any encryption
    #
    #   # Find UTF-8 strings (UE FString: 4-byte length prefix + bytes):
    #   import struct, re
    #   strings = []
    #   i = 0
    #   while i < len(header) - 4:
    #       (length,) = struct.unpack_from("<i", header, i)
    #       if 1 <= length <= 256:
    #           try:
    #               s = header[i+4:i+4+length].decode("utf-8").rstrip("\x00")
    #               if s.isprintable() and len(s) >= 3:
    #                   strings.append(s)
    #           except UnicodeDecodeError:
    #               pass
    #       i += 1
    #
    #   # Then look for known keys: e.g. "World" prefix means current map name.
    # ====================================================================

    return SaveSummary(
        slot_path=str(path),
        modified=mtime,
        # TODO: populate game-specific fields here
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", action="store_true",
                        help="Write JSON snapshot to save_state/latest.json")
    parser.add_argument("--all", action="store_true",
                        help="Print summary for every save slot")
    args = parser.parse_args()

    if args.all:
        if not SAVE_DIR.exists():
            print(f"save dir not found: {SAVE_DIR}")
            sys.exit(1)
        for path in sorted(SAVE_DIR.glob(SAVE_GLOB)):
            if path.name in EXCLUDE:
                continue
            summary = parse_save(path)
            print(json.dumps(asdict(summary), indent=2))
        return

    latest = find_latest_save()
    if not latest:
        print(f"no saves found in {SAVE_DIR}")
        sys.exit(1)

    summary = parse_save(latest)
    print(json.dumps(asdict(summary), indent=2))

    if args.snapshot:
        SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
        snapshot_path = SNAPSHOT_DIR / "latest.json"
        snapshot_path.write_text(json.dumps(asdict(summary), indent=2), encoding="utf-8")
        print(f"\nsnapshot written: {snapshot_path}", file=sys.stderr)


if __name__ == "__main__":
    main()

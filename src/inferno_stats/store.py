"""Data store — discover RuneLite data, load attempts, manage metadata."""

from __future__ import annotations

import json
import os
from pathlib import Path

from inferno_stats.models import Attempt, CharacterProfile
from inferno_stats.parser import parse_file

DEFAULT_DATA_DIR = Path.home() / ".runelite" / "inferno-stats"
DEFAULT_META_DIR = Path.home() / ".inferno-stats"
META_FILENAME = "metadata.json"


def get_data_dir() -> Path:
    """Return the inferno-stats data directory.

    Checks INFERNO_STATS_DIR env var first, then falls back to default.
    """
    env = os.environ.get("INFERNO_STATS_DIR")
    if env:
        return Path(env)
    return DEFAULT_DATA_DIR


def get_meta_path() -> Path:
    """Return the path to the metadata JSON file."""
    env = os.environ.get("INFERNO_STATS_META")
    if env:
        return Path(env)
    return DEFAULT_META_DIR / META_FILENAME


def get_share_dir() -> Path:
    """Return the directory `inferno share` writes to when no --output is given.

    Checks INFERNO_STATS_SHARE_DIR env var first, then falls back to default.
    """
    env = os.environ.get("INFERNO_STATS_SHARE_DIR")
    if env:
        return Path(env).expanduser()
    return DEFAULT_META_DIR / "exports"


def discover_characters(data_dir: Path | None = None) -> list[str]:
    """List character names found in the data directory."""
    data_dir = data_dir or get_data_dir()
    if not data_dir.exists():
        return []
    return sorted(
        d.name for d in data_dir.iterdir() if d.is_dir() and not d.name.startswith(".")
    )


def load_profile(character: str, data_dir: Path | None = None) -> CharacterProfile:
    """Load all attempts for a character, sorted chronologically."""
    data_dir = data_dir or get_data_dir()
    inferno_dir = data_dir / character / "inferno"
    profile = CharacterProfile(name=character)

    if not inferno_dir.exists():
        return profile

    # Gather and sort split files by name (which sorts chronologically)
    files = sorted(inferno_dir.glob("*.txt"))

    attempts: list[Attempt] = []
    for path in files:
        attempt = parse_file(path, character, attempt_number=0)
        if attempt is not None:
            attempts.append(attempt)

    # Sort by timestamp and assign attempt numbers
    attempts.sort(key=lambda a: a.timestamp)
    for i, attempt in enumerate(attempts, start=1):
        attempt.number = i

    # Apply metadata
    meta = load_metadata()
    char_meta = meta.get("characters", {}).get(character, {}).get("attempts", {})
    for attempt in attempts:
        key = attempt.timestamp.isoformat()
        if key in char_meta:
            m = char_meta[key]
            attempt.gear_setup = m.get("gear_setup")
            attempt.on_task = m.get("on_task")
            attempt.notes = m.get("notes")

    profile.attempts = attempts
    return profile


def load_metadata() -> dict:
    """Load the metadata JSON file, returning empty dict if not found."""
    meta_path = get_meta_path()
    if not meta_path.exists():
        return {"version": 1, "characters": {}}
    with open(meta_path, encoding="utf-8") as f:
        return json.load(f)


def save_metadata(meta: dict) -> None:
    """Write metadata JSON file, creating parent dirs if needed."""
    meta_path = get_meta_path()
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)


def tag_attempt(
    character: str,
    attempt: Attempt,
    gear_setup: str | None = None,
    on_task: bool | None = None,
    notes: str | None = None,
) -> None:
    """Add or update metadata for a specific attempt."""
    meta = load_metadata()
    characters = meta.setdefault("characters", {})
    char = characters.setdefault(character, {})
    attempts = char.setdefault("attempts", {})

    key = attempt.timestamp.isoformat()
    entry = attempts.get(key, {})

    if gear_setup is not None:
        entry["gear_setup"] = gear_setup
    if on_task is not None:
        entry["on_task"] = on_task
    if notes is not None:
        entry["notes"] = notes

    attempts[key] = entry
    save_metadata(meta)

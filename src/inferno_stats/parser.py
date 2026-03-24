"""Parse RuneLite inferno-stats split files into Attempt objects."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from inferno_stats.models import Attempt, Split

# Filename: "2025-09-18 00-24-51 Successful KC on Wave 69, Splits.txt"
FILENAME_RE = re.compile(
    r"(\d{4}-\d{2}-\d{2}) (\d{2}-\d{2}-\d{2}) "
    r"(Failed|Successful) KC on Wave (\d+), Splits\.txt"
)

# Content lines
SPLIT_RE = re.compile(r"Wave:\s*(\d+),\s*Split:\s*(\d+:\d+)\s*\(\+(\d+:\d+)\)")
DURATION_RE = re.compile(r"Duration\s*\((Success|Failed)\):\s*(\d+:\d+(?:\.\d+)?)")


def parse_time(time_str: str) -> float:
    """Parse MM:SS or MM:SS.d into total seconds.

    The plugin uses MM:SS where MM can exceed 60 (e.g., 97:21 = 97 minutes).
    """
    parts = time_str.split(":")
    minutes = int(parts[0])
    seconds = float(parts[1])
    return minutes * 60.0 + seconds


def parse_filename(filename: str) -> dict | None:
    """Extract metadata from a split filename.

    Returns dict with keys: timestamp, success, death_wave, or None if no match.
    """
    match = FILENAME_RE.match(filename)
    if not match:
        return None
    date_str, time_str, status, wave = match.groups()
    timestamp = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H-%M-%S")
    return {
        "timestamp": timestamp,
        "success": status == "Successful",
        "death_wave": int(wave),
    }


def parse_file(path: Path, character: str, attempt_number: int) -> Attempt | None:
    """Parse a single split file into an Attempt.

    Returns None if the filename doesn't match the expected pattern.
    """
    meta = parse_filename(path.name)
    if meta is None:
        return None

    content = path.read_text(encoding="utf-8")
    splits: list[Split] = []
    duration_seconds = 0.0

    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue

        split_match = SPLIT_RE.search(line)
        if split_match:
            wave = int(split_match.group(1))
            cumulative = parse_time(split_match.group(2))
            segment = parse_time(split_match.group(3))
            splits.append(Split(wave=wave, cumulative_seconds=cumulative, segment_seconds=segment))
            continue

        duration_match = DURATION_RE.search(line)
        if duration_match:
            duration_seconds = parse_time(duration_match.group(2))

    # Detect corrupt/zero data (all splits at 00:00 and duration 0)
    all_zero = duration_seconds == 0.0 and all(s.cumulative_seconds == 0.0 for s in splits)
    data_valid = not all_zero or (len(splits) == 0 and duration_seconds == 0.0 and meta["death_wave"] <= 1)

    # Wave 1 death with 0 duration is plausible (instant quit), but wave 28 with all zeros is corrupt
    if all_zero and meta["death_wave"] > 1:
        data_valid = False

    return Attempt(
        number=attempt_number,
        timestamp=meta["timestamp"],
        character=character,
        success=meta["success"],
        death_wave=meta["death_wave"],
        splits=splits,
        duration_seconds=duration_seconds,
        data_valid=data_valid,
    )

"""Data models for Inferno attempts and splits."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Split:
    """A single wave split checkpoint."""

    wave: int
    cumulative_seconds: float
    segment_seconds: float


@dataclass
class Attempt:
    """A single Inferno attempt parsed from a RuneLite split file."""

    number: int  # 1-indexed chronological attempt number
    timestamp: datetime
    character: str
    success: bool
    death_wave: int
    splits: list[Split] = field(default_factory=list)
    duration_seconds: float = 0.0
    data_valid: bool = True  # False for corrupt/zero-data files

    # Metadata (from separate JSON, not from split file)
    gear_setup: str | None = None
    on_task: bool | None = None
    notes: str | None = None

    @property
    def effective_duration_seconds(self) -> float:
        """Best estimate of total duration.

        The plugin sometimes reports anomalous Duration values (e.g., 02:12.6
        for a full completion). When the last split time exceeds the reported
        duration, use the last split as the effective total.
        """
        if self.splits:
            last_split = self.splits[-1].cumulative_seconds
            return max(self.duration_seconds, last_split)
        return self.duration_seconds


@dataclass
class CharacterProfile:
    """All attempts for a single character."""

    name: str
    attempts: list[Attempt] = field(default_factory=list)

    @property
    def valid_attempts(self) -> list[Attempt]:
        """Attempts with valid data (excludes corrupt/zero files)."""
        return [a for a in self.attempts if a.data_valid]

    @property
    def completions(self) -> list[Attempt]:
        """Successful attempts."""
        return [a for a in self.valid_attempts if a.success]

    @property
    def failures(self) -> list[Attempt]:
        """Failed attempts."""
        return [a for a in self.valid_attempts if not a.success]

    @property
    def best_wave(self) -> int:
        """Highest wave reached across all valid attempts."""
        if not self.valid_attempts:
            return 0
        return max(a.death_wave for a in self.valid_attempts)

    @property
    def pb(self) -> Attempt | None:
        """Personal best — fastest completion, or deepest attempt if no cape."""
        if self.completions:
            return min(self.completions, key=lambda a: a.effective_duration_seconds)
        if self.valid_attempts:
            return max(self.valid_attempts, key=lambda a: a.death_wave)
        return None

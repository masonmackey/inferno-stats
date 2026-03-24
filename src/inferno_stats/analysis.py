"""Smart commentary engine — analyze patterns and generate insights."""

from __future__ import annotations

from inferno_stats.constants import (
    DEATH_TIPS,
    SPEED_RUN_THRESHOLD_MINUTES,
    get_section_name_for_wave,
)
from inferno_stats.display import format_duration_short, format_time
from inferno_stats.models import CharacterProfile


def compute_avg_segments(profile: CharacterProfile) -> dict[int, float]:
    """Average segment time per split wave across all valid attempts."""
    totals: dict[int, list[float]] = {}
    for attempt in profile.valid_attempts:
        for split in attempt.splits:
            if split.segment_seconds > 0:
                totals.setdefault(split.wave, []).append(split.segment_seconds)

    return {wave: sum(times) / len(times) for wave, times in totals.items() if times}


def detect_death_wall(profile: CharacterProfile) -> list[str]:
    """Find the section where the player dies most often."""
    section_deaths: dict[str, int] = {}
    for attempt in profile.failures:
        name = get_section_name_for_wave(attempt.death_wave)
        section_deaths[name] = section_deaths.get(name, 0) + 1

    if not section_deaths:
        return []

    worst = max(section_deaths, key=lambda k: section_deaths[k])
    count = section_deaths[worst]

    insights: list[str] = []
    if count >= 2:
        tip = DEATH_TIPS.get(worst, "")
        insights.append(f"Death wall: {worst} section ({count} deaths). {tip}")
    return insights


def detect_consistency(profile: CharacterProfile) -> list[str]:
    """Check split consistency at early waves."""
    wave9_times = [
        s.segment_seconds
        for a in profile.valid_attempts
        for s in a.splits
        if s.wave == 9 and s.segment_seconds > 0
    ]

    insights: list[str] = []
    if len(wave9_times) >= 3:
        low = format_duration_short(min(wave9_times))
        high = format_duration_short(max(wave9_times))
        spread = max(wave9_times) - min(wave9_times)
        if spread < 90:
            insights.append(f"Wave 9 splits are consistent ({low} - {high}) — early waves locked in.")
        else:
            insights.append(f"Wave 9 splits vary ({low} - {high}) — early game could be more consistent.")
    return insights


def detect_section_improvement(profile: CharacterProfile) -> list[str]:
    """Compare segment times between early and recent attempts."""
    valid = profile.valid_attempts
    if len(valid) < 4:
        return []

    early = valid[: len(valid) // 3]
    recent = valid[-len(valid) // 3 :]

    insights: list[str] = []

    # Compare average segment times for wave sections both groups reached
    for wave in [35, 42, 50, 57]:
        early_times = [
            s.segment_seconds
            for a in early
            for s in a.splits
            if s.wave == wave and s.segment_seconds > 0
        ]
        recent_times = [
            s.segment_seconds
            for a in recent
            for s in a.splits
            if s.wave == wave and s.segment_seconds > 0
        ]

        if early_times and recent_times:
            early_avg = sum(early_times) / len(early_times)
            recent_avg = sum(recent_times) / len(recent_times)
            if early_avg > 0 and recent_avg < early_avg * 0.85:
                pct = int((1 - recent_avg / early_avg) * 100)
                insights.append(
                    f"Wave {wave} segment improved: "
                    f"{format_duration_short(early_avg)} → {format_duration_short(recent_avg)} "
                    f"({pct}% faster)"
                )

    return insights


def detect_journey(profile: CharacterProfile) -> list[str]:
    """Summarize the overall journey."""
    valid = profile.valid_attempts
    if not valid:
        return []

    insights: list[str] = []
    first_wave = valid[0].death_wave
    days = (valid[-1].timestamp - valid[0].timestamp).days

    if profile.completions:
        cape = profile.completions[0]
        insights.append(
            f"Journey: Wave {first_wave} → cape in {len(valid)} attempts over {days} days."
        )
        pb_time = format_time(cape.effective_duration_seconds)
        threshold = SPEED_RUN_THRESHOLD_MINUTES * 60
        delta = cape.effective_duration_seconds - threshold
        if delta > 0:
            insights.append(
                f"PB of {pb_time} is {format_time(delta)} off Combat Achievement speed run (sub-65 min)."
            )
        else:
            insights.append(f"PB of {pb_time} — under the Combat Achievement threshold!")
    else:
        best = profile.best_wave
        insights.append(
            f"Journey so far: {len(valid)} attempts over {days} days. Best wave: {best}."
        )
    return insights


def detect_outliers(profile: CharacterProfile) -> list[str]:
    """Find attempts with abnormally slow segments."""
    avgs = compute_avg_segments(profile)
    insights: list[str] = []

    for attempt in profile.valid_attempts:
        for split in attempt.splits:
            if split.wave in avgs and split.segment_seconds > 0:
                avg = avgs[split.wave]
                if avg > 0 and split.segment_seconds > avg * 2.5 and split.segment_seconds > 120:
                    insights.append(
                        f"Outlier: Attempt #{attempt.number} spent "
                        f"{format_duration_short(split.segment_seconds)} on wave {split.wave} segment "
                        f"(avg {format_duration_short(avg)}). Rough RNG or AFK?"
                    )
    return insights


def generate_commentary(profile: CharacterProfile) -> list[str]:
    """Generate all insights for a character profile."""
    commentary: list[str] = []
    commentary.extend(detect_journey(profile))
    commentary.extend(detect_death_wall(profile))
    commentary.extend(detect_consistency(profile))
    commentary.extend(detect_section_improvement(profile))
    commentary.extend(detect_outliers(profile))
    return commentary

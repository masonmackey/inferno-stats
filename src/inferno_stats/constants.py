"""Static OSRS Inferno knowledge — wave data, enemy info, tips."""

from __future__ import annotations

# Split points tracked by the inferno-stats RuneLite plugin
SPLIT_WAVES: list[int] = [9, 18, 25, 35, 42, 50, 57, 60, 63, 66, 67, 68, 69]

TOTAL_WAVES = 69

# Wave sections with names, enemies, and theming
WAVE_SECTIONS: dict[tuple[int, int], dict[str, str]] = {
    (1, 8): {"name": "Warmup", "enemies": "Nibblers + Bats + Blobs", "emoji": "\U0001f987"},
    (9, 17): {"name": "Melee", "enemies": "+Jal-ImKot", "emoji": "\u2694\ufe0f"},
    (18, 24): {"name": "Rangers", "enemies": "+Jal-Xil", "emoji": "\U0001f3f9"},
    (25, 34): {"name": "Pre-Mage", "enemies": "Mixed", "emoji": "\U0001f525"},
    (35, 41): {"name": "Mages", "enemies": "+Jal-Zek", "emoji": "\U0001f9d9"},
    (42, 49): {"name": "Full Roster", "enemies": "All types", "emoji": "\U0001f480"},
    (50, 56): {"name": "Deep Waves", "enemies": "All combined", "emoji": "\U0001f30b"},
    (57, 59): {"name": "Triple Trouble", "enemies": "Heavy combos", "emoji": "\U0001f624"},
    (60, 65): {"name": "Final Gauntlet", "enemies": "Complex spawns", "emoji": "\u26a1"},
    (66, 66): {"name": "Pre-Jad", "enemies": "Last regular wave", "emoji": "\U0001f514"},
    (67, 67): {"name": "Jad", "enemies": "JalTok-Jad + Healers", "emoji": "\U0001f432"},
    (68, 68): {"name": "Triple Jads", "enemies": "3x JalTok-Jad", "emoji": "\U0001f432\U0001f432\U0001f432"},
    (69, 69): {"name": "Zuk", "enemies": "TzKal-Zuk", "emoji": "\U0001f451"},
}

# Valid gear setup identifiers
GEAR_SETUPS = ("tbow", "bowfa", "shadow", "other")

# Combat Achievement speed run threshold (minutes)
SPEED_RUN_THRESHOLD_MINUTES = 65

# Section-specific death tips
DEATH_TIPS: dict[str, str] = {
    "Warmup": "Early deaths usually mean a supply or prayer issue. Check your inventory setup.",
    "Melee": "Jal-ImKot hits hard in melee. Keep distance and pray melee when trapped.",
    "Rangers": "Jal-Xil is fast — pray range and learn safe spots behind pillars.",
    "Pre-Mage": "These waves are about efficiency. Conserve supplies for mages.",
    "Mages": "Jal-Zek is the biggest skill check. Focus on mage prayer switches and safe spots.",
    "Full Roster": "All enemy types at once. Prioritize magers, then rangers, then melee.",
    "Deep Waves": "You're deep — stay calm. Pillar positioning is everything.",
    "Triple Trouble": "Heavy combos require fast prayer switching. Don't panic.",
    "Final Gauntlet": "Almost there. Manage your supplies carefully for the bosses ahead.",
    "Pre-Jad": "Last regular wave. Top off prayer and HP before Jad spawns.",
    "Jad": "Jad is about rhythm. Practice prayer flicking — watch the attack animation.",
    "Triple Jads": "Pure prayer muscle memory. Pick one Jad, kill it, then rotate.",
    "Zuk": "Zuk is methodical. Shield timing and healer management are key.",
}


def get_section_for_wave(wave: int) -> dict[str, str] | None:
    """Return the section info for a given wave number."""
    for (low, high), info in WAVE_SECTIONS.items():
        if low <= wave <= high:
            return info
    return None


def get_section_name_for_wave(wave: int) -> str:
    """Return just the section name for a wave, or 'Unknown'."""
    section = get_section_for_wave(wave)
    return section["name"] if section else "Unknown"

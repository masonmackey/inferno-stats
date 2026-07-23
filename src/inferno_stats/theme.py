"""OSRS-themed color palette and Rich styling."""

from __future__ import annotations

from rich.style import Style
from rich.theme import Theme

# Muted palette — nothing neon, everything readable
GOLD = "#C8A84E"
GREEN_MUTED = "#6BAF6B"
RED_MUTED = "#C46B6B"
ORANGE_MUTED = "#C89650"
BLUE_MUTED = "#6B8EAF"
SLATE = "#A0A8B0"
DIM = "#606060"
GRAY = "#888888"
LAVA_MUTED = "#B85C3A"

# Kept for classic theme — original OSRS neon colors
GOLD_BRIGHT = "#FFD700"
GREEN_BRIGHT = "#00FF00"
RED_BRIGHT = "#FF3333"
ORANGE_BRIGHT = "#FF981F"
CYAN_BRIGHT = "#00FFFF"
LAVA_BRIGHT = "#FF4500"

# "classic" — original full-color OSRS theme (neon)
CLASSIC_THEME = Theme(
    {
        "header": Style(color=GOLD_BRIGHT, bold=True),
        "subheader": Style(color=ORANGE_BRIGHT, bold=True),
        "success": Style(color=GREEN_BRIGHT, bold=True),
        "failure": Style(color=RED_BRIGHT, bold=True),
        "info": Style(color=CYAN_BRIGHT),
        "dim": Style(color=DIM),
        "commentary": Style(color=CYAN_BRIGHT, italic=True),
        "wave.early": Style(color=GREEN_BRIGHT),
        "wave.mid": Style(color=ORANGE_BRIGHT),
        "wave.late": Style(color=RED_BRIGHT),
        "wave.boss": Style(color=GOLD_BRIGHT, bold=True),
        "split.fast": Style(color=GREEN_BRIGHT),
        "split.slow": Style(color=RED_BRIGHT),
        "metric.label": Style(color=SLATE),
        "metric.value": Style(color=GOLD_BRIGHT, bold=True),
        "lava": Style(color=LAVA_BRIGHT, bold=True),
        "date": Style(color=CYAN_BRIGHT),
        "death": Style(color=RED_BRIGHT, bold=True),
    }
)

# "clean" — muted, easy on the eyes, color only where it matters
CLEAN_THEME = Theme(
    {
        "header": Style(color=GOLD, bold=True),
        "subheader": Style(color=ORANGE_MUTED, bold=True),
        "success": Style(color=GREEN_MUTED, bold=True),
        "failure": Style(color=DIM),
        "info": Style(color=BLUE_MUTED),
        "dim": Style(color=DIM),
        "commentary": Style(color=BLUE_MUTED, italic=True),
        "wave.early": Style(color=GRAY),
        "wave.mid": Style(color=GRAY),
        "wave.late": Style(color=GRAY),
        "wave.boss": Style(color=GOLD, bold=True),
        "split.fast": Style(color=GREEN_MUTED),
        "split.slow": Style(color=RED_MUTED),
        "metric.label": Style(color=SLATE),
        "metric.value": Style(color=GOLD, bold=True),
        "lava": Style(color=LAVA_MUTED, bold=True),
        "date": Style(color=GRAY),
        "death": Style(color=DIM),
    }
)

THEMES = {
    "classic": CLASSIC_THEME,
    "clean": CLEAN_THEME,
}

# Default for backwards compat
OSRS_THEME = CLASSIC_THEME


def get_theme(name: str = "classic") -> Theme:
    """Return a theme by name."""
    return THEMES.get(name, CLASSIC_THEME)


def wave_style(wave: int) -> str:
    """Return the theme style name for a wave number."""
    if wave <= 17:
        return "wave.early"
    if wave <= 34:
        return "wave.mid"
    if wave <= 66:
        return "wave.late"
    return "wave.boss"

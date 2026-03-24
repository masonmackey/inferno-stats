"""OSRS-themed color palette and Rich styling."""

from rich.style import Style
from rich.theme import Theme

# OSRS color palette
GOLD = "#FFD700"
GREEN = "#00FF00"
RED = "#FF3333"
ORANGE = "#FF981F"
CYAN = "#00FFFF"
YELLOW = "#FFFF00"
LAVA = "#FF4500"
WHITE = "#EEEEEE"
DIM = "#666666"

# Semantic styles
OSRS_THEME = Theme(
    {
        "header": Style(color=GOLD, bold=True),
        "subheader": Style(color=ORANGE, bold=True),
        "success": Style(color=GREEN, bold=True),
        "failure": Style(color=RED, bold=True),
        "info": Style(color=CYAN),
        "dim": Style(color=DIM),
        "commentary": Style(color=CYAN, italic=True),
        "wave.early": Style(color=GREEN),
        "wave.mid": Style(color=ORANGE),
        "wave.late": Style(color=RED),
        "wave.boss": Style(color=GOLD, bold=True),
        "split.fast": Style(color=GREEN),
        "split.slow": Style(color=RED),
        "metric.label": Style(color=WHITE),
        "metric.value": Style(color=GOLD, bold=True),
        "lava": Style(color=LAVA, bold=True),
    }
)


def wave_style(wave: int) -> str:
    """Return the theme style name for a wave number."""
    if wave <= 17:
        return "wave.early"
    if wave <= 34:
        return "wave.mid"
    if wave <= 66:
        return "wave.late"
    return "wave.boss"

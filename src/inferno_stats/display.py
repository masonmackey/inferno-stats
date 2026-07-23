"""Rich rendering for Inferno stats output."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from inferno_stats.constants import TOTAL_WAVES, WAVE_SECTIONS, get_section_for_wave
from inferno_stats.models import Attempt, CharacterProfile
from inferno_stats.theme import get_theme, wave_style

# Theme name is set by CLI and read by get_console
_active_theme: str = "classic"


def set_active_theme(name: str) -> None:
    """Set the theme used by get_console."""
    global _active_theme
    _active_theme = name


def get_console() -> Console:
    """Create a themed Rich console."""
    return Console(theme=get_theme(_active_theme))


def is_clean() -> bool:
    """Check if the active theme is clean."""
    return _active_theme == "clean"


def format_time(seconds: float) -> str:
    """Format seconds into human-readable time.

    < 60m: MM:SS
    >= 60m: Xh YYm ZZs
    """
    if seconds <= 0:
        return "--:--"
    total_minutes = int(seconds // 60)
    secs = int(seconds % 60)
    if total_minutes < 60:
        return f"{total_minutes}:{secs:02d}"
    hours = total_minutes // 60
    mins = total_minutes % 60
    return f"{hours}h {mins:02d}m {secs:02d}s"


def format_duration_short(seconds: float) -> str:
    """Compact duration for tables."""
    if seconds <= 0:
        return "--"
    total_minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{total_minutes}:{secs:02d}"


def _section_label(section: dict[str, str] | None, use_short: bool = False) -> str:
    """Build a section label, optionally compact."""
    if not section:
        return "?"
    name = section["short"] if use_short else section["name"]
    if use_short:
        # Clean: emoji only on boss waves (Jad, 3x Jad, Zuk)
        if name in ("Jad", "3x Jad", "Zuk"):
            return f"{section['emoji']} {name}"
        return name
    return f"{section['emoji']} {name}"


def render_stats_summary(console: Console, profile: CharacterProfile) -> None:
    """Render the main stats dashboard."""
    valid = profile.valid_attempts
    completions = profile.completions
    total = len(valid)
    comp_count = len(completions)
    rate = f"{comp_count / total * 100:.1f}%" if total > 0 else "0%"
    best = profile.best_wave

    pb = profile.pb
    pb_time = format_time(pb.effective_duration_seconds) if pb and pb.success else "--"

    # Journey dates
    first_date = valid[0].timestamp.strftime("%b %d, %Y") if valid else "--"
    last_date = valid[-1].timestamp.strftime("%b %d, %Y") if valid else "--"
    if valid and len(valid) > 1:
        days = (valid[-1].timestamp - valid[0].timestamp).days
        journey = f"{days} days"
    else:
        journey = "--"

    # Cape date
    cape_date = completions[0].timestamp.strftime("%b %d, %Y") if completions else "--"

    # Build the summary panel
    lines = Text()
    lines.append("\n")

    def add_metric(label: str, value: str) -> None:
        lines.append(f"  {label:<20}", style="metric.label")
        lines.append(f"{value}\n", style="metric.value")

    add_metric("Total Attempts:", str(total))
    add_metric("Completions:", str(comp_count))
    add_metric("Completion Rate:", rate)
    add_metric("Best Wave:", f"{best}/{TOTAL_WAVES}" + (" \U0001f451" if best == TOTAL_WAVES else ""))
    add_metric("PB Time:", pb_time)
    lines.append("\n")
    add_metric("First Attempt:", first_date)
    if completions:
        add_metric("Cape Earned:", cape_date)
    add_metric("Last Attempt:", last_date)
    add_metric("Journey:", journey)
    lines.append("\n")

    # Death heatmap
    lines.append("  Death Heatmap:\n", style="subheader")
    death_counts: dict[str, int] = {}
    for attempt in profile.failures:
        section = get_section_for_wave(attempt.death_wave)
        name = section["name"] if section else "Unknown"
        death_counts[name] = death_counts.get(name, 0) + 1

    clean = is_clean()
    for (_, _), info in WAVE_SECTIONS.items():
        name = info["name"]
        short = info.get("short", name)
        count = death_counts.get(name, 0)
        bar = "\u2588" * count if count > 0 else "\u2591"
        label = short if clean else f"{info['emoji']} {name}"
        style = "dim" if count == 0 else "death"
        lines.append(f"  {label:<14}", style="metric.label")
        lines.append(f"{bar} ", style=style)
        if count > 0:
            lines.append(f"({count})", style="dim")
        lines.append("\n")

    lines.append("\n")

    title = f"\U0001f525 INFERNO STATS: {profile.name} \U0001f525"
    console.print(Panel(lines, title=title, title_align="center", border_style="header", padding=(0, 1)))


def render_history_table(console: Console, profile: CharacterProfile) -> None:
    """Render a table of all attempts."""
    clean = is_clean()

    table = Table(
        title=f"\U0001f525 Attempt History: {profile.name}",
        title_style="header",
        border_style="dim",
        show_lines=False,
        pad_edge=True,
    )

    table.add_column("#", style="dim", justify="right", width=4)
    table.add_column("Date", style="date", width=12)
    table.add_column("Wave", justify="center", width=6)
    table.add_column("Section", width=12)
    table.add_column("Duration", justify="right", width=10)
    table.add_column("Status", justify="center", width=8)
    table.add_column("Setup", justify="center", width=8)
    table.add_column("Task", justify="center", width=6)

    for attempt in profile.attempts:
        if not attempt.data_valid:
            table.add_row(
                str(attempt.number),
                attempt.timestamp.strftime("%b %d %H:%M"),
                f"W{attempt.death_wave}",
                "--",
                "--",
                "[dim]bad data[/dim]",
                "",
                "",
            )
            continue

        section = get_section_for_wave(attempt.death_wave)
        section_label = _section_label(section, use_short=clean)

        if attempt.success:
            status = "[success]\u2714 Cape[/success]"
        else:
            status = "[death]\U0001f480[/death]"

        duration = format_duration_short(attempt.effective_duration_seconds)
        setup = attempt.gear_setup or "[dim]-[/dim]"
        task = "\u2714" if attempt.on_task else ("\u2718" if attempt.on_task is False else "[dim]-[/dim]")

        # Wave column: only color boss waves, otherwise plain
        if clean:
            wave_text = Text(f"W{attempt.death_wave}", style="wave.boss" if attempt.death_wave >= 67 else "dim")
        else:
            wave_text = Text(f"W{attempt.death_wave}", style=wave_style(attempt.death_wave))

        table.add_row(
            str(attempt.number),
            attempt.timestamp.strftime("%b %d %H:%M"),
            wave_text,
            section_label,
            duration,
            status,
            setup,
            task,
        )

    console.print(table)


def render_attempt_detail(console: Console, attempt: Attempt, avg_splits: dict[int, float] | None = None) -> None:
    """Render detailed view of a single attempt with splits."""
    clean = is_clean()
    section = get_section_for_wave(attempt.death_wave)
    status_str = "\u2714 Success" if attempt.success else f"\U0001f480 Wave {attempt.death_wave}"
    status_style = "success" if attempt.success else "death"

    header = Text()
    header.append(f"\n  Attempt #{attempt.number}", style="header")
    header.append(f"  |  {attempt.timestamp.strftime('%b %d, %Y %H:%M')}", style="date")
    header.append(f"  |  ", style="dim")
    header.append(status_str, style=status_style)
    if section:
        label = _section_label(section, use_short=clean)
        header.append(f"  ({label})", style="dim")
    header.append("\n")

    if attempt.gear_setup or attempt.on_task is not None:
        header.append("  ", style="dim")
        if attempt.gear_setup:
            header.append(f"Setup: {attempt.gear_setup}  ", style="info")
        if attempt.on_task is not None:
            task_str = "On task" if attempt.on_task else "Off task"
            header.append(f"| {task_str}", style="info")
        header.append("\n")

    if attempt.notes:
        header.append(f"  Note: {attempt.notes}\n", style="commentary")

    console.print(header)

    if not attempt.splits:
        console.print("  [dim]No split data for this attempt.[/dim]\n")
        console.print(f"  Duration: [metric.value]{format_time(attempt.effective_duration_seconds)}[/metric.value]\n")
        return

    table = Table(border_style="dim", show_lines=False, pad_edge=True, show_header=True)
    table.add_column("Wave", justify="center", width=6)
    table.add_column("Section", width=12)
    table.add_column("Split", justify="right", width=10)
    table.add_column("Segment", justify="right", width=10)
    if avg_splits:
        table.add_column("vs Avg", justify="right", width=10)

    for split in attempt.splits:
        section_info = get_section_for_wave(split.wave)
        section_label = _section_label(section_info, use_short=clean)

        if clean:
            w_style = "wave.boss" if split.wave >= 67 else "dim"
        else:
            w_style = wave_style(split.wave)

        row: list = [
            Text(f"W{split.wave}", style=w_style),
            section_label,
            format_duration_short(split.cumulative_seconds),
            f"+{format_duration_short(split.segment_seconds)}",
        ]

        if avg_splits and split.wave in avg_splits:
            avg = avg_splits[split.wave]
            delta = split.segment_seconds - avg
            if abs(delta) < 5:
                row.append(Text("~avg", style="dim"))
            elif delta < 0:
                row.append(Text(f"-{format_duration_short(abs(delta))}", style="split.fast"))
            else:
                row.append(Text(f"+{format_duration_short(delta)}", style="split.slow"))

        table.add_row(*row)

    console.print(table)
    console.print(
        f"\n  Total: [metric.value]{format_time(attempt.effective_duration_seconds)}[/metric.value]\n"
    )


def render_comparison(console: Console, a: Attempt, b: Attempt) -> None:
    """Render side-by-side comparison of two attempts."""
    clean = is_clean()

    table = Table(
        title=f"Attempt #{a.number} vs #{b.number}",
        title_style="header",
        border_style="dim",
        show_lines=False,
    )

    table.add_column("Wave", justify="center", width=6)
    table.add_column(f"#{a.number} Split", justify="right", width=10)
    table.add_column(f"#{a.number} Seg", justify="right", width=10)
    table.add_column(f"#{b.number} Split", justify="right", width=10)
    table.add_column(f"#{b.number} Seg", justify="right", width=10)
    table.add_column("Delta", justify="right", width=10)

    a_splits = {s.wave: s for s in a.splits}
    b_splits = {s.wave: s for s in b.splits}
    all_waves = sorted(set(a_splits.keys()) | set(b_splits.keys()))

    for wave in all_waves:
        sa = a_splits.get(wave)
        sb = b_splits.get(wave)

        if clean:
            w_style = "wave.boss" if wave >= 67 else "dim"
        else:
            w_style = wave_style(wave)

        a_split = format_duration_short(sa.cumulative_seconds) if sa else "--"
        a_seg = f"+{format_duration_short(sa.segment_seconds)}" if sa else "--"
        b_split = format_duration_short(sb.cumulative_seconds) if sb else "--"
        b_seg = f"+{format_duration_short(sb.segment_seconds)}" if sb else "--"

        if sa and sb:
            delta = sb.cumulative_seconds - sa.cumulative_seconds
            if abs(delta) < 5:
                delta_text = Text("~even", style="dim")
            elif delta < 0:
                delta_text = Text(f"-{format_duration_short(abs(delta))}", style="split.fast")
            else:
                delta_text = Text(f"+{format_duration_short(delta)}", style="split.slow")
        else:
            delta_text = Text("--", style="dim")

        table.add_row(Text(f"W{wave}", style=w_style), a_split, a_seg, b_split, b_seg, delta_text)

    console.print(table)

    # Total comparison
    a_total = format_time(a.effective_duration_seconds)
    b_total = format_time(b.effective_duration_seconds)
    console.print(f"\n  #{a.number} Total: [metric.value]{a_total}[/metric.value]    #{b.number} Total: [metric.value]{b_total}[/metric.value]\n")

"""CLI entry point — Click command group for inferno-stats."""

from __future__ import annotations

import functools
from pathlib import Path

import click
from rich.console import Console

from inferno_stats.analysis import compute_avg_segments, generate_commentary
from inferno_stats.constants import GEAR_SETUPS
from inferno_stats.display import (
    get_console,
    render_attempt_detail,
    render_comparison,
    render_history_table,
    render_stats_summary,
    set_active_theme,
)
from inferno_stats.models import CharacterProfile
from inferno_stats.share import export_markdown, export_svg
from inferno_stats.store import (
    discover_characters,
    get_data_dir,
    load_profile,
    tag_attempt as store_tag_attempt,
)


COMMANDS_EPILOG = """\b
Commands:
  inferno stats              Summary dashboard with death heatmap
  inferno history            All attempts in a table
  inferno attempt N          Detailed splits for attempt #N
  inferno pb                 Personal best breakdown
  inferno progress           Trend analysis + smart commentary
  inferno compare N M        Side-by-side two attempts
  inferno tag N [OPTIONS]    Tag with --setup, --task/--no-task, --notes
  inferno share [OPTIONS]    Export as --format svg/md
"""


class InfernoContext:
    """Shared context passed between CLI commands."""

    def __init__(self, profile: CharacterProfile, console: Console):
        self.profile = profile
        self.console = console


pass_ctx = click.make_pass_decorator(InfernoContext)


def common_options(f):
    """Add --theme to any subcommand. Applied before pass_ctx resolves."""
    @click.option(
        "--theme",
        type=click.Choice(["classic", "clean"]),
        default="clean",
        help="Display theme (classic = full color, clean = toned down).",
    )
    @functools.wraps(f)
    def wrapper(theme, *args, **kwargs):
        set_active_theme(theme)
        # Rebuild console with the right theme
        ctx_obj = click.get_current_context().find_object(InfernoContext)
        if ctx_obj:
            ctx_obj.console = get_console()
        return f(*args, **kwargs)
    return wrapper


@click.group(epilog=COMMANDS_EPILOG)
@click.option(
    "--data-dir",
    envvar="INFERNO_STATS_DIR",
    default=None,
    type=click.Path(exists=False),
    help="Path to RuneLite inferno-stats directory.",
)
@click.option(
    "--character",
    "-c",
    default=None,
    help="Character name (auto-detected if only one exists).",
)
@click.pass_context
def inferno(ctx: click.Context, data_dir: str | None, character: str | None) -> None:
    """\U0001f525 Inferno Stats — OSRS Inferno attempt tracker and analyzer."""
    data_path = Path(data_dir) if data_dir else get_data_dir()
    set_active_theme("clean")
    console = get_console()

    characters = discover_characters(data_path)
    if not characters:
        console.print(f"[failure]No character data found in {data_path}[/failure]")
        console.print("Make sure the RuneLite inferno-stats plugin has saved some attempts.")
        ctx.exit(1)

    if character is None:
        if len(characters) == 1:
            character = characters[0]
        else:
            console.print("[header]Multiple characters found:[/header]")
            for name in characters:
                console.print(f"  - {name}")
            console.print("\nUse [info]--character 'Name'[/info] to select one.")
            ctx.exit(1)

    if character not in characters:
        console.print(f"[failure]Character '{character}' not found.[/failure]")
        console.print(f"Available: {', '.join(characters)}")
        ctx.exit(1)

    profile = load_profile(character, data_path)
    ctx.ensure_object(dict)
    ctx.obj = InfernoContext(profile=profile, console=console)


@inferno.command(epilog=COMMANDS_EPILOG)
@common_options
@pass_ctx
def stats(ctx: InfernoContext) -> None:
    """Summary dashboard — attempts, completions, best wave, death heatmap."""
    render_stats_summary(ctx.console, ctx.profile)


@inferno.command(epilog=COMMANDS_EPILOG)
@common_options
@pass_ctx
def history(ctx: InfernoContext) -> None:
    """All attempts in a rich table."""
    render_history_table(ctx.console, ctx.profile)


@inferno.command(epilog=COMMANDS_EPILOG)
@common_options
@click.argument("number", type=int)
@pass_ctx
def attempt(ctx: InfernoContext, number: int) -> None:
    """Detailed split view for attempt #N."""
    valid = ctx.profile.attempts
    match = next((a for a in valid if a.number == number), None)
    if match is None:
        ctx.console.print(f"[failure]Attempt #{number} not found.[/failure]")
        ctx.console.print(f"Valid range: 1-{len(valid)}")
        return

    avg_splits = compute_avg_segments(ctx.profile)
    render_attempt_detail(ctx.console, match, avg_splits)


@inferno.command(epilog=COMMANDS_EPILOG)
@common_options
@pass_ctx
def pb(ctx: InfernoContext) -> None:
    """Personal best breakdown with splits."""
    best = ctx.profile.pb
    if best is None:
        ctx.console.print("[failure]No attempts found.[/failure]")
        return

    ctx.console.print()
    if best.success:
        ctx.console.print("[success]\U0001f451 PERSONAL BEST — CAPE EARNED \U0001f451[/success]")
    else:
        ctx.console.print(f"[header]\U0001f525 Best Attempt — Wave {best.death_wave}[/header]")

    avg_splits = compute_avg_segments(ctx.profile)
    render_attempt_detail(ctx.console, best, avg_splits)


@inferno.command(epilog=COMMANDS_EPILOG)
@common_options
@pass_ctx
def progress(ctx: InfernoContext) -> None:
    """Trend analysis with smart commentary."""
    ctx.console.print()
    ctx.console.print("[header]\U0001f525 Progression Analysis[/header]\n")

    commentary = generate_commentary(ctx.profile)
    if not commentary:
        ctx.console.print("[dim]Not enough data for analysis yet. Keep going![/dim]")
        return

    for line in commentary:
        ctx.console.print(f"  [commentary]\u2022 {line}[/commentary]")
    ctx.console.print()


@inferno.command(epilog=COMMANDS_EPILOG)
@common_options
@click.argument("a", type=int)
@click.argument("b", type=int)
@pass_ctx
def compare(ctx: InfernoContext, a: int, b: int) -> None:
    """Side-by-side comparison of two attempts."""
    attempts = ctx.profile.attempts
    attempt_a = next((x for x in attempts if x.number == a), None)
    attempt_b = next((x for x in attempts if x.number == b), None)

    if attempt_a is None or attempt_b is None:
        missing = a if attempt_a is None else b
        ctx.console.print(f"[failure]Attempt #{missing} not found.[/failure]")
        return

    render_comparison(ctx.console, attempt_a, attempt_b)


@inferno.command(epilog=COMMANDS_EPILOG)
@click.argument("number", type=int)
@click.option("--setup", type=click.Choice(GEAR_SETUPS), help="Gear setup used.")
@click.option("--task/--no-task", default=None, help="Whether on slayer task.")
@click.option("--notes", type=str, default=None, help="Notes about this attempt.")
@pass_ctx
def tag(ctx: InfernoContext, number: int, setup: str | None, task: bool | None, notes: str | None) -> None:
    """Tag attempt #N with gear setup, task status, or notes."""
    match = next((a for a in ctx.profile.attempts if a.number == number), None)
    if match is None:
        ctx.console.print(f"[failure]Attempt #{number} not found.[/failure]")
        return

    if setup is None and task is None and notes is None:
        ctx.console.print("[dim]Nothing to tag. Use --setup, --task/--no-task, or --notes.[/dim]")
        return

    store_tag_attempt(ctx.profile.name, match, gear_setup=setup, on_task=task, notes=notes)
    ctx.console.print(f"[success]\u2714 Tagged attempt #{number}[/success]")

    if setup:
        ctx.console.print(f"  Setup: [info]{setup}[/info]")
    if task is not None:
        ctx.console.print(f"  Task: [info]{'on' if task else 'off'}[/info]")
    if notes:
        ctx.console.print(f"  Notes: [info]{notes}[/info]")


@inferno.command(epilog=COMMANDS_EPILOG)
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["svg", "md"]),
    default="svg",
    help="Export format.",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default=None,
    help="Output file path.",
)
@pass_ctx
def share(ctx: InfernoContext, fmt: str, output: str | None) -> None:
    """Export stats as SVG image or Markdown."""
    name_slug = ctx.profile.name.lower().replace(" ", "-")

    if output is None:
        ext = "svg" if fmt == "svg" else "md"
        output = f"inferno-stats-{name_slug}.{ext}"

    path = Path(output)

    if fmt == "svg":
        export_svg(ctx.profile, path)
    else:
        export_markdown(ctx.profile, path)

    ctx.console.print(f"[success]\u2714 Exported to {path}[/success]")

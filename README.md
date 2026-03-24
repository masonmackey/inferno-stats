# inferno-stats

OSRS Inferno attempt tracker and analyzer for [RuneLite](https://runelite.net/).

Reads your local data from the [inferno-stats plugin](https://github.com/InfernoStats/InfernoStats) and gives you a rich, OSRS-themed CLI with progression analysis, split comparisons, and shareable exports.

## Install

```bash
pip install inferno-stats
```

Or from source:

```bash
git clone https://github.com/masonmackey/inferno-stats.git
cd inferno-stats
pip install -e .
```

Requires Python 3.9+ and the RuneLite inferno-stats plugin.

## Commands

### `inferno stats`
Summary dashboard with attempt count, completion rate, best wave, PB time, and a death heatmap showing where you die most.

### `inferno history`
All attempts in a color-coded table with wave sections, durations, and status.

### `inferno attempt N`
Detailed split view for attempt #N with segment times and comparison vs your averages.

### `inferno pb`
Personal best breakdown — fastest completion or deepest attempt if no cape yet.

### `inferno progress`
Smart commentary engine that analyzes your data and surfaces insights:
- Death wall detection (where you die most)
- Section improvement trends
- Consistency checks on early waves
- Outlier detection (unusually slow segments)
- Journey summary and speed run context

### `inferno compare N M`
Side-by-side split comparison between any two attempts.

### `inferno tag N`
Add metadata to attempts that the plugin doesn't track:
```bash
inferno tag 18 --setup bowfa --no-task --notes "First cape!"
```

Supported setups: `tbow`, `bowfa`, `shadow`, `other`

### `inferno share`
Export your stats as SVG or Markdown:
```bash
inferno share --format svg -o my-stats.svg
inferno share --format md -o my-stats.md
```

## Options

```
--data-dir PATH    Custom path to RuneLite inferno-stats directory
--character NAME   Select character (auto-detected if only one)
```

## How It Works

The RuneLite inferno-stats plugin saves attempt data as plain text files in `~/.runelite/inferno-stats/`. This tool reads those files, parses the splits, and layers on analysis and rich formatting. Your metadata (gear setup, task status, notes) is stored separately in `~/.inferno-stats/metadata.json`.

## License

MIT

---

*Old School RuneScape is a trademark of Jagex Ltd. This project is not affiliated with or endorsed by Jagex.*

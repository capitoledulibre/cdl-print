# cdl_paper_generator

Generates the Capitole du Libre paper schedule as a print-ready A3 PDF, from
the conference's Pretalx FRAB XML export.

## Getting Started

### Prerequisites

* [uv](https://docs.astral.sh/uv/getting-started/installation/)

### Installing

```shell
uv sync
```

### Running

```shell
uv run python gen.py
```

This fetches the schedule for the current year and writes `conference.pdf`.
Set `CDL_YEAR` to build another edition:

```shell
CDL_YEAR=2025 uv run python gen.py
```

### Options

```shell
uv run python gen.py --year 2026 --output programme.pdf
```

| Option | Default | Description |
| --- | --- | --- |
| `--year` | `$CDL_YEAR`, else the current year | Conference edition to fetch |
| `--url` | derived from `--year` | Schedule XML URL, overriding `--year` |
| `--output` | `conference.pdf` | PDF file to write |
| `--stylesheet` | `style.css` | CSS stylesheet to apply |
| `--locale` | `fr_FR.UTF-8` | Locale used to format dates |

## Configuration

The schedule export does not carry the breaks, so they are declared in the
`BREAKS` tuple at the top of `gen.py`. A break is only printed in a room when
it fits inside that room's programme for the day and overlaps no event, so
all-day workshops and evening-only slots are left untouched.

Rooms listed in `EXCLUDED_ROOMS` are left out of the programme entirely.

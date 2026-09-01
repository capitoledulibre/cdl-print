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
| `--no-qr` | QR codes shown | Leave out the QR code linking to each talk page |
| `--stylesheet` | `style.css` | CSS stylesheet to apply |
| `--locale` | `fr_FR.UTF-8` | Locale used to format dates |

## Configuration

The schedule export does not carry the breaks, so they are declared in the
`BREAKS` tuple at the top of `gen.py`. A break is only printed in a room when
it fits inside that room's programme for the day and overlaps no event, so
all-day workshops and evening-only slots are left untouched.

Rooms listed in `EXCLUDED_ROOMS` are left out of the programme entirely.

## Layout

Each room gets one A3 poster per day, meant to be read from a few metres away
on the door of the room. Slots grow in proportion to their duration, so the
page fills itself and the length of a talk can be seen without reading the
times; gaps in the programme stay visible as gaps.

Events are coloured by format, from the `type` the schedule export carries:
a full orange rule for a long talk, a lighter one for a short talk, and a
blue tint for workshops. A room with at most `POSTER_MODE_MAX_EVENTS` talks
switches to a poster layout with much larger type, so that a room used for a
single workshop does not print two lines of small text on an empty A3.

Every talk carries a QR code to its page on the CFP site, where the abstract
and the feedback form live. Pass `--no-qr` to drop them.

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
| `--schedule-file` | fetch over the network | Read a local XML export instead, ignoring `--year` and `--url` |
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

A room too dense for its sheet has its timeline set a step smaller until it
fits, so a page is never split in two or quietly clipped. Nothing in the 2025
programme needs it; the 2024 one turns two rooms down by a few per cent. A
room that will not fit even at `MIN_TIMELINE_SIZE` aborts the run with a
message naming it, rather than printing something broken. Sizing every room
this way is what makes a run take a few seconds rather than one.

Fira Sans is embedded from `fonts/`, so the PDF renders the same at the print
shop as it does here. It has no glyph for the handful of emoji that reach a
talk title; those still fall back to whatever the generating machine has, so
check them before a print run.

## Tests

```shell
uv run pytest
```

The suite renders the trimmed schedule exports under `tests/fixtures/` -- no
network needed -- and checks that every room gets exactly one page, that no
page loses its footer to clipping, that dense rooms are scaled rather than
split, and that no talk or speaker disappears from the layout. `--schedule-file` is what makes those fixtures usable.

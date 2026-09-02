# cdl_paper_generator

Generates the Capitole du Libre printed matter from the conference's Pretalx
FRAB export. One command, three PDFs:

| File | Format | What it is |
| --- | --- | --- |
| `conference-programme-salles-<year>.pdf` | A3 portrait, one sheet per room and day | The door posters, read standing from a few metres away |
| `conference-programme-global-<year>.pdf` | A1 landscape, one sheet per day | The hall poster: every room side by side, for the entrance |
| `conference-livret-<year>.pdf` | A5, folded and stapled | The pocket booklet: the programme by the hour, and the annexes |

The year comes from the parsed schedule rather than the command line, so a
new edition never overwrites the previous one's PDFs.

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

This fetches the schedule for the current year and writes the three PDFs into
the working directory. Set `CDL_YEAR` to build another edition:

```shell
CDL_YEAR=2025 uv run python gen.py
```

### Options

```shell
uv run python gen.py --only livret --output-dir build
```

| Option | Default | Description |
| --- | --- | --- |
| `--year` | `$CDL_YEAR`, else the current year | Conference edition to fetch |
| `--url` | derived from `--year` | Schedule XML URL, overriding `--year` |
| `--schedule-file` | fetch over the network | Read a local XML export instead, ignoring `--year` and `--url` |
| `--only` | all three | Build only this output (`salles`, `global`, `livret`); repeatable |
| `--output-dir` | the working directory | Where to write the PDFs |
| `--no-qr` | QR codes shown | Leave out the QR code linking to each talk page |
| `--locale` | `fr_FR.UTF-8` | Locale used to format dates |

## Layout

`gen.py` orchestrates; each output is a module beside it.

| Module | Role |
| --- | --- |
| `schedule.py` | Parses the export into conference, days, rooms, events and people. Knows nothing about pages. |
| `render.py` | Shared by every output: escaping, QR codes, fitting a page. |
| `posters.py` + `styles/posters.css` | The door posters |
| `overview.py` + `styles/overview.css` | The hall poster |
| `booklet.py` + `styles/booklet.css` | The booklet |
| `content.py` | Booklet copy that does not come from the export: editorial, first-timer guide, the curated highlights, stands, partners, practical info. **Mostly placeholder text**; the first-timer page is drawn from capitoledulibre.org. |

## Printing in black and white

The run is printed in greyscale, where two tints of the same hue come out as
the same grey. Nothing that matters is told apart by colour alone:

* a workshop carries a hatch, a doubled left rule, an outlined rather than
  filled room badge, and the word `Atelier` spelled out;
* the short and long talk formats no longer differ by tint at all, because
  the height of a block already says how long a talk runs.

Colour still does its work on screen and in a colour run; it is never the
only cue. Check any change against a greyscale conversion of the PDF.

The booklet's dark pages survive greyscale with good contrast, but a
full-bleed near-black A5 page is heavy on toner in a long print run. If that
matters, invert `.page.dark` in `styles/booklet.css` and keep the dark ground
for the cover alone.

## Configuration

The export does not carry the breaks, so they are declared in the `BREAKS`
tuple at the top of `schedule.py`. A break is only printed in a room when it
fits inside that room's programme for the day and overlaps no event, so
all-day workshops and evening-only slots are left untouched. Rooms listed in
`EXCLUDED_ROOMS` are left out entirely.

### The door posters

Slots grow in proportion to their duration, so the page fills itself and the
length of a talk can be seen without reading the times. Events are coloured
by format, from the `type` the export carries. A room with at most
`POSTER_MODE_MAX_EVENTS` talks switches to a much larger poster layout.

A room too dense for its sheet has its timeline set a step smaller until it
fits, so a page is never split in two or quietly clipped. A room that will
not fit even at `MIN_TIMELINE_SIZE` aborts the run with a message naming it.
Sizing every room this way is what makes a run take a few seconds.

### The hall poster

Rooms are columns, time runs down the sheet, and a talk sits at its real
position. Titles are shortened to what their block can hold, computed from
the sheet geometry: WeasyPrint crashes laying out a grid item that carries
`overflow: hidden`, so clipping has to happen before the markup is written.

### The booklet

The cover is the edition poster from `assets/`, and the annexes wear the dark
2026 identity; the programme pages stay white so they are readable and cheap
to print.

The programme is organised **by the hour**, not as one long chronological
list: someone holding the booklet is asking "it is eleven, what is on?". Each
day opens on a dark page listing its hours, then every start time gets a
full-width orange band followed by one card per talk, carrying the room, the
length, the speakers, a trimmed abstract and a QR code to the full one. A
running head repeats the day and the current hour, because a band's cards run
over several pages.

The booklet opens with a **`Premier Capitole du Libre ?`** page -- free but
registration required, come and go as you like, start at the village
associatif, talks are filmed -- and an **`À ne pas manquer`** page. The
highlights are curated in `content.py` by a fragment of each talk's title; a
fragment matching nothing is reported when the booklet is built, so a talk
renamed in Pretalx cannot quietly drop off the page.

There is no timetable grid in the booklet. At A5 it came out at 5.25pt with
titles cut to twenty characters -- unreadable, and no longer information. The
bird's-eye view is the job of the A1 hall poster. What the booklet has
instead is a **`Salle par salle`** index at the back, one line per talk, for
whoever is already sitting in a room and wants to know what follows, and an
alphabetical **`Les intervenants`** index, filed through the locale so that
É files with E, listing each person's talks with the hour and the room.

The page count is rounded up to a multiple of four with note pages, so the
booklet can be folded and stapled. Folios are printed like a book's: none on
the cover or the back.

Fira Sans is embedded from `fonts/`, so the PDFs render the same at the print
shop as they do here. It has no glyph for the handful of emoji that reach a
talk title; those still fall back to whatever the generating machine has, so
check them before a print run.

## Tests

```shell
uv run pytest
```

The suite renders the trimmed schedule exports under `tests/fixtures/` -- no
network needed -- and checks the shapes a printer depends on: one page per
room and day, no page losing its footer to clipping, dense rooms scaled
rather than split, one hall sheet per day, a booklet page count that folds,
no talk or speaker disappearing from any of the three, and file names that
carry the edition.

# cdl-print

Generates the Capitole du Libre printed matter from the conference's Pretalx
FRAB export. One command, six PDFs:

| File | Format | What it is |
| --- | --- | --- |
| `conference-programme-salles-<year>.pdf` | A3 portrait, one sheet per room and day | The door posters, read standing from a few metres away |
| `conference-panneaux-salles-<year>.pdf` | A3 landscape, one sheet per room | The room signs: the name alone, read from the far end of the corridor |
| `conference-programme-global-<year>.pdf` | A0 landscape, one sheet per day | The hall poster: every room side by side, for the entrance |
| `conference-livret-<year>.pdf` | A5, folded and stapled | The pocket booklet: the programme by the hour, and the annexes |
| `conference-feuilles-salles-<year>.pdf` | A4 portrait, one per room and day | The room sheets: the working document of the volunteer on duty |
| `conference-depliant-<year>.pdf` | A4 landscape, folded in three | The leaflet, for whoever will not carry a booklet |

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

This fetches the schedule for the current year and writes the six PDFs into
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
| `--only` | all of them | Build only this output (`salles`, `panneaux`, `global`, `livret`, `feuilles`, `depliant`); repeatable |
| `--output-dir` | the working directory | Where to write the PDFs |
| `--audience-file` | fetch over the network | Read the "public visé" answers from a local API dump |
| `--no-audience` | shown | Leave out who each talk is for |
| `--no-qr` | QR codes shown | Leave out the QR code linking to each talk page |
| `--locale` | `fr_FR.UTF-8` | Locale used to format dates |

## Layout

`gen.py` orchestrates; each output is a module beside it.

| Module | Role |
| --- | --- |
| `schedule.py` | Parses the export into conference, days, rooms, events and people. Knows nothing about pages. |
| `render.py` | Shared by every output: escaping, QR codes, fitting a page. |
| `posters.py` + `styles/posters.css` | The door posters |
| `signage.py` + `styles/signage.css` | The room signs |
| `overview.py` + `styles/overview.css` | The hall poster |
| `booklet.py` + `styles/booklet.css` | The booklet |
| `roomsheets.py` + `styles/roomsheets.css` | The room sheets |
| `leaflet.py` + `styles/leaflet.css` | The leaflet |
| `audience.py` | Who each talk is for, fetched from the Pretalx submissions API |
| `content.py` | Booklet copy that does not come from the export: editorial, first-timer guide, the curated highlights, stands, partners, practical info. **Mostly placeholder text**; the first-timer page is drawn from capitoledulibre.org. |

## Who each talk is for

`Quel est le public visé ?` is a Pretalx **custom question**, and no schedule
export carries custom answers -- not the FRAB XML, not `schedule.json`. They
come from the submissions API, which serves them without a token as long as
the question is public, and are joined to the schedule on the talk code both
carry:

```
/api/events/cdl-<year>/submissions/?expand=answers.question
```

The question is identified by its Pretalx identifier rather than its wording,
with the label as a fallback, so rephrasing it does not break the join.

Speakers answer in anything from two words to a paragraph -- for 2026 the
median is 37 characters and the longest is 289 -- so it is treated as prose,
not as a badge with a fixed vocabulary. A booklet card gives it a line of its
own under the abstract; a door poster shows it only when it is at most
`AUDIENCE_MAX_LENGTH` characters, since that sheet is read from a few metres
away and must stay uncluttered.

It is an enrichment, never a dependency: a fetch that fails warns and the run
goes on without it. `--audience-file` reads a saved API dump instead, which is
also how the tests work offline.

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

### The room signs

The companion sheet of the door poster, and deliberately the emptier of the
two: someone at the far end of a corridor is not reading a programme, they
are looking for a number. So the sheet carries the room name and nothing
else, set as large as the paper allows, and it is landscape where the
programme is portrait -- a room name is one short word, and the wider sheet
is what buys the type its size.

One sheet per room, not per room and per day: a door does not change name
between Saturday and Sunday, so a room used on both days is printed once.

The name is sized the way a dense room's timeline is: down a step at a time
from `BASE_NAME_SIZE` until it holds its sheet, so `Hall C` shrinks rather
than pushing the footer onto a second page, and a name that will not fit even
at `MIN_NAME_SIZE` aborts the run instead of printing something broken.

### The hall poster

Rooms are columns, time runs down the sheet, and a talk sits at its real
position. Titles are shortened to what their block can hold, computed from
the sheet geometry: WeasyPrint crashes laying out a grid item that carries
`overflow: hidden`, so clipping has to happen before the markup is written.

A block shorter than its text stretches the grid instead, and the end of the
day lands alone on an extra A0 sheet. Back-to-back lightning talks are
therefore one block named after the session, as on the door posters, and the
build refuses a hall poster that is not exactly one sheet per day.

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
bird's-eye view is the job of the A0 hall poster. What the booklet has
instead is a **`Salle par salle`** index at the back, one line per talk, for
whoever is already sitting in a room and wants to know what follows, and an
alphabetical **`Les intervenants`** index, filed through the locale so that
É files with E, listing each person's talks with the hour and the room.

The page count is rounded up to a multiple of four with note pages, so the
booklet can be folded and stapled. Folios are printed like a book's: none on
the cover or the back.

Fira Sans is embedded from `fonts/`, so the PDFs render the same at the print
shop as they do here. Anything the font cannot draw is dropped from the text
rather than left to a fallback: a few talk titles carry emoji, which would
otherwise be a tofu box at the print shop and a grey blob in a greyscale run.
The coverage is read from the font file itself, so replacing the font changes
what survives without any code edit.

### The room sheets

Not a programme: the working document of whoever holds a room. Each talk with
its length, three boxes to tick -- speaker arrived, sound and video tested,
timing started -- handover fields for the morning and afternoon volunteers,
and a ruled space for incidents.

It is also the only thing in the whole run that says a speaker **refused to
be filmed**. The export carries that in `<recording><optout>`, which the
generic parse branch could not see because `<recording>` wraps its own
children; the sheet now shows it twice, once as a notice at the top and once
on the line itself.

### The leaflet

One A4 landscape sheet, three 99mm panels a side, letter fold. Page one is
the outside, left to right: the flap that folds inward, the back, the front
cover. Page two is the inside as it reads opened flat. **Confirm the fold
against a paper dummy before a print run.**

The programme runs across all three inside panels as one flow, grouped under
each hour. One day per panel was tried first and broke on the 2026 export,
where sixty-six Saturday talks did not fit a single panel and turned the
sheet into an unfoldable third page. Three columns hold both days with room
to spare, which also bought back the hour headings and a readable 7pt.

A panel that outgrows its space would silently become a third page, so the
build refuses anything but two.

## Tests

```shell
uv run pytest
```

The suite renders the trimmed schedule exports under `tests/fixtures/` -- no
network needed -- and checks the shapes a printer depends on: one page per
room and day, no page losing its footer to clipping, dense rooms scaled
rather than split, one hall sheet per day, a booklet page count that folds,
no talk or speaker disappearing from any of the three, one sign per room
whichever days it is used, and file names that carry the edition.

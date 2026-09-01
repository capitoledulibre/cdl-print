
import argparse
import functools
import html
import io
import locale
import os
import re
import sys
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timedelta
from xml.etree import ElementTree

from urllib.request import urlopen

import segno
from weasyprint import CSS, HTML
from weasyprint.text.fonts import FontConfiguration

# --- Configuration ---------------------------------------------------------
#
# Everything that changes from one edition to the next comes from the
# environment or the command line, so that a new year needs no code edit.

YEAR_ENV_VAR = 'CDL_YEAR'
SCHEDULE_URL_TEMPLATE = (
    'https://cfp.capitoledulibre.org/cdl-{year}/schedule/export/schedule.xml')
DEFAULT_OUTPUT = 'conference.pdf'
DEFAULT_STYLESHEET = 'style.css'
DEFAULT_LOCALE = 'fr_FR.UTF-8'

# Rooms with at most this many slots are laid out as a poster rather than
# a timeline, so a nearly empty day does not become a nearly empty page.
POSTER_MODE_MAX_EVENTS = 2

# Ink colour of the QR codes linking to each talk page.
QR_COLOUR = '#111111'

# Type size of a timeline, in px, matching .timeline in the stylesheet. A room
# too dense for the sheet is rendered again a step smaller until it fits.
BASE_TIMELINE_SIZE = 16
MIN_TIMELINE_SIZE = 9
TIMELINE_SIZE_STEP = 0.5

# ISO weekday numbers, as returned by datetime.isoweekday().
SATURDAY = 6

# <conference> children worth keeping; the rest of the export is ignored.
CONFERENCE_DETAILS = frozenset({'title', 'venue', 'city',
                               'start_date', 'end_date', 'days_count'})

# Rooms left out of the printed programme entirely, by name.
EXCLUDED_ROOMS: frozenset[str] = frozenset()


@dataclass(frozen=True)
class Break:
    """A pause to weave into a room's programme.

    The schedule export does not carry the breaks, so they are added here.
    `weekdays` restricts the break to those ISO weekdays; None means every
    day of the conference.
    """

    title: str
    start: str
    duration: str
    weekdays: frozenset[int] | None = None


BREAKS = (
    Break(title='Pause déjeuner', start='12:30', duration='01:30'),
    # Sunday ends early enough not to need an afternoon break.
    Break(title='Pause', start='16:00', duration='00:30',
          weekdays=frozenset({SATURDAY})),
)


def default_year() -> int:
    """Conference edition to build unless --year says otherwise.

    The current year, or $CDL_YEAR when set.
    """
    override = os.environ.get(YEAR_ENV_VAR)
    if override:
        try:
            return int(override)
        except ValueError:
            print(f'warning: {YEAR_ENV_VAR}={override!r} is not a year, '
                  'using the current one instead',
                  file=sys.stderr)
    return datetime.now().year


def _hours_minutes(value: str) -> tuple[int, int]:
    """Split an 'HH:MM' string into an (hours, minutes) pair."""
    hours, minutes = str(value).split(':')
    return int(hours), int(minutes)


def _datetime_at(date: datetime, hhmm: str) -> datetime:
    """Combine a day with an 'HH:MM' wall-clock time."""
    hours, minutes = _hours_minutes(hhmm)
    return datetime(year=date.year,
                    month=date.month,
                    day=date.day,
                    hour=hours,
                    minute=minutes)


def _overlaps(first_start: datetime, first_end: datetime,
              second_start: datetime, second_end: datetime) -> bool:
    """Whether two half-open time ranges intersect.

    Ranges that merely touch (one ends exactly when the other starts) do not
    overlap, so a break may be slotted flush against a talk.
    """
    return first_start < second_end and second_start < first_end


class Conference(object):
    """A whole edition: its days, and the rooms and events they hold."""

    def __init__(self, source):
        self._source = source
        self._days: dict[datetime, Day] = {}

    def __str__(self):
        return self._title

    @property
    def _rooms(self) -> dict[str, 'Room']:
        """Every room of the edition, keyed by name.

        A room used on both days appears once, as its second day: rooms are
        built per day, so use Day._rooms to reach a particular one.
        """
        rooms = {}
        for day in self._days.values():
            rooms.update(day._rooms)
        return rooms

    @property
    def _events(self) -> dict[str, 'Event']:
        events = {}
        for day in self._days.values():
            events.update(day._events)
        return events

    @property
    def _persons(self) -> dict[str, 'Person']:
        persons = {}
        for day in self._days.values():
            persons.update(day._persons)
        return persons

    def parse(self):
        tree = ElementTree.parse(self._source)
        for element in tree.getroot():
            if element.tag == 'conference':
                for detail in element:
                    if detail.tag in CONFERENCE_DETAILS:
                        setattr(self, f'_{detail.tag}', detail.text)
            elif element.tag == 'day':
                date = datetime.strptime(element.get('date'), '%Y-%m-%d')
                self._days[date] = Day(date)
                self._days[date].parse(element)


class Day(object):
    """One day of the conference, holding that day's rooms."""

    def __init__(self, date: datetime):
        self._date = date
        self._rooms: dict[str, Room] = {}

    def __str__(self):
        return f'{self._date:%A %d %B}'

    @property
    def _events(self) -> dict[str, 'Event']:
        events = {}
        for room in self._rooms.values():
            events.update(room._events)
        return events

    @property
    def _persons(self) -> dict[str, 'Person']:
        persons = {}
        for event in self._events.values():
            persons.update(event._persons)
        return persons

    def parse(self, day_element):
        for element in day_element:
            if element.tag == 'room':
                name = element.get('name')
                self._rooms[name] = Room(name, self)
                self._rooms[name].parse(element)


class Room(object):
    """A room on a given day.

    A room used on both days of the conference is two Room objects, one per
    day, each holding only that day's events.
    """

    def __init__(self, name: str, day: Day):
        self._name = name
        self._day = day
        self._events: dict[str, Event] = {}

    def __str__(self):
        return self._name

    def sorted_events(self) -> list['Event']:
        return sorted(self._events.values(), key=lambda e: e._start_datetime)

    def parse(self, room_element):
        for element in room_element:
            if element.tag == 'event':
                event_id = element.get('id')
                self._events[event_id] = Event(event_id, self._day)
                self._events[event_id].parse(element)


class Event(object):
    """One slot of the programme: a talk, a workshop or a break."""

    def __init__(self, event_id, day: Day):
        self._id = event_id
        self._day = day
        self._persons: dict[str, Person] = {}

    def __str__(self):
        return self._title

    @property
    def title(self):
        return self._title

    @property
    def _start_datetime(self):
        return _datetime_at(self._day._date, self._start)

    @property
    def _end_datetime(self):
        hours, minutes = _hours_minutes(self._duration)
        return self._start_datetime + timedelta(hours=hours,
                                                minutes=minutes)

    @property
    def persons(self) -> str:
        """The speakers, as a French enumeration; empty when there are none."""
        names = [person._name for person in self._persons.values()]
        if not names:
            return ''
        if len(names) == 1:
            return names[0]
        return '{} et {}'.format(', '.join(names[:-1]), names[-1])

    def parse(self, event_element):
        for element in event_element:
            if element.tag == 'persons':
                for person_element in element:
                    person_id = person_element.get('id')
                    self._persons[person_id] = Person(person_id)
                    self._persons[person_id].parse(person_element)
            else:
                setattr(self, f'_{element.tag}', element.text)


class Person(object):
    """Someone giving a talk or running a workshop."""

    def __init__(self, person_id):
        self._id = person_id
        self._name = ''

    def __str__(self):
        return self._name

    def parse(self, person_element):
        self._name = person_element.text


def build_breaks(room: Room, day: Day, events: list) -> list['Event']:
    """Build the breaks that belong in this room's programme for that day.

    A break is only added when it fits inside the room's programme span --
    from the first event's start to the last event's end -- and overlaps no
    event. All-day workshops, devroom blocks and evening-only slots are
    therefore left untouched instead of being cut in two, and a room that is
    only used in the evening gets no lunch break at all.
    """
    if not events:
        return []

    programme_start = events[0]._start_datetime
    programme_end = events[-1]._end_datetime

    breaks = []
    for index, pause in enumerate(BREAKS):
        if pause.weekdays is not None \
                and day._date.isoweekday() not in pause.weekdays:
            continue

        start = _datetime_at(day._date, pause.start)
        hours, minutes = _hours_minutes(pause.duration)
        end = start + timedelta(hours=hours, minutes=minutes)

        if start < programme_start or end > programme_end:
            continue
        if any(_overlaps(start, end, e._start_datetime, e._end_datetime)
               for e in events):
            continue

        # A unique id per room and per day: the singleton cache in
        # UniqueByConference would otherwise hand out one shared break object
        # for the whole conference.
        event = Event(f'break-{day._date:%Y%m%d}-{room._name}-{index}',
                      day)
        event._title = pause.title
        event._start = pause.start
        event._duration = pause.duration
        event._persons = {}
        event._type = 'pause'
        breaks.append(event)

    return breaks


def event_classes(event: Event) -> str:
    """CSS classes for an event: its family, then its exact format.

    The schedule export types events as 'Conférence 25min', 'Atelier 2h' and
    the like, so the raw value cannot go into a class attribute as is: its
    space would split it into several bogus classes. Emit a slug of it
    alongside a coarse family, so a format the stylesheet does not know about
    still picks up the family styling.
    """
    if event._type == 'pause':
        return 'pause'

    slug = unicodedata.normalize('NFKD', event._type or '')
    slug = slug.encode('ascii', 'ignore').decode('ascii').lower()
    slug = re.sub(r'[^a-z0-9]+', '-', slug).strip('-')

    family = 'workshop' if slug.startswith('atelier') else 'talk'
    return f'{family} {slug}' if slug else family


def clean(value: str) -> str:
    """Prepare export data for the page.

    Escapes it, since titles such as 'Guix & Nix' must not reach the parser as
    markup, and swaps the narrow no-break space Pretalx puts before French
    punctuation for the ordinary one, which the embedded font actually has.
    """
    return html.escape((value or '').replace('\u202f', '\u00a0'))


@functools.lru_cache(maxsize=None)
def qr_code(url: str) -> str:
    """Inline SVG QR code pointing at a talk page."""
    buffer = io.BytesIO()
    segno.make(url, error='m').save(buffer, kind='svg', xmldecl=False,
                                    svgns=True, scale=1, border=0,
                                    dark=QR_COLOUR)
    return buffer.getvalue().decode('utf-8')


def duration_minutes(event: Event) -> int:
    delta = event._end_datetime - event._start_datetime
    return int(delta.total_seconds() // 60)


def render_event(event: Event, show_qr: bool = True) -> str:
    """One slot of the timeline, its height driven by its duration.

    flex-grow is the duration in minutes, so the free space on the page is
    shared out in proportion to how long each event lasts, while the content
    still sets each slot's minimum height. A strict proportional grid would
    clip the title of a 25 minute talk.
    """
    classes = event_classes(event)
    title = clean(event.title)
    speakers = clean(event.persons)
    people = f'<p class="who">{speakers}</p>' if speakers else ''

    url = getattr(event, '_url', None)
    qr = f'<div class="qr">{qr_code(url)}</div>' if show_qr and url else ''

    return f'''
                <div class="slot {classes}"
                     style="flex-grow: {duration_minutes(event)}">
                    <div class="when">
                        <b>{event._start_datetime:%Hh%M}</b>
                        <i>{event._end_datetime:%Hh%M}</i>
                    </div>
                    <div class="what">
                        <h2>{title}</h2>
                        {people}
                    </div>
                    {qr}
                </div>
    '''


def render_room(conference: Conference, day: Day, room: Room,
                show_qr: bool = True, timeline_size: float = None) -> str:
    talks = room.sorted_events()
    if not talks:
        return ''

    # Built into a local list rather than written back into the room: the
    # breaks belong to this page, not to the parsed schedule.
    events = sorted(talks + build_breaks(room, day, talks),
                    key=lambda event: event._start_datetime)

    slots = ''
    previous_end = None
    for event in events:
        if previous_end is not None and event._start_datetime > previous_end:
            gap = int((event._start_datetime
                       - previous_end).total_seconds() // 60)
            slots += f'<div class="hole" style="flex-grow: {gap}"></div>'
        previous_end = event._end_datetime
        slots += render_event(event, show_qr=show_qr)

    # A room with one or two talks would otherwise stretch a couple of lines
    # of small text over a whole A3; the poster variant scales the type up.
    # Breaks do not count: they are what a near-empty room is padded with.
    poster = ' poster' if len(talks) <= POSTER_MODE_MAX_EVENTS else ''
    sizing = f' style="font-size: {timeline_size}px"' if timeline_size else ''

    return f'''
        <section class="page">
            <header>
                <div class="brand"></div>
                <div class="ident">
                    <h1>{clean(room._name)}</h1>
                    <p>{day._date:%A %d %B}</p>
                </div>
            </header>
            <div class="timeline{poster}"{sizing}>
                {slots}
            </div>
            <footer>
                <span>{clean(str(conference))}</span>
                <span>Salle {clean(room._name)} &middot; {day._date:%A}</span>
            </footer>
        </section>
    '''


def printable_rooms(conference: Conference):
    """Every (day, room) that earns a sheet, in printing order."""
    for day in conference._days.values():
        for room in day._rooms.values():
            if room._name not in EXCLUDED_ROOMS and room.sorted_events():
                yield day, room


def build_html(conference: Conference, show_qr: bool = True,
               sizes: dict = None) -> str:
    sizes = sizes or {}
    return ''.join(
        render_room(conference, day, room, show_qr=show_qr,
                    timeline_size=sizes.get((day._date, room._name)))
        for day, room in printable_rooms(conference))


def fits_one_sheet(markup: str, css: CSS, fonts) -> bool:
    return len(HTML(string=markup).render(stylesheets=[css],
                                          font_config=fonts).pages) == 1


def fit_rooms(conference: Conference, css: CSS, fonts,
              show_qr: bool = True) -> tuple[dict, list]:
    """Pick the largest type size at which each room still fits its sheet.

    A poster is one page by construction, so a room denser than the
    stylesheet's defaults would otherwise spill onto a second sheet, or worse
    have its footer clipped away unnoticed. Turn such a room's timeline down a
    step at a time instead, and report the ones that will not fit at all
    rather than printing something broken.
    """
    sizes = {}
    too_dense = []

    for day, room in printable_rooms(conference):
        size = BASE_TIMELINE_SIZE
        while not fits_one_sheet(
                render_room(conference, day, room, show_qr, size),
                css, fonts):
            size -= TIMELINE_SIZE_STEP
            if size < MIN_TIMELINE_SIZE:
                too_dense.append(f'{room} on {day}')
                break
        if size != BASE_TIMELINE_SIZE:
            sizes[(day._date, room._name)] = size

    return sizes, too_dense


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description='Generate the Capitole du Libre paper schedule as a PDF.')
    parser.add_argument(
        '--year', type=int, default=default_year(),
        help=f'conference edition to fetch '
             f'(default: ${YEAR_ENV_VAR}, else the current year)')
    parser.add_argument(
        '--url',
        help='schedule XML URL, overriding the one derived from --year')
    parser.add_argument(
        '--schedule-file',
        help='read the schedule from a local XML export instead of the '
             'network, ignoring --year and --url')
    parser.add_argument(
        '--output', default=DEFAULT_OUTPUT,
        help=f'PDF file to write (default: {DEFAULT_OUTPUT})')
    parser.add_argument(
        '--stylesheet', default=DEFAULT_STYLESHEET,
        help=f'CSS stylesheet to apply (default: {DEFAULT_STYLESHEET})')
    parser.add_argument(
        '--no-qr', dest='qr', action='store_false',
        help='leave out the QR code linking to each talk page')
    parser.add_argument(
        '--locale', default=DEFAULT_LOCALE,
        help=f'locale used to format dates (default: {DEFAULT_LOCALE})')

    args = parser.parse_args(argv)
    if args.url is None:
        args.url = SCHEDULE_URL_TEMPLATE.format(year=args.year)
    return args


def load_conference(args) -> Conference:
    """Parse the schedule named by the command line.

    Raises OSError if it cannot be reached and ElementTree.ParseError if what
    comes back is not the export we expect.
    """
    source = args.schedule_file if args.schedule_file else urlopen(args.url)
    conference = Conference(source)
    conference.parse()
    return conference


def main(argv=None) -> int:
    args = parse_args(argv)

    try:
        conference = load_conference(args)
    except OSError as error:
        target = args.schedule_file or args.url
        print(f'error: cannot read the schedule at {target}: {error}',
              file=sys.stderr)
        return 1
    except ElementTree.ParseError as error:
        print(f'error: the schedule is not valid XML: {error}',
              file=sys.stderr)
        return 1

    try:
        locale.setlocale(locale.LC_ALL, args.locale)
    except locale.Error:
        print(f'warning: locale {args.locale} is unavailable, '
              'dates will not be localised',
              file=sys.stderr)

    # Without an explicit font configuration threaded through both the
    # stylesheet and the write, WeasyPrint silently ignores @font-face and
    # falls back to whatever the machine happens to have installed.
    fonts = FontConfiguration()
    css = CSS(filename=args.stylesheet, font_config=fonts)

    sizes, too_dense = fit_rooms(conference, css, fonts, show_qr=args.qr)
    if too_dense:
        print('error: these rooms do not fit on one sheet even at the '
              f'smallest type size ({MIN_TIMELINE_SIZE}px):',
              file=sys.stderr)
        for room in too_dense:
            print(f'  {room}', file=sys.stderr)
        return 1

    document = HTML(string=build_html(conference, show_qr=args.qr,
                                      sizes=sizes))

    try:
        os.remove(args.output)
    except FileNotFoundError:
        pass

    document.write_pdf(args.output, stylesheets=[css],
                       font_config=fonts)
    return 0


if __name__ == "__main__":
    sys.exit(main())

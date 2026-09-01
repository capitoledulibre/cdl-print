
import argparse
import io
import locale
import os
import re
import sys
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict
from urllib.request import urlopen
from xml.etree import ElementTree

import segno
from weasyprint import CSS, HTML

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

# ISO weekday numbers, as returned by datetime.isoweekday().
SATURDAY = 6
SUNDAY = 7

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


class UniqueByConference(object):
    def __new__(cls, conference, attr, *args, **kwargs):
        if getattr(cls,
                   '_instances',
                   None) is None:
            cls._instances = {}
        instance_id = (conference, attr)
        if cls._instances.get(instance_id, None) is None:
            cls._instances[instance_id] = super().__new__(cls)
            if hasattr(cls._instances[instance_id], 'init'):
                cls._instances[instance_id].init()
        return cls._instances[instance_id]

    def __init__(self, conference, attr):
        self._conference = conference


class Conference(object):
    def __init__(self, url):
        self._url = url
        self._days: Dict[datetime, Day] = {}

    def __str__(self):
        return self._title

    @property
    def _rooms(self):
        rooms = {}
        for day in self._days.values():
            rooms.update(day._rooms.items())
        return rooms

    @property
    def _events(self):
        events = {}
        for day in self._days.values():
            events.update(day._events.items())
        return events

    @property
    def _persons(self):
        persons = {}
        for day in self._days.values():
            persons.update(day._persons.items())
        return persons

    def parse(self):
        remote = urlopen(self._url)
        tree = ElementTree.parse(remote)
        root_element = tree.getroot()
        for element in list(root_element):
            if element.tag == 'conference':
                for element_details in list(element):
                    if element_details.tag in ['title', 'venue', 'city', 'start_date', 'end_date', 'days_count']:
                        setattr(self,
                                f'_{element_details.tag}',
                                element_details.text)
            elif element.tag == 'day':
                date = datetime.strptime(element.get('date'), '%Y-%m-%d')
                self._days[date] = Day(self, date)
                self._days[date].parse(element)
            else:
                print('unknown element type')


class Day(UniqueByConference):
    def __init__(self, conference: Conference, date: datetime):
        super().__init__(conference, date)
        self._date = date

    def init(self):
        self._rooms: Dict[str, Room] = {}

    @property
    def _persons(self):
        persons = {}
        for room in self._rooms.values():
            for event in room._events.values():
                persons.update(event._persons.items())
        return persons

    def parse(self, day_element):
        for element in list(day_element):
            if element.tag == 'room':
                room_name = element.get('name')
                self._rooms[room_name] = Room(
                    self._conference,
                    room_name,
                    self)
                self._rooms[room_name].parse(element, self)


class Room(UniqueByConference):
    def __init__(self, conference: Conference, name: str, day: Day):
        super().__init__(conference, name)
        self._name = name
        self._days[day._date] = day

    def init(self):
        self._days: Dict[datetime, Day] = {}
        self._events: Dict[str, Event] = {}

    def __str__(self):
        return self._name

    def get_events_by_day(self, day):
        events = {}
        for event in self._events.values():
            if event._day is day:
                events[event._id] = event

        return events

    def get_sorted_list_by_day(self, day):
        events = list(self.get_events_by_day(day).values())
        events.sort(key=lambda e: e._start_datetime)
        return events

    def parse(self, room_element, day: Day):
        for element in list(room_element):
            if element.tag == 'event':
                event_id = element.get('id')
                self._events[event_id] = Event(
                    self._conference,
                    event_id,
                    day)
                self._events[event_id].parse(element)


class Event(UniqueByConference):
    def __init__(self, conference, event_id, day: Day):
        super().__init__(conference, event_id)
        self._id = event_id
        self._day: Day = day

    def init(self):
        self._persons: Dict[str, Person] = {}

    def _str__(self):
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
    def persons(self):
        names = [person._name for person in self._persons.values()]
        if len(names) >= 3:
            return '{} et {}'.format(', '.join(names[:-1]), names[-1])
        elif len(names) == 2:
            return '{} et {}'.format(*names)
        return names[0]

    def parse(self, event_element):
        for element in list(event_element):
            if element.tag == 'persons':
                for person_element in list(element):
                    person_id = person_element.get('id')
                    self._persons[person_id] = Person(
                        self._conference,
                        person_id,
                        self)
                    self._persons[person_id].parse(person_element)
            else:
                setattr(self,
                        f'_{element.tag}',
                        element.text)


class Person(UniqueByConference):
    def __init__(self, conference: Conference, person_id, event: Event):
        super().__init__(conference, person_id)
        self._id = person_id
        if getattr(self,
                   '_events',
                   None) is None:
            self._events = {}
        self._events[event._id] = event

    def __str__(self):
        return self._name

    def parse(self, person_element):
        self._name = person_element.text


def build_breaks(conference: Conference, room: Room, day: Day, events: list):
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
        event = Event(
            conference,
            f'break-{day._date:%Y%m%d}-{room._name}-{index}',
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
    people = f'<p class="who">{event.persons}</p>' if event._persons else ''

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
                        <h2>{event.title}</h2>
                        {people}
                    </div>
                    {qr}
                </div>
    '''


def render_room(conference: Conference, day: Day, room: Room,
                show_qr: bool = True) -> str:
    events = room.get_sorted_list_by_day(day)
    if not events:
        return ''

    for pause in build_breaks(conference, room, day, events):
        room._events[pause._id] = pause
    events = room.get_sorted_list_by_day(day)

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
    talks = [event for event in events if event._type != 'pause']
    poster = ' poster' if len(talks) <= POSTER_MODE_MAX_EVENTS else ''

    return f'''
        <section class="page">
            <header>
                <div class="brand"></div>
                <div class="ident">
                    <h1>{room}</h1>
                    <p>{day._date:%A %d %B}</p>
                </div>
            </header>
            <div class="timeline{poster}">
                {slots}
            </div>
            <footer>
                <span>{conference}</span>
                <span>Salle {room} &middot; {day._date:%A}</span>
            </footer>
        </section>
    '''


def render_day(conference: Conference, day: Day, show_qr: bool = True) -> str:
    return ''.join(render_room(conference, day, room, show_qr=show_qr)
                   for room in day._rooms.values()
                   if room._name not in EXCLUDED_ROOMS)


def build_html(conference: Conference, show_qr: bool = True) -> str:
    return ''.join(render_day(conference, day, show_qr=show_qr)
                   for day in conference._days.values())


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


def main(argv=None) -> int:
    args = parse_args(argv)

    conference = Conference(url=args.url)
    conference.parse()

    try:
        locale.setlocale(locale.LC_ALL, args.locale)
    except locale.Error:
        print(f'warning: locale {args.locale} is unavailable, '
              'dates will not be localised',
              file=sys.stderr)

    html = HTML(string=build_html(conference, show_qr=args.qr))
    css = CSS(filename=args.stylesheet)

    try:
        os.remove(args.output)
    except FileNotFoundError:
        pass

    html.write_pdf(args.output, stylesheets=[css])
    return 0


if __name__ == "__main__":
    sys.exit(main())

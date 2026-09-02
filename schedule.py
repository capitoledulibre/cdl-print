"""The conference schedule: parsing the Pretalx FRAB export into a model.

Nothing in here knows about pages or layout; the renderers build on it.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from xml.etree import ElementTree

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

    @property
    def year(self) -> int:
        """The edition's year, taken from the schedule rather than the flags.

        --schedule-file can name any export, so the file names have to follow
        what was actually parsed.
        """
        return min(self._days).year

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


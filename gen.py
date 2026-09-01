
import locale
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict
from urllib.request import urlopen
from xml.etree import ElementTree

from weasyprint import CSS, HTML

# --- Breaks ----------------------------------------------------------------

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


def render_event(event: Event) -> str:
    html = f'''
                        <tr class="event_row {event._type}">
                            <td class="event_date">
                                {event._start_datetime:%Hh%M}
                                à
                                {event._end_datetime:%Hh%M}
                            </td>
                            <td class="event_cell">
                                <div class="event_title">
                                    {event.title}
                                </div>
    '''
    if len(event._persons.values()) > 0:
        html += f'''
                                    <div class="event_persons">
                                        {event.persons}
                                    </div>
        '''
    html += '''
                            </td>
                        </tr>
    '''
    return html


def render_room(conference: Conference, day: Day, room: Room) -> str:
    events = room.get_sorted_list_by_day(day)
    if not events:
        return ''

    for pause in build_breaks(conference, room, day, events):
        room._events[pause._id] = pause
    events = room.get_sorted_list_by_day(day)

    html = f'''
            <div class="room">
                <header>
                    <div class="conf_title"><!-- Capitole du Libre 2025 --></div>
                    <div class="day_title">{day._date:%A %d %B}</div>
                    <div class="room_title">Salle {room}</div>
                </header>
                <table>
                    <thead>
                        <th>Heure</th>
                        <th>Conférence</th>
                    </thead>
                    <tbody>
    '''
    for i, event in enumerate(events):
        if i != 0 and events[i - 1]._end_datetime != event._start_datetime:
            html += '''
                        <tr>
                            <td colspan="2"><!-- Pause --></td>
                        </tr>
            '''
        html += render_event(event)
    html += '''
                    </tbody>
                </table>
            </div>
    '''
    return html


def render_day(conference: Conference, day: Day) -> str:
    html = ''
    for room in day._rooms.values():
        if room._name in EXCLUDED_ROOMS:
            continue
        html += render_room(conference, day, room)
    return f'<div class="day">{html}</div>'


def build_html(conference: Conference) -> str:
    return ''.join(render_day(conference, day)
                   for day in conference._days.values())


def main():
    conference = Conference(
        url='https://cfp.capitoledulibre.org/cdl-2025/schedule/export/schedule.xml')
    conference.parse()

    locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')

    html = HTML(string=build_html(conference))
    css = CSS(filename='style.css')
    file_name = 'conference.pdf'
    try:
        os.remove(file_name)
    except FileNotFoundError:
        pass

    html.write_pdf(file_name, stylesheets=[css])


if __name__ == "__main__":
    main()

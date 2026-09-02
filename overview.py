"""The hall poster: one A1 sheet per day, every room side by side.

Unlike a door poster, this one is read by several people at once looking for
where to go next, so the whole day has to be visible in one glance. Rooms are
columns, time runs down the page, and a talk is a block placed at its real
position: an actual grid, not a list.
"""

from datetime import timedelta

from render import clean, event_classes
from schedule import Conference, Day, EXCLUDED_ROOMS, build_breaks

STYLESHEET = 'styles/overview.css'
OUTPUT = 'conference-programme-global.pdf'

# The grid is laid out in rows of this many minutes.
SLOT_MINUTES = 5

# Geometry of the sheet, kept in step with styles/overview.css. It is needed
# here because a title too long for its block cannot be clipped in CSS:
# WeasyPrint crashes on a grid item carrying overflow:hidden, so titles are
# shortened to what their block can hold before they are written out.
SHEET_WIDTH_MM = 841
SHEET_PADDING_MM = 14
GUTTER_MM = 42
COLUMN_GAP_MM = 2
GRID_HEIGHT_MM = 492
SLOT_PADDING_MM = 5
TITLE_SIZE_PX = 18
WHEN_HEIGHT_MM = 5.5
PX_TO_MM = 25.4 / 96

# A speaker line costs more than it gives on a block this short.
MIN_MINUTES_FOR_SPEAKERS = 30


def day_rooms(day: Day) -> list:
    """The rooms to show for a day, in export order, keeping only used ones."""
    return [room for room in day._rooms.values()
            if room._name not in EXCLUDED_ROOMS and room.sorted_events()]


def day_span(day: Day, rooms: list) -> tuple:
    """The earliest start and latest end across every room of the day."""
    starts = [room.sorted_events()[0]._start_datetime for room in rooms]
    ends = [room.sorted_events()[-1]._end_datetime for room in rooms]
    return min(starts), max(ends)


def slot_of(moment, origin) -> int:
    return int((moment - origin).total_seconds() // 60 // SLOT_MINUTES)


def title_budget(room_count: int, span_minutes: int, minutes: int) -> int:
    """Roughly how many characters this block can hold.

    Derived from the sheet geometry rather than guessed, so that a day with
    sixteen rooms shortens harder than one with twelve.
    """
    columns_mm = (SHEET_WIDTH_MM - 2 * SHEET_PADDING_MM - GUTTER_MM
                  - COLUMN_GAP_MM * room_count)
    column_mm = columns_mm / room_count - SLOT_PADDING_MM
    character_mm = 0.5 * TITLE_SIZE_PX * PX_TO_MM
    per_line = max(8, int(column_mm / character_mm))

    block_mm = GRID_HEIGHT_MM * minutes / span_minutes
    line_mm = 1.12 * TITLE_SIZE_PX * PX_TO_MM
    lines = max(1, int((block_mm - SLOT_PADDING_MM - WHEN_HEIGHT_MM) / line_mm))

    return per_line * lines


def shorten(text: str, budget: int) -> str:
    """Cut a title to its budget on a word boundary."""
    if len(text) <= budget:
        return text
    cut = text[:budget].rsplit(' ', 1)[0]
    return f'{cut}\u2026'


def render_hour_marks(start, end, origin) -> str:
    """An hour label down the left gutter, on the hour, every hour."""
    marks = ''
    hour = start.replace(minute=0, second=0) + timedelta(hours=1)
    while hour < end:
        row = slot_of(hour, origin) + 1
        marks += (f'<div class="hour" style="grid-row: {row} / span '
                  f'{60 // SLOT_MINUTES}">{hour:%Hh}</div>')
        hour += timedelta(hours=1)
    return marks


def render_event(event, column: int, origin, budget: int,
                 minutes: int) -> str:
    top = slot_of(event._start_datetime, origin) + 1
    bottom = slot_of(event._end_datetime, origin) + 1
    people = ''
    if event._persons and minutes >= MIN_MINUTES_FOR_SPEAKERS:
        people = f'<p class="who">{clean(shorten(event.persons, budget))}</p>' 
    return f'''
        <div class="slot {event_classes(event)}"
             style="grid-column: {column}; grid-row: {top} / {bottom}">
            <p class="when">{event._start_datetime:%Hh%M}</p>
            <h2>{clean(shorten(event.title, budget))}</h2>
            {people}
        </div>'''


def render_day(conference: Conference, day: Day) -> str:
    rooms = day_rooms(day)
    if not rooms:
        return ''

    origin, end = day_span(day, rooms)
    rows = slot_of(end, origin)

    headers = ''.join(
        f'<div class="room-name" style="grid-column: {index + 2}">'
        f'{clean(room._name)}</div>'
        for index, room in enumerate(rooms))

    span = int((end - origin).total_seconds() // 60)
    slots = render_hour_marks(origin, end, origin)
    for index, room in enumerate(rooms):
        talks = room.sorted_events()
        for event in talks + build_breaks(room, day, talks):
            minutes = int((event._end_datetime
                           - event._start_datetime).total_seconds() // 60)
            slots += render_event(event, index + 2, origin,
                                  title_budget(len(rooms), span, minutes),
                                  minutes)

    return f'''
    <section class="page">
        <header>
            <div class="brand"></div>
            <div class="ident">
                <h1>{day._date:%A %d %B}</h1>
                <p>{clean(str(conference))}</p>
            </div>
        </header>
        <div class="headers"
             style="grid-template-columns: var(--gutter) repeat({len(rooms)}, 1fr)">
            <div></div>{headers}
        </div>
        <div class="grid"
             style="grid-template-columns: var(--gutter) repeat({len(rooms)}, 1fr);
                    grid-template-rows: repeat({rows}, 1fr)">
            {slots}
        </div>
    </section>'''


def build_html(conference: Conference) -> str:
    return ''.join(render_day(conference, day)
                   for day in conference._days.values())

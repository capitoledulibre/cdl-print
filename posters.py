"""The door posters: one A3 sheet per room and per day."""

from weasyprint import CSS

from audience import code_of
from render import clean, duration_minutes, event_classes, fit_size, qr_code
from schedule import (Conference, Day, EXCLUDED_ROOMS, Event, Room,
                      build_breaks)

STYLESHEET = 'styles/posters.css'
OUTPUT = 'conference-programme-salles-{year}.pdf'

# A room with at most this many talks is laid out as a poster rather than a
# timeline, so a nearly empty day does not become a nearly empty page.
POSTER_MODE_MAX_EVENTS = 2

# A door poster is read from a few metres away, so the audience line only
# earns its place when it is a handful of words.
AUDIENCE_MAX_LENGTH = 45

# Type size of a timeline, in px, matching .timeline in the stylesheet.
BASE_TIMELINE_SIZE = 16
MIN_TIMELINE_SIZE = 9
TIMELINE_SIZE_STEP = 0.5

# A talk's page on the conference site, keyed on the same Pretalx code as the
# CfP page. Attendees scanning a door know the site, not the CfP tool.
SITE_TALK_TEMPLATE = 'https://capitoledulibre.org/programme/talk/{code}/'


def site_url(event: Event) -> str | None:
    """The event's page on capitoledulibre.org, falling back to its CfP URL.

    The fallback covers an export whose URLs carry no talk code, so a door
    still gets a working QR code rather than none.
    """
    code = code_of(event)
    if code:
        return SITE_TALK_TEMPLATE.format(code=code)
    return getattr(event, '_url', None) or None


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

    audience = getattr(event, '_audience', None)
    for_whom = ''
    if audience and len(audience) <= AUDIENCE_MAX_LENGTH:
        for_whom = f'<p class="audience">{clean(audience)}</p>'

    url = site_url(event)
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
                        {for_whom}
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
        size = fit_size(
            lambda at: render_room(conference, day, room, show_qr, at),
            css, fonts,
            BASE_TIMELINE_SIZE, MIN_TIMELINE_SIZE, TIMELINE_SIZE_STEP)
        if size is None:
            too_dense.append(f'{room} on {day}')
        elif size != BASE_TIMELINE_SIZE:
            sizes[(day._date, room._name)] = size

    return sizes, too_dense

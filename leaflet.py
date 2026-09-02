"""The tri-fold leaflet: one A4 landscape sheet, folded in three.

For whoever will not carry a fifty page booklet. Both days fit on the inside
as a compact list, because at 99mm a panel has no room for a grid.

Panel order follows the usual letter fold. Page one is the outside, left to
right: the flap that folds inward, the back, then the front cover. Page two
is the inside as it reads when the sheet is opened flat. Confirm the fold
against a paper dummy before a print run.
"""

import content
from render import clean
from schedule import Conference, Day, EXCLUDED_ROOMS

STYLESHEET = 'styles/leaflet.css'
OUTPUT = 'conference-depliant-{year}.pdf'

# A column of the inside spread holds about this much of a title.
TITLE_BUDGET = 40

# The leaflet is one folded sheet: two pages, no more.
EXPECTED_PAGES = 2


def shorten(text: str, budget: int) -> str:
    if len(text) <= budget:
        return text
    return f'{text[:budget].rsplit(" ", 1)[0]}…'


def day_talks(day: Day) -> list:
    events = [event for room in day._rooms.values()
              if room._name not in EXCLUDED_ROOMS
              for event in room.sorted_events()]
    return sorted(events, key=lambda e: (e._start_datetime,
                                         getattr(e, '_room', '')))


def render_day_flow(day: Day) -> str:
    """The day's talks as a continuous column, grouped under each hour.

    The programme runs across all three inside panels as one flow rather
    than one day per panel. A day per panel meant a panel had to hold a
    whole day -- sixty-six talks in 184mm in 2026, which did not fit and
    turned the sheet into an unfoldable third page. Three columns hold both
    days with room to spare, and the hour headings come back.
    """
    lines = f'<h2>{day._date:%A %d %B}</h2>'
    previous = None
    for event in day_talks(day):
        start = event._start_datetime
        if start != previous:
            previous = start
            lines += f'<p class="hour">{start:%Hh%M}</p>'
        lines += (f'<p class="line">'
                  f'<i>{clean(getattr(event, "_room", ""))}</i>'
                  f'{clean(shorten(event.title, TITLE_BUDGET))}</p>')
    return lines


def render_cover(conference: Conference) -> str:
    days = list(conference._days.values())
    dates = f'{days[0]._date:%d} et {days[-1]._date:%d %B %Y}'
    return f'''
        <div class="panel cover">
            <div class="brand"></div>
            <p class="kicker">Programme</p>
            <p class="dates">{dates}</p>
            <p class="venue">ENSEEIHT &middot; Toulouse</p>
            <p class="site">capitoledulibre.org</p>
        </div>'''


def render_practical() -> str:
    """Practical information, with the newcomer essentials above it."""
    newcomer = ''.join(
        f'<p class="item"><b>{clean(heading)}</b> {clean(body)}</p>'
        for heading, body in content.FIRST_TIME[:3])
    rows = ''.join(f'<p class="item"><b>{clean(name)}</b> {clean(about)}</p>'
                   for name, about in content.PRACTICAL)
    return f'''
        <div class="panel">
            <h2>{clean(content.FIRST_TIME_TITLE)}</h2>
            {newcomer}
            <h2 class="second">{clean(content.PRACTICAL_TITLE)}</h2>
            {rows}
        </div>'''


def render_highlights(conference: Conference) -> str:
    import booklet
    entries = ''
    for event, why in booklet.find_highlights(conference):
        entries += (f'<p class="pick">'
                    f'<b>{event._start_datetime:%a} '
                    f'{event._start_datetime:%Hh%M}</b> '
                    f'<span class="room">'
                    f'{clean(getattr(event, "_room", ""))}</span><br>'
                    f'{clean(event.title)}</p>')
    stands = ', '.join(clean(name) for name, _ in content.STANDS[:8])
    return f'''
        <div class="panel">
            <h2>{clean(content.HIGHLIGHTS_TITLE)}</h2>
            {entries}
            <h2 class="second">{clean(content.STANDS_TITLE)}</h2>
            <p class="item">{stands} et d’autres, dans le Hall C.</p>
        </div>'''


def build_html(conference: Conference) -> str:
    days = list(conference._days.values())
    outside = (render_highlights(conference) + render_practical()
               + render_cover(conference))
    inside = ''.join(render_day_flow(day) for day in days)
    return (f'<section class="sheet">{outside}</section>'
            f'<section class="sheet"><div class="flow">{inside}</div>'
            f'</section>')

"""The tri-fold leaflet: one A4 landscape sheet, folded in three.

For whoever will not carry a fifty page booklet. Both days fit on the inside
as a compact list, because at 99mm a panel has no room for a grid.

Panel order follows the usual letter fold. Page one is the outside, left to
right: the flap that folds inward, the back, then the front cover. Page two
is the inside as it reads when the sheet is opened flat. Confirm the fold
against a paper dummy before a print run.
"""

import content
from render import (campus_plan, clean, event_classes, partner_logo, qr_code,
                    rooms_by_floor)
from schedule import Conference, Day, EXCLUDED_ROOMS

STYLESHEET = 'styles/leaflet.css'
OUTPUT = 'conference-depliant-{year}.pdf'

# Where the cover's QR code leads: the live programme, with any change made
# after the print run.
PROGRAMME_URL = 'https://capitoledulibre.org/programme/'

# Marks a workshop in the programme, where there is no room to spell out
# 'Atelier'. A wrench, drawn in the text colour so it survives greyscale.
WORKSHOP_ICON = (
    '<svg class="icon" viewBox="0 0 24 24" aria-label="Atelier">'
    '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77'
    'a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91'
    'a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>')

# Type size of the programme lines, in points. The inside spread is set as
# large as it will go, down to the smallest size still worth printing.
BASE_FLOW_SIZE = 7.0
MIN_FLOW_SIZE = 5.6
FLOW_SIZE_STEP = 0.2

# The leaflet is one folded sheet: two pages, no more.
EXPECTED_PAGES = 2


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
        workshop = event_classes(event).startswith('workshop')
        lines += (f'<p class="line">'
                  f'<i>{clean(getattr(event, "_room", ""))}</i>'
                  f'{WORKSHOP_ICON if workshop else ""}'
                  f'{clean(event.title)}</p>')
    return lines


def render_rooms(conference: Conference) -> str:
    """The rooms of the programme, building by building and floor by floor."""
    names = [name for name in conference._rooms if name not in EXCLUDED_ROOMS]
    lines = ''
    for building, floors in rooms_by_floor(names):
        detail = ' &middot; '.join(
            f'{floor} {", ".join(clean(room) for room in rooms)}'
            for floor, rooms in floors)
        lines += f'<p class="building"><b>{clean(building)}</b>{detail}</p>'
    return lines


def render_back(conference: Conference) -> str:
    """The back of the folded leaflet: the plan, then practical information.

    In a letter fold this is the panel seen when the leaflet is turned over,
    so it carries what a visitor looks up standing in the hall.
    """
    legend = ''.join(f'<li><b>{number}</b>{clean(label)}</li>'
                     for number, label in enumerate(content.PLAN_LEGEND, 1))
    # The opening hours have a section of their own on the flap.
    rows = ''.join(f'<p class="item"><b>{clean(name)}</b> {clean(about)}</p>'
                   for name, about in content.PRACTICAL
                   if name != 'Horaires')
    return f'''
        <div class="panel">
            <h2>{clean(content.PLAN_TITLE)}</h2>
            <div class="plan">{campus_plan()}</div>
            <ol class="legend">{legend}</ol>
            {render_rooms(conference)}
            <h2 class="second">{clean(content.PRACTICAL_TITLE)}</h2>
            {rows}
        </div>'''


def render_cover(conference: Conference) -> str:
    days = list(conference._days.values())
    dates = f'{days[0]._date:%d} et {days[-1]._date:%d %B %Y}'
    return f'''
        <div class="panel cover">
            <div class="brand"></div>
            <p class="kicker">Programme</p>
            <p class="dates">{dates}</p>
            <p class="venue">ENSEEIHT &middot; Toulouse</p>
            <div class="online">
                <div class="qr">{qr_code(PROGRAMME_URL)}</div>
                <p>Le programme à jour<br>
                <span class="site">capitoledulibre.org</span></p>
            </div>
            {render_partners()}
        </div>'''


def render_partners() -> str:
    """The sponsors tier by tier, then the institutions, as logos.

    Each group is a class of its own, so the stylesheet can print a higher
    tier larger.
    """
    groups = ''
    for name, partners in content.PARTNER_GROUPS:
        if name not in content.LEAFLET_PARTNER_GROUPS:
            continue
        logos = ''.join(f'<li>{partner_logo(partner, content.PARTNER_LOGOS)}'
                        f'</li>' for partner in partners)
        tier = name.lower()
        groups += (f'<p class="tier">{clean(name)}</p>'
                   f'<ul class="logos {tier}">{logos}</ul>')
    return f'''
            <div class="partners">
                <h3>{clean(content.PARTNERS_TITLE)}</h3>
                {groups}
            </div>'''


def render_flap(conference: Conference) -> str:
    """The flap folded inside: newcomer essentials, hours and highlights."""
    # How to support the event in place of the registration tip, which is
    # moot by the time someone holds the leaflet; then the next two tips, and
    # the last one: knowing that the volunteers in red are there to be asked
    # is worth more than a fourth tip.
    tips = ([content.LEAFLET_SUPPORT] + content.FIRST_TIME[1:3]
            + content.FIRST_TIME[-1:])
    newcomer = ''.join(
        f'<p class="item"><b>{clean(heading)}</b> {clean(body)}</p>'
        for heading, body in tips)
    hours = ''.join(f'<p class="item"><b>{clean(day)}</b> {clean(about)}</p>'
                    for day, about in content.ACCESS_HOURS)
    return f'''
        <div class="panel">
            <h2>{clean(content.FIRST_TIME_TITLE)}</h2>
            {newcomer}
            <h2 class="second">{clean(content.ACCESS_HOURS_TITLE)}</h2>
            {hours}
            {render_highlights(conference)}
        </div>'''


def render_highlights(conference: Conference) -> str:
    import booklet
    entries = ''
    for event, why in booklet.find_highlights(conference):
        if any(fragment in event.title
               for fragment in content.LEAFLET_HIGHLIGHTS_LEFT_OUT):
            continue
        entries += (f'<p class="pick">'
                    f'<b>{event._start_datetime:%a} '
                    f'{event._start_datetime:%Hh%M}</b> '
                    f'<span class="room">'
                    f'{clean(getattr(event, "_room", ""))}</span> '
                    f'{clean(event.title)}</p>')
    return f'''
        <h2 class="second">{clean(content.HIGHLIGHTS_TITLE)}</h2>
        {entries}'''


def render_outside(conference: Conference) -> str:
    return (render_flap(conference) + render_back(conference)
            + render_cover(conference))


def outside_fits(conference: Conference, css, fonts) -> bool:
    """Whether the three outside panels hold on their one page.

    Checked on its own so that a panel grown too long is not reported as a
    programme too long for its columns: either makes a third page.
    """
    from weasyprint import HTML

    markup = f'<section class="sheet">{render_outside(conference)}</section>'
    return len(HTML(string=markup).render(stylesheets=[css],
                                          font_config=fonts).pages) == 1


def build_html(conference: Conference, size: float = BASE_FLOW_SIZE) -> str:
    days = list(conference._days.values())
    outside = render_outside(conference)
    key = f'<p class="key">{WORKSHOP_ICON} atelier</p>'
    inside = key + ''.join(render_day_flow(day) for day in days)
    return (f'<section class="sheet">{outside}</section>'
            f'<section class="sheet inside">'
            f'<div class="flow" style="font-size: {size}pt">{inside}</div>'
            f'</section>')


def fit_flow(conference: Conference, css, fonts) -> float | None:
    """Largest programme size at which the sheet is still two pages.

    The inside spread has no fixed height, so a programme too long for its
    three columns runs onto a third page instead of into a fourth column
    off the edge of the sheet, where it would be lost without a word.
    Returns None when even the smallest size does not fit.
    """
    from weasyprint import HTML

    size = BASE_FLOW_SIZE
    while size >= MIN_FLOW_SIZE - 1e-6:
        document = HTML(string=build_html(conference, size)).render(
            stylesheets=[css], font_config=fonts)
        if len(document.pages) == EXPECTED_PAGES:
            return size
        size = round(size - FLOW_SIZE_STEP, 2)
    return None

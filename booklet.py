"""The pocket booklet: A5, the grid, a card per talk, and the annexes.

The cover and the annexes wear the 2026 identity -- dark ground, orange
accents; the programme pages stay on white so that they stay readable and
cheap to print in quantity.
"""

import functools
import locale
import sys
import unicodedata

import content
from render import clean, event_classes, qr_code
from schedule import Conference, Day, EXCLUDED_ROOMS

STYLESHEET = 'styles/booklet.css'
OUTPUT = 'conference-livret-{year}.pdf'

# How much of an abstract a card can hold before it crowds its neighbours.
# Two or three sentences: the card is a decision aid, the QR code carries
# the full abstract.
ABSTRACT_BUDGET = 230

# The index is a reminder, not a description: one line per talk.
INDEX_TITLE_BUDGET = 46

# Speakers answer "who is this for?" in anything from two words to a
# paragraph; a card gives it a line, not a column.
AUDIENCE_BUDGET = 90

# A saddle-stitched booklet is printed on folded sheets, so its page count has
# to be a multiple of four. One page of notes earns its place; past two they
# are padding, and a blank leaf at the back is what padding should look like.
SHEET_MULTIPLE = 4
NOTE_PAGES = 1
MAX_NOTE_PAGES = 2


def shorten(text: str, budget: int) -> str:
    if len(text) <= budget:
        return text
    return f'{text[:budget].rsplit(" ", 1)[0]}…'


def day_rooms(day: Day) -> list:
    return [room for room in day._rooms.values()
            if room._name not in EXCLUDED_ROOMS and room.sorted_events()]


def talks_of(day: Day) -> list:
    """Every talk of a day, in chronological order, breaks left out."""
    events = [event for room in day_rooms(day)
              for event in room.sorted_events()]
    return sorted(events, key=lambda e: (e._start_datetime, getattr(e, '_room', '')))


# --- cover and plain pages --------------------------------------------------

def render_cover(conference: Conference) -> str:
    """The edition poster, full bleed and untouched.

    It already carries the name, the dates and the venue, and anything laid
    over it lands on its own type. The booklet says "Programme" on the title
    page instead.
    """
    return '''
    <section class="page cover">
        <div class="cover-art"></div>
    </section>'''


def render_title(conference: Conference) -> str:
    days = list(conference._days.values())
    dates = f'{days[0]._date:%d} et {days[-1]._date:%d %B %Y}'
    return f'''
    <section class="page dark title">
        <p class="kicker">Programme</p>
        <h1>{clean(str(conference))}</h1>
        <p class="dates">{dates}</p>
        <p class="venue">ENSEEIHT &middot; Toulouse</p>
        <p class="site">capitoledulibre.org</p>
    </section>'''


def render_editorial() -> str:
    body = ''.join(f'<p>{clean(paragraph)}</p>'
                   for paragraph in content.EDITORIAL)
    return f'''
    <section class="page dark">
        <h1>{clean(content.EDITORIAL_TITLE)}</h1>
        {body}
        <p class="signature">{clean(content.EDITORIAL_SIGNATURE)}</p>
    </section>'''


def render_contents(chapters: list) -> str:
    rows = ''.join(f'<li><span>{clean(title)}</span></li>'
                   for title in chapters)
    return f'''
    <section class="page dark">
        <h1>Sommaire</h1>
        <ul class="contents">{rows}</ul>
    </section>'''


def render_map_page(section: dict) -> str:
    body = ''.join(f'<p>{clean(paragraph)}</p>' for paragraph in section['body'])
    floors = ''
    if section.get('floors'):
        floors = '<dl class="floors">' + ''.join(
            f'<dt>{clean(name)}</dt><dd>{clean(detail)}</dd>'
            for name, detail in section['floors']) + '</dl>'
    return f'''
    <section class="page">
        <h1>{clean(section['title'])}</h1>
        {body}
        {floors}
        <figure class="placeholder">
            <p>{clean(section['map_caption'])}</p>
        </figure>
    </section>'''


def render_stands() -> str:
    rows = ''.join(
        f'<dt>{clean(name)}</dt><dd>{clean(about)}</dd>'
        for name, about in content.STANDS)
    return f'''
    <section class="page">
        <h1>{clean(content.STANDS_TITLE)}</h1>
        <p class="intro">{clean(content.STANDS_INTRO)}</p>
        <dl class="stands">{rows}</dl>
    </section>'''


def render_practical() -> str:
    rows = ''.join(f'<dt>{clean(name)}</dt><dd>{clean(about)}</dd>'
                   for name, about in content.PRACTICAL)
    return f'''
    <section class="page">
        <h1>{clean(content.PRACTICAL_TITLE)}</h1>
        <dl class="stands">{rows}</dl>
    </section>'''


def render_emergency() -> str:
    rows = ''.join(f'<li>{clean(line)}</li>' for line in content.EMERGENCY)
    return f'''
    <section class="page dark">
        <h1>{clean(content.EMERGENCY_TITLE)}</h1>
        <ul class="plain">{rows}</ul>
    </section>'''


def render_partners() -> str:
    groups = ''
    for name, partners in content.PARTNER_GROUPS:
        logos = ''.join(f'<li>{clean(partner)}</li>' for partner in partners)
        groups += f'<h2>{clean(name)}</h2><ul class="logos">{logos}</ul>'
    return f'''
    <section class="page">
        <h1>{clean(content.PARTNERS_TITLE)}</h1>
        <p class="intro">{clean(content.PARTNERS_INTRO)}</p>
        {groups}
    </section>'''


def render_join() -> str:
    body = ''.join(f'<p>{clean(paragraph)}</p>' for paragraph in content.JOIN)
    return f'''
    <section class="page dark">
        <h1>{clean(content.JOIN_TITLE)}</h1>
        {body}
        <p class="callout">toulibre.org</p>
    </section>'''


def render_notes(count: int) -> str:
    return ''.join('''
    <section class="page notes">
        <h1>Notes</h1>
        <div class="lines"></div>
    </section>''' for _ in range(count))


def render_blanks(count: int) -> str:
    """Padding to the next folded sheet, once the notes have had their share."""
    return '<section class="page blank"></section>' * count


def render_back(conference: Conference) -> str:
    return f'''
    <section class="page back">
        <div class="brand"></div>
        <p class="site">capitoledulibre.org</p>
        <p class="org">Organisé par Toulibre</p>
        <p class="edition">{clean(str(conference))}</p>
    </section>'''


# --- the programme, one band per time slot ----------------------------------

def slots_of(day: Day) -> list:
    """The day's talks grouped by start time, in order.

    Someone holding the booklet is asking "it is eleven, what is on?", so the
    hour is the way in, not the room and not a flat chronological list.
    """
    grouped = {}
    for room in day_rooms(day):
        for event in room.sorted_events():
            grouped.setdefault(event._start_datetime, []).append(event)
    return [(start, sorted(events, key=lambda e: getattr(e, '_room', '')))
            for start, events in sorted(grouped.items())]


def render_card(event, show_qr: bool) -> str:
    abstract = getattr(event, '_description', None) or ''
    people = (f'<p class="who">{clean(event.persons)}</p>'
              if event._persons else '')
    url = getattr(event, '_url', None)
    qr = f'<div class="qr">{qr_code(url)}</div>' if show_qr and url else ''
    minutes = int((event._end_datetime
                   - event._start_datetime).total_seconds() // 60)
    # Spelled out, because the hatch and the rule are cues and this is a fact.
    kind = ('<span class="kind">Atelier</span>'
            if 'workshop' in event_classes(event) else '')
    audience = getattr(event, '_audience', None)
    for_whom = (f'<p class="audience"><b>Pour qui</b> '
                f'{clean(shorten(audience, AUDIENCE_BUDGET))}</p>'
                if audience else '')
    return f'''
        <article class="card {event_classes(event)}">
            {qr}
            <p class="head">
                <span class="room">{clean(getattr(event, '_room', ''))}</span>
                <span class="length">{minutes} min</span>{kind}
            </p>
            <h3>{clean(event.title)}</h3>
            {people}
            <p class="abstract">{clean(shorten(abstract,
                                               ABSTRACT_BUDGET))}</p>
            {for_whom}
        </article>'''


def render_slot(start, events, show_qr: bool) -> str:
    end = max(event._end_datetime for event in events)
    cards = ''.join(render_card(event, show_qr) for event in events)
    return f'''
        <div class="slot-band">
            <span class="from">{start:%Hh%M}</span>
            <span class="to">jusqu&rsquo;à {end:%Hh%M}</span>
            <span class="count">{len(events)} au programme</span>
        </div>
        <div class="slot-cards">{cards}</div>'''


def render_day_programme(day: Day, show_qr: bool) -> str:
    slots = slots_of(day)
    body = ''.join(render_slot(start, events, show_qr)
                   for start, events in slots)
    return f'''
    <section class="page dark day-opener">
        <p class="kicker">Le programme</p>
        <h1>{day._date:%A %d %B}</h1>
        <p class="lede">{sum(len(e) for _, e in slots)} conférences et
            ateliers, de {slots[0][0]:%Hh%M} à
            {max(e._end_datetime for _, ev in slots for e in ev):%Hh%M}.</p>
        <ul class="hours">{''.join(
            f'<li><b>{start:%Hh%M}</b> &middot; {len(events)}</li>'
            for start, events in slots)}</ul>
    </section>
    <section class="page programme">
        {body}
    </section>'''


# --- what to put in front of a newcomer -------------------------------------

def render_first_time() -> str:
    points = ''.join(
        f'<div class="tip"><h3>{clean(heading)}</h3><p>{clean(body)}</p></div>'
        for heading, body in content.FIRST_TIME)
    day = ''.join(
        f'<li><b>{clean(hour)}</b> {clean(what)}</li>'
        for hour, what in content.FIRST_TIME_DAY)
    return f'''
    <section class="page first-time">
        <h1>{clean(content.FIRST_TIME_TITLE)}</h1>
        <p class="intro">{clean(content.FIRST_TIME_LEDE)}</p>
        {points}
        <h2>Une journée, en gros</h2>
        <ul class="daily">{day}</ul>
    </section>'''


@functools.lru_cache(maxsize=None)
def find_highlights(conference: Conference) -> list:
    """Match each curated fragment to a real talk.

    A fragment that matches nothing is reported rather than skipped: a talk
    renamed in Pretalx must not drop off the page in silence. Cached, because
    several outputs ask and the warning should be said once.
    """
    events = [event for day in conference._days.values()
              for room in day_rooms(day)
              for event in room.sorted_events()]

    found = []
    for fragment, why in content.HIGHLIGHTS:
        matches = [event for event in events if fragment in event.title]
        if not matches:
            print(f'warning: no talk matches the highlight {fragment!r}',
                  file=sys.stderr)
            continue
        found.append((min(matches, key=lambda e: e._start_datetime), why))
    return sorted(found, key=lambda pair: pair[0]._start_datetime)


def render_highlights(conference: Conference) -> str:
    entries = ''
    for event, why in find_highlights(conference):
        entries += f'''
        <div class="highlight">
            <p class="when">{event._start_datetime:%A} &middot;
                {event._start_datetime:%Hh%M}
                <span class="room">{clean(getattr(event, '_room', ''))}</span>
            </p>
            <h3>{clean(event.title)}</h3>
            <p class="why">{clean(why)}</p>
        </div>'''
    return f'''
    <section class="page dark highlights">
        <h1>{clean(content.HIGHLIGHTS_TITLE)}</h1>
        <p class="lede">{clean(content.HIGHLIGHTS_LEDE)}</p>
        {entries}
    </section>'''


# --- the speaker index ------------------------------------------------------

def initial_of(name: str) -> str:
    """The letter a name files under, accents folded onto their base letter."""
    folded = unicodedata.normalize('NFKD', name.strip())
    folded = folded.encode('ascii', 'ignore').decode('ascii').upper()
    return folded[0] if folded and folded[0].isalpha() else '#'


def speakers_of(conference: Conference) -> list:
    """Every speaker with their talks, filed alphabetically.

    Sorted through the locale so that É files with E rather than after Z.
    """
    people = {}
    for day in conference._days.values():
        for room in day_rooms(day):
            for event in room.sorted_events():
                for person in event._persons.values():
                    people.setdefault(person._name, []).append(event)

    try:
        key = locale.strxfrm
    except AttributeError:                       # pragma: no cover
        key = str
    return [(name, sorted(people[name], key=lambda e: e._start_datetime))
            for name in sorted(people, key=lambda n: key(n.upper()))]


def render_speaker_index(conference: Conference) -> str:
    letter = None
    entries = ''
    for name, events in speakers_of(conference):
        first = initial_of(name)
        if first != letter:
            letter = first
            entries += f'<p class="letter">{letter}</p>'
        talks = ''.join(
            f'<span class="talk">{event._start_datetime:%a} '
            f'{event._start_datetime:%Hh%M} &middot; '
            f"{clean(getattr(event, '_room', ''))}</span>"
            for event in events)
        entries += (f'<div class="speaker"><b>{clean(name)}</b>'
                    f'{talks}</div>')
    return f'''
    <section class="page speakers">
        <h1>Les intervenants</h1>
        <p class="intro">Par ordre alphabétique, avec l’heure et la salle de
            chaque intervention.</p>
        <div class="speaker-index">{entries}</div>
    </section>'''


# --- the index, one line per room -------------------------------------------

def render_room_index(conference: Conference) -> str:
    """What is on in each room, for whoever is already sitting in one."""
    blocks = ''
    for day in conference._days.values():
        rooms = ''
        for room in day_rooms(day):
            lines = ''.join(
                f'<li><b>{event._start_datetime:%Hh%M}</b> '
                f'{clean(shorten(event.title, INDEX_TITLE_BUDGET))}</li>'
                for event in room.sorted_events())
            rooms += (f'<div class="room-block"><h3>{clean(room._name)}</h3>'
                      f'<ul>{lines}</ul></div>')
        blocks += (f'<h2>{day._date:%A %d %B}</h2>'
                   f'<div class="room-index">{rooms}</div>')
    return f'''
    <section class="page index">
        <h1>Salle par salle</h1>
        <p class="intro">Pour savoir ce qui suit là où vous êtes assis.</p>
        {blocks}
    </section>'''


# --- assembly ---------------------------------------------------------------

def build_html(conference: Conference, show_qr: bool = True,
               filler: int = 0) -> str:
    days = list(conference._days.values())
    chapters = ['Premier Capitole du Libre ?', 'Le site', 'Trouver sa salle',
                'Le village associatif', 'À ne pas manquer']
    chapters += [f'Le programme — {day._date:%A}' for day in days]
    chapters += ['Salle par salle', 'Les intervenants', 'Infos pratiques',
                 'En cas de pépin', 'Nos partenaires', 'Rejoindre Toulibre']

    pages = [
        render_cover(conference),
        render_title(conference),
        render_editorial(),
        render_contents(chapters),
        render_first_time(),
        render_map_page(content.VENUE),
        render_map_page(content.BUILDINGS),
        render_stands(),
        render_highlights(conference),
    ]
    pages += [render_day_programme(day, show_qr) for day in days]
    pages += [
        render_room_index(conference),
        render_speaker_index(conference),
        render_practical(),
        render_emergency(),
        render_partners(),
        render_join(),
        render_notes(min(MAX_NOTE_PAGES, NOTE_PAGES + filler)),
        render_blanks(max(0, NOTE_PAGES + filler - MAX_NOTE_PAGES)),
        render_back(conference),
    ]
    return ''.join(pages)


def fill_to_a_folded_multiple(pages: int) -> int:
    """How many note pages to add so the booklet can be folded and stapled."""
    return (-pages) % SHEET_MULTIPLE

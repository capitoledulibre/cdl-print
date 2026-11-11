"""The video covers: one 1920x1080 image per filmed talk.

Not printed matter, but the same idea: the cover shown on YouTube and
PeerTube before each recording plays. The talk leads -- its title as large
as it will go, then who gives it -- and the partners are thanked along a
quiet band at the foot, tier by tier, rather than shouted over the title.

Only what is filmed gets a cover: workshops are not, nor is a talk whose
speaker refused. The pages are laid out as one PDF by WeasyPrint, then each
is rasterised to PNG by pdfium.
"""

import math
import os
import pathlib
import re
import unicodedata

import content
from render import clean, event_classes, partner_logo
from schedule import Conference, EXCLUDED_ROOMS, Event

STYLESHEET = 'styles/covers.css'
OUTPUT_DIR = 'couvertures-{year}'

# The size of the image, in CSS px: one CSS px is one image pixel.
WIDTH = 1920
HEIGHT = 1080

# The title is set as large as its box allows, within these bounds, in px.
BASE_TITLE_SIZE = 108
MIN_TITLE_SIZE = 56
TITLE_SIZE_STEP = 4

# Room the title has, in px, kept in step with styles/covers.css: narrower
# when the speakers' photos stand to its right.
TITLE_WIDTH = 1480
TITLE_WIDTH_WITH_PHOTOS = 1300
TITLE_MAX_HEIGHT = 390

# At most this many photos, side by side in a column to the right.
MAX_PHOTOS = 3

# Rough shape of a Fira Sans Bold line, to make a first guess at the size
# before the layout confirms it.
CHARACTER_EM = 0.52
LINE_EM = 1.08

# The sponsors on the band, as two columns of two tiers each: the higher
# tier above, on cells half as many and half as wide again, so that both
# rows of a column end on the same line.
SPONSOR_COLUMNS = (('Platine', 'Argent'), ('Or', 'Bronze'))
INSTITUTIONS = 'Institutions'

# The ENSEEIHT student clubs who run the sound, the video, the network and
# the photos, thanked next to the organiser.
CLUBS = ('TVn7', 'CAn7', 'net7', 'photo7')

# Credited in the dark area, for the recording itself.
VIDEO_CREDIT = 'Captation vidéo : TVn7'

HERE = os.path.dirname(os.path.abspath(__file__))


def filmed(event: Event) -> bool:
    """Workshops are not filmed, and a speaker may refuse for a talk."""
    if event._type == 'pause':
        return False
    if event_classes(event).startswith('workshop'):
        return False
    return not event.recording_refused


def filmed_events(conference: Conference) -> list:
    events = [event for day in conference._days.values()
              for room in day._rooms.values()
              if room._name not in EXCLUDED_ROOMS
              for event in room.sorted_events() if filmed(event)]
    return sorted(events, key=lambda event: (event._start_datetime,
                                             getattr(event, '_room', '')))


def kind(event: Event) -> str:
    """'Conférence 55min' -> 'Conférence': the length means nothing here."""
    label = re.sub(r'\s*\d+\s*(min|h)\w*$', '', event._type or '').strip()
    return label[:1].upper() + label[1:].lower() if label else 'Conférence'


def when(event: Event) -> str:
    """'Samedi 14 novembre 2026': the day capitalised, the month not."""
    text = f'{event._start_datetime:%A %d %B %Y}'
    return text[:1].upper() + text[1:]


def slug(text: str) -> str:
    ascii_text = unicodedata.normalize('NFKD', text)
    ascii_text = ascii_text.encode('ascii', 'ignore').decode('ascii').lower()
    return re.sub(r'[^a-z0-9]+', '-', ascii_text).strip('-')[:60].strip('-')


def filename(event: Event) -> str:
    """Sorted by when the talk was given, so the folder reads in order."""
    room = slug(getattr(event, '_room', '')) or 'salle'
    return (f'{event._start_datetime:%Y-%m-%d_%Hh%M}_{room}_'
            f'{slug(event.title) or event._id}.png')


def photos(event: Event) -> list:
    return (getattr(event, '_photos', None) or [])[:MAX_PHOTOS]


def first_guess(event: Event) -> float:
    """The largest size at which the title should fit, from its length."""
    title = event.title
    width = TITLE_WIDTH_WITH_PHOTOS if photos(event) else TITLE_WIDTH
    size = BASE_TITLE_SIZE
    while size > MIN_TITLE_SIZE:
        per_line = width / (CHARACTER_EM * size)
        lines = math.ceil(len(title) / per_line)
        if lines * LINE_EM * size <= TITLE_MAX_HEIGHT * 0.92:
            break
        size -= TITLE_SIZE_STEP
    return size


def svg_asset(name: str, fill: str = None) -> str:
    with open(os.path.join(HERE, 'assets', name), encoding='utf-8') as svg:
        drawing = svg.read()
    if fill:
        drawing = drawing.replace('<svg ', f'<svg fill="{fill}" ', 1)
    return drawing


def render_partners() -> str:
    """The band: organiser, sponsors on a grid, institutions, in three
    blocks set apart by rules."""
    groups = dict(content.PARTNER_GROUPS)

    def tier(name) -> str:
        logos = ''.join(
            f'<li>{partner_logo(partner, content.PARTNER_LOGOS)}</li>'
            for partner in groups.get(name, ()))
        return (f'<div class="tier {slug(name)}">'
                f'<p>{clean(name)}</p><ul>{logos}</ul></div>')

    columns = ''.join(
        f'<div class="column">{"".join(tier(name) for name in names)}</div>'
        for names in SPONSOR_COLUMNS)

    clubs = ''.join(f'<li>{partner_logo(club, content.PARTNER_LOGOS)}</li>'
                    for club in CLUBS)
    return f'''
        <footer class="partners">
            <div class="organiser">
                <p>Organisé par</p>
                <div class="toulibre">{svg_asset('toulibre.svg')}</div>
                <p class="with">Avec les clubs de l’N7</p>
                <ul class="clubs">{clubs}</ul>
            </div>
            <div class="sponsors">{columns}</div>
            <div class="public">{tier(INSTITUTIONS)}</div>
        </footer>'''


def render_cover(conference: Conference, event: Event, size: float,
                 partners: str, cross: str) -> str:
    speakers = clean(event.persons)
    people = f'<p class="speakers">{speakers}</p>' if speakers else ''
    faces = photos(event)
    portraits = ''
    if faces:
        images = ''.join(
            f'<li><img src="{pathlib.Path(path).resolve().as_uri()}" '
            f'alt=""></li>' for path in faces)
        portraits = (f'<ul class="photos count-{len(faces)}">'
                     f'{images}</ul>')
    return f'''
    <section class="cover{' with-photos' if faces else ''}">
        <div class="cross">{cross}</div>
        <header>
            <div class="brand"></div>
            <p class="edition">{clean(str(conference))}<br>
               <span>Toulouse &middot; ENSEEIHT</span></p>
        </header>
        <main>
            <p class="kicker"><span class="kind">{clean(kind(event))}</span>
               {clean(when(event))}</p>
            <h1 class="title" style="font-size: {size}px">
                {clean(event.title)}</h1>
            {people}
        </main>
        {portraits}
        <p class="credit">{clean(VIDEO_CREDIT)}</p>
        {partners}
    </section>'''


def build_html(conference: Conference, events: list, sizes: dict) -> str:
    partners = render_partners()
    # WeasyPrint does not carry currentColor into an inline SVG: the colour
    # is written in.
    cross = svg_asset('croix-occitane.svg', fill='#d03d00')
    return ''.join(render_cover(conference, event, sizes[event._id],
                                partners, cross)
                   for event in events)


def title_height(page) -> float:
    boxes = [page._page_box]
    while boxes:
        box = boxes.pop(0)
        element = getattr(box, 'element', None)
        if element is not None and 'title' in (element.get('class') or ''):
            return box.height
        boxes.extend(getattr(box, 'children', ()))
    return 0


def fit_titles(conference: Conference, events: list, css, fonts) -> tuple:
    """Each title at the largest size that holds its box: laid out, checked,
    and set a step smaller where it overflows, until all of them hold.

    Returns the sizes, and the talks whose title overflows even at the
    smallest size.
    """
    from weasyprint import HTML

    sizes = {event._id: first_guess(event) for event in events}
    while True:
        document = HTML(string=build_html(conference, events, sizes)).render(
            stylesheets=[css], font_config=fonts)
        shrunk = False
        overflowing = []
        for event, page in zip(events, document.pages):
            if title_height(page) <= TITLE_MAX_HEIGHT:
                continue
            if sizes[event._id] - TITLE_SIZE_STEP >= MIN_TITLE_SIZE:
                sizes[event._id] -= TITLE_SIZE_STEP
                shrunk = True
            else:
                overflowing.append(event)
        if not shrunk:
            return sizes, overflowing, document


def write_pngs(document, events: list, directory: str) -> list:
    import pypdfium2

    os.makedirs(directory, exist_ok=True)
    pdf = pypdfium2.PdfDocument(document.write_pdf())
    written = []
    for event, page in zip(events, pdf):
        # The PDF is in points, 72 to the inch; CSS px are 96 to the inch.
        image = page.render(scale=96 / 72).to_pil()
        if image.size != (WIDTH, HEIGHT):
            image = image.resize((WIDTH, HEIGHT))
        path = os.path.join(directory, filename(event))
        image.save(path)
        written.append(path)
    return written

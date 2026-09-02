"""Helpers shared by every output: escaping, QR codes, page fitting."""

import functools
import html
import io
import re
import unicodedata

import segno
from weasyprint import CSS, HTML

from schedule import Event

# Ink colour of the QR codes linking to each talk page.
QR_COLOUR = '#111111'


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


def fits_one_page(markup: str, css: CSS, fonts) -> bool:
    """Whether this markup lays out on a single page."""
    return len(HTML(string=markup).render(stylesheets=[css],
                                          font_config=fonts).pages) == 1


def fit_size(render_one, css, fonts, base: float, minimum: float,
             step: float) -> float | None:
    """Largest type size at which render_one(size) still takes one page.

    Returns None when even the smallest size overflows, so the caller can
    refuse to print rather than hand over a broken sheet.
    """
    size = base
    while not fits_one_page(render_one(size), css, fonts):
        size -= step
        if size < minimum:
            return None
    return size

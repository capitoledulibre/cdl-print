"""Helpers shared by every output: escaping, QR codes, page fitting."""

import functools
import html
import io
import os
import re
import unicodedata

import segno
from fontTools.ttLib import TTFont
from weasyprint import CSS, HTML

from schedule import Event

# Ink colour of the QR codes linking to each talk page.
QR_COLOUR = '#111111'

# The font every output embeds. Its coverage decides what can be printed.
FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    'fonts', 'FiraSans-Regular.woff2')

# Punctuation left stranded when a leading emoji is dropped.
STRANDED = ':;,.!? \u00a0\u2013\u2014-'


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


@functools.lru_cache(maxsize=1)
def printable() -> frozenset | None:
    """The code points the embedded font can actually draw.

    None when the font cannot be read, in which case nothing is dropped:
    losing a character is worse than risking a fallback glyph.
    """
    try:
        font = TTFont(FONT)
    except Exception:                                  # pragma: no cover
        return None
    covered = set()
    for table in font['cmap'].tables:
        covered |= set(table.cmap)
    return frozenset(covered)


def clean(value: str) -> str:
    """Prepare export data for the page.

    Three things happen here. The text is escaped, since titles such as
    'Guix & Nix' must not reach the parser as markup. The narrow no-break
    space Pretalx puts before French punctuation becomes the ordinary one,
    which the embedded font has. And anything the font cannot draw is
    dropped: a few talk titles carry emoji, and letting a fallback font
    supply them means a tofu box at the print shop and a grey blob in a
    greyscale run.
    """
    text = (value or '').replace('\u202f', '\u00a0')

    covered = printable()
    if covered is not None:
        kept = ''.join(character for character in text
                       if character.isspace() or ord(character) in covered)
        if kept != text:
            # Tidy up after what was removed, without touching the no-break
            # spaces: a dropped leading emoji leaves ': questionnez Docker'.
            kept = re.sub(r'[ \t]{2,}', ' ', kept).strip()
            kept = kept.lstrip(STRANDED).strip()
        text = kept

    return html.escape(text)


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

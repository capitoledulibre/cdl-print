"""The sponsor signs: one A4 landscape sheet per Platine and Or sponsor.

The same formula as the stand signs, for the sponsors' stands: the tier in
the header, and the sponsor as large as the sheet allows -- its logo, since
a sponsor is known by it.

A logo is never printed larger than MIN_LOGO_DPI allows. One too small to
make a sign at that resolution -- a 240px PNG off a website -- would come
out blurred, so that sponsor's name is set in type instead, fitted like a
stand name, and the build says which logo to replace with a vector one.
"""

import os
import sys

from weasyprint import CSS, HTML

import content
from render import clean
from standsigns import (BASE_NAME_SIZE, MIN_NAME_SIZE, NAME_SIZE_STEP,
                        name_fits, name_markup)

STYLESHEET = 'styles/sponsorsigns.css'
OUTPUT = 'conference-panneaux-sponsors-{year}.pdf'

TIERS = ('Platine', 'Or')

# The box a logo is fitted into, in mm, kept in step with the stylesheet.
LOGO_WIDTH_MM = 240
LOGO_HEIGHT_MM = 105

# A raster logo is printed no larger than this, and one that would come out
# smaller than MIN_LOGO_MM on its longer side is replaced by the name.
MIN_LOGO_DPI = 150
MIN_LOGO_MM = 80

LOGOS = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     'assets', 'partners')


def sponsors() -> list:
    """(tier, name) for every sponsor that gets a sign, tier by tier."""
    groups = dict(content.PARTNER_GROUPS)
    return [(tier, name) for tier in TIERS for name in groups.get(tier, ())]


def logo_size(name: str) -> tuple | None:
    """The size to print a sponsor's logo at, in mm, or None for the name.

    A vector logo fills its box. A raster one fills it too, unless that
    would take it under MIN_LOGO_DPI; then it is printed at the size that
    resolution allows, and if that is too small for a sign, not at all.
    """
    filename = content.PARTNER_LOGOS.get(name)
    if not filename:
        return None
    path = os.path.join(LOGOS, filename)
    if filename.endswith('.svg'):
        return LOGO_WIDTH_MM, LOGO_HEIGHT_MM

    from PIL import Image
    with Image.open(path) as image:
        width, height = image.size
    fit = min(LOGO_WIDTH_MM / width, LOGO_HEIGHT_MM / height)
    sharp = 25.4 / MIN_LOGO_DPI
    scale = min(fit, sharp)
    printed = (width * scale, height * scale)
    if max(printed) < MIN_LOGO_MM:
        return None
    return printed


def render_sign(conference, tier: str, name: str,
                name_size: float = None) -> str:
    size = logo_size(name)
    if size:
        path = os.path.join(LOGOS, content.PARTNER_LOGOS[name])
        width, height = size
        sponsor = (f'<img class="logo" src="file://{path}" alt="{clean(name)}"'
                   f' style="width: {width:.1f}mm; height: {height:.1f}mm">')
    else:
        sizing = f' style="font-size: {name_size}px"' if name_size else ''
        sponsor = f'<div class="name"{sizing}>{name_markup(name)}</div>'
    return f'''
        <section class="page {tier.lower()}">
            <header>
                <div class="brand"></div>
                <p class="kicker">Sponsor {clean(tier)}</p>
            </header>
            <div class="stand">{sponsor}</div>
            <footer>
                <span>{clean(str(conference))}</span>
                <span>Merci pour votre soutien</span>
            </footer>
        </section>
    '''


def build_html(conference, sizes: dict = None) -> str:
    sizes = sizes or {}
    return ''.join(render_sign(conference, tier, name, sizes.get(name))
                   for tier, name in sponsors())


def fit_signs(conference, css: CSS, fonts) -> tuple[dict, list]:
    """Type sizes for the sponsors printed by name, as for the stands.

    Also warns about every logo too small to print, so it can be replaced.
    """
    sizes = {}
    too_long = []
    for tier, name in sponsors():
        if logo_size(name):
            continue
        print(f'warning: the logo of {name} is too small to print on its '
              f'sign; its name is set instead. Put a vector logo in '
              f'assets/partners/ to use it.', file=sys.stderr)
        size = BASE_NAME_SIZE
        while True:
            document = HTML(string=render_sign(conference, tier, name, size)
                            ).render(stylesheets=[css], font_config=fonts)
            if name_fits(document):
                break
            size -= NAME_SIZE_STEP
            if size < MIN_NAME_SIZE:
                too_long.append(name)
                break
        sizes[name] = size
    return sizes, too_long

"""The stand signs: one A4 landscape sheet per stand of the village associatif.

Taped to the front of a table, read by someone walking down the hall: the
stand's name as large as the sheet allows, and the line the site gives it
when there is one. The stands come from content.STANDS, since the schedule
export does not carry them.
"""

from weasyprint import CSS, HTML

import content
from render import clean

STYLESHEET = 'styles/standsigns.css'
OUTPUT = 'conference-panneaux-stands-{year}.pdf'

# Type size of the stand name, in px, matching .name in the stylesheet.
BASE_NAME_SIZE = 240
MIN_NAME_SIZE = 60
NAME_SIZE_STEP = 10

# A name set on more lines than this reads as a paragraph, not a sign.
MAX_NAME_LINES = 2

# Room kept clear on either side of the name, in px, so that a long one
# does not run edge to edge.
SIDE_MARGIN = 36


def name_markup(name: str) -> str:
    """The name, a hyphenated word kept whole: 'Borsalinux-' then 'fr' on
    the next line reads as two names."""
    return ' '.join(
        f'<span class="whole">{clean(word)}</span>' if '-' in word
        else clean(word)
        for word in name.split(' '))


def render_sign(conference, name: str, about: str,
                name_size: float = None) -> str:
    sizing = f' style="font-size: {name_size}px"' if name_size else ''
    line = f'<p class="about">{clean(about)}</p>' if about else ''
    return f'''
        <section class="page">
            <header>
                <div class="brand"></div>
                <p class="kicker">Village associatif</p>
            </header>
            <div class="stand">
                <div class="name"{sizing}>{name_markup(name)}</div>
                {line}
            </div>
            <footer>
                <span>{clean(str(conference))}</span>
                <span>capitoledulibre.org</span>
            </footer>
        </section>
    '''


def build_html(conference, sizes: dict = None) -> str:
    sizes = sizes or {}
    return ''.join(render_sign(conference, name, about, sizes.get(name))
                   for name, about in content.STANDS)


def boxes_by_class(page) -> dict:
    """The first laid out box of each class this sheet uses."""
    found = {}
    boxes = [page._page_box]
    while boxes:
        box = boxes.pop()
        element = getattr(box, 'element', None)
        if element is not None:
            found.setdefault(element.get('class') or '', box)
        boxes.extend(reversed(getattr(box, 'children', ())))
    return found


def name_fits(document) -> bool:
    """Whether the name holds its sheet, measured rather than assumed.

    Counting pages is not enough here. A single long word -- 'RxLaboratorio'
    -- cannot break, and at too large a size it does not add a page: its
    flex container widens to hold it, past the edge of the sheet. And a name
    set on three lines overflows its fixed-height sheet up into the header
    without adding one either. So the name must keep to MAX_NAME_LINES, each
    line inside the sheet's text area less SIDE_MARGIN, and the name and its
    line under it inside the room the sheet leaves them.
    """
    if len(document.pages) != 1:
        return False
    boxes = boxes_by_class(document.pages[0])
    sheet, stand, name = boxes['page'], boxes['stand'], boxes['name']
    lines = list(name.children)
    if len(lines) > MAX_NAME_LINES:
        return False
    left = sheet.content_box_x() + SIDE_MARGIN
    right = sheet.content_box_x() + sheet.width - SIDE_MARGIN
    for line in lines:
        for child in getattr(line, 'children', ()):
            if child.position_x < left - 0.5 \
                    or child.position_x + child.margin_width() > right + 0.5:
                return False
    used = name.margin_height()
    if 'about' in boxes:
        used += boxes['about'].margin_height()
    return used <= stand.height + 0.5


def fit_signs(conference, css: CSS, fonts) -> tuple[dict, list]:
    """The largest size at which each name holds its sheet.

    Returns the sizes, and the stands whose name will not hold even at the
    smallest size.
    """
    sizes = {}
    too_long = []
    for name, about in content.STANDS:
        size = BASE_NAME_SIZE
        while True:
            markup = render_sign(conference, name, about, size)
            document = HTML(string=markup).render(stylesheets=[css],
                                                  font_config=fonts)
            if name_fits(document):
                break
            size -= NAME_SIZE_STEP
            if size < MIN_NAME_SIZE:
                too_long.append(name)
                break
        if size != BASE_NAME_SIZE and name not in too_long:
            sizes[name] = size
    return sizes, too_long

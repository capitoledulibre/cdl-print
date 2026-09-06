"""The room signs: one A3 sheet per room, the room name and nothing else.

The door posters answer "what is on in there?"; this answers the question
asked from the far end of the corridor, "which room is this?". It is the
companion sheet of the programme, so it is deliberately empty: a name set as
large as the paper allows, and no line of type competing with it.

One sheet per room, not per room and per day: a door does not change name
between Saturday and Sunday.
"""

from weasyprint import CSS

from render import clean, fit_size
from schedule import Conference, EXCLUDED_ROOMS, Room

STYLESHEET = 'styles/signage.css'
OUTPUT = 'conference-panneaux-salles-{year}.pdf'

# Type size of the room name, in px, matching .name in the stylesheet. A
# short code such as 'B207' takes the largest; 'Hall C' or a named amphi is
# stepped down until it fits the sheet on one line.
BASE_NAME_SIZE = 520
MIN_NAME_SIZE = 90
NAME_SIZE_STEP = 20


def render_sign(conference: Conference, room: Room,
                name_size: float = None) -> str:
    sizing = f' style="font-size: {name_size}px"' if name_size else ''
    return f'''
        <section class="page">
            <header>
                <div class="brand"></div>
                <p class="kicker">Salle</p>
            </header>
            <div class="name"{sizing}>{clean(room._name)}</div>
            <footer>
                <span>{clean(str(conference))}</span>
                <span>Programme de la salle ci-contre</span>
            </footer>
        </section>
    '''


def signed_rooms(conference: Conference):
    """Every room that earns a sign, once, in printing order.

    A room is parsed once per day, so the same door comes round twice; the
    first one wins and the second is dropped.
    """
    seen = set()
    for day in conference._days.values():
        for room in day._rooms.values():
            if room._name in EXCLUDED_ROOMS or room._name in seen:
                continue
            if not room.sorted_events():
                continue
            seen.add(room._name)
            yield room


def build_html(conference: Conference, sizes: dict = None) -> str:
    sizes = sizes or {}
    return ''.join(render_sign(conference, room, sizes.get(room._name))
                   for room in signed_rooms(conference))


def fit_signs(conference: Conference, css: CSS, fonts) -> tuple[dict, list]:
    """Pick the largest type size at which each name still fits its sheet.

    Same bargain as the door posters: a name too long for the default size
    would push the footer onto a second sheet rather than shrink, so step it
    down instead, and report the ones that will not fit at all.
    """
    sizes = {}
    too_long = []

    for room in signed_rooms(conference):
        size = fit_size(lambda at: render_sign(conference, room, at),
                        css, fonts,
                        BASE_NAME_SIZE, MIN_NAME_SIZE, NAME_SIZE_STEP)
        if size is None:
            too_long.append(str(room))
        elif size != BASE_NAME_SIZE:
            sizes[room._name] = size

    return sizes, too_long

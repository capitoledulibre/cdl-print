"""The room sheets: one A4 per room and per day, for the volunteer on duty.

Not a programme. This is the working document of whoever holds a room: who
is due, for how long, and the three things to tick before each talk. It also
carries what nothing else does -- that a speaker refused to be filmed.
"""

from render import clean
from schedule import Conference, Day, EXCLUDED_ROOMS, Room, build_breaks

STYLESHEET = 'styles/roomsheets.css'
OUTPUT = 'conference-feuilles-salles-{year}.pdf'

# Ticked off by hand, in the order they happen.
CHECKS = ('Intervenant arrivé', 'Son et vidéo testés', 'Minutage lancé')


def render_row(event) -> str:
    minutes = int((event._end_datetime
                   - event._start_datetime).total_seconds() // 60)
    if event._type == 'pause':
        return f'''
            <tr class="pause">
                <td class="when">{event._start_datetime:%Hh%M}</td>
                <td colspan="2">{clean(event.title)} &mdash;
                    reprise à {event._end_datetime:%Hh%M}</td>
            </tr>'''

    people = (f'<p class="who">{clean(event.persons)}</p>'
              if event._persons else '<p class="who">&mdash;</p>')
    warning = ('<p class="warning">Pas de captation : cet intervenant a '
               'refusé d’être filmé</p>' if event.recording_refused else '')
    boxes = ''.join(f'<span class="box">{clean(check)}</span>'
                    for check in CHECKS)
    return f'''
            <tr>
                <td class="when">
                    <b>{event._start_datetime:%Hh%M}</b>
                    <i>{event._end_datetime:%Hh%M}</i>
                    <span class="length">{minutes} min</span>
                </td>
                <td class="what">
                    <p class="title">{clean(event.title)}</p>
                    {people}
                    {warning}
                </td>
                <td class="checks">{boxes}</td>
            </tr>'''


def render_sheet(conference: Conference, day: Day, room: Room) -> str:
    talks = room.sorted_events()
    if not talks:
        return ''

    events = sorted(talks + build_breaks(room, day, talks),
                    key=lambda event: event._start_datetime)
    rows = ''.join(render_row(event) for event in events)
    refused = sum(1 for event in talks if event.recording_refused)

    notice = ''
    if refused == 1:
        notice = ('<p class="notice">Une intervention de cette salle ne doit '
                  'pas être filmée. Voir la ligne signalée.</p>')
    elif refused:
        notice = (f'<p class="notice">{refused} interventions de cette salle '
                  'ne doivent pas être filmées. Voir les lignes '
                  'signalées.</p>')

    return f'''
    <section class="page">
        <header>
            <div class="ident">
                <p class="kicker">Feuille de salle &middot; bénévoles</p>
                <h1>{clean(room._name)}</h1>
            </div>
            <div class="day">
                <p>{day._date:%A %d %B}</p>
                <p class="count">{len(talks)} interventions</p>
            </div>
        </header>
        {notice}
        <table>
            <thead>
                <tr>
                    <th>Horaire</th>
                    <th>Intervention</th>
                    <th>À cocher</th>
                </tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>
        <div class="handover">
            <p><span class="field">Bénévole du matin</span>
               <span class="field">Téléphone</span></p>
            <p><span class="field">Bénévole de l’après-midi</span>
               <span class="field">Téléphone</span></p>
        </div>
        <div class="notes">
            <p class="label">Incidents, retards, remarques</p>
        </div>
        <footer>
            <span>{clean(str(conference))}</span>
            <span>Salle {clean(room._name)} &middot; {day._date:%A}</span>
        </footer>
    </section>'''


def build_html(conference: Conference) -> str:
    return ''.join(
        render_sheet(conference, day, room)
        for day in conference._days.values()
        for room in day._rooms.values()
        if room._name not in EXCLUDED_ROOMS and room.sorted_events())

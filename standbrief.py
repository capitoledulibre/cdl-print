"""The stand briefing: one A4 for each stand, associations' and sponsors'.

Handed over at setup, read once and pinned behind the table. The run of the
weekend is drawn from the schedule; the wifi credentials only the team
knows, and come from content.py. A field the team has not filled in
prints as a blank line rather than as a guess.
"""

import os
import sys
from datetime import datetime

import content
from render import campus_plan, clean
from schedule import BREAKS, Conference, Day, EXCLUDED_ROOMS

STYLESHEET = 'styles/standbrief.css'
OUTPUT = 'conference-briefing-stands-{year}.pdf'

# One sheet, pinned behind a table.
EXPECTED_PAGES = 1


def at(day: Day, hhmm: str) -> datetime:
    hours, minutes = (int(part) for part in hhmm.split(':'))
    return day._date.replace(hour=hours, minute=minutes)


def day_talks(day: Day) -> list:
    return sorted((event for room in day._rooms.values()
                   if room._name not in EXCLUDED_ROOMS
                   for event in room.sorted_events()),
                  key=lambda event: event._start_datetime)


def day_moments(conference: Conference, day: Day) -> list:
    """The day's landmarks for a stand: (time, what), in time order.

    Only what moves the crowd past the stands: doors, first and last talk,
    the breaks, and the talks the leaflet puts forward in the amphi.
    """
    import booklet

    talks = day_talks(day)
    if not talks:
        return []
    moments = [(at(day, content.STAND_OPENING), 'Ouverture au public')]

    for pause in BREAKS:
        if pause.weekdays is None or day._date.isoweekday() in pause.weekdays:
            label = pause.title
            if 'déjeuner' in label:
                label += ' : affluence aux stands'
            else:
                label += ' : les salles se vident'
            moments.append((at(day, pause.start), label))

    for event, _why in booklet.find_highlights(conference):
        if event._start_datetime.date() != day._date.date():
            continue
        if any(fragment in event.title
               for fragment in content.LEAFLET_HIGHLIGHTS_LEFT_OUT):
            continue
        room = clean(getattr(event, '_room', ''))
        moments.append((event._start_datetime,
                        f'{clean(event.title)} ({room})'))

    # The opening talk usually starts the day; a generic line at the same
    # time would only repeat it.
    first = talks[0]._start_datetime
    if all(when != first for when, _what in moments):
        moments.append((first, 'Premières conférences'))

    end = max(event._end_datetime for event in talks)
    moments.append((end, 'Fin des conférences'))
    if day._date.isoweekday() == 6:
        moments.append((at(day, content.STAND_COCKTAIL),
                        'Cocktail offert, hall principal'))
    return sorted(moments, key=lambda moment: moment[0])


# Fields read from the environment rather than from content.py, which is
# published with the repository: CDL_WIFI_PASSWORD=... uv run python gen.py
STAND_BRIEF_SECRETS = {'Mot de passe wifi': 'CDL_WIFI_PASSWORD'}


def value_of(name: str) -> str | None:
    variable = STAND_BRIEF_SECRETS.get(name)
    if variable and os.environ.get(variable):
        return os.environ[variable]
    return content.STAND_BRIEF_FIELDS.get(name)


def field(name: str) -> str:
    value = value_of(name)
    if value:
        return f'<span class="value">{clean(value)}</span>'
    return '<span class="blank"></span>'


def missing_fields() -> list:
    return [name for name in content.STAND_BRIEF_FIELDS
            if not value_of(name)]


def render_day(conference: Conference, day: Day) -> str:
    rows = ''.join(
        f'<li><b>{when:%Hh%M}</b><span>{what}</span></li>'
        for when, what in day_moments(conference, day))
    return f'''
            <div class="day">
                <h3>{day._date:%A %d %B}</h3>
                <ol class="moments">{rows}</ol>
            </div>'''


def build_html(conference: Conference) -> str:
    days = [day for day in conference._days.values() if day_talks(day)]
    first, last = days[0], days[-1]
    dates = f'{first._date:%d} et {last._date:%d %B %Y}'
    weekend = ''.join(render_day(conference, day) for day in days)
    help_lines = ''.join(f'<li>{clean(line)}</li>'
                         for line in content.STAND_HELP)
    tips = ''.join(f'<dt>{clean(name)}</dt><dd>{clean(about)}</dd>'
                   for name, about in content.STAND_TIPS)
    legend = ''.join(f'<li><b>{number}</b>{clean(label)}</li>'
                     for number, label in enumerate(content.PLAN_LEGEND, 1))

    return f'''
    <section class="page">
        <header>
            <div class="brand"></div>
            <div class="ident">
                <h1>{clean(content.STAND_BRIEF_TITLE)}</h1>
                <p>{dates} &middot; ENSEEIHT, Toulouse</p>
            </div>
        </header>
        <p class="lede">{clean(content.STAND_BRIEF_LEDE)}</p>

        <h2>Le week-end</h2>
        <div class="days">{weekend}</div>

        <div class="boxes">
            <div class="box wifi">
                <h2>Wifi</h2>
                <p><span class="label">Réseau</span>{field('Réseau wifi')}</p>
                <p><span class="label">Identifiant</span>
                   {field('Identifiant wifi')}</p>
                <p><span class="label">Mot de passe</span>
                   {field('Mot de passe wifi')}</p>
                <p class="steps">{clean(content.STAND_WIFI_STEPS)}</p>
                <p class="note">{clean(content.STAND_WIFI_NOTE)}</p>
            </div>
            <div class="box help">
                <h2>Un souci ?</h2>
                <ul>{help_lines}</ul>
            </div>
        </div>

        <div class="bottom">
            <figure class="plan">
                <h2>Le site</h2>
                {campus_plan()}
                <ol class="legend">{legend}</ol>
            </figure>
            <div class="tips">
                <h2>{clean(content.STAND_TIPS_TITLE)}</h2>
                <dl>{tips}</dl>
            </div>
        </div>

        <footer>
            <span>{clean(str(conference))}</span>
            <span>{clean(content.STAND_BRIEF_TITLE)}</span>
        </footer>
    </section>'''


def warn_missing():
    for name in missing_fields():
        where = (f'set {STAND_BRIEF_SECRETS[name]} in the environment'
                 if name in STAND_BRIEF_SECRETS
                 else 'STAND_BRIEF_FIELDS in content.py')
        print(f'warning: the stand briefing has no {name!r} yet; it prints '
              f'as a blank to fill in ({where})', file=sys.stderr)

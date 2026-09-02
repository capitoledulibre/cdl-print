"""Tests for the paper schedule generator.

The rendering tests are the ones that matter: the layout gives each room a
fixed height A3 page, so a room that grows past it does not fail loudly, it
either spills onto a stray page or has its footer quietly clipped. These
assertions are what turns that into a build failure.
"""

import os
import re
from datetime import datetime

import pytest
from weasyprint import CSS, HTML
from weasyprint.text.fonts import FontConfiguration
from xml.etree import ElementTree

import gen
import posters
import render
import schedule

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, os.pardir)
FIXTURE = os.path.join(HERE, 'fixtures', 'schedule-2025.xml')


def stylesheet(name: str) -> str:
    return os.path.join(ROOT, name)


STYLESHEET = stylesheet(posters.STYLESHEET)


def page_text(page) -> str:
    """All the text laid out on a rendered page."""
    collected = []

    def walk(box):
        text = getattr(box, 'text', None)
        if text:
            collected.append(text)
        for child in getattr(box, 'children', ()):
            walk(child)

    walk(page._page_box)
    return ' '.join(collected)


@pytest.fixture(scope='module')
def conference() -> schedule.Conference:
    parsed = schedule.Conference(FIXTURE)
    parsed.parse()
    return parsed


@pytest.fixture(scope='module')
def room_days(conference) -> list:
    """Every (day, room) of the fixture that has at least one event."""
    return [(day, room)
            for day in conference._days.values()
            for room in day._rooms.values()
            if room.sorted_events()]


def lay_out(conference) -> tuple[list, dict, list]:
    """Run the real pipeline: size every room to its sheet, then render."""
    fonts = FontConfiguration()
    css = CSS(filename=STYLESHEET, font_config=fonts)
    sizes, too_dense = posters.fit_rooms(conference, css, fonts, show_qr=False)
    document = HTML(string=posters.build_html(conference, show_qr=False,
                                          sizes=sizes)).render(
        stylesheets=[css], font_config=fonts)
    return [page_text(page) for page in document.pages], sizes, too_dense


@pytest.fixture(scope='module')
def laid_out(conference) -> tuple:
    return lay_out(conference)


@pytest.fixture(scope='module')
def pages(laid_out) -> list:
    return laid_out[0]


# --- the layout must not overflow ------------------------------------------

def test_one_page_per_room_and_day(pages, room_days):
    assert len(pages) == len(room_days)


def test_every_page_carries_its_footer(pages):
    """A clipped page loses its footer without losing a page."""
    without = [number for number, text in enumerate(pages, 1)
               if 'Salle' not in text]
    assert without == []


def squashed(text: str) -> str:
    """Drop everything a line break can fall on, so wrapping does not matter.

    A title breaking after a hyphen or an apostrophe is good typography, not a
    missing word.
    """
    return re.sub(r"[\s'\u2019-]+", '', text).replace('\u202f', '\u00a0')


def test_no_talk_is_lost(pages, conference):
    laid_out = squashed(' '.join(pages))
    for event in conference._events.values():
        assert squashed(event.title) in laid_out, event.title
        for person in event._persons.values():
            assert squashed(person._name) in laid_out, person._name


# --- breaks ----------------------------------------------------------------

def test_no_break_overlaps_a_talk(room_days):
    for day, room in room_days:
        talks = room.sorted_events()
        for pause in schedule.build_breaks(room, day, talks):
            for talk in talks:
                assert not schedule._overlaps(
                    pause._start_datetime, pause._end_datetime,
                    talk._start_datetime, talk._end_datetime), \
                    f'{pause._title} clashes with {talk.title} in {room}'


def test_breaks_stay_inside_the_programme(room_days):
    for day, room in room_days:
        talks = room.sorted_events()
        first, last = talks[0]._start_datetime, talks[-1]._end_datetime
        for pause in schedule.build_breaks(room, day, talks):
            assert pause._start_datetime >= first
            assert pause._end_datetime <= last


def test_all_day_workshop_gets_no_break(conference):
    """B105 runs 11:00 to 18:25 without stopping."""
    day = list(conference._days.values())[0]
    room = day._rooms['B105']
    assert schedule.build_breaks(room, day, room.sorted_events()) == []


def test_evening_only_room_gets_no_lunch_break(conference):
    """Hall C holds the 19:30 buffet and nothing else."""
    day = list(conference._days.values())[0]
    room = day._rooms['Hall C']
    assert schedule.build_breaks(room, day, room.sorted_events()) == []


def test_breaks_are_distinct_objects_per_room(conference):
    day = list(conference._days.values())[0]
    identifiers = set()
    for room in day._rooms.values():
        for pause in schedule.build_breaks(room, day, room.sorted_events()):
            assert pause._id not in identifiers
            identifiers.add(pause._id)


# --- poster mode -----------------------------------------------------------

def test_poster_mode_does_not_count_breaks(conference):
    """B205 holds two workshops around a lunch break, so it is a poster."""
    day = list(conference._days.values())[0]
    room = day._rooms['B205']
    assert len(room.sorted_events()) == 2
    assert 'timeline poster' in posters.render_room(conference, day, room,
                                                show_qr=False)


def test_dense_room_is_not_a_poster(conference):
    day = list(conference._days.values())[0]
    room = day._rooms['B00']
    assert 'poster' not in posters.render_room(conference, day, room,
                                           show_qr=False)


# --- export data reaching the page -----------------------------------------

def test_event_type_becomes_usable_classes():
    day = schedule.Day(datetime(2025, 11, 15))
    event = schedule.Event('1', day)

    event._type = 'Conférence 25min'
    assert render.event_classes(event) == 'talk conference-25min'

    event._type = 'Atelier 2h'
    assert render.event_classes(event) == 'workshop atelier-2h'

    event._type = 'pause'
    assert render.event_classes(event) == 'pause'


def test_unknown_type_still_gets_its_family():
    day = schedule.Day(datetime(2025, 11, 15))
    event = schedule.Event('1', day)
    event._type = 'Table ronde 90min'
    assert render.event_classes(event).startswith('talk ')


def test_markup_in_a_title_is_escaped():
    assert render.clean('Guix & Nix') == 'Guix &amp; Nix'
    assert '<script>' not in render.clean('<script>alert(1)</script>')


def test_narrow_no_break_space_is_replaced():
    """The embedded font has no glyph for U+202F, which Pretalx emits."""
    assert render.clean('Quacken : libre') == 'Quacken : libre'


def test_speakers_are_enumerated_in_french():
    day = schedule.Day(datetime(2025, 11, 15))
    event = schedule.Event('1', day)
    assert event.persons == ''

    for index, name in enumerate(('Ada', 'Grace', 'Alan')):
        person = schedule.Person(str(index))
        person._name = name
        event._persons[str(index)] = person
        if index == 0:
            assert event.persons == 'Ada'
        elif index == 1:
            assert event.persons == 'Ada et Grace'
        else:
            assert event.persons == 'Ada, Grace et Alan'


# --- the model -------------------------------------------------------------

def test_conference_gathers_its_events_and_people(conference):
    from_rooms = sum(len(room._events)
                     for day in conference._days.values()
                     for room in day._rooms.values())
    assert len(conference._events) == from_rooms
    assert conference._persons
    assert all(person._name for person in conference._persons.values())


def test_a_room_used_on_both_days_keeps_the_days_apart(conference):
    saturday, sunday = conference._days.values()
    assert saturday._rooms['B00'] is not sunday._rooms['B00']
    for event in saturday._rooms['B00']._events.values():
        assert event._day is saturday


# --- the edition to build --------------------------------------------------

def test_year_comes_from_the_environment(monkeypatch):
    monkeypatch.setenv(gen.YEAR_ENV_VAR, '2022')
    assert gen.parse_args([]).year == 2022


def test_command_line_beats_the_environment(monkeypatch):
    monkeypatch.setenv(gen.YEAR_ENV_VAR, '2022')
    assert gen.parse_args(['--year', '2019']).year == 2019


def test_unparsable_environment_falls_back_to_the_current_year(monkeypatch):
    monkeypatch.setenv(gen.YEAR_ENV_VAR, 'pouet')
    assert gen.default_year() == datetime.now().year


def test_year_fills_in_the_schedule_url():
    assert '2026' in gen.parse_args(['--year', '2026']).url


# --- failure modes ---------------------------------------------------------

def test_a_missing_schedule_is_reported(capsys):
    assert gen.main(['--schedule-file', '/does/not/exist.xml',
                     '--only', 'salles']) == 1
    assert 'cannot read the schedule' in capsys.readouterr().err


def test_invalid_xml_is_reported(tmp_path, capsys):
    broken = tmp_path / 'broken.xml'
    broken.write_text('<schedule><oops')
    assert gen.main(['--schedule-file', str(broken),
                     '--only', 'salles']) == 1
    assert 'not valid XML' in capsys.readouterr().err


def test_the_fixture_is_the_shape_we_think_it_is():
    """Guards the other tests against a fixture quietly losing a room."""
    rooms = {room.get('name')
             for room in ElementTree.parse(FIXTURE).iter('room')}
    assert {'B00', 'B105', 'Hall C', 'B205', 'A304', 'A303'} <= rooms


# --- dense rooms are scaled to fit ------------------------------------------

DENSE_FIXTURE = os.path.join(os.path.dirname(__file__), 'fixtures',
                             'schedule-2024-dense.xml')


@pytest.fixture(scope='module')
def dense() -> schedule.Conference:
    parsed = schedule.Conference(DENSE_FIXTURE)
    parsed.parse()
    return parsed


def test_a_dense_room_still_fits_one_sheet(dense):
    """The 2024 export used to spill B00's footer and clip A001's away."""
    rendered, _sizes, too_dense = lay_out(dense)
    expected = list(posters.printable_rooms(dense))

    assert too_dense == []
    assert len(rendered) == len(expected)
    assert all('Salle' in text for text in rendered)


def test_a_dense_room_is_the_one_scaled_down(dense):
    _pages, sizes, _too_dense = lay_out(dense)
    assert sizes, 'the 2024 rooms should need turning down'
    assert all(size < posters.BASE_TIMELINE_SIZE for size in sizes.values())
    assert all(size >= posters.MIN_TIMELINE_SIZE for size in sizes.values())


def test_a_room_that_fits_is_left_alone(laid_out):
    """Nothing in the 2025 programme needs shrinking, so nothing is shrunk."""
    _pages, sizes, too_dense = laid_out
    assert sizes == {}
    assert too_dense == []


def test_a_room_that_cannot_fit_is_reported(monkeypatch, capsys, tmp_path):
    """With no room to shrink into, the run must refuse rather than print."""
    monkeypatch.setattr(posters, 'MIN_TIMELINE_SIZE', posters.BASE_TIMELINE_SIZE + 1)
    assert gen.main(['--schedule-file', DENSE_FIXTURE, '--only', 'salles',
                     '--output-dir', str(tmp_path), '--no-qr']) == 1
    assert 'do not fit on one sheet' in capsys.readouterr().err
    assert list(tmp_path.iterdir()) == []

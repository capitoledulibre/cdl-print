"""The room sheets, the room signs and the leaflet.

Each is a physical object before it is a PDF: a sheet a volunteer writes on,
a name hung on a door, and one sheet folded in three. What these hold is that
shape, plus the one fact only the room sheets carry -- that a speaker refused
to be filmed.
"""

import locale
import os
import re

import pytest
from weasyprint import CSS, HTML
from weasyprint.text.fonts import FontConfiguration

import gen
import leaflet
import roomsheets
import schedule
import signage

locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, os.pardir)
FIXTURE = os.path.join(HERE, 'fixtures', 'schedule-2025.xml')

MM = 96 / 25.4


@pytest.fixture(scope='module')
def conference() -> schedule.Conference:
    parsed = schedule.Conference(FIXTURE)
    parsed.parse()
    return parsed


def lay_out(markup: str, stylesheet: str):
    fonts = FontConfiguration()
    css = CSS(filename=os.path.join(ROOT, stylesheet), font_config=fonts)
    return HTML(string=markup).render(stylesheets=[css], font_config=fonts)


def page_text(page) -> str:
    collected = []

    def walk(box):
        text = getattr(box, 'text', None)
        if text:
            collected.append(text)
        for child in getattr(box, 'children', ()):
            walk(child)

    walk(page._page_box)
    return ' '.join(collected)


# --- the recording refusal --------------------------------------------------

def test_a_recording_refusal_is_read_from_the_export(conference):
    """<recording> wraps its children, so the generic branch stored nothing."""
    refused = [event for event in conference._events.values()
               if event.recording_refused]
    assert len(refused) == 1
    assert 'Glitcher' in refused[0].title


def test_the_refusal_reaches_the_room_sheet(conference):
    """Nothing else in the whole run says so, so this must not be lost."""
    refused = next(event for event in conference._events.values()
                   if event.recording_refused)
    day = next(day for day in conference._days.values()
               if refused in day._events.values())
    room = next(room for room in day._rooms.values()
                if refused in room._events.values())

    sheet = roomsheets.render_sheet(conference, day, room)
    assert 'Pas de captation' in sheet
    assert 'ne doit pas être filmée' in sheet


def test_a_room_without_a_refusal_carries_no_notice(conference):
    day = list(conference._days.values())[0]
    room = day._rooms['B205']
    assert not any(event.recording_refused for event in room.sorted_events())
    assert 'captation' not in roomsheets.render_sheet(conference, day, room)


# --- the room sheets --------------------------------------------------------

def test_one_room_sheet_per_room_and_day(conference):
    document = lay_out(roomsheets.build_html(conference),
                       roomsheets.STYLESHEET)
    expected = [(day, room) for day in conference._days.values()
                for room in day._rooms.values() if room.sorted_events()]
    assert len(document.pages) == len(expected)
    for page in document.pages:
        assert page.width == pytest.approx(210 * MM, abs=2)


def test_a_room_sheet_lists_its_talks_and_its_checks(conference):
    document = lay_out(roomsheets.build_html(conference),
                       roomsheets.STYLESHEET)
    first = page_text(document.pages[0])
    for check in roomsheets.CHECKS:
        assert check in first
    assert 'Bénévole du matin' in first


# --- the room signs ---------------------------------------------------------

def signs(conference) -> str:
    """The signs as gen.py builds them: fitted, so each holds one sheet."""
    fonts = FontConfiguration()
    css = CSS(filename=os.path.join(ROOT, signage.STYLESHEET),
              font_config=fonts)
    sizes, too_long = signage.fit_signs(conference, css, fonts)
    assert not too_long
    return signage.build_html(conference, sizes=sizes)


def test_one_sign_per_room_whichever_days_it_is_used(conference):
    """A door does not change name between Saturday and Sunday."""
    document = lay_out(signs(conference), signage.STYLESHEET)
    names = {room._name for day in conference._days.values()
             for room in day._rooms.values() if room.sorted_events()}
    assert len(document.pages) == len(names)
    for page in document.pages:
        assert page.width == pytest.approx(420 * MM, abs=2)
        assert page.height == pytest.approx(297 * MM, abs=2)


def test_a_sign_carries_its_room_name(conference):
    document = lay_out(signs(conference), signage.STYLESHEET)
    laid_out = [page_text(page) for page in document.pages]
    for room in signage.signed_rooms(conference):
        assert any(room._name in text for text in laid_out), room._name


def test_a_long_name_is_stepped_down_rather_than_spilled(conference):
    """Otherwise the footer would quietly land on a second sheet."""
    fonts = FontConfiguration()
    css = CSS(filename=os.path.join(ROOT, signage.STYLESHEET),
              font_config=fonts)
    sizes, too_long = signage.fit_signs(conference, css, fonts)
    assert not too_long
    assert sizes['Hall C'] < signage.BASE_NAME_SIZE


def test_a_name_that_will_not_fit_at_all_is_refused(conference, tmp_path,
                                                    capsys, monkeypatch):
    monkeypatch.setattr(signage, 'BASE_NAME_SIZE', 5000)
    monkeypatch.setattr(signage, 'MIN_NAME_SIZE', 5000)
    assert gen.main(['--schedule-file', FIXTURE, '--no-audience',
                     '--only', 'panneaux',
                     '--output-dir', str(tmp_path)]) == 1
    assert 'do not fit their sheet' in capsys.readouterr().err
    assert list(tmp_path.iterdir()) == []


# --- the leaflet ------------------------------------------------------------

def test_the_leaflet_is_one_folded_sheet(conference):
    document = lay_out(leaflet.build_html(conference), leaflet.STYLESHEET)
    assert len(document.pages) == leaflet.EXPECTED_PAGES
    for page in document.pages:
        assert page.width == pytest.approx(297 * MM, abs=2)
        assert page.height == pytest.approx(210 * MM, abs=2)


def test_a_third_page_is_refused(conference, tmp_path, capsys, monkeypatch):
    """A panel outgrowing its 99mm cannot be folded, so it must not ship."""
    monkeypatch.setattr(leaflet, 'EXPECTED_PAGES', 99)
    assert gen.main(['--schedule-file', FIXTURE, '--no-audience',
                     '--only', 'depliant',
                     '--output-dir', str(tmp_path)]) == 1
    assert 'a panel no longer fits' in capsys.readouterr().err
    assert list(tmp_path.iterdir()) == []


def squashed(text: str) -> str:
    """Drop what a line break can fall on, so wrapping cannot fail a test."""
    return re.sub(r"[\s'\u2019-]+", '', text).replace('\u202f', '\u00a0')


def test_the_leaflet_holds_every_talk(conference):
    document = lay_out(leaflet.build_html(conference), leaflet.STYLESHEET)
    laid_out = squashed(' '.join(page_text(page) for page in document.pages))
    for day in conference._days.values():
        for event in leaflet.day_talks(day):
            # Titles are shortened to the panel width, so only the head of a
            # long one is on the sheet.
            assert squashed(event.title)[:15] in laid_out, event.title


# --- all of them at once ----------------------------------------------------

def test_one_run_writes_every_output(tmp_path, conference):
    assert gen.main(['--schedule-file', FIXTURE, '--no-qr',
                     '--no-audience', '--output-dir', str(tmp_path)]) == 0
    assert len(list(tmp_path.iterdir())) == len(gen.OUTPUTS)

"""The three printed outputs, end to end.

Each has a shape a printer depends on: one sheet per room, one per day, and a
booklet that can actually be folded. These check that shape rather than the
look, which is what a test can honestly hold.
"""

import locale
import os
import re

import pytest
from weasyprint import CSS, HTML
from weasyprint.text.fonts import FontConfiguration

import booklet
import content
import gen
import overview
import posters
import render
import schedule

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


# --- the hall poster --------------------------------------------------------

def test_the_hall_poster_is_one_a0_sheet_per_day(conference):
    document = lay_out(overview.build_html(conference), overview.STYLESHEET)
    assert len(document.pages) == len(conference._days)
    for page in document.pages:
        assert page.width == pytest.approx(1189 * MM, abs=2)
        assert page.height == pytest.approx(841 * MM, abs=2)


def test_the_hall_poster_names_every_room_of_the_day(conference):
    document = lay_out(overview.build_html(conference), overview.STYLESHEET)
    for page, day in zip(document.pages, conference._days.values()):
        text = page_text(page)
        for room in overview.day_rooms(day):
            assert room._name in text


def test_a_title_is_shortened_to_its_block():
    long = 'un titre interminable ' * 20
    assert len(overview.shorten(long, 40)) <= 41
    assert overview.shorten('court', 40) == 'court'


def test_a_shorter_talk_gets_a_smaller_budget():
    short = overview.title_budget(14, 600, 25)
    long = overview.title_budget(14, 600, 55)
    assert 0 < short < long


# --- the booklet ------------------------------------------------------------

@pytest.fixture(scope='module')
def booklet_pages(conference) -> list:
    markup = booklet.build_html(conference, show_qr=False)
    document = lay_out(markup, booklet.STYLESHEET)
    filler = booklet.fill_to_a_folded_multiple(len(document.pages))
    if filler:
        markup = booklet.build_html(conference, show_qr=False, filler=filler)
        document = lay_out(markup, booklet.STYLESHEET)
    return [page_text(page) for page in document.pages]


def test_the_booklet_can_be_folded(booklet_pages):
    """A saddle-stitched booklet is printed on folded sheets."""
    assert len(booklet_pages) % booklet.SHEET_MULTIPLE == 0


def squashed(text: str) -> str:
    """Drop what a line break can fall on, so wrapping cannot fail a test."""
    return re.sub(r"[\s'\u2019-]+", '', text).replace('\u202f', '\u00a0')


def test_every_talk_has_a_card(booklet_pages, conference):
    laid_out = squashed(' '.join(booklet_pages))
    for event in conference._events.values():
        assert squashed(event.title) in laid_out, event.title


def test_the_booklet_carries_its_annexes(booklet_pages):
    laid_out = ' '.join(booklet_pages)
    for heading in ('Sommaire', 'Le village associatif', 'Salle par salle',
                    'Infos pratiques', 'Nos partenaires',
                    'Rejoindre Toulibre'):
        assert heading in laid_out


def test_the_programme_is_grouped_by_start_time(conference):
    """The hour is the way in, so every talk sits under its own band."""
    for day in conference._days.values():
        slots = booklet.slots_of(day)
        starts = [start for start, _ in slots]
        assert starts == sorted(starts)
        assert len(set(starts)) == len(starts)

        counted = sum(len(events) for _, events in slots)
        expected = sum(len(room.sorted_events())
                       for room in booklet.day_rooms(day))
        assert counted == expected


def test_the_index_covers_every_room(conference):
    markup = booklet.render_room_index(conference)
    for day in conference._days.values():
        for room in booklet.day_rooms(day):
            assert f'>{room._name}<' in markup


def test_filler_rounds_up_to_a_sheet():
    assert booklet.fill_to_a_folded_multiple(48) == 0
    assert booklet.fill_to_a_folded_multiple(47) == 1
    assert booklet.fill_to_a_folded_multiple(45) == 3


# --- all three at once ------------------------------------------------------

def test_a_run_writes_the_three_programme_outputs(tmp_path, conference):
    assert gen.main(['--schedule-file', FIXTURE, '--no-qr',
                     '--no-audience', '--only', 'salles', '--only', 'global',
                     '--only', 'livret', '--output-dir', str(tmp_path)]) == 0
    written = {path.name for path in tmp_path.iterdir()}
    assert written == {name.format(year=conference.year)
                       for name in (posters.OUTPUT, overview.OUTPUT,
                                    booklet.OUTPUT)}


def test_the_file_names_carry_the_edition(tmp_path, conference):
    """A new year must not overwrite the previous one's PDFs."""
    assert gen.main(['--schedule-file', FIXTURE, '--no-qr', '--no-audience',
                     '--only', 'livret', '--output-dir', str(tmp_path)]) == 0
    written = [path.name for path in tmp_path.iterdir()]
    assert written == [f'conference-livret-{conference.year}.pdf']


def test_the_edition_comes_from_the_schedule_not_the_flags(conference):
    """--schedule-file can name any export, so --year must not decide."""
    assert conference.year == 2025


def test_only_builds_what_is_asked(tmp_path, conference):
    assert gen.main(['--schedule-file', FIXTURE, '--no-qr', '--no-audience',
                     '--only', 'global', '--output-dir', str(tmp_path)]) == 0
    assert {path.name for path in tmp_path.iterdir()} == {
        overview.OUTPUT.format(year=conference.year)}


# --- what a newcomer is pointed at ------------------------------------------

@pytest.fixture(autouse=True)
def forget_matched_highlights():
    """find_highlights is cached, so a test changing the picks must clear it."""
    booklet.find_highlights.cache_clear()
    yield
    booklet.find_highlights.cache_clear()


def test_a_highlight_is_matched_to_its_talk(conference, monkeypatch, capsys):
    """The picks are editorial and change every year, so name our own here.

    Stale picks are caught at build time by the warning below, not by a test
    against a frozen fixture.
    """
    monkeypatch.setattr(content, 'HIGHLIGHTS',
                        [('Bienvenue au', 'pourquoi')])
    found = booklet.find_highlights(conference)
    assert len(found) == 1
    assert 'Bienvenue au' in found[0][0].title
    assert 'warning' not in capsys.readouterr().err


def test_an_unmatched_highlight_is_reported(conference, monkeypatch, capsys):
    monkeypatch.setattr(content, 'HIGHLIGHTS',
                        [('pas dans le programme', 'pourquoi')])
    assert booklet.find_highlights(conference) == []
    assert 'no talk matches the highlight' in capsys.readouterr().err


def test_highlights_are_in_chronological_order(conference, monkeypatch):
    monkeypatch.setattr(content, 'HIGHLIGHTS',
                        [('Buffet convivial', 'le soir'),
                         ('Bienvenue au', 'le matin')])
    found = booklet.find_highlights(conference)
    starts = [event._start_datetime for event, _ in found]
    assert len(starts) == 2
    assert starts == sorted(starts)


def test_the_shipped_picks_are_reported_when_they_go_stale(conference,
                                                           capsys):
    """content.HIGHLIGHTS names the live edition, not this fixture."""
    booklet.find_highlights(conference)
    reported = capsys.readouterr().err.count('no talk matches the highlight')
    assert reported == sum(
        1 for fragment, _ in content.HIGHLIGHTS
        if not any(fragment in event.title
                   for event in conference._events.values()))


def test_the_first_time_page_is_there(booklet_pages):
    laid_out = ' '.join(booklet_pages)
    assert content.FIRST_TIME_TITLE in laid_out
    for heading, _ in content.FIRST_TIME:
        assert heading[:20] in laid_out


def test_the_booklet_says_registration_is_required(booklet_pages):
    """The site says "gratuit, inscription obligatoire"; so must the booklet."""
    laid_out = ' '.join(booklet_pages).lower()
    assert 'inscription' in laid_out
    assert 'obligatoire' in laid_out


# --- the speaker index ------------------------------------------------------

def test_every_speaker_is_indexed(conference):
    indexed = {name for name, _ in booklet.speakers_of(conference)}
    expected = {person._name
                for person in conference._persons.values()}
    assert indexed == expected


def test_the_index_is_alphabetical_with_accents_folded(conference):
    names = [name for name, _ in booklet.speakers_of(conference)]
    assert names == sorted(names, key=lambda n: locale.strxfrm(n.upper()))
    assert booklet.initial_of('Étienne Gonnu') == 'E'
    assert booklet.initial_of('Ada') == 'A'
    assert booklet.initial_of('42 crew') == '#'


def test_a_speaker_lists_all_their_talks(conference):
    for name, events in booklet.speakers_of(conference):
        expected = sum(1 for event in conference._events.values()
                       if name in {p._name for p in event._persons.values()})
        assert len(events) == expected, name


# --- black and white printing -----------------------------------------------

def test_a_workshop_is_marked_without_relying_on_colour(conference):
    """The booklet is printed in greyscale, where two tints read the same."""
    workshops = [event for day in conference._days.values()
                 for room in booklet.day_rooms(day)
                 for event in room.sorted_events()
                 if 'workshop' in render.event_classes(event)]
    assert workshops, 'the fixture should hold a workshop'

    for event in workshops:
        card = booklet.render_card(event, show_qr=False)
        assert 'class="kind">Atelier<' in card
        assert 'card workshop' in card


def test_a_talk_carries_no_workshop_marking(conference):
    talks = [event for day in conference._days.values()
             for room in booklet.day_rooms(day)
             for event in room.sorted_events()
             if 'workshop' not in render.event_classes(event)]
    for event in talks:
        assert 'class="kind"' not in booklet.render_card(event, show_qr=False)


def test_the_short_and_long_formats_no_longer_differ_by_tint():
    """Duration is carried by the height of a block, not by a colour."""
    for name in ('styles/posters.css', 'styles/overview.css'):
        with open(os.path.join(ROOT, name), encoding='utf-8') as handle:
            assert 'conference-25min' not in handle.read()

"""The video covers: one 1920x1080 PNG per filmed talk."""

import locale
import os

import pytest
from weasyprint import CSS
from weasyprint.text.fonts import FontConfiguration

import avatars
import covers
import schedule

locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, os.pardir)
FIXTURE = os.path.join(HERE, 'fixtures', 'schedule-2025.xml')


@pytest.fixture(scope='module')
def conference() -> schedule.Conference:
    parsed = schedule.Conference(FIXTURE)
    parsed.parse()
    return parsed


def test_only_what_is_filmed_gets_a_cover(conference):
    events = covers.filmed_events(conference)
    assert events
    assert not any(event._type.lower().startswith('atelier')
                   for event in events)
    assert not any(event.recording_refused for event in events)
    assert any(event.recording_refused
               for event in conference._events.values()), \
        'the fixture should carry a refusal for this test to mean anything'


def test_a_filename_sorts_by_time_and_is_plain_ascii(conference):
    names = [covers.filename(event)
             for event in covers.filmed_events(conference)]
    assert names == sorted(names)
    assert len(set(names)) == len(names)
    assert all(name.isascii() and name.endswith('.png') for name in names)


def test_the_format_drops_its_length():
    event = schedule.Event('1', schedule.Day(None))
    event._type = 'Conférence 55min'
    assert covers.kind(event) == 'Conférence'
    event._type = 'Lightning Talk'
    assert covers.kind(event) == 'Lightning talk'


def test_a_cover_is_a_1920_by_1080_png(conference, tmp_path):
    fonts = FontConfiguration()
    css = CSS(filename=os.path.join(ROOT, covers.STYLESHEET),
              font_config=fonts)
    events = covers.filmed_events(conference)[:2]
    sizes, overflowing, document = covers.fit_titles(conference, events,
                                                     css, fonts)
    assert overflowing == []
    assert all(covers.MIN_TITLE_SIZE <= size <= covers.BASE_TITLE_SIZE
               for size in sizes.values())
    written = covers.write_pngs(document, events, str(tmp_path))
    assert len(written) == 2

    from PIL import Image
    with Image.open(written[0]) as image:
        assert image.size == (covers.WIDTH, covers.HEIGHT)


# --- speaker photos ---------------------------------------------------------

def test_photos_are_keyed_on_the_talk_code():
    speakers = [
        {'name': 'Alice', 'submissions': ['AAA', 'BBB'],
         'avatar_url': 'https://example.org/a.webp'},
        {'name': 'Bob', 'submissions': ['AAA'], 'avatar_url': None},
        {'name': 'Carol', 'submissions': ['AAA'],
         'avatar_url': 'https://example.org/c.webp'},
    ]
    found = avatars.photos_from(speakers)
    assert [name for name, _url in found['AAA']] == ['Alice', 'Carol']
    assert [name for name, _url in found['BBB']] == ['Alice']


def test_photos_follow_the_order_of_the_names():
    event = schedule.Event('1', schedule.Day(None))
    for index, name in enumerate(('Carol', 'Alice')):
        person = schedule.Person(str(index))
        person._name = name
        event._persons[str(index)] = person
    found = [('Alice', 'a'), ('Zoé', 'z'), ('Carol', 'c')]
    assert [name for name, _url in avatars.in_name_order(event, found)] \
        == ['Carol', 'Alice', 'Zoé']


def test_no_photos_is_no_failure(conference, monkeypatch, capsys):
    def offline(year):
        raise OSError('network is unreachable')
    monkeypatch.setattr(avatars, 'fetch', offline)
    assert avatars.gather(conference, 2025, '/nonexistent') == 0
    assert 'go without them' in capsys.readouterr().err

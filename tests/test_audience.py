"""Who each talk is for.

The answer to "Quel est le public visé ?" is a Pretalx custom question, and
no schedule export carries custom answers -- neither the FRAB XML nor
schedule.json. It comes from the submissions API and is joined on the talk
code. That join, and the promise that a failure to reach it never stops a
print run, is what these hold.
"""

import json
import locale
import os

import pytest

import audience
import booklet
import gen
import posters
import schedule

locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')

HERE = os.path.dirname(__file__)
FIXTURE = os.path.join(HERE, 'fixtures', 'schedule-2026.xml')
ANSWERS = os.path.join(HERE, 'fixtures', 'audience-2026.json')


@pytest.fixture
def conference() -> schedule.Conference:
    parsed = schedule.Conference(FIXTURE)
    parsed.parse()
    return parsed


@pytest.fixture
def enriched(conference) -> schedule.Conference:
    audience.gather(conference, 2026, ANSWERS)
    return conference


# --- the join ---------------------------------------------------------------

def test_the_talk_code_comes_out_of_its_url():
    event = schedule.Event('1', schedule.Day(None))
    event._url = 'https://cfp.capitoledulibre.org/cdl-2026/talk/S8VJEU/'
    assert audience.code_of(event) == 'S8VJEU'


def test_an_event_without_a_url_has_no_code():
    event = schedule.Event('1', schedule.Day(None))
    assert audience.code_of(event) is None


def test_every_talk_of_the_fixture_is_matched(enriched):
    missing = [event.title for event in enriched._events.values()
               if not getattr(event, '_audience', None)]
    assert missing == []


# --- picking the right question ---------------------------------------------

def test_the_question_is_found_by_its_identifier():
    payload = [{'code': 'AAAAAA', 'answers': [{
        'answer': 'tout public',
        'question': {'identifier': audience.QUESTION_IDENTIFIER,
                     'question': {'fr': 'libellé qui a changé'}}}]}]
    assert audience.answers_from(payload) == {'AAAAAA': 'tout public'}


def test_the_label_is_the_fallback_when_the_identifier_moves():
    payload = [{'code': 'AAAAAA', 'answers': [{
        'answer': 'débutant·es',
        'question': {'identifier': 'AUTRECHOSE',
                     'question': {'fr': 'Quel est le public visé ?'}}}]}]
    assert audience.answers_from(payload) == {'AAAAAA': 'débutant·es'}


def test_other_questions_are_ignored():
    payload = [{'code': 'AAAAAA', 'answers': [{
        'answer': 'oui',
        'question': {'identifier': 'ZZZZZZ',
                     'question': {'fr': 'Acceptez-vous d’être filmé ?'}}}]}]
    assert audience.answers_from(payload) == {}


def test_a_blank_answer_is_not_an_answer():
    payload = [{'code': 'AAAAAA', 'answers': [{
        'answer': '   ',
        'question': {'identifier': audience.QUESTION_IDENTIFIER,
                     'question': {'fr': 'Quel est le public visé ?'}}}]}]
    assert audience.answers_from(payload) == {}


# --- what reaches the page --------------------------------------------------

def test_the_answer_is_capitalised(conference):
    """Speakers write "tout public" and "Tout public" alike."""
    code = audience.code_of(next(iter(conference._events.values())))
    audience.attach(conference, {code: 'tout public'})
    assert next(iter(conference._events.values()))._audience == 'Tout public'


def test_a_card_says_who_the_talk_is_for(enriched):
    event = next(iter(enriched._events.values()))
    card = booklet.render_card(event, show_qr=False)
    assert 'Pour qui' in card
    assert event._audience[:30] in card


def test_a_door_poster_only_carries_a_short_answer(enriched):
    short = [event for event in enriched._events.values()
             if len(event._audience) <= posters.AUDIENCE_MAX_LENGTH]
    long = [event for event in enriched._events.values()
            if len(event._audience) > posters.AUDIENCE_MAX_LENGTH]
    assert short and long, 'the fixture should hold both'

    for event in short:
        assert 'class="audience"' in posters.render_event(event, show_qr=False)
    for event in long:
        assert 'class="audience"' not in posters.render_event(event,
                                                              show_qr=False)


# --- an enrichment must never stop a print run ------------------------------

def test_a_missing_answers_file_only_warns(conference, capsys):
    assert audience.gather(conference, 2026, '/does/not/exist.json') == 0
    assert 'cannot read the audience answers' in capsys.readouterr().err


def test_a_broken_answers_file_only_warns(conference, tmp_path, capsys):
    broken = tmp_path / 'broken.json'
    broken.write_text('{not json')
    assert audience.gather(conference, 2026, str(broken)) == 0
    assert 'cannot read the audience answers' in capsys.readouterr().err


def test_answers_that_match_nothing_are_reported(conference, capsys):
    assert audience.gather(conference, 2026, ANSWERS) > 0
    capsys.readouterr()
    for event in conference._events.values():
        event._url = ''
    assert audience.gather(conference, 2026, ANSWERS) == 0
    assert 'none of the audience answers matched' in capsys.readouterr().err


def test_the_run_still_produces_everything_without_them(tmp_path):
    assert gen.main(['--schedule-file', FIXTURE, '--no-qr', '--no-audience',
                     '--output-dir', str(tmp_path)]) == 0
    assert len(list(tmp_path.iterdir())) == len(gen.OUTPUTS)


# --- reading the answers from a file ----------------------------------------

def test_a_plain_mapping_is_accepted(tmp_path):
    path = tmp_path / 'audience.json'
    path.write_text(json.dumps({'AAAAAA': ' tout public '}))
    assert audience.load(str(path)) == {'AAAAAA': 'tout public'}


def test_an_api_dump_is_accepted():
    assert len(audience.load(ANSWERS)) == 17


def test_a_door_poster_links_to_the_site_not_the_cfp():
    event = schedule.Event('1', schedule.Day(None))
    event._url = 'https://cfp.capitoledulibre.org/cdl-2026/talk/S8VJEU/'
    assert (posters.site_url(event)
            == 'https://capitoledulibre.org/programme/talk/S8VJEU/')


def test_a_door_poster_keeps_a_url_it_cannot_read_a_code_from():
    event = schedule.Event('1', schedule.Day(None))
    event._url = 'https://example.org/somewhere'
    assert posters.site_url(event) == 'https://example.org/somewhere'

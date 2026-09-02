"""Who each talk is for.

The schedule export does not carry it: "Quel est le public visé ?" is a
Pretalx custom question, and neither the FRAB XML nor schedule.json includes
custom answers. They come from the submissions API instead, which serves them
without a token as long as the question is public, and are joined to the
schedule on the talk code that both carry.

An enrichment must never break a print run, so a fetch that fails is a
warning and the outputs are built without it.
"""

import json
import re
import sys
from urllib.error import URLError
from urllib.request import urlopen

# The question, by its Pretalx identifier. Stable across edits to the wording,
# unlike the label, which is matched only as a fallback.
QUESTION_IDENTIFIER = 'WRQBZB3S'
QUESTION_LABEL = 'public visé'

API_TEMPLATE = ('https://cfp.capitoledulibre.org/api/events/cdl-{year}/'
                'submissions/?expand=answers.question&limit=200')

# A talk's code, as it appears in the URL the schedule export carries.
CODE_IN_URL = re.compile(r'/talk/([A-Z0-9]+)/')


def code_of(event) -> str | None:
    """The Pretalx code for an event, read out of its talk URL."""
    match = CODE_IN_URL.search(getattr(event, '_url', '') or '')
    return match.group(1) if match else None


def _label_of(question) -> str:
    label = question.get('question') if isinstance(question, dict) else ''
    if isinstance(label, dict):
        return ' '.join(str(value) for value in label.values())
    return str(label or '')


def answers_from(submissions: list) -> dict:
    """Map talk code to its audience answer, over a submissions payload."""
    found = {}
    for submission in submissions:
        code = submission.get('code')
        for answer in submission.get('answers') or []:
            question = answer.get('question') or {}
            if not isinstance(question, dict):
                continue
            matches = (question.get('identifier') == QUESTION_IDENTIFIER
                       or QUESTION_LABEL in _label_of(question).lower())
            text = (answer.get('answer') or '').strip()
            if matches and code and text:
                found[code] = text
    return found


def fetch(year: int) -> dict:
    """Every audience answer for an edition, from the submissions API."""
    submissions = []
    page = API_TEMPLATE.format(year=year)
    while page:
        with urlopen(page) as response:
            payload = json.load(response)
        submissions += payload.get('results') or []
        page = payload.get('next')
    return answers_from(submissions)


def load(path: str) -> dict:
    """Audience answers from a local file: either a mapping or an API dump."""
    with open(path, encoding='utf-8') as handle:
        payload = json.load(handle)
    if isinstance(payload, dict) and 'results' in payload:
        return answers_from(payload['results'])
    if isinstance(payload, list):
        return answers_from(payload)
    return {code: str(text).strip() for code, text in payload.items()}


def attach(conference, answers: dict) -> int:
    """Hang each answer on its event. Returns how many found a home."""
    attached = 0
    for event in conference._events.values():
        code = code_of(event)
        text = answers.get(code) if code else None
        if text:
            # Speakers write "tout public" and "Tout public" alike.
            event._audience = text[0].upper() + text[1:]
            attached += 1
    return attached


def gather(conference, year: int, path: str | None) -> int:
    """Find the answers wherever they are, and never fail the run over them."""
    try:
        answers = load(path) if path else fetch(year)
    except (OSError, URLError, ValueError) as error:
        print(f'warning: cannot read the audience answers ({error}); '
              'the outputs will not mention who each talk is for',
              file=sys.stderr)
        return 0

    attached = attach(conference, answers)
    if answers and not attached:
        print('warning: none of the audience answers matched a talk; '
              'has the export stopped carrying talk URLs?', file=sys.stderr)
    return attached

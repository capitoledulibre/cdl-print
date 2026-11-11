"""Speaker photos, for the video covers.

Pretalx keeps an avatar for each speaker who uploaded one, and lists it in
the speakers API along with the codes of their talks. The schedule export
carries neither, so the photos are joined to a talk on that code, the same
way the audience answers are.

Like the audience, they are an enrichment, never a dependency: a speaker
without a photo gets a cover without one, and a fetch that fails warns and
the run goes on. Downloads are kept in a cache folder, so a second run does
not fetch them again.
"""

import json
import os
import sys
from urllib.error import URLError
from urllib.request import urlopen

from audience import code_of

API_TEMPLATE = ('https://cfp.capitoledulibre.org/api/events/cdl-{year}/'
                'speakers/?limit=50')


def photos_from(speakers: list) -> dict:
    """Map talk code to [(speaker name, avatar URL), ...], in API order."""
    found = {}
    for speaker in speakers:
        url = speaker.get('avatar_url')
        if not url:
            continue
        for code in speaker.get('submissions') or []:
            found.setdefault(code, []).append((speaker.get('name', ''), url))
    return found


def fetch(year: int) -> dict:
    speakers = []
    page = API_TEMPLATE.format(year=year)
    while page:
        with urlopen(page, timeout=30) as response:
            payload = json.load(response)
        speakers += payload.get('results') or []
        # Pretalx hands out its next page over plain http.
        page = payload.get('next')
        if page and page.startswith('http://'):
            page = 'https://' + page[len('http://'):]
    return photos_from(speakers)


def download(url: str, cache: str) -> str | None:
    """The local copy of a photo, fetched once."""
    os.makedirs(cache, exist_ok=True)
    path = os.path.join(cache, url.rstrip('/').rsplit('/', 1)[-1])
    if not os.path.exists(path):
        try:
            with urlopen(url, timeout=30) as response:
                data = response.read()
        except (URLError, OSError) as error:
            print(f'warning: could not fetch the photo {url}: {error}',
                  file=sys.stderr)
            return None
        with open(path, 'wb') as handle:
            handle.write(data)
    return path


def in_name_order(event, found: list) -> list:
    """The photos in the order the cover lists the names.

    The API lists speakers in its own order; a speaker it names differently
    from the export goes last rather than being dropped.
    """
    names = [person._name for person in event._persons.values()]

    def rank(pair):
        name = pair[0]
        return names.index(name) if name in names else len(names)

    return sorted(found, key=rank)


def gather(conference, year: int, cache: str) -> int:
    """Hang each talk's speaker photos on it, as local paths.

    Returns how many talks got at least one. Never fails the run.
    """
    try:
        photos = fetch(year)
    except (URLError, OSError, ValueError) as error:
        print(f'warning: could not fetch the speaker photos, the covers go '
              f'without them: {error}', file=sys.stderr)
        return 0

    attached = 0
    for event in conference._events.values():
        code = code_of(event)
        found = in_name_order(event, photos.get(code, []))
        paths = [path for _name, url in found
                 if (path := download(url, cache))]
        if paths:
            event._photos = paths
            attached += 1
    return attached

"""Generate the Capitole du Libre printed matter from the schedule export.

Three outputs come out of the same parsed schedule:

  * the door posters, one A3 sheet per room and per day;
  * the hall poster, one A1 sheet per day showing every room at once;
  * the pocket booklet, A5, with the grid, a card per talk and the annexes.
"""

import argparse
import locale
import os
import sys
from datetime import datetime
from urllib.request import urlopen
from xml.etree import ElementTree

from weasyprint import CSS, HTML
from weasyprint.text.fonts import FontConfiguration

import booklet
import overview
import posters
from schedule import Conference

# --- Configuration ---------------------------------------------------------
#
# Everything that changes from one edition to the next comes from the
# environment or the command line, so that a new year needs no code edit.

YEAR_ENV_VAR = 'CDL_YEAR'
SCHEDULE_URL_TEMPLATE = (
    'https://cfp.capitoledulibre.org/cdl-{year}/schedule/export/schedule.xml')
DEFAULT_LOCALE = 'fr_FR.UTF-8'

# What `--only` accepts, in the order the outputs are built.
OUTPUTS = ('salles', 'global', 'livret')


def default_year() -> int:
    """Conference edition to build unless --year says otherwise.

    The current year, or $CDL_YEAR when set.
    """
    override = os.environ.get(YEAR_ENV_VAR)
    if override:
        try:
            return int(override)
        except ValueError:
            print(f'warning: {YEAR_ENV_VAR}={override!r} is not a year, '
                  'using the current one instead',
                  file=sys.stderr)
    return datetime.now().year


def build_posters(conference, fonts, output, show_qr) -> int:
    css = CSS(filename=posters.STYLESHEET, font_config=fonts)
    sizes, too_dense = posters.fit_rooms(conference, css, fonts,
                                         show_qr=show_qr)
    if too_dense:
        print('error: these rooms do not fit on one sheet even at the '
              f'smallest type size ({posters.MIN_TIMELINE_SIZE}px):',
              file=sys.stderr)
        for room in too_dense:
            print(f'  {room}', file=sys.stderr)
        return 1

    markup = posters.build_html(conference, show_qr=show_qr, sizes=sizes)
    write_pdf(markup, css, fonts, output)
    return 0


def build_overview(conference, fonts, output) -> int:
    css = CSS(filename=overview.STYLESHEET, font_config=fonts)
    write_pdf(overview.build_html(conference), css, fonts, output)
    return 0


def build_booklet(conference, fonts, output, show_qr) -> int:
    """Lay the booklet out twice: once to count, once to fold cleanly.

    The page count is only known after rendering, and a saddle-stitched
    booklet needs a multiple of four, so the note pages at the back absorb
    the difference.
    """
    css = CSS(filename=booklet.STYLESHEET, font_config=fonts)

    markup = booklet.build_html(conference, show_qr=show_qr)
    counted = HTML(string=markup).render(stylesheets=[css], font_config=fonts)
    filler = booklet.fill_to_a_folded_multiple(len(counted.pages))
    if filler:
        markup = booklet.build_html(conference, show_qr=show_qr,
                                    filler=filler)

    write_pdf(markup, css, fonts, output)
    return 0


def write_pdf(markup: str, css: CSS, fonts, output: str):
    try:
        os.remove(output)
    except FileNotFoundError:
        pass
    HTML(string=markup).write_pdf(output, stylesheets=[css],
                                  font_config=fonts)
    print(f'wrote {output}')


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description='Generate the Capitole du Libre printed matter.')
    parser.add_argument(
        '--year', type=int, default=default_year(),
        help=f'conference edition to fetch '
             f'(default: ${YEAR_ENV_VAR}, else the current year)')
    parser.add_argument(
        '--url',
        help='schedule XML URL, overriding the one derived from --year')
    parser.add_argument(
        '--schedule-file',
        help='read the schedule from a local XML export instead of the '
             'network, ignoring --year and --url')
    parser.add_argument(
        '--only', choices=OUTPUTS, action='append',
        help='build only this output; repeatable (default: all three)')
    parser.add_argument(
        '--output-dir', default='.',
        help='directory to write the PDFs into (default: the current one)')
    parser.add_argument(
        '--no-qr', dest='qr', action='store_false',
        help='leave out the QR code linking to each talk page')
    parser.add_argument(
        '--locale', default=DEFAULT_LOCALE,
        help=f'locale used to format dates (default: {DEFAULT_LOCALE})')

    args = parser.parse_args(argv)
    if args.url is None:
        args.url = SCHEDULE_URL_TEMPLATE.format(year=args.year)
    if not args.only:
        args.only = list(OUTPUTS)
    return args


def load_conference(args) -> Conference:
    """Parse the schedule named by the command line.

    Raises OSError if it cannot be reached and ElementTree.ParseError if what
    comes back is not the export we expect.
    """
    source = args.schedule_file if args.schedule_file else urlopen(args.url)
    conference = Conference(source)
    conference.parse()
    return conference


def main(argv=None) -> int:
    args = parse_args(argv)

    try:
        conference = load_conference(args)
    except OSError as error:
        target = args.schedule_file or args.url
        print(f'error: cannot read the schedule at {target}: {error}',
              file=sys.stderr)
        return 1
    except ElementTree.ParseError as error:
        print(f'error: the schedule is not valid XML: {error}',
              file=sys.stderr)
        return 1

    try:
        locale.setlocale(locale.LC_ALL, args.locale)
    except locale.Error:
        print(f'warning: locale {args.locale} is unavailable, '
              'dates will not be localised',
              file=sys.stderr)

    fonts = FontConfiguration()

    def path(name):
        return os.path.join(args.output_dir,
                            name.format(year=conference.year))

    if 'salles' in args.only:
        if build_posters(conference, fonts, path(posters.OUTPUT), args.qr):
            return 1
    if 'global' in args.only:
        if build_overview(conference, fonts, path(overview.OUTPUT)):
            return 1
    if 'livret' in args.only:
        if build_booklet(conference, fonts, path(booklet.OUTPUT), args.qr):
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

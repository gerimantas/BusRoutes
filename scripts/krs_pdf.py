"""
Reads the route 106 timetable PDFs that Kauno rajono savivaldybė publishes on krs.lt.

The municipality publishes one PDF per day type, each named with the date it takes
effect: internetas-106-dd-nuo-2026-10-01.pdf (workdays), -š- (Saturday), -s-
(Sunday), -šs- (both weekend days). Older PDFs stay on the page next to newer ones,
so the one in force on a date is the newest whose start date has passed.

The PDFs list local route 106 trips only; intercity trips are not in them.

Each PDF holds two tables, one per direction. Every table has a "Kauno autobusų
stotis" row and a "Juragiai" row with one time per trip. Column for column, the
stop with the earlier time is where that trip departs from. The weekend PDF prints
both tables side by side on one line, which the same rule handles.
"""

import datetime as dt
import io
import re
import urllib.parse
import urllib.request

PAGE = 'https://www.krs.lt/gyventojams/viesasis-transportas/priemiestiniai-autobusu-marsrutai/'

# PDF day type -> the check labels it covers (WD, SAT, SUN as in check_schedule.py)
KINDS = {'dd': ('WD',), 'š': ('SAT',), 's': ('SUN',), 'šs': ('SAT', 'SUN')}

HREF = re.compile(r'href="([^"]*internetas-106-[^"]*\.pdf)"', re.I)
NAME = re.compile(r'internetas-106-(dd|šs|š|s)-nuo-(\d{4})-(\d{2})-(\d{2})\.pdf$', re.I)
CLOCK = re.compile(r'\b\d{2}:\d{2}\b')

KAUNAS_ROW = 'Kauno autobusų stotis'
JURAGIAI_ROW = 'Juragiai'


def fetch(url):
    """Return the bytes at url. Non-ASCII characters in the path are encoded."""
    parts = urllib.parse.urlsplit(url)
    url = parts._replace(path=urllib.parse.quote(urllib.parse.unquote(parts.path))).geturl()
    req = urllib.request.Request(url, headers={'User-Agent': 'BusRoutes schedule watch'})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def list_pdfs(html):
    """Return [{kind, start, url}] for every route 106 PDF linked from the page."""
    out, seen = [], set()
    for href in HREF.findall(html):
        path = urllib.parse.unquote(href)
        m = NAME.search(path)
        if not m or path in seen:
            continue
        seen.add(path)
        y, mo, d = (int(x) for x in m.group(2, 3, 4))
        out.append(dict(kind=m.group(1).lower(), start=dt.date(y, mo, d),
                        url=urllib.parse.urljoin(PAGE, path)))
    return out


def pdf_for(pdfs, label, date):
    """Return the PDF in force for a WD/SAT/SUN date, or None if none has started."""
    started = [p for p in pdfs if label in KINDS[p['kind']] and p['start'] <= date]
    return max(started, key=lambda p: p['start']) if started else None


def parse_text(text):
    """Return {'kaunas-juragiai': [departures], 'juragiai-kaunas': [departures]}.

    Raises ValueError when the two stop rows do not pair up — a layout this code
    does not understand must fail the check, not pass it with half the trips.
    """
    rows = {KAUNAS_ROW: [], JURAGIAI_ROW: []}
    for line in text.splitlines():
        times = CLOCK.findall(line)
        label = ' '.join(CLOCK.sub(' ', line).split())
        if times and label in rows:
            rows[label].append(times)

    kaunas, juragiai = rows[KAUNAS_ROW], rows[JURAGIAI_ROW]
    if not kaunas or len(kaunas) != len(juragiai):
        raise ValueError(f'expected paired stop rows, got {len(kaunas)} Kaunas '
                         f'and {len(juragiai)} Juragiai')

    out = {'kaunas-juragiai': [], 'juragiai-kaunas': []}
    for k_row, j_row in zip(kaunas, juragiai):
        if len(k_row) != len(j_row):
            raise ValueError(f'row lengths differ: {k_row} vs {j_row}')
        for k, j in zip(k_row, j_row):
            if k < j:
                out['kaunas-juragiai'].append(k)
            else:
                out['juragiai-kaunas'].append(j)
    return {direction: sorted(times) for direction, times in out.items()}


def read_pdf(data):
    """Return parse_text() of a PDF given as bytes."""
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    text = '\n'.join(p.extract_text(extraction_mode='layout') for p in reader.pages)
    return parse_text(text)

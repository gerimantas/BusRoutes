"""
Parses firecrawl-scraped autobusubilietai.lt search pages into a trip table.

Why this exists: the search page renders round-hour markers (05:00, 06:00, 08:00 ...)
that look like departures but carry no route, no carrier and no price. The older
Playwright scraper collected them as real trips, which put ~16 non-existent intercity
departures into the app. A trip is only real if its card contains a route line ending
in "Reiso tvarkaraštis". Everything else is discarded here.

Usage:
    python scripts/parse_firecrawl.py <workday.md> <saturday.md> <sunday.md>

Each argument is a firecrawl `scrape --only-main-content` output for one date.
Output is a table with per-day presence flags, so periodicity is read off directly:
    x x x -> ALL_DAYS      x . . -> WORKDAYS      . x x -> WEEKEND
"""

import io
import re
import sys

# Departure line as firecrawl renders it: **05:00** \- 05:34
TIME = re.compile(r'^\*\*(\d{2}:\d{2})\*\* \\- (\d{2}:\d{2})$')


def parse(path):
    """Return {(departure, route): record} for every real trip card in the page."""
    lines = [l.rstrip('\n') for l in io.open(path, encoding='utf-8')]
    trips = {}
    for i, line in enumerate(lines):
        m = TIME.match(line.strip())
        if not m:
            continue
        dep, arr = m.groups()
        window = [x.strip() for x in lines[i + 1:i + 12] if x.strip()]
        route = carrier = price = None
        for w in window:
            if 'Reiso tvarkara' in w:
                route = w.replace('Reiso tvarkaraštis', '').strip()
            elif w.endswith('€'):
                price = w
            elif route and not carrier and 'Trukm' not in w and w != 'Pirkti':
                carrier = re.split(r'!\[', w)[0].strip()
        if not route:
            continue  # round-hour marker or collapsed duplicate card — not a trip
        trips[(dep, route)] = dict(dep=dep, arr=arr, route=route,
                                   carrier=carrier or '?', price=price or '?')
    return trips


def main():
    if len(sys.argv) != 4:
        print(__doc__.strip())
        sys.exit(2)

    data = dict(zip(['WD', 'SAT', 'SUN'], (parse(p) for p in sys.argv[1:4])))
    for label, trips in data.items():
        print(f"{label}: {len(trips)} trips")

    keys = sorted(set().union(*[set(d) for d in data.values()]))
    print(f"\n{'DEP':<7}{'ARR':<7}{'W':<3}{'S':<3}{'N':<3}{'PRICE':<9}{'CARRIER':<15}ROUTE")
    print('-' * 112)
    for key in keys:
        rec = next(d[key] for d in data.values() if key in d)
        flags = ['x' if key in data[k] else '.' for k in ('WD', 'SAT', 'SUN')]
        print(f"{rec['dep']:<7}{rec['arr']:<7}"
              f"{flags[0]:<3}{flags[1]:<3}{flags[2]:<3}"
              f"{rec['price']:<9}{rec['carrier'][:14]:<15}{rec['route'][:48]}")


if __name__ == '__main__':
    main()

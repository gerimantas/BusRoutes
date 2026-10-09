"""
Drafts the app update for a timetable change check_schedule.py found.

Reads the --json report check_schedule.py wrote, rebuilds the data arrays of
paper/grafikai.html from the search results it scraped, and edits the app, the
two schedule records and the service worker cache in place. The workflow commits
the result to a branch and opens a pull request; merging it publishes the update.
Nothing here commits, pushes or merges.

It drafts only from data it can trust, and refuses otherwise:
- both directions were scraped, and the week after gives the same timetable
  (a partial scrape shows up as a change that does not repeat);
- every trip runs on workdays, weekends or every day — the three periodicities;
- each direction keeps its 5 intercity trips (a different count has always
  meant a bad scrape, never a new timetable);
- the app carries no switch still to come.

The search shows a new timetable for future dates before it starts, so the
start date is searched for day by day from tomorrow: the first day the search
shows the new timetable, or the krs.lt PDF date when one falls between that day
and the last day still showing the old one. The draft keeps the current arrays
as *Before with SWITCH_DATE, and the app switches on the day by itself.

Exit codes:
    0 - drafted; --body holds the pull request text
    2 - the report holds no change to draft
    3 - refused; --body holds the reason

Usage:
    python scripts/draft_update.py diff.json --body pr.md [--issue N] [--diff-id ID]
"""

import argparse
import datetime as dt
import json
import os
import re
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_schedule as cs  # noqa: E402
from parse_firecrawl import parse  # noqa: E402

DIRECTIONS = {
    'kaunas-juragiai': dict(array='dataKaunas', title='Kaunas → Juragiai',
                            platforms=('5', '12'),
                            totals=('5 aikštelė', '12 aikštelė'),
                            record='paper/kaunas-juragiai_grafikas.md'),
    'juragiai-kaunas': dict(array='dataJurginiskai', title='Juragiai → Kaunas',
                            platforms=('106', 'tm'),
                            totals=('106', 'tm'),
                            record='paper/juragiai-kaunas_grafikas.md'),
}
INTERCITY_TRIPS = 5      # each way; stable across every refresh so far
CONFIRM_WEEKS = 1        # the same timetable must come back this many weeks later

CODE = {'WORKDAYS': '12345', 'WEEKEND': 'ŠS', 'ALL_DAYS': '1234567'}
LABELS = ('WD', 'SAT', 'SUN')
# Days a route variant runs on, as the records write them.
SPAN = {frozenset({'WD'}): 'Pr–Pn', frozenset({'SAT', 'SUN'}): 'Š–S',
        frozenset({'SAT'}): 'Š', frozenset({'SUN'}): 'S',
        frozenset({'WD', 'SAT'}): 'Pr–Š', frozenset({'WD', 'SUN'}): 'Pr–Pn, S',
        frozenset(LABELS): 'Pr–S'}
FOLD = str.maketrans('ąčęėįšųūžĄČĘĖĮŠŲŪŽ–', 'aceeisuuzACEEISUUZ-')

ENTRY = re.compile(r'^\s*\["(\d{2}:\d{2})",\s*(WORKDAYS|WEEKEND|ALL_DAYS),\s*"([^"]+)"\],?'
                   r'\s*(?://\s*(.*))?$')

SWITCH_BLOCK = re.compile(r'// Timetable in force until SWITCH_DATE.*?'
                          r'const dataJurginiskaiBefore = \[\n.*?\n\];\n\n', re.S)
PRECALC = 'precalculateTripMinutes(dataJurginiskai);\n'
PRECALC_BEFORE = ('precalculateTripMinutes(dataKaunasBefore);\n'
                  'precalculateTripMinutes(dataJurginiskaiBefore);\n')
RENDER_NOW = ('  renderList(dataKaunas, "list-kaunas", now);\n'
              '  renderList(dataJurginiskai, "list-jurginiskai", now);\n')
RENDER_SWITCH = ('  const beforeSwitch = now < SWITCH_DATE;\n'
                 '  renderList(beforeSwitch ? dataKaunasBefore : dataKaunas, "list-kaunas", now);\n'
                 '  renderList(beforeSwitch ? dataJurginiskaiBefore : dataJurginiskai, '
                 '"list-jurginiskai", now);\n')


class Refused(Exception):
    """The data cannot be trusted to draft from; the message says why."""


# --- the timetable ------------------------------------------------------------

def day_label(date):
    return {5: 'SAT', 6: 'SUN'}.get(date.weekday(), 'WD')


def read_array(html, name):
    """Return [(departure, periodicity, platform, comment)] for one data array."""
    m = re.search(r'const %s = \[\n(.*?)\n\];' % name, html, re.S)
    if not m:
        raise Refused(f'the app has no {name} array where expected')
    return [(e.group(1), e.group(2), e.group(3), (e.group(4) or '').strip())
            for e in map(ENTRY.match, m.group(1).split('\n')) if e]


def by_departure(days):
    """{departure: {route: dict(labels, arr, price)}} from {label: {date, trips}}."""
    out = {}
    for label, day in days.items():
        for dep, arr, route, price in day['trips']:
            rec = out.setdefault(dep, {}).setdefault(route, dict(labels=set(), arr=arr,
                                                                 price=price))
            rec['labels'].add(label)
    return out


def variants(routes):
    """Route variants of one departure, the one running on workdays first."""
    return sorted(routes.items(), key=lambda kv: min(LABELS.index(l) for l in kv[1]['labels']))


def short_route(route):
    """The comment form of a route: Kaunas and Jonučiai dropped, ASCII only."""
    return '-'.join(s for s in route.split('-') if s not in ('Kaunas', 'Jonučiai')).translate(FOLD)


def describe(routes, intercity):
    """The comment for a new array entry, in the style of the existing ones."""
    if len(routes) == 1:
        text = short_route(next(iter(routes)))
    else:
        text = ' / '.join(f"{short_route(r)} ({SPAN[frozenset(v['labels'])].translate(FOLD)})"
                          for r, v in variants(routes))
    return f'tarpmiestinis, {text}' if intercity else text


def timetable(direction, days, current):
    """Return the new [(departure, periodicity, platform, comment)], by departure.

    current is the app's array for the direction: a trip that keeps its days and
    platform keeps its hand-written comment.
    """
    local, intercity = DIRECTIONS[direction]['platforms']
    per = cs.periodicity({label: [(t[0], t[2]) for t in day['trips']]
                          for label, day in days.items()})
    mixed = sorted(d for d, p in per.items() if p == 'MIXED')
    if mixed:
        raise Refused(f"{DIRECTIONS[direction]['title']}: {', '.join(mixed)} run on a mix of "
                      "days that is none of workdays, weekends or every day")

    trips, known = by_departure(days), {e[0]: e for e in current}
    out = []
    for dep in sorted(per):
        # Every intercity service serving Juragiai runs via Marijampolė; route 106 never does.
        platform = intercity if any('Marijampol' in r for r in trips[dep]) else local
        old = known.get(dep)
        comment = (old[3] if old and old[1:3] == (per[dep], platform)
                   else describe(trips[dep], platform == intercity))
        out.append((dep, per[dep], platform, comment))

    count = sum(1 for e in out if e[2] == intercity)
    if count != INTERCITY_TRIPS:
        raise Refused(f"{DIRECTIONS[direction]['title']}: {count} intercity trips where "
                      f"{INTERCITY_TRIPS} have always run — more likely a bad scrape than a "
                      "new timetable")
    return out


def runs_on(entries, label):
    return {e[0] for e in entries if e[1] in cs.RUNS_ON[label]}


def classify(seen, old, new):
    """'old', 'new', 'same' (both agree on this day) or 'unknown' (neither)."""
    if seen == old and seen == new:
        return 'same'
    return 'old' if seen == old else 'new' if seen == new else 'unknown'


def start_window(direction, old, new, known, scrape_day, today, last, log):
    """Return (lo, hi): the new timetable starts on some day from lo to hi.

    Walks the days from tomorrow: hi is the first day the search shows the new
    timetable in full, lo the day after the last one still showing the old one
    (None when no day did). Days near today often come back incomplete; they
    match neither and say nothing.
    """
    last_old, day = None, today + dt.timedelta(days=1)
    while day <= last:
        label = day_label(day)
        if day in known:
            seen = known[day]
        else:
            trips = scrape_day(direction, day)
            seen = None if trips is None else {t[0] for t in trips}
        kind = 'unknown' if seen is None else classify(seen, runs_on(old, label),
                                                       runs_on(new, label))
        log(f'  {direction} {day} ({label}): {kind}')
        if kind == 'old':
            last_old = day
        elif kind == 'new':
            return (last_old + dt.timedelta(days=1) if last_old else None), day
        day += dt.timedelta(days=1)
    raise Refused(f"{DIRECTIONS[direction]['title']}: no day up to {last} shows the new "
                  "timetable in full")


def krs_starts(report):
    """Start dates of the krs.lt PDFs the check read."""
    results = (report.get('krs.lt') or {}).get('results') or []
    return sorted({dt.date.fromisoformat(m.group(1)) for r in results
                   for m in [re.search(r'from (\d{4}-\d{2}-\d{2})', r['pdf'])] if m})


# --- the files ----------------------------------------------------------------

def entry_text(e):
    return f'["{e[0]}", {e[1] + ",":<9} "{e[2]}"],'


def array_text(entries):
    width = max(len(entry_text(e)) for e in entries) + 3
    return '\n'.join(f'  {entry_text(e):<{width}}// {e[3]}' if e[3] else f'  {entry_text(e)}'
                     for e in entries)


def edit_app(html, new, switch):
    """Return the app with new arrays in force from switch, the current ones before it.

    new maps an array name to its entries; arrays not in it stay as they are.
    An earlier switch, already passed, is removed.
    """
    def block(name):
        return re.search(r'const %s = \[\n(.*?)\n\];' % name, html, re.S).group(1)

    current = {cfg['array']: block(cfg['array']) for cfg in DIRECTIONS.values()}
    if 'const SWITCH_DATE' in html:
        html, n = SWITCH_BLOCK.subn('', html, count=1)
        if not n or PRECALC_BEFORE not in html or RENDER_SWITCH not in html:
            raise Refused('the app carries a SWITCH_DATE this script cannot remove')
        html = html.replace(PRECALC_BEFORE, '').replace(RENDER_SWITCH, RENDER_NOW)

    for name, entries in new.items():
        html = html.replace(f'const {name} = [\n{current[name]}\n];',
                            f'const {name} = [\n{array_text(entries)}\n];', 1)

    if not all(s in html for s in ('const dataKaunas = [\n', PRECALC, RENDER_NOW)):
        raise Refused('the app no longer has the layout this script edits')
    js_month = f'{switch.year}, {switch.month - 1}, {switch.day}'
    before = ''.join(f'const {name}Before = [\n{text}\n];\n\n' for name, text in current.items())
    html = html.replace('const dataKaunas = [\n',
                        '// Timetable in force until SWITCH_DATE; the arrays below it apply '
                        'from that date.\n'
                        '// Delete the *Before arrays and SWITCH_DATE at the next timetable '
                        'refresh.\n'
                        f'const SWITCH_DATE = new Date({js_month});  // {switch} 00:00 local time\n\n'
                        + before + 'const dataKaunas = [\n', 1)
    html = html.replace(PRECALC, PRECALC + PRECALC_BEFORE, 1)
    return html.replace(RENDER_NOW, RENDER_SWITCH, 1)


def bump_cache(sw):
    m = re.search(r"tvarkarastis-v(\d+)", sw)
    if not m:
        raise Refused('sw.js has no tvarkarastis-vNN cache name to bump')
    return sw.replace(m.group(0), f'tvarkarastis-v{int(m.group(1)) + 1}', 1)


def lt_count(n, one, few, many):
    """Lithuanian noun form for a count: 1 reisas, 2 reisai, 10 reisų."""
    if n % 10 == 1 and n % 100 != 11:
        return f'{n} {one}'
    if 2 <= n % 10 <= 9 and not 12 <= n % 100 <= 19:
        return f'{n} {few}'
    return f'{n} {many}'


def record_row(entry, routes, width):
    dep, per, platform, _ = entry
    vs = variants(routes)
    route = (vs[0][0] if len(vs) == 1 else
             ' / '.join(f"{r} ({SPAN[frozenset(v['labels'])]})" for r, v in vs))
    price = ' / '.join(dict.fromkeys(v['price'] for _, v in vs))
    return (f"| {dep} | {vs[0][1]['arr']} | {CODE[per]:<7} | {platform:<{width}} "
            f"| {route} | {price} |")


def edit_record(text, direction, entries, days, start, checked, provenance):
    """Return the schedule record rewritten for the new timetable.

    A trip that keeps its days and platform keeps its hand-written row; the
    others are written from the scrape.
    """
    cfg = DIRECTIONS[direction]
    lines = text.split('\n')
    rows = [i for i, l in enumerate(lines) if re.match(r'^\| \d{2}:\d{2} \|', l)]
    if not rows:
        raise Refused(f"{cfg['record']} has no timetable rows")
    kept = {}
    for i in rows:
        cells = [c.strip() for c in lines[i].strip('|').split('|')]
        kept[(cells[0], cells[2], cells[3])] = lines[i]
    trips = by_departure(days)
    width = max(len(p) for p in cfg['platforms'])
    new_rows = [kept.get((e[0], CODE[e[1]], e[2])) or record_row(e, trips[e[0]], width)
                for e in entries]
    lines[rows[0]:rows[-1] + 1] = new_rows

    head = next((i for i, l in enumerate(lines) if l.startswith('Periodiškumas:')), None)
    if head is None:
        raise Refused(f"{cfg['record']} has no 'Periodiškumas:' line")
    lines[2:head] = provenance + ['']
    lines[0] = re.sub(r'\(galioja nuo [\d-]+, patikrinta [\d-]+\)',
                      f'(galioja nuo {start}, patikrinta {checked})', lines[0])

    local, intercity = cfg['platforms']
    n_local = sum(1 for e in entries if e[2] == local)
    n_inter = len(entries) - n_local
    total = (f"**Iš viso:** {lt_count(len(entries), 'reisas', 'reisai', 'reisų')} — "
             f"{lt_count(n_local, 'vietinis', 'vietiniai', 'vietinių')} ({cfg['totals'][0]}) + "
             f"{lt_count(n_inter, 'tarpmiestinis', 'tarpmiestiniai', 'tarpmiestinių')} "
             f"({cfg['totals'][1]})")
    return '\n'.join(total if l.startswith('**Iš viso:**') else l for l in lines)


# --- the draft ----------------------------------------------------------------

def draft(report, today, scrape_day, root=cs.ROOT, log=print, issue=None, diff_id=None):
    """Return ({relative path: new text}, pull request body). Raises Refused."""
    changed = [d for d in DIRECTIONS if report.get(d)
               and (report[d]['added'] or report[d]['removed'] or report[d]['changed'])]
    missing = [d for d in DIRECTIONS if not report.get(d)]
    if missing:
        raise Refused(f"{', '.join(missing)} could not be scraped, so the check is incomplete")
    if report.get('switch') and dt.date.fromisoformat(report['switch']) > today:
        raise Refused(f"the app already carries a timetable that starts on {report['switch']}; "
                      "two pending timetables need a person")

    def read(rel):
        with open(os.path.join(root, rel), encoding='utf-8', newline='') as fh:
            return fh.read()

    html = read('paper/grafikai.html')
    dates = {label: dt.date.fromisoformat(d) for label, d in report['dates'].items()}

    new, windows = {}, {}
    for direction in changed:
        days = report[direction]['days']
        current = read_array(html, DIRECTIONS[direction]['array'])
        new[direction] = timetable(direction, days, current)

        # A scrape that missed trips does not miss the same ones a week later.
        for week in range(1, CONFIRM_WEEKS + 1):
            later = {}
            for label, date in dates.items():
                date += dt.timedelta(weeks=week)
                trips = scrape_day(direction, date)
                if not trips:
                    raise Refused(f"{DIRECTIONS[direction]['title']}: {date} could not be "
                                  "scraped to confirm the change")
                later[label] = dict(date=str(date), trips=trips)
            again = timetable(direction, later, current)
            if [e[:3] for e in again] != [e[:3] for e in new[direction]]:
                raise Refused(f"{DIRECTIONS[direction]['title']}: the week from "
                              f"{min(dates.values()) + dt.timedelta(weeks=week)} shows a "
                              "different timetable than the week checked")

        known = {dt.date.fromisoformat(day['date']): {t[0] for t in day['trips']}
                 for day in days.values()}
        windows[direction] = start_window(direction, current, new[direction], known,
                                          scrape_day, today, max(dates.values()), log)

    lo = max((w[0] for w in windows.values() if w[0]), default=None)
    hi = min(w[1] for w in windows.values())
    if lo and lo > hi:
        raise Refused(f'the two directions disagree on when the new timetable starts '
                      f'({", ".join(f"{d}: {w[0]}…{w[1]}" for d, w in windows.items())})')
    pdf = [d for d in krs_starts(report) if (lo or today + dt.timedelta(days=1)) <= d <= hi]
    start = pdf[-1] if pdf else hi

    files = {'paper/grafikai.html': edit_app(
        html, {DIRECTIONS[d]['array']: new[d] for d in changed}, start)}
    files['sw.js'] = bump_cache(read('sw.js'))
    provenance = [
        'Source: `autobusubilietai.lt` search, scraped by Schedule Watch for '
        + ', '.join(f'{label} {date}' for label, date in dates.items())
        + f' and the week after ({today}).',
        f'Start date: {start}, {how_started(lo, hi, pdf)}.',
        'Not cross-checked against a photo.',
    ]
    for direction in changed:
        rel = DIRECTIONS[direction]['record']
        files[rel] = edit_record(read(rel), direction, new[direction],
                                 report[direction]['days'], start, today, provenance)
    return files, body(report, changed, new, start, lo, hi, pdf, dates, issue, diff_id)


def how_started(lo, hi, pdf):
    since = (f'the search still showed the old one on {lo - dt.timedelta(days=1)}' if lo
             else 'no earlier day showed the old one in full, so it may have started sooner')
    if pdf:
        return f'the date the krs.lt PDF names; the search first shows it on {hi} and {since}'
    return f'the first day the search shows it ({since}); no krs.lt PDF names it yet'


def body(report, changed, new, start, lo, hi, pdf, dates, issue, diff_id):
    out = [f"Timetable update drafted by Schedule Watch from autobusubilietai.lt."
           + (f" Closes #{issue}." if issue else ''), '',
           f"**Starts {start}** — {how_started(lo, hi, pdf)}.", '',
           'The app keeps the current timetable until that day and switches by itself, '
           'so this can be merged any time before it.', '']
    for direction in changed:
        r = report[direction]
        trips = by_departure(r['days'])
        per = {e[0]: e[1] for e in new[direction]}
        out += [f"### {DIRECTIONS[direction]['title']}", '',
                '| | Time | Days | Route |', '|---|---|---|---|']
        out += [f"| new | {t} | {CODE[per[t]]} | {' / '.join(trips[t])} |" for t in r['added']]
        out += [f"| gone | {t} | | |" for t in r['removed']]
        out += [f"| days changed | {c['time']} | {CODE[c['was']]} → {CODE[c['now']]} "
                f"| {' / '.join(trips[c['time']])} |" for c in r['changed']]
        out += ['', f"{len(new[direction])} trips after the change.", '']
    week2 = ', '.join(str(d + dt.timedelta(weeks=1)) for d in dates.values())
    krs = (report.get('krs.lt') or {}).get('result', 'unknown')
    out += ['**Checks passed:** the same timetable a week later '
            f'({week2}); {INTERCITY_TRIPS} intercity trips each way; every trip runs on '
            'workdays, weekends or every day; the app script and the tests pass. '
            f"krs.lt PDFs: {cs.SECONDARY.get(krs, krs)}.", '',
            'Merging publishes the app within a minute; the watcher then checks it again.']
    if diff_id:
        out += ['', f'<!-- diff:{diff_id} -->']
    return '\n'.join(out) + '\n'


def scraper(workdir):
    """scrape_day(direction, date) -> [[dep, arr, route, price]], or None on failure."""
    def scrape_day(direction, date):
        path = cs.scrape(cs.ROUTES[direction]['url'], date, workdir, f'{direction}-{date}')
        return None if path is None else [[r['dep'], r['arr'], r['route'], r['price']]
                                          for r in parse(path).values()]
    return scrape_day


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('report', nargs='?', help='the --json report check_schedule.py wrote')
    ap.add_argument('--body', help='where to write the pull request text')
    ap.add_argument('--issue', help='the issue the pull request closes')
    ap.add_argument('--diff-id', help='marker the workflow uses to tell drafts apart')
    ap.add_argument('--extract-js', metavar='PATH',
                    help="only write the app's script to PATH, for `node --check`")
    args = ap.parse_args(argv)

    if args.extract_js:
        with open(cs.APP, encoding='utf-8') as fh:
            script = re.search(r'<script>(.*?)</script>', fh.read(), re.S).group(1)
        with open(args.extract_js, 'w', encoding='utf-8') as fh:
            fh.write(script)
        return 0
    if not (args.report and args.body):
        ap.error('a report and --body are required')

    with open(args.report, encoding='utf-8') as fh:
        report = json.load(fh)
    if not any(report.get(d) and (report[d]['added'] or report[d]['removed']
                                  or report[d]['changed']) for d in DIRECTIONS):
        print('No change in the report — nothing to draft.')
        return 2

    try:
        with tempfile.TemporaryDirectory() as workdir:
            files, text = draft(report, dt.date.today(), scraper(workdir),
                                issue=args.issue, diff_id=args.diff_id)
    except Refused as exc:
        print(f'Not drafted: {exc}')
        with open(args.body, 'w', encoding='utf-8') as fh:
            fh.write(f'{exc}\n')
        return 3

    for rel, text_ in files.items():
        with open(os.path.join(cs.ROOT, rel), 'w', encoding='utf-8', newline='') as fh:
            fh.write(text_)
        print(f'wrote {rel}')
    with open(args.body, 'w', encoding='utf-8') as fh:
        fh.write(text)
    return 0


if __name__ == '__main__':
    sys.exit(main())

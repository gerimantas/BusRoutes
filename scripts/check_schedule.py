"""
Checks the live timetable against what the app currently ships.

Reads the departure/periodicity pairs out of paper/grafikai.html and compares them
with two sources, in order of priority:

1. autobusubilietai.lt search results for a workday, a Saturday and a Sunday —
   every trip, intercity included, and the first place a new timetable shows up.
   The primary source: it alone sets the exit code, and with it the status the
   app shows riders.
2. the route 106 PDFs on krs.lt — the municipality's own timetable, local trips
   only, each named with the date it takes effect (see krs_pdf.py). The
   secondary source: its result (ok, changed, failed, skipped) goes into the
   --json report as krs.lt.result, and the workflow files its own issue for it.

Exit codes (primary source only):
    0 - no change
    1 - the search differs from the app
    2 - a direction could not be checked, and the other does not differ

Requires the `firecrawl` CLI on PATH, FIRECRAWL_API_KEY in the environment, and pypdf.

Usage:
    python scripts/check_schedule.py                 # human-readable report
    python scripts/check_schedule.py --json out.json # machine-readable diff too
"""

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import krs_pdf  # noqa: E402
from parse_firecrawl import parse  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, 'paper', 'grafikai.html')

RETRIES = 3    # attempts per scrape when the API rate-limits us
BACKOFF = 20   # seconds to wait after a rate-limit refusal
PACE = 7       # seconds between successful scrapes, to stay under ~10/min
LEAD = 3       # days ahead of today the checked week starts; see next_dates()

ROUTES = {
    'kaunas-juragiai': dict(
        array='dataKaunas',
        url=('https://www.autobusubilietai.lt/search?departureTime=00:00'
             '&departureDate={date}&from=2408-1&fromStop=Kaunas'
             '&to=3-1,3-2&toStop=Juragiai'),
    ),
    'juragiai-kaunas': dict(
        array='dataJurginiskai',
        url=('https://www.autobusubilietai.lt/search?departureTime=00:00'
             '&departureDate={date}&from=3-1,3-2&fromStop=Juragiai'
             '&to=2408-1&toStop=Kaunas'),
    ),
}

TRIP = re.compile(r'\["(\d{2}:\d{2})",\s*(WORKDAYS|WEEKEND|ALL_DAYS),\s*"([^"]+)"\]')

LOCAL = ('5', '106')   # platforms of route 106 trips; '12' and 'tm' are intercity
RUNS_ON = {'WD': ('WORKDAYS', 'ALL_DAYS'),
           'SAT': ('WEEKEND', 'ALL_DAYS'),
           'SUN': ('WEEKEND', 'ALL_DAYS')}
WEEKDAYS = {'WD': (0, 1, 2, 3, 4), 'SAT': (5,), 'SUN': (6,)}


def app_schedule(array_name, local_only=False):
    """Return {departure: periodicity} for one data array in grafikai.html."""
    with open(APP, encoding='utf-8') as fh:
        html = fh.read()
    start = html.index(f'const {array_name} = [')
    end = html.index('];', start)
    return {m.group(1): m.group(2) for m in TRIP.finditer(html[start:end])
            if not local_only or m.group(3) in LOCAL}


def switch_date():
    """Return the app's SWITCH_DATE as a date, or None when it has none.

    `new Date(2026, 9, 1)` in JS: the month is zero-based.
    """
    with open(APP, encoding='utf-8') as fh:
        m = re.search(r'const SWITCH_DATE = new Date\((\d{4}),\s*(\d{1,2}),\s*(\d{1,2})\)', fh.read())
    return dt.date(int(m.group(1)), int(m.group(2)) + 1, int(m.group(3))) if m else None


def next_dates(today=None, switch=None):
    """A Thursday, Saturday and Sunday starting at least LEAD days ahead.

    The search returns incomplete lists for the next day or two (2026-09-27, the
    day after a check, listed no route 106 trips at all), which the old
    tomorrow-onwards window reported as a timetable change.

    When the app carries a dated switch, all three dates must fall on one side
    of it — the comparison is against one timetable. A switch inside the
    window moves the window to start on it.
    """
    today = today or dt.date.today()
    start = today + dt.timedelta(days=LEAD)
    if switch and start < switch <= start + dt.timedelta(days=7):
        start = switch
    out = {}
    for label, weekday in (('WD', 3), ('SAT', 5), ('SUN', 6)):
        out[label] = start + dt.timedelta(days=(weekday - start.weekday()) % 7)
    return out


def firecrawl_cmd():
    """Return the argv prefix that runs the firecrawl CLI.

    On Windows the `firecrawl` entry on PATH is a .CMD shim, and running it
    hands the argv to cmd.exe, which splits the search URL at every '&' and
    tries to execute the fragments as commands. Invoking the package's JS
    entry point through node avoids the shell entirely. On Linux (CI) the
    plain binary works.
    """
    from shutil import which

    node = which('node')
    if node:
        for base in filter(None, [os.environ.get('APPDATA'),
                                  '/usr/lib', '/usr/local/lib',
                                  os.path.expanduser('~/.npm-global/lib')]):
            entry = os.path.join(base, 'npm', 'node_modules',
                                 'firecrawl-cli', 'dist', 'index.js')
            if os.path.exists(entry):
                return [node, entry]
            entry = os.path.join(base, 'node_modules',
                                 'firecrawl-cli', 'dist', 'index.js')
            if os.path.exists(entry):
                return [node, entry]

    direct = which('firecrawl')
    if direct and not direct.lower().endswith(('.cmd', '.bat')):
        return [direct]
    return None


def scrape(url, date, workdir, tag):
    """Fetch one date via the firecrawl CLI. Returns the output path, or None."""
    prefix = firecrawl_cmd()
    if not prefix:
        print("  ! firecrawl CLI not found", file=sys.stderr)
        return None
    out = os.path.join(workdir, f'{tag}.md')
    cmd = prefix + ['scrape', url.format(date=date),
                    '--wait-for', '8000', '--only-main-content', '-o', out]

    # The API allows ~10 requests/minute; six scrapes back to back trip it.
    for attempt in range(RETRIES):
        try:
            # firecrawl writes UTF-8 with ANSI colour codes; decoding it as the
            # Windows default codepage raises UnicodeDecodeError in subprocess.
            subprocess.run(cmd, check=True, capture_output=True, timeout=180,
                           encoding='utf-8', errors='replace')
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            detail = str(getattr(exc, 'stderr', '') or getattr(exc, 'stdout', '') or exc)
            if 'Rate limit' in detail and attempt < RETRIES - 1:
                print(f"  . rate limited on {tag}, waiting {BACKOFF}s", file=sys.stderr)
                time.sleep(BACKOFF)
                continue
            print(f"  ! fetch failed for {tag}: {detail[-300:]}", file=sys.stderr)
            return None
        break

    if os.path.exists(out) and os.path.getsize(out) > 0:
        time.sleep(PACE)   # stay under the per-minute limit for the next call
        return out
    return None


def live_schedule(url, dates, workdir, prefix):
    """Return {departure: periodicity} derived from three scraped days."""
    days = {}
    for label, date in dates.items():
        path = scrape(url, date, workdir, f'{prefix}-{label}')
        if not path:
            return None
        days[label] = parse(path)

    if not any(days.values()):
        return None
    return periodicity(days)


def periodicity(days):
    """Return {departure: periodicity} from {'WD'|'SAT'|'SUN': parse() output}."""
    # A departure can appear under two route strings on different days
    # (the operator swaps the village it serves). Collapse to the time.
    by_time = {}
    for label, trips in days.items():
        for (dep, _route) in trips:
            by_time.setdefault(dep, set()).add(label)

    out = {}
    for dep, labels in by_time.items():
        wd, sat, sun = 'WD' in labels, 'SAT' in labels, 'SUN' in labels
        if wd and sat and sun:
            out[dep] = 'ALL_DAYS'
        elif wd and not sat and not sun:
            out[dep] = 'WORKDAYS'
        elif sat and sun and not wd:
            out[dep] = 'WEEKEND'
        else:
            out[dep] = 'MIXED'  # needs a human — reported as a change
    return out


def diff(app, live):
    """Return (added, removed, changed) between the app and the live timetable."""
    added = sorted(t for t in live if t not in app)
    removed = sorted(t for t in app if t not in live)
    changed = sorted((t, app[t], live[t]) for t in app if t in live and app[t] != live[t])
    return added, removed, changed


def first_day(label, start):
    """The first date on or after start that is a WD / SAT / SUN day."""
    while start.weekday() not in WEEKDAYS[label]:
        start += dt.timedelta(days=1)
    return start


def check_pdfs(switch, today=None, fetch=krs_pdf.fetch):
    """Compare the krs.lt route 106 PDFs with the app's local trips.

    Checks the PDF in force on the next workday, Saturday and Sunday, and the
    first day of every PDF that starts later — an announced timetable is worth
    knowing about before it runs. Returns (results, notes, unknown), where unknown
    lists route 106 PDFs whose file name this check cannot read; the caller reports
    those as a failed check. Raises when the page or a PDF cannot be read.
    """
    today = today or dt.date.today()
    html = fetch(krs_pdf.PAGE).decode('utf-8', 'replace')
    pdfs, unknown = krs_pdf.list_pdfs(html), krs_pdf.unrecognised(html)
    if not pdfs:
        raise ValueError('no route 106 PDFs krs.lt names in a known way'
                         + (f"; unrecognised: {', '.join(unknown)}" if unknown else ''))

    starts = {today} | {p['start'] for p in pdfs if p['start'] > today}
    if switch and switch > today:
        starts.add(switch)
    checks = sorted({(first_day(label, s), label) for s in starts for label in WEEKDAYS})

    parsed, results, notes, done = {}, [], [], set()
    for date, label in checks:
        pdf = krs_pdf.pdf_for(pdfs, label, date)
        if pdf is None:
            raise ValueError(f'no PDF in force for {label} on {date}')
        # The app shows its *Before arrays until SWITCH_DATE.
        suffix = 'Before' if switch and date < switch else ''
        if (pdf['url'], label, suffix) in done:
            continue
        done.add((pdf['url'], label, suffix))

        if switch and date >= switch and pdf['start'] < switch:
            # autobusubilietai.lt gets a new timetable before the municipality
            # publishes its PDF; the PDF still in force describes the old one.
            notes.append(f"no PDF yet for the timetable the app shows from {switch} ({label})")
            continue

        if pdf['url'] not in parsed:
            parsed[pdf['url']] = krs_pdf.read_pdf(fetch(pdf['url']))
        for direction, cfg in ROUTES.items():
            app = app_schedule(cfg['array'] + suffix, local_only=True)
            app_times = {t for t, per in app.items() if per in RUNS_ON[label]}
            pdf_times = set(parsed[pdf['url']][direction])
            results.append(dict(pdf=f"{pdf['kind']} from {pdf['start']}", day=label,
                                direction=direction, trips=len(pdf_times),
                                added=sorted(pdf_times - app_times),
                                removed=sorted(app_times - pdf_times)))
    return results, sorted(set(notes)), unknown


SECONDARY = {
    'ok': 'matches the app',
    'changed': 'differs from the app (secondary source; does not change the app status)',
    'failed': 'could not be checked (secondary source; does not change the app status)',
    'skipped': 'skipped, no way to reach it from here',
}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--json', metavar='PATH', help='also write the diff as JSON')
    args = ap.parse_args(argv)

    switch = switch_date()
    dates = next_dates(switch=switch)
    # A switch more than a week out leaves the whole window on the old timetable.
    suffix = 'Before' if switch and max(dates.values()) < switch else ''
    print("Checking against:", ", ".join(f"{k} {v}" for k, v in dates.items()))
    if switch:
        print(f"App switches timetable on {switch}; comparing with the "
              f"{'old' if suffix else 'new'} one")

    report, failed, any_change = {}, [], False
    with tempfile.TemporaryDirectory() as workdir:
        for name, cfg in ROUTES.items():
            print(f"\n{name}")
            app = app_schedule(cfg['array'] + suffix)
            live = live_schedule(cfg['url'], dates, workdir, name)

            if live is None:
                print("  ! could not fetch — skipped")
                failed.append(name)
                continue

            added, removed, changed = diff(app, live)
            report[name] = dict(app_count=len(app), live_count=len(live),
                                added=added, removed=removed,
                                changed=[dict(time=t, was=w, now=n) for t, w, n in changed])

            if not (added or removed or changed):
                print(f"  no change ({len(app)} trips)")
                continue

            any_change = True
            for t in added:
                print(f"  + {t}  new ({live[t]})")
            for t in removed:
                print(f"  - {t}  gone (was {app[t]})")
            for t, was, now in changed:
                print(f"  ~ {t}  {was} -> {now}")

    # Lines below carry PDF start dates only, never the check date: the workflow
    # hashes this report to tell one difference from another.
    print("\nkrs.lt (municipality PDFs, route 106 trips only — secondary source)")
    try:
        results, notes, unknown = check_pdfs(switch)
    except OSError as exc:
        # krs.lt drops connections from outside Lithuania; krs_pdf.fetch then
        # goes through firecrawl, and raises OSError only when there is no
        # FIRECRAWL_API_KEY to do so.
        print(f"  . not reachable from here, skipped: {exc}")
        krs = dict(result='skipped', error=str(exc))
    except Exception as exc:   # reachable, but a PDF is missing or unreadable
        print(f"  ! could not check: {exc}")
        krs = dict(result='failed', error=str(exc))
    else:
        krs = dict(result='ok', results=results, notes=notes, unrecognised=unknown)
        for r in results:
            where = f"{r['pdf']}, {r['day']}, {r['direction']}"
            if not (r['added'] or r['removed']):
                print(f"  {where}: no change ({r['trips']} trips)")
                continue
            krs['result'] = 'changed'
            print(f"  ~ {where}: in PDF only {', '.join(r['added']) or '-'}; "
                  f"in app only {', '.join(r['removed']) or '-'}")
        for note in notes:
            print(f"  . {note}")
        # A route 106 PDF under a new naming style may be the new timetable; the
        # rows above would then compare the app with the old one.
        for name in unknown:
            print(f"  ! route 106 PDF with a name this check cannot read: {name}")
        if unknown and krs['result'] == 'ok':
            krs['result'] = 'failed'
    report['krs.lt'] = krs

    if args.json:
        with open(args.json, 'w', encoding='utf-8') as fh:
            json.dump(report, fh, ensure_ascii=False, indent=2)

    # The secondary source never changes the exit code: the workflow reads its
    # result from the JSON report and files a separate issue.
    print(f"\nkrs.lt: {SECONDARY[krs['result']]}")

    # A partial run cannot prove "no change": the direction that failed may be
    # the one that moved. Only a complete comparison may report all-clear.
    if failed:
        print(f"Could not check: {', '.join(failed)}", file=sys.stderr)
        if any_change:
            print("Schedule changed in the directions that were checked.")
            return 1
        return 2
    if any_change:
        print("Schedule changed.")
        return 1
    print("No changes.")
    return 0


if __name__ == '__main__':
    sys.exit(main())

"""
Checks the live timetable against what the app currently ships.

Reads the departure/periodicity pairs out of paper/grafikai.html, fetches the same
route from autobusubilietai.lt for a workday, a Saturday and a Sunday, and reports
the difference.

Exit codes:
    0 - no change (or the fetch produced nothing usable; see stderr)
    1 - the live timetable differs from the app
    2 - the fetch failed and no comparison could be made

Requires the `firecrawl` CLI on PATH and FIRECRAWL_API_KEY in the environment.

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
from parse_firecrawl import parse  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, 'paper', 'grafikai.html')

RETRIES = 3    # attempts per scrape when the API rate-limits us
BACKOFF = 20   # seconds to wait after a rate-limit refusal
PACE = 7       # seconds between successful scrapes, to stay under ~10/min

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


def app_schedule(array_name):
    """Return {departure: periodicity} for one data array in grafikai.html."""
    with open(APP, encoding='utf-8') as fh:
        html = fh.read()
    start = html.index(f'const {array_name} = [')
    end = html.index('];', start)
    return {m.group(1): m.group(2) for m in TRIP.finditer(html[start:end])}


def next_dates(today=None):
    """Next Thursday, Saturday and Sunday — always a full future week."""
    today = today or dt.date.today()
    out = {}
    for label, weekday in (('WD', 3), ('SAT', 5), ('SUN', 6)):
        delta = (weekday - today.weekday()) % 7 or 7
        out[label] = today + dt.timedelta(days=delta)
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--json', metavar='PATH', help='also write the diff as JSON')
    args = ap.parse_args()

    dates = next_dates()
    print("Checking against:", ", ".join(f"{k} {v}" for k, v in dates.items()))

    report, failed, any_change = {}, [], False
    with tempfile.TemporaryDirectory() as workdir:
        for name, cfg in ROUTES.items():
            print(f"\n{name}")
            app = app_schedule(cfg['array'])
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

    if args.json:
        with open(args.json, 'w', encoding='utf-8') as fh:
            json.dump(report, fh, ensure_ascii=False, indent=2)

    # A partial run cannot prove "no change": the direction that failed may be
    # the one that moved. Only a complete comparison may report all-clear.
    if failed:
        print(f"\nCould not check: {', '.join(failed)}", file=sys.stderr)
        if any_change:
            print("Schedule changed in the directions that were checked.")
            return 1
        return 2
    if any_change:
        print("\nSchedule changed.")
        return 1
    print("\nNo changes.")
    return 0


if __name__ == '__main__':
    sys.exit(main())

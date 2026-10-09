"""
Offline tests for scripts/draft_update.py, the step that turns a change the watcher
found into an edited app for a pull request.

The app is the grafikai_with_switch.html fixture (its October arrays), the records
are copies taken on 2026-10-02, and the search is a stand-in that serves one
timetable before a start date and another from it. Nothing touches the network.

Run:  python -m unittest discover -s tests -v
"""

import contextlib
import datetime as dt
import io
import json
import os
import re
import shutil
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, 'fixtures')
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'scripts'))

import check_schedule as cs  # noqa: E402
import draft_update as du  # noqa: E402

D = dt.date
TODAY = D(2026, 10, 9)          # a Friday; the check window is 10-15, 10-17, 10-18
DATES = cs.next_dates(today=TODAY)
ROUTE = {  # one plausible route per (direction, intercity)
    ('kaunas-juragiai', False): 'Kaunas-Jonučiai-Skriaudžiai',
    ('kaunas-juragiai', True): 'Kaunas-Marijampolė-Vilkaviškis',
    ('juragiai-kaunas', False): 'Skriaudžiai-Jonučiai-Kaunas',
    ('juragiai-kaunas', True): 'Vilkaviškis-Marijampolė-Kaunas',
}


def fixture_app():
    with open(os.path.join(FIX, 'grafikai_with_switch.html'), encoding='utf-8') as fh:
        return fh.read()


def october_html():
    """The fixture app with its switch taken out: only the October arrays."""
    html = fixture_app()
    html = du.SWITCH_BLOCK.sub('', html, count=1)
    return html.replace(du.PRECALC_BEFORE, '').replace(du.RENDER_SWITCH, du.RENDER_NOW)


def october(direction):
    return du.read_array(october_html(), du.DIRECTIONS[direction]['array'])


def edited(entries, add=(), drop=()):
    """entries with (dep, periodicity, platform) added and departures dropped."""
    out = [e for e in entries if e[0] not in drop] + [(*a, '') for a in add]
    return sorted(out)


def trips_on(direction, entries, date):
    label = du.day_label(date)
    inter = du.DIRECTIONS[direction]['platforms'][1]
    return [[e[0], '00:00', ROUTE[(direction, e[2] == inter)], '1,55 €']
            for e in entries if e[1] in cs.RUNS_ON[label]]


class Search:
    """Serves the old timetable before start, the new one from it.

    blank lists dates that come back incomplete (None), as near dates often do.
    """
    def __init__(self, old, new, start, blank=()):
        self.old, self.new, self.start, self.blank = old, new, start, set(blank)
        self.calls = []

    def __call__(self, direction, date):
        self.calls.append((direction, date))
        if date in self.blank:
            return None
        table = self.new if date >= self.start else self.old
        return trips_on(direction, table[direction], date)

    def report(self, krs_pdfs=(), switch=None):
        out = dict(dates={k: str(v) for k, v in DATES.items()}, switch=switch,
                   **{'krs.lt': dict(result='ok', results=[dict(pdf=p) for p in krs_pdfs])})
        for direction in du.DIRECTIONS:
            days = {label: dict(date=str(date), trips=self(direction, date))
                    for label, date in DATES.items()}
            old = {e[0]: e[1] for e in self.old[direction]}
            new = {e[0]: e[1] for e in self.new[direction]}
            added, removed, changed = cs.diff(old, new)
            out[direction] = dict(added=added, removed=removed,
                                  changed=[dict(time=t, was=w, now=n) for t, w, n in changed],
                                  days=days)
        self.calls.clear()
        return out


def search(start, blank=(), **change):
    """A Search where Kaunas → Juragiai gains 07:10 and loses 06:45 on workdays."""
    old = {d: october(d) for d in du.DIRECTIONS}
    new = dict(old)
    new['kaunas-juragiai'] = edited(old['kaunas-juragiai'], **(change or dict(
        add=[('07:10', 'WORKDAYS', '5')], drop=['06:45'])))
    return Search(old, new, start, blank)


@contextlib.contextmanager
def project(html=None):
    """A copy of the files draft() reads, as a project root."""
    with tempfile.TemporaryDirectory() as root:
        os.makedirs(os.path.join(root, 'paper'))
        with open(os.path.join(root, 'paper', 'grafikai.html'), 'w', encoding='utf-8',
                  newline='') as fh:
            fh.write(html if html is not None else october_html())
        with open(os.path.join(root, 'sw.js'), 'w', encoding='utf-8', newline='') as fh:
            fh.write("const CACHE = 'tvarkarastis-v30';\n")
        for direction, cfg in du.DIRECTIONS.items():
            shutil.copy(os.path.join(FIX, f'{direction}_grafikas_2026-10-02.md'),
                        os.path.join(root, cfg['record']))
        yield root


def run(s, report=None, html=None, **kw):
    """Draft against Search s; return (files, body) with the app also readable via cs."""
    with project(html) as root:
        files, body = du.draft(report or s.report(), TODAY, s, root=root, log=lambda m: None,
                               **kw)
        return files, body


@contextlib.contextmanager
def as_app(html):
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, 'grafikai.html')
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(html)
        with mock.patch.object(cs, 'APP', path):
            yield


class ArrayText(unittest.TestCase):
    def test_the_app_arrays_are_written_back_unchanged(self):
        html = fixture_app()
        for name in ('dataKaunas', 'dataJurginiskai'):
            block = re.search(r'const %s = \[\n(.*?)\n\];' % name, html, re.S).group(1)
            self.assertEqual(du.array_text(du.read_array(html, name)), block)

    def test_a_split_route_gets_a_comment_in_the_house_style(self):
        routes = {'Kaunas-Jonučiai-Jurginiškiai-Skriaudžiai': dict(labels={'WD'}),
                  'Kaunas-Jonučiai-Garliava-Jurginiškiai': dict(labels={'SAT', 'SUN'})}
        self.assertEqual(du.describe(routes, False),
                         'Jurginiskiai-Skriaudziai (Pr-Pn) / Garliava-Jurginiskiai (S-S)')

    def test_intercity_is_told_apart_by_the_route(self):
        days = {label: dict(date=str(d), trips=trips_on('kaunas-juragiai',
                                                        october('kaunas-juragiai'), d))
                for label, d in DATES.items()}
        new = du.timetable('kaunas-juragiai', days, [])
        self.assertEqual([e[:3] for e in new], [e[:3] for e in october('kaunas-juragiai')])
        self.assertEqual(new[5][3], 'tarpmiestinis, Marijampole-Vilkaviskis')


class Draft(unittest.TestCase):
    def test_a_future_start_keeps_the_current_timetable_until_then(self):
        files, body = run(search(D(2026, 10, 14)), issue='7', diff_id='abc')
        html = files['paper/grafikai.html']
        with as_app(html):
            self.assertEqual(cs.switch_date(), D(2026, 10, 14))
            now = cs.app_schedule('dataKaunas')
            self.assertIn('07:10', now)
            self.assertNotIn('06:45', now)
            self.assertEqual(cs.app_schedule('dataKaunasBefore'),
                             {e[0]: e[1] for e in october('kaunas-juragiai')})
            self.assertEqual(cs.app_schedule('dataJurginiskai'),
                             cs.app_schedule('dataJurginiskaiBefore'))
        self.assertIn('  ["07:10", WORKDAYS, "5"],    // Skriaudziai\n', html)
        self.assertIn(du.RENDER_SWITCH, html)
        self.assertEqual(html.count('precalculateTripMinutes(dataKaunasBefore);'), 1)
        self.assertEqual(files['sw.js'], "const CACHE = 'tvarkarastis-v31';\n")

        record = files['paper/kaunas-juragiai_grafikas.md']
        self.assertIn('(galioja nuo 2026-10-14, patikrinta 2026-10-09)', record)
        self.assertIn('| 07:10 | 00:00 | 12345   | 5  | Kaunas-Jonučiai-Skriaudžiai | 1,55 € |',
                      record)
        self.assertNotIn('| 06:45 |', record)
        # Unchanged rows stay as written by hand, carrier notes included.
        self.assertIn('| 11:35 | 11:57 | 1234567 | 12 | Kaunas-Marijampolė-Vilkaviškis '
                      '(Kautra Plius) | 2,00 € |', record)
        self.assertIn('**Iš viso:** 25 reisai — 20 vietinių (5 aikštelė) + '
                      '5 tarpmiestiniai (12 aikštelė)', record)
        self.assertNotIn('paper/juragiai-kaunas_grafikas.md', files)

        self.assertIn('Closes #7.', body)
        self.assertIn('**Starts 2026-10-14**', body)
        self.assertIn('old one on 2026-10-13', body)
        self.assertIn('| new | 07:10 | 12345 | Kaunas-Jonučiai-Skriaudžiai |', body)
        self.assertIn('| gone | 06:45 |', body)
        self.assertIn('<!-- diff:abc -->', body)

    def test_the_scan_stops_at_the_first_day_showing_the_new_timetable(self):
        s = search(D(2026, 10, 12))
        run(s)
        scanned = sorted(d for _, d in s.calls if d < D(2026, 10, 19))
        self.assertEqual(scanned, [D(2026, 10, 10), D(2026, 10, 11), D(2026, 10, 12)])

    def test_incomplete_near_days_leave_the_first_full_day_as_the_start(self):
        s = search(D(2026, 10, 12), blank=[D(2026, 10, 10), D(2026, 10, 11),
                                            D(2026, 10, 12), D(2026, 10, 13)])
        files, body = run(s)
        with as_app(files['paper/grafikai.html']):
            self.assertEqual(cs.switch_date(), D(2026, 10, 14))
        self.assertIn('may have started sooner', body)

    def test_a_krs_pdf_date_between_old_and_new_is_the_start(self):
        s = search(D(2026, 10, 13), blank=[D(2026, 10, 13)])
        report = s.report(krs_pdfs=['dd from 2026-10-01', 'dd from 2026-10-13'])
        files, body = run(s, report)
        with as_app(files['paper/grafikai.html']):
            self.assertEqual(cs.switch_date(), D(2026, 10, 13))
        self.assertIn('the date the krs.lt PDF names', body)

    def test_a_passed_switch_is_replaced_not_stacked(self):
        s = search(D(2026, 10, 14))
        files, _ = run(s, s.report(switch='2026-10-01'), html=fixture_app())
        html = files['paper/grafikai.html']
        self.assertEqual(html.count('const SWITCH_DATE'), 1)
        self.assertEqual(html.count('const dataKaunasBefore'), 1)
        with as_app(html):
            self.assertEqual(cs.switch_date(), D(2026, 10, 14))
            self.assertEqual(cs.app_schedule('dataKaunasBefore'),
                             {e[0]: e[1] for e in october('kaunas-juragiai')})


class Refusals(unittest.TestCase):
    def refused(self, s, report=None, html=None):
        with self.assertRaises(du.Refused) as cm:
            run(s, report, html)
        return str(cm.exception)

    def test_a_pending_switch_needs_a_person(self):
        s = search(D(2026, 10, 14))
        self.assertIn('already carries', self.refused(s, s.report(switch='2026-10-20')))

    def test_a_trip_on_workdays_and_saturday_only(self):
        s = search(D(2026, 10, 14))
        report = s.report()
        report['kaunas-juragiai']['days']['SAT']['trips'].append(
            ['07:10', '07:40', ROUTE[('kaunas-juragiai', False)], '1,55 €'])
        self.assertIn('07:10', self.refused(s, report))

    def test_a_missing_intercity_trip_is_a_bad_scrape(self):
        s = search(D(2026, 10, 14), drop=['08:00'])
        self.assertIn('4 intercity trips', self.refused(s))

    def test_a_change_that_does_not_repeat_a_week_later(self):
        s = search(D(2026, 10, 14))
        report = s.report()
        s.start = D(2026, 12, 1)   # the week after shows the old timetable again
        self.assertIn('different timetable', self.refused(s, report))

    def test_an_unscraped_direction(self):
        s = search(D(2026, 10, 14))
        report = s.report()
        del report['juragiai-kaunas']
        self.assertIn('could not be scraped', self.refused(s, report))


class Main(unittest.TestCase):
    def test_a_report_without_a_change_drafts_nothing(self):
        s = search(D(2026, 10, 14), add=[], drop=[])
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'diff.json')
            with open(path, 'w', encoding='utf-8') as fh:
                json.dump(s.report(), fh)
            with contextlib.redirect_stdout(io.StringIO()):
                code = du.main([path, '--body', os.path.join(tmp, 'pr.md')])
        self.assertEqual(code, 2)

    def test_lithuanian_counts(self):
        self.assertEqual([du.lt_count(n, 'reisas', 'reisai', 'reisų') for n in (1, 2, 11, 20, 21, 25)],
                         ['1 reisas', '2 reisai', '11 reisų', '20 reisų', '21 reisas', '25 reisai'])


if __name__ == '__main__':
    unittest.main()

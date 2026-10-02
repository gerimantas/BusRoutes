"""
Offline tests for the schedule watcher: scripts/check_schedule.py, krs_pdf.py and
parse_firecrawl.py.

Nothing here touches the network. The fixtures are real downloads:
  kaunas-juragiai_2026-10-10.md   firecrawl scrape of the search page, a Saturday
  krs_page_2026-10-02.html        krs.lt route list with five route 106 PDFs
  106-*.pdf                       those five PDFs (September and October)
  grafikai_with_switch.html       the app at 7de485b, carrying both timetables
                                  and SWITCH_DATE 2026-10-01

Run:  python -m unittest discover -s tests -v
"""

import base64
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
import urllib.parse
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, 'fixtures')
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'scripts'))

import check_schedule as cs  # noqa: E402
import krs_pdf  # noqa: E402
from parse_firecrawl import parse  # noqa: E402

D = dt.date

PDF_FILES = {
    ('dd', D(2026, 8, 31)): '106-dd-2026-08-31.pdf',
    ('š', D(2026, 9, 5)): '106-sat-2026-09-05.pdf',
    ('s', D(2026, 9, 6)): '106-sun-2026-09-06.pdf',
    ('dd', D(2026, 10, 1)): '106-dd-2026-10-01.pdf',
    ('šs', D(2026, 10, 3)): '106-weekend-2026-10-03.pdf',
}

OCT_WD = {
    'kaunas-juragiai': ['05:00', '05:50', '05:55', '06:45', '06:50', '09:05', '09:55',
                        '10:50', '12:15', '12:35', '13:30', '14:00', '14:50', '15:30',
                        '16:00', '16:25', '17:30', '18:40', '19:30'],
    'juragiai-kaunas': ['06:03', '06:53', '07:17', '08:04', '08:36', '10:06', '11:18',
                        '11:46', '13:38', '14:03', '14:58', '15:23', '16:13', '16:53',
                        '17:01', '17:46', '19:03', '20:03', '20:26'],
}
OCT_WEEKEND = {
    'kaunas-juragiai': ['05:50', '08:30', '10:50', '12:35', '15:30'],
    'juragiai-kaunas': ['06:57', '09:20', '11:45', '13:38', '16:53'],
}


def read_fixture(name, mode='rb'):
    with open(os.path.join(FIX, name), mode, **({} if 'b' in mode else {'encoding': 'utf-8'})) as fh:
        return fh.read()


def fake_fetch(page=None):
    """A krs_pdf.fetch stand-in serving the fixtures; page overrides the route list."""
    page = page if page is not None else read_fixture('krs_page_2026-10-02.html', 'r')

    def fetch(url):
        if url == krs_pdf.PAGE:
            return page.encode('utf-8')
        m = krs_pdf.NAME.search(urllib.parse.unquote(url))
        start = D(*(int(x) for x in m.group(2, 3, 4)))
        return read_fixture(PDF_FILES[(m.group(1).lower(), start)])
    return fetch


def page_without(fragment):
    """The real krs.lt page with every route 106 PDF link containing fragment removed."""
    html = read_fixture('krs_page_2026-10-02.html', 'r')
    return re.sub(r'<a [^>]*internetas-106-[^"]*' + re.escape(fragment) + r'[^>]*>', '', html)


@contextlib.contextmanager
def app_file(path=None, replace=None):
    """Point the watcher at another copy of grafikai.html, optionally edited.

    replace is one (old, new) pair or a list of them, applied in order.
    """
    src = path or cs.APP
    with tempfile.TemporaryDirectory() as tmp:
        dst = os.path.join(tmp, 'grafikai.html')
        shutil.copy(src, dst)
        if replace:
            with open(dst, encoding='utf-8') as fh:
                html = fh.read()
            for old, new in [replace] if isinstance(replace, tuple) else replace:
                assert old in html, old
                html = html.replace(old, new)
            with open(dst, 'w', encoding='utf-8', newline='') as fh:
                fh.write(html)
        with mock.patch.object(cs, 'APP', dst):
            yield


def october_app(replace=()):
    """The fixture app with its switch removed: dataKaunas/dataJurginiskai are
    the October arrays the October PDF fixtures describe. Tests use this rather
    than the live app so a future timetable change does not break them."""
    return app_file(os.path.join(FIX, 'grafikai_with_switch.html'),
                    replace=[('const SWITCH_DATE =', 'const NOT_A_SWITCH =')] + list(replace))


def changes(results):
    return [r for r in results if r['added'] or r['removed']]


# --- autobusubilietai.lt -----------------------------------------------------

class FirecrawlParser(unittest.TestCase):
    def test_keeps_real_trips_and_drops_round_hour_markers(self):
        path = os.path.join(FIX, 'kaunas-juragiai_2026-10-10.md')
        bold_times = [l for l in read_fixture('kaunas-juragiai_2026-10-10.md', 'r').splitlines()
                      if re.match(r'^\*\*\d{2}:\d{2}\*\*', l.strip())]
        trips = parse(path)
        self.assertEqual(len(bold_times), 24)   # 10 trips + 14 markers on the page
        self.assertEqual(sorted({dep for dep, _ in trips}),
                         ['05:50', '08:00', '08:30', '10:50', '11:35', '12:00',
                          '12:35', '12:40', '15:30', '16:50'])
        for rec in trips.values():
            self.assertTrue(rec['price'].endswith('€'), rec)


class Periodicity(unittest.TestCase):
    def test_days_present_decide_the_periodicity(self):
        days = {
            'WD': {('05:00', 'a'): {}, ('06:00', 'a'): {}, ('07:00', 'a'): {}},
            'SAT': {('06:00', 'a'): {}, ('08:00', 'a'): {}, ('07:00', 'a'): {}},
            'SUN': {('06:00', 'a'): {}, ('08:00', 'a'): {}},
        }
        self.assertEqual(cs.periodicity(days), {
            '05:00': 'WORKDAYS', '06:00': 'ALL_DAYS', '08:00': 'WEEKEND',
            '07:00': 'MIXED'})   # WD + SAT only: no constant fits, a human decides

    def test_one_departure_on_two_routes_is_one_trip(self):
        # The operator runs 12:35 via Skriaudžiai on workdays, via Garliava at weekends.
        days = {'WD': {('12:35', 'Skriaudziai'): {}},
                'SAT': {('12:35', 'Garliava'): {}},
                'SUN': {('12:35', 'Garliava'): {}}}
        self.assertEqual(cs.periodicity(days), {'12:35': 'ALL_DAYS'})


class Diff(unittest.TestCase):
    def test_added_removed_changed(self):
        app = {'05:00': 'WORKDAYS', '06:00': 'ALL_DAYS', '07:00': 'WEEKEND'}
        live = {'05:00': 'WORKDAYS', '06:00': 'WORKDAYS', '08:00': 'ALL_DAYS'}
        self.assertEqual(cs.diff(app, live),
                         (['08:00'], ['07:00'], [('06:00', 'ALL_DAYS', 'WORKDAYS')]))

    def test_identical_is_empty(self):
        app = {'05:00': 'WORKDAYS'}
        self.assertEqual(cs.diff(app, dict(app)), ([], [], []))


class NextDates(unittest.TestCase):
    def test_thursday_saturday_sunday_at_least_lead_days_ahead(self):
        today = D(2026, 10, 2)   # Friday
        dates = cs.next_dates(today=today)
        self.assertEqual(dates, {'WD': D(2026, 10, 8), 'SAT': D(2026, 10, 10),
                                 'SUN': D(2026, 10, 11)})
        for d in dates.values():
            self.assertGreaterEqual((d - today).days, cs.LEAD)

    def test_switch_inside_the_window_moves_it_onto_the_new_timetable(self):
        dates = cs.next_dates(today=D(2026, 9, 26), switch=D(2026, 10, 1))
        self.assertTrue(all(d >= D(2026, 10, 1) for d in dates.values()), dates)

    def test_switch_beyond_the_window_leaves_it(self):
        dates = cs.next_dates(today=D(2026, 9, 1), switch=D(2026, 10, 1))
        self.assertTrue(all(d < D(2026, 10, 1) for d in dates.values()), dates)


class AppData(unittest.TestCase):
    def test_every_trip_line_is_read(self):
        # A trip written in a shape the regex misses would silently drop out of
        # every comparison.
        with open(cs.APP, encoding='utf-8') as fh:
            html = fh.read()
        for name in ('dataKaunas', 'dataJurginiskai'):
            start = html.index(f'const {name} = [')
            block = html[start:html.index('];', start)]
            lines = [l for l in block.splitlines() if l.strip().startswith('["')]
            self.assertEqual(len(lines), len(cs.app_schedule(name)), name)

    def test_local_only_drops_intercity(self):
        with october_app():
            full = cs.app_schedule('dataKaunas')
            local = cs.app_schedule('dataKaunas', local_only=True)
        self.assertNotIn('08:00', local)      # intercity, bay 12
        self.assertEqual(len(full) - len(local), 5)

    def test_switch_date_is_read_and_absent_is_none(self):
        with app_file(os.path.join(FIX, 'grafikai_with_switch.html')):
            self.assertEqual(cs.switch_date(), D(2026, 10, 1))
        with app_file(os.path.join(FIX, 'grafikai_with_switch.html'),
                      replace=('const SWITCH_DATE =', 'const NOT_A_SWITCH =')):
            self.assertIsNone(cs.switch_date())


# --- krs.lt PDFs --------------------------------------------------------------

class KrsPage(unittest.TestCase):
    def test_lists_all_route_106_pdfs(self):
        pdfs = krs_pdf.list_pdfs(read_fixture('krs_page_2026-10-02.html', 'r'))
        self.assertEqual({(p['kind'], p['start']) for p in pdfs}, set(PDF_FILES))
        for p in pdfs:
            self.assertTrue(p['url'].startswith('https://www.krs.lt/media/'), p['url'])

    def test_percent_encoded_links_are_read(self):
        html = '<a href="/media/1/internetas-106-%C5%A1s-nuo-2026-11-07.pdf">x</a>'
        self.assertEqual([(p['kind'], p['start']) for p in krs_pdf.list_pdfs(html)],
                         [('šs', D(2026, 11, 7))])

    def test_pdf_in_force_is_the_newest_started(self):
        pdfs = krs_pdf.list_pdfs(read_fixture('krs_page_2026-10-02.html', 'r'))
        pick = lambda label, d: (lambda p: p and (p['kind'], p['start']))(krs_pdf.pdf_for(pdfs, label, d))
        self.assertEqual(pick('WD', D(2026, 9, 30)), ('dd', D(2026, 8, 31)))
        self.assertEqual(pick('WD', D(2026, 10, 1)), ('dd', D(2026, 10, 1)))
        self.assertEqual(pick('SAT', D(2026, 9, 26)), ('š', D(2026, 9, 5)))
        self.assertEqual(pick('SAT', D(2026, 10, 3)), ('šs', D(2026, 10, 3)))
        self.assertEqual(pick('SUN', D(2026, 10, 4)), ('šs', D(2026, 10, 3)))
        self.assertIsNone(pick('WD', D(2026, 8, 1)))


class KrsFetch(unittest.TestCase):
    """krs.lt blocks foreign IPs; fetch() falls back to firecrawl from Lithuania."""

    URL = 'https://www.krs.lt/media/89573/internetas-106-šs-nuo-2026-10-03.pdf'

    def setUp(self):
        patches = [mock.patch.object(krs_pdf, '_direct', True),
                   mock.patch.dict(os.environ, {'FIRECRAWL_API_KEY': 'fc-test'})]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def firecrawl_reply(self, status=200, raw=b'%PDF-1.7 bytes'):
        reply = {'success': True, 'data': {'rawBase64': base64.b64encode(raw).decode(),
                                           'metadata': {'statusCode': status}}}
        resp = mock.MagicMock()
        resp.__enter__.return_value = io.BytesIO(json.dumps(reply).encode())
        return resp

    def test_direct_failure_switches_to_firecrawl_for_the_rest_of_the_run(self):
        sent = []

        def urlopen(req, timeout):
            if not req.full_url.startswith(krs_pdf.FIRECRAWL):
                raise TimeoutError('timed out')
            sent.append(json.loads(req.data))
            return self.firecrawl_reply()

        with mock.patch.object(krs_pdf.urllib.request, 'urlopen', side_effect=urlopen) as op:
            self.assertEqual(krs_pdf.fetch(self.URL), b'%PDF-1.7 bytes')
            self.assertEqual(krs_pdf.fetch(krs_pdf.PAGE), b'%PDF-1.7 bytes')
        self.assertEqual(op.call_count, 3)   # one direct attempt, then firecrawl only
        self.assertEqual(sent[0]['formats'], ['rawBase64'])
        self.assertEqual(sent[0]['location'], {'country': 'LT'})
        self.assertNotIn('š', sent[0]['url'])  # path is percent-encoded

    def test_without_an_api_key_the_direct_error_is_raised(self):
        with mock.patch.dict(os.environ, {'FIRECRAWL_API_KEY': ''}),              mock.patch.object(krs_pdf, 'fetch_direct', side_effect=TimeoutError):
            with self.assertRaises(OSError):
                krs_pdf.fetch(self.URL)

    def test_firecrawl_failure_is_not_an_unreachable_site(self):
        # OSError means "skipped"; a failing fallback must fail the check instead.
        with mock.patch.object(krs_pdf, 'fetch_direct', side_effect=TimeoutError),              mock.patch.object(krs_pdf.urllib.request, 'urlopen',
                               return_value=self.firecrawl_reply(status=404)):
            with self.assertRaises(RuntimeError):
                krs_pdf.fetch(self.URL)
        with mock.patch.object(krs_pdf, 'fetch_direct', side_effect=TimeoutError),              mock.patch.object(krs_pdf.urllib.request, 'urlopen',
                               side_effect=TimeoutError('timed out')):
            with self.assertRaises(RuntimeError):
                krs_pdf.fetch(self.URL)


class KrsPdfParser(unittest.TestCase):
    def test_october_workday_pdf(self):
        self.assertEqual(krs_pdf.read_pdf(read_fixture('106-dd-2026-10-01.pdf')), OCT_WD)

    def test_october_weekend_pdf_with_tables_side_by_side(self):
        self.assertEqual(krs_pdf.read_pdf(read_fixture('106-weekend-2026-10-03.pdf')), OCT_WEEKEND)

    def test_every_fixture_pdf_parses_to_both_directions(self):
        for name in PDF_FILES.values():
            out = krs_pdf.read_pdf(read_fixture(name))
            self.assertTrue(out['kaunas-juragiai'] and out['juragiai-kaunas'], name)

    def test_unpaired_rows_fail_instead_of_dropping_trips(self):
        text = ('Kauno autobusų stotis  05:00  06:00  07:00\n'
                '      Juragiai          05:34  06:34\n')
        with self.assertRaises(ValueError):
            krs_pdf.parse_text(text)
        with self.assertRaises(ValueError):
            krs_pdf.parse_text('no timetable here')

    def test_direction_follows_the_earlier_stop(self):
        text = ('05:50  08:30   Kauno autobusų stotis   07:34  09:57\n'
                '06:24  09:09        Juragiai           06:57  09:20\n')
        self.assertEqual(krs_pdf.parse_text(text),
                         {'kaunas-juragiai': ['05:50', '08:30'],
                          'juragiai-kaunas': ['06:57', '09:20']})


class CheckPdfs(unittest.TestCase):
    def test_october_app_matches_the_october_pdfs(self):
        with october_app():
            results, notes = cs.check_pdfs(None, today=D(2026, 10, 2), fetch=fake_fetch())
        self.assertEqual(len(results), 6)   # WD, SAT, SUN x two directions
        self.assertEqual(changes(results), [])
        self.assertEqual(notes, [])

    def test_a_changed_trip_is_reported_on_the_right_day_and_direction(self):
        with october_app([('["05:00", WORKDAYS, "5"]', '["05:05", WORKDAYS, "5"]')]):
            results, _ = cs.check_pdfs(None, today=D(2026, 10, 2), fetch=fake_fetch())
        self.assertEqual([(r['day'], r['direction'], r['added'], r['removed'])
                          for r in changes(results)],
                         [('WD', 'kaunas-juragiai', ['05:00'], ['05:05'])])

    def test_intercity_trips_are_not_compared_with_the_pdf(self):
        with october_app([('["08:00", ALL_DAYS, "12"]', '["08:01", ALL_DAYS, "12"]')]):
            results, _ = cs.check_pdfs(None, today=D(2026, 10, 2), fetch=fake_fetch())
        self.assertEqual(changes(results), [])

    def test_announced_pdf_is_checked_before_it_starts(self):
        # 2026-09-30, an app that only knows September: the October PDFs are
        # already on the page and must be reported before they start.
        september_only = [
            ('const SWITCH_DATE =', 'const NOT_A_SWITCH ='),
            ('const dataKaunas = [', 'const octoberKaunas = ['),
            ('const dataJurginiskai = [', 'const octoberJurginiskai = ['),
            ('const dataKaunasBefore = [', 'const dataKaunas = ['),
            ('const dataJurginiskaiBefore = [', 'const dataJurginiskai = ['),
        ]
        with app_file(os.path.join(FIX, 'grafikai_with_switch.html'), replace=september_only):
            results, _ = cs.check_pdfs(None, today=D(2026, 9, 30), fetch=fake_fetch())
        self.assertEqual({r['pdf'] for r in changes(results)},
                         {'dd from 2026-10-01', 'šs from 2026-10-03'})

    def test_both_timetables_match_around_the_switch(self):
        # The app as shipped on 2026-09-26: September arrays until 2026-10-01,
        # October after. On 2026-09-30 every PDF lines up with its own arrays.
        with app_file(os.path.join(FIX, 'grafikai_with_switch.html')):
            results, notes = cs.check_pdfs(D(2026, 10, 1), today=D(2026, 9, 30),
                                           fetch=fake_fetch())
        self.assertEqual(changes(results), [])
        self.assertEqual(notes, [])
        self.assertEqual({r['pdf'] for r in results},
                         {'dd from 2026-08-31', 'dd from 2026-10-01', 'šs from 2026-10-03'})

    def test_missing_pdf_for_the_new_timetable_is_a_note_not_a_change(self):
        # 2026-09-26: autobusubilietai.lt showed October, krs.lt had no PDF yet.
        with app_file(os.path.join(FIX, 'grafikai_with_switch.html')):
            results, notes = cs.check_pdfs(D(2026, 10, 1), today=D(2026, 9, 26),
                                           fetch=fake_fetch(page_without('2026-10')))
        self.assertEqual(changes(results), [])
        self.assertTrue(results)
        self.assertTrue(notes)
        self.assertTrue(all('2026-10-01' in n for n in notes), notes)

    def test_page_without_route_106_fails(self):
        with self.assertRaises(ValueError):
            cs.check_pdfs(None, today=D(2026, 10, 2), fetch=fake_fetch('<html></html>'))


# --- exit codes ------------------------------------------------------------------

class ExitCodes(unittest.TestCase):
    """0 = all clear, 1 = changed, 2 = could not check and nothing checked differs."""

    def run_main(self, live='same', pdf='same'):
        def fake_live(url, dates, workdir, name):
            if live == 'fail' and name == 'juragiai-kaunas':
                return None
            app = cs.app_schedule(cs.ROUTES[name]['array'])
            if live == 'changed' and name == 'kaunas-juragiai':
                app['23:59'] = 'WORKDAYS'
            return app

        def fake_pdfs(switch):
            if pdf == 'fail':
                raise ValueError('expected paired stop rows')
            if pdf == 'unreachable':
                raise TimeoutError('timed out')
            diff = ['05:05'] if pdf == 'changed' else []
            return [dict(pdf='dd from 2026-10-01', day='WD', direction='kaunas-juragiai',
                         trips=19, added=diff, removed=[])], []

        out = io.StringIO()
        with mock.patch.object(cs, 'live_schedule', fake_live), \
             mock.patch.object(cs, 'check_pdfs', fake_pdfs), \
             contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = cs.main([])
        return code, out.getvalue()

    def test_all_clear(self):
        self.assertEqual(self.run_main()[0], 0)

    def test_change_on_the_search_page(self):
        self.assertEqual(self.run_main(live='changed')[0], 1)

    def test_change_in_the_pdf(self):
        code, report = self.run_main(pdf='changed')
        self.assertEqual(code, 1)
        self.assertIn('in PDF only 05:05', report)

    def test_failed_source_is_never_all_clear(self):
        self.assertEqual(self.run_main(live='fail')[0], 2)
        self.assertEqual(self.run_main(pdf='fail')[0], 2)

    def test_unreachable_krs_is_skipped_not_failed(self):
        # krs.lt blocks foreign IPs; the GitHub runner cannot reach it.
        code, report = self.run_main(pdf='unreachable')
        self.assertEqual(code, 0)
        self.assertIn('not reachable from here', report)
        self.assertEqual(self.run_main(live='changed', pdf='unreachable')[0], 1)
        self.assertEqual(self.run_main(live='fail', pdf='unreachable')[0], 2)

    def test_change_wins_over_a_failed_source(self):
        self.assertEqual(self.run_main(live='fail', pdf='changed')[0], 1)
        self.assertEqual(self.run_main(live='changed', pdf='fail')[0], 1)

    def test_report_lines_carry_no_check_date(self):
        # The workflow hashes the report (minus the "Checking against" line) to
        # tell one difference from another; a date in it would file a new
        # comment every day for the same difference.
        _, report = self.run_main(pdf='changed')
        today = dt.date.today()
        body = [l for l in report.splitlines() if not l.startswith('Checking against')]
        for d in cs.next_dates().values():
            self.assertFalse(any(str(d) in l for l in body), (d, body))
        self.assertFalse(any(str(today) in l for l in body))


if __name__ == '__main__':
    unittest.main()

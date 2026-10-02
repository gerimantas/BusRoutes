# Grafikai — CONTEXT

## Status
Active. The app carries only the October route 106 timetable (no dated switch
pending); it matches the krs.lt PDFs to the minute. The watcher compares two
sources — autobusubilietai.lt and the krs.lt PDFs, including PDFs announced for a
later date — and publishes its result, shown under the tabs ("Tikrinta …").
krs.lt blocks non-Lithuanian IPs, so on GitHub the PDF check is skipped (a note,
not a failure); it runs only locally. CI therefore still checks one source.
33 offline tests in `tests/` run on GitHub on every watcher/app change.
Cache `tvarkarastis-v28` live on GitHub Pages.

## Next Tasks
- Make the krs.lt PDF check run in CI: krs.lt drops GitHub runner connections.
  firecrawl `--country LT` reaches it, but its PDF parse misaligns stop rows, so
  PDF bytes must come another way (an LT proxy, or a raw-file option). Archive 2026-10-02.

## Done Log

### 2026-10-02
- October timetable verified against krs.lt PDFs; September arrays and `SWITCH_DATE` removed
- Watcher checks krs.lt PDFs as a second source (`scripts/krs_pdf.py`); skipped in CI (geo-block)
- 33 offline tests with real fixtures + `tests.yml` CI

### 2026-09-26
- October timetable shipped with a dated switch; issue #4 closed
- Last-check line in the app, fed by the watcher via the `status` branch
- Watcher: 3-day lead, `SWITCH_DATE`-aware, one issue per change
- App name Juragiai; READMEs updated; session-start idle-gap fix

## Key Facts
- Live: https://gerimantas.github.io/BusRoutes/paper/grafikai.html
- Repo: https://github.com/gerimantas/BusRoutes
- Route 106 plus intercity services stopping at Juragiai — single-file PWA
- Trips from 2026-10-01: Kaunas→Juragiai 25 (20 local + 5 intercity), Juragiai→Kaunas 27 (22 + 5)
- Official timetable PDFs: https://www.krs.lt/gyventojams/viesasis-transportas/priemiestiniai-autobusu-marsrutai/
- Route 106 terminates at Skriaudžiai; trips via Garliava end at Jurginiškiai
- Service Worker cache: read the current value from `sw.js` line 1; bump on every HTML change
- Structure: `paper/` (production) + `scripts/` (schedule tooling)
- Schedule source is autobusubilietai.lt via firecrawl, not the MD files —
  those record what was verified and when

### Deploy workflow
1. Edit `paper/grafikai.html`
2. Bump `CACHE` in `sw.js`
3. `git add paper/grafikai.html sw.js && git commit -m "..." && git push`
4. Verify: `gh api repos/gerimantas/BusRoutes/pages --jq '.status'`

### Refresh workflow
1. `firecrawl scrape` the search URL for a workday, Saturday and Sunday, both directions
2. `python scripts/parse_firecrawl.py <wd> <sat> <sun>` — read periodicity off the day flags
3. Update `paper/grafikai.html` and both `paper/*_grafikas.md`
4. Deploy as above

Full procedure: `.claude/skills/grafikai/SKILL.md`

## Dead Ends
- **Playwright scraper (`scripts/scrape_juragiai.py`, removed 2026-09-02).** It read
  every `HH:MM` on the search page, including round-hour markers that carry no route,
  carrier or fare. Its intercity output listed 20 trips where 5 exist. Any future
  scraper must require a route line and a fare before accepting a row.
- **PR-based change notification (removed 2026-09-02).** The weekly workflow filed
  pull requests against `web/`, which is not deployed and which nobody watched. Two
  August schedule changes went unnoticed. Notification now goes through GitHub
  issues, which email the owner.
- **Bash heredocs for edit scripts.** Regex backslashes (`\\-`, `\s`) get mangled by
  the shell; the pattern then matches nothing and the script reports zero results
  as though the data were empty. Write the script to a file first.
- **firecrawl for krs.lt PDFs (2026-10-02).** Reaches krs.lt only with `--country LT`,
  and its PDF-to-markdown output shifts stop rows by one. Read PDFs with pypdf.
- **Partial periodicity constants.** `SUNDAY` and `MON_SAT` were added and reverted
  the same session: the trips that appeared to need them are single daily trips the
  operator routes through a different village on Sunday.

## Files
- `paper/grafikai.html` — production PWA
- `paper/kaunas-juragiai_grafikas.md` — schedule record Kaunas→Juragiai
- `paper/juragiai-kaunas_grafikas.md` — schedule record Juragiai→Kaunas
- `sw.js` — Service Worker (cache-first, bump version on each release)
- `manifest.json` — PWA manifest
- `scripts/check_schedule.py` — live-vs-app comparison; exit 1 = changed, 2 = could not check
- `scripts/parse_firecrawl.py` — parses firecrawl output into a trip table
- `scripts/krs_pdf.py` — finds and reads the route 106 PDFs on krs.lt
- `tests/test_check_schedule.py` + `tests/fixtures/` — offline watcher tests;
  fixtures test logic, keep them when the timetable changes
- `.github/workflows/schedule-watch.yml` — daily watcher, opens an issue on change,
  force-pushes `status.json` to the `status` branch (read by the app)
- `.github/workflows/tests.yml` — runs the tests on changes to scripts, tests, app

## Archive

### Session 2026-10-02 — September timetable removed, krs.lt PDFs in the watcher, tests

- **Done:** krs.lt October 106 PDFs (dd from 10-01, šs from 10-03) match the app to the minute (19+19 workday, 5+5 weekend). Removed `dataKaunasBefore`/`dataJurginiskaiBefore`/`SWITCH_DATE`; cache v28 live. Watcher now compares krs.lt PDFs with the app's local trips: PDF in force now + every PDF announced for a later date; a missing PDF for a timetable the app already switched to is a note, not a change. 32 offline tests with real fixtures; `tests.yml` passed on GitHub.
- **Found:** krs.lt blocks non-Lithuanian IPs. CI run 36975699351 timed out on it, turned the app status red and opened issue #5 (closed). firecrawl fails without `--country LT`; with it, the page loads but its PDF-to-markdown parse shifts stop rows (Juragiai row carries Stanaičiai times) — unusable for times.
- **Decided / overturned:** an unreachable krs.lt (OSError) is skipped with a note; a reachable krs.lt with a missing/unreadable PDF still fails. Tests run against a fixture copy of the app (`grafikai_with_switch.html`) so a timetable change does not break them. pypdf pinned to 6.19.0 in CI.
- **Code:** new `scripts/krs_pdf.py`, `tests/test_check_schedule.py` (33 tests), `tests/fixtures/` (5 PDFs, krs.lt page, one scraped search page, app at 7de485b), `.github/workflows/tests.yml`; changed `scripts/check_schedule.py` (`check_pdfs`, `periodicity`, `main(argv)`), `scripts/parse_firecrawl.py` (closes file), `schedule-watch.yml` (pypdf, issue text), `paper/grafikai.html`, `sw.js`, READMEs, both `paper/*_grafikas.md`. Commits `7c7c10f`, `3b5bc49`, `524c0e4`. Local only: `CLAUDE.md`, grafikai `SKILL.md`.
- **Entry point:** `python scripts/check_schedule.py`; `python -m unittest discover -s tests -v`
- **Not measured:** a real change flowing through the PDF path into an issue; the Node 20 deprecation on `setup-node@v4`/`upload-artifact@v4`.

### Session 2026-09-26 — October timetable with dated switch, last-check line in app

- **Done:** Watcher issue #4 was real: route 106 gets a new timetable on 2026-10-01 (autobusubilietai.lt, verified on two October weeks). App carries both timetables and switches at midnight on `SWITCH_DATE`. Watcher publishes `status.json` to the orphan `status` branch; app shows "Tikrinta … — grafikas sutampa", red on change/failure/>48 h. Watcher now checks 3+ days ahead, reads `SWITCH_DATE`, keeps one issue per change. App name Juragiai (106 now terminates at Skriaudžiai; only Garliava trips end at Jurginiškiai). session-start no longer flags an idle project as a gap (ai-skills `2a3fe45`).
- **Decided / overturned:** watcher only reports, never edits the app (a scrape can return a partial list — 2026-09-27 listed no 106 trips). krs.lt PDFs are the official cross-check; they matched the September timetable to the minute. No route 106A exists.
- **Code:** `paper/grafikai.html` (`dataKaunasBefore`/`dataJurginiskaiBefore`, `SWITCH_DATE`, `#check-status`, CSP allows raw.githubusercontent.com), both `paper/*_grafikas.md`, `scripts/check_schedule.py`, `.github/workflows/schedule-watch.yml`, `manifest.json`, `README.md`, `paper/README.md`, `sw.js` → v27. Commits `023cb62`, `46e315b`, `fd2c91c`. Local only: `CLAUDE.md`, grafikai `SKILL.md` (PDF source, Node Playwright + fake-clock test recipe).
- **Entry point:** `gh workflow run schedule-watch.yml` (run 36254744357: ok, status published); `curl -s https://raw.githubusercontent.com/gerimantas/BusRoutes/status/status.json`
- **Not measured:** the October timetable against an official PDF (none published by 09-26); the midnight switch on a real phone; the dedupe path of the issue step (no change has occurred since).

### Session 2026-09-02 — timetable refresh + change detection

The app had been serving a June timetable since an August change nobody was told
about. Root cause was not the scraper failing but the notification going nowhere:
the weekly workflow filed pull requests against `web/`, an experimental directory
that is not deployed and that nobody watched. Two PRs sat open for weeks.

The scraper was also wrong. `scrape_juragiai.py` read every `HH:MM` on the
autobusubilietai.lt search page, including round-hour markers that carry no route,
no carrier and no fare. Its intercity output listed 20 trips where 5 exist. Mid-
session I offered the user a choice between "3 trustworthy trips" and "all 20" —
that was the wrong move; the correct response to untrustworthy data is to go get
trustworthy data, which is what firecrawl then did.

Refreshed both directions from autobusubilietai.lt via the firecrawl CLI, scraped
for Thursday, Saturday and Sunday, plus Monday as a consistency check. Cross-checked
against a station board photo and a stop sign photo the user supplied. The photos
confirmed the times but were cropped — they cut off `05:00` and `05:50`, which do
run — so the live data won where they disagreed.

Added `MON_SAT` and `SUNDAY` constants, then reverted them the same session: the
two trips that seemed to need partial periodicity are single daily trips the
operator routes through a different village on Sunday, visible as two route strings
on one departure time. Back to 3 constants.

Also found and fixed: `sw.js` was already at `v24` before my first bump, so that
bump was a no-op and returning users would have kept the cached June schedule —
now `v25`. README had been damaged by my own earlier edit (a table cut mid-row
swallowed the following section); rewritten. `CLAUDE.md` pointed the skill at a
`.gemini` path that does not exist.

Deleting `web/` broke the user's phone shortcut — it pointed at the experimental
build. I had asked whether the QR was in use and read "1" as consent without
confirming what it meant. Regenerated both QR codes against the production URL.

**Code:**
- new `scripts/parse_firecrawl.py` (72 lines) — parses scraped search pages; requires
  a route line and a fare before accepting a row
- new `scripts/check_schedule.py` (239 lines) — live-vs-app comparison
- new `.github/workflows/schedule-watch.yml` (105 lines) — daily watcher
- rewrote `paper/grafikai.html` data arrays, both `paper/*_grafikas.md`, `README.md`,
  `CONTEXT.md`, `CLAUDE.md`, `.claude/skills/grafikai/SKILL.md`, `qr-codes.html`
- deleted `web/` (13 files), `scripts/scrape_juragiai.py`, `weekly-scraper.yml`,
  `test-scraper.yml`, `paper/kaunas-juragiai_2026-06-10.md`, and untracked
  `notused/`, `references/`, root `SKILL.md` (~2.4 MB)
- regenerated `qr.png`, `paper/qr-paper.png`; `sw.js` → `tvarkarastis-v25`
- 3 commits: `ea48dfe`, `4a6a0da`, `75420c5`

**Entry point:**
```bash
python scripts/check_schedule.py          # exit 0 = same, 1 = changed, 2 = could not check
gh workflow run schedule-watch.yml        # same check in CI
```

**Verified:** checker reports "no change (27 trips)" / "no change (29 trips)" against
live data, and detects an injected time change (exit 1). CI run 33630847837 completed
green and correctly opened no issue. QR codes decoded back to the production URL.

**Not measured:** whether the daily cron actually fires at 04:00 UTC — only the manual
dispatch has run. Whether `paper/README.md` still describes the removed `web/` split;
it was not opened this session. The Node 20 deprecation warning on
`actions/setup-node@v4` and `actions/upload-artifact@v4` was noted, not addressed.

### Session 2026-05-28 to 2026-06-10 — v6 release
- Accessibility update: larger text, stronger font-weight, improved spacing
- Visual continuity: full-page + header theme sync, no bottom seam
- Removed trip-card glow, kept route-colored borders
- Directory split: paper/ (production) + web/ (experimental, since removed)
- Wiki created: `wiki/bus-routes/` (7 articles)

### Key decisions
- Accessibility over decorative effects: bigger text/weight in all critical UI zones
- Single `new Date()` per `refresh()` cycle, passed as `now` to all subfunctions
- CSP meta: connect-src self + raw.githubusercontent.com (status fetch), object-src none, base-uri self
- SKILL.md and CLAUDE.md removed from git history via git filter-repo
- A failed schedule check must never report all-clear — the direction that failed
  may be the one that moved

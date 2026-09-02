# Grafikai — CONTEXT

## Status
Active. Timetable refreshed 2026-09-02 and a daily watcher now reports changes.
Cache `tvarkarastis-v25` live on GitHub Pages.

## Next Tasks
- (none — the watcher opens an issue when the schedule moves; act on that)

## Done Log

### 2026-09-02
- Timetable refreshed from live data; both directions verified against photos
- Daily `schedule-watch.yml` replaces the unread weekly PR workflow
- `parse_firecrawl.py` + `check_schedule.py` built and verified both ways
- `web/`, the Playwright scraper and ~2.4 MB of dead files removed
- QR codes regenerated against the production URL
- README, CONTEXT, CLAUDE.md, paper/README.md and the grafikai skill rewritten

## Key Facts
- Live: https://gerimantas.github.io/BusRoutes/paper/grafikai.html
- Repo: https://github.com/gerimantas/BusRoutes
- Route 106 plus intercity services stopping at Juragiai — single-file PWA
- Trips: Kaunas→Juragiai 27 (22 local + 5 intercity), Juragiai→Kaunas 29 (24 + 5)
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
- `.github/workflows/schedule-watch.yml` — daily watcher, opens an issue on change

## Archive

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
- CSP meta: connect-src none, object-src none, base-uri self
- SKILL.md and CLAUDE.md removed from git history via git filter-repo
- A failed schedule check must never report all-clear — the direction that failed
  may be the one that moved

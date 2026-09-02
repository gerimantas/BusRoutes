# Grafikai — CONTEXT

## Status
Active. Timetable refreshed 2026-09-02 and a daily watcher now reports changes.
Cache `tvarkarastis-v25` live on GitHub Pages.

## Next Tasks
- (none — the watcher opens an issue when the schedule moves; act on that)

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
- Timetable had been stale since an August change nobody was told about
- Refreshed both directions from autobusubilietai.lt via firecrawl, cross-checked
  against station board and stop sign photos
- MD records now carry arrival time, route, carrier and fare
- Built `parse_firecrawl.py` and `check_schedule.py`; verified the checker both
  reports no-change on correct data and detects an injected change
- Replaced the weekly PR workflow with `schedule-watch.yml`, which emails via issues
- Deleted `web/`, `scripts/scrape_juragiai.py`, `notused/`, `references/` and a stale
  root `SKILL.md` (~2.4 MB); removed the two old workflows
- Regenerated QR codes — the old pair predated the paper/web split
- Rewrote `.claude/skills/grafikai/SKILL.md` around the verified refresh procedure

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

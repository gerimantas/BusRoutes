# BusRoutes — Kaunas ↔ Juragiai

Mobile-optimized bus schedule PWA for travel between Kaunas and the Juragiai stop:
suburban route 106 plus the intercity services that stop at Juragiai.

Route 106 runs on to **Skriaudžiai**, its terminus for most trips. Only the trips
routed via Garliava still end at Jurginiškiai.

**Live:** https://gerimantas.github.io/BusRoutes/paper/grafikai.html

![QR code](qr.png)

Scan to open on a phone, or print [qr-codes.html](qr-codes.html).

---

## Schedule

The route 106 timetable in force since **2026-10-01** (weekend timetable from
2026-10-03), verified against the Kaunas district municipality PDFs on 2026-10-02.

| Direction | Trips |
|---|---|
| **Kaunas → Juragiai** | 25 |
| **Juragiai → Kaunas** | 27 |

Each direction has 24 workday and 10 weekend departures, 5 of them intercity;
daily trips count once.

Sources:

- **October timetable** — autobusubilietai.lt, checked 2026-09-26 for 10-01, 10-03
  and 10-04, then confirmed against 10-05, 10-10 and 10-11. Recorded in
  [paper/kaunas-juragiai_grafikas.md](paper/kaunas-juragiai_grafikas.md) and
  [paper/juragiai-kaunas_grafikas.md](paper/juragiai-kaunas_grafikas.md).
- **Municipality PDFs** — the
  [Kaunas district municipality PDFs](https://www.krs.lt/gyventojams/viesasis-transportas/priemiestiniai-autobusu-marsrutai/)
  in force from 10-01 (workdays) and 10-03 (weekends) match the app to the minute
  (checked 2026-10-02).

### Keeping it current

[.github/workflows/schedule-watch.yml](.github/workflows/schedule-watch.yml) runs
daily at 04:00 UTC:

- Compares a Thursday, a Saturday and a Sunday **at least 3 days ahead** against the
  app. Nearer dates can come back from the search incomplete.
- Compares the route 106 PDFs on krs.lt with the app's local trips: the PDF in force
  now, and every PDF announced for a later date before it starts.
- Opens an issue **only** when they differ, and keeps one open issue per change.
  The same difference on a later day adds nothing; a different one is added as a
  comment. A check that fails to complete opens a separate issue and never reports
  all-clear.
- Publishes its result (`ok`, `changed` or `failed`, with the time) to the `status`
  branch. The app shows it to the rider, see [Last check line](#last-check-line).

The watcher only reports. It never edits the app, because a scrape can return a
partial list. To apply a change, open the project in Claude Code and say
`atnaujink grafikus`.

Requires the `FIRECRAWL_API_KEY` repository secret.

---

## Features

### Last check line
Under the tabs: `Tikrinta 09-26 19:15 — grafikas sutampa`, the last watcher run and
its result, fetched from the `status` branch every 30 minutes while the app is open.
It turns red when the check found a change, failed, or is older than 48 hours,
which means the watcher stopped. Offline, the app shows the last result it
received.

### Dated timetable switch
A timetable announced for a future date ships before that date. The old arrays
stay in the app as `dataKaunasBefore` / `dataJurginiskaiBefore` until
`SWITCH_DATE`, and the app picks one by the phone's date every minute. The watcher
reads `SWITCH_DATE` too, so a pending switch never shows up as a change. Both are
removed once the date has passed; no switch is pending now.

### Dual route colour palette
Two independent themes. Every element in a card — time, day labels, badges, borders,
side accents, header controls — uses its route's palette:

- **Kaunas → Juragiai:** blue (`#82cbff`)
- **Juragiai → Kaunas:** amber (`#ffb347`)

Switching direction fades all header colours, borders and shadows over 0.3s.

### Compact day labels
Cards show only the days a trip runs, as spaced numbers: `1 2 3 4 5` (workdays),
`1 2 3 4 5 6 7` (daily), `6 7` (weekends). Today carries a route-coloured underline.

### Smart filter
- **On** — today's trips only (`1-5` / `6-7` / `ND`)
- **Off** — the full week (`1-7`), with a crimson warning aura on the header

### Geolocation auto-routing
Haversine distance to Kaunas bus station and to Juragiai, computed on load, selects
the direction tab.

### Vibration alert
Double pulse (`200ms, 100ms, 200ms`) when 2 minutes or less remain to the next departure.

### Holiday engine
Gauss Easter algorithm plus the 14 statutory Lithuanian holidays (DK 160 str.),
computed for any year — no manual updates. All holidays run the weekend schedule.
The day indicator switches to `"N - ND"` (e.g. `"4 - ND"`).

### Accessibility
Large type and heavy weights (`800`) on clock, tabs, badges and time-left labels;
generous spacing on status lines.

### Performance
`precalculateTripMinutes()` converts every trip time once on load. One `new Date()`
per render cycle, passed down to every function. The Page Visibility API pauses the
timer while the tab is hidden.

### PWA
Installs to Android and iOS home screens, works fully offline, updates through the
service worker. Cache key lives in [sw.js](sw.js) line 1 and must be bumped on every
deploy that touches the app.

---

## Directory structure

### `paper/` — production

| File | Purpose |
|---|---|
| `grafikai.html` | The PWA — all JS, CSS and data in one file |
| `kaunas-juragiai_grafikas.md` | Schedule record: Kaunas → Juragiai |
| `juragiai-kaunas_grafikas.md` | Schedule record: Juragiai → Kaunas |
| `*_grfk_*.jpg`, `Kaunas-Juragiai_*.jpg` | Station board and stop sign photos |
| `qr-paper.png` | QR code for the production URL |
| `README.md` | Notes for this directory |

### `scripts/` — schedule tooling

| File | Purpose |
|---|---|
| `check_schedule.py` | Compares the live timetable against the app; exit 1 = changed, 2 = could not check |
| `parse_firecrawl.py` | Parses scraped search pages into a trip table |
| `krs_pdf.py` | Finds and reads the route 106 PDFs on krs.lt |

Offline tests for all three live in `tests/` with real downloaded pages and PDFs as
fixtures: `python -m unittest discover -s tests -v`. GitHub runs them
([tests.yml](.github/workflows/tests.yml)) whenever the scripts, tests or app data change.

Data comes from `autobusubilietai.lt` through the firecrawl CLI, scraped for a
workday, a Saturday and a Sunday so periodicity follows from which days a trip
appears on. A row without a route line and a fare is a page marker, not a departure,
and is discarded — see [.claude/skills/grafikai/SKILL.md](.claude/skills/grafikai/SKILL.md).

### Root

| File | Purpose |
|---|---|
| `sw.js` | Cache-first service worker (offline support) |
| `manifest.json` | PWA install config — `start_url` points at `paper/grafikai.html` |
| `icon-192.png`, `icon-512.png` | PWA icons |
| `qr.png` | QR code for the production URL |
| `qr-codes.html` | Printable QR page |

### `status` branch

Holds a single `status.json` (`{"checked": "<UTC time>", "result": "ok"}`), which
the watcher force-pushes on every run. It is not deployed. The app reads it from
`raw.githubusercontent.com`.

---

## Update & deploy

```bash
# 1. Edit paper/grafikai.html
# 2. Bump the cache version — read the current one first
sed -n '1p' sw.js

git add paper/grafikai.html paper/*_grafikas.md sw.js
git commit -m "..."
git push
# GitHub Pages publishes in about a minute
gh api repos/gerimantas/BusRoutes/pages --jq '.status'   # "built" = live
```

Skipping the cache bump leaves returning visitors on the old schedule.

---

## Removed

`web/` and `scripts/scrape_juragiai.py` were deleted on 2026-09-02. That Playwright
scraper counted round-hour markers on the search page as departures, so its intercity
output listed 20 trips where 5 exist, and the experimental build it fed displayed
departures that do not run. Two weekly pull requests it filed against `web/` went
unreviewed, which is how an August timetable change stayed invisible.

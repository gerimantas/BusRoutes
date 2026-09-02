# BusRoutes — Kaunas ↔ Juragiai / Jurginiškiai

Mobile-optimized bus schedule PWA for the Kaunas ↔ Juragiai / Jurginiškiai suburban
line (route 106 plus the intercity services that stop at Juragiai).

**Live:** https://gerimantas.github.io/BusRoutes/paper/grafikai.html

![QR code](qr.png)

Scan to open on a phone, or print [qr-codes.html](qr-codes.html).

---

## Schedule

| Direction | Workdays | Weekends | Intercity | Total |
|---|---|---|---|---|
| **Kaunas → Juragiai** | 24 | 10 | 5 | 27 |
| **Juragiai → Kaunas** | 24 | 10 | 5 | 29 |

Workday and weekend columns include the all-day trips, so they overlap; the total
is the number of distinct entries.

Source: [paper/kaunas-juragiai_grafikas.md](paper/kaunas-juragiai_grafikas.md) and
[paper/juragiai-kaunas_grafikas.md](paper/juragiai-kaunas_grafikas.md), verified
2026-09-02 against autobusubilietai.lt and station photos.

### Keeping it current

[.github/workflows/schedule-watch.yml](.github/workflows/schedule-watch.yml) runs
daily at 04:00 UTC. It compares the live timetable against the app and opens an
issue **only** when they differ — a quiet day sends nothing. A check that fails to
complete opens a separate issue rather than reporting all-clear.

Requires the `FIRECRAWL_API_KEY` repository secret.

---

## Features

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

---

## Update & deploy

```bash
# 1. Edit paper/grafikai.html
# 2. Bump the cache version — read the current one first
sed -n '1p' sw.js

git add paper/grafikai.html sw.js
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

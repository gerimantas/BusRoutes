# Grafikai — CONTEXT

## Purpose
Suburban bus schedule Kaunas ↔ Juragiai / Jurginiškiai (Route 106) — single-file PWA optimized for mobile.

## URL & Repository
- **Live App:** https://gerimantas.github.io/BusRoutes/paper/grafikai.html
- **Repository:** https://github.com/gerimantas/BusRoutes

## Technical Status
- **Current Version:** **v6 (Accessibility & Visual Continuity Update)**
- **Service Worker Cache:** **`tvarkarastis-v23`** (bump in `sw.js` on every HTML change)
- **Directory Structure:** **`paper/` (production) + `web/` (experimental web scraper)**

---

## Complete Feature Set

### 1. Navigation & Route Identifiers
- **Dual Tab Routing:** Kaunas → Juragiai (blue theme) and Juragiai → Kaunas (amber theme).
- **Header + Body Themes:** Fixed top bar and full page swap `theme-kaunas` / `theme-jurginiskai` with 0.3s fade-transition:
  - **Kaunas:** deep blue gradient and inset side/top glow
  - **Juragiai:** deep amber gradient and inset side/top glow
  - No header bottom border/glow seam.
- **Geolocation Auto-Select:** Haversine formula → auto-switches tab on load. Locked after manual interaction.

### 2. Unified Route Color Palette (v6)
All card elements use route palette — no global accent overrides, with card glow removed for cleaner readability:

| Element | Kaunas (blue) | Juragiai (amber) |
|---------|--------------|-----------------|
| `.time` base | `#82cbff` | `#ffb347` |
| `.time` upcoming | `#7ec8ff` | `#ff9d5c` |
| `.time` next (ARTIMIAUSIAS) | `var(--accent-go)` green `!important` | green `!important` |
| `.time-left` | `rgba(126,200,255,0.7)` | `rgba(245,158,11,0.7)` |
| `.day-label` inactive | `rgba(126,200,255,0.70)` | `rgba(245,158,11,0.70)` |
| `.day-label.today` | `#82cbff` + underline | `#ffb347` + underline |
| `.platform-badge` | `#82cbff` + tinted bg | `#ffb347` + tinted bg |
| `.stop-badge` | `#82cbff` + tinted bg | `#ffb347` + tinted bg |
| Side border (`platform-12/6/tm`) | `#82cbff` / `rgba(126,200,255,0.5)` | `#ffb347` |
| `#filter-btn` | `#82cbff` + tinted bg | `#ffb347` + tinted bg |
| `#clock-day` | `#82cbff` + tinted bg | `#ffb347` + tinted bg |

### 3. Compact Day Label System (v5)
Trip cards show only days the trip runs, as plain numbers:
- `1 2 3 4 5` — workdays only
- `1 2 3 4 5 6 7` — every day
- `6 7` — weekends only

Today's day: route-colored `border-bottom: 2px solid`. Inactive days at 70% opacity.
Font: `18px`, bold. `renderDays(days, now)` — replaces old `renderDots()`.

### 4. Unified Header Bar (v6)
`#filter-btn` and `#clock-day` share identical style:
- `height: 36px`, `border-radius: 8px`, `font-size: 16px`
- `border: 1px solid` in route palette color, tinted bg (7% opacity)
- Header `padding: 10px 16px`
- `#clock-day` auto-width with padding (fits holiday text e.g. `"4 - ND"`)

### 5. Accessibility Typography (v6)
- Key texts increased and emboldened for low-vision users:
  - larger clock, tabs, trip time, day labels, and info banners
  - stronger `font-weight: 800` on primary controls and status labels
- Spacing improvements for readability:
  - increased line-height and vertical paddings for status rows and banners
  - improved `ARTIMIAUSIAS` label spacing and stable placement under fixed header

### 6. Holiday Display (v5)
- **Clock bar** (`#clock-day`): shows `"N - ND"` format on public holidays
- **Holiday banner** (`#holiday-banner`): full holiday name in red
- Style: red border, red text, red tinted bg

### 7. Time-Keeping & Alerts
- Font sizes: `.time` `30px` base, `46px` upcoming. `.time-left` `17px` base, `21px` upcoming.
- Tactile vibration: `[200, 100, 200]` when ≤ 2 min to nearest departure.
- Buffer-aware next trip: green `!important` on `.trip.next .time`, emerald border, `ARTIMIAUSIAS` label.
- Page Visibility API: pauses timer when tab hidden, resumes on focus.

### 8. Filters
- Filter ON: shows `1-5` / `6-7` / `ND` — only today's trips.
- Filter OFF (`1-7`): shows all trips. Header → deep crimson warning state.
- `filterBtnLabel(now, todayIdx)` — receives `now` from caller, never calls `new Date()` internally.

### 9. Automated Calendar Engine
Gauss Easter algorithm (any year), 14 statutory LT holidays, auto year-transition.

### 10. Performance
- `precalculateTripMinutes()` pre-converts all times to minutes on load.
- Single `new Date()` per `refresh()` cycle — passed as `now` to all subfunctions.

### 11. Security
- `Content-Security-Policy` meta: `connect-src 'none'`, `object-src 'none'`, `base-uri 'self'`
- `.gitignore`: excludes `SKILL.md`, `CLAUDE.md`, `qr.png`, `notused/`
- `SKILL.md` and `CLAUDE.md` removed from full git history via `git filter-repo`

---

## Directory Structure (2026-06-10)

### `paper/` — Production Version (Manual Curation)
Hand-maintained schedule data from PDF timetables and photos of bus station displays. Deployed to GitHub Pages.

**Files:**
- `grafikai.html` — **Production PWA** (live at `/paper/grafikai.html`)
- `kaunas-juragiai_grafikas.md` — Canonical schedule: Kaunas → Juragiai
- `juragiai-kaunas_grafikas.md` — Canonical schedule: Juragiai → Kaunas
- `kaunas-juragiai_YYYY-MM-DD.md` — Dated version snapshots (change history)
- `Kaunas-Juragiai_*.jpg` — Source photos from bus station
- `qr-paper.png` — QR code for production URL
- `README.md` — Documentation for paper/ directory

### `web/` — Automated Web Scraper (Experimental)
Fully automated schedule extraction from autobusubilietai.lt with multi-day periodicity detection (WORKDAYS / WEEKEND / ALL_DAYS).

**Files:**
- `grafikai-web.html` — Experimental test version with web-scraped data
- `106_kaunas-juragiai_pilnas.md` — 106 route: Kaunas → Juragiai
- `106_juragiai-kaunas_pilnas.md` — 106 route: Juragiai → Kaunas
- `tarpmiestiniai_kaunas-juragiai_pilnas.md` — Intercity via Juragiai (to Marijampolė)
- `tarpmiestiniai_juragiai-kaunas_pilnas.md` — Intercity via Juragiai (from Marijampolė)
- `*_web.md` — Other experimental routes
- `qr-web.png` — QR code for experimental URL
- `README.md` — Documentation for web/ directory

**Scraper:** `notused/scrape_juragiai.py` (Playwright, 6s page wait, deduplication, periodicity auto-detection)

---

## Latest Decisions (2026-05-28 → 2026-06-10)
1. Accessibility over decorative effects: increased text size/weight and spacing in all critical UI zones.
2. Visual continuity: synchronized full-page and header theme atmosphere, without bottom seam under header.
3. Cleaner cards: removed trip-card glow while keeping readable, route-colored borders.
6. **QR codes:** Generated QR codes for both versions (`qr.png`, `paper/qr-paper.png`, `web/qr-web.png`) + printable HTML page (`qr-codes.html`).
4. **Directory reorganization:** Split into `paper/` (production, manual) and `web/` (experimental, automated scraper).
5. **Web scraper workflow:** Built automated extraction pipeline with periodicity detection — potential future replacement for manual photo uploads.

---

## Directory Structure

### Production (`paper/`)
| File | Purpose |
|---|---|
| `grafikai.html` | Single-file PWA — deployed to GitHub Pages |
| `kaunas-juragiai_grafikas.md` | Canonical schedule source: Kaunas → Juragiai |
| `juragiai-kaunas_grafikas.md` | Canonical schedule source: Juragiai → Kaunas |
| `kaunas-juragiai_YYYY-MM-DD.md` | Dated snapshots (version history) |
| `Kaunas-Juragiai_*.jpg` | Source photos from bus station |
| `qr-paper.png` | QR code for production URL |
| `README.md` | Documentation |

### Experimental (`web/`)
| File | Purpose |
|---|---|
| `grafikai-web.html` | Experimental PWA with web-scraped data |
| `manifest-web.json` | Separate PWA manifest (start_url = ./grafikai-web.html) |
| `106_*_pilnas.md` | Web-scraped 106 route data |
| `tarpmiestiniai_*_pilnas.md` | Web-scraped intercity routes |
| `qr-web.png` | QR code for experimental URL |
| `README.md` | Documentation |

### Core (Root)
| File | Purpose |
|---|---|
| `sw.js` | Cache-first Service Worker — current: `tvarkarastis-v23` |
| `manifest.json` | PWA manifest (points to `paper/grafikai.html`) |
| `icon-192.png` / `icon-512.png` | PWA icons |
| `qr.png` | Main QR code (production) |
| `qr-codes.html` | Visual display of QR codes |

---

## Deployment & Updates
1. Edit `paper/grafikai.html`.
2. Bump `CACHE` version in `sw.js`.
3. `git add paper/grafikai.html sw.js && git commit -m "..." && git push`
4. GitHub Pages deploys in ~1 min.
5. Verify: `gh api repos/gerimantas/BusRoutes/pages --jq '.status'`

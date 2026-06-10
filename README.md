# BusRoutes — Kaunas ↔ Juragiai / Jurginiškiai

Mobile-optimized bus schedule PWA for the Kaunas ↔ Juragiai / Jurginiškiai (Route 106) suburban bus line.

**Live application:** https://gerimantas.github.io/BusRoutes/paper/grafikai.html

### Quick Access QR Codes
Scan to open on your mobile device:

| Production | Experimental |
|---|---|
| ![Production QR](qr.png) | ![Experimental QR](web/qr-web.png) |
| [paper/grafikai.html](https://gerimantas.github.io/BusRoutes/paper/grafikai.html) | [web/grafikai-web.html](https://gerimantas.github.io/BusRoutes/web/grafikai-web.html) |
| Manual curation | Automated scraper |

---

## Features

### Dual Route Color Palette
Two fully independent visual themes — every element in the card (time, day labels, badges, borders, side accents, header controls) uses the route palette:
- **Kaunas → Juragiai:** Blue palette (`#82cbff`) — deep blue background with blue neon glow
- **Juragiai → Kaunas:** Amber palette (`#ffb347`) — deep amber background with amber neon glow

Switching direction triggers a **0.3s fade transition** across all header colors, borders, and shadows.

### Accessibility-First Typography (v6)
Text sizes and weights were increased across the app for better readability in low-vision usage scenarios:
- Larger clock, tab, badge, and time-left labels
- Stronger font weights (`800`) on key labels and controls
- Improved spacing/line-height for status lines (`ARTIMIAUSIAS`, holiday and no-more-trip banners)

### Unified Header + Page Atmosphere (v6)
- Header and page now share the same theme direction (blue/amber) for a continuous visual surface.
- Header no longer uses a bottom border/glow seam.
- Trip cards keep clear borders but **no extra glow effects** on cards/time text.

### Compact Day Labels
Trip cards show only the days the trip runs — as plain, spaced numbers:
- `1 2 3 4 5` — workdays
- `1 2 3 4 5 6 7` — every day
- `6 7` — weekends

Today's day is marked with a route-colored bottom underline.

### Smart Header Bar
Filter button and day indicator share identical style — same `36px` height, `8px` border-radius, route-colored border and tinted background. On public holidays, the day indicator shows `"N - ND"` format (e.g. `"4 - ND"`).

### Geolocation Auto-Routing
Haversine formula calculates distance to Kaunas Bus Station and Juragiai on load — automatically activates the correct direction tab.

### Tactile Vibration Alerts
Device double-pulses (`[200ms, 100ms, 200ms]`) when ≤ 2 minutes remain to the nearest departure.

### Smart Filter
- **ON:** shows only today's trips (`1-5` / `6-7` / `ND`)
- **OFF:** shows all 7-day schedule (`1-7`) with crimson warning header aura

### Zero-Maintenance Holiday Engine
Gauss Easter algorithm + 14 statutory Lithuanian holidays (DK 160 str.) — auto-calculates for any future year. No manual updates needed.

### Performance
- `precalculateTripMinutes()` pre-converts all trip times on load
- Single `new Date()` per render cycle
- Page Visibility API pauses timer when tab is hidden

### PWA
Installs to Android/iOS home screens, works 100% offline, auto-updates via service worker.

Current cache key: `tvarkarastis-v23`.

---

## Schedule

| Route | Workdays | Weekends |
|---|---|---|
| **Kaunas → Juragiai** | 20 trips | 6 trips |
| **Juragiai → Kaunas** | 21 trips | 6 trips |

*Source: `paper/kaunas-juragiai_grafikas.md`, `paper/juragiai-kaunas_grafikas.md` (verified 2026-06-10)*

---

## Update & Deploy

```powershell
# 1. Edit paper/grafikai.html, bump CACHE version in sw.js
git add paper/grafikai.html sw.js
git commit -m "update: describe changes"
git push
# GitHub Pages deploys in ~1 min
```

---

## Directory Structure

### `paper/` — Production Version (Manual Updates)
Hand-curated schedule data from PDF timetables and photos of bus station displays.

| File | Purpose |
|---|---|
| `grafikai.html` | **Production PWA** — deployed to GitHub Pages |
| `kaunas-juragiai_grafikas.md` | Canonical schedule source: Kaunas → Juragiai |
| `juragiai-kaunas_grafikas.md` | Canonical schedule source: Juragiai → Kaunas |
| `kaunas-juragiai_YYYY-MM-DD.md` | Dated snapshots preserving schedule change history |
| `Kaunas-Juragiai_*.jpg` | Source photos of platform displays |
| `qr-paper.png` | QR code for production URL |
| `README.md` | Documentation for paper/ directory |

### `web/` — Automated Web Scraper Data (Experimental)
Fully automated schedule extraction from autobusubilietai.lt with periodicity detection.

| File | Purpose |
|---|---|
| `grafikai-web.html` | **Experimental HTML** — for real-world testing |
| `manifest-web.json` | **Separate PWA manifest** — start_url points to web version |
| `106_kaunas-juragiai_pilnas.md` | Web-scraped 106 route: Kaunas → Juragiai |
| `106_juragiai-kaunas_pilnas.md` | Web-scraped 106 route: Juragiai → Kaunas |
| `tarpmiestiniai_kaunas-juragiai_pilnas.md` | Intercity routes via Juragiai (Kaunas → Marijampolė) |
| `tarpmiestiniai_juragiai-kaunas_pilnas.md` | Intercity routes via Juragiai (Marijampolė → Kaunas) |
| `*_web.md` | Other experimental scraped routes |
| `qr-web.png` | QR code for experimental URL |
| `README.md` | Documentation for web/ directory |

**Scraper:** `scripts/scrape_juragiai.py` — Playwright-based tool that compares workday/weekend trips to auto-determine periodicity (WORKDAYS / WEEKEND / ALL_DAYS).

---

## Core Files (Root)

| File | Purpose |
|---|---|
| `sw.js` | Cache-first Service Worker (offline
| `qr.png` | Main QR code (points to production) |
| `qr-codes.html` | Visual display of both QR codes (printable) | support) |
| `manifest.json` | PWA install configuration (points to `paper/grafikai.html`) |
| `icon-192.png` / `icon-512.png` | PWA icons |

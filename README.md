# BusRoutes — Kaunas ↔ Juragiai

Mobile-optimized bus schedule PWA for Kaunas ↔ Juragiai / Jurginiškiai route.

**Live app:** https://gerimantas.github.io/BusRoutes/grafikai.html

## Features

- Live countdown to each departure (updates every minute, aligned to clock)
- Nearest departure highlighted in green
- Last trip of the day warning banner
- Upcoming trips shown at 2× size
- Day-of-week dots per trip — today highlighted
- Public holidays treated as weekend (schedule switches automatically)
- Platform badges (5, 6, 12, 106, tarpmiestinis)
- Works offline (PWA, installable to home screen)

## Schedule

| Route | Trips/day (workdays) | Trips/day (weekend) |
|-------|---------------------|---------------------|
| Kaunas → Juragiai | 20 | 6 |
| Juragiai → Kaunas | 21 | 6 |

Source PDFs: `kaunas-juragiai_0522.pdf`, `juragiai-kaunas_0522.pdf` (2026-05-22)

## Install on mobile

1. Open https://gerimantas.github.io/BusRoutes/grafikai.html in Chrome/Safari
2. **Android:** menu → "Add to Home screen"
3. **iOS:** Share → "Add to Home Screen"

App works offline after first load.

## Updating the schedule

1. Edit `grafikai.html` — `dataKaunas` / `dataJurginiskai` arrays
2. Bump cache version in `sw.js`: `const CACHE = 'tvarkarastis-vX'`
3. Push — GitHub Pages deploys in ~1 min, phones update automatically

## Holiday list

Fixed dates in `grafikai.html` → `HOLIDAYS` array (MM-DD format).  
Easter must be updated yearly:
- 2026: `04-05`, `04-06`
- 2027: update before season

## Files

| File | Purpose |
|------|---------|
| `grafikai.html` | Main app — all logic and styles |
| `manifest.json` | PWA manifest |
| `sw.js` | Service worker — offline cache |
| `icon-192.png` / `icon-512.png` | PWA icons |
| `kaunas-juragiai_grafikas.md` | Schedule source (Kaunas → Juragiai) |
| `juragiai-kaunas_grafikas.md` | Schedule source (Juragiai → Kaunas) |

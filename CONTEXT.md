# Grafikai — CONTEXT

## Purpose
Bus schedule Kaunas ↔ Juragiai — single HTML file, optimized for mobile.

## Files
- `grafikai.html` — main file, opened directly in browser
- `Kaunas-JURAGIAI-Jurginiskiai.jpg` — source: Kaunas → Juragiai
- `Jurginiskai-JURAGIAI-Kaunas.jpg` — source: Juragiai → Kaunas

## Status
v2 — fully working, mobile-responsive.

## Features
- 2 tabs: Kaunas→Juragiai (blue) / Juragiai→Kaunas (orange) — fixed header, sticky on scroll
- Live clock with day-of-week dots (1–7), active day highlighted with neon yellow border
- Sat/Sun dots always orange; holidays shown in red with "ND" label
- Countdown to each departure (recalculates every minute)
- Nearest departure — neon green border
- Upcoming trips 2× larger font; past trips shown with elapsed time
- Sat/Sun trips — orange color
- Public holidays treated as Saturday (weekend schedule applies)
- 2-row trip card: row1 = time + day dots, row2 = stop badge + time remaining
- No dimmed text — all labels at full visibility

## Holiday list
Fixed dates in `HOLIDAYS` array (MM-DD). Velykos (Easter) must be updated yearly:
- 2025: 04-20, 04-21
- 2026: 04-05, 04-06

## Possible improvements
- Seasonal schedules (school holidays, summer/winter)
- PWA (offline support)
- Auto-update Easter dates

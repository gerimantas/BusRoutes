# BusRoutes — Kaunas ↔ Juragiai / Jurginiškiai

Mobile-optimized bus schedule PWA for the Kaunas ↔ Juragiai / Jurginiškiai (Route 106) suburban bus line.

**Live application:** https://gerimantas.github.io/BusRoutes/grafikai.html

---

## Features

### Dual Route Color Palette
Two fully independent visual themes — every element in the card (time, day labels, badges, borders, side accents, header controls) uses the route palette:
- **Kaunas → Juragiai:** Blue palette (`#82cbff`) — deep blue background with blue neon glow
- **Juragiai → Kaunas:** Amber palette (`#ffb347`) — deep amber background with amber neon glow

Switching direction triggers a **0.3s fade transition** across all header colors, borders, and shadows.

### Compact Day Labels
Trip cards show only the days the trip runs — as plain, spaced numbers:
- `1 2 3 4 5` — workdays
- `1 2 3 4 5 6 7` — every day
- `6 7` — weekends

Today's day is marked with a route-colored bottom underline.

### Smart Header Bar
Filter button and day indicator share identical style — same `32px` height, `8px` border-radius, route-colored border and tinted background. On public holidays, the day indicator shows `"N - ND"` format (e.g. `"4 - ND"`).

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

---

## Schedule

| Route | Workdays | Weekends |
|---|---|---|
| **Kaunas → Juragiai** | 20 trips | 6 trips |
| **Juragiai → Kaunas** | 21 trips | 6 trips |

*Source: `kaunas-juragiai_grafikas.md`, `juragiai-kaunas_grafikas.md` (verified 2026-05-22)*

---

## Update & Deploy

```powershell
# 1. Edit grafikai.html, bump CACHE version in sw.js
git add grafikai.html sw.js
git commit -m "update: describe changes"
git push
# GitHub Pages deploys in ~1 min
```

---

## Files

| File | Purpose |
|---|---|
| `grafikai.html` | Single-file PWA — all HTML, CSS, JS, schedule data |
| `sw.js` | Cache-first Service Worker (offline support) |
| `manifest.json` | PWA install configuration |
| `icon-192.png` / `icon-512.png` | PWA icons |
| `kaunas-juragiai_grafikas.md` | Canonical schedule source: Kaunas → Juragiai |
| `juragiai-kaunas_grafikas.md` | Canonical schedule source: Juragiai → Kaunas |

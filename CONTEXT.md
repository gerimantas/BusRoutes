# Grafikai — CONTEXT

## Purpose
Bus schedule Kaunas ↔ Juragiai — single HTML file PWA, optimized for mobile.

## Live URL
https://gerimantas.github.io/BusRoutes/grafikai.html

## Repo
https://github.com/gerimantas/BusRoutes

## Files
- `grafikai.html` — main app, all logic and styles
- `manifest.json` — PWA manifest
- `sw.js` — service worker, offline cache-first (bump `CACHE` version on each deploy)
- `icon-192.png`, `icon-512.png` — PWA icons
- `kaunas-juragiai_grafikas.md` — schedule source: Kaunas → Juragiai
- `juragiai-kaunas_grafikas.md` — schedule source: Juragiai → Kaunas

## Status
v3 — PWA, fully working, deployed to GitHub Pages.

## Features
- 2 tabs: Kaunas→Juragiai (blue) / Juragiai→Kaunas (orange)
- Fixed header: [Filtro mygtukas] [Laikas] [Dienos badge (Pr/An/Tr/Kt/Pn/Š/S)]
- Day filter toggle: Pr–Pn laikai / Š–S laikai (ON, default) → Visi laikai (OFF)
  - OFF: header tampa tamsiai raudonas su raudonu border
  - Praėję laikai visada rodomi (pritempti) — aktualūs sekančiai dienai
- Live clock, seconds-accurate countdown
- Nearest departure — neon green border + "ARTIMIAUSIAS" label ant viršutinio borderio
- Auto-scroll to nearest trip on load and on tab switch
- Upcoming trips 2× larger font; past trips show elapsed time
- Last trip of day warning banner (orange)
- No more trips today banner (yellow)
- Public holiday banner — shows holiday name in red
- Sat/Sun trips — orange color; platform badges (5a, 6a, 12a, 106, tm) neon spalvos
- All UI text uppercase
- PWA: installable, works offline after first load

## Schedule data
Source PDFs: `kaunas-juragiai_0522.pdf`, `juragiai-kaunas_0522.pdf` (verified 2026-05-22)
3 periodicities: `12345` = Pr–Pn, `ŠS` = Š–S, `1234567` = visos

## Holiday logic
- 14 public holidays per DK 160 str.
- Easter (Velykos + pirmadienis) auto-calculated via Gauss algorithm each year
- All holidays treated as weekend schedule (ŠS)
- Holiday name shown in red banner in header

## Update workflow
1. Edit `grafikai.html` — `dataKaunas` / `dataJurginiskai`
2. Bump `CACHE` version in `sw.js`: `tvarkarastis-v1` → `v2` etc.
3. `git add . && git commit -m "..." && git push`
4. GitHub Pages deploys in ~1 min, phones update automatically

## SW Cache
Current: `tvarkarastis-v3` — bump on every deploy that changes `grafikai.html`

## Possible improvements
- Geolocation — auto-select tab by user location
- Vibration alert when ≤ 2 min to departure
- Share button for next departure
- Seasonal schedules (school holidays, summer/winter)

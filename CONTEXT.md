# Grafikai — CONTEXT

## Status
Paused. v6 live on GitHub Pages. No active work.

## Next Tasks
- (none — project stable, update only when schedule changes)

## Key Facts
- Live: https://gerimantas.github.io/BusRoutes/paper/grafikai.html
- Repo: https://github.com/gerimantas/BusRoutes
- Route 106: Kaunas ↔ Juragiai / Jurginiškiai — single-file PWA
- Current version: v6 (Accessibility & Visual Continuity)
- Service Worker cache: `tvarkarastis-v23` — bump in `sw.js` on every HTML change
- Structure: `paper/` (production, manual) + `web/` (experimental scraper)

### Deploy workflow
1. Edit `paper/grafikai.html`
2. Bump `CACHE` in `sw.js`
3. `git add paper/grafikai.html sw.js && git commit -m "..." && git push`
4. Verify: `gh api repos/gerimantas/BusRoutes/pages --jq '.status'`

## Dead Ends
- (none recorded)

## Files
- `paper/grafikai.html` — production PWA
- `paper/kaunas-juragiai_grafikas.md` — canonical schedule Kaunas→Juragiai
- `paper/juragiai-kaunas_grafikas.md` — canonical schedule Juragiai→Kaunas
- `sw.js` — Service Worker (cache-first, bump version on each release)
- `manifest.json` — PWA manifest
- `web/grafikai-web.html` — experimental scraper-fed version
- `notused/scrape_juragiai.py` — Playwright scraper (periodicity auto-detection)

## Archive

### Session 2026-05-28 to 2026-06-10 — v6 release
- Accessibility update: larger text, stronger font-weight, improved spacing
- Visual continuity: full-page + header theme sync, no bottom seam
- Removed trip-card glow, kept route-colored borders
- Directory split: paper/ (production) + web/ (experimental)
- QR codes generated for both versions
- Web scraper pipeline built with periodicity detection
- Wiki created: `wiki/bus-routes/` (7 articles)

### Key decisions
- Accessibility over decorative effects: bigger text/weight in all critical UI zones
- Single new Date() per refresh() cycle, passed as `now` to all subfunctions
- CSP meta: connect-src none, object-src none, base-uri self
- SKILL.md and CLAUDE.md removed from git history via git filter-repo

# Web — Experimental Version

## Experimental Test Version
**Test URL:** https://gerimantas.github.io/BusRoutes/web/grafikai-web.html

⚠️ **Experimental** — This version uses automated web scraper data for testing purposes.

### QR Code
Scan to test the web-scraped schedule on your mobile device:

![QR Code](qr-web.png)

---

## Files
- `grafikai-web.html` — Experimental test version with web-scraped data
- `106_kaunas-juragiai_pilnas.md` — 106 route: Kaunas → Juragiai (23 trips)
- `106_juragiai-kaunas_pilnas.md` — 106 route: Juragiai → Kaunas (23 trips)
- `tarpmiestiniai_kaunas-juragiai_pilnas.md` — Intercity routes via Juragiai
- `tarpmiestiniai_juragiai-kaunas_pilnas.md` — Intercity routes via Juragiai
- `*_web.md` — Other experimental scraped routes
- `qr-web.png` — QR code for this version

## Automated Workflow

### Data Source
All data is automatically extracted from **autobusubilietai.lt** using the web scraper:
- `../notused/scrape_juragiai.py`

### Scraper Features
- **Playwright-based browser automation**
- **Multi-day periodicity detection** (compares Thursday/Saturday/Sunday)
- **Automatic categorization:** WORKDAYS / WEEKEND / ALL_DAYS
- **Deduplication** by (departure time, carrier, price)
- **Platform assignment:** 106 for local routes, tm for intercity
- **Full 24-hour schedule** extraction (not just future trips)

### Testing Purpose
Compare web-scraped data accuracy against actual bus departures to evaluate:
1. Schedule completeness (all trips present?)
2. Periodicity accuracy (workday/weekend detection correct?)
3. Platform assignments (106 vs tarpmiestinis)
4. Update frequency requirements

If proven reliable, this could replace manual photo/PDF workflow entirely.

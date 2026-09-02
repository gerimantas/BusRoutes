# Paper — Production Version

**Live:** https://gerimantas.github.io/BusRoutes/paper/grafikai.html

![QR Code](qr-paper.png)

---

## Files

- `grafikai.html` — the PWA deployed to GitHub Pages; all JS, CSS and data in one file
- `kaunas-juragiai_grafikas.md` — schedule record: Kaunas → Juragiai
- `juragiai-kaunas_grafikas.md` — schedule record: Juragiai → Kaunas
- `*_grfk_*.jpg`, `Kaunas-Juragiai_*.jpg` — station board and stop sign photos
- `qr-paper.png` — QR code for the production URL

## Where the data comes from

`autobusubilietai.lt`, scraped through the firecrawl CLI for a workday, a Saturday
and a Sunday, so periodicity follows from which of those days a trip appears on.
`scripts/parse_firecrawl.py` turns the scraped pages into a trip table.

The `*_grafikas.md` files are a **record of the last refresh, not a live source** —
each carries the date it was verified. To answer "did the schedule change?", run
`scripts/check_schedule.py`, which fetches live data and compares.

Photos are a cross-check, not the source. A station board photo is cropped and a
stop sign omits route information, so where a photo and the live data disagree, the
live data wins.

Full procedure: `.claude/skills/grafikai/SKILL.md`

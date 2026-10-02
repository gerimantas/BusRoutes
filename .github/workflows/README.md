# Workflows

## schedule-watch.yml

Runs daily at 04:00 UTC (07:00 Vilnius summer, 06:00 winter) and on manual dispatch.

Compares the departure times in `paper/grafikai.html` with two sources, in order
of priority:

1. **autobusubilietai.lt (primary)** — a workday, a Saturday and a Sunday at least
   3 days ahead. Its result is what the app shows riders ("Tikrinta …"):
   - **no change** — finishes silently, sends nothing
   - **changed** — opens a "Schedule changed" issue; GitHub emails it to the owner
   - **check failed** — opens a "Schedule Watch could not run" issue, unless one is
     already open. A failed check never reports all-clear.
2. **krs.lt route 106 PDFs (secondary)** — fetched through firecrawl from a
   Lithuanian IP, since krs.lt blocks GitHub's runners. A difference, a failed
   check or a route 106 PDF with an unreadable file name opens a "krs.lt PDFs …"
   issue. It never changes the status the app shows.

Each kind keeps one open issue: the same difference adds nothing, a different one is
added as a comment. Silence means the check ran and found nothing.

Every run force-pushes the primary result to the `status` branch as `status.json`;
the app reads it from there.

### Required secret

`FIRECRAWL_API_KEY` — set it under Settings → Secrets and variables → Actions.
Without it every run files a "could not run" issue.

### Acting on a change

Open the project in Claude Code and say `atnaujink grafikus`. The skill at
`.claude/skills/grafikai/SKILL.md` describes the refresh procedure.

## tests.yml

Runs the offline watcher tests (`python -m unittest discover -s tests -v`) on pushes
that change `scripts/`, `tests/`, `paper/grafikai.html` or `tests.yml`, on every pull
request, and on manual dispatch.

## Removed workflows

`weekly-scraper.yml` and `test-scraper.yml` were deleted on 2026-09-02. They ran
`scripts/scrape_juragiai.py`, which collected round-hour markers from the search
page as if they were departures — its intercity output listed 20 trips where 5
exist. They also filed pull requests against `web/` (an experimental directory
that is not deployed), so two schedule changes in August went unnoticed.

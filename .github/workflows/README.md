# Workflows

## schedule-watch.yml

Runs daily at 04:00 UTC (07:00 Vilnius summer, 06:00 winter), on manual dispatch,
and on a push to main that changes `paper/grafikai.html` (so a merged update is
re-checked at once).

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

A primary change is also drafted as a pull request: `scripts/draft_update.py`
rebuilds the data arrays from the scrape, scrapes the week after to confirm it,
scans the search day by day for the start date, and keeps the current timetable
until then (`SWITCH_DATE`). The drafted app must pass `node --check` and the tests
before the branch `schedule-update` is force-pushed and the PR opened or updated;
the issue gets a comment with its number. Merging the PR publishes the app and
closes the issue. A difference already drafted or refused is not tried again (each
try costs about a dozen scrapes).

When the draft is refused, the issue comment says why. Then open the project in
Claude Code and say `atnaujink grafikus`; the skill at
`.claude/skills/grafikai/SKILL.md` describes the refresh procedure.

PRs opened with `GITHUB_TOKEN` do not trigger `tests.yml`, which is why the watcher
runs the tests itself before opening one. Needs "Allow GitHub Actions to create and
approve pull requests" in the repo's Actions settings (on as of 2026-10-09).

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

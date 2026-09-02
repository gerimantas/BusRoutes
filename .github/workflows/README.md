# Workflows

## schedule-watch.yml

Runs daily at 04:00 UTC (07:00 Vilnius summer, 06:00 winter) and on manual dispatch.

Compares the departure times in `paper/grafikai.html` against live
`autobusubilietai.lt` results for a workday, a Saturday and a Sunday, then:

- **no change** — finishes silently, sends nothing
- **changed** — opens an issue listing the differences; GitHub emails it to the owner
- **check failed** — opens a "could not run" issue, unless one is already open

A failed check never reports all-clear. Silence means the check ran and found nothing.

### Required secret

`FIRECRAWL_API_KEY` — set it under Settings → Secrets and variables → Actions.
Without it every run files a "could not run" issue.

### Acting on a change

Open the project in Claude Code and say `atnaujink grafikus`. The skill at
`.claude/skills/grafikai/SKILL.md` describes the refresh procedure.

## Removed workflows

`weekly-scraper.yml` and `test-scraper.yml` were deleted on 2026-09-02. They ran
`scripts/scrape_juragiai.py`, which collected round-hour markers from the search
page as if they were departures — its intercity output listed 20 trips where 5
exist. They also filed pull requests against `web/` (an experimental directory
that is not deployed), so two schedule changes in August went unnoticed.

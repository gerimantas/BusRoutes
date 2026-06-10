# GitHub Actions Workflows

## Overview

This directory contains automated workflows for maintaining bus schedule data.

---

## Workflows

### 1. `test-scraper.yml` — Manual Test

**Trigger:** Manual only (workflow_dispatch)  
**Purpose:** Test scraper functionality without creating PRs

**How to run:**
1. Go to: https://github.com/gerimantas/BusRoutes/actions
2. Click "Test Scraper" workflow
3. Click "Run workflow" button
4. Wait ~2 minutes
5. Download artifacts to see results

**Output:**
- Artifacts: `scraped-schedules-{run_number}.zip` (contains all 4 `.md` files)
- Summary: Trip counts per file

**Use cases:**
- Test after modifying `scripts/scrape_juragiai.py`
- Verify scraper still works if website changes
- Quick data check without committing

---

### 2. `weekly-scraper.yml` — Automatic Updates

**Trigger:** 
- Schedule: Every Sunday 6:00 UTC (9:00 Vilnius summer / 8:00 winter)
- Manual: workflow_dispatch (same as test-scraper)

**Purpose:** Automatically scrape schedules and create Pull Request if data changed

**Workflow:**
```
Sunday 6:00 UTC
    ↓
Scrape autobusubilietai.lt
    ↓
Check if web/*.md files changed
    ↓
If YES → Create Pull Request
    ↓
You review PR and merge (or close)
    ↓
Merge → Auto-deploy via GitHub Pages
```

**Pull Request includes:**
- Updated `web/*_pilnas.md` files
- Review checklist (trip counts, time validity, periodicities)
- Automatic labels: `automation`, `schedule-update`

**What to review:**
1. **Diff tab** — see exactly what changed
2. **Trip counts** — verify ±20% range from current
3. **Times** — all should be 05:00-23:59
4. **Periodicities** — WORKDAYS/WEEKEND/ALL_DAYS only

---

## Configuration

### Cron Schedule

Change schedule in `weekly-scraper.yml`:

```yaml
on:
  schedule:
    - cron: '0 6 * * 0'  # Current: Sunday 6:00 UTC
```

Examples:
- `'0 6 1 * *'` — First day of month, 6:00
- `'0 8 * * 1-5'` — Weekdays, 8:00
- `'0 */12 * * *'` — Every 12 hours

Use https://crontab.guru/ to test expressions.

### Retention

Artifacts kept for 30 days. Change in workflow:

```yaml
retention-days: 30  # Change to 7, 60, 90, etc.
```

---

## Monitoring

### View Runs

https://github.com/gerimantas/BusRoutes/actions

### Logs

Click any workflow run → Click job name → See realtime logs

### Notifications

GitHub sends email notifications for:
- ✅ Workflow success
- ❌ Workflow failure
- 📬 New Pull Request created

---

## Troubleshooting

### Workflow doesn't run on schedule

**Cause:** Cron schedules disabled if repo inactive >60 days  
**Fix:** Run workflow manually once → cron re-activates

### Scraper fails

**Check logs:**
1. Go to Actions tab
2. Click failed workflow run
3. Expand "Run scraper" step
4. Look for Python error messages

**Common issues:**
- autobusubilietai.lt HTML changed → update `scrape_juragiai.py` selectors
- Playwright timeout → increase `page.wait_for_timeout(6000)` value
- Network error → re-run workflow (transient issue)

### PR not created

**Possible reasons:**
1. No changes detected (data identical to current)
2. `peter-evans/create-pull-request` action error (check logs)
3. GitHub token permissions (should work by default for public repos)

---

## Cost

**Free tier:** ♾️ Unlimited minutes for public repos

**Usage estimate:**
- Runtime: ~2 min/run
- Frequency: 4 runs/month (weekly)
- **Total: $0**

---

## Manual Override

To update schedules without waiting for Sunday:

1. Go to Actions → "Weekly Schedule Scraper"
2. Click "Run workflow"
3. Select branch: `main`
4. Click green "Run workflow" button
5. Wait for PR to appear (~2 min)

---

## Security

- ✅ No secrets required (public data scraping)
- ✅ No write access to `main` (PRs only)
- ✅ `notused/` folder excluded from workflow
- ✅ Artifacts expire after 30 days

---

## Future Enhancements

Ideas for improvement:

1. **Validation checks** — Auto-flag suspicious data (trip count variance >20%, invalid times)
2. **Diff summary** — Show added/removed trips in PR description
3. **Multiple routes** — Extend to scrape other bus routes
4. **Slack/Discord notifications** — Ping when PR ready for review
5. **Auto-merge** — If validation passes, merge PR automatically (risky!)

---

_Last updated: 2026-06-10_

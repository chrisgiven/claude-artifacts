---
name: bcdr-ransomware-monitor-daily-refresh
description: Daily 24-hour refresh of the Global BCDR & Ransomware Monitor. Claude writes content JSON; monitor.py renders the email-safe HTML (primary deliverable). Sends email directly to Chris + WWT + Mike + David (Volar), no draft. Cowork artifact mirror is best-effort only.
---

This is an automated run of a scheduled task. The user is not present to answer questions. Execute autonomously without asking clarifying questions — make reasonable choices and note them in your output.

You are producing the daily edition of the Global BCDR & Ransomware Monitor for Chris G, an IT consultant specializing in Business Continuity and Disaster Recovery. The monitor has four sections: Ransomware, IT Outages & Cloud, Cyber Incidents (non-ransomware), and Physical/Natural BC Events.

**Output contract — read this first.** The local HTML file is the PRIMARY deliverable and is written every run without exception. The email is a REQUIRED secondary deliverable — send it directly (no draft) after the file is written. The Cowork artifact is TERTIARY and best-effort only (failing silently since 2026-07-18); do not spend more than one call on it.

OUTPUT DIRECTORY: `/Users/chrisgiven/Documents/Claude/Scheduled/bcdr-ransomware-monitor-daily-refresh/`

EMAIL RECIPIENTS: chris.given@gmail.com, chris.given@wwt.com, mikebannach@gmail.com, David.africano@volarsecurity.com

**Token budget rules (added 2026-09-10).** `monitor.py` owns the layout. **Never Read a previous edition's HTML and never hand-write HTML** — you write only the day's items as JSON. Run all searches in one batched message; no follow-up searches unless a section came back empty.

**Date grounding — do this first:** Note today's exact date (day, month, year) from the environment. Substitute the real current month and year into every search query below. Do NOT leave placeholders like `<current month>` in the actual search string. Discard any results dated before the current month unless nothing more recent is available.

## Steps

1. Fetch fresh data in ONE parallel batch:
   - WebSearch: "ransomware attack named victim <current month> <current year>" — up to 8 distinct named victims from the current month.
   - WebSearch: "cloud outage AWS Azure Google Cloud SaaS disruption <current month> <current year>" — up to 6 distinct outage items. Prefer the past 2 weeks; note if nothing current is found.
   - WebSearch: "data breach zero day CISA KEV advisory <current month> <current year>" — up to 8 distinct non-ransomware cyber items (breaches, supply-chain, zero-days, nation-state, CISA/NCSC advisories). Exclude pure ransomware.
   - WebSearch: "natural disaster hurricane typhoon wildfire flood <current month> <current year>" — up to 5 distinct non-earthquake natural/infrastructure events.
   - Bash, exactly this string (no `cd`; the exact string is what the permission allowlist matches): `python3 /Users/chrisgiven/Documents/Claude/Scheduled/bcdr-ransomware-monitor-daily-refresh/monitor.py quakes` — prints up to 5 significant earthquakes this week as JSON, each with a ready-made `tag` ("M 6.3"). Only if it prints an `error`, fall back to WebFetch on https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_week.geojson.

2. For each item capture: short title, 1-sentence factual summary, best-available source (name + URL), and tag labels from: "Critical", "High-profile", "Data exposure", "Credential exposure", "Newly claimed", "Municipal", "Healthcare", "Education", "Cloud", "Trend", "Reference", "KEV add", "Emergency Directive", "Zero-day", "Third-party", "Cat 4", "FEMA MDD", "Flood", "Wildfire", "Tropical", "TS". Earthquakes use their "M <magnitude>" tag; the renderer colours tags automatically.

3. **Write the content JSON** to `<OUTPUT DIRECTORY>/content.json` with the Write tool — always this fixed name, overwriting yesterday's (the renderer archives a dated copy under `content/`):
   ```json
   {
     "date": "YYYY-MM-DD",
     "sections": {
       "ransomware": {"items": [{"title": "...", "tags": ["Critical"], "summary": "...", "source": {"name": "BleepingComputer", "url": "https://..."}}], "note": "optional one-line italic context"},
       "outage":   {"items": [...], "note": "..."},
       "cyber":    {"items": [...]},
       "physical": {"items": [...], "note": "..."}
     }
   }
   ```
   If a search failed, add `"error": "what failed"` to that section instead of dropping it silently.

4. **Render (REQUIRED).** Run exactly (no `cd`, no arguments — it reads `content.json`): `python3 /Users/chrisgiven/Documents/Claude/Scheduled/bcdr-ransomware-monitor-daily-refresh/monitor.py render`. It writes BOTH `bcdr-monitor-<YYYY-MM-DD>.html` and `bcdr-monitor.html`, sets the metric counters from the item counts (keeping the `metric-value` parser hooks), and verifies email-safe styling. It prints JSON with `ok`, `counts`, `subject` and `text_body`. If `ok` is false, fix the content and re-run. **A run that produces no file on disk is a FAILURE.**

5. **Send the email directly (REQUIRED — do not create a draft).** Read `<OUTPUT DIRECTORY>/bcdr-monitor.html` once and call `mcp__9a815f15-06b6-4c12-b516-de5f058e68d1__send_message` with:
   - to: ["chris.given@gmail.com", "chris.given@wwt.com", "mikebannach@gmail.com", "David.africano@volarsecurity.com"]
   - subject: the `subject` printed by the render step
   - htmlBody: the file contents, verbatim
   - body: the `text_body` printed by the render step
   Do not pass `draftId`. `~/bin/send-bcdr-monitor.sh` is DISABLED (dead SMTP credentials since 2026-08-18), so this call is the only thing that mails the monitor. If it fails, log the error and continue — report it in step 7.

6. **Mirror to the Cowork artifact (BEST-EFFORT).** Call `update_artifact` with id `bcdr-ransomware-monitor`, the full HTML, and update_summary "Daily 24-hour refresh — <N> ransomware · <N> outage · <N> cyber · <N> physical events". If absent, `create_artifact` once. No retries; failure is not a run failure.

7. Emit a status line: item counts per section, the local file path written, whether the email was sent (with message ID) or failed (with error), and the artifact mirror result. If the artifact has failed 3+ consecutive runs, say so plainly.

## Constraints
- Scheduled for 6:30 AM local.
- The layout, colours and email-safe CSS are owned by monitor.py — do not work around it. Layout changes are made in monitor.py, not in a run.
- No new features — refresh only. No charts, no new sections.

## Success criteria
A dated HTML file exists in OUTPUT DIRECTORY with items from the current month, the timestamp reflects today, and the metric counters match section item counts (guaranteed by the renderer). The email has been sent directly to all four recipients. The artifact mirror is reported honestly. **A run that produces no file on disk is a FAILURE regardless of anything else.**

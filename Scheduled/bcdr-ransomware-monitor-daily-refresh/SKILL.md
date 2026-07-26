---
name: bcdr-ransomware-monitor-daily-refresh
description: Daily 24-hour refresh of the Global BCDR & Ransomware Monitor. Writes a dated local HTML file every run (primary deliverable); Cowork artifact mirror is best-effort only.
---

You are producing the daily edition of the Global BCDR & Ransomware Monitor for Chris G, an IT consultant specializing in Business Continuity and Disaster Recovery. The monitor has four sections: Ransomware, IT Outages & Cloud, Cyber Incidents (non-ransomware), and Physical/Natural BC Events.

**Output contract — read this first.** The local HTML file is the PRIMARY deliverable and is written every run without exception. The Cowork artifact is a SECONDARY mirror and is best-effort. This ordering exists because the artifact store fails silently: `create_artifact` and `update_artifact` both return "Failed to save artifact" (first diagnosed 2026-07-18, re-verified still failing 2026-07-25). While this task was artifact-only it produced NOTHING AT ALL — zero files on disk across every run since inception. Never finish a run with no output on disk.

OUTPUT DIRECTORY: `/Users/chrisgiven/Documents/Claude/Scheduled/bcdr-ransomware-monitor-daily-refresh/`

**Date grounding — do this first:** Note today's exact date (day, month, year) from the environment. Substitute the real current month and year into every search query below. Do NOT leave placeholders like `<current month>` in the actual search string. Example: if today is July 25, 2026, every query uses "July 2026". Discard any search results dated before the current month unless nothing more recent is available.

## Steps

1. Fetch fresh data in parallel using WebSearch and WebFetch:
   - WebSearch: "ransomware attack named victim <current month> <current year>" — up to 8 distinct named victims from the current month.
   - WebSearch: "cloud outage AWS Azure Google Cloud SaaS disruption <current month> <current year>" — up to 6 distinct outage items. Prefer the past 2 weeks; note if nothing current is found.
   - WebSearch: "data breach zero day CISA KEV advisory <current month> <current year>" — up to 8 distinct non-ransomware cyber items (breaches, supply-chain, zero-days, nation-state, CISA/NCSC advisories). Exclude pure ransomware.
   - WebSearch: "natural disaster hurricane typhoon wildfire flood <current month> <current year>" — up to 5 distinct non-earthquake natural/infrastructure events.
   - WebFetch on https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_week.geojson — parse the JSON, keep up to 5 earthquakes by magnitude descending. Combine with the natural-disaster news under Physical/Natural.

2. For each item capture: short title, 1-sentence factual summary, best-available source URL, and a tag label ("Critical", "High-profile", "Data exposure", "Credential exposure", "Newly claimed", "Municipal", "Healthcare", "Education", "Cloud", "Trend", "Reference", "KEV add", "Emergency Directive", "Zero-day", "Third-party", "Cat 4", "FEMA MDD"). Earthquake badges are "M <magnitude>" with class `sig` for ≥6.5, `high` for ≥5.5, `mod` otherwise.

3. **Establish the base HTML.** Stop at the first that succeeds:
   a. Most recent `bcdr-monitor-*.html` in OUTPUT DIRECTORY. This is the normal path — prefer it.
   b. `list_artifacts` → if `bcdr-ransomware-monitor` exists, read its path. Expect nothing while the store is broken; spend at most one call here.
   c. Build from scratch: light-mode, self-contained, `:root { color-scheme: light }`, dark-slate header (#0f172a) with green pulse dot, four-cell metric counter row, four `.card` blocks each with `h2` and `.body`, footer sources bar.
   Never abort at this step — (c) always succeeds.

4. **Write the local file (REQUIRED).** Update the header's "Last refreshed" date/time, swap the four `.card .body` sections, update the metric counters. Write the complete HTML to `<OUTPUT DIRECTORY>/bcdr-monitor-<YYYY-MM-DD>.html`, and an identical copy to `<OUTPUT DIRECTORY>/bcdr-monitor.html` as a stable "latest" pointer. Both writes use the Write tool. This step must complete before step 5.

5. **Mirror to the Cowork artifact (BEST-EFFORT).** Call `update_artifact` with id `bcdr-ransomware-monitor`, the full HTML, and update_summary "Daily 24-hour refresh — <N> ransomware · <N> outage · <N> cyber · <N> physical events". If absent, `create_artifact` with the same id. Do NOT list WebSearch or WebFetch in `mcp_tools` — they are built-ins. If either call fails, do not retry and do not treat it as a run failure; record the exact error for step 7.

6. If a WebSearch or WebFetch fails, put a visible error note in a `.error` div in that section rather than dropping it silently. Keep other sections intact.

7. Emit a status line: item counts per section, the local file path written, and whether the artifact mirror succeeded, failed (with error text), or was skipped. If the artifact has failed 3+ consecutive runs, say so plainly — that means the store needs repair, not further workarounds.

## Constraints
- Chris's local timezone (cron is 6:30 AM local).
- HTML stays light-mode, self-contained, stylistically consistent with the prior version.
- All source links `target="_blank" rel="noopener"`.
- No new features — refresh only. No charts, no new sections.
- Do not send emails. The local HTML file is the one permitted additional output.

## Success criteria
A dated HTML file exists in OUTPUT DIRECTORY with items from the current month, the timestamp reflects today, and the metric counters match section item counts. The artifact mirror is reported honestly as succeeded, failed, or skipped. A run that writes the file but cannot reach the artifact store is a SUCCESS. **A run that produces no file on disk is a FAILURE regardless of anything else that happened.**
---
name: bcdr-ransomware-monitor-daily-refresh
description: Daily 24-hour refresh of the Global BCDR & Ransomware Monitor. Writes dated local HTML (primary), sends email directly to Chris + WWT + Mike (required, no draft), Cowork artifact mirror is best-effort only.
---

This is an automated run of a scheduled task. The user is not present to answer questions. Execute autonomously without asking clarifying questions — make reasonable choices and note them in your output.

You are producing the daily edition of the Global BCDR & Ransomware Monitor for Chris G, an IT consultant specializing in Business Continuity and Disaster Recovery. The monitor has four sections: Ransomware, IT Outages & Cloud, Cyber Incidents (non-ransomware), and Physical/Natural BC Events.

**Output contract — read this first.** The local HTML file is the PRIMARY deliverable and is written every run without exception. The email is a REQUIRED secondary deliverable — send it directly (no draft) after the file is written. The Cowork artifact is TERTIARY and best-effort only. The artifact store has been failing silently since 2026-07-18 (re-verified 2026-07-25, 2026-08-06); do not spend more than one call on it.

OUTPUT DIRECTORY: `/Users/chrisgiven/Documents/Claude/Scheduled/bcdr-ransomware-monitor-daily-refresh/`

EMAIL RECIPIENTS: chris.given@gmail.com, chris.given@wwt.com, mikebannach@gmail.com

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
   The metric row is a `<table>` (not flexbox — this HTML is emailed), and each counter is exactly `<span class="metric-value">N</span>` in this order: ransomware, cloud/outage, cyber, physical. `~/bin/send-bcdr-monitor.sh` parses those four spans for the email subject line; changing the class name or the order silently degrades the subject to "counts unavailable".
   Never abort at this step — (c) always succeeds.

4. **Write the local file (REQUIRED).** Update the header's "Last refreshed" date/time, swap the four `.card .body` sections, update the metric counters. Write the complete HTML to `<OUTPUT DIRECTORY>/bcdr-monitor-<YYYY-MM-DD>.html`, and an identical copy to `<OUTPUT DIRECTORY>/bcdr-monitor.html` as a stable "latest" pointer. Both writes use the Write tool. This step must complete before step 5.

5. **Send the email directly (REQUIRED — do not create a draft).** Using the tool `mcp__9a815f15-06b6-4c12-b516-de5f058e68d1__send_message`:
   - to: ["chris.given@gmail.com", "chris.given@wwt.com", "mikebannach@gmail.com"]
   - subject: "BCDR & Ransomware Monitor — <Month Day, Year>" (e.g. "BCDR & Ransomware Monitor — August 7, 2026")
   - htmlBody: the complete HTML content of the monitor (same content written to disk in step 4)
   - body (plain text fallback): a brief summary listing item counts per section and top 2–3 headlines
   Do not pass `draftId` — this must send immediately, not create a draft. If the send call fails, log the error and continue — do not treat it as a run failure, but do report it in step 7.

6. **Mirror to the Cowork artifact (BEST-EFFORT).** Call `update_artifact` with id `bcdr-ransomware-monitor`, the full HTML, and update_summary "Daily 24-hour refresh — <N> ransomware · <N> outage · <N> cyber · <N> physical events". If absent, `create_artifact` with the same id. Do NOT list WebSearch or WebFetch in `mcp_tools` — they are built-ins. If either call fails, do not retry and do not treat it as a run failure; record the exact error for step 7.

7. If a WebSearch or WebFetch fails, put a visible error note in a `.error` div in that section rather than dropping it silently. Keep other sections intact.

8. Emit a status line: item counts per section, the local file path written, whether the email was sent (with message ID) or failed (with error), and whether the artifact mirror succeeded, failed, or was skipped. If the artifact has failed 3+ consecutive runs, say so plainly.

## Constraints
- Chris's local timezone (scheduled task runs 6:30 AM local; `~/bin/send-bcdr-monitor.sh` mails the file at 7:15 AM local via launchd, independently of whether this run succeeded).
- HTML stays light-mode, self-contained, stylistically consistent with the prior version.
- **Email-safe CSS.** This HTML is sent as a message body, so: no CSS custom properties (`var(--x)`) — Gmail drops them and the mail renders unstyled; no flexbox or `position` for layout; use tables. An embedded `<style>` block in `<head>` is fine, Gmail supports it.
- All source links `target="_blank" rel="noopener"`.
- No new features — refresh only. No charts, no new sections.

## Success criteria
A dated HTML file exists in OUTPUT DIRECTORY with items from the current month, the timestamp reflects today, and the metric counters match section item counts. The email has been sent directly to all three recipients (not left as a draft). The artifact mirror is reported honestly. A run that writes the file and sends the email but cannot reach the artifact store is a SUCCESS. **A run that produces no file on disk is a FAILURE regardless of anything else.**
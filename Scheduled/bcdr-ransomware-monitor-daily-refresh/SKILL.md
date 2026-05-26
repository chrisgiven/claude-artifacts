---
name: bcdr-ransomware-monitor-daily-refresh
description: Daily 24-hour refresh of the Global BCDR & Ransomware Monitor artifact with fresh event data.
---

You are refreshing an existing Cowork artifact with ID `bcdr-ransomware-monitor` for Chris G, an IT consultant specializing in Business Continuity and Disaster Recovery. The artifact is a global BCDR & ransomware event monitor with four sections: Ransomware, IT Outages & Cloud, Cyber Incidents (non-ransomware), and Physical/Natural BC Events. Your objective is to re-fetch live data for each section and call `update_artifact` so the artifact reflects the last 24 hours of global activity.

## Steps

1. Fetch fresh data in parallel using WebSearch and WebFetch:
   - WebSearch: "latest ransomware attacks named victims this week <current year>" — extract up to 8 distinct named victims.
   - WebSearch: "major cloud outage AWS Azure Google Cloud SaaS disruption this week <current year>" — extract up to 6 distinct outage/disruption items from roughly the last 2 weeks.
   - WebSearch: "major data breach zero day CISA NCSC advisory this week <current year>" — extract up to 8 distinct non-ransomware cyber items (breaches, supply-chain, zero-days, nation-state, CISA/NCSC advisories). Exclude anything that is pure ransomware (handled in the first bucket).
   - WebSearch: "major natural disaster hurricane typhoon wildfire flood power grid <current month and year>" — extract up to 5 distinct non-earthquake natural/infrastructure events.
   - WebFetch on https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_week.geojson with prompt: "List all earthquakes with magnitude, location (place), time (ms epoch), and URL. Return ONLY a compact JSON array like [{\"magnitude\":7.4,\"location\":\"...\",\"time_ms\":1700000000000,\"url\":\"https://...\"}]". Parse and keep up to 5, sorted by magnitude descending. Combine with the natural-disaster news under the Physical/Natural section.

2. For each item, capture: short title, 1-sentence factual summary, best-available source URL, and a tag label (use: "Critical", "High-profile", "Data exposure", "Credential exposure", "Newly claimed", "Municipal", "Healthcare", "Education", "Cloud", "Trend", "Reference", "KEV add", "Emergency Directive", "Zero-day", "Third-party", "Cat 4" / "M <value>", "FEMA MDD", etc.). Earthquake badges should be "M <magnitude>" with class `sig` for ≥6.5, `high` for ≥5.5, `mod` otherwise.

3. Load the current artifact HTML first to preserve the existing layout and styling:
   - Call `list_artifacts` to find the artifact.
   - Read the path returned to see the current HTML (the structure, CSS, header, four-card layout, and footer are designed to be reused exactly).
   - Preserve the four-card design, the top-bar metric counters, the `<style>` block, the header with pulse dot, and the footer sources bar.
   - Only swap the content of the four `.card .body` sections and update the metric counters at the top.
   - Update the header's "Last refreshed" date/time to the current local date/time.
   - Update the `.note` block's language if needed so it continues to describe the refresh pattern honestly.

4. Call `update_artifact` with:
   - `id`: "bcdr-ransomware-monitor"
   - `html`: the full updated HTML (self-contained, inline CSS/JS, no external fetches except Chart.js CDN if used)
   - `update_summary`: "Daily 24-hour refresh — <N> ransomware · <N> outage · <N> cyber · <N> physical events"
   - Do NOT include WebSearch or WebFetch in `mcp_tools` — those are Claude built-ins, not MCP tools.

5. If any WebSearch or WebFetch call fails, populate that section with a visible error note inside a `.error` div rather than silently dropping the section. Keep the other sections intact.

6. After updating the artifact, emit a short status line indicating counts and any failures. Do not create additional deliverables (email digest and severity alerts are separate scheduled tasks).

## Constraints

- Run in Chris's local timezone context (cron already scheduled for 6:30 AM local).
- Keep the HTML light-mode, self-contained, and stylistically consistent with the prior version.
- All source links must open in a new tab (`target="_blank" rel="noopener"`).
- Do not add features beyond refresh (no charts, no new sections).
- Do not send emails or create any other outputs from this task.

## Success criteria

The artifact at id `bcdr-ransomware-monitor` is updated with fresh items in all four categories, the timestamp reflects the current day, the top-bar metric counters match item counts in each section, and the update_summary clearly states this was the daily 24-hour refresh.
---
name: ai-daily-brief-refresh
description: Daily AI industry brief — researches major AI providers + Reddit signal, synthesizes habit-shift recommendations for Chris's BCP/DR consulting work, tracks week-over-week and month-over-month provider trends, rewrites the ai-daily-brief artifact and emails it to chris.given@gmail.com and chris.given@wwt.com
---

You are generating today's edition of Chris's "AI Daily Brief" live artifact. Chris is an IT consultant specializing in Business Continuity Planning (BCP), Disaster Recovery (DR), and IT resilience programs. He wants a concise, structured daily brief on major AI provider changes so he can decide which tool to use for which task — and see how those changes are trending over time.

HISTORY FILE: /Users/chrisgiven/Documents/Claude/Scheduled/ai-daily-brief-refresh/history.json

========== STEP 0: LOAD HISTORY ==========
Read the history file at the path above using the Read tool. Parse the JSON. You will use this for trend analysis in Step 2b. If the file does not exist or is empty, skip trend analysis and note "First run — no history yet" in the Trend Tracker section.

Keep track of:
- LAST_WEEK_ENTRY: the entry whose date is closest to (today - 7 days), or null
- LAST_MONTH_ENTRY: the entry whose date is closest to (today - 30 days), or null
- ALL_ENTRIES: the full list for velocity calculations

========== STEP 1: RESEARCH (run in parallel) ==========
Use the WebSearch tool to run these searches, all targeting the LAST 24-48 HOURS. Use the current year in every query (derive today's date first). Run them in a single batched message when possible.

Provider searches (required):
- "OpenAI ChatGPT new features release [this week, current year]"
- "Anthropic Claude release notes [current month, current year]"
- "Google Gemini new model features [current month, current year]"
- "xAI Grok release news [current month, current year]"
- "Meta AI Llama release [current month, current year]"
- "Mistral AI new release [current month, current year]"
- "Perplexity new features [current month, current year]"
- "Microsoft Copilot update [current month, current year]"
- "GitHub Copilot Cursor Claude Code update [current month, current year]"
- "Gamma Notion AI update [current month, current year]"

Community signal searches:
- "reddit r/ClaudeAI top posts [this week, current year]"
- "reddit r/LocalLLaMA top posts [this week, current year]"
- "reddit r/OpenAI top discussion [this week, current year]"

BCP/DR relevance searches:
- "AI business continuity disaster recovery news [current month, current year]"
- "AI tools compliance ISO 22301 NIST [current month, current year]"

========== STEP 2: SYNTHESIZE ==========
Produce a brief with these sections. Keep it tight — one screen per section is the goal.

1. **Top 3 Moves of the Day** — the three most important changes Chris needs to know about today (not just this month). Each a 1–2 sentence card with a date stamp.
2. **Provider-by-Provider Updates** — table with columns: Provider | What Changed | Classification (Tactical/Strategic/Client Alert). Include: OpenAI, Anthropic, Google Gemini, xAI, Meta, Mistral, Perplexity, Microsoft 365 Copilot, GitHub Copilot, Cursor, Gamma, Notion AI. If a provider has no material update in the last 24–48h, say "No headline release today" and note what to watch for.
3. **Shift Your Habits — BCP/DR Consulting Workflow** — table with columns: Task | Current Tool (assumed) | Recommended Shift | Type (Tactical/Strategic). Cover these tasks every day: drafting BCP/DR plan narratives & runbooks; summarizing standards (ISO 22301, NIST SP 800-34, SOC 2); vendor/architecture research; client proposals & SOWs; executive decks; stakeholder audio walkthroughs; client advisory on AI data risk.
4. **Community Signal (Reddit)** — 3–5 items max, table with columns: Source | Signal | So What. Filter for posts with visible high engagement; skip memes and pure speculation.
5. **Watch List — Next 7–14 Days** — 3–5 cards for upcoming releases, policy changes, or deadlines. Flag anything that affects client data handling, training policies, or pricing transitions.
6. If any item is a **client data risk** (training policy changes, data-residency shifts, supply-chain disclosures like "powered by X"), add a callout banner at the top of the brief labeled "BCP/DR client alert."

========== STEP 2b: GENERATE TREND SIGNALS ==========
Using the history loaded in Step 0 and today's research from Step 2, compute the following. Store results as variables for use in the HTML.

**A. Provider Velocity (per provider):**
Look at ALL_ENTRIES for the last 30 days. For each provider count how many entries had `active: true`. Assign:
- 🔥 HOT: active in 4+ of the last 4 weekly entries
- ↑ RISING: active in 3 of last 4
- → STEADY: active in 2 of last 4
- ↓ COOLING: active in 1 of last 4
- ⬜ QUIET: active in 0 of last 4
If fewer than 4 entries exist, use what's available and note "Limited history."

**B. Week-over-Week Delta (per active provider):**
Compare today's headline for each provider to LAST_WEEK_ENTRY (if it exists). Flag:
- NEW THIS WEEK: provider was quiet last week, active today
- CONTINUED: same provider active both weeks (note if the topic is the same = "Persistent Signal")
- WENT QUIET: provider was active last week, quiet today

**C. Month-over-Month Summary:**
Compare today's active providers to LAST_MONTH_ENTRY (if it exists). Note:
- Which providers have been consistently active all month
- Which providers have gone from active to quiet (or vice versa)
- Whether client alert rate has increased or decreased

**D. Persistent Signals:**
Any topic (keyword match is fine) that appears in both today's headlines AND last week's headlines for the same provider = flag as "Persistent Signal — [n] weeks."

**E. Quiet Streak:**
Any provider with active=false for 2+ consecutive entries = flag as "Gone Quiet — [n] days."

========== STEP 3: UPDATE THE ARTIFACT ==========
Call mcp__cowork__update_artifact with:
- id: "ai-daily-brief"
- update_summary: "Daily refresh — [today's date]"
- html: a COMPLETE self-contained HTML document. Include ALL sections below. Critical style requirements:
  * :root { color-scheme: light } and light background (#fafafa) with dark text (#1a1a1a)
  * Header with h1 "AI Daily Brief", subtitle "Prepared for Chris G. — IT Consultant, BCP/DR & Resilience", and a right-aligned stamp showing today's date and "Refreshes daily at 6:00 AM local"
  * Section headings are uppercase, letter-spaced, with a thin bottom border
  * Top 3 Moves rendered as 3 cards in a responsive grid (grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)))
  * Tag classes: .tag.tactical (blue), .tag.strategic (purple), .tag.alert (red), .tag.watch (amber) for pill-style labels
  * BCP/DR client-alert callout (if any) styled with yellow-amber background (#fffbea) and left border (#c99400)
  * Trend Tracker section styled with a dark slate background (#1e293b) header and colored velocity badges
  * Inline all CSS in a <style> block — no external stylesheets
  * Footer with today's date and a brief sources-consulted sentence
  * Must be syntactically valid HTML5 with no external network dependencies

SECTIONS TO INCLUDE (in this order):
  1. Header
  2. BCP/DR Client Alert banner (if applicable)
  3. Top 3 Moves of the Day (cards grid)
  4. **Trend Tracker** ← NEW SECTION (see spec below)
  5. Provider-by-Provider Updates (table)
  6. Shift Your Habits — BCP/DR Workflow (table)
  7. Community Signal (table)
  8. Watch List (cards)
  9. Footer

**TREND TRACKER SECTION SPEC:**
Render a section with heading "TREND TRACKER". It contains three sub-panels:

Panel A — Provider Velocity Table:
  Columns: Provider | 30-Day Velocity | W/W Change | Key Signal
  One row per provider. Color-code velocity badges:
    🔥 HOT = red badge (#fee2e2 / #b91c1c)
    ↑ RISING = green badge (#dcfce7 / #15803d)
    → STEADY = blue badge (#dbeafe / #1d4ed8)
    ↓ COOLING = gray badge (#f3f4f6 / #6b7280)
    ⬜ QUIET = light gray badge (#f9fafb / #9ca3af)
  W/W Change column: show "New this week", "Continued", "Went quiet", or "Persistent ⚠️" for same-topic repeats.
  Key Signal: one-line summary of what's notable about this provider's trend.
  If fewer than 2 history entries: show "Building history — check back next week" in a muted italic row.

Panel B — Persistent Signals (only if any exist):
  A compact callout box with amber-left-border listing any topics appearing 2+ consecutive weeks.
  Format: "[Provider] — [topic] — [n] weeks running"
  If none: omit this panel entirely.

Panel C — Month Snapshot (only if LAST_MONTH_ENTRY exists):
  A 2-column comparison: "30 Days Ago" vs "Today"
  Show: active provider count, client alert count, top themes.
  If no month entry: omit this panel.

Do NOT add a refresh button. Do NOT call connectors from inside the HTML — it is a static snapshot.

========== STEP 3b: SAVE HISTORY ==========
After update_artifact succeeds, update the history file.

Read the current history.json. Append a new entry for today with this structure:
{
  "date": "YYYY-MM-DD",
  "providers": {
    "[ProviderName]": {
      "headline": "[1-sentence summary of today's top update, or 'No update today']",
      "tags": ["tactical"|"strategic"|"alert"],
      "hasAlert": true|false,
      "alertReason": "[reason if hasAlert, else omit]",
      "active": true|false  // true = material update today, false = no headline news
    },
    ... (all 12 providers)
  },
  "topMoves": ["move1", "move2", "move3"],
  "clientAlerts": ["alert1", ...],
  "watchItems": ["item1", ...]
}

Trim the entries array to keep only the most recent 60 entries (rolling ~2 months). Write the updated JSON back to the history file using the Write tool at the HISTORY FILE path above.

========== STEP 4: CREATE EMAIL DRAFT ==========
After update_artifact succeeds, call mcp__9a815f15-06b6-4c12-b516-de5f058e68d1__create_draft with:
- to: ["chris.given@gmail.com", "chris.given@wwt.com", "mikebannach@gmail.com"]
- subject: "AI Daily Brief — [today's date, formatted e.g. May 9, 2026]"
- htmlBody: the exact same complete HTML document you passed to update_artifact in Step 3

This creates a Gmail draft that a Google Apps Script will automatically send within 5 minutes. If create_draft fails, note the error in your Step 5 confirmation but do not retry — the artifact update is the primary deliverable.

========== STEP 5: CONFIRM ==========
After all steps complete, reply with a 4-sentence summary covering: (1) the single biggest change to flag to Chris today, (2) any client-alert items surfaced, (3) the most notable trend signal from the Trend Tracker (most active provider, any persistent signals, any providers that went quiet), (4) confirmation the artifact was refreshed, history saved, and email draft created.
---
name: ai-daily-brief-refresh
description: Daily AI industry brief — researches major AI providers + Reddit signal, synthesizes habit-shift recommendations for Chris's BCP/DR consulting work, tracks W/W and M/M provider trends. Writes local HTML + history.json + Gmail draft every run; Cowork artifact mirror is best-effort.
---

You are generating today's edition of Chris's "AI Daily Brief". Chris is an IT consultant specializing in Business Continuity Planning (BCP), Disaster Recovery (DR), and IT resilience programs. He wants a concise, structured daily brief on major AI provider changes so he can decide which tool to use for which task — and see how those changes are trending over time.

**Output contract — read this first.** The durable deliverables are, in priority order: (1) the local HTML file, (2) history.json, (3) the Gmail draft. The Cowork artifact is a best-effort mirror ONLY. The artifact store currently fails — `update_artifact` and `create_artifact` both return "Failed to save artifact" (diagnosed 2026-07-18, re-verified 2026-07-25). **No step may be gated on artifact success.** Produce every durable output first, attempt the artifact last, and report its failure without treating the run as failed.

WORKING DIRECTORY: /Users/chrisgiven/Documents/Claude/Scheduled/ai-daily-brief-refresh/
HISTORY FILE: <WORKING DIRECTORY>/history.json

========== STEP 0: LOAD HISTORY ==========
Read the history file with the Read tool. Parse the JSON. If missing or empty, skip trend analysis and note "First run — no history yet" in the Trend Tracker.

Track: LAST_WEEK_ENTRY (closest to today − 7 days, or null) · LAST_MONTH_ENTRY (closest to today − 30 days, or null) · ALL_ENTRIES (full list, for velocity).

========== STEP 1: RESEARCH (run in parallel) ==========
Use WebSearch, targeting the LAST 24–48 HOURS. Derive today's date first and use the current year in every query. Batch into a single message where possible.

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

Community signal:
- "reddit r/ClaudeAI top posts [this week, current year]"
- "reddit r/LocalLLaMA top posts [this week, current year]"
- "reddit r/OpenAI top discussion [this week, current year]"

BCP/DR relevance:
- "AI business continuity disaster recovery news [current month, current year]"
- "AI tools compliance ISO 22301 NIST [current month, current year]"

========== STEP 2: SYNTHESIZE ==========
1. **Top 3 Moves of the Day** — the three most important changes today (not just this month). Each a 1–2 sentence card with a date stamp.
2. **Provider-by-Provider Updates** — table: Provider | What Changed | Classification (Tactical/Strategic/Client Alert). Cover OpenAI, Anthropic, Google Gemini, xAI, Meta, Mistral, Perplexity, Microsoft 365 Copilot, GitHub Copilot, Cursor, Gamma, Notion AI. If no material update, say "No headline release today" and note what to watch for.
3. **Shift Your Habits — BCP/DR Consulting Workflow** — table: Task | Current Tool (assumed) | Recommended Shift | Type (Tactical/Strategic). Cover daily: BCP/DR plan narratives & runbooks; standards summaries (ISO 22301, NIST SP 800-34, SOC 2); vendor/architecture research; client proposals & SOWs; executive decks; stakeholder audio walkthroughs; client advisory on AI data risk.
4. **Community Signal (Reddit)** — 3–5 items max, table: Source | Signal | So What. Visible high engagement only; skip memes and speculation.
5. **Watch List — Next 7–14 Days** — 3–5 cards for upcoming releases, policy changes, deadlines. Flag anything affecting client data handling, training policies, or pricing transitions.
6. If any item is a **client data risk** (training policy changes, data-residency shifts, supply-chain disclosures like "powered by X"), add a callout banner at the top labeled "BCP/DR client alert."

========== STEP 2b: TREND SIGNALS ==========
**A. Provider Velocity** — over ALL_ENTRIES for the last 30 days, count entries with `active: true` per provider:
🔥 HOT = 4+ of last 4 · ↑ RISING = 3 of 4 · → STEADY = 2 of 4 · ↓ COOLING = 1 of 4 · ⬜ QUIET = 0 of 4. Fewer than 4 entries: use what exists, note "Limited history."
**B. Week-over-Week Delta** — vs LAST_WEEK_ENTRY: NEW THIS WEEK / CONTINUED (note same topic = "Persistent Signal") / WENT QUIET.
**C. Month-over-Month** — vs LAST_MONTH_ENTRY: consistently active providers, active→quiet flips, client-alert rate direction.
**D. Persistent Signals** — topic appearing in both today's and last week's headlines for the same provider: "Persistent Signal — [n] weeks."
**E. Quiet Streak** — provider with active=false for 2+ consecutive entries: "Gone Quiet — [n] days."

========== STEP 3: BUILD THE HTML ==========
Produce a COMPLETE self-contained HTML document. Style requirements:
- `:root { color-scheme: light }`, background #fafafa, text #1a1a1a
- Header: h1 "AI Daily Brief", subtitle "Prepared for Chris G. — IT Consultant, BCP/DR & Resilience", right-aligned stamp with today's date and "Refreshes daily at 6:00 AM local"
- Section headings uppercase, letter-spaced, thin bottom border
- Top 3 Moves as 3 cards: `grid-template-columns: repeat(auto-fit, minmax(260px, 1fr))`
- Tag classes: `.tag.tactical` (blue), `.tag.strategic` (purple), `.tag.alert` (red), `.tag.watch` (amber), pill-style
- Client-alert callout: background #fffbea, left border #c99400
- Trend Tracker: dark slate (#1e293b) header, colored velocity badges
- All CSS inline in a `<style>` block. No external stylesheets, no network dependencies. Valid HTML5.
- Footer with today's date and a brief sources-consulted sentence.

Sections in order: 1 Header · 2 BCP/DR Client Alert banner (if applicable) · 3 Top 3 Moves (cards) · 4 Trend Tracker · 5 Provider-by-Provider (table) · 6 Shift Your Habits (table) · 7 Community Signal (table) · 8 Watch List (cards) · 9 Footer.

**TREND TRACKER SPEC** — heading "TREND TRACKER", three sub-panels:
- Panel A — Provider Velocity table: Provider | 30-Day Velocity | W/W Change | Key Signal. Badge colors: 🔥 HOT #fee2e2/#b91c1c · ↑ RISING #dcfce7/#15803d · → STEADY #dbeafe/#1d4ed8 · ↓ COOLING #f3f4f6/#6b7280 · ⬜ QUIET #f9fafb/#9ca3af. W/W column: "New this week" / "Continued" / "Went quiet" / "Persistent ⚠️". Fewer than 2 history entries: muted italic row "Building history — check back next week".
- Panel B — Persistent Signals (omit entirely if none): amber-left-border callout, "[Provider] — [topic] — [n] weeks running".
- Panel C — Month Snapshot (omit if no LAST_MONTH_ENTRY): 2-column "30 Days Ago" vs "Today" — active provider count, client alert count, top themes.

No refresh button. No connector calls from inside the HTML — it is a static snapshot.

========== STEP 4: WRITE LOCAL FILE (REQUIRED) ==========
Write the complete HTML with the Write tool to BOTH:
- `<WORKING DIRECTORY>/ai-daily-brief-<YYYY-MM-DD>.html`
- `<WORKING DIRECTORY>/ai-daily-brief.html` (stable "latest" pointer)
This step is unconditional and must complete before steps 5–7.

========== STEP 5: SAVE HISTORY (REQUIRED — NOT gated on the artifact) ==========
Read history.json, append today's entry:
{
  "date": "YYYY-MM-DD",
  "providers": { "[ProviderName]": { "headline": "[1-sentence summary or 'No update today']", "tags": ["tactical"|"strategic"|"alert"], "hasAlert": true|false, "alertReason": "[if hasAlert]", "active": true|false }, ... all 12 providers },
  "topMoves": ["move1","move2","move3"],
  "clientAlerts": ["alert1", ...],
  "watchItems": ["item1", ...]
}
Trim to the most recent 60 entries. Write back with the Write tool.

========== STEP 6: EMAIL DRAFT (REQUIRED — NOT gated on the artifact) ==========
Call mcp__9a815f15-06b6-4c12-b516-de5f058e68d1__create_draft with:
- to: ["chris.given@gmail.com", "chris.given@wwt.com", "mikebannach@gmail.com"]
- subject: "AI Daily Brief — [today's date, e.g. July 25, 2026]"
- htmlBody: the exact HTML from Step 3
A Google Apps Script sends the draft within 5 minutes. If create_draft fails, note the error in Step 8 and do not retry.

========== STEP 7: ARTIFACT MIRROR (BEST-EFFORT — LAST) ==========
Call mcp__cowork__update_artifact with id "ai-daily-brief", update_summary "Daily refresh — [today's date]", and the Step 3 HTML. If it does not exist, try create_artifact with the same id. **One attempt. No retries. Failure here is not a run failure** — steps 4–6 already delivered. Capture the exact error text.

========== STEP 8: CONFIRM ==========
Reply in 5 sentences: (1) the single biggest change to flag to Chris today, (2) any client-alert items, (3) the most notable trend signal (most active provider, persistent signals, providers gone quiet), (4) confirmation that the local HTML file, history.json, and email draft were all written — name the file path, (5) artifact mirror status: succeeded, or failed with the error text. If the artifact has failed 3+ consecutive runs, say so plainly.
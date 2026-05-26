---
name: ai-daily-brief-refresh
description: Daily AI industry brief — researches major AI providers + Reddit signal, synthesizes habit-shift recommendations for Chris's BCP/DR consulting work, rewrites the ai-daily-brief artifact and emails it to chris.given@gmail.com and chris.given@wwt.com
---

You are generating today's edition of Chris's "AI Daily Brief" live artifact. Chris is an IT consultant specializing in Business Continuity Planning (BCP), Disaster Recovery (DR), and IT resilience programs. He wants a concise, structured daily brief on major AI provider changes so he can decide which tool to use for which task.

========== STEP 1: RESEARCH (run in parallel) ==========
Use the WebSearch tool to run these searches, all targeting the LAST 24-48 HOURS. Use the current year in every query (derive today's date first). Run them in a single batched message when possible.

Provider searches (required):
- "OpenAI ChatGPT new features release [this week, current year]"
- "Anthropic Claude release notes [current month, current year]"
- "Google Gemini new model features [current month, current year]"
- "xAI Grok release news [current month, current year]"
- "Meta AI Llama Muse release [current month, current year]"
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
2. **Provider-by-Provider Updates** — table with columns: Provider | What Changed | Classification (Tactical/Strategic/Client Alert). Include: OpenAI, Anthropic, Google Gemini, xAI, Meta, Mistral, Perplexity, Microsoft 365 Copilot, GitHub Copilot, Cursor, Gamma. If a provider has no material update in the last 24–48h, say "No headline release today" and note what to watch for.
3. **Shift Your Habits — BCP/DR Consulting Workflow** — table with columns: Task | Current Tool (assumed) | Recommended Shift | Type (Tactical/Strategic). Cover these tasks every day: drafting BCP/DR plan narratives & runbooks; summarizing standards (ISO 22301, NIST SP 800-34, SOC 2); vendor/architecture research; client proposals & SOWs; executive decks; stakeholder audio walkthroughs; client advisory on AI data risk.
4. **Community Signal (Reddit)** — 3–5 items max, table with columns: Source | Signal | So What. Filter for posts with visible high engagement; skip memes and pure speculation.
5. **Watch List — Next 7–14 Days** — 3–5 cards for upcoming releases, policy changes, or deadlines. Flag anything that affects client data handling, training policies, or pricing transitions.
6. If any item is a **client data risk** (training policy changes, data-residency shifts, supply-chain disclosures like "powered by X"), add a callout banner at the top of the brief labeled "BCP/DR client alert."

========== STEP 3: UPDATE THE ARTIFACT ==========
Call mcp__cowork__update_artifact with:
- id: "ai-daily-brief"
- update_summary: "Daily refresh — [today's date]"
- html: a COMPLETE self-contained HTML document matching the visual style of the existing artifact. Critical style requirements:
  * :root { color-scheme: light } and light background (#fafafa) with dark text (#1a1a1a)
  * Header with h1 "AI Daily Brief", subtitle "Prepared for Chris G. — IT Consultant, BCP/DR & Resilience", and a right-aligned stamp showing today's date and "Refreshes daily at 6:00 AM local"
  * Section headings are uppercase, letter-spaced, with a thin bottom border
  * Top 3 Moves rendered as 3 cards in a responsive grid (grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)))
  * Tag classes: .tag.tactical (blue), .tag.strategic (purple), .tag.alert (red) for pill-style labels in the classification column
  * BCP/DR client-alert callout (if any) styled with yellow-amber background (#fffbea) and left border (#c99400)
  * Inline all CSS in a <style> block — no external stylesheets
  * Footer with today's date and a brief sources-consulted sentence
  * Must be syntactically valid HTML5 with no external network dependencies (sandboxed view)

Do NOT add a refresh button — Cowork's artifact view has a built-in reload. Do NOT call connectors from inside the HTML — the artifact is a static snapshot rewritten once per day by this task.

========== STEP 4: CREATE EMAIL DRAFT ==========
After update_artifact succeeds, call mcp__9a815f15-06b6-4c12-b516-de5f058e68d1__create_draft with:
- to: ["chris.given@gmail.com", "chris.given@wwt.com"]
- subject: "AI Daily Brief — [today's date, formatted e.g. May 7, 2026]"
- htmlBody: the exact same complete HTML document you passed to update_artifact in Step 3

This creates a Gmail draft that a Google Apps Script will automatically send 15 minutes later. If create_draft fails, note the error in your Step 5 confirmation but do not retry — the artifact update is the primary deliverable.

========== STEP 5: CONFIRM ==========
After both steps complete, reply with a 3-sentence summary covering: (1) the single biggest change to flag to Chris today, (2) any client-alert items surfaced, (3) confirmation the artifact was refreshed and the email draft was created.

#!/usr/bin/env python3
"""AI Daily Brief — trend summary, email-safe renderer, and history keeper.

Why: each run used to Read the full history.json (~410 KB, ~100K tokens) and the previous
edition (~46 KB), then hand-write ~46 KB of inline-styled HTML. Now:

    python3 brief.py trends                 # ~1K-token summary of history for synthesis
    python3 brief.py render content.json    # writes dated + latest HTML, appends history

The renderer computes Panel A (velocity, W/W) and Panel C counts from history itself, so
Claude only supplies today's facts. Trimmed to the most recent 60 history entries.

content.json:
{
  "date": "2026-09-10",                                  # optional, defaults to today
  "client_alerts": [{"headline": "...", "body": "..."}], # [] = no banner
  "top_moves": [{"title", "date_label", "urgent": false, "body", "tag": "tactical|strategic|watch|alert"}] x3,
  "providers": [{"name": "OpenAI", "display": "OpenAI", "headline": "1-sentence key signal",
                 "detail": "table text (**bold** ok)", "tags": ["tactical"], "active": true,
                 "hasAlert": false, "alertReason": ""}, ... 12 providers],
  "persistent_signals": [{"provider": "xAI", "text": "xAI — Grok 4.7 countdown — 2+ weeks running (...)"}],
  "month_themes": {"then": "...", "now": "..."},         # optional; falls back to topMoves
  "habits": [{"task", "tool", "shift", "type": "tactical|strategic|watch"}],
  "community": [{"source", "signal", "so_what"}],
  "watch": [{"kind": "watch|deadline|security|regulatory|pricing", "title", "body"}],
  "sources": "Sources consulted: ..."
}
"""

import argparse
import html
import json
import re
import shutil
import sys
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
HISTORY = HERE / "history.json"
KEEP = 60
PROVIDERS = ["OpenAI", "Anthropic", "Google Gemini", "xAI", "Meta", "Mistral", "Perplexity",
             "Microsoft 365 Copilot", "GitHub Copilot", "Cursor", "Gamma", "Notion AI"]
QUIET_DAYS_LABEL = 14  # "Gone quiet — N days" once a provider has been silent this long

PILL = {
    "tactical": ("Tactical", "#dbeafe", "#1e40af"), "strategic": ("Strategic", "#ede9fe", "#6d28d9"),
    "watch": ("Watch", "#fef3c7", "#92400e"), "alert": ("Client Alert", "#fee2e2", "#b91c1c"),
}
VELOCITY = [  # active count in last 4 entries -> badge
    ("&#11036; QUIET", "#f9fafb", "#9ca3af", "; border:1px solid #e5e7eb"),
    ("&#8595; COOLING", "#f3f4f6", "#6b7280", ""),
    ("&#8594; STEADY", "#dbeafe", "#1d4ed8", ""),
    ("&#8593; RISING", "#dcfce7", "#15803d", ""),
    ("&#128293; HOT", "#fee2e2", "#b91c1c", ""),
]
WATCH_KIND = {
    "watch": ("&#128269; Watch", "#6d28d9"), "deadline": ("&#128176; Deadline", "#92400e"),
    "pricing": ("&#128176; Pricing", "#92400e"), "security": ("&#9888; Security", "#b91c1c"),
    "regulatory": ("&#9888; Regulatory", "#b91c1c"),
}
TH = ("text-align:left; padding:9px 12px; background-color:#f9fafb; border-bottom:1px solid #e5e7eb; "
      "font-size:11px; text-transform:uppercase; letter-spacing:0.05em; color:#6b7280;")
SECTION = ('  <div style="font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:0.1em; '
           'color:#6b7280; border-bottom:1px solid #e5e7eb; padding-bottom:7px; margin:0 0 14px;">{}</div>\n')


def rich(s):
    """Escape, then allow **bold** — the only markup Claude needs."""
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html.escape(s or "", quote=False))


def E(s):
    return html.escape(s or "", quote=False)


def short(d):
    return ("Sept" if d.month == 9 else f"{d:%b}") + f" {d.day}"


def long(d):
    return f"{d:%B} {d.day}, {d.year}"


# ---------------------------------------------------------------- history
def load_history():
    try:
        h = json.loads(HISTORY.read_text())
    except (OSError, ValueError):
        return []
    return h if isinstance(h, list) else h.get("entries", [])


def closest(entries, target, max_off=4):
    best = None
    for e in entries:
        off = abs((date.fromisoformat(e["date"]) - target).days)
        if off <= max_off and (best is None or off < best[0]):
            best = (off, e)
    return best[1] if best else None


def active(entry, name):
    return bool(((entry or {}).get("providers") or {}).get(name, {}).get("active"))


def last_active(entries, name):
    for e in reversed(entries):
        if active(e, name):
            return date.fromisoformat(e["date"])
    return None


def analyse(prior, today, today_active):
    """Velocity / W/W / quiet streak per provider. `prior` excludes today's entry."""
    window = prior[-3:]
    last_week = closest(prior, today - timedelta(days=7))
    last_month = closest(prior, today - timedelta(days=30))
    rows = {}
    for p in PROVIDERS:
        now = today_active.get(p, False)
        n = sum(active(e, p) for e in window) + (1 if now else 0)
        was = active(last_week, p) if last_week else None
        la = today if now else last_active(prior, p)
        quiet_days = (today - la).days if la else None
        rows[p] = {"velocity": min(n, 4), "now": now, "last_week": was, "quiet_days": quiet_days,
                   "last_week_headline": ((last_week or {}).get("providers") or {}).get(p, {}).get("headline")}
    return {"window": [e["date"] for e in window] + [today.isoformat()], "last_week": last_week,
            "last_month": last_month, "rows": rows}


def cmd_trends(args):
    today = date.fromisoformat(args.date) if args.date else date.today()
    entries = [e for e in load_history() if e["date"] < today.isoformat()]
    if not entries:
        print("First run — no history yet.")
        return 0
    a = analyse(entries, today, {})
    lw, lm = a["last_week"], a["last_month"]
    print(f"History: {len(entries)} entries, latest {entries[-1]['date']}. "
          f"Velocity window = last 3 entries ({', '.join(a['window'][:-1])}) + today.")
    print(f"Last-week entry: {lw['date'] if lw else 'none'} · Last-month entry: {lm['date'] if lm else 'none'}")
    print("\nprovider | active in last 3 | last active | last-week headline")
    for p, r in a["rows"].items():
        la = f"{r['quiet_days']}d ago" if r["quiet_days"] is not None else "never"
        print(f"- {p} | {r['velocity']}/3 | {la} | {(r['last_week_headline'] or '—')[:150]}")
    print("\nYesterday's top moves (avoid repeating as 'new'): " +
          " / ".join(entries[-1].get("topMoves", [])[:3]))
    if lm:
        n = sum(active(lm, p) for p in PROVIDERS)
        print(f"\nMonth-ago ({lm['date']}): {n} of 12 active, {len(lm.get('clientAlerts', []))} client alerts; "
              f"top moves: " + " / ".join(lm.get("topMoves", [])[:3]))
    print("\nPersistent signal = same topic for the same provider in today's AND last week's headline. "
          "Pass those in content.json persistent_signals.")
    return 0


# ---------------------------------------------------------------- render
def pill(tag, pad="8px"):
    label, bg, fg = PILL.get((tag or "").lower(), PILL["tactical"])
    return (f'<span style="display:inline-block; padding:2px {pad}; border-radius:999px; font-size:11px; '
            f'font-weight:600; background-color:{bg}; color:{fg};">{label}</span>')


def rows_html(rows, cell_fn):
    out = []
    for i, r in enumerate(rows):
        last = i == len(rows) - 1
        out.append("      <tr>\n" + "".join(cell_fn(r, last)) + "      </tr>\n")
    return "".join(out)


def td(content, style, last, pad="10px 12px"):
    border = "" if last else " border-bottom:1px solid #f3f4f6;"
    return f'        <td style="padding:{pad};{border}{style}">{content}</td>\n'


def header(d):
    return f'''  <!-- 1. HEADER -->
  <table style="width:100%; border-collapse:collapse; margin:20px 0 4px;">
    <tr>
      <td style="vertical-align:bottom; padding:0;">
        <h1 style="margin:0 0 4px; font-size:26px; font-weight:700; color:#1a1a1a; letter-spacing:-0.01em;">AI Daily Brief</h1>
        <div style="font-size:13px; color:#6b7280;">Prepared for Chris G. — IT Consultant, BCP/DR &amp; Resilience</div>
      </td>
      <td style="vertical-align:bottom; text-align:right; padding:0;">
        <div style="font-size:15px; font-weight:700; color:#1a1a1a;">{long(d)}</div>
        <div style="font-size:11px; color:#9ca3af;">Refreshes daily at 6:00 AM local</div>
      </td>
    </tr>
  </table>
  <div style="height:3px; background-color:#1e293b; margin:0 0 22px;"></div>

'''


def alert_banner(alerts):
    if not alerts:
        return ""
    n = len(alerts)
    body = "".join(
        f'    <p style="margin:{"0" if i == n - 1 else "0 0 10px"}; font-size:14px; color:#3f3000;">'
        f'<strong style="color:#1a1a1a;">{E(a["headline"])}</strong> {rich(a.get("body"))}</p>\n'
        for i, a in enumerate(alerts))
    return ('  <!-- 2. CLIENT ALERT -->\n'
            '  <div style="background-color:#fffbea; border-left:4px solid #c99400; border-radius:0 8px 8px 0; padding:14px 18px; margin:0 0 26px;">\n'
            f'    <div style="font-size:13px; font-weight:700; color:#7c5e00; text-transform:uppercase; letter-spacing:0.06em; margin:0 0 10px;">&#9888; BCP/DR Client Alert — {n} Active Item{"s" if n > 1 else ""}</div>\n'
            f'{body}  </div>\n\n')


def top_moves(moves):
    cells = []
    for i, m in enumerate(moves[:3], 1):
        dcol = "#b91c1c" if m.get("urgent") else "#6b7280"
        cells.append(f'''      <td style="width:33%; vertical-align:top; background-color:#ffffff; border:1px solid #e5e7eb; border-radius:8px; padding:15px;">
        <div style="font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; color:#9ca3af; margin:0 0 6px;">Move #{i}</div>
        <div style="font-size:15px; font-weight:700; color:#1a1a1a; margin:0 0 5px; line-height:1.3;">{E(m["title"])}</div>
        <div style="font-size:11px; color:{dcol}; font-weight:600; margin:0 0 8px;">{E(m.get("date_label", ""))}</div>
        <div style="font-size:13px; color:#4b5563; margin:0 0 10px;">{rich(m.get("body"))}</div>
        <div>{pill(m.get("tag"), "9px")}</div>
      </td>
''')
    return ('  <!-- 3. TOP 3 MOVES -->\n' + SECTION.format("Top 3 Moves of the Day") +
            '  <table style="width:100%; border-collapse:separate; border-spacing:10px 0; margin:0 0 28px;">\n    <tr>\n'
            + "".join(cells) + '    </tr>\n  </table>\n\n')


def ww_cell(p, r, persistent):
    if r["last_week"] is None:
        return "&mdash;", "#9ca3af"
    if r["now"] and r["last_week"]:
        return ("Persistent &#9888;&#65039;", "#b45309") if p in persistent else ("Continued", "#1d4ed8")
    if r["now"]:
        return "New this week", "#15803d"
    if r["last_week"]:
        return "Went quiet", "#b91c1c"
    if r["quiet_days"] is not None and r["quiet_days"] >= QUIET_DAYS_LABEL:
        return f"Gone quiet &mdash; {r['quiet_days']} days", "#9ca3af"
    return "&mdash;", "#9ca3af"


def trend_tracker(d, a, providers, persistent, month_themes, prior_count):
    lw = a["last_week"]
    window = ", ".join(str(date.fromisoformat(x).day) for x in a["window"])
    month = short(date.fromisoformat(a["window"][0])).split(" ")[0]
    note = (f"Velocity computed over the last {len(a['window'])} recorded entries ({month} {window}). "
            + (f"W/W compares against {short(date.fromisoformat(lw['date']))} (closest entry to 7 days ago)." if lw
               else "No entry near 7 days ago yet."))
    out = ['  <!-- 4. TREND TRACKER -->\n', SECTION.format("Trend Tracker"),
           '  <div style="background-color:#1e293b; color:#ffffff; padding:12px 16px; border-radius:8px 8px 0 0;">\n'
           '    <div style="font-size:13px; font-weight:700; letter-spacing:0.06em; text-transform:uppercase;">Panel A &mdash; Provider Velocity</div>\n'
           f'    <div style="font-size:11px; color:#94a3b8; margin-top:3px;">{note}</div>\n  </div>\n'
           '  <table style="width:100%; border-collapse:collapse; background-color:#ffffff; border:1px solid #e5e7eb; border-top:none; margin:0 0 18px; font-size:13px;">\n'
           '    <thead>\n      <tr>\n'
           + "".join(f'        <th style="{TH}">{h}</th>\n' for h in ("Provider", "30-Day Velocity", "W/W Change", "Key Signal Today"))
           + '      </tr>\n    </thead>\n    <tbody>\n']
    if prior_count < 2:
        out.append('      <tr>\n        <td colspan="4" style="padding:12px; color:#9ca3af; font-style:italic;">'
                   'Building history — check back next week</td>\n      </tr>\n')
    else:
        by = {p["name"]: p for p in providers}

        def cells(p, last):
            r = a["rows"][p]
            label, bg, fg, extra = VELOCITY[r["velocity"]]
            ww, col = ww_cell(p, r, persistent)
            return [td(E(p), " font-weight:600;", last, "9px 12px"),
                    td(f'<span style="display:inline-block; padding:2px 8px; border-radius:999px; font-size:11px; '
                       f'font-weight:700; background-color:{bg}; color:{fg}{extra};">{label}</span>', "", last, "9px 12px"),
                    td(ww, f" color:{col}; font-weight:600;", last, "9px 12px"),
                    td(E(by.get(p, {}).get("headline", "")), " color:#4b5563;", last, "9px 12px")]
        out.append(rows_html(PROVIDERS, cells))
    out.append('    </tbody>\n  </table>\n\n')

    if persistent:
        body = "".join(f'    <p style="margin:{"0" if i == len(persistent) - 1 else "0 0 6px"}; font-size:13px; color:#3f3000;">{E(s["text"])}</p>\n'
                       for i, s in enumerate(persistent.values()))
        out.append('  <div style="background-color:#fffbea; border-left:4px solid #c99400; border-radius:0 8px 8px 0; padding:12px 16px; margin:0 0 18px;">\n'
                   '    <div style="font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:0.06em; color:#7c5e00; margin:0 0 8px;">Panel B &mdash; Persistent Signals</div>\n'
                   f'{body}  </div>\n\n')

    lm = a["last_month"]
    if lm:
        then_active = sum(active(lm, p) for p in PROVIDERS)
        now_active = sum(1 for p in providers if p.get("active"))
        then_alerts = len(lm.get("clientAlerts") or [])
        now_alerts = sum(1 for p in providers if p.get("hasAlert")) or None

        def delta(now, then, good_when_up, fmt):
            diff = now - then
            if diff == 0:
                return f"{fmt(now)} &nbsp;&#9654; flat", "#6b7280"
            arrow, sign = ("&#9650;", "+") if diff > 0 else ("&#9660;", "&minus;")
            good = (diff > 0) == good_when_up
            return f"{fmt(now)} &nbsp;{arrow} {sign}{abs(diff)}", "#15803d" if good else "#b91c1c"
        act_txt, act_col = delta(now_active, then_active, True, lambda n: f"{n} of 12")
        alerts_now = now_alerts if now_alerts is not None else 0
        al_txt, al_col = delta(alerts_now, then_alerts, False, str)
        themes = month_themes or {}
        then_t = themes.get("then") or "; ".join(lm.get("topMoves", [])[:3])
        now_t = themes.get("now") or ""
        mth = ('style="width:{w}; text-align:left; padding:9px 16px; background-color:#f9fafb; border-bottom:1px solid #e5e7eb; '
               'font-size:11px; text-transform:uppercase; letter-spacing:0.05em; color:#6b7280;"')
        out.append(f'''  <div style="background-color:#ffffff; border:1px solid #e5e7eb; border-radius:8px; padding:0; margin:0 0 28px;">
    <div style="background-color:#1e293b; color:#ffffff; padding:11px 16px; border-radius:7px 7px 0 0; font-size:13px; font-weight:700; letter-spacing:0.06em; text-transform:uppercase;">Panel C &mdash; Month Snapshot</div>
    <table style="width:100%; border-collapse:collapse; font-size:13px;">
      <tr>
        <th {mth.format(w="34%")}>Measure</th>
        <th {mth.format(w="33%")}>30 Days Ago ({short(date.fromisoformat(lm["date"]))})</th>
        <th {mth.format(w="33%")}>Today ({short(d)})</th>
      </tr>
      <tr>
        <td style="padding:9px 16px; border-bottom:1px solid #f3f4f6; font-weight:600;">Active providers</td>
        <td style="padding:9px 16px; border-bottom:1px solid #f3f4f6; color:#4b5563;">{then_active} of 12</td>
        <td style="padding:9px 16px; border-bottom:1px solid #f3f4f6; color:{act_col}; font-weight:600;">{act_txt}</td>
      </tr>
      <tr>
        <td style="padding:9px 16px; border-bottom:1px solid #f3f4f6; font-weight:600;">Client alerts</td>
        <td style="padding:9px 16px; border-bottom:1px solid #f3f4f6; color:#4b5563;">{then_alerts}</td>
        <td style="padding:9px 16px; border-bottom:1px solid #f3f4f6; color:{al_col}; font-weight:600;">{al_txt}</td>
      </tr>
      <tr>
        <td style="padding:9px 16px; font-weight:600; vertical-align:top;">Top themes</td>
        <td style="padding:9px 16px; color:#4b5563; vertical-align:top;">{E(then_t)}</td>
        <td style="padding:9px 16px; color:#4b5563; vertical-align:top;">{E(now_t)}</td>
      </tr>
    </table>
  </div>

''')
    return "".join(out)


def table(title, comment, cols, rows, cell_fn):
    head = "".join(f'        <th style="width:{w}; {TH}">{h}</th>\n' for h, w in cols)
    return (f'  <!-- {comment} -->\n' + SECTION.format(title) +
            '  <table style="width:100%; border-collapse:collapse; background-color:#ffffff; border:1px solid #e5e7eb; margin:0 0 28px; font-size:13px;">\n'
            f'    <thead>\n      <tr>\n{head}      </tr>\n    </thead>\n    <tbody>\n'
            + rows_html(rows, cell_fn) + '    </tbody>\n  </table>\n\n')


def watch_list(items):
    cards = []
    for w in items:
        label, col = WATCH_KIND.get((w.get("kind") or "watch").lower(), WATCH_KIND["watch"])
        cards.append(f'''    <tr>
      <td style="background-color:#ffffff; border:1px solid #e5e7eb; border-left:4px solid {col}; border-radius:0 8px 8px 0; padding:13px 16px;">
        <div style="font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.06em; color:{col}; margin:0 0 4px;">{label}</div>
        <div style="font-size:14px; font-weight:700; color:#1a1a1a; margin:0 0 4px;">{E(w["title"])}</div>
        <div style="font-size:13px; color:#4b5563;">{rich(w.get("body"))}</div>
      </td>
    </tr>
''')
    return ('  <!-- 8. WATCH LIST -->\n'
            '  <div style="font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:0.1em; color:#6b7280; border-bottom:1px solid #e5e7eb; padding-bottom:7px; margin:0 0 24px;">Watch List &mdash; Next 7&ndash;14 Days</div>\n'
            '  <table style="width:100%; border-collapse:separate; border-spacing:0 8px; margin:0 0 24px;">\n'
            + "".join(cards) + '  </table>\n\n')


def footer(d, sources):
    return f'''  <!-- 9. FOOTER -->
  <div style="border-top:1px solid #e5e7eb; padding-top:14px; margin-top:8px;">
    <p style="margin:0 0 6px; font-size:12px; color:#6b7280;"><strong style="color:#1a1a1a;">AI Daily Brief &mdash; {long(d)}</strong> &nbsp;|&nbsp; Prepared for Chris G., IT Consultant, BCP/DR &amp; Resilience</p>
    <p style="margin:0 0 6px; font-size:11px; color:#9ca3af; line-height:1.5;">{E(sources)}</p>
    <p style="margin:0; font-size:11px; color:#9ca3af;">Generated by Claude (Anthropic) &middot; Automated daily brief &middot; Static snapshot, no live connections.</p>
  </div>
'''


def render(c, prior):
    d = date.fromisoformat(c["date"]) if c.get("date") else date.today()
    providers = c["providers"]
    names = {p["name"] for p in providers}
    missing = [p for p in PROVIDERS if p not in names]
    if missing:
        raise SystemExit(f"content.json is missing providers: {missing}")
    today_active = {p["name"]: bool(p.get("active")) for p in providers}
    a = analyse(prior, d, today_active)
    persistent = {s["provider"]: s for s in c.get("persistent_signals") or []}
    ordered = sorted(providers, key=lambda p: PROVIDERS.index(p["name"]))

    def prov_cells(p, last):
        tag = p.get("classification") or (p.get("tags") or [None])[0]
        cls = (td(pill(tag), " vertical-align:top;", last) if tag and tag in PILL
               else td("&mdash;", " color:#9ca3af; vertical-align:top;", last))
        return [td(E(p.get("display") or p["name"]), " font-weight:700; vertical-align:top;", last),
                td(rich(p.get("detail") or p.get("headline")), " color:#4b5563; vertical-align:top;", last), cls]

    def habit_cells(h, last):
        return [td(E(h["task"]), " font-weight:600; vertical-align:top;", last),
                td(E(h.get("tool")), " color:#6b7280; vertical-align:top;", last),
                td(rich(h.get("shift")), " color:#4b5563; vertical-align:top;", last),
                td(pill(h.get("type")), " vertical-align:top;", last)]

    def comm_cells(x, last):
        return [td(E(x["source"]), " font-weight:600; vertical-align:top;", last),
                td(rich(x.get("signal")), " color:#4b5563; vertical-align:top;", last),
                td(rich(x.get("so_what")), " color:#4b5563; vertical-align:top;", last)]

    body = (header(d) + alert_banner(c.get("client_alerts") or []) + top_moves(c["top_moves"])
            + trend_tracker(d, a, ordered, persistent, c.get("month_themes"), len(prior))
            + table("Provider-by-Provider Updates", "5. PROVIDER BY PROVIDER",
                    [("Provider", "16%"), ("What Changed", "62%"), ("Classification", "22%")], ordered, prov_cells)
            + table("Shift Your Habits &mdash; BCP/DR Consulting Workflow", "6. SHIFT YOUR HABITS",
                    [("Task", "22%"), ("Current Tool", "18%"), ("Recommended Shift", "45%"), ("Type", "15%")],
                    c.get("habits") or [], habit_cells)
            + table("Community Signal", "7. COMMUNITY SIGNAL",
                    [("Source", "18%"), ("Signal", "41%"), ("So What", "41%")], c.get("community") or [], comm_cells)
            + watch_list(c.get("watch") or []) + footer(d, c.get("sources", "")))
    doc = ('<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
           '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
           f'<title>AI Daily Brief — {long(d)}</title>\n</head>\n'
           '<body style="margin:0; padding:0; background-color:#fafafa; color:#1a1a1a; font-family:-apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, Helvetica, Arial, sans-serif; font-size:15px; line-height:1.55;">\n\n'
           '<div style="max-width:900px; margin:0 auto; padding:0 16px 40px;">\n\n'
           + body + '\n</div>\n\n</body>\n</html>\n')
    return d, doc


def history_entry(c, d):
    return {
        "date": d.isoformat(),
        "providers": {p["name"]: {k: v for k, v in {
            "headline": p.get("headline") or "No update today", "tags": p.get("tags") or [],
            "hasAlert": bool(p.get("hasAlert")), "alertReason": p.get("alertReason") or None,
            "active": bool(p.get("active"))}.items() if v is not None} for p in c["providers"]},
        "topMoves": [m["title"] for m in c["top_moves"]],
        "clientAlerts": [a["headline"] for a in c.get("client_alerts") or []],
        "watchItems": [w["title"] for w in c.get("watch") or []],
    }


def cmd_render(args):
    c = json.loads(Path(args.content).read_text())
    d = date.fromisoformat(c["date"]) if c.get("date") else date.today()
    history = load_history()
    prior = [e for e in history if e["date"] < d.isoformat()]
    d, doc = render(c, prior)
    styles = doc.count('style="')
    problems = []
    if "<style" in doc:
        problems.append("contains <style")
    if styles < 150:
        problems.append(f"only {styles} inline styles (expected 150+)")
    if "var(--" in doc or "display:flex" in doc or "display:grid" in doc:
        problems.append("contains CSS vars, flexbox or grid")
    out = Path(args.out) if args.out else HERE
    out.mkdir(parents=True, exist_ok=True)
    dated, latest = out / f"ai-daily-brief-{d.isoformat()}.html", out / "ai-daily-brief.html"
    dated.write_text(doc)
    latest.write_text(doc)
    if not args.out:  # keep each day's content for reference
        (HERE / "content").mkdir(exist_ok=True)
        shutil.copy2(args.content, HERE / "content" / f"content-{d.isoformat()}.json")
    hist_msg = "skipped (--no-history)"
    if not args.no_history:
        if HISTORY.exists():
            shutil.copy2(HISTORY, HISTORY.with_suffix(".json.bak"))
        kept = [e for e in history if e["date"] != d.isoformat()] + [history_entry(c, d)]
        kept.sort(key=lambda e: e["date"])
        HISTORY.write_text(json.dumps(kept[-KEEP:], indent=2, ensure_ascii=False))
        hist_msg = f"appended {d.isoformat()} ({len(kept[-KEEP:])} entries kept)"
    print(json.dumps({"ok": not problems, "problems": problems, "files": [str(dated), str(latest)],
                      "inline_styles": styles, "bytes": len(doc), "history": hist_msg,
                      "subject": f"AI Daily Brief — {long(d)}"}, indent=1, ensure_ascii=False))
    return 0 if not problems else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("trends")
    t.add_argument("--date")
    r = sub.add_parser("render")
    # Fixed default path keeps the command string identical every day, so a saved
    # Bash allow rule matches and the unattended run never waits on a prompt.
    r.add_argument("content", nargs="?", default=str(HERE / "content.json"))
    r.add_argument("--out", help="output directory (default: this folder)")
    r.add_argument("--no-history", action="store_true", help="don't touch history.json (testing)")
    args = ap.parse_args()
    sys.exit({"trends": cmd_trends, "render": cmd_render}[args.cmd](args))


if __name__ == "__main__":
    main()

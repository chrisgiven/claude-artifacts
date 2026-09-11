#!/usr/bin/env python3
"""Render the Global BCDR & Ransomware Monitor from a small content JSON.

Why: the scheduled run used to Read the previous edition (~7K tokens) and hand-write
~26 KB of inline-styled HTML twice. Now Claude writes only the day's items as JSON;
this script owns the email-safe layout, so formatting can't drift edition to edition.

    python3 monitor.py quakes                  # top-5 significant quakes this week (JSON)
    python3 monitor.py render content.json     # writes dated + latest HTML, prints status JSON

content.json:
{
  "date": "2026-09-10",                         # optional, defaults to today
  "sections": {
    "ransomware": {"items": [ITEM, ...], "note": "optional italic footnote", "error": "optional"},
    "outage": {...}, "cyber": {...}, "physical": {...}
  }
}
ITEM = {"title": "...", "tags": ["Critical", "Municipal"], "summary": "...",
        "source": {"name": "BleepingComputer", "url": "https://..."}}
A tag may also be {"label": "High-profile", "tone": "blue"} to force a colour.
Earthquake tags are "M 6.3" and are coloured by magnitude automatically.
"""

import argparse
import html
import json
import re
import shutil
import sys
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
USGS = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_week.geojson"

TONES = {
    "red": ("#fee2e2", "#b91c1c"), "orange": ("#ffedd5", "#c2410c"),
    "yellow": ("#fef9c3", "#a16207"), "blue": ("#dbeafe", "#1d4ed8"),
    "purple": ("#ede9fe", "#6d28d9"), "slate": ("#e2e8f0", "#334155"),
    "quake": ("#e2e8f0", "#475569"),
}
# Most common colour per label across the Aug-Sep 2026 editions.
TAG_TONE = {
    "critical": "red", "emergency directive": "red",
    "high-profile": "orange", "flood": "orange", "wildfire": "orange", "tropical": "orange",
    "ts": "orange", "fema mdd": "orange", "hurricane": "orange", "typhoon": "orange",
    "cloud": "blue", "trend": "blue",
    "data exposure": "yellow", "credential exposure": "yellow", "healthcare": "yellow",
    "kev add": "purple", "zero-day": "purple",
    "education": "slate", "municipal": "slate", "newly claimed": "slate",
    "reference": "slate", "third-party": "slate",
}
SECTIONS = [
    ("ransomware", "🔒 Ransomware", "Ransomware"),
    ("outage", "☁️ IT Outages &amp; Cloud", "Cloud / Outage"),
    ("cyber", "🛡️ Cyber Incidents (non-ransomware)", "Cyber"),
    ("physical", "🌍 Physical / Natural BC Events", "Physical / Natural"),
]


def E(s):
    """Text content: escape <>& only, so quotes/apostrophes stay readable."""
    return html.escape(s or "", quote=False)


def tone_for(label, section):
    m = re.match(r"^M\s?(\d+(?:\.\d+)?)$", label.strip())
    if m:
        mag = float(m.group(1))
        return "red" if mag >= 6.5 else "orange" if mag >= 5.5 else "quake"
    if re.match(r"^cat \d", label.strip().lower()):
        return "orange"
    return TAG_TONE.get(label.strip().lower(), "orange" if section == "physical" else "slate")


def badge(tag, section):
    label, tone = (tag["label"], tag.get("tone")) if isinstance(tag, dict) else (tag, None)
    bg, fg = TONES.get(tone or tone_for(label, section), TONES["slate"])
    return (f'<span style="display:inline-block; font-size:10px; font-weight:700; text-transform:uppercase; '
            f'letter-spacing:0.03em; padding:2px 8px; border-radius:10px; margin-left:6px; vertical-align:middle; '
            f'background-color:{bg}; color:{fg};">{E(label)}</span>')


def item_html(it, last, section):
    border = "none" if last else "1px solid #f1f5f9"
    src = it.get("source") or {}
    link = (f' <a href="{html.escape(src["url"])}" target="_blank" rel="noopener" style="color:#1d4ed8; '
            f'text-decoration:none;">{E(src.get("name") or "Source")}</a>') if src.get("url") else ""
    tags = "".join(badge(t, section) for t in it.get("tags") or [])
    return (f'      <div style="padding:10px 0; border-bottom:{border};">\n'
            f'        <div style="font-weight:600; font-size:14px;">{E(it["title"])}{tags}</div>\n'
            f'        <p style="margin:3px 0 0; font-size:13px; color:#334155;">{E(it.get("summary", ""))}{link}</p>\n'
            f'      </div>\n')


def section_html(key, heading, sec):
    items = sec.get("items") or []
    body = "".join(item_html(it, i == len(items) - 1, key) for i, it in enumerate(items))
    if sec.get("error"):
        body += ('      <div class="error" style="font-size:13px; color:#b91c1c; background-color:#fef2f2; '
                 f'border:1px solid #fecaca; border-radius:6px; padding:8px 10px; margin:8px 0 2px;">⚠ {E(sec["error"])}</div>\n')
    if sec.get("note"):
        body += ('      <div style="font-size:12px; color:#64748b; font-style:italic; padding:6px 0 2px;">'
                 f'{E(sec["note"])}</div>\n')
    return ('  <div style="background-color:#ffffff; border:1px solid #e2e8f0; border-radius:10px; margin:16px 0; overflow:hidden;">\n'
            f'    <h2 style="margin:0; padding:12px 18px; font-size:15px; background-color:#f8fafc; border-bottom:1px solid #e2e8f0; color:#0f172a;">{heading}</h2>\n'
            '    <div style="padding:6px 18px 14px;">\n'
            f'{body}'
            '    </div>\n'
            '  </div>\n')


def metric(n, label):
    return ('      <td style="width:25%; background-color:#ffffff; border:1px solid #e2e8f0; border-radius:10px; text-align:center; padding:14px 8px; vertical-align:middle;">'
            f'<span class="metric-value" style="display:block; font-size:30px; font-weight:700; color:#0f172a; line-height:1.1;">{n}</span>'
            f'<span style="display:block; font-size:11px; text-transform:uppercase; letter-spacing:0.04em; color:#64748b; margin-top:4px;">{label}</span></td>\n')


def long_date(d):
    return f"{d:%B} {d.day}, {d.year}"


def render(content):
    d = date.fromisoformat(content["date"]) if content.get("date") else date.today()
    secs = content["sections"]
    counts = {k: len((secs.get(k) or {}).get("items") or []) for k, _, _ in SECTIONS}
    sources = []
    for k, _, _ in SECTIONS:
        for it in (secs.get(k) or {}).get("items") or []:
            name = (it.get("source") or {}).get("name")
            if name and name not in sources:
                sources.append(name)
    if content.get("usgs", True) and "USGS Earthquake Feed" not in sources:
        sources.append("USGS Earthquake Feed")
    refreshed = content.get("refreshed_time", "6:30 AM")
    doc = (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f'<title>Global BCDR &amp; Ransomware Monitor — {long_date(d)}</title>\n</head>\n'
        '<body style="margin:0; background-color:#f1f5f9; color:#0f172a; font-family:-apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, Helvetica, Arial, sans-serif; font-size:15px; line-height:1.5;">\n'
        '<div style="background-color:#0f172a; color:#ffffff; padding:20px 24px; border-radius:0 0 10px 10px;">\n'
        '  <div style="max-width:860px; margin:0 auto; padding:0;">\n'
        '    <h1 style="margin:0 0 4px; font-size:20px; font-weight:700; color:#ffffff;"><span style="display:inline-block; width:10px; height:10px; border-radius:50%; background-color:#22c55e; margin-right:8px; vertical-align:middle;"></span>Global BCDR &amp; Ransomware Monitor</h1>\n'
        f'    <p style="margin:0; font-size:13px; color:#94a3b8;">Business Continuity &amp; Disaster Recovery daily brief · Last refreshed {long_date(d)} · {E(refreshed)}</p>\n'
        '  </div>\n</div>\n'
        '<div style="max-width:860px; margin:0 auto; padding:0 16px 32px;">\n\n'
        '  <table style="width:100%; border-collapse:separate; border-spacing:8px; margin:16px 0 8px;">\n    <tr>\n'
        + "".join(metric(counts[k], lab) for k, _, lab in SECTIONS)
        + '    </tr>\n  </table>\n\n'
        + "\n".join(section_html(k, h, secs.get(k) or {}) for k, h, _ in SECTIONS)
        + '\n  <div style="font-size:12px; color:#64748b; text-align:center; margin-top:20px; line-height:1.7;">\n'
        f'    Sources: {" · ".join(E(s) for s in sources)}<br>\n'
        '    Global BCDR &amp; Ransomware Monitor · Automated daily refresh · Not an official advisory — verify before acting.\n'
        '  </div>\n\n</div>\n</body>\n</html>\n'
    )
    return d, doc, counts


def text_body(d, content, counts):
    lines = [f"Global BCDR & Ransomware Monitor — {long_date(d)}",
             f"{counts['ransomware']} ransomware · {counts['outage']} cloud/outage · "
             f"{counts['cyber']} cyber · {counts['physical']} physical/natural", "", "Top items:"]
    for k, _, _ in SECTIONS:
        items = (content["sections"].get(k) or {}).get("items") or []
        if items:
            lines.append(f"- {items[0]['title']}")
    return "\n".join(lines[:8])


def cmd_render(args):
    content = json.loads(Path(args.content).read_text())
    d, doc, counts = render(content)
    styles = doc.count('style="')
    problems = []
    if "<style" in doc:
        problems.append("contains <style")
    if styles < 100:  # a normal 20-item edition renders ~140
        problems.append(f"only {styles} inline styles — sections look empty")
    if "var(--" in doc or "display:flex" in doc:
        problems.append("contains CSS vars or flexbox")
    out = Path(args.out) if args.out else HERE
    out.mkdir(parents=True, exist_ok=True)
    dated = out / f"bcdr-monitor-{d.isoformat()}.html"
    latest = out / "bcdr-monitor.html"
    dated.write_text(doc)
    latest.write_text(doc)
    if not args.out:  # keep each day's content for reference
        (HERE / "content").mkdir(exist_ok=True)
        shutil.copy2(args.content, HERE / "content" / f"content-{d.isoformat()}.json")
    print(json.dumps({
        "ok": not problems, "problems": problems, "files": [str(dated), str(latest)],
        "counts": counts, "inline_styles": styles, "bytes": len(doc),
        "subject": f"BCDR & Ransomware Monitor — {long_date(d)}",
        "text_body": text_body(d, content, counts),
    }, indent=1, ensure_ascii=False))
    return 0 if not problems else 1


def cmd_quakes(_):
    try:
        with urllib.request.urlopen(USGS, timeout=20) as r:
            feed = json.load(r)
    except Exception as e:  # network blocked -> caller falls back to WebFetch
        print(json.dumps({"error": f"{type(e).__name__}: {e}"}))
        return 1
    rows = []
    for f in feed.get("features", []):
        p = f["properties"]
        rows.append({
            "mag": p.get("mag"), "place": p.get("place"),
            "date": datetime.fromtimestamp(p["time"] / 1000, timezone.utc).strftime("%b %d"),
            "tsunami": bool(p.get("tsunami")), "alert": p.get("alert"), "url": p.get("url"),
            "tag": f"M {p.get('mag'):.1f}" if p.get("mag") is not None else None,
        })
    rows.sort(key=lambda x: -(x["mag"] or 0))
    print(json.dumps(rows[:5], indent=1))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("render")
    # Fixed default path keeps the command string identical every day, so a saved
    # Bash allow rule matches and the unattended run never waits on a prompt.
    r.add_argument("content", nargs="?", default=str(HERE / "content.json"))
    r.add_argument("--out", help="output directory (default: this folder)")
    sub.add_parser("quakes")
    args = ap.parse_args()
    sys.exit({"render": cmd_render, "quakes": cmd_quakes}[args.cmd](args))


if __name__ == "__main__":
    main()

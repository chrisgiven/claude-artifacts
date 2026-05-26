---
name: daily-comms-review
description: Daily morning review of email — surfaces action items and sends a digest to chris.given@gmail.com
---

You are running a daily communications review for Chris Given (chris.given@gmail.com), an IT Consultant specializing in Business Continuity and Disaster Recovery.

## Objective
Search Gmail for unread or important emails from the past 24 hours, synthesize key action items, and send Chris a concise morning digest email.

## Steps

1. **Search Gmail** for threads from the last 24 hours. Use queries like:
   - `is:unread newer_than:1d`
   - `is:important newer_than:1d`
   Retrieve up to 20 threads. For any thread that looks substantive, fetch the full thread content.

2. **Triage and summarize** what you find:
   - Action items requiring Chris's response or decision
   - Time-sensitive items (deadlines, meetings, approvals)
   - FYI items (no action needed)
   - Items that can be ignored/are low priority

3. **Draft and send a digest email** to chris.given@gmail.com with:
   - Subject: `Daily Comms Digest — [Today's Date]`
   - A clean, structured summary organized by priority (Action Required → Time-Sensitive → FYI)
   - For each item: sender, subject, one-line summary, and recommended action
   - Keep it scannable — Chris is busy and consulting-focused

4. If there are no emails of note, still send a short "All clear" email so Chris knows the task ran.

## Constraints
- Chris's role is IT Consultant / BC & DR specialist — flag anything related to client engagements, project deadlines, or enterprise IT
- Be concise. No fluff. Professional and analytical tone.
- Always send the digest email — do not skip this step even if the inbox is quiet
#!/usr/bin/env python3
"""Fetch a user's public contribution calendar (no token, no GraphQL) and
write data/contributions.json with raw days plus derived stats.

GitHub serves the same calendar fragment the profile page uses at
https://github.com/users/<username>/contributions as public HTML.
"""
import json
import os
import re
import sys
from datetime import date, datetime, timedelta, timezone

import requests
from bs4 import BeautifulSoup

USERNAME = os.environ.get("GH_USERNAME", "BhavneetBhoria29")
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "contributions.json")

URL = f"https://github.com/users/{USERNAME}/contributions"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (profile-art-bot)",
    "X-Requested-With": "XMLHttpRequest",
}


def _count_from_tooltip(text: str) -> int:
    if not text:
        return 0
    if text.lower().startswith("no contribution"):
        return 0
    m = re.match(r"\s*([\d,]+)", text)
    return int(m.group(1).replace(",", "")) if m else 0


def fetch_days():
    r = requests.get(URL, headers=HEADERS, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    # id -> contribution count, parsed from the <tool-tip> elements
    counts = {}
    for tip in soup.select("tool-tip"):
        key = tip.get("for")
        if key:
            counts[key] = _count_from_tooltip(tip.get_text(strip=True))

    days = []
    for cell in soup.select("td.ContributionCalendar-day"):
        d = cell.get("data-date")
        if not d:
            continue
        cid = cell.get("id", "")
        level = int(cell.get("data-level", "0") or 0)
        count = counts.get(cid, 0)
        days.append({"date": d, "count": count, "level": level})

    days.sort(key=lambda x: x["date"])
    return days


def compute_stats(days):
    total = sum(d["count"] for d in days)

    best = max(days, key=lambda x: x["count"], default={"date": None, "count": 0})

    # Longest streak = longest run of consecutive calendar days with count > 0.
    longest = cur = 0
    prev = None
    for d in days:
        dt = datetime.strptime(d["date"], "%Y-%m-%d").date()
        if d["count"] > 0:
            cur = cur + 1 if (prev and dt - prev == timedelta(days=1)) else 1
            longest = max(longest, cur)
        else:
            cur = 0
        prev = dt

    # Current streak = run of active days ending on the most recent dated day
    # (walk backwards, but allow "today has no commits yet").
    current = 0
    today = date.today()
    for d in reversed(days):
        dt = datetime.strptime(d["date"], "%Y-%m-%d").date()
        if dt > today:
            continue
        if d["count"] > 0:
            current += 1
        elif dt == today:
            continue  # today not done yet — don't break the streak
        else:
            break

    # Monthly totals for the info card / footer, keyed YYYY-MM.
    monthly = {}
    for d in days:
        monthly[d["date"][:7]] = monthly.get(d["date"][:7], 0) + d["count"]

    return {
        "total_last_year": total,
        "current_streak": current,
        "longest_streak": longest,
        "best_day": {"date": best["date"], "count": best["count"]},
        "monthly": monthly,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def main():
    days = fetch_days()
    if not days:
        print("No contribution cells found — did the page markup change?", file=sys.stderr)
        sys.exit(1)
    payload = {"username": USERNAME, "days": days, "stats": compute_stats(days)}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(payload, f, indent=2)
    s = payload["stats"]
    print(
        f"{USERNAME}: {len(days)} days, {s['total_last_year']} contributions, "
        f"current streak {s['current_streak']}, longest {s['longest_streak']}"
    )


if __name__ == "__main__":
    main()

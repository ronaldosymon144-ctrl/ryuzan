"""Ryuzan — structural window study.

Measures the interval between a scheduled Japanese information event and the
next opening of London and New York, with daylight saving resolved per event
date. This measures WHEN INSTITUTIONS PUBLISH relative to when the deepest
pools open. It is NOT a measure of information advantage: Singapore and Hong
Kong trade throughout these hours and machine-readable news moves in
milliseconds. See the Edge tab for the distinction.

Usage:  python3 window_study.py events.csv
"""
import csv, sys, datetime as dt
from zoneinfo import ZoneInfo

JST = ZoneInfo("Asia/Tokyo")
LDN = ZoneInfo("Europe/London")
NYC = ZoneInfo("America/New_York")

# Scheduled publication time by event class. These are institutional practice,
# not per-day observations. BOJ decisions are announced at the conclusion of
# the meeting, JST midday (variable ~11:30-12:30); 12:00 is used as the anchor.
def classify(name, typ):
    if typ == "jp":
        if name.startswith("BOJ"):   return ("BOJ policy decision", 12, 0)
        if "Takata" in name:         return ("BOJ board speech",   10, 30)
        return ("MOF official remarks", 9, 30)
    if typ == "joint" and "Rate checks" in name:
        return ("MOF rate check", 10, 0)
    return (None, None, None)          # excluded — see below

# EXCLUSIONS, and why:
#   iv     interventions   no scheduled time; they are the OUTCOME predicted,
#                          not an input to the prediction
#   mkt    market events   no scheduled publication
#   joint  bilateral       no fixed schedule (rate checks excepted)
#   us     US-origin       used as the control group, measured to the Tokyo open

def next_open(utc_moment, tz, hour=8):
    local = utc_moment.astimezone(tz)
    cand = local.replace(hour=hour, minute=0, second=0, microsecond=0)
    if cand <= local:
        cand = (cand + dt.timedelta(days=1)).replace(hour=hour, minute=0)
    return cand.astimezone(dt.timezone.utc)

def main(path):
    rows, control = [], []
    for e in csv.DictReader(open(path)):
        d = dt.date.fromisoformat(e["date"])
        if e["type"] == "us":
            h, m = (10, 0) if "Jackson" in e["name"] else (14, 0)
            u = dt.datetime(d.year, d.month, d.day, h, m, tzinfo=NYC).astimezone(dt.timezone.utc)
            control.append(((next_open(u, JST, 9) - u).total_seconds() / 3600, e["name"]))
            continue
        label, h, m = classify(e["name"], e["type"])
        if label is None:
            continue
        u = dt.datetime(d.year, d.month, d.day, h, m, tzinfo=JST).astimezone(dt.timezone.utc)
        rows.append({
            "date": e["date"], "class": label, "jst": f"{h:02d}:{m:02d}",
            "to_london_h": round((next_open(u, LDN) - u).total_seconds() / 3600, 2),
            "to_newyork_h": round((next_open(u, NYC) - u).total_seconds() / 3600, 2),
            "name": e["name"],
        })

    def med(v):
        v = sorted(v); n = len(v)
        return v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2

    print(f"{'DATE':<12}{'CLASS':<24}{'JST':<7}{'LONDON':>8}{'NEW YORK':>10}  EVENT")
    for r in rows:
        print(f"{r['date']:<12}{r['class']:<24}{r['jst']:<7}"
              f"{r['to_london_h']:>7.2f}h{r['to_newyork_h']:>9.2f}h  {r['name'][:34]}")

    for lab in sorted({r["class"] for r in rows}):
        sub = [r for r in rows if r["class"] == lab]
        print(f"\n{lab:<24} n={len(sub)}  London mean {sum(r['to_london_h'] for r in sub)/len(sub):5.2f}h"
              f"  NY mean {sum(r['to_newyork_h'] for r in sub)/len(sub):5.2f}h")

    print(f"\nALL JAPANESE EVENTS      n={len(rows)}"
          f"  London median {med([r['to_london_h'] for r in rows]):.2f}h"
          f"  NY median {med([r['to_newyork_h'] for r in rows]):.2f}h")
    print(f"CONTROL (US-origin)      n={len(control)}"
          f"  to Tokyo mean {sum(c for c, _ in control)/len(control):.2f}h")
    print("\nControl note: US events land while New York and London are both trading,"
          "\nso those hours are hours of an already-adjusted price. The clock gap is"
          "\nsimilar; the liquidity behind it is not.")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "events.csv")

"""Ryuzan — event-response backtest.

For each event, measures the percentage change in USD/JPY at +1, +4 and +12
weeks using the last observation on or before each horizon date.

WHAT THIS MEASURES: direction at a fixed horizon.
WHAT IT DOES NOT MEASURE: option profitability. A stronger yen four weeks later
can still leave an option losing money; the payoff depends on strike, entry
volatility, elapsed time, exit price and costs. Do not compare these hit rates
with the 24.3% option breakeven as though they were the same quantity.

Sample sizes are small. Six successes in ten observations gives an approximate
95% Wilson interval of 31%-83%, which does not establish that a subset is
meaningfully above even.

Usage:  python3 backtest.py fx_weekly.csv events.csv
"""
import csv, sys, math, datetime as dt
from collections import defaultdict

TYPE_NAMES = {"iv": "Intervention", "jp": "Japan policy", "us": "US policy",
              "joint": "Joint action", "mkt": "Market"}

def load_fx(path):
    return sorted((dt.date.fromisoformat(r["date"]), float(r["usd_jpy"]))
                  for r in csv.DictReader(open(path)))

def rate_at(fx, when):
    """Last observation on or before `when`. None if the series starts later."""
    best = None
    for d, v in fx:
        if d <= when:
            best = (d, v)
        else:
            break
    return best

def pct_after(fx, start, weeks):
    a = rate_at(fx, start)
    if not a:
        return None
    b = rate_at(fx, start + dt.timedelta(weeks=weeks))
    # No later observation exists -> incomplete follow-up, excluded (not zero).
    if not b or b[0] <= a[0]:
        return None
    return (b[1] - a[1]) / a[1] * 100

def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (100 * (c - h), 100 * (c + h))

def main(fx_path, ev_path):
    fx = load_fx(fx_path)
    print(f"Series: {len(fx)} observations, {fx[0][0]} to {fx[-1][0]}\n")

    by_type, incomplete = defaultdict(list), 0
    for e in csv.DictReader(open(ev_path)):
        d = dt.date.fromisoformat(e["date"])
        r = {w: pct_after(fx, d, w) for w in (1, 4, 12)}
        if r[4] is None:
            incomplete += 1          # excluded from +4wk statistics
        by_type[e["type"]].append(r)

    print(f"{'TYPE':<16}{'n':>4}{'avg +1wk':>11}{'avg +4wk':>11}"
          f"{'yen stronger @4wk':>20}{'95% interval':>18}")
    allr = []
    for t, rows in list(by_type.items()) + [("ALL", [r for v in by_type.values() for r in v])]:
        four = [r[4] for r in rows if r[4] is not None]
        one = [r[1] for r in rows if r[1] is not None]
        if not four:
            continue
        k = sum(1 for v in four if v < 0)          # negative = yen strengthened
        lo, hi = wilson(k, len(four))
        print(f"{TYPE_NAMES.get(t, t):<16}{len(four):>4}"
              f"{sum(one)/len(one):>10.2f}%{sum(four)/len(four):>10.2f}%"
              f"{f'{k} of {len(four)}':>20}{f'{lo:.0f}%-{hi:.0f}%':>18}")

    print(f"\nEvents excluded from +4wk statistics (incomplete follow-up): {incomplete}")
    print("Negative = yen strengthened, the direction the Ministry buys for.")
    print("\nCAUTION: related intervention dates within one policy campaign are not")
    print("independent observations. Group them into episodes before treating a")
    print("count as a hit rate.")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "fx_weekly.csv",
         sys.argv[2] if len(sys.argv) > 2 else "events.csv")

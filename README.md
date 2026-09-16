# Reproducibility pack

Every figure published in the desk is derived from these files. Standard library only — no network, no dependencies.

## Scripts

| Script | What it re-derives | Expected |
|---|---|---|
| `halo_verify.py` | All 54 figures on The Halo tab: breadth distribution, family aggregates, the yen path by family, the M09/M13 worked example, the credit test, and the intervention direction split. | `54 checks, 0 failures` |
| `backtest.py` | The 28-event measured backtest against 141 weeks of price. | −0.40% average, 13 of 28 |
| `window_study.py` | The lead-time study: eleven scheduled Japanese events against the London and New York opens. | 10.5h median to NY, 5.5h to London |

```bash
python3 halo_verify.py && python3 backtest.py && python3 window_study.py
```

## Tables

**Atlas** — the 45-event register and its market panel.

| File | Rows | Contents |
|---|---|---|
| `Events.csv` | 45 | The event register with breadth scores, evidence grades and the one-day cross-market panel |
| `Event_Windows.csv` | 1,482 | One row per event × series × window (1d / 5d / 20d), 14 public FRED series |
| `Interventions.csv` | 386 | Japan MOF daily intervention operations, April 1991 – June 2026, with direction |
| `Documented_Reactions.csv` | 7 | Source-documented mechanisms, kept separate from measured co-movements |
| `Entity_Watch.csv` | 16 | The observability map: institutions, companies and what each reveals |
| `Signal_Library.csv` | 6 | Candidate signatures with preconditions, confirmations and invalidations |
| `Sources.csv` | 46 | Annotated source register with URLs |

**Desk** — the original dataset behind The Tape.

| File | Rows | Contents |
|---|---|---|
| `fx_weekly.csv` | 141 | Weekly USD/JPY, ECB reference rates, 2 Jan 2024 – 7 Sep 2026 |
| `events.csv` | 28 | Dated and sourced policy events with type and weight |

## Conventions

- **FX sign.** Returns are oriented as the named currency versus USD. Positive JPY means yen appreciation.
- **Yields and spreads.** Changes in basis points. Positive yield means rates rose; positive OAS means credit widened.
- **Windows.** The baseline is the last observation before the event date. 1d is the first observation on or after it; 5d and 20d are the fifth and twentieth subsequent observations.
- **Missingness.** `NA` means the series did not cover the date, or the date was too imprecise for window arithmetic. **NA is never replaced by zero.**
- **Causality.** Event windows are descriptive co-movements. They do not establish that a yen event caused the observed move. Documented mechanisms live in their own table for exactly this reason.
- **Episodes.** 45 events span 26 independent episodes. Every published statistic is computed at episode level; counting events would give one week of August 2024 a fifth of the modern sample.

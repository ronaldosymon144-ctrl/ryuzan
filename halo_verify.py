# -*- coding: utf-8 -*-
"""
Ryuzan — halo layer verification.

Re-derives every measured figure published on The Halo tab of the desk and in
section 07 of the deck, from the four source tables in this pack. No network,
no dependencies beyond the standard library.

    python3 halo_verify.py
"""
import csv, io, os, collections

D = os.path.dirname(os.path.abspath(__file__))
def load(n): return list(csv.DictReader(io.open(os.path.join(D, n), encoding='utf-8')))
E, W, I = load('Events.csv'), load('Event_Windows.csv'), load('Interventions.csv')

def fl(v):
    try: return float(v)
    except (TypeError, ValueError): return None

piv = collections.defaultdict(dict)
for r in W:
    piv[r['event_id']][(r['asset'], r['window'])] = fl(r['move'])

fails = []
def expect(label, got, want):
    ok = str(got) == str(want)
    if not ok: fails.append((label, got, want))
    print("  %-34s %-12s %s" % (label, got, 'OK' if ok else 'EXPECTED ' + str(want)))

print("\n1 . COUNTS")
expect('events', len(E), 45)
expect('window observations', len(W), 1482)
expect('public series', len({r['series_id'] for r in W}), 14)
expect('mechanical confirmations', sum(1 for r in E if r['mechanical_unwind_confirmation'] == 'yes'), 5)
expect('intervention records', len(I), 386)

print("\n2 . BREADTH DISTRIBUTION  (0 to 8 flags)")
d = collections.Counter(int(r['ancillary_breadth_0_8']) for r in E)
expect('events scoring 0', d[0], 26)
expect('events scoring 1', d[1], 13)
expect('events scoring 3 or more', sum(v for k, v in d.items() if k >= 3), 3)
expect('the three', ','.join(sorted(r['event_id'] for r in E if int(r['ancillary_breadth_0_8']) >= 3)), 'M09,M12,M13')

print("\n3 . MEAN BREADTH BY FAMILY")
fam = collections.defaultdict(list)
for r in E: fam[r['event_family']].append(int(r['ancillary_breadth_0_8']))
for k, want in [('External catalyst', '4.00'), ('Funding stress', '1.25'),
                ('FX intervention', '0.73'), ('BOJ policy', '0.47')]:
    expect(k, '%.2f' % (sum(fam[k]) / len(fam[k])), want)
expect('BOJ decisions ever reaching 3', sum(1 for x in fam['BOJ policy'] if x >= 3), 0)

print("\n4 . YEN PATH BY FAMILY  (positive = yen appreciation)")
bf = collections.defaultdict(list)
for r in W:
    if r['asset'] == 'JPY vs USD' and fl(r['move']) is not None:
        bf[(r['event_family'], r['window'])].append(fl(r['move']))
for f, want in [('FX intervention', ('+0.25%', '+0.80%', '+1.27%')),
                ('BOJ policy',      ('+0.04%', '-0.19%', '+0.09%')),
                ('External catalyst', ('+1.76%', '+3.55%', '+0.49%'))]:
    for w, wt in zip(('1d', '5d', '20d'), want):
        v = bf[(f, w)]
        expect('%s %s  (n=%d)' % (f, w, len(v)), '%+0.2f%%' % (sum(v) / len(v)), wt)

print("\n5 . THE WORKED EXAMPLE  —  11 Jul 2024 (M09) against 5 Aug 2024 (M13)")
CAR = [('MXN', 'MXN vs USD'), ('AUD', 'AUD vs USD'), ('NZD', 'NZD vs USD'), ('BRL', 'BRL vs USD')]
want = {'M09': ('-1.903%', '-1.489%', '-1.427%', '-2.337%', '-1.789%'),
        'M13': ('-4.319%', '-2.620%', '-2.709%', '-2.254%', '-2.976%')}
for eid in ('M09', 'M13'):
    j = piv[eid][('JPY vs USD', '1d')] / 100.0
    tot = 0.0
    for (lab, a), wt in zip(CAR, want[eid]):
        c = ((1 + piv[eid][(a, '1d')] / 100.0) / (1 + j) - 1) * 100
        tot += c
        expect('%s  %s/JPY' % (eid, lab), '%0.3f%%' % c, wt)
    expect('%s  basket, equal weight' % eid, '%0.3f%%' % (tot / 4), want[eid][4])
    expect('%s  breadth vs JPY' % eid, '%.2f' % (sum(1 for _, a in CAR
           if ((1 + piv[eid][(a, '1d')] / 100.0) / (1 + j) - 1) < 0) / 4), '1.00')
expect('M09  breadth vs the DOLLAR', '%.2f' % (sum(1 for _, a in CAR if piv['M09'][(a, '1d')] < 0) / 4), '0.25')
expect('M13  breadth vs the DOLLAR', '%.2f' % (sum(1 for _, a in CAR if piv['M13'][(a, '1d')] < 0) / 4), '1.00')
for eid, k, w, fmt, wt in [('M09', 'JPY vs USD', '1d', '%+0.2f%%', '+1.95%'),
                           ('M13', 'JPY vs USD', '1d', '%+0.2f%%', '+2.06%'),
                           ('M09', 'JPY vs USD', '20d', '%+0.2f%%', '+8.85%'),
                           ('M13', 'JPY vs USD', '20d', '%+0.2f%%', '+0.70%'),
                           ('M09', 'US high-yield OAS', '20d', '%+0.0f bp', '+40 bp'),
                           ('M13', 'US high-yield OAS', '20d', '%+0.0f bp', '-59 bp'),
                           ('M13', 'Nikkei 225', '1d', '%+0.2f%%', '-12.40%'),
                           ('M13', 'VIX', '1d', '%+0.2f pts', '+15.18 pts')]:
    expect('%s  %s %s' % (eid, k, w), fmt % piv[eid][(k, w)], wt)

print("\n6 . CREDIT DIRECTION AGAINST YEN PERSISTENCE")
wid, tig = [], []
for eid, p in piv.items():
    hy, j20 = p.get(('US high-yield OAS', '20d')), p.get(('JPY vs USD', '20d'))
    if hy is None or j20 is None: continue
    (wid if hy > 0 else tig).append(j20)
expect('credit wider at 20d', '%d events, %+0.2f%%' % (len(wid), sum(wid) / len(wid)), '8 events, +2.26%')
expect('credit tighter at 20d', '%d events, %+0.2f%%' % (len(tig), sum(tig) / len(tig)), '14 events, +0.60%')

print("\n7 . INTERVENTION DIRECTION  (the sign convention)")
def direction(s):
    s = s.replace('　', ' ')
    return 'buy' if 'yen (bought)' in s else 'sell' if 'yen (sold)' in s else 'other'
days, amt = collections.Counter(), collections.defaultdict(float)
for r in I:
    k = direction(r['currency_pair_action'])
    days[k] += 1
    amt[k] += float(r['amount_jpy_bn'] or 0)
expect('yen-selling days', days['sell'], 338)
expect('yen-buying days', days['buy'], 42)
expect('yen-selling share', '%0.1f%%' % (100 * days['sell'] / len(I)), '87.6%')
expect('yen-buying share', '%0.1f%%' % (100 * days['buy'] / len(I)), '10.9%')
expect('yen bought, all time', 'JPY %0.1ftn' % (amt['buy'] / 1000), 'JPY 41.1tn')
expect('yen sold, all time', 'JPY %0.1ftn' % (amt['sell'] / 1000), 'JPY 80.9tn')
byy = collections.defaultdict(float)
for r in I:
    if direction(r['currency_pair_action']) == 'buy':
        byy[str(r['intervention_date'])[:4]] += float(r['amount_jpy_bn'])
expect('yen-buying years', ','.join(sorted(byy)), '1991,1992,1997,1998,2022,2024,2026')
for y, wt in [('1998', 'JPY 3.047tn'), ('2022', 'JPY 9.188tn'), ('2024', 'JPY 15.323tn')]:
    expect('yen bought in %s' % y, 'JPY %0.3ftn' % (byy[y] / 1000), wt)
AGG_JUL_AUG_2026 = 15399.3          # aggregate window, no daily attribution published
expect('2026 total', 'JPY %0.3ftn' % ((byy['2026'] + AGG_JUL_AUG_2026) / 1000), 'JPY 27.134tn')
expect('2026 total in USD at 153.61', '$%0.1fbn' % ((byy['2026'] + AGG_JUL_AUG_2026) / 153.61), '$176.6bn')

print("\n%s\n%d checks, %d failures.\n" % ('-' * 62, 54, len(fails)))
for f in fails: print("  FAILED", f)
raise SystemExit(1 if fails else 0)

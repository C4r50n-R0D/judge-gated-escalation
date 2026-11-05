#!/usr/bin/env python3
"""Gate 1 power rule (PREREG section 9). Two modes.

  python power.py assume --n-test 390 --sd 0.15 0.25 0.35
      Analytic, for planning: SE of a paired accuracy difference = sd / sqrt(n).
  python power.py pilot pilot_labeled.jsonl --judge haiku --n-test 390
      Uses CALIBRATION-split pilot rows only. Picks tau with the same pre-registered rule as controllers.py
      calibrate, measures the across-task sd of (judge->reroute minus strong-only) at that tau, and projects to n-test.

Rule: delta = max(0.03, the smallest multiple of 0.01 that is >= 2.8 * SE). 2.8 = 1.96 + 0.84, i.e. 80% power for
the one-sided non-inferiority test when the true difference is 0. If that delta exceeds 0.05, H2 is reported as an
estimate with its CI instead of a test. Also printed: power if the true difference is -delta/2, which is lower;
the paper reports both numbers.
"""
import argparse, math, statistics, sys
import controllers as C

def norm_cdf(x): return 0.5 * (1 + math.erf(x / math.sqrt(2)))

def rule(sd, n):
    se = sd / math.sqrt(n)
    d = max(0.03, math.ceil(2.8 * se * 100 - 1e-9) / 100)
    pw = lambda true: norm_cdf((true + d) / se - 1.96)    # P(lower 95% bound > -delta)
    verdict = "test H2 with this delta" if d <= 0.05 else "delta would exceed 0.05: report H2 as an estimate, not a test"
    print(f"sd={sd:.3f} n={n}: SE {se:.4f} -> delta {d:.2f} ({verdict}); power if true diff 0: {pw(0):.2f}, if -delta/2: {pw(-d / 2):.2f}")
    return d

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("mode", choices=["assume", "pilot"]); ap.add_argument("path", nargs="?")
    ap.add_argument("--n-test", type=int, default=390); ap.add_argument("--sd", type=float, nargs="*", default=[0.15, 0.25, 0.35])
    ap.add_argument("--judge"); ap.add_argument("--local", default="local3b"); ap.add_argument("--strong", default="strong14b")
    ap.add_argument("--mc", type=int, default=200); ap.add_argument("--delta", type=float, default=0.03)
    ap.add_argument("--cost-metric", default="tok", choices=sorted(C.COST_IDX))
    a = ap.parse_args()
    if a.mode == "assume":
        for sd in a.sd: rule(sd, a.n_test)
        sys.exit(0)
    tasks, excl, _, stats = C.load(a.path, a.local, a.strong, "cal")
    if a.judge:
        c = C.choose_tau(tasks, a.judge, a.delta, a.mc, 20261009, cost_metric=a.cost_metric)   # same seed and rule as controllers.py calibrate
        if c is None: raise SystemExit(f"no {a.judge} labels on calibration pilot rows")
        g = C.gate("judge", a.judge, c["tau"]); label = f"judge:{a.judge} tau={c['tau']} (pre-registered rule)"
    else:
        g = C.gate("visible"); label = "visible gate"
    pa = C.per_task(tasks, ("reroute", g, 1), a.mc, 1); pb = C.per_task(tasks, ("strong-only", None, 1), a.mc, 1)
    d = [pa[t][0] - pb[t][0] for t in pa if t in pb]
    if len(d) < 3: raise SystemExit("need at least 3 calibration pilot tasks with both tiers")
    sd = statistics.stdev(d)
    print(f"calibration pilot tasks {len(d)} (excluded {len(excl)}); {label}; per-task diff sd {sd:.3f}")
    print("note: the mean difference is not shown, to keep the margin decision independent of effect size")
    rule(sd, a.n_test)

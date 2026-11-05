#!/usr/bin/env python3
"""E14a (exploratory): calibration and drift of the frozen judge taus, from stored labels. No model calls.
  nice python3 ext/E14/e14.py runs/confirmatory.labeled.jsonl ext/E14/out [--pilot]
--pilot: 20 tasks per split, 200 bootstrap resamples, 50 monitor streams (timing and plumbing check only).

For each judge (tev, llama, selfconf) and each condition (the drafts the frozen tau is applied to):
  reference   calibration split, 3B drafts (where the taus were set)
  split       test split, 3B drafts
  generator   test split, 1.5B / 7B / 14B drafts (same tasks as test 3B: paired)
  suite       test split, 3B drafts, MBPP+ and HumanEval+ separately
  time        test split, 3B drafts, quintiles of generation time (each quintile is also a different set of tasks)
the outcomes at the frozen thresholds.json tau (accept decision from controllers.gate, unchanged):
  acceptance rate, accepted-set accuracy (hidden pass rate among accepted drafts), false-accept rate (share of wrong
  drafts accepted), false-reject rate (share of correct drafts rejected); and AUROC, ECE and Brier of the raw score and
  of Platt and isotonic recalibrations fitted on the reference condition only (judgestats fits, unchanged).
CIs: task-cluster bootstrap. Differences against test 3B are paired over tasks for the generator conditions; other
differences use independent bootstraps of the two conditions.

Drift monitor (label-free: uses only the judge's accept decisions and the visible tests, both available at deployment):
two-sided Bernoulli CUSUM, allowance k = 0.05, on (A) the accept indicator and (B) the indicator "accepted and fails
the visible tests". Reference rate and alarm threshold h come from the reference condition only: h is the smallest
grid value with at most 5% false alarms over 1,000 drafts drawn from the reference pool. Evaluated on streams of
1,000 drafts: 3B test drafts throughout (false alarms), and 300 3B test drafts followed by 700 drafts of another
generator (detection rate and delay)."""
import json, math, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import controllers as C, judgestats as S
from jsonl import read_jsonl

inp, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True); PILOT = "--pilot" in sys.argv
TH = json.load(open("thresholds.json")); SEED = TH["seed"]; B = 200 if PILOT else 2000; NSTREAM = 50 if PILOT else 400
JUDGES = ("tev", "llama", "selfconf"); BINS = 10
rows = [r for r in read_jsonl(inp) if "_meta" not in r and not r.get("error") and r.get("hidden_passed") is not None]
if PILOT:
    keep = {s: set(sorted({r["task"] for r in rows if r["split"] == s})[:20]) for s in ("cal", "test")}
    rows = [r for r in rows if r["task"] in keep[r["split"]]]
gates = {j: C.gate("judge", j, TH["taus"][j]) for j in JUDGES}
acc = lambda d, j: bool(gates[j](d)[0])
P = lambda d, j: d["judges"][j]["p"]

t3 = sorted((r for r in rows if r["split"] == "test" and r["tier"] == "local3b"), key=lambda r: r["ts"])
cut = [t3[min(len(t3) - 1, len(t3) * q // 5)]["ts"] for q in range(1, 5)]
quint = lambda r: sum(r["ts"] >= c for c in cut) + 1
COND = {"ref: cal 3B": lambda r: r["split"] == "cal" and r["tier"] == "local3b",
        "test 3B": lambda r: r["split"] == "test" and r["tier"] == "local3b",
        "test 1.5B": lambda r: r["split"] == "test" and r["tier"] == "local1p5b",
        "test 7B": lambda r: r["split"] == "test" and r["tier"] == "local7b",
        "test 14B": lambda r: r["split"] == "test" and r["tier"] == "strong14b",
        "test 3B MBPP+": lambda r: r["split"] == "test" and r["tier"] == "local3b" and r["suite"].lower().startswith("mbpp"),
        "test 3B HumanEval+": lambda r: r["split"] == "test" and r["tier"] == "local3b" and r["suite"].lower().startswith("humaneval")}
for q in range(1, 6): COND[f"test 3B time Q{q}"] = (lambda q: lambda r: r["split"] == "test" and r["tier"] == "local3b" and quint(r) == q)(q)
draws = {c: [r for r in rows if f(r) and all((r.get("judges") or {}).get(j) for j in JUDGES)] for c, f in COND.items()}
draws = {c: ds for c, ds in draws.items() if ds}   # a condition can be empty in the pilot subset

ref = draws["ref: cal 3B"]; ys_ref = [int(r["hidden_passed"]) for r in ref]
FIT = {j: {"platt": S.fit_platt([P(r, j) for r in ref], ys_ref), "iso": S.fit_isotonic([P(r, j) for r in ref], ys_ref)} for j in JUDGES}
VER = {"raw": lambda j, p: p, "platt": lambda j, p: S.apply_platt(FIT[j]["platt"], p), "iso": lambda j, p: S.apply_isotonic(FIT[j]["iso"], p)}

KL = ["n", "y", "acc", "acc_y", "wrong", "wrong_acc", "right_rej"] + [f"{k}_{s}{b}" for k in VER for s in ("n", "p", "y") for b in range(BINS)] + [f"{k}_sq" for k in VER]
KI = {k: i for i, k in enumerate(KL)}

def task_stats(ds, j):
    """Per-task sufficient statistics (vectors in KL order), so bootstrap resamples are weighted sums of task vectors."""
    by = {}
    for d in ds:
        y, a = int(d["hidden_passed"]), int(acc(d, j)); v = by.setdefault(d["task"], [0.0] * len(KL))
        for k, x in (("n", 1), ("y", y), ("acc", a), ("acc_y", a * y), ("wrong", 1 - y), ("wrong_acc", a * (1 - y)), ("right_rej", y * (1 - a))):
            v[KI[k]] += x
        for k, f in VER.items():
            p = f(j, P(d, j)); b = min(BINS - 1, int(p * BINS))
            v[KI[f"{k}_n{b}"]] += 1; v[KI[f"{k}_p{b}"]] += p; v[KI[f"{k}_y{b}"]] += y; v[KI[f"{k}_sq"]] += (p - y) ** 2
    return by

def metrics(tot):
    m = lambda a, b: tot[a] / tot[b] if tot[b] else None
    out = {"pass_rate": m("y", "n"), "accept_rate": m("acc", "n"), "accepted_acc": m("acc_y", "acc"),
           "false_accept": m("wrong_acc", "wrong"), "false_reject": m("right_rej", "y")}
    for k in VER:
        if not tot["n"]: out[f"ece_{k}"] = out[f"brier_{k}"] = None; continue
        out[f"ece_{k}"] = sum(abs(tot[f"{k}_p{b}"] - tot[f"{k}_y{b}"]) for b in range(BINS)) / tot["n"]
        out[f"brier_{k}"] = tot[f"{k}_sq"] / tot["n"]
    return out

def summed(by, names):
    """Sum of task vectors over a list of task names (repeats allowed), returned as a dict keyed by KL."""
    cnt = {}
    for t in names: cnt[t] = cnt.get(t, 0) + 1
    tot = [0.0] * len(KL)
    for t, c in cnt.items():
        v = by[t]
        for i in range(len(KL)): tot[i] += c * v[i]
    return dict(zip(KL, tot))

def boot(by, B, seed):
    names = sorted(by); rnd = random.Random(seed)
    return [metrics(summed(by, [names[rnd.randrange(len(names))] for _ in names])) for _ in range(B)]

def ci(vals):
    vals = sorted(v for v in vals if v is not None)
    return [C.pct(vals, .025), C.pct(vals, .975)] if vals else [None, None]

res = {"settings": {"B": B, "seed": SEED, "taus": {j: TH["taus"][j] for j in JUDGES}, "bins": BINS,
                    "time_cuts": cut, "fits_on": "ref: cal 3B", "n_ref": len(ref)}, "conditions": {}, "diffs": {}, "monitor": {}}
BY = {(c, j): task_stats(ds, j) for c, ds in draws.items() for j in JUDGES}
BS = {}
for c, ds in draws.items():
    res["conditions"][c] = {"n_drafts": len(ds), "n_tasks": len({d["task"] for d in ds}), "judges": {}}
    for j in JUDGES:
        by = BY[(c, j)]; point = metrics(summed(by, sorted(by))); BS[(c, j)] = bs = boot(by, B, SEED + 7)
        point.update({f"{k}_ci": ci([b[k] for b in bs]) for k in list(point)})
        pos = [VER["raw"](j, P(d, j)) for d in ds if d["hidden_passed"]]; neg = [P(d, j) for d in ds if not d["hidden_passed"]]
        point["auroc"] = C.auroc(pos, neg) if pos and neg else None
        res["conditions"][c]["judges"][j] = point
    print(f"{c}: {len(ds)} drafts", flush=True)

KEYS = ("accept_rate", "accepted_acc", "false_accept", "false_reject", "ece_raw", "ece_platt", "ece_iso")
def diff(a, b, j, paired):
    if a not in draws or b not in draws: return None
    if paired:   # same tasks: resample task names once, sum both conditions over them
        ba, bb = BY[(a, j)], BY[(b, j)]; names = sorted(set(ba) & set(bb)); rnd = random.Random(SEED + 11); ds = []
        for _ in range(B):
            s = [names[rnd.randrange(len(names))] for _ in names]
            ma, mb = metrics(summed(ba, s)), metrics(summed(bb, s))
            ds.append({k: None if ma[k] is None or mb[k] is None else ma[k] - mb[k] for k in KEYS})
    else:
        ds = [{k: None if x[k] is None or y[k] is None else x[k] - y[k] for k in KEYS} for x, y in zip(BS[(a, j)], BS[(b, j)])]
    pa, pb = res["conditions"][a]["judges"][j], res["conditions"][b]["judges"][j]
    return {k: {"diff": None if pa[k] is None or pb[k] is None else pa[k] - pb[k], "ci": ci([d[k] for d in ds])} for k in KEYS}

for j in JUDGES:
    D = res["diffs"][j] = {}
    D["test 3B minus ref"] = diff("test 3B", "ref: cal 3B", j, False)
    for g in ("test 1.5B", "test 7B", "test 14B"): D[f"{g} minus test 3B"] = diff(g, "test 3B", j, True)
    D["HumanEval+ minus MBPP+ (test 3B)"] = diff("test 3B HumanEval+", "test 3B MBPP+", j, False)
    D["time Q5 minus Q1 (test 3B)"] = diff("test 3B time Q5", "test 3B time Q1", j, False)

# drift monitor
def cusum(xs, p0, h, k=0.05):
    sp = sm = 0.0
    for i, x in enumerate(xs):
        sp = max(0.0, sp + x - (p0 + k)); sm = max(0.0, sm + (p0 - k) - x)
        if sp > h or sm > h: return i
    return None
SIG = {"A_accept": lambda d, j: float(acc(d, j)), "B_accepted_visible_fail": lambda d, j: float(acc(d, j) and not d.get("visible_passed"))}
rnd = random.Random(SEED + 23); L = 1000
stream = lambda pool, n: [pool[rnd.randrange(len(pool))] for _ in range(n)]
for j in JUDGES:
    for sname, sig in SIG.items():
        p0 = sum(sig(d, j) for d in ref) / len(ref)
        refs = [[sig(d, j) for d in stream(ref, L)] for _ in range(NSTREAM)]
        h = next(h for h in [x / 2 for x in range(1, 201)] if sum(cusum(s, p0, h) is not None for s in refs) <= 0.05 * NSTREAM)
        R = {"p0": p0, "h": h}
        fa = [cusum([sig(d, j) for d in stream(draws["test 3B"], L)], p0, h) for _ in range(NSTREAM)]
        R["test 3B only: false-alarm rate"] = sum(x is not None for x in fa) / NSTREAM
        for g in ("test 1.5B", "test 7B", "test 14B"):
            det = []
            for _ in range(NSTREAM):
                i = cusum([sig(d, j) for d in stream(draws["test 3B"], 300) + stream(draws[g], L - 300)], p0, h)
                det.append(None if i is None else i - 300)
            hits = sorted(x for x in det if x is not None and x >= 0)
            R[f"switch to {g[5:]}"] = {"early alarm (before switch)": sum(x is not None and x < 0 for x in det) / NSTREAM,
                                      "detected within 700": len(hits) / NSTREAM,
                                      "median delay": C.pct(hits, .5) if hits else None}
        res["monitor"][f"{j} {sname}"] = R
    print(f"monitor {j} done", flush=True)

json.dump(res, open(os.path.join(out, "results.json"), "w"), indent=1, default=str)
f3 = lambda x: "n/a" if x is None else f"{x:.3f}"
cis = lambda v, k: f"{f3(v[k])} [{f3(v[k + '_ci'][0])}, {f3(v[k + '_ci'][1])}]"
with open(os.path.join(out, "summary.md"), "w") as f:
    f.write(f"Frozen taus: " + ", ".join(f"{j} {TH['taus'][j]:.3f}" for j in JUDGES) + f". Recalibration fitted on ref ({len(ref)} drafts).\n\n")
    for j in JUDGES:
        f.write(f"## {j}: frozen-tau behaviour by condition\n\n| condition | drafts | pass rate | AUROC | accept rate | accepted-set acc | false-accept | false-reject | ECE raw | ECE platt | ECE iso |\n|---|---|---|---|---|---|---|---|---|---|---|\n")
        for c, v in res["conditions"].items():
            m = v["judges"][j]
            f.write(f"| {c} | {v['n_drafts']} | {f3(m['pass_rate'])} | {f3(m['auroc'])} | {cis(m, 'accept_rate')} | {cis(m, 'accepted_acc')} | "
                    f"{cis(m, 'false_accept')} | {cis(m, 'false_reject')} | {f3(m['ece_raw'])} | {f3(m['ece_platt'])} | {f3(m['ece_iso'])} |\n")
        f.write(f"\n### {j}: differences [95% CI]\n\n| comparison | " + " | ".join(KEYS) + " |\n|---|" + "---|" * len(KEYS) + "\n")
        for n, d in res["diffs"][j].items():
            if d is None: continue
            f.write(f"| {n} | " + " | ".join("n/a" if d[k]["diff"] is None else f"{d[k]['diff']:+.3f} [{d[k]['ci'][0]:+.3f}, {d[k]['ci'][1]:+.3f}]" for k in KEYS) + " |\n")
        f.write("\n")
    f.write("## Drift monitor (CUSUM, k 0.05, h set for 5% false alarms over 1,000 reference drafts)\n\n")
    for n, R in res["monitor"].items():
        f.write(f"- **{n}**: p0 {R['p0']:.3f}, h {R['h']}; test 3B false-alarm rate {R['test 3B only: false-alarm rate']:.2f}; " +
                "; ".join(f"{g}: detected {v['detected within 700']:.2f}, median delay {f3(v['median delay'])}, early {v['early alarm (before switch)']:.2f}"
                          for g, v in R.items() if g.startswith("switch")) + "\n")
print("wrote", out)

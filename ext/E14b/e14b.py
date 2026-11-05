#!/usr/bin/env python3
"""E14b: frozen-tau behaviour, recalibration and the drift monitor under the E3 to E6 shifts. No model calls; imports
controllers.py and judgestats.py unchanged.
  python3 ext/E14b/e14b.py OUTDIR [--pilot]
Inputs (stored labels): runs/confirmatory.labeled.jsonl (reference: calibration 3B drafts, where Platt and isotonic
maps are fitted, as in E14a), runs/E3.j18.jsonl (prompt variants), runs/E4.j02.jsonl (surface rewrites),
runs/E5.j02.jsonl (mutants), runs/E6.j06.jsonl (injections and defenses). Every condition is gated with the BASE
judge's frozen tau (a deployed system would not know its prompt or input had shifted). Paired differences are against
"subset clean": the same E3-subset local3b drafts, base judge, no shift."""
import json, math, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import controllers as C, judgestats as S
from jsonl import read_jsonl

out = sys.argv[1]; os.makedirs(out, exist_ok=True); PILOT = "--pilot" in sys.argv
TH = json.load(open("thresholds.json")); SEED = TH["seed"]; B = 200 if PILOT else 1000; NSTREAM = 50 if PILOT else 400
JUDGES = ("tev", "llama"); BINS = 10; TAU = {j: TH["taus"][j] for j in JUDGES}
ok = lambda r: "_meta" not in r and not r.get("error") and r.get("hidden_passed") is not None
lab = lambda r, k: ((r.get("judges") or {}).get(k) or {}).get("p")

ref = [r for r in read_jsonl("runs/confirmatory.labeled.jsonl") if ok(r) and r["split"] == "cal" and r["tier"] == "local3b"
       and all(lab(r, j) is not None for j in JUDGES)]
FIT = {j: {"platt": S.fit_platt([lab(r, j) for r in ref], [int(r["hidden_passed"]) for r in ref]),
           "iso": S.fit_isotonic([lab(r, j) for r in ref], [int(r["hidden_passed"]) for r in ref])} for j in JUDGES}
VER = {"raw": lambda j, p: p, "platt": lambda j, p: S.apply_platt(FIT[j]["platt"], p), "iso": lambda j, p: S.apply_isotonic(FIT[j]["iso"], p)}

# conditions: name -> function(judge) -> list of (row, p) on the E3 subset
src = {}
def load(path):
    if path not in src: src[path] = [r for r in read_jsonl(path) if ok(r)] if os.path.exists(path) else []
    return src[path]
def cond(path, tier, key=lambda j: j):
    return lambda j: [(r, lab(r, key(j))) for r in load(path) if r["tier"] == tier and lab(r, key(j)) is not None]
COND = {"subset clean": cond("runs/E3.j18.jsonl", "local3b")}
for v in ("p1", "p2", "p3", "p4", "p5", "p6", "codeonly", "codefirst"):
    COND[f"E3 prompt {v}"] = cond("runs/E3.j18.jsonl", "local3b", (lambda v: lambda j: f"{j}_{v}")(v))
COND["E3 prompt nocrit/crit"] = cond("runs/E3.j18.jsonl", "local3b", lambda j: {"tev": "tev_nocrit", "llama": "llama_crit"}[j])
for t in ("strip_comments", "reformat", "rename_locals", "verbose_comments"):
    COND[f"E4 {t}"] = cond("runs/E4.j02.jsonl", f"local3b+{t}")
MUT = ("off_by_one", "flip_comparison", "swap_args", "wrong_init", "drop_guard", "early_exit")
COND["E5 mutants (all wrong)"] = lambda j: [x for m in MUT for x in cond("runs/E5.j02.jsonl", f"local3b+{m}")(j)]
INJ = ("direct", "authority", "fake_json", "role_tags", "multilingual", "hidden_chars", "homoglyph", "padding", "string", "identifier")
COND["E6 injected, no defense (pooled)"] = lambda j: [x for i in INJ for x in cond("runs/E6.j06.jsonl", f"local3b+inject_{i}")(j)]
for i in INJ: COND[f"E6 inject {i}"] = cond("runs/E6.j06.jsonl", f"local3b+inject_{i}")
for d in ("strip", "san"):
    COND[f"E6 defense {d} (clean + injected)"] = (lambda d: lambda j: [x for t in ("local3b",) + tuple(f"local3b+inject_{i}" for i in INJ)
                                                                       for x in cond("runs/E6.j06.jsonl", f"{t}@{d}")(j)])(d)
for d in ("delim", "hier"):
    COND[f"E6 defense {d} (clean + injected)"] = (lambda d: lambda j: [x for t in ("local3b",) + tuple(f"local3b+inject_{i}" for i in INJ)
                                                                       for x in cond("runs/E6.j06.jsonl", t, lambda j: f"{j}_{d}")(j)])(d)

KL = ["n", "y", "acc", "acc_y", "wrong", "wrong_acc", "right_rej"] + [f"{k}_{s}{b}" for k in VER for s in ("n", "p", "y") for b in range(BINS)]
KI = {k: i for i, k in enumerate(KL)}
def task_stats(ds, j):
    by = {}
    for r, p in ds:
        y, a = int(r["hidden_passed"]), int(p >= TAU[j]); v = by.setdefault(r["task"], [0.0] * len(KL))
        for k, x in (("n", 1), ("y", y), ("acc", a), ("acc_y", a * y), ("wrong", 1 - y), ("wrong_acc", a * (1 - y)), ("right_rej", y * (1 - a))): v[KI[k]] += x
        for k, f in VER.items():
            q = f(j, p); b = min(BINS - 1, int(q * BINS)); v[KI[f"{k}_n{b}"]] += 1; v[KI[f"{k}_p{b}"]] += q; v[KI[f"{k}_y{b}"]] += y
    return by
def metrics(t):
    m = lambda a, b: t[a] / t[b] if t[b] else None
    o = {"pass_rate": m("y", "n"), "accept_rate": m("acc", "n"), "accepted_acc": m("acc_y", "acc"), "false_accept": m("wrong_acc", "wrong"),
         "false_reject": m("right_rej", "y")}
    for k in VER: o[f"ece_{k}"] = sum(abs(t[f"{k}_p{b}"] - t[f"{k}_y{b}"]) for b in range(BINS)) / t["n"] if t["n"] else None
    return o
def summed(by, names):
    tot = [0.0] * len(KL)
    for t in names:
        if t in by:
            for i, x in enumerate(by[t]): tot[i] += x
    return dict(zip(KL, tot))
def ci(vals):
    vals = sorted(v for v in vals if v is not None); return [C.pct(vals, .025), C.pct(vals, .975)] if vals else [None, None]
KEYS = ("accept_rate", "accepted_acc", "false_accept", "false_reject", "ece_raw", "ece_platt", "ece_iso")

res = {"taus": TAU, "n_ref": len(ref), "conditions": {}, "diffs": {}, "monitor": {}}
for split in ("test", "cal"):
    base = {j: task_stats([x for x in COND["subset clean"](j) if x[0]["split"] == split], j) for j in JUDGES}
    for name, f in COND.items():
        for j in JUDGES:
            ds = [x for x in f(j) if x[0]["split"] == split]
            if not ds: continue
            by = task_stats(ds, j); names = sorted(by); rnd = random.Random(SEED + 31)
            idx = [[names[rnd.randrange(len(names))] for _ in names] for _ in range(B)]
            m = metrics(summed(by, names)); bs = [metrics(summed(by, ix)) for ix in idx]
            for k in KEYS: m[k + "_ci"] = ci([b[k] for b in bs])
            res["conditions"][f"{split}|{name}|{j}"] = dict(n=len(ds), n_tasks=len(names), **m)
            if name != "subset clean":
                common = sorted(set(names) & set(base[j]))
                if common:
                    pt = {k: (lambda a, b: None if a is None or b is None else a - b)(metrics(summed(by, common))[k], metrics(summed(base[j], common))[k]) for k in KEYS}
                    bd = []
                    for _ in range(B):
                        ix = [common[rnd.randrange(len(common))] for _ in common]
                        a, b = metrics(summed(by, ix)), metrics(summed(base[j], ix))
                        bd.append({k: None if a[k] is None or b[k] is None else a[k] - b[k] for k in KEYS})
                    res["diffs"][f"{split}|{name}|{j}"] = {k: dict(diff=pt[k], ci=ci([x[k] for x in bd])) for k in KEYS}
    print("conditions done", split, flush=True)

def cusum(xs, p0, h, k=0.05):
    sp = sm = 0.0
    for i, x in enumerate(xs):
        sp = max(0.0, sp + x - (p0 + k)); sm = max(0.0, sm + (p0 - k) - x)
        if sp > h or sm > h: return i
    return None
rnd = random.Random(SEED + 23); L = 1000
stream = lambda pool, n: [pool[rnd.randrange(len(pool))] for _ in range(n)]
for j in JUDGES:
    p0 = sum(lab(r, j) >= TAU[j] for r in ref) / len(ref)
    refs = [[float(p >= TAU[j]) for p in stream([lab(r, j) for r in ref], L)] for _ in range(NSTREAM)]
    h = next(h for h in [x / 2 for x in range(1, 201)] if sum(cusum(s, p0, h) is not None for s in refs) <= 0.05 * NSTREAM)
    clean = [float(p >= TAU[j]) for r, p in COND["subset clean"](j) if r["split"] == "test"]
    R = {"p0": p0, "h": h, "subset clean only: false-alarm rate": sum(cusum(stream(clean, L), p0, h) is not None for _ in range(NSTREAM)) / NSTREAM}
    for name, f in COND.items():
        if name == "subset clean": continue
        sh = [float(p >= TAU[j]) for r, p in f(j) if r["split"] == "test"]
        if len(sh) < 50: continue
        det = []
        for _ in range(NSTREAM):
            i = cusum(stream(clean, 300) + stream(sh, L - 300), p0, h); det.append(None if i is None else i - 300)
        hits = sorted(x for x in det if x is not None and x >= 0)
        R[name] = {"early": sum(x is not None and x < 0 for x in det) / NSTREAM, "detected": len(hits) / NSTREAM,
                   "median_delay": C.pct(hits, .5) if hits else None}
    res["monitor"][j] = R
    print("monitor done", j, flush=True)

json.dump(res, open(os.path.join(out, "results.json"), "w"), indent=1, default=str)
f3 = lambda x: "n/a" if x is None else f"{x:.3f}"
cis = lambda m, k: f"{f3(m[k])} [{f3(m[k + '_ci'][0])}, {f3(m[k + '_ci'][1])}]"
dd = lambda d: "n/a" if d is None or d["diff"] is None else f"{d['diff']:+.3f} [{d['ci'][0]:+.3f}, {d['ci'][1]:+.3f}]"
with open(os.path.join(out, "summary.md"), "w") as fo:
    fo.write(f"Base-judge frozen taus: tev {TAU['tev']:.3f}, llama {TAU['llama']:.3f}. Recalibration fitted on {len(ref)} calibration 3B drafts. "
             f"Differences are condition minus subset clean, paired by task.\n")
    for split in ("test", "cal"):
        for j in JUDGES:
            fo.write(f"\n## {split}, {j}\n\n| condition | drafts | pass rate | accept rate | accepted-set acc | false-accept | false-reject | ECE raw | ECE platt | ECE iso | "
                     "d accept | d accepted acc | d false-accept | d ECE iso |\n|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n")
            for name in COND:
                m = res["conditions"].get(f"{split}|{name}|{j}")
                if not m: continue
                d = res["diffs"].get(f"{split}|{name}|{j}", {})
                fo.write(f"| {name} | {m['n']} | {f3(m['pass_rate'])} | {cis(m, 'accept_rate')} | {cis(m, 'accepted_acc')} | {cis(m, 'false_accept')} | "
                         f"{cis(m, 'false_reject')} | {f3(m['ece_raw'])} | {f3(m['ece_platt'])} | {f3(m['ece_iso'])} | {dd(d.get('accept_rate'))} | "
                         f"{dd(d.get('accepted_acc'))} | {dd(d.get('false_accept'))} | {dd(d.get('ece_iso'))} |\n")
    fo.write("\n## Drift monitor (accept-rate CUSUM, k 0.05, h for 5% false alarms over 1,000 reference drafts; 300 clean then 700 shifted, test)\n\n")
    for j, R in res["monitor"].items():
        fo.write(f"- **{j}**: p0 {R['p0']:.3f}, h {R['h']}, false alarms on clean subset {R['subset clean only: false-alarm rate']:.2f}\n")
        for n, v in R.items():
            if isinstance(v, dict): fo.write(f"  - {n}: detected {v['detected']:.2f}, median delay {f3(v['median_delay'])}, early {v['early']:.2f}\n")
print("wrote", out)

#!/usr/bin/env python3
"""E5 analysis: judge detection of synthetic bugs (T18 mutants of hidden-correct local3b drafts) vs natural wrong drafts.
Imports controllers.py unchanged.  python3 ext/E5/analyze.py LABELED.jsonl OUTDIR [--boots 1000]
Per bug class (and pooled), judge and split, at the frozen tau:
  detection = share of mutants rejected (p < tau); natural = share of natural hidden-failing local3b drafts rejected,
  on the same split; their difference on the same task-cluster resamples (unpaired drafts, shared tasks resampled);
  parent acceptance and 'caught' (parent accepted and mutant rejected) over mutant-parent pairs; pairwise
  discrimination P(p_parent > p_mutant) + ties/2; mean dp (mutant minus parent); AUROC of all hidden-correct local3b
  drafts vs the mutants (vs the natural wrong drafts, for reference); and the visible tests' catch rate.
Writes OUTDIR/e5.json and OUTDIR/e5.md."""
import argparse, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import controllers as C

MUTATORS = ("off_by_one", "flip_comparison", "swap_args", "wrong_init", "drop_guard", "early_exit")
JUDGES = ("tev", "llama")
ap = argparse.ArgumentParser(); ap.add_argument("inp"); ap.add_argument("out"); ap.add_argument("--boots", type=int, default=1000); a = ap.parse_args()
os.makedirs(a.out, exist_ok=True)
TH = json.load(open("thresholds.json")); SEED = TH["seed"]; TAU = {j: TH["taus"][j] for j in JUDGES}
rows = [r for r in map(json.loads, open(a.inp)) if "_meta" not in r]
lab = lambda r, j: (r.get("judges") or {}).get(j)
P = lambda r, j: r["judges"][j]["p"]
base = {(r["task"], r["rep"]): r for r in rows if r.get("tier") == "local3b"}
mut = [r for r in rows if r.get("codemod") in MUTATORS]

def ratio(per_task, idx):
    """per_task: list of (num, den); point and percentile CI of sum(num)/sum(den) over task resamples."""
    den = sum(d for _, d in per_task); pt = sum(n for n, _ in per_task) / den if den else None
    bs = []
    for ix in idx:
        d = sum(per_task[i][1] for i in ix)
        if d: bs.append(sum(per_task[i][0] for i in ix) / d)
    return dict(v=pt, lo=C.pct(bs, 0.025) if bs else None, hi=C.pct(bs, 0.975) if bs else None), bs

def diff(pa, pb, idx):
    """difference of two ratios over the same task resamples."""
    out = []
    for ix in idx:
        da = sum(pa[i][1] for i in ix); db = sum(pb[i][1] for i in ix)
        if da and db: out.append(sum(pa[i][0] for i in ix) / da - sum(pb[i][0] for i in ix) / db)
    da = sum(d for _, d in pa); db = sum(d for _, d in pb)
    v = (sum(n for n, _ in pa) / da - sum(n for n, _ in pb) / db) if da and db else None
    return dict(v=v, lo=C.pct(out, 0.025) if out else None, hi=C.pct(out, 0.975) if out else None)

res = {"taus": TAU, "boots": a.boots, "cells": {}}
for split in ("test", "cal"):
    for j in JUDGES:
        tau = TAU[j]
        correct = [r for r in base.values() if r["split"] == split and r["hidden_passed"] and lab(r, j)]
        natural = [r for r in base.values() if r["split"] == split and not r["hidden_passed"] and lab(r, j)]
        for cls in MUTATORS + ("pooled",):
            M = [r for r in mut if r["split"] == split and (cls == "pooled" or r["codemod"] == cls) and lab(r, j)
                 and lab(base.get((r["task"], r["rep"]), {}), j)]
            if not M: continue
            names = sorted({r["task"] for r in M + natural + correct}); pos = {n: i for i, n in enumerate(names)}
            idx = C.boot_idx(len(names), a.boots, SEED + 1)
            def per(rs, f):
                v = [[0, 0] for _ in names]
                for r in rs:
                    x = f(r)
                    if x is not None: v[pos[r["task"]]][0] += x; v[pos[r["task"]]][1] += 1
                return v
            par = lambda r: base[(r["task"], r["rep"])]
            det_m = per(M, lambda r: P(r, j) < tau); det_n = per(natural, lambda r: P(r, j) < tau)
            disc = per(M, lambda r: 1.0 if P(par(r), j) > P(r, j) else 0.5 if P(par(r), j) == P(r, j) else 0.0)
            tasks_m = {n: {"L": []} for n in names}; tasks_n = {n: {"L": []} for n in names}
            for r in correct: tasks_m[r["task"]]["L"].append(r); tasks_n[r["task"]]["L"].append(r)
            for r in M: tasks_m[r["task"]]["L"].append(r)
            for r in natural: tasks_n[r["task"]]["L"].append(r)
            res["cells"][f"{cls}|{split}|{j}"] = dict(
                n_mutants=len(M), n_natural=len(natural), n_tasks_mut=len({r["task"] for r in M}),
                detection=ratio(det_m, idx)[0], natural_detection=ratio(det_n, idx)[0], detection_minus_natural=diff(det_m, det_n, idx),
                parent_accept=ratio(per(M, lambda r: P(par(r), j) >= tau), idx)[0],
                caught=ratio(per(M, lambda r: P(par(r), j) >= tau and P(r, j) < tau), idx)[0],
                pairwise=ratio(disc, idx)[0], mean_dp=ratio(per(M, lambda r: P(r, j) - P(par(r), j)), idx)[0],
                auroc_mut=C.judge_auroc(tasks_m, j, idx, a.boots, SEED + 2), auroc_nat=C.judge_auroc(tasks_n, j, idx, 0, SEED + 2)["auroc"],
                visible_catch=ratio(per(M, lambda r: not r["visible_passed"]), idx)[0],
                natural_visible_catch=ratio(per(natural, lambda r: not r.get("visible_passed")), idx)[0],
                unparseable=sum(1 for r in M if r["judges"][j].get("unparseable_votes")) / len(M))

json.dump(res, open(os.path.join(a.out, "e5.json"), "w"), indent=1, default=str)
f3 = lambda x: "n/a" if x is None else f"{x:.3f}"
ci = lambda d: f"{f3(d['v'])} [{f3(d['lo'])}, {f3(d['hi'])}]"
sd = lambda d: "n/a" if d["v"] is None else f"{d['v']:+.3f} [{d['lo']:+.3f}, {d['hi']:+.3f}]"
with open(os.path.join(a.out, "e5.md"), "w") as f:
    f.write(f"Frozen taus: tev {TAU['tev']:.3f}, llama {TAU['llama']:.3f}. Bootstrap {a.boots} task-cluster resamples. "
            "Detection = rejected at the frozen tau. dp = mutant minus parent.\n")
    for split in ("test", "cal"):
        f.write(f"\n## {split} split\n\n| bug class | judge | mutants | detection | natural wrong detection | minus natural | parent accepted | caught | "
                "P(parent > mutant) | mean dp | AUROC correct vs mutants | AUROC vs natural | visible tests catch | unparseable |\n"
                "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n")
        for cls in MUTATORS + ("pooled",):
            for j in JUDGES:
                c = res["cells"].get(f"{cls}|{split}|{j}")
                if c is None: continue
                am = c["auroc_mut"]
                f.write(f"| {cls} | {j} | {c['n_mutants']} | {ci(c['detection'])} | {f3(c['natural_detection']['v'])} | {sd(c['detection_minus_natural'])} | "
                        f"{f3(c['parent_accept']['v'])} | {ci(c['caught'])} | {ci(c['pairwise'])} | {f3(c['mean_dp']['v'])} | "
                        f"{f3(am['auroc'])} [{f3(am['lo'])}, {f3(am['hi'])}] | {f3(c['auroc_nat'])} | {f3(c['visible_catch']['v'])} | {c['unparseable']:.3f} |\n")
print("wrote", a.out)

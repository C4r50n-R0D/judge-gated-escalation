#!/usr/bin/env python3
"""E4 analysis: judge surface invariance under the T18 semantics-preserving rewrites. Imports controllers.py unchanged.
  python3 ext/E4/analyze.py LABELED.jsonl OUTDIR [--boots 1000]
Pairs each rewritten local3b draft with its original (same task and rep) and, per transform, judge and split, over the
pairs both labels exist for: mean dp (rewritten minus original), mean |dp|, share with |dp| >= 0.1, decision flips at
the frozen tau, acceptance and false-accept rates before and after, and AUROC on the rewritten code minus AUROC on the
original code of the same drafts (task-cluster bootstrap, same resamples). Writes OUTDIR/e4.json and OUTDIR/e4.md."""
import argparse, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import controllers as C

TRANSFORMS = ("strip_comments", "reformat", "rename_locals", "verbose_comments", "reorder_helpers")
JUDGES = ("tev", "llama")
ap = argparse.ArgumentParser(); ap.add_argument("inp"); ap.add_argument("out"); ap.add_argument("--boots", type=int, default=1000); a = ap.parse_args()
os.makedirs(a.out, exist_ok=True)
TH = json.load(open("thresholds.json")); SEED = TH["seed"]; TAU = {j: TH["taus"][j] for j in JUDGES}
rows = [json.loads(l) for l in open(a.inp)]
orig = {(r["task"], r["rep"]): r for r in rows if "_meta" not in r and r.get("tier") == "local3b"}
lab = lambda r, j: (r.get("judges") or {}).get(j)

def boot_ratio(per_task, idx):
    """per_task: list of (numerator, denominator) per task; returns point, lo, hi of sum(num)/sum(den)."""
    den = sum(d for _, d in per_task)
    pt = sum(n for n, _ in per_task) / den if den else None
    bs = []
    for ix in idx:
        n = sum(per_task[i][0] for i in ix); d = sum(per_task[i][1] for i in ix)
        if d: bs.append(n / d)
    return dict(v=pt, lo=C.pct(bs, 0.025) if bs else None, hi=C.pct(bs, 0.975) if bs else None)

res = {"taus": TAU, "boots": a.boots, "cells": {}}
for T in TRANSFORMS:
    for split in ("test", "cal"):
        for j in JUDGES:
            pairs = [(orig[(r["task"], r["rep"])], r) for r in rows if r.get("codemod") == T and r.get("split") == split
                     and (r["task"], r["rep"]) in orig]
            pairs = [(o, t) for o, t in pairs if lab(o, j) and lab(t, j)]
            if not pairs: continue
            names = sorted({o["task"] for o, _ in pairs}); pos = {n: i for i, n in enumerate(names)}
            by = [[] for _ in names]
            for o, t in pairs: by[pos[o["task"]]].append((o, t))
            idx = C.boot_idx(len(names), a.boots, SEED + 1); tau = TAU[j]
            P = lambda r: r["judges"][j]["p"]
            def stat(f, cond=lambda o, t: True):
                return boot_ratio([(sum(f(o, t) for o, t in b if cond(o, t)), sum(1 for o, t in b if cond(o, t))) for b in by], idx)
            wrong = lambda o, t: not o["hidden_passed"]
            tasks = {n: {"L": [dict(hidden_passed=o["hidden_passed"], judges={"orig": o["judges"][j], "rew": t["judges"][j]}) for o, t in by[pos[n]]]}
                     for n in names}
            res["cells"][f"{T}|{split}|{j}"] = dict(
                n_pairs=len(pairs), n_tasks=len(names), code_unchanged=sum(t.get("code_unchanged", False) for _, t in pairs) / len(pairs),
                mean_dp=stat(lambda o, t: P(t) - P(o)), mean_abs_dp=stat(lambda o, t: abs(P(t) - P(o))),
                big_dp=stat(lambda o, t: abs(P(t) - P(o)) >= 0.1), flips=stat(lambda o, t: (P(t) >= tau) != (P(o) >= tau)),
                accept_orig=stat(lambda o, t: P(o) >= tau), accept_rew=stat(lambda o, t: P(t) >= tau),
                accept_diff=stat(lambda o, t: (P(t) >= tau) - (P(o) >= tau)),
                fa_orig=stat(lambda o, t: P(o) >= tau, wrong), fa_rew=stat(lambda o, t: P(t) >= tau, wrong),
                fa_diff=stat(lambda o, t: (P(t) >= tau) - (P(o) >= tau), wrong),
                auroc_orig=C.judge_auroc(tasks, "orig", idx, 0, SEED)["auroc"], auroc_rew=C.judge_auroc(tasks, "rew", idx, 0, SEED)["auroc"],
                auroc_diff=C.paired_auroc_diff(tasks, "rew", "orig", idx),
                unparseable=sum(1 for _, t in pairs if t["judges"][j].get("unparseable_votes")) / len(pairs))

json.dump(res, open(os.path.join(a.out, "e4.json"), "w"), indent=1, default=str)
f3 = lambda x: "n/a" if x is None else f"{x:+.3f}"
ci = lambda d: f"{f3(d['v'])} [{f3(d['lo'])}, {f3(d['hi'])}]"
v = lambda x: "n/a" if x is None else f"{x:.3f}"
au = lambda d: "n/a" if d.get("diff") is None else f"{d['diff']:+.3f} [{d['lo']:+.3f}, {d['hi']:+.3f}]"
with open(os.path.join(a.out, "e4.md"), "w") as f:
    f.write(f"Frozen taus: tev {TAU['tev']:.3f}, llama {TAU['llama']:.3f}. Bootstrap {a.boots} task-cluster resamples. dp = rewritten minus original.\n")
    for split in ("test", "cal"):
        f.write(f"\n## {split} split\n\n| transform | judge | pairs | code unchanged | mean dp | mean abs dp | abs dp >= 0.1 | flips | accept rate orig -> rew | accept diff | false-accept orig -> rew | false-accept diff | AUROC orig -> rew | AUROC diff | unparseable |\n"
                "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n")
        for T in TRANSFORMS:
            for j in JUDGES:
                c = res["cells"].get(f"{T}|{split}|{j}")
                if c is None: continue
                f.write(f"| {T} | {j} | {c['n_pairs']} | {c['code_unchanged']:.2f} | {ci(c['mean_dp'])} | {ci(c['mean_abs_dp'])} | {ci(c['big_dp'])} | {ci(c['flips'])} | "
                        f"{v(c['accept_orig']['v'])} -> {v(c['accept_rew']['v'])} | {ci(c['accept_diff'])} | "
                        f"{v(c['fa_orig']['v'])} -> {v(c['fa_rew']['v'])} | {ci(c['fa_diff'])} | "
                        f"{v(c['auroc_orig'])} -> {v(c['auroc_rew'])} | {au(c['auroc_diff'])} | {c['unparseable']:.3f} |\n")
print("wrote", a.out)

#!/usr/bin/env python3
"""Judge metrics for exploratory experiments (E2 to E6, E14). Imports controllers.py and judgestats.py unchanged.
  python3 tools/judge_eval.py LABELED.jsonl OUTDIR --judges tev,llama,gemma [--tier local3b] [--ref tev] [--boots 2000]

For each judge, on each split, over the chosen tier's drafts: AUROC and within-task AUROC (task-cluster bootstrap
CIs), the paired AUROC difference against --ref, Brier, ECE, unparseable-label rate, seconds and token-compute per
label. Gate behavior on the test split, two modes: transfer (the frozen thresholds.json tau, for judges that have
one) and recal (tau refit on the calibration split with controllers.choose_tau, the pre-registered rule), each as
judge->reroute accuracy and token-compute, paired against strong-only and against visible->reroute.
Writes OUTDIR/judges.json and OUTDIR/judges.md."""
import argparse, json, math, os, statistics as st, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import controllers as C, judgestats as S

ap = argparse.ArgumentParser(); ap.add_argument("inp"); ap.add_argument("out"); ap.add_argument("--judges", required=True)
ap.add_argument("--tier", default="local3b"); ap.add_argument("--strong", default="strong14b"); ap.add_argument("--ref", default="tev")
ap.add_argument("--boots", type=int, default=2000); ap.add_argument("--no-gate", action="store_true"); a = ap.parse_args()
os.makedirs(a.out, exist_ok=True)
TH = json.load(open("thresholds.json")); MC, SEED = TH["mc"], TH["seed"]
judges = a.judges.split(",")
res = {"tier": a.tier, "ref": a.ref, "boots": a.boots, "splits": {}}

def label_stats(tasks, j):
    ls = [d["judges"][j] for t in tasks for d in tasks[t]["L"] if (d.get("judges") or {}).get(j)]
    ps = [d["judges"][j]["p"] for t in tasks for d in tasks[t]["L"] if (d.get("judges") or {}).get(j)]
    ys = [int(bool(d["hidden_passed"])) for t in tasks for d in tasks[t]["L"] if (d.get("judges") or {}).get(j)]
    n_all = sum(len(tasks[t]["L"]) for t in tasks)
    return {"n_labels": len(ls), "unjudged": n_all - len(ls), "brier": S.brier(ps, ys), "ece": S.ece(ps, ys),
            "unparseable_rate": (sum(1 for l in ls if l.get("unparseable_votes")) / len(ls)) if ls else None,
            "sec_per_label": st.mean(l.get("wall") or 0.0 for l in ls) if ls else None,
            "tok_per_label": st.mean((l.get("params_b") or 0.0) * (l.get("tokens") or 0) for l in ls) if ls else None}

for split in ("cal", "test"):
    tasks, excl, _, stats = C.load(a.inp, a.tier, a.strong, split)
    names = sorted(tasks); idx = C.boot_idx(len(names), a.boots, SEED + 1)
    R = {"n_tasks": len(tasks), "excluded": len(excl), "judges": {}}
    for j in judges:
        R["judges"][j] = dict(auroc=C.judge_auroc(tasks, j, idx, a.boots, SEED + 2), within=C.within_task_auroc(tasks, j, idx, SEED),
                              vs_ref=None if j == a.ref else C.paired_auroc_diff(tasks, j, a.ref, idx), **label_stats(tasks, j))
        print(f"{split} {j}: AUROC {C.fmt(R['judges'][j]['auroc']['auroc'])}", flush=True)
    res["splits"][split] = R

if not a.no_gate:
    cal, _, _, _ = C.load(a.inp, a.tier, a.strong, "cal"); test, _, _, _ = C.load(a.inp, a.tier, a.strong, "test")
    names = sorted(test); idx = C.boot_idx(len(names), a.boots, SEED + 1)
    specs = {"strong-only": ("strong-only", None, 1), "visible->reroute": ("reroute", C.gate("visible"), 1)}
    taus = {}
    for j in judges:
        c = C.choose_tau(cal, j, TH["delta"], MC, SEED, cost_metric=TH["cost_metric"])
        if c is None: continue
        taus[f"recal:{j}"] = c["tau"]; specs[f"[recal] {j}->reroute"] = ("reroute", C.gate("judge", j, c["tau"]), 1)
        if j in TH["taus"] and a.tier == TH["local"]:
            t = TH["taus"][j]; t = math.inf if t == "always-reroute" else t
            taus[f"transfer:{j}"] = t; specs[f"[transfer] {j}->reroute"] = ("reroute", C.gate("judge", j, t), 1)
        print(f"gate {j}: recal tau {c['tau']}", flush=True)
    pt = {n: C.per_task(test, s, MC, SEED) for n, s in specs.items()}
    G = {}
    for n in specs:
        sel = [t for t in names if t in pt[n]]; pos = {t: i for i, t in enumerate(sel)}
        sub = [[pos[names[i]] for i in ix if names[i] in pos] for ix in idx]
        G[n] = {m: C.mean_ci([pt[n][t][i] for t in sel], [s for s in sub if s]) for i, m in enumerate(C.METRICS)}
        for base in ("strong-only", "visible->reroute"):
            if n != base: G[n][f"minus {base}"] = C.compare(pt, n, base, idx, names)
    res["gate_test"] = {"taus": {k: (None if v == math.inf else v) for k, v in taus.items()}, "controllers": G}

json.dump(res, open(os.path.join(a.out, "judges.json"), "w"), indent=1, default=str)
f3 = lambda x: "n/a" if x is None else f"{x:.3f}"
ci = lambda d, k="auroc": f"{f3(d.get(k))} [{f3(d.get('lo'))}, {f3(d.get('hi'))}]"
with open(os.path.join(a.out, "judges.md"), "w") as f:
    for split in ("test", "cal"):
        R = res["splits"][split]
        f.write(f"## {split} split: {a.tier} drafts, {R['n_tasks']} tasks\n\n")
        f.write(f"| judge | AUROC | within-task AUROC | AUROC minus {a.ref} | Brier | ECE | unparseable | s/label | token-compute/label | unjudged |\n|---|---|---|---|---|---|---|---|---|---|\n")
        for j, v in R["judges"].items():
            d = v["vs_ref"]; dd = "" if d is None else f"{d['diff']:+.3f} [{d['lo']:+.3f}, {d['hi']:+.3f}]" if d.get("diff") is not None else "n/a"
            sec = "n/a" if v["sec_per_label"] is None else f"{v['sec_per_label']:.2f}"
            tok = "n/a" if v["tok_per_label"] is None else f"{v['tok_per_label']:.0f}"
            f.write(f"| {j} | {ci(v['auroc'])} | {ci(v['within'])} | {dd} | {f3(v['brier'])} | {f3(v['ece'])} | "
                    f"{f3(v['unparseable_rate'])} | {sec} | {tok} | {v['unjudged']} |\n")
        f.write("\n")
    if "gate_test" in res:
        f.write("## Gates on the test split (judge->reroute)\n\n| controller | accuracy | token-compute | s/task | acc minus strong-only | tok minus strong-only | acc minus visible->reroute | tok minus visible->reroute |\n|---|---|---|---|---|---|---|---|\n")
        for n, v in res["gate_test"]["controllers"].items():
            cells = [f"{v['acc'][0]:.3f} [{v['acc'][1]:.3f}, {v['acc'][2]:.3f}]", f"{v['tok'][0]:.0f}", f"{v['sec'][0]:.1f}"]
            for base in ("strong-only", "visible->reroute"):
                c = v.get(f"minus {base}")
                cells += ["", ""] if c is None else [f"{c['acc']['diff']:+.3f} [{c['acc']['lo']:+.3f}, {c['acc']['hi']:+.3f}]",
                                                     f"{c['tok']['diff']:+.0f} [{c['tok']['lo']:+.0f}, {c['tok']['hi']:+.0f}]"]
            f.write(f"| {n} | " + " | ".join(cells) + " |\n")
        f.write("\nTaus: " + ", ".join(f"{k} {C.fmt(v)}" for k, v in res["gate_test"]["taus"].items()) + "\n")
print("wrote", a.out)

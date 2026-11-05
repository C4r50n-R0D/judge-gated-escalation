#!/usr/bin/env python3
"""E3 (exploratory): judge prompt sensitivity. Reads the labeled subset; imports controllers.py and judgestats.py unchanged.
  nice python3 ext/E3/analyze.py runs/E3.labeled.jsonl ext/E3/out [--boots 1000]
On the test tasks of the subset (3B drafts):
- per prompt variant: AUROC, paired AUROC difference vs its base judge (tev or llama), ECE, mean |p - p_base| on the same
  drafts, and the share of drafts whose accept decision at the frozen base tau flips;
- transfer gate at the base judge's frozen tau: acceptance rate, accepted-set accuracy, false-accept rate, and
  judge->reroute accuracy and token-compute vs visible->reroute (recal-mode gates come from tools/judge_eval.py);
- spread: SD and range of AUROC across the base prompt plus its six paraphrases, for tev and for llama, against the SD
  and range across six judge models (tev, llama, selfconf, gemma, qwen35, qwen25i) on the same drafts, with task-cluster
  bootstrap CIs and the paired difference (prompt SD minus model SD)."""
import json, math, os, statistics as st, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import controllers as C, judgestats as S
inp, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True)
B = int(sys.argv[sys.argv.index("--boots") + 1]) if "--boots" in sys.argv else 1000
TH = json.load(open("thresholds.json")); MC, SEED = TH["mc"], TH["seed"]
PARA = {b: [b] + [f"{b}_p{i}" for i in range(1, 7)] for b in ("tev", "llama")}
OTHER = {"tev": ["tev_nocrit", "tev_codeonly", "tev_codefirst"], "llama": ["llama_crit", "llama_codeonly", "llama_codefirst"]}
MODELS = ["tev", "llama", "selfconf", "gemma", "qwen35", "qwen25i"]
test, _, _, _ = C.load(inp, "local3b", "strong14b", "test")
J = lambda d, j: (d.get("judges") or {}).get(j)
# only drafts labeled by every judge and variant (all of them in the full run; the pilot labels 2 draws per task)
ALL = MODELS + PARA["tev"][1:] + PARA["llama"][1:] + OTHER["tev"] + OTHER["llama"]
for t in list(test):
    test[t]["L"] = [d for d in test[t]["L"] if all(J(d, j) for j in ALL)]
    if not test[t]["L"]: del test[t]
names = sorted(test); idx = C.boot_idx(len(names), B, SEED + 1)
have = lambda j: all(J(d, j) for t in names for d in test[t]["L"])
def auroc_on(tl, j):
    ds = [d for t in tl for d in test[t]["L"] if J(d, j)]
    pos = [J(d, j)["p"] for d in ds if d["hidden_passed"]]; neg = [J(d, j)["p"] for d in ds if not d["hidden_passed"]]
    return C.auroc(pos, neg) if pos and neg else None
res = {"n_test_tasks": len(names), "boots": B, "variants": {}, "spread": {}}
boot_tasks = [[names[i] for i in ix] for ix in idx]
for b in ("tev", "llama"):
    tau = TH["taus"][b]; g0 = C.gate("judge", b, tau)
    for v in PARA[b] + OTHER[b]:
        if not have(v): res["variants"][v] = {"missing": True}; continue
        ds = [d for t in names for d in test[t]["L"]]; g = C.gate("judge", v, tau)
        ps, ys = [J(d, v)["p"] for d in ds], [int(d["hidden_passed"]) for d in ds]
        acc = [bool(g(d)[0]) for d in ds]; acc0 = [bool(g0(d)[0]) for d in ds]
        R = {"auroc": C.judge_auroc(test, v, idx, B, SEED + 2), "ece": S.ece(ps, ys), "brier": S.brier(ps, ys),
             "mean_abs_dp": st.mean(abs(J(d, v)["p"] - J(d, b)["p"]) for d in ds),
             "decision_flip_rate": sum(a != a0 for a, a0 in zip(acc, acc0)) / len(ds),
             "accept_rate": sum(acc) / len(ds), "accepted_acc": (sum(a and y for a, y in zip(acc, ys)) / sum(acc)) if sum(acc) else None,
             "false_accept": sum(a and not y for a, y in zip(acc, ys)) / max(1, ys.count(0)),
             "unparseable_rate": st.mean((J(d, v).get("unparseable_votes") or 0) for d in ds),
             "sec_per_label": st.mean(J(d, v).get("wall") or 0 for d in ds)}
        if v != b: R["minus_base"] = C.paired_auroc_diff(test, v, b, idx)
        res["variants"][v] = R; print(f"{v}: AUROC {C.fmt(R['auroc']['auroc'])}", flush=True)
    # transfer gates: every variant at the base judge's frozen tau
specs = {"strong-only": ("strong-only", None, 1), "visible->reroute": ("reroute", C.gate("visible"), 1)}
for b in ("tev", "llama"):
    for v in PARA[b] + OTHER[b]:
        if not res["variants"][v].get("missing"): specs[f"[transfer] {v}->reroute"] = ("reroute", C.gate("judge", v, TH["taus"][b]), 1)
pt = {n: C.per_task(test, s, MC, SEED) for n, s in specs.items()}
res["gates_transfer"] = {n: {"acc": C.mean_ci([pt[n][t][0] for t in names], idx), "tok": C.mean_ci([pt[n][t][3] for t in names], idx),
                             **({} if n == "visible->reroute" else {"minus visible->reroute": C.compare(pt, n, "visible->reroute", idx, names)})}
                         for n in specs}
# spread of AUROC: prompts vs models
fam = {"tev prompts": [v for v in PARA["tev"] if have(v)], "llama prompts": [v for v in PARA["llama"] if have(v)],
       "models": [m for m in MODELS if have(m)]}
sd = lambda xs: st.pstdev(xs) if len(xs) > 1 else None
def qci(xs):
    xs = sorted(x for x in xs if x is not None)
    return [C.pct(xs, .025), C.pct(xs, .975)] if xs else [None, None]
point = {f: [x for x in (auroc_on(names, j) for j in js) if x is not None] for f, js in fam.items()}
boots = {f: [] for f in fam}
for tl in boot_tasks:
    for f, js in fam.items():
        a = [x for x in (auroc_on(tl, j) for j in js) if x is not None]
        boots[f].append((sd(a), max(a) - min(a)) if len(a) > 1 else (None, None))
for f in fam:
    res["spread"][f] = {"judges": fam[f], "aurocs": point[f], "sd": sd(point[f]), "range": max(point[f]) - min(point[f]),
                        "sd_ci": qci([x[0] for x in boots[f]]), "range_ci": qci([x[1] for x in boots[f]])}
for f in fam:
    if f != "models":
        dd = [x[0] - y[0] for x, y in zip(boots[f], boots["models"]) if x[0] is not None and y[0] is not None]
        res["spread"][f]["sd_minus_models_sd"] = {"diff": res["spread"][f]["sd"] - res["spread"]["models"]["sd"], "ci": qci(dd)}
json.dump(res, open(os.path.join(out, "e3.json"), "w"), indent=1, default=str)
f3 = lambda x: "n/a" if x is None else f"{x:.3f}"
with open(os.path.join(out, "e3.md"), "w") as f:
    f.write(f"Test tasks: {len(names)} (3B drafts). Bootstrap {B}. Frozen taus: tev {TH['taus']['tev']:.3f}, llama {TH['taus']['llama']:.3f}.\n\n")
    f.write("| variant | AUROC | minus base | ECE | mean abs dp | decision flips | accept rate | accepted acc | false-accept | unparseable | s/label |\n|---|---|---|---|---|---|---|---|---|---|---|\n")
    for v, R in res["variants"].items():
        if R.get("missing"): f.write(f"| {v} | missing labels | | | | | | | | | |\n"); continue
        a = R["auroc"]; m = R.get("minus_base")
        mb = "" if m is None else f"{m['diff']:+.3f} [{m['lo']:+.3f}, {m['hi']:+.3f}]"
        f.write(f"| {v} | {f3(a['auroc'])} [{f3(a['lo'])}, {f3(a['hi'])}] | {mb} | {f3(R['ece'])} | {f3(R['mean_abs_dp'])} | {f3(R['decision_flip_rate'])} | "
                f"{f3(R['accept_rate'])} | {f3(R['accepted_acc'])} | {f3(R['false_accept'])} | {f3(R['unparseable_rate'])} | {R['sec_per_label']:.2f} |\n")
    f.write("\n## Spread of AUROC: prompts vs models\n\n| family | members | SD [95% CI] | range [95% CI] | SD minus models SD |\n|---|---|---|---|---|\n")
    for k, R in res["spread"].items():
        d = R.get("sd_minus_models_sd")
        f.write(f"| {k} | {len(R['judges'])} | {f3(R['sd'])} [{f3(R['sd_ci'][0])}, {f3(R['sd_ci'][1])}] | {f3(R['range'])} [{f3(R['range_ci'][0])}, {f3(R['range_ci'][1])}] | "
                + ("" if d is None else f"{d['diff']:+.3f} [{d['ci'][0]:+.3f}, {d['ci'][1]:+.3f}]") + " |\n")
    f.write("\n## Transfer gates (frozen base tau), test subset\n\n| controller | accuracy | token-compute | acc minus visible->reroute | tok minus visible->reroute |\n|---|---|---|---|---|\n")
    for n, R in res["gates_transfer"].items():
        c = R.get("minus visible->reroute")
        f.write(f"| {n} | {R['acc'][0]:.3f} [{R['acc'][1]:.3f}, {R['acc'][2]:.3f}] | {R['tok'][0]:.0f} | " +
                ("| " if c is None else f"{c['acc']['diff']:+.3f} [{c['acc']['lo']:+.3f}, {c['acc']['hi']:+.3f}] | {c['tok']['diff']:+.0f} ") + "|\n")
print("wrote", out)

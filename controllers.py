#!/usr/bin/env python3
"""Judge-gated escalation analysis. Implements the analysis pre-registered in PREREG.md.

Decision point (all controllers): the LOCAL model writes a draft. A GATE then decides to accept it. If the gate
rejects it, the controller either REROUTES (asks the strong model) or RESAMPLES (asks the local model again).

  python controllers.py calibrate labeled.jsonl --out thresholds.json     # calibration split only; freezes tau per judge
  python controllers.py test labeled.jsonl --thresholds thresholds.json --report report.md --json results.json
  python controllers.py explore labeled.jsonl                           # pilot / sanity: any split, no hypothesis tests

Gates: judge:<name> (accept if p >= tau), visible (accept if the developer-available tests pass), oracle (accept if
hidden tests pass; an upper bound no real system has). Controllers:
  local-only              accept the first local draft unconditionally
  strong-only             always use the strong model (the accuracy reference for H2)
  <gate>->reroute         draft; accept if the gate passes, else one strong-model draw     (Chen's "fixed reroute")
  <gate>->resample(k)     up to k local drafts; accept the first that passes; if none, keep the best-scored draft
  <gate>->resample(k)->reroute   as above, but escalate if none passes (an adaptive hybrid; exploratory)
Each task's expected accuracy, USD and seconds are computed by Monte Carlo over that task's stored draws (local
drafts drawn without replacement, strong draws with replacement). Judge cost and latency are charged for every
draft the judge scores. Confidence intervals: cluster bootstrap over TASKS, paired across controllers.
Visible-test execution time is not measured and is charged as 0 s (it is small next to generation; stated in the paper).
Cost metric (frozen in thresholds.json): "tok" (token-compute: billion parameters x tokens, hardware-independent) in
the local-only design, chosen by Carson at STOP A because wall seconds on the fanless Mac varied with heat and power
state; "sec" (seconds per task) is reported as H5; "usd" applies only when a hosted tier is used. The cost metric
decides the cheapest tau and H2's savings test.
Secondary comparisons (PREREG v2 section 8): S1 primary judge gate->reroute vs local-only; S2 each judge vs selfconf
(paired AUROC difference, and judge:J->reroute vs selfconf->reroute at the frozen taus).
"""
import json, random, argparse, hashlib, math, sys
from collections import defaultdict
from jsonl import read_jsonl

# ---------- data ----------
def load(path, local, strong, split=None):
    """Scored, error-free draws of the two tiers, grouped by task. Also returns counts of rows that could not be
    used (errors, unscored) so that nothing disappears silently."""
    allr = [r for r in read_jsonl(path) if "_meta" not in r and (split is None or r.get("split") == split)]
    stats = {"rows": len(allr), "error_rows": sum(1 for r in allr if r.get("error")),
             "unscored_rows": sum(1 for r in allr if not r.get("error") and r.get("hidden_passed") is None)}
    rows = [r for r in allr if not r.get("error") and r.get("hidden_passed") is not None]
    by = defaultdict(lambda: {"L": [], "S": []})
    for r in rows:
        if r["tier"] == local: by[r["task"]]["L"].append(r)
        elif r["tier"] == strong: by[r["task"]]["S"].append(r)
    tasks = {t: v for t, v in by.items() if v["L"] and v["S"]}
    stats["tasks_seen"] = len({r["task"] for r in allr})
    excluded = sorted({r["task"] for r in allr} - set(tasks))
    return tasks, excluded, rows, stats

def coverage(tasks, manifest_path, split, limit):
    """Compare usable tasks with the split manifest. Fails (PREREG section 10) if more than `limit` are missing."""
    m = json.load(open(manifest_path))
    expected = {i for i, sp in m["pairs"] if sp == split}
    missing = sorted(expected - set(tasks)); unexpected = sorted(set(tasks) - expected)
    if unexpected: raise SystemExit(f"{len(unexpected)} tasks are not in the {split} split of {manifest_path}: {unexpected[:5]}")
    frac = len(missing) / len(expected) if expected else 1.0
    info = {"expected": len(expected), "usable": len(expected) - len(missing), "missing": len(missing), "missing_ids": missing[:50], "missing_frac": frac}
    print(f"{split} coverage: {info['usable']}/{info['expected']} tasks usable ({frac:.1%} missing)")
    if frac > limit: raise SystemExit(f"more than {limit:.0%} of {split} tasks missing: fix collection or scoring first (PREREG section 10)")
    return info

def data_hash(tasks):
    h = hashlib.sha256()
    for t in sorted(tasks):
        for r in sorted(tasks[t]["L"] + tasks[t]["S"], key=lambda r: (r["tier"], r["rep"])):
            # judge labels count only on local drafts, so labeling strong-tier drafts later (style-bias check) does not
            # look like a change to the calibration data
            jl = {k: v["p"] for k, v in sorted((r.get("judges") or {}).items())} if r in tasks[t]["L"] else {}
            h.update(json.dumps([t, r["tier"], r["rep"], r["hidden_passed"], r.get("visible_passed"), jl]).encode())
    return h.hexdigest()

# ---------- gates ----------
def gate(kind, judge=None, tau=None):
    """Returns f(draft) -> (accept, score, usd, seconds, token-compute), or None if a visible verdict is missing.
    A draft the judge never labeled (judge error or spend cap) counts as a REJECTION with score -1, as in deployment:
    dropping it instead would remove mostly-wrong drafts and flatter the judge."""
    if kind == "judge":
        def f(d):
            j = (d.get("judges") or {}).get(judge)
            if j is None: return False, -1.0, 0.0, 0.0, 0.0
            return j["p"] >= tau, j["p"], j.get("cost") or 0.0, j.get("wall") or 0.0, (j.get("params_b") or 0.0) * (j.get("tokens") or 0)
    elif kind == "visible":
        def f(d):
            v = d.get("visible_passed")
            return None if v is None else (bool(v), float(bool(v)), 0.0, 0.0, 0.0)
    elif kind == "oracle":
        def f(d): return bool(d["hidden_passed"]), float(bool(d["hidden_passed"])), 0.0, 0.0, 0.0
    else: raise ValueError(kind)
    return f

def _gen(d):
    """(usd, seconds, token-compute) of one draw. Seconds exclude a model load Ollama reported (wall_s_net) when
    recorded; token-compute = parameters (billions) x (prompt + generated tokens)."""
    sec = d["wall_s_net"] if d.get("wall_s_net") is not None else (d.get("wall_s") or 0.0)
    return d.get("cost_usd") or 0.0, sec, (d.get("params_b") or 0.0) * ((d.get("tokens_in") or 0) + (d.get("tokens_out") or 0))

# ---------- controllers on one task (one Monte Carlo replicate) ----------
def run_ctrl(name, L, S, rnd, g=None, k=1):
    if name == "strong-only":
        s = rnd.choice(S); c, w, x = _gen(s); return float(s["hidden_passed"]), c, w, x
    usable = L if g is None else [d for d in L if g(d) is not None]
    if not usable: return None
    order = rnd.sample(usable, len(usable))
    if name == "local-only":
        d = order[0]; c, w, x = _gen(d); return float(d["hidden_passed"]), c, w, x
    cost = wall = comp = 0.0; best = None
    tries = 1 if name == "reroute" else min(k, len(order))
    for d in order[:tries]:
        acc, score, gc, gw, gx = g(d); c, w, x = _gen(d); cost += c + gc; wall += w + gw; comp += x + gx
        if acc: return float(d["hidden_passed"]), cost, wall, comp
        if best is None or score > best[0]: best = (score, d)
    if name == "resample":
        return float(best[1]["hidden_passed"]), cost, wall, comp
    s = rnd.choice(S); c, w, x = _gen(s)                 # reroute, or resample->reroute exhausted
    return float(s["hidden_passed"]), cost + c, wall + w, comp + x

METRICS = ("acc", "usd", "sec", "tok")   # per-task tuple layout; tok = token-compute (billion parameters x tokens)

def per_task(tasks, spec, mc, seed):
    """spec = (ctrl_name, gate_fn or None, k). Returns {task: (acc, usd, sec, tok)} expectations; tasks with no usable draws omitted."""
    out = {}
    for t in sorted(tasks):
        rnd = random.Random(f"{seed}|{t}|{spec[0]}|{spec[2]}")
        res = [run_ctrl(spec[0], tasks[t]["L"], tasks[t]["S"], rnd, spec[1], spec[2]) for _ in range(mc)]
        if res[0] is None: continue
        out[t] = tuple(sum(x[i] for x in res) / mc for i in range(len(METRICS)))
    return out

# ---------- statistics ----------
def auroc(pos, neg):
    if not pos or not neg: return None
    allv = sorted([(v, 1) for v in pos] + [(v, 0) for v in neg])
    # rank-based (Mann-Whitney) with ties averaged
    ranks = {}; i = 0
    while i < len(allv):
        j = i
        while j < len(allv) and allv[j][0] == allv[i][0]: j += 1
        for m in range(i, j): ranks.setdefault(allv[m][0], (i + j + 1) / 2)
        i = j
    rp = sum(ranks[v] for v in pos)
    return (rp - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))

def pct(xs, q):
    xs = sorted(xs); i = (len(xs) - 1) * q; lo = math.floor(i); hi = math.ceil(i)
    return xs[lo] + (xs[hi] - xs[lo]) * (i - lo)

def boot_idx(n, B, seed):
    rnd = random.Random(seed); return [[rnd.randrange(n) for _ in range(n)] for _ in range(B)]

def mean_ci(vals, idx):
    m = sum(vals) / len(vals); bs = [sum(vals[i] for i in ix) / len(ix) for ix in idx]
    return m, pct(bs, 0.025), pct(bs, 0.975)

def judge_auroc(tasks, judge, idx_tasks, B, seed):
    names = sorted(tasks); draws = {t: [d for d in tasks[t]["L"] if (d.get("judges") or {}).get(judge)] for t in names}
    def au(sel):
        pos = [d["judges"][judge]["p"] for t in sel for d in draws[t] if d["hidden_passed"]]
        neg = [d["judges"][judge]["p"] for t in sel for d in draws[t] if not d["hidden_passed"]]
        return auroc(pos, neg), len(pos), len(neg)
    a, npos, nneg = au(names)
    if a is None or B == 0: return dict(auroc=a, lo=None, hi=None, n_correct=npos, n_wrong=nneg)
    bs = [x for x in (au([names[i] for i in ix])[0] for ix in boot_idx(len(names), B, seed)) if x is not None]
    return dict(auroc=a, lo=pct(bs, 0.025), hi=pct(bs, 0.975), n_correct=npos, n_wrong=nneg)

def paired_auroc_diff(tasks, j1, j2, idx):
    """AUROC(j1) - AUROC(j2) on the local drafts both judges labeled, with a task-cluster bootstrap CI (same resamples)."""
    names = sorted(tasks)
    both = {t: [d for d in tasks[t]["L"] if (d.get("judges") or {}).get(j1) and (d.get("judges") or {}).get(j2)] for t in names}
    def diff(sel):
        pos = [d for t in sel for d in both[t] if d["hidden_passed"]]; neg = [d for t in sel for d in both[t] if not d["hidden_passed"]]
        a1 = auroc([d["judges"][j1]["p"] for d in pos], [d["judges"][j1]["p"] for d in neg])
        a2 = auroc([d["judges"][j2]["p"] for d in pos], [d["judges"][j2]["p"] for d in neg])
        return None if a1 is None or a2 is None else a1 - a2
    dd = diff(names); bs = [x for x in (diff([names[i] for i in ix]) for ix in idx) if x is not None]
    return dict(diff=dd, lo=pct(bs, 0.025) if bs else None, hi=pct(bs, 0.975) if bs else None)

def within_task_auroc(tasks, judge, idx, seed):
    """Task-stratified AUROC: only pairs (correct draft, wrong draft) from the SAME task. Pooled AUROC can be high
    just because a judge recognizes easy tasks; resampling decisions need discrimination within a task."""
    names = sorted(tasks); per = {}
    for t in names:
        ps = [(d["judges"][judge]["p"], d["hidden_passed"]) for d in tasks[t]["L"] if (d.get("judges") or {}).get(judge)]
        pos = [p for p, ok in ps if ok]; neg = [p for p, ok in ps if not ok]
        per[t] = (sum(1 if a > b else .5 if a == b else 0 for a in pos for b in neg), len(pos) * len(neg))
    def agg(sel):
        w = sum(per[t][1] for t in sel); return (sum(per[t][0] for t in sel) / w) if w else None
    a = agg(names)
    bs = [x for x in (agg([names[i] for i in ix]) for ix in idx) if x is not None]
    return dict(auroc=a, lo=pct(bs, .025) if bs else None, hi=pct(bs, .975) if bs else None,
                tasks_with_pairs=sum(1 for t in names if per[t][1]))

def unjudged(tasks, judge):
    return sum(1 for t in tasks for d in tasks[t]["L"] if not (d.get("judges") or {}).get(judge))

# ---------- threshold selection (calibration split only) ----------
TAU_RULE = "lb"   # pre-registered: "lb" = bootstrap lower bound rule (below); "parity" kept only for the simulation check
COST_IDX = {"usd": 1, "sec": 2, "tok": 3}   # position in a per-task (acc, usd, sec, tok) tuple

def choose_tau(tasks, judge, delta, mc, seed, boots=1000, rule=None, cost_metric="tok"):
    """PREREG section 7. Candidates: every distinct judge probability on the calibration split, plus infinity
    (always reroute). Feasible: the 2.5th percentile of a task-cluster bootstrap of the calibration accuracy
    difference (gate->reroute minus strong-only) is >= -delta/2. Among feasible taus pick the cheapest; if none is
    feasible, pick the most accurate. Requiring a bootstrap lower bound, not a point estimate, is the guard against
    selection optimism from trying many taus on ~150 tasks."""
    rule = rule or TAU_RULE
    ps = sorted({d["judges"][judge]["p"] for t in tasks for d in tasks[t]["L"] if (d.get("judges") or {}).get(judge)})
    if not ps: return None
    strong = per_task(tasks, ("strong-only", None, 1), mc, seed)
    names = sorted(tasks); idx = boot_idx(len(names), boots, seed + 7)
    cands = []
    for tau in ps + [math.inf]:                      # tau = inf means "always reroute after paying the judge"
        pt = per_task(tasks, ("reroute", gate("judge", judge, tau), 1), mc, seed)
        common = [t for t in names if t in pt and t in strong]
        d = {t: pt[t][0] - strong[t][0] for t in common}
        ci = COST_IDX[cost_metric]
        acc = sum(pt[t][0] for t in common) / len(common); cost = sum(pt[t][ci] for t in common) / len(common)
        acc_s = sum(strong[t][0] for t in common) / len(common)
        bs = [sum(d[names[i]] for i in ix if names[i] in d) / max(1, sum(1 for i in ix if names[i] in d)) for ix in idx]
        lb = pct(bs, 0.025)
        feas = (lb >= -delta / 2) if rule == "lb" else (acc >= acc_s)
        cands.append(dict(tau=tau, acc=acc, cost=cost, acc_strong=acc_s, diff_lb=lb, feasible=feas))
    feas = [c for c in cands if c["feasible"]]
    pick = min(feas, key=lambda c: (c["cost"], -c["acc"])) if feas else max(cands, key=lambda c: (c["acc"], -c["cost"]))
    why = {"lb": "cheapest tau whose calibration bootstrap lower bound of (gate - strong) accuracy is >= -delta/2",
           "parity": "cheapest tau with calibration accuracy >= strong-only"}[rule]
    return dict(pick, rule=why if feas else "no feasible tau: max accuracy", cost_metric=cost_metric,
                curve=[{k: (None if v == math.inf else v) for k, v in c.items()} for c in cands])

# ---------- commands ----------
def specs_for(judges, taus, k):
    sp = {"local-only": ("local-only", None, 1), "strong-only": ("strong-only", None, 1)}
    for gname, g in [("visible", gate("visible")), ("oracle", gate("oracle"))] + \
                    [(f"judge:{j}", gate("judge", j, taus[j])) for j in judges if taus.get(j) is not None]:
        sp[f"{gname}->reroute"] = ("reroute", g, 1)
        sp[f"{gname}->resample({k})"] = ("resample", g, k)
        sp[f"{gname}->resample({k})->reroute"] = ("resample-reroute", g, k)
    return sp

def compare(pt, a, b, idx_names, names):
    """Paired difference a - b over tasks present in both; returns dict for accuracy, usd, seconds."""
    common = [t for t in names if t in pt[a] and t in pt[b]]
    pos = {t: i for i, t in enumerate(common)}
    out = {}
    for m, key in enumerate(METRICS):
        d = [pt[a][t][m] - pt[b][t][m] for t in common]
        idx = [[pos[names[i]] for i in ix if names[i] in pos] for ix in idx_names]
        bs = [sum(d[i] for i in ix) / len(ix) for ix in idx if ix]
        out[key] = dict(diff=sum(d) / len(d), lo=pct(bs, 0.025), hi=pct(bs, 0.975))
    out["n_tasks"] = len(common)
    return out

def summarize(tasks, specs, mc, seed, B):
    names = sorted(tasks); idx = boot_idx(len(names), B, seed + 1)
    pt = {n: per_task(tasks, s, mc, seed) for n, s in specs.items()}
    rows = {}
    for n in specs:
        sel = [t for t in names if t in pt[n]]; pos = {t: i for i, t in enumerate(sel)}
        sub = [[pos[names[i]] for i in ix if names[i] in pos] for ix in idx]
        rows[n] = {m: mean_ci([pt[n][t][j] for t in sel], [s for s in sub if s]) for j, m in enumerate(METRICS)}
        rows[n]["n_tasks"] = len(sel)
    return pt, rows, names, idx

def difficulty_bins(tasks, hard_max):
    return {t: ("hard" if sum(d["hidden_passed"] for d in v["L"]) / len(v["L"]) <= hard_max else "not-hard") for t, v in tasks.items()}

def stopping_debt(tasks, judge, tau, bins, idx, names):
    def far(sel, b):
        wrong = [d for t in sel if bins[t] == b for d in tasks[t]["L"] if not d["hidden_passed"] and (d.get("judges") or {}).get(judge)]
        return (sum(d["judges"][judge]["p"] >= tau for d in wrong) / len(wrong)) if wrong else None
    base = {b: far(names, b) for b in ("hard", "not-hard")}
    diffs = []
    for ix in idx:
        sel = [names[i] for i in ix]; h, nh = far(sel, "hard"), far(sel, "not-hard")
        if h is not None and nh is not None: diffs.append(h - nh)
    wa = [t for t in names for d in tasks[t]["L"] if not d["hidden_passed"] and (d.get("judges") or {}).get(judge) and d["judges"][judge]["p"] >= tau]
    recover = [sum(s["hidden_passed"] for s in tasks[t]["S"]) / len(tasks[t]["S"]) for t in wa]
    return dict(false_accept_rate=base, diff=(base["hard"] - base["not-hard"]) if None not in base.values() else None,
                lo=pct(diffs, 0.025) if diffs else None, hi=pct(diffs, 0.975) if diffs else None,
                n_wrong_accepts=len(wa), strong_success_on_wrong_accepts=(sum(recover) / len(recover)) if recover else None)

def two_stage_ci(tasks, spec_a, spec_b, B, mc, seed):
    """Sensitivity: resample tasks AND draws within each task (slower, wider). Accuracy difference a - b."""
    rnd = random.Random(seed); names = sorted(tasks); out = []
    for _ in range(B):
        sel = [rnd.choice(names) for _ in names]
        bt = {f"{i}": {"L": [rnd.choice(tasks[t]["L"]) for _ in tasks[t]["L"]], "S": [rnd.choice(tasks[t]["S"]) for _ in tasks[t]["S"]]} for i, t in enumerate(sel)}
        pa, pb = per_task(bt, spec_a, mc, seed), per_task(bt, spec_b, mc, seed)
        common = [t for t in pa if t in pb]
        if common: out.append(sum(pa[t][0] - pb[t][0] for t in common) / len(common))
    return dict(lo=pct(out, 0.025), hi=pct(out, 0.975), B=B)

def fmt(x, nd=3): return "n/a" if x is None else (f"{x:.{nd}f}" if isinstance(x, float) else str(x))

def cmd_calibrate(a):
    if not a.primary_judge: raise SystemExit("--primary-judge is required: it is fixed at Gate 1 and frozen here")
    tasks, excl, _, stats = load(a.path, a.local, a.strong, "cal")
    if not tasks: raise SystemExit("no calibration tasks with both local and strong draws")
    cov = coverage(tasks, a.manifest, "cal", a.max_missing)
    out = {"prereg": "PREREG.md v1", "delta": a.delta, "k": a.k, "local": a.local, "strong": a.strong, "mc": a.mc, "seed": a.seed,
           "primary_judge": a.primary_judge, "hard_max": a.hard_max, "cost_metric": a.cost_metric, "secondary_cost_metric": "sec" if a.cost_metric == "tok" else "tok",
           "n_cal_tasks": len(tasks), "excluded_cal_tasks": excl,
           "row_stats": stats, "coverage": cov, "cal_data_sha256": data_hash(tasks), "taus": {}, "details": {}}
    for j in a.judges.split(","):
        c = choose_tau(tasks, j, a.delta, a.mc, a.seed, cost_metric=a.cost_metric)
        if c is None: print(f"judge {j}: no labels on calibration split; skipped"); continue
        out["taus"][j] = "always-reroute" if c["tau"] == math.inf else c["tau"]; out["details"][j] = c
        out["details"][j]["unjudged_cal_drafts"] = unjudged(tasks, j)
        print(f"judge {j}: tau={out['taus'][j]} cal acc={c['acc']:.3f} (strong-only {c['acc_strong']:.3f}) {a.cost_metric}={c['cost']:.5f} [{c['rule']}]")
    if a.primary_judge not in out["taus"]: raise SystemExit(f"primary judge {a.primary_judge} has no calibration labels")
    json.dump(out, open(a.out, "w"), indent=1, default=str); print("froze thresholds ->", a.out, "(commit this file before running test)")

def cmd_test(a):
    th = json.load(open(a.thresholds))
    # every analysis setting comes from the frozen file; command-line values may not differ
    frozen = ("local", "strong", "delta", "k", "mc", "seed", "hard_max", "primary_judge", "cost_metric")
    for key in frozen:
        cli = getattr(a, key)
        if cli is not None and cli != th[key]: raise SystemExit(f"--{key}={cli} differs from the frozen thresholds file ({th[key]}); refusing")
    for key in frozen: setattr(a, key, th[key])
    cal, _, _, _ = load(a.path, a.local, a.strong, "cal")
    if data_hash(cal) != th["cal_data_sha256"]:
        raise SystemExit("calibration data changed since thresholds were frozen (re-scored or re-judged?); refusing")
    tasks, excl, _, stats = load(a.path, a.local, a.strong, "test")
    if not tasks: raise SystemExit("no test tasks with both local and strong draws")
    cov = coverage(tasks, a.manifest, "test", a.max_missing)
    taus = {j: (math.inf if v == "always-reroute" else v) for j, v in th["taus"].items()}
    judges = list(taus); specs = specs_for(judges, taus, a.k)
    pt, rows, names, idx = summarize(tasks, specs, a.mc, a.seed, a.boots)
    res = {"n_test_tasks": len(names), "excluded_test_tasks": excl, "row_stats": stats, "coverage": cov, "thresholds": th["taus"],
           "delta": a.delta, "primary_judge": a.primary_judge, "cost_metric": a.cost_metric, "unjudged_test_drafts": {j: unjudged(tasks, j) for j in judges},
           "controllers": rows, "hypotheses": {}}
    H = res["hypotheses"]
    H["H1_auroc"] = {j: judge_auroc(tasks, j, idx, a.boots, a.seed + 2) for j in judges}
    H["H1_within_task_auroc"] = {j: within_task_auroc(tasks, j, idx, a.seed) for j in judges}
    H["H2_gate_vs_strong"] = {}
    for g in [f"judge:{j}" for j in judges] + ["visible", "oracle"]:
        n = f"{g}->reroute"
        if n not in pt or not pt[n]: continue
        c = compare(pt, n, "strong-only", idx, names)
        c["noninferior"] = c["acc"]["lo"] > -a.delta; c["cheaper"] = c[a.cost_metric]["hi"] < 0
        c["supported"] = c["noninferior"] and c["cheaper"]
        H["H2_gate_vs_strong"][g] = c
    if a.two_stage and f"judge:{a.primary_judge}->reroute" in pt:
        H["H2_primary_two_stage_sensitivity"] = two_stage_ci(tasks, specs[f"judge:{a.primary_judge}->reroute"], specs["strong-only"], a.two_stage, max(20, a.mc // 10), a.seed + 3)
    H["H3_reroute_vs_resample"] = {}
    for g in [f"judge:{j}" for j in judges] + ["visible"]:
        r, s, h = f"{g}->reroute", f"{g}->resample({a.k})", f"{g}->resample({a.k})->reroute"
        if r not in pt or not pt[r]: continue
        c1 = compare(pt, r, s, idx, names); c2 = compare(pt, h, r, idx, names)
        H["H3_reroute_vs_resample"][g] = dict(reroute_minus_resample=c1, reroute_beats_resample=c1["acc"]["lo"] > 0,
                                              hybrid_minus_reroute=c2, no_hybrid_gain_over_delta=c2["acc"]["hi"] < a.delta)
    bins = difficulty_bins(tasks, a.hard_max)
    H["H4_stopping_debt"] = {j: dict(stopping_debt(tasks, j, taus[j], bins, idx, names), hard_tasks=sum(b == "hard" for b in bins.values()))
                             for j in judges if taus[j] != math.inf}
    H["H5_latency"] = {n: rows[n]["sec"] for n in rows}
    # S1: what the judge adds over never escalating (read together with H2)
    p_r = f"judge:{a.primary_judge}->reroute"
    if p_r in pt and pt[p_r]: H["S1_gate_vs_local_only"] = compare(pt, p_r, "local-only", idx, names)
    # S2: each judge against the generator's own confidence (selfconf), the free baseline
    if "selfconf" in judges:
        H["S2_judge_vs_selfconf"] = {}
        for j in judges:
            if j == "selfconf": continue
            c = {"auroc_diff": paired_auroc_diff(tasks, j, "selfconf", idx)}
            if f"judge:{j}->reroute" in pt and "judge:selfconf->reroute" in pt:
                c["reroute_diff"] = compare(pt, f"judge:{j}->reroute", "judge:selfconf->reroute", idx, names)
            H["S2_judge_vs_selfconf"][j] = c
    json.dump(res, open(a.json, "w"), indent=1, default=str)
    write_report(res, a.report, a.primary_judge); print("wrote", a.report, "and", a.json)

def write_report(res, path, primary):
    L = [f"# Test-split results ({res['n_test_tasks']} tasks; excluded {len(res['excluded_test_tasks'])}; rows {res['row_stats']}; coverage {res['coverage'] and {k: v for k, v in res['coverage'].items() if k != 'missing_ids'}})", "",
         f"Frozen thresholds: {res['thresholds']}. Non-inferiority margin delta = {res['delta']}. Primary judge: {primary or 'not set'}. "
         f"Cost metric for the cheapest tau and H2 savings: {res.get('cost_metric', 'usd')}.", "",
         "## Controllers (mean [95% cluster-bootstrap CI])", "", "| controller | accuracy | USD/task | s/task | token-compute/task (B-param x tokens) | tasks |", "|---|---|---|---|---|---|"]
    for n, r in res["controllers"].items():
        L.append(f"| {n} | {r['acc'][0]:.3f} [{r['acc'][1]:.3f}, {r['acc'][2]:.3f}] | {r['usd'][0]:.5f} [{r['usd'][1]:.5f}, {r['usd'][2]:.5f}] | {r['sec'][0]:.1f} [{r['sec'][1]:.1f}, {r['sec'][2]:.1f}] | {r['tok'][0]:.0f} [{r['tok'][1]:.0f}, {r['tok'][2]:.0f}] | {r['n_tasks']} |")
    H = res["hypotheses"]
    L += ["", "## H1 judge discrimination (AUROC vs hidden-test correctness of local drafts)", ""]
    for j, v in H["H1_auroc"].items():
        w = H["H1_within_task_auroc"][j]
        L.append(f"- {j}: AUROC {fmt(v.get('auroc'))} [{fmt(v.get('lo'))}, {fmt(v.get('hi'))}]; correct {v['n_correct']}, wrong {v['n_wrong']}; supported: {v.get('lo') is not None and v['lo'] > 0.5}; "
                 f"within-task AUROC {fmt(w['auroc'])} [{fmt(w['lo'])}, {fmt(w['hi'])}] over {w['tasks_with_pairs']} tasks; unjudged drafts (counted as rejections) {res['unjudged_test_drafts'][j]}")
    L += ["", "## H2 gate->reroute vs strong-only (paired differences)", ""]
    for g, c in H["H2_gate_vs_strong"].items():
        L.append(f"- {g}: accuracy {c['acc']['diff']:+.3f} [{c['acc']['lo']:+.3f}, {c['acc']['hi']:+.3f}], USD {c['usd']['diff']:+.5f} [{c['usd']['lo']:+.5f}, {c['usd']['hi']:+.5f}], "
                 f"seconds {c['sec']['diff']:+.1f}, token-compute {c['tok']['diff']:+.0f}; non-inferior {c['noninferior']}, cheaper {c['cheaper']}, supported {c['supported']}")
    if "H2_primary_two_stage_sensitivity" in H:
        s = H["H2_primary_two_stage_sensitivity"]; L.append(f"- sensitivity (two-stage bootstrap, primary judge, accuracy diff): [{s['lo']:+.3f}, {s['hi']:+.3f}]")
    if "S1_gate_vs_local_only" in H:
        c = H["S1_gate_vs_local_only"]
        L += ["", "## S1 what the primary judge adds: gate->reroute vs local-only (read H2 together with this)", "",
              f"- accuracy {c['acc']['diff']:+.3f} [{c['acc']['lo']:+.3f}, {c['acc']['hi']:+.3f}], token-compute {c['tok']['diff']:+.0f} "
              f"[{c['tok']['lo']:+.0f}, {c['tok']['hi']:+.0f}], seconds {c['sec']['diff']:+.1f} [{c['sec']['lo']:+.1f}, {c['sec']['hi']:+.1f}]"]
    if "S2_judge_vs_selfconf" in H:
        L += ["", "## S2 judges vs the generator's own confidence (selfconf)", ""]
        for j, c in H["S2_judge_vs_selfconf"].items():
            ad = c["auroc_diff"]; line = f"- {j}: AUROC difference {fmt(ad['diff'])} [{fmt(ad['lo'])}, {fmt(ad['hi'])}]"
            if "reroute_diff" in c:
                r = c["reroute_diff"]
                line += f"; judge:{j}->reroute minus selfconf->reroute: accuracy {r['acc']['diff']:+.3f} [{r['acc']['lo']:+.3f}, {r['acc']['hi']:+.3f}], token-compute {r['tok']['diff']:+.0f}"
            L.append(line)
    L += ["", "## H3 after rejection: reroute vs resample", ""]
    for g, c in H["H3_reroute_vs_resample"].items():
        r, h = c["reroute_minus_resample"]["acc"], c["hybrid_minus_reroute"]["acc"]
        L.append(f"- {g}: reroute - resample {r['diff']:+.3f} [{r['lo']:+.3f}, {r['hi']:+.3f}] (reroute better: {c['reroute_beats_resample']}); "
                 f"hybrid - reroute {h['diff']:+.3f} [{h['lo']:+.3f}, {h['hi']:+.3f}] (no gain > delta: {c['no_hybrid_gain_over_delta']})")
    L += ["", "## H4 stopping debt by difficulty (false-accept rate among wrong drafts)", ""]
    for j, s in H["H4_stopping_debt"].items():
        L.append(f"- {j}: hard {fmt(s['false_accept_rate']['hard'])} vs not-hard {fmt(s['false_accept_rate']['not-hard'])}; diff {fmt(s['diff'])} [{fmt(s['lo'])}, {fmt(s['hi'])}]; "
                 f"{s['n_wrong_accepts']} wrong accepts, strong model right on those tasks {fmt(s['strong_success_on_wrong_accepts'])}; hard tasks {s['hard_tasks']}")
    L += ["", "H5 (latency) is the s/task column above. Visible-test execution time is charged as 0 s and 0 token-compute."]
    open(path, "w").write("\n".join(L) + "\n")

def cmd_explore(a):
    if a.split != "cal": print("WARNING: exploring a non-calibration split. PREREG forbids this before thresholds are committed.")
    tasks, excl, rows, stats = load(a.path, a.local, a.strong, a.split)
    print(f"tasks {len(tasks)} (excluded {len(excl)}), usable draws {len(rows)}, row stats {stats}")
    judges = [j for j in a.judges.split(",") if j]
    for j in judges:
        au = judge_auroc(tasks, j, [], 0, 0); print(f"judge {j}: AUROC {fmt(au.get('auroc'))} (correct {au['n_correct']}, wrong {au['n_wrong']})")
        c = choose_tau(tasks, j, a.delta, a.mc, a.seed, cost_metric=a.cost_metric)
        if c:
            for p in c["curve"]: print(f"   tau={fmt(p['tau'], 2)} acc={p['acc']:.3f} {a.cost_metric}={p['cost']:.5f} strong={p['acc_strong']:.3f} feasible={p['feasible']}")
    taus = {j: 0.5 for j in judges}
    _, r, _, _ = summarize(tasks, specs_for(judges, taus, a.k), a.mc, a.seed, 200)
    for n, v in r.items(): print(f"{n:42s} acc {v['acc'][0]:.3f}  usd {v['usd'][0]:.5f}  s {v['sec'][0]:.1f}  tok {v['tok'][0]:.0f}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=["calibrate", "test", "explore"]); ap.add_argument("path")
    ap.add_argument("--local"); ap.add_argument("--strong"); ap.add_argument("--judges", default="tev,llama,selfconf")
    ap.add_argument("--cost-metric", choices=sorted(COST_IDX))
    ap.add_argument("--k", type=int); ap.add_argument("--delta", type=float); ap.add_argument("--hard-max", type=float)
    ap.add_argument("--mc", type=int); ap.add_argument("--seed", type=int); ap.add_argument("--boots", type=int, default=2000)
    ap.add_argument("--out", default="thresholds.json"); ap.add_argument("--thresholds", default="thresholds.json")
    ap.add_argument("--report", default="report.md"); ap.add_argument("--json", default="results.json")
    ap.add_argument("--primary-judge", default=None); ap.add_argument("--two-stage", type=int, default=0)
    ap.add_argument("--manifest", default=None, help="split manifest from suites.py (required for calibrate and test)")
    ap.add_argument("--max-missing", type=float, default=0.05)
    ap.add_argument("--split", default="cal", help="explore only: cal (default). Looking at test before thresholds are frozen breaks PREREG")
    a = ap.parse_args()
    if a.cmd in ("calibrate", "test") and not a.manifest: raise SystemExit("--manifest is required (PREREG section 10 coverage check)")
    if a.cmd != "test":   # defaults for calibrate and explore; test takes every value from the frozen file
        for k, v in dict(local="local3b", strong="strong14b", k=3, delta=0.03, hard_max=1 / 3, mc=200, seed=20261009, cost_metric="tok").items():
            if getattr(a, k) is None: setattr(a, k, v)
    {"calibrate": cmd_calibrate, "test": cmd_test, "explore": cmd_explore}[a.cmd](a)

#!/usr/bin/env python3
"""E12 (exploratory): controllers beyond the baseline, simulated from stored draws. No generation, no judge calls.
  nice python3 ext/E12/sim.py runs/confirmatory.labeled.jsonl ext/E12/out [--pilot]
--pilot: 20 tasks per split, 20 Monte Carlo replicates, 200 bootstrap resamples (timing and plumbing check only).

Uses controllers.py's own gates, Monte Carlo replicates, bootstrap and tau rule unchanged (imported, not edited).
Combined gates are built as synthetic judge labels on each local draft, so controllers.gate("judge") and
choose_tau() apply to them as to any judge:
  vis&J      accept iff the visible tests pass AND judge J accepts; J is called only when the visible tests pass,
             so its cost is charged only then (visible-test execution is charged 0, as in the main study)
  tev&sc     accept iff tev AND selfconf accept;  tev|sc  accept iff tev OR selfconf accepts (tev always called)
Two modes for every gate: transfer (the frozen thresholds.json taus) and recal (tau refit on the calibration split
with controllers.choose_tau, same rule and cost metric). For tev&sc and tev|sc the recal score is the min / max of
the two judges' calibration-split percentile ranks, so one tau can be refit.
Also: visible and tev resample(k)->reroute for k = 1..5, a 3B -> 7B -> 14B cascade, and accuracy-vs-cost curves
over a tau grid for each judge. All results on both splits; the test split is the headline (exploratory, post-hoc)."""
import bisect, json, math, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import controllers as C
from jsonl import read_jsonl

inp, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True); PILOT = "--pilot" in sys.argv
TH = json.load(open("thresholds.json")); MC, SEED, B, DELTA = TH["mc"], TH["seed"], 2000, TH["delta"]
if PILOT: MC, B = 20, 200
TAU = {j: (math.inf if v == "always-reroute" else v) for j, v in TH["taus"].items()}
TIERS = ("local1p5b", "local3b", "local7b", "strong14b")

rows = [r for r in read_jsonl(inp) if "_meta" not in r and not r.get("error") and r.get("hidden_passed") is not None]
J = lambda r, j: (r.get("judges") or {}).get(j)

# percentile ranks from calibration-split 3B drafts (for the recal score of tev&sc / tev|sc)
cal3 = [r for r in rows if r["split"] == "cal" and r["tier"] == "local3b"]
ranks = {j: sorted(J(r, j)["p"] for r in cal3 if J(r, j)) for j in ("tev", "selfconf")}
F = lambda j, p: bisect.bisect_right(ranks[j], p) / len(ranks[j])

def lab(p, called=None):
    """Synthetic judge label; `called` is the tev label whose cost is charged, or None if no paid call was made."""
    c = called or {}
    return {"p": p, "cost": c.get("cost") or 0.0, "wall": c.get("wall") or 0.0,
            "params_b": c.get("params_b") or 0.0, "tokens": c.get("tokens") or 0}

for r in rows:
    js = r.setdefault("judges", {}); vis = bool(r.get("visible_passed"))
    for j in ("tev", "llama", "selfconf"):
        if J(r, j): js[f"vis&{j}"] = lab(js[j]["p"] if vis else 0.0, js[j] if vis else None)
    t, s = J(r, "tev"), J(r, "selfconf")
    if t and s:
        a_t, a_s = t["p"] >= TAU["tev"], s["p"] >= TAU["selfconf"]
        js["tev&sc@frozen"] = lab(float(a_t and a_s), t); js["tev|sc@frozen"] = lab(float(a_t or a_s), t)
        js["tev&sc"] = lab(min(F("tev", t["p"]), F("selfconf", s["p"])), t)
        js["tev|sc"] = lab(max(F("tev", t["p"]), F("selfconf", s["p"])), t)

def group(split, local, strong="strong14b"):
    by = {}
    for r in rows:
        if r["split"] != split: continue
        by.setdefault(r["task"], {k: [] for k in TIERS})[r["tier"]].append(r)
    tasks = {t: dict(v, L=v[local], S=v[strong]) for t, v in by.items() if v[local] and v[strong]}
    return {t: tasks[t] for t in sorted(tasks)[:20]} if PILOT else tasks

def cascade_task(v, mc, seed, gate_name, g):
    """3B -> 7B -> 14B: draw a 3B draft and gate it; on rejection draw a 7B draft and gate it with the same gate;
    on rejection draw a 14B draft. Costs of every draw and gate call are summed."""
    rnd = random.Random(f"{seed}|cascade|{gate_name}"); res = []
    for _ in range(mc):
        acc = cost = wall = comp = 0.0
        for tier in ("local3b", "local7b"):
            d = rnd.choice(v[tier]); ok, _, gc, gw, gx = g(d); c, w, x = C._gen(d)
            cost += c + gc; wall += w + gw; comp += x + gx
            if ok: acc = float(d["hidden_passed"]); break
        else:
            s = rnd.choice(v["strong14b"]); c, w, x = C._gen(s); acc = float(s["hidden_passed"]); cost += c; wall += w; comp += x
        res.append((acc, cost, wall, comp))
    return tuple(sum(x[i] for x in res) / mc for i in range(4))

def evaluate(split, taus_by_mode):
    tasks = group(split, "local3b"); names = sorted(tasks); idx = C.boot_idx(len(names), B, SEED + 1)
    specs = {"strong-only": ("strong-only", None, 1), "local-only": ("local-only", None, 1),
             "visible->reroute": ("reroute", C.gate("visible"), 1)}
    for k in (2, 3, 4, 5):
        specs[f"visible->resample({k})->reroute"] = ("resample-reroute", C.gate("visible"), k)
    for mode, taus in taus_by_mode.items():
        for j, tau in taus.items():
            if tau is None: continue
            g = C.gate("judge", j, tau)
            specs[f"[{mode}] {j}->reroute"] = ("reroute", g, 1)
            if j == "tev":
                for k in (2, 3, 4, 5): specs[f"[{mode}] tev->resample({k})->reroute"] = ("resample-reroute", g, k)
    pt = {n: C.per_task(tasks, s, MC, SEED) for n, s in specs.items()}
    # cascades: visible gate, and the frozen tev and vis&tev gates (transfer mode only; the taus were set for the 3B)
    for gname, g in (("visible", C.gate("visible")), ("tev", C.gate("judge", "tev", TAU["tev"])),
                     ("vis&tev", C.gate("judge", "vis&tev", TAU["tev"]))):
        n = f"cascade 3B->7B->14B gate {gname}" + ("" if gname == "visible" else " [transfer]")
        pt[n] = {t: cascade_task(tasks[t], MC, SEED, gname + t, g) for t in names if tasks[t]["local7b"]}
    rows_out = {}
    for n in pt:
        sel = [t for t in names if t in pt[n]]; pos = {t: i for i, t in enumerate(sel)}
        sub = [[pos[names[i]] for i in ix if names[i] in pos] for ix in idx]
        rows_out[n] = {m: C.mean_ci([pt[n][t][i] for t in sel], [s for s in sub if s]) for i, m in enumerate(C.METRICS)}
        rows_out[n]["n_tasks"] = len(sel)
    cmp = {}
    for n in pt:
        for base in ("strong-only", "visible->reroute"):
            if n != base: cmp[f"{n} minus {base}"] = C.compare(pt, n, base, idx, names)
    return tasks, rows_out, cmp

# recalibrated taus: the pre-registered rule on the calibration split, for every gate
cal_tasks = group("cal", "local3b")
GATES = ["tev", "llama", "selfconf", "vis&tev", "vis&llama", "vis&selfconf", "tev&sc", "tev|sc"]
recal = {}
for j in GATES:
    c = C.choose_tau(cal_tasks, j, DELTA, MC, SEED, boots=200 if PILOT else 1000, cost_metric=TH["cost_metric"])
    recal[j] = c["tau"]; print(f"recal tau {j}: {c['tau']} ({c['rule']})", flush=True)
transfer = {"tev": TAU["tev"], "llama": TAU["llama"], "selfconf": TAU["selfconf"],
            "vis&tev": TAU["tev"], "vis&llama": TAU["llama"], "vis&selfconf": TAU["selfconf"],
            "tev&sc@frozen": 0.5, "tev|sc@frozen": 0.5}
modes = {"transfer": transfer, "recal": recal}

res = {"settings": {"mc": MC, "seed": SEED, "boots": B, "delta": DELTA, "cost_metric": TH["cost_metric"]},
       "taus": {m: {k: (None if v == math.inf else v) for k, v in t.items()} for m, t in modes.items()}, "splits": {}}
for split in ("cal", "test"):
    tasks, ro, cmp = evaluate(split, modes)
    res["splits"][split] = {"n_tasks": len(tasks), "controllers": ro, "comparisons": cmp}
    print(f"{split}: {len(tasks)} tasks, {len(ro)} controllers", flush=True)

# accuracy-vs-cost curves on the test split: 21 taus per judge at calibration-split quantiles of its 3B scores
test_tasks = group("test", "local3b"); curves = {}
for j in ("tev", "llama", "selfconf", "vis&tev", "vis&selfconf"):
    ps = sorted(r["judges"][j]["p"] for r in cal3 if J(r, j))
    grid = sorted({ps[min(len(ps) - 1, int(q * len(ps)))] for q in [i / 20 for i in range(20)]} | {math.inf})
    curves[j] = []
    for tau in grid:
        pt = C.per_task(test_tasks, ("reroute", C.gate("judge", j, tau), 1), MC, SEED)
        m = [sum(pt[t][i] for t in pt) / len(pt) for i in range(4)]
        curves[j].append({"tau": None if tau == math.inf else tau, "acc": m[0], "sec": m[2], "tok": m[3]})
res["curves_test"] = curves
json.dump(res, open(os.path.join(out, "results.json"), "w"), indent=1, default=str)

with open(os.path.join(out, "summary.md"), "w") as f:
    for split in ("test", "cal"):
        S = res["splits"][split]
        f.write(f"## {split} split ({S['n_tasks']} tasks): controllers, mean [95% task-cluster bootstrap CI]\n\n")
        f.write("| controller | accuracy | s/task | token-compute/task |\n|---|---|---|---|\n")
        for n, v in S["controllers"].items():
            a, s, t = v["acc"], v["sec"], v["tok"]
            f.write(f"| {n} | {a[0]:.3f} [{a[1]:.3f}, {a[2]:.3f}] | {s[0]:.1f} [{s[1]:.1f}, {s[2]:.1f}] | {t[0]:.0f} [{t[1]:.0f}, {t[2]:.0f}] |\n")
        f.write(f"\n### {split}: paired differences\n\n| comparison | accuracy | s/task | token-compute |\n|---|---|---|---|\n")
        for n, c in S["comparisons"].items():
            f.write(f"| {n} | {c['acc']['diff']:+.3f} [{c['acc']['lo']:+.3f}, {c['acc']['hi']:+.3f}] | {c['sec']['diff']:+.1f} "
                    f"[{c['sec']['lo']:+.1f}, {c['sec']['hi']:+.1f}] | {c['tok']['diff']:+.0f} [{c['tok']['lo']:+.0f}, {c['tok']['hi']:+.0f}] |\n")
        f.write("\n")
    f.write("## Recalibrated taus (calibration split, pre-registered rule)\n\n")
    for j, t in res["taus"]["recal"].items(): f.write(f"- {j}: {t}\n")
print("wrote", out)

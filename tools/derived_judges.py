#!/usr/bin/env python3
"""Add derived judges to labeled rows (KICKOFF2 T21, exploratory). Fits use calibration rows only.
  python3 tools/derived_judges.py IN.jsonl OUT.jsonl --base tev,llama,selfconf --tiers local3b [--fits fits.json] [--apply-only fits.json]

Derived judges written into r["judges"]:
  <j>_platt, <j>_iso      Platt-scaled and isotonic-recalibrated versions of each base judge j
  ens_mean                mean of the base judges' probabilities
  ens_stack               logistic regression on the base judges' logits (L2 = 1e-3)
Fits are made on calibration-split rows of the listed tiers whose hidden verdict is known, and saved to --fits.
--apply-only reuses saved fits (for later conditions: the "transfer" mode). A derived judge's cost, seconds and
token-compute are the sums over the base judges it needs; a row missing any needed base label gets no derived label
(and so counts as a rejection downstream, as for any unjudged draft)."""
import argparse, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import judgestats as S
from jsonl import read_jsonl

ap = argparse.ArgumentParser(); ap.add_argument("inp"); ap.add_argument("out"); ap.add_argument("--base", required=True)
ap.add_argument("--tiers", required=True); ap.add_argument("--fits"); ap.add_argument("--apply-only"); a = ap.parse_args()
base = a.base.split(","); tiers = set(a.tiers.split(","))
rows = read_jsonl(a.inp)
lab = lambda r, j: (r.get("judges") or {}).get(j)

if a.apply_only:
    fits = json.load(open(a.apply_only))
else:
    train = [r for r in rows if "_meta" not in r and r.get("split") == "cal" and r.get("tier") in tiers
             and r.get("hidden_passed") is not None and all(lab(r, j) for j in base)]
    if len(train) < 20: raise SystemExit(f"only {len(train)} calibration rows with every base label; need at least 20")
    ys = [int(bool(r["hidden_passed"])) for r in train]
    fits = {"base": base, "tiers": sorted(tiers), "n_train": len(train), "platt": {}, "iso": {}}
    for j in base:
        ps = [lab(r, j)["p"] for r in train]
        fits["platt"][j] = S.fit_platt(ps, ys); fits["iso"][j] = S.fit_isotonic(ps, ys)
    fits["stack"] = S.fit_logreg([[S.logit(lab(r, j)["p"]) for j in base] for r in train], ys)
    if a.fits: json.dump(fits, open(a.fits, "w"), indent=1)

def derived(r, name, p, need):
    parts = [lab(r, j) for j in need]
    r["judges"][name] = {"p": p, "cost": sum(x.get("cost") or 0 for x in parts), "wall": sum(x.get("wall") or 0 for x in parts),
                         # controllers charge params_b x tokens: carry the summed compute as tokens with params_b = 1
                         "tokens": sum((x.get("params_b") or 0) * (x.get("tokens") or 0) for x in parts), "params_b": 1.0, "derived_from": need}

n = 0
for r in rows:
    if "_meta" in r or r.get("tier") not in tiers or not r.get("judges"): continue
    for j in fits["base"]:
        if lab(r, j):
            derived(r, f"{j}_platt", S.apply_platt(fits["platt"][j], lab(r, j)["p"]), [j])
            derived(r, f"{j}_iso", S.apply_isotonic(fits["iso"][j], lab(r, j)["p"]), [j])
    if all(lab(r, j) for j in fits["base"]):
        ps = [lab(r, j)["p"] for j in fits["base"]]
        derived(r, "ens_mean", sum(ps) / len(ps), fits["base"])
        derived(r, "ens_stack", S.predict_logreg(fits["stack"], [S.logit(p) for p in ps]), fits["base"])
        n += 1
with open(a.out, "w") as f: f.writelines(json.dumps(r) + "\n" for r in rows)
print(f"derived judges added to {n} rows (fits on {fits['n_train']} calibration rows of {fits['tiers']}) -> {a.out}")

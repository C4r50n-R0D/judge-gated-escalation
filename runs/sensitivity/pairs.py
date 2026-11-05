#!/usr/bin/env python3
"""PREREG v2 section 11 sensitivity: H1 to H4 for the 7B->14B and 1.5B->14B pairs, with controllers.py unchanged.
  python3 runs/sensitivity/pairs.py
For each local tier, two thresholds files are derived from thresholds.json (only local, cal_data_sha256 and, for
"refit", the taus differ) and passed to `controllers.py test`:
  transfer  the frozen taus (fitted on 3B calibration drafts) applied as they are
  refit     taus from `controllers.py calibrate` on that pair's calibration drafts, same rule, delta and cost metric
Reports: runs/sensitivity/<local>.<mode>.{md,json}. Exploratory; never feeds back into H1 to H5."""
import json, os, subprocess, sys
sys.path.insert(0, ".")
import controllers as C
D = "runs/sensitivity"; DATA = "runs/confirmatory.labeled.jsonl"; os.makedirs(D, exist_ok=True)
TH = json.load(open("thresholds.json"))
for local in ("local7b", "local1p5b"):
    cal, _, _, _ = C.load(DATA, local, TH["strong"], "cal")
    h = C.data_hash(cal)
    tmp = f"{D}/{local}.calibrate.json"
    subprocess.run(["python3", "controllers.py", "calibrate", DATA, "--local", local, "--strong", TH["strong"], "--manifest", "split_manifest.json", "--primary-judge", TH["primary_judge"],
                    "--out", tmp, "--delta", str(TH["delta"]), "--k", str(TH["k"]), "--cost-metric", TH["cost_metric"]], check=True)
    refit = json.load(open(tmp))["taus"]
    for mode, taus in (("transfer", TH["taus"]), ("refit", refit)):
        t = dict(TH, local=local, cal_data_sha256=h, taus=taus, derived_from="thresholds.json", sensitivity_mode=mode)
        p = f"{D}/thresholds.{local}.{mode}.json"; json.dump(t, open(p, "w"), indent=1)
        subprocess.run(["python3", "controllers.py", "test", DATA, "--thresholds", p, "--manifest", "split_manifest.json", "--primary-judge", TH["primary_judge"],
                        "--report", f"{D}/{local}.{mode}.md", "--json", f"{D}/{local}.{mode}.json", "--boots", "2000"], check=True)
        print(local, mode, "taus", taus, flush=True)

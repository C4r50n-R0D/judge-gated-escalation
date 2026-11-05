#!/usr/bin/env python3
"""Verify candidate-code transforms with the official evaluator (KICKOFF2 T18). Runs on the homelab.
  python3 tools/codemod_check.py SCORED_ROWS.jsonl SUITE TRANSFORM OUT_DIR [--split cal] [--seed 1]

SCORED_ROWS must already carry EvalPlus verdicts (hidden_passed). The transform is applied, the new code is scored
with evalplus.evaluate in the network-less container, and:
  preserve / inject: every row must keep its verdict; any change is a bug in the transform and is listed.
  mutate: applied to hidden-correct rows only; a mutant is kept only if it now FAILS (equivalent mutants dropped).
Writes OUT_DIR/<transform>.scored.jsonl (mutate: only the kept mutants) and OUT_DIR/<transform>.check.json."""
import argparse, json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import evalplus_io, suites
from jsonl import read_jsonl
from variants.codemods import CODE_TRANSFORMS, apply_rows

ap = argparse.ArgumentParser(); ap.add_argument("rows"); ap.add_argument("suite"); ap.add_argument("transform"); ap.add_argument("out_dir")
ap.add_argument("--split", default="cal"); ap.add_argument("--seed", type=int, default=1); a = ap.parse_args()
if a.split != "cal": raise SystemExit("Phase 2 verification uses calibration rows only")
kind = CODE_TRANSFORMS[a.transform][1]
rows = [r for r in read_jsonl(a.rows) if "_meta" not in r and r.get("split") == a.split and r.get("hidden_passed") is not None
        and r.get("suite", a.suite) == a.suite and (kind != "mutate" or r["hidden_passed"])]
mod, skipped = apply_rows(rows, a.transform, a.seed)
os.makedirs(a.out_dir, exist_ok=True); base = os.path.join(a.out_dir, a.transform)
for r in mod: r["suite"] = a.suite
with open(base + ".rows.jsonl", "w") as f: f.writelines(json.dumps(r) + "\n" for r in mod)
for stale in (base + ".samples_eval_results.json", base + ".scored.all.jsonl"):   # evalplus reuses an old results file
    if os.path.exists(stale): os.remove(stale)
evalplus_io.export(base + ".rows.jsonl", a.suite, base + ".samples.jsonl")
ds = suites.EVALPLUS_NAME[a.suite]; d = os.path.abspath(a.out_dir); s = os.path.basename(base) + ".samples.jsonl"
cmd = ["docker", "run", "--rm", "--network", "none", "--memory", "6g", "-e", "EVALPLUS_MAX_MEMORY_BYTES=8589934592", "-v", f"{d}:/app",
       "-v", "evalplus-cache:/root/.cache/evalplus", "evalplus:0.3.1", "evalplus.evaluate", "--dataset", ds, "--samples", f"/app/{s}", "--parallel", "1"]
with open(base + ".evalplus.log", "w") as log: subprocess.run(cmd, check=True, stdout=log, stderr=subprocess.STDOUT)
res = base + ".samples_eval_results.json"
evalplus_io.import_(base + ".rows.jsonl", a.suite, base + ".samples.jsonl", res, base + ".scored.all.jsonl")
sc = read_jsonl(base + ".scored.all.jsonl")
report = {"transform": a.transform, "kind": kind, "suite": a.suite, "input_rows": len(rows), "transformed": len(sc), "not_applicable": skipped}
if kind == "mutate":
    kept = [r for r in sc if not r["hidden_passed"]]
    report.update(kept=len(kept), dropped_as_possibly_equivalent=len(sc) - len(kept), bug_class=CODE_TRANSFORMS[a.transform][2])
    out = kept
else:
    changed = [(r["task"], r["orig_tier"], r["orig_hidden_passed"], r["hidden_passed"]) for r in sc if r["hidden_passed"] != r["orig_hidden_passed"]]
    report.update(verdict_changes=len(changed), changed=changed[:30], ok=not changed)
    out = sc
with open(base + ".scored.jsonl", "w") as f: f.writelines(json.dumps(r) + "\n" for r in out)
json.dump(report, open(base + ".check.json", "w"), indent=1)
print(json.dumps({k: v for k, v in report.items() if k != "changed"}))
if kind != "mutate" and changed: sys.exit(1)

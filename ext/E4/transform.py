#!/usr/bin/env python3
"""E4 input: the T18 semantics-preserving rewrites of every local3b draft in IN (E3's task subset), each re-scored with
the official evaluator in the network-less container. Any verdict change stops the run: it is a bug in the transform.
  python3 ext/E4/transform.py IN OUT WORKDIR
OUT = every row of IN plus one row per rewritten draft (tier local3b+<transform>, orig_code, code_unchanged)."""
import json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import evalplus_io, suites
from jsonl import read_jsonl
from variants.codemods import apply_rows

TRANSFORMS = ("strip_comments", "reformat", "rename_locals", "verbose_comments", "reorder_helpers")
inp, out, wd = sys.argv[1:4]; os.makedirs(wd, exist_ok=True)
rows = [r for r in read_jsonl(inp) if "_meta" not in r]
base = [r for r in rows if r["tier"] == "local3b" and r.get("hidden_passed") is not None]
orig = {(r["task"], r["rep"]): r for r in base}
new, report, bad = [], {}, 0
for name in TRANSFORMS:
    for suite in sorted({r["suite"] for r in base}):
        src = [r for r in base if r["suite"] == suite]
        mod, skipped = apply_rows(src, name, 1)
        b = os.path.join(wd, f"{name}.{suite}")
        for r in mod:
            o = orig[(r["task"], r["rep"])]; r["orig_code"] = o["code"]; r["code_unchanged"] = r["code"] == o["code"]
        with open(b + ".rows.jsonl", "w") as f: f.writelines(json.dumps(r) + "\n" for r in mod)
        for stale in (b + ".samples_eval_results.json", b + ".scored.jsonl"):   # evalplus reuses an old results file
            if os.path.exists(stale): os.remove(stale)
        evalplus_io.export(b + ".rows.jsonl", suite, b + ".samples.jsonl")
        d, s = os.path.abspath(wd), os.path.basename(b) + ".samples.jsonl"
        cmd = ["docker", "run", "--rm", "--network", "none", "--memory", "6g", "-e", "EVALPLUS_MAX_MEMORY_BYTES=8589934592", "-v", f"{d}:/app",
               "-v", "evalplus-cache:/root/.cache/evalplus", "evalplus:0.3.1", "evalplus.evaluate", "--dataset", suites.EVALPLUS_NAME[suite],
               "--samples", f"/app/{s}", "--parallel", "1"]
        with open(b + ".evalplus.log", "w") as log: subprocess.run(cmd, check=True, stdout=log, stderr=subprocess.STDOUT)
        evalplus_io.import_(b + ".rows.jsonl", suite, b + ".samples.jsonl", b + ".samples_eval_results.json", b + ".scored.jsonl")
        sc = read_jsonl(b + ".scored.jsonl")
        changed = [(r["task"], r["rep"]) for r in sc if r["hidden_passed"] != r["orig_hidden_passed"]]
        vis = sum(r["visible_passed"] != orig[(r["task"], r["rep"])].get("visible_passed") for r in sc)
        report[f"{name}|{suite}"] = dict(input=len(src), transformed=len(sc), not_applicable=skipped,
                                         code_unchanged=sum(r["code_unchanged"] for r in sc), verdict_changes=len(changed),
                                         visible_changes=vis, changed=changed[:30])
        print(name, suite, {k: v for k, v in report[f"{name}|{suite}"].items() if k != "changed"}, flush=True)
        bad += len(changed) + vis; new += sc
with open(out, "w") as f: f.writelines(json.dumps(r) + "\n" for r in rows + new)
json.dump(report, open(os.path.join(wd, "check.json"), "w"), indent=1)
print(f"{len(new)} rewritten drafts -> {out}; verdict changes {bad}")
sys.exit(1 if bad else 0)

#!/usr/bin/env python3
"""E5 input: the T18 bug mutators applied to every hidden-correct local3b draft in IN (E3's task subset), each mutant
scored with the official evaluator in the network-less container. A mutant is kept only if it now fails the hidden
tests (possibly-equivalent mutants are dropped and counted).
  python3 ext/E5/mutate.py IN OUT WORKDIR
OUT = every row of IN plus one row per kept mutant (tier local3b+<mutator>, bug_class, orig_code)."""
import json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import evalplus_io, suites
from jsonl import read_jsonl
from variants.codemods import apply_rows

MUTATORS = ("off_by_one", "flip_comparison", "swap_args", "wrong_init", "drop_guard", "early_exit")
inp, out, wd = sys.argv[1:4]; os.makedirs(wd, exist_ok=True)
rows = [r for r in read_jsonl(inp) if "_meta" not in r]
base = [r for r in rows if r["tier"] == "local3b" and r.get("hidden_passed")]
orig = {(r["task"], r["rep"]): r for r in base}
new, report = [], {}
for name in MUTATORS:
    for suite in sorted({r["suite"] for r in base}):
        src = [r for r in base if r["suite"] == suite]
        mod, skipped = apply_rows(src, name, 1)
        b = os.path.join(wd, f"{name}.{suite}")
        for r in mod: r["orig_code"] = orig[(r["task"], r["rep"])]["code"]
        with open(b + ".rows.jsonl", "w") as f: f.writelines(json.dumps(r) + "\n" for r in mod)
        for stale in (b + ".samples_eval_results.json", b + ".scored.jsonl"):   # evalplus reuses an old results file
            if os.path.exists(stale): os.remove(stale)
        if mod:
            evalplus_io.export(b + ".rows.jsonl", suite, b + ".samples.jsonl")
            d, s = os.path.abspath(wd), os.path.basename(b) + ".samples.jsonl"
            cmd = ["docker", "run", "--rm", "--network", "none", "--memory", "6g", "-e", "EVALPLUS_MAX_MEMORY_BYTES=8589934592", "-v", f"{d}:/app",
                   "-v", "evalplus-cache:/root/.cache/evalplus", "evalplus:0.3.1", "evalplus.evaluate", "--dataset", suites.EVALPLUS_NAME[suite],
                   "--samples", f"/app/{s}", "--parallel", "1"]
            with open(b + ".evalplus.log", "w") as log: subprocess.run(cmd, check=True, stdout=log, stderr=subprocess.STDOUT)
            evalplus_io.import_(b + ".rows.jsonl", suite, b + ".samples.jsonl", b + ".samples_eval_results.json", b + ".scored.jsonl")
            sc = read_jsonl(b + ".scored.jsonl")
        else:
            sc = []
        kept = [r for r in sc if not r["hidden_passed"]]
        report[f"{name}|{suite}"] = dict(input=len(src), mutated=len(sc), not_applicable=skipped, kept=len(kept),
                                         dropped_as_possibly_equivalent=len(sc) - len(kept),
                                         kept_visible_fail=sum(not r["visible_passed"] for r in kept))
        print(name, suite, report[f"{name}|{suite}"], flush=True)
        new += kept
with open(out, "w") as f: f.writelines(json.dumps(r) + "\n" for r in rows + new)
json.dump(report, open(os.path.join(wd, "check.json"), "w"), indent=1)
print(f"{len(new)} kept mutants -> {out}")

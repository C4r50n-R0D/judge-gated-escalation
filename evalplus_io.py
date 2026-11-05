#!/usr/bin/env python3
"""Score EvalPlus rows with the OFFICIAL evaluator, then copy the verdicts back into our rows.

  python evalplus_io.py export rows.jsonl humaneval+ runs/eval/he_cal.jsonl --split cal
  docker run ... evalplus.evaluate --dataset humaneval --samples /app/he_cal.jsonl            # official scorer (evalplus 0.3.1)
  python evalplus_io.py import rows.jsonl humaneval+ runs/eval/he_cal.jsonl runs/eval/he_cal_eval_results.json scored.jsonl --split cal
  python evalplus_io.py selfcheck-rows humaneval+ runs/selfcheck_he.jsonl     # real-data check of the bridge (see KICKOFF.md)
  python evalplus_io.py selfcheck-verify runs/selfcheck_he.scored.jsonl

--split cal|test|all chooses which rows are exported and imported (default all). Scoring the test split must be
BLIND: evalplus.evaluate prints pass@k over the whole file, so for test-split files send its stdout to /dev/null
(the README commands do this). Nothing else here prints outcomes.

Why the official scorer: HumanEval+/MBPP+ use per-task oracles, float tolerances and time limits; a home-made
re-implementation would be a threat to validity. It executes model code, so run it in the network-less container
with only the samples directory mounted.

The solution sent for scoring is the problem's context prefix (imports and helper functions that precede the
entry point in the prompt) followed by the model's code.
evalplus.evaluate requires a sample for EVERY problem in the dataset; export adds a placeholder for each problem
with no exported rows, and import ignores placeholders. Mapping: evalplus orders results per task by position in
the samples file and echoes the solution text; import checks both and refuses on any mismatch.
"""
import json, sys, argparse
import suites
from jsonl import read_jsonl

PLACEHOLDER = "def __placeholder__():\n    pass\n"

def solution_for(row, task):
    return task.get("context_prefix", "") + (row.get("code") or "")

def _selected(r, tasks, split):
    return ("_meta" not in r and r.get("task") in tasks and r.get("code") is not None and not r.get("error")
            and (split == "all" or r.get("split") == split))

def base_ids(suite, tasks):
    """Every problem id of the EvalPlus dataset behind `suite` (a variant suite is scored on its base dataset)."""
    if suite.startswith("variant:"):
        return [t["id"] for t in suites.load(next(iter(tasks.values()))["base_suite"])] if tasks else []
    return list(tasks)

def export(rows_path, suite, out_path, split="all"):
    tasks = {t["id"]: t for t in suites.load(suite)}
    rows = [r for r in read_jsonl(rows_path) if _selected(r, tasks, split)]
    seen = set()
    with open(out_path, "w") as f:
        for r in rows:
            f.write(json.dumps({"task_id": r["task"], "solution": solution_for(r, tasks[r["task"]])}) + "\n"); seen.add(r["task"])
        ids = base_ids(suite, tasks)
        for tid in ids:
            if tid not in seen: f.write(json.dumps({"task_id": tid, "solution": PLACEHOLDER}) + "\n")
    print(f"exported {len(rows)} samples (split={split}; {len(ids) - len(seen)} placeholder problems) -> {out_path}")

def import_(rows_path, suite, samples_path, results_path, out_path, split="all"):
    tasks = {t["id"]: t for t in suites.load(suite)}
    samples = read_jsonl(samples_path)
    res = json.load(open(results_path))["eval"]
    pos = {}; verdict = {}
    for s in samples:
        k = pos.get(s["task_id"], 0); pos[s["task_id"]] = k + 1
        if s["solution"] == PLACEHOLDER: continue
        e = res[s["task_id"]][k]
        if e["solution"] != s["solution"]: raise SystemExit(f"mismatch at {s['task_id']}#{k}: results do not belong to this samples file")
        verdict.setdefault(s["task_id"], []).append((e["base_status"] == "pass", e["base_status"] == "pass" and e["plus_status"] == "pass", s["solution"]))
    used = {}; n = 0
    rows = read_jsonl(rows_path)
    for r in rows:
        if _selected(r, tasks, split):
            k = used.get(r["task"], 0); used[r["task"]] = k + 1
            try: vis, hid, sol = verdict[r["task"]][k]
            except (KeyError, IndexError): raise SystemExit(f"no verdict for {r['task']} draw #{k}: rows changed since export? re-export and re-score")
            if sol != solution_for(r, tasks[r["task"]]): raise SystemExit(f"row {r['task']} draw #{k} does not match the exported sample")
            r["visible_passed"], r["hidden_passed"], r["scored_by"] = vis, hid, "evalplus-0.3.1"; n += 1
    extra = sum(len(v) for v in verdict.values()) - n
    if extra: raise SystemExit(f"{extra} scored samples have no matching row: wrong rows file or split?")
    with open(out_path, "w") as out:
        for r in rows: out.write(json.dumps(r) + "\n")
    print(f"scored {n} rows (split={split}) -> {out_path}")

def selfcheck_rows(suite, out_path):
    """Real-data check of the whole scoring bridge, before any model runs. For every problem write two fake 'draws':
    tier 'reference' = the canonical solution with the context prefix stripped (exactly what a model returning only
    the entry function would produce), and tier 'stub' = a function returning None. After export -> evalplus ->
    import, every reference row must be hidden-correct and every stub row must fail. Uses all splits, but only
    canonical and stub code, so no model outcome is revealed."""
    n = 0
    with open(out_path, "w") as f:
        for t in suites.load(suite):
            ref = t["reference"]; pre = t.get("context_prefix", "")
            code = ref[len(pre):] if pre and ref.startswith(pre) else ref
            for tier, c in (("reference", code), ("stub", f"def {t['entry']}(*args, **kwargs):\n    return None\n")):
                f.write(json.dumps(dict(tier=tier, model=tier, suite=suite, task=t["id"], split=t["split"], rep=0, code=c, error=None)) + "\n"); n += 1
    print(f"wrote {n} selfcheck rows -> {out_path}")

# Canonical solutions that fail the official evaluator on this setup; kept in the data by Carson's T3 decision
# (HumanEval/32: an EvalPlus find_zero bug; Mbpp/255: reference near its time limit). Reported, not failed on.
KNOWN_ALWAYS_FAIL = {"HumanEval/32", "Mbpp/255"}

def selfcheck_verify(scored_path, allow_known=False):
    rows = [r for r in read_jsonl(scored_path) if r.get("tier") in ("reference", "stub")]
    known = sorted({r["task"] for r in rows if r["tier"] == "reference" and not r.get("hidden_passed") and r["task"] in KNOWN_ALWAYS_FAIL}) if allow_known else []
    ref_fail = [r["task"] for r in rows if r["tier"] == "reference" and not r.get("hidden_passed") and r["task"] not in known]
    stub_pass = [r["task"] for r in rows if r["tier"] == "stub" and r.get("hidden_passed")]
    unscored = [r["task"] for r in rows if r.get("hidden_passed") is None]
    print(f"{len(rows)} rows: reference failures {len(ref_fail)}, stub passes {len(stub_pass)}, unscored {len(unscored)}"
          + (f", known always-fail {known}" if known else ""))
    for name, xs in (("reference failures", ref_fail), ("stub passes", stub_pass), ("unscored", unscored)):
        if xs: print(f"  {name}: {xs[:20]}")
    if ref_fail or stub_pass or unscored: raise SystemExit("SELFCHECK FAILED: investigate before any model run (see KICKOFF.md)")
    print("SELFCHECK OK: the scoring bridge reproduces canonical correctness on real data")

if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "selfcheck-rows": selfcheck_rows(sys.argv[2], sys.argv[3]); sys.exit(0)
    if len(sys.argv) >= 2 and sys.argv[1] == "selfcheck-verify": selfcheck_verify(sys.argv[2], "--allow-known" in sys.argv); sys.exit(0)
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=["export", "import"]); ap.add_argument("args", nargs="+")
    ap.add_argument("--split", default="all", choices=["all", "cal", "test"]); a = ap.parse_args()
    if a.cmd == "export" and len(a.args) == 3: export(*a.args, split=a.split)
    elif a.cmd == "import" and len(a.args) == 5: import_(*a.args, split=a.split)
    else: print(__doc__)

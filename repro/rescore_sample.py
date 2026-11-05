#!/usr/bin/env python3
"""Export a random sample of stored draws for the official evaluator (--export), then compare its verdicts (--compare)."""
import collections, json, os, random, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT); os.chdir(ROOT)
import suites, evalplus_io as io
mode, V, n = sys.argv[1], sys.argv[2], int(sys.argv[3]); ds = {"humaneval+": "he", "mbpp+": "mb"}
rows = [r for r in map(json.loads, open("runs/confirmatory.labeled.jsonl")) if "_meta" not in r]
samp = random.Random(551).sample(rows, n)
agree = collections.Counter(); dis = []
for su, tag in ds.items():
    tasks = {t["id"]: t for t in suites.load(su)}
    if mode == "--export":
        seen = set()
        with open(f"{V}/{tag}.jsonl", "w") as f:
            for r in samp:
                if r["suite"] == su: f.write(json.dumps({"task_id": r["task"], "solution": io.solution_for(r, tasks[r["task"]])}) + "\n"); seen.add(r["task"])
            for t in tasks:
                if t not in seen: f.write(json.dumps({"task_id": t, "solution": io.PLACEHOLDER}) + "\n")
    else:
        res = json.load(open(f"{V}/{tag}_eval_results.json"))["eval"]; pos = collections.Counter()
        for r in samp:
            if r["suite"] != su: continue
            e = res[r["task"]][pos[r["task"]]]; pos[r["task"]] += 1
            v = e["base_status"] == "pass"; h = v and e["plus_status"] == "pass"
            ok = v == r["visible_passed"] and h == r["hidden_passed"]; agree["match" if ok else "differ"] += 1
            if not ok: dis.append((r["task"], r["tier"], r["rep"]))
if mode != "--export": print(dict(agree), dis[:20])

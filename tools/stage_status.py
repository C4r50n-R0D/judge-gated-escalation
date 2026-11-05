#!/usr/bin/env python3
"""Planned vs collected draws for one split, without looking at any outcome.
  python3 tools/stage_status.py RUN.jsonl config.json cal|test [--missing]
Prints per-tier planned, done (no error), errored and missing counts; with --missing prints only the missing total."""
import collections, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import bench, suites
from jsonl import read_jsonl
path, cfg_path, split = sys.argv[1:4]
cfg = bench.load_config(cfg_path); tasks = bench.select_tasks(cfg, split=split)
done, err = set(), collections.Counter()
for r in read_jsonl(path) if os.path.exists(path) else []:
    if "_meta" in r: continue
    k = (r["tier"], r["task"], r["rep"])
    if r.get("error"): err[k] += 1
    else: done.add(k)
tot_missing = 0; lines = []
for t in cfg["tiers"]:
    if t.get("role", "generator") != "generator": continue
    plan = [(t["name"], x["id"], rep) for x in tasks for rep in range(t.get("draws", 1))
            if not (t.get("subset_fraction") is not None and suites.subset_hash(x["id"]) >= t["subset_fraction"])]
    d = sum(k in done for k in plan); e = sum(1 for k in plan if k not in done and err[k]); m = len(plan) - d
    tot_missing += m; lines.append(f"{t['name']:10s} planned {len(plan):5d} done {d:5d} errored {e:4d} missing {m:5d}")
if "--missing" in sys.argv: print(tot_missing)
else: print("\n".join(lines))

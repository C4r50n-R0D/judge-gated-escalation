#!/usr/bin/env python3
"""Exploratory (PREREG section 11): does a judge rate hidden-correct code higher when a stronger model wrote it?
  python style_bias.py labeled.jsonl --judge haiku [--split cal|test]  (test only after thresholds are committed)
Uses only drafts that pass hidden tests, so differences reflect style, not correctness. Requires the drafts of
each tier to have been judged (judge_label.py --tiers mac,homelab3b,claude). Task-cluster bootstrap CIs."""
import json, argparse, random
from collections import defaultdict
import controllers as C
ap = argparse.ArgumentParser(); ap.add_argument("path"); ap.add_argument("--judge", required=True); ap.add_argument("--split", default="cal"); ap.add_argument("--thresholds", default="thresholds.json")
ap.add_argument("--boots", type=int, default=2000); a = ap.parse_args()
import os
if a.split == "test" and not os.path.exists(a.thresholds): raise SystemExit("test split only after thresholds.json is committed (PREREG)")
from jsonl import read_jsonl
rows = [r for r in read_jsonl(a.path) if "_meta" not in r and r.get("hidden_passed") and (r.get("judges") or {}).get(a.judge) and r.get("split") == a.split]
by = defaultdict(lambda: defaultdict(list))
for r in rows: by[r["tier"]][r["task"]].append(r["judges"][a.judge]["p"])
tiers = sorted(by)
common = sorted(set.intersection(*(set(by[t]) for t in tiers))) if tiers else []
print(f"judge {a.judge}, split {a.split}: tiers {tiers}, tasks where every tier has a correct judged draft: {len(common)}")
if len(common) < 5: raise SystemExit("too few common tasks for a comparison")
mean_t = {t: {k: sum(v) / len(v) for k, v in by[t].items()} for t in tiers}
idx = C.boot_idx(len(common), a.boots, 11)
for t in tiers:
    vals = [mean_t[t][k] for k in common]; m, lo, hi = C.mean_ci(vals, idx)
    print(f"  {t:10s} mean judge p on correct code {m:.3f} [{lo:.3f}, {hi:.3f}]")
for i, t1 in enumerate(tiers):
    for t2 in tiers[i + 1:]:
        d = [mean_t[t1][k] - mean_t[t2][k] for k in common]; m, lo, hi = C.mean_ci(d, idx)
        print(f"  {t1} - {t2}: {m:+.3f} [{lo:+.3f}, {hi:+.3f}]")

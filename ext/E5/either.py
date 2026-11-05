#!/usr/bin/env python3
"""E5 unplanned descriptive check: share of test-split mutants caught by visible tests, tev, or either.  python3 ext/E5/either.py"""
import json
TH = json.load(open("thresholds.json"))["taus"]
rows = [r for r in map(json.loads, open("runs/E5.j02.jsonl")) if "_meta" not in r and r.get("bug_class") and r["split"] == "test"]
n = len(rows); vis = sum(not r["visible_passed"] for r in rows)
tev = sum(r["judges"]["tev"]["p"] < TH["tev"] for r in rows)
either = sum((not r["visible_passed"]) or r["judges"]["tev"]["p"] < TH["tev"] for r in rows)
vis_miss = [r for r in rows if r["visible_passed"]]
print(f"test mutants {n}: visible catch {vis/n:.3f}, tev {tev/n:.3f}, either {either/n:.3f}; tev catches {sum(r['judges']['tev']['p'] < TH['tev'] for r in vis_miss)} of {len(vis_miss)} visible-passing mutants")

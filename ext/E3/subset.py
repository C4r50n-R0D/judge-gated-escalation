#!/usr/bin/env python3
"""E3 input: every row of N_TEST randomly chosen test tasks and N_CAL calibration tasks (seeded; all tiers, so
judge->reroute can be simulated).  python3 ext/E3/subset.py IN OUT N_TEST N_CAL SEED"""
import json, random, sys
inp, out, nt, nc, seed = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
rows = [json.loads(l) for l in open(inp)]
pick = lambda s, n: set(random.Random(f"{seed}|{s}").sample(sorted({r["task"] for r in rows if r.get("split") == s and "_meta" not in r}), n))
keep = pick("test", nt) | pick("cal", nc)
with open(out, "w") as f:
    for r in rows:
        if "_meta" not in r and r["task"] in keep: f.write(json.dumps(r) + "\n")
print(f"{len(keep)} tasks -> {out}")

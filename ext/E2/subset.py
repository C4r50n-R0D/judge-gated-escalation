#!/usr/bin/env python3
"""Pilot input: rows of the first N calibration tasks (sorted ids), all tiers.  python3 ext/E2/subset.py IN OUT N"""
import json, sys
inp, out, n = sys.argv[1], sys.argv[2], int(sys.argv[3])
rows = [json.loads(l) for l in open(inp)]
keep = set(sorted({r["task"] for r in rows if r.get("split") == "cal" and "_meta" not in r})[:n])
with open(out, "w") as f:
    for r in rows:
        if "_meta" not in r and r["task"] in keep: f.write(json.dumps(r) + "\n")

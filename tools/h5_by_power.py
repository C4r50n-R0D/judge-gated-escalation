#!/usr/bin/env python3
"""H5 sensitivity (PREREG v2 section 8): seconds per draft, split by the Mac's power source at generation time.
  python3 tools/h5_by_power.py RUN.hw.jsonl [--split cal|test]
RUN.hw.jsonl is a labeled run joined with the Mac hardware log (tools/hwjoin.py). Descriptive only; it reads no
outcome. The test split is refused until thresholds.json is committed (blindness rule)."""
import argparse, collections, os, statistics as st, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from jsonl import read_jsonl

ap = argparse.ArgumentParser(); ap.add_argument("path"); ap.add_argument("--split", default="cal", choices=["cal", "test"]); a = ap.parse_args()
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if a.split == "test" and subprocess.run(["git", "ls-files", "--error-unmatch", "thresholds.json"], cwd=root, capture_output=True).returncode != 0:
    raise SystemExit("thresholds.json is not committed: test-split rows stay closed (CLAUDE.md rule 1)")
rows = [r for r in read_jsonl(a.path) if "_meta" not in r and r.get("split") == a.split]
power = lambda r: (r.get("hw") or {}).get("power") or "unknown"
print(f"split {a.split}: {len(rows)} draws; by power source {dict(collections.Counter(power(r) for r in rows))}")
print(f"{'tier':10s} {'power':14s} {'n':>5s} {'s/draft mean':>13s} {'median':>8s}")
for t in sorted({r["tier"] for r in rows}):
    for p in sorted({power(r) for r in rows}):
        x = [r.get("wall_s_net", r.get("wall_s")) for r in rows if r["tier"] == t and power(r) == p]
        if x: print(f"{t:10s} {p:14s} {len(x):5d} {st.mean(x):13.2f} {st.median(x):8.2f}")
# Judge labels are not split: they run in a later pass, so a draw's power state is not the state its label ran under.

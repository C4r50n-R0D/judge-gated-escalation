#!/usr/bin/env python3
"""Attach the Mac's power and thermal state to each draw by time (PREREG section 3).
  python3 tools/hwjoin.py draws.jsonl runs/hwlog_mac.jsonl out.jsonl
Each draw (and each batch record) gets "hw": the latest Mac log entry at or before its timestamp, or null if none.
Prints counts per power source and per warning level, so a run on battery or under throttling is visible."""
import bisect, collections, json, sys
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.dirname(__import__("os").path.abspath(__file__))))
from jsonl import read_jsonl

def join(rows, log):
    log = sorted(log, key=lambda e: e["ts"]); keys = [e["ts"] for e in log]
    def at(ts):
        i = bisect.bisect_right(keys, (ts or "")[:19] + "Z") - 1   # draws carry microseconds; the log has seconds
        return log[i] if i >= 0 else None
    for r in rows:
        if "_meta" in r and "batch" in r["_meta"]: r["_meta"]["batch"]["hw"] = at(r["_meta"]["batch"]["ts"])
        elif "_meta" not in r and r.get("ts"): r["hw"] = at(r["ts"])
    return rows

if __name__ == "__main__":
    rows = join(read_jsonl(sys.argv[1]), read_jsonl(sys.argv[2]))
    with open(sys.argv[3], "w") as f: f.writelines(json.dumps(r) + "\n" for r in rows)
    c = collections.Counter((r["hw"] or {}).get("power") if r.get("hw") else None for r in rows if "_meta" not in r)
    w = collections.Counter(((r.get("hw") or {}).get("thermal_warning"), (r.get("hw") or {}).get("performance_warning")) for r in rows if "_meta" not in r)
    print("draws by power source:", dict(c)); print("draws by (thermal, performance) warning:", dict(w))

#!/usr/bin/env python3
"""T13 timing noise floor (KICKOFF2): compare per-draft seconds across repeated runs of the same calibration tasks.
  python3 tools/t13_timing.py runs/t13 cold1 cold2 warm1 warm2
Reads <dir>/<run>.hw.jsonl (bench output joined with the Mac hardware log). Calibration rows only."""
import json, os, statistics as st, sys

d, runs = sys.argv[1], sys.argv[2:]
data = {}
for r in runs:
    rows = [json.loads(l) for l in open(os.path.join(d, f"{r}.hw.jsonl"))]
    batches = [x["_meta"]["batch"] for x in rows if "batch" in x.get("_meta", {})]
    rows = [x for x in rows if "_meta" not in x]
    assert all(x["split"] == "cal" for x in rows), "non-calibration rows in a timing run"
    data[r] = rows
    for tier in sorted({x["tier"] for x in rows}):
        ok = [x for x in rows if x["tier"] == tier and not x.get("error")]
        w = [x["wall_s_net"] for x in ok]; raw = [x["wall_s"] for x in ok]
        tps = [x["decode_tps"] for x in ok if x.get("decode_tps")]; tok = [x["tokens_out"] for x in ok]
        ld = [x.get("load_s") or 0 for x in ok]
        print(f"{r:6s} {tier:9s} n={len(ok)} errors={sum(1 for x in rows if x['tier'] == tier and x.get('error'))} "
              f"s/draft {st.mean(w):.2f} (sd {st.stdev(w):.2f}, raw {st.mean(raw):.2f}) decode tok/s {st.mean(tps):.1f} (sd {st.stdev(tps):.2f}) "
              f"tokens_out {st.mean(tok):.0f} max load_s {max(ld):.2f}")
    print(f"{r:6s} batches {len(batches)}")

key = lambda x: (x["tier"], x["task"], x["rep"])
base = {key(x): x for x in data[runs[0]]}
for r in runs[1:]:
    same = [x for x in data[r] if key(x) in base and base[key(x)]["code"] == x["code"]]
    print(f"\n{r} vs {runs[0]}: identical code in {len(same)}/{len(data[r])} draws")
    for tier in sorted({x["tier"] for x in same}):
        rat = [x["wall_s_net"] / base[key(x)]["wall_s_net"] for x in same if x["tier"] == tier and base[key(x)]["wall_s_net"] > 0.3]
        tr = [x["decode_tps"] / base[key(x)]["decode_tps"] for x in same if x["tier"] == tier and x.get("decode_tps") and base[key(x)].get("decode_tps")]
        q = st.quantiles(rat, n=4)
        print(f"   {tier}: per-draft time ratio median {st.median(rat):.3f} (IQR {q[0]:.3f} to {q[2]:.3f}); decode tok/s ratio median {st.median(tr):.3f}")

# drift within a run: first vs last third of each tier's draws, by decode speed
print()
for r in runs:
    for tier in sorted({x["tier"] for x in data[r]}):
        tps = [x["decode_tps"] for x in sorted(data[r], key=lambda x: x["ts"]) if x["tier"] == tier and x.get("decode_tps")]
        k = len(tps) // 3
        print(f"{r:6s} {tier:9s} decode tok/s first third {st.mean(tps[:k]):.2f}, last third {st.mean(tps[-k:]):.2f}")

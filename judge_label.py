#!/usr/bin/env python3
"""Add one judge's probabilities to draws produced by bench.py. Run once per judge; results accumulate in r["judges"].
  python judge_label.py in.jsonl config.json JUDGE out.jsonl [--tiers mac] [--max-rep 5]

- Only draws from the listed tiers (default: local generator tiers) with rep < --max-rep are judged.
- Labels are cached per judge in <judge_cache_dir>/<JUDGE>.jsonl (relative to the config file), keyed by (judge config hash, task, code), independent of
  the output file: rerunning, resuming, or writing a different output never pays twice, and changing a judge's
  settings (model, prompt) never reuses old labels.
- Empty code gets p = 0 without calling the judge (recorded as 'empty'). A draft left unjudged (error)
  is treated by controllers.py as a REJECTION, which is what a deployed system would do; counts are reported.
- Prints only counts, never outcomes."""
import os, json, hashlib, argparse
from judge import make
import suites, bench
from jsonl import read_jsonl, open_append, resolve
ap = argparse.ArgumentParser(); ap.add_argument("inp"); ap.add_argument("config"); ap.add_argument("judge"); ap.add_argument("out")
ap.add_argument("--tiers", default=""); ap.add_argument("--max-rep", type=int, default=10**9); a = ap.parse_args()
cfg = bench.load_config(a.config); j = make(a.judge, cfg)
want = set(x for x in a.tiers.split(",") if x) or {t["name"] for t in cfg["tiers"] if t.get("role", "generator") == "generator" and t["kind"] == "ollama"}
# parameter count for the token-compute cost: the judge's own, or its tier's
jcfg = cfg["judges"][a.judge]
params_b = jcfg.get("params_b") or next((t.get("params_b") for t in cfg["tiers"] if t["name"] == jcfg.get("tier")), None)
rows = read_jsonl(a.inp)
T = {t["id"]: t for t in suites.load_many(sorted({r["suite"] for r in rows if "suite" in r}))}
cdir = resolve(cfg, "judge_cache_dir", "judge_cache"); os.makedirs(cdir, exist_ok=True); cpath = os.path.join(cdir, f"{a.judge}.jsonl")
cache = {d["k"]: d["v"] for d in read_jsonl(cpath)} if os.path.exists(cpath) else {}
n = new = errors = empty = unparseable = 0
with open(a.out, "w") as out, open_append(cpath) as cf:
    for r in rows:
        if "_meta" not in r and not r.get("error") and r.get("code") is not None and r["tier"] in want and r["rep"] < a.max_rep:
            if not r["code"].strip():
                r.setdefault("judges", {})[a.judge] = {"p": 0.0, "cost": 0.0, "wall": 0.0, "empty": True}; empty += 1; n += 1
            else:
                # a row-based judge (selfconf) reads the draw itself, so its key names the draw, not just the code
                ident = f"{r['tier']}|{r['rep']}|{r['code']}" if getattr(j, "uses_row", False) else r["code"]
                k = hashlib.sha256(f"{j.hash}|{r['task']}|{ident}".encode()).hexdigest()
                if k not in cache:
                    try:
                        p, c, w, extra = j.p_from_row(r) if getattr(j, "uses_row", False) else j.p_correct(T[r["task"]]["judge_task"], r["code"])
                        cache[k] = [p, c, w, extra]; new += 1
                        cf.write(json.dumps({"k": k, "v": cache[k]}) + "\n"); cf.flush()
                    except Exception as e:
                        errors += 1; print("judge error (draft left unjudged; rerun to retry):", type(e).__name__, str(e)[:150])
                if k in cache:
                    p, c, w, extra = cache[k]
                    r.setdefault("judges", {})[a.judge] = {"p": p, "cost": c, "wall": w, "unparseable_votes": (extra or {}).get("unparseable_votes", 0),
                                                           "tokens": (extra or {}).get("tokens", 0), "params_b": params_b}
                    unparseable += (extra or {}).get("unparseable_votes", 0); n += 1
        out.write(json.dumps(r) + "\n")
print(f"judge {a.judge} [{j.hash}]: labeled {n} draws ({new} new, {empty} empty code), {errors} errors, "
      f"{unparseable} unparseable votes -> {a.out}")

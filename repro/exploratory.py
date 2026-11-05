#!/usr/bin/env python3
"""Rerun the exploratory analyses from the stored labels, using the commands in each ext/E*/spec.json, and compare the
outputs with the committed ones. Stored labels only: no model is called and no model-written code is executed.

Markdown must match byte for byte. JSON must match in structure, with numbers equal to 1e-9. The stored outputs came from
Python 3.13; sum() on floats changed in Python 3.12, so older versions differ in the last digits (at most 1.3e-11 here).
`--compare DIR` skips the runs and compares outputs already in DIR."""
import filecmp, json, math, os, subprocess, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(ROOT)
OUT = "repro_out"; keys = ("judge_eval", "analyze.py", "sim.py", "e14.py", "e14b.py")
args = sys.argv[1:]; replay = args[:1] == ["--compare"]
if replay: OUT = args[1]; args = args[2:]
only = args; rows = []; seen = set()
def close(a, b):
    if isinstance(a, dict): return isinstance(b, dict) and a.keys() == b.keys() and all(close(a[k], b[k]) for k in a)
    if isinstance(a, list): return isinstance(b, list) and len(a) == len(b) and all(map(close, a, b))
    if isinstance(a, float) or isinstance(b, float): return isinstance(a, (int, float)) and isinstance(b, (int, float)) and math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-9)
    return a == b
def verdict(a, b):
    if filecmp.cmp(a, b, shallow=False): return "identical"
    return "equal to 1e-9" if a.endswith(".json") and close(json.load(open(a)), json.load(open(b))) else "DIFFERENT"
def run(e, cmd, dest, ref):
    t = time.time()
    if not replay:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if r.returncode: print(f"{e}: FAILED\n{r.stderr[-600:]}", flush=True); rows.append((e, ref, "failed")); return
    for f in sorted(os.listdir(ref)) if os.path.isdir(ref) else []:
        a, b = os.path.join(ref, f), os.path.join(dest, f)
        if not f.endswith((".md", ".json")) or not os.path.exists(b) or a in seen: continue
        seen.add(a); rows.append((e, f, verdict(a, b)))
        print(f"{e:6s} {f:24s} {rows[-1][2]}  ({time.time() - t:.0f}s)", flush=True)
for e in ("E2", "E3", "E4", "E5", "E6", "E12", "E14", "E14b"):
    if only and e not in only: continue
    for st in json.load(open(f"ext/{e}/spec.json"))["steps"]:
        c = st["cmd"]
        if not any(k in c for k in keys): continue
        ref = next(x for x in c.split() if x.startswith(f"ext/{e}/out"))
        dest = os.path.join(OUT, ref.replace("ext/", "")); os.makedirs(dest, exist_ok=True)
        run(e, c.replace("nice ", "").replace(ref, dest), dest, ref)
if not only or "E6" in only:
    os.makedirs(f"{OUT}/E6/out", exist_ok=True)
    run("E6", f"python3 ext/E6/pooled.py runs/E6.j06.jsonl {OUT}/E6/out", f"{OUT}/E6/out", "ext/E6/out")
n = lambda v: sum(r[2] == v for r in rows)
print(f"\n{n('identical')} identical, {n('equal to 1e-9')} equal to 1e-9, {n('DIFFERENT')} different, {n('failed')} failed")
sys.exit(1 if n("DIFFERENT") or n("failed") else 0)

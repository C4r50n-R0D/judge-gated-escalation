#!/usr/bin/env python3
"""Regenerate a random sample of stored draws and judge labels, then compare them with the stored ones.

  python3 repro/repeat_check.py --draws local3b=12,local1p5b=6,strong14b=3 --labels tev=8,llama=8

Talks only to an Ollama on this machine (OLLAMA_URL, default http://localhost:11434) and refuses anything else, unless
--allow-remote is given. The models must have the digests in ENVIRONMENT.md. Run nothing else on Ollama meanwhile."""
import argparse, json, os, random, sys, urllib.parse, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT); os.chdir(ROOT)
import bench, suites, judge
from jsonl import read_jsonl

ap = argparse.ArgumentParser()
ap.add_argument("--draws", default="local3b=12,local1p5b=6,strong14b=3"); ap.add_argument("--labels", default="tev=8,llama=8")
ap.add_argument("--seed", type=int, default=20261104); ap.add_argument("--allow-remote", action="store_true")
ap.add_argument("--out", default="repro_out/repeat_check.json")
a = ap.parse_args()
url = os.environ.get("OLLAMA_URL", "http://localhost:11434").rstrip("/")
if urllib.parse.urlparse(url).hostname not in ("localhost", "127.0.0.1", "::1") and not a.allow_remote:
    raise SystemExit(f"{url} is not this machine; pass --allow-remote to use it deliberately")
cfg = bench.load_config("config.study.json")
for t in cfg["tiers"]: t["base_url"] = url
for j in cfg["judges"].values():
    if "base_url" in j: j["base_url"] = url
have = {m["name"]: m["digest"][:12] for m in json.load(urllib.request.urlopen(url + "/api/tags"))["models"]}
digests = json.load(open("repro/model_digests.json"))
rows = [r for r in read_jsonl("runs/confirmatory.labeled.jsonl") if "_meta" not in r and not r.get("error")]
T = {t["id"]: t for t in suites.load_many(["humaneval+", "mbpp+"])}
rnd = random.Random(a.seed); res = {"draws": [], "labels": [], "ollama": json.load(urllib.request.urlopen(url + "/api/version"))["version"]}
tiers = {t["name"]: t for t in cfg["tiers"]}
parse = lambda s: {k: int(v) for k, v in (x.split("=") for x in s.split(",") if x)}
for name, n in parse(a.draws).items():
    t = tiers[name]
    if have.get(t["model"]) != digests[t["model"]]: raise SystemExit(f"{t['model']}: digest {have.get(t['model'])} is not the study's {digests[t['model']]}")
    run = bench.tier_run(cfg, t)
    bench.gen_ollama(t, dict(run, num_predict=64, temperature=0.0), bench.PROBE_PROMPT, seed=1)   # discarded, as in bench.py
    for r in rnd.sample([x for x in rows if x["tier"] == name], n):
        g = bench.gen_ollama(t, run, T[r["task"]]["prompt"], seed=(run.get("seed") or 0) + r["rep"])
        code = bench.extract_code(g["text"]); same = code == r["code"]
        res["draws"].append(dict(tier=name, task=r["task"], rep=r["rep"], identical=same, tokens_stored=r["tokens_out"], tokens_now=g["tokens_out"]))
        print(f"{name:10s} {r['task']:14s} rep {r['rep']} {'IDENTICAL' if same else 'DIFFERENT'}", flush=True)
for name, n in parse(a.labels).items():
    j = judge.make(name, cfg)
    for r in rnd.sample([x for x in rows if x["tier"] == "local3b" and (x["code"] or "").strip()], n):
        p = j.p_correct(T[r["task"]]["judge_task"], r["code"])[0]; old = r["judges"][name]["p"]
        res["labels"].append(dict(judge=name, task=r["task"], rep=r["rep"], stored=old, now=p, abs_diff=abs(p - old), same_verdict=(p >= json.load(open("thresholds.json"))["taus"][name]) == (old >= json.load(open("thresholds.json"))["taus"][name])))
        print(f"{name:10s} {r['task']:14s} stored {old:.6f} now {p:.6f}", flush=True)
os.makedirs(os.path.dirname(a.out), exist_ok=True); json.dump(res, open(a.out, "w"), indent=1)
d, l = res["draws"], res["labels"]
print(f"draws identical: {sum(x['identical'] for x in d)} of {len(d)}")
if l: print(f"labels: same verdict {sum(x['same_verdict'] for x in l)} of {len(l)}; largest difference {max(x['abs_diff'] for x in l):.6f}")

#!/usr/bin/env python3
"""Draw generator for the judge-gated escalation study (stdlib only).

  python bench.py validate [suites]                       # own suite: references pass, stubs and exit(0) cheats fail
  python bench.py run config.json out.jsonl [--pilot N] [--split cal|test] [--suites own] [--max-tasks N]

One JSONL row = one generation (tier, task, rep). Runs are RESUMABLE: rows already in out.jsonl without an error
are skipped, so an interrupted overnight batch just restarts. Each tier draws `draws` samples per task at its own
`temperature` (pre-registered in PREREG.md). Tiers with "role": "judge" are not used for generation.

--pilot N  draws only N tasks, chosen at random (fixed seed) from the CALIBRATION split, so the pilot never
           touches test-split tasks.
Scoring: own-suite rows are scored here; EvalPlus rows are scored later by evalplus_io.py (official evaluator).
"""
import json, os, re, subprocess, sys, tempfile, time, urllib.request, urllib.error, platform, datetime, random, argparse, secrets, shlex, signal
import suites
from jsonl import read_jsonl, open_append

SYSTEM = "You are a careful Python programmer. Reply with a single ```python code block containing only the requested code and its imports. No explanation, no tests, no example usage."

def http_json(url, payload=None, headers=None, timeout=300):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json", **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())

def extract_code(text):
    m = re.findall(r"```(?:python|py)?\s*\n(.*?)```", text, re.S)
    return (m[0] if m else text).strip()

_WARNED = False
def _warn_unsandboxed(sandbox):
    global _WARNED
    if sandbox or _WARNED: return
    _WARNED = True
    if os.environ.get("BENCH_ALLOW_UNSANDBOXED") != "1":
        raise SystemExit("refusing to run model-written code on this host: set BENCH_SANDBOX (see README), or "
                         "BENCH_ALLOW_UNSANDBOXED=1 for mock tests only")
    print("WARNING: running test code unsandboxed (BENCH_ALLOW_UNSANDBOXED=1)", file=sys.stderr)

def run_tests(code, tests, timeout=10):
    """Run code + tests in a fresh interpreter. Pass = exit code 0 AND a per-call random sentinel printed after the
    tests, so neither sys.exit(0) nor printing a fixed marker can fake a pass. If BENCH_SANDBOX is set (a command
    that reads a Python program on stdin, e.g. a network-less docker container; see README), the program runs
    there instead of on this host. The whole process group is killed on timeout."""
    nonce = secrets.token_hex(16)
    marker = f"__PASS_{nonce}__"
    src = code + "\n\n" + tests + f"\nprint('{marker}')\n"
    sandbox = os.environ.get("BENCH_SANDBOX")
    _warn_unsandboxed(sandbox)
    with tempfile.TemporaryDirectory() as d:
        # the program goes in on stdin in both modes, so it never exists as a file it could read its sentinel from
        cmd, stdin = (shlex.split(sandbox) if sandbox else [sys.executable, "-I", "-"]), src
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True, cwd=d, start_new_session=True)
        try:
            out, err = proc.communicate(stdin, timeout=timeout + (15 if sandbox else 0))   # allow for container start-up
        except subprocess.TimeoutExpired:
            try: os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError: pass
            proc.communicate(); return False, "timeout"
        ok = proc.returncode == 0 and marker in out
        return ok, (err[-300:] or ("exited before tests completed" if not ok else ""))

def gen_ollama(t, run, prompt, seed=None, system=None):
    t0 = time.perf_counter()
    r = http_json(t["base_url"] + "/api/generate", {
        "model": t["model"], "system": system or SYSTEM, "prompt": prompt, "stream": False, "logprobs": True,
        "options": {"temperature": run["temperature"], "seed": (run.get("seed") or 0) if seed is None else seed, "num_predict": run["num_predict"]}},
        timeout=run["timeout_s"])
    wall = time.perf_counter() - t0
    ev, ed = r.get("eval_count"), r.get("eval_duration")
    pc, pd = r.get("prompt_eval_count"), r.get("prompt_eval_duration")
    lps = [x["logprob"] for x in (r.get("logprobs") or []) if x.get("logprob") is not None]
    return dict(text=r.get("response", ""), wall_s=wall, tokens_out=ev, tokens_in=pc,
                decode_tps=(ev / ed * 1e9) if ev and ed else None,
                prefill_tps=(pc / pd * 1e9) if pc and pd else None,
                load_s=(r.get("load_duration") or 0) / 1e9, cost_usd=0.0,
                # the generator's own confidence over the whole reply (the selfconf baseline gate)
                lp_mean=(sum(lps) / len(lps)) if lps else None, lp_min=min(lps) if lps else None)

GEN = {"ollama": gen_ollama}

def tier_run(cfg, t):
    """Per-tier generation settings: tier values override the global defaults."""
    return {k: t.get(k, cfg.get(k)) for k in ("temperature", "num_predict", "timeout_s", "seed")}

def cmd_validate(suite_names):
    ok = True
    for t in suites.load_many(suite_names):
        if t["scorer"] != "local": continue
        good = run_tests(t["reference"], t["tests"])[0]; hgood = run_tests(t["reference"], t["hidden"])[0]
        stub = f"def {t['entry']}(*a, **k):\n    return None\n"
        bad = run_tests(stub, t["tests"])[0] or run_tests(stub, t["hidden"])[0]
        cheat = run_tests(f"def {t['entry']}(*a, **k):\n    raise SystemExit(0)\n", t["hidden"])[0]
        line_ok = good and hgood and not bad and not cheat
        print(f"{t['id']:14s} {t['split']:4s} {'OK' if line_ok else 'FAIL'} ref_visible={good} ref_hidden={hgood} stub_passes={bad} exit0_passes={cheat}")
        ok &= line_ok
    sys.exit(0 if ok else 1)

MAX_ATTEMPTS = 3   # PREREG section 10: a draw that errors 3 times is excluded and counted

def read_done(path):
    done, errors = set(), {}
    if os.path.exists(path):
        for r in read_jsonl(path):
            if "_meta" in r: continue
            k = (r["tier"], r["task"], r["rep"])
            if r.get("error"): errors[k] = errors.get(k, 0) + 1
            else: done.add(k)
    return done, errors


def load_config(path):
    cfg = json.load(open(path)); cfg["_config_dir"] = os.path.dirname(os.path.abspath(path)); return cfg

def select_tasks(cfg, pilot=None, suite_override=None, max_tasks=None, split=None):
    tasks = suites.load_many(suite_override or cfg["suites"])
    if split: tasks = [t for t in tasks if t["split"] == split]
    if pilot:
        cal = [t for t in tasks if t["split"] == "cal"]
        tasks = random.Random(cfg.get("pilot_seed", 7)).sample(cal, min(pilot, len(cal)))
    return tasks[:max_tasks] if max_tasks else tasks

def blocks(cfg, tasks):
    """Collection order (PREREG section 3): tasks in a fixed seeded random order, cut into blocks of `block_size`.
    Every tier runs through a block before the next block starts (chunked round-robin), so heat and power state are
    spread across tiers without a model swap on every task. The order depends only on the task ids and the seed."""
    order = sorted(tasks, key=lambda t: t["id"])
    random.Random(cfg.get("order_seed", 2026)).shuffle(order)
    n = cfg.get("block_size", 20)
    return [order[i:i + n] for i in range(0, len(order), n)]

GEN_FIELDS = ("name", "kind", "model", "temperature", "num_predict", "role", "seed", "draws")

def gen_signature(cfg):
    """Generation-relevant settings. Resuming into a file made with different settings would mix conditions."""
    return [{k: t.get(k, cfg.get(k)) for k in GEN_FIELDS} for t in cfg["tiers"]] + [suites.SALT, suites.CAL_FRACTION, SYSTEM, suites.PROMPT_WRAP] + \
           [{"block_size": cfg.get("block_size", 20), "order_seed": cfg.get("order_seed", 2026)}]

def check_same_conditions(cfg, out_path):
    if not os.path.exists(out_path): return
    for r in read_jsonl(out_path):
        if "_meta" in r:
            old = r["_meta"].get("gen_signature")
            if old is not None and old != gen_signature(cfg):
                raise SystemExit(f"{out_path} was made with different generation settings; write to a new file instead of mixing conditions")

def now_iso(): return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None).isoformat() + "Z"

PROBE_PROMPT = "Write a Python function that returns the n-th prime, with a docstring and comments."

NETWORK_ERRORS = (urllib.error.URLError, ConnectionError, TimeoutError, OSError)

def is_network_error(e):
    """Connection-level failures (host unreachable, refused, timed out), not an HTTP error from a running model."""
    return isinstance(e, NETWORK_ERRORS) and not isinstance(e, urllib.error.HTTPError)

def with_network_retry(call, out=None, tier="", max_wait_s=7200, sleep=time.sleep):
    """Run call(); on a network failure wait (30 s doubling to 5 min) and retry the SAME draw, for up to max_wait_s.
    a dropped link between the two machines must not turn the remaining draws into error rows. Outages are
    logged as _meta records. Other exceptions propagate and become error rows as before."""
    waited, delay = 0, 30
    while True:
        try:
            r = call()
            if waited and out is not None:
                out.write(json.dumps({"_meta": {"outage": {"tier": tier, "ts": now_iso(), "waited_s": waited}}}) + "\n"); out.flush()
            return r
        except Exception as e:
            if not is_network_error(e) or waited >= max_wait_s: raise
            print(f"  network error ({type(e).__name__}); retrying in {delay}s", flush=True)
            sleep(delay); waited += delay; delay = min(delay * 2, 300)

def throttled(recent, t, cool):
    """True when the median decode speed of the last `window` drafts is below min_ratio x the tier's cold reference
    (`ref_decode_tps` in config). T13 showed heat on the fanless Mac slows decoding by up to 2.4x."""
    ref = t.get("ref_decode_tps")
    if not cool or not ref or len(recent) < cool.get("window", 10): return False
    return sorted(recent)[len(recent) // 2] < cool.get("min_ratio", 0.7) * ref

def cool_down(gen, t, run, cool, sleep=time.sleep):
    """Pause, then probe with a fixed short generation until decode speed recovers or max_wait_s passes.
    Returns (waited_s, last probe tokens/s); the caller logs it. Probe outputs are discarded."""
    waited, tps = 0, None
    while waited < cool.get("max_wait_s", 1800):
        sleep(cool.get("pause_s", 240)); waited += cool.get("pause_s", 240)
        try: tps = gen(t, dict(run, num_predict=64, temperature=0.0), PROBE_PROMPT, seed=1).get("decode_tps")
        except Exception: tps = None
        if tps and tps >= cool.get("min_ratio", 0.7) * t["ref_decode_tps"]: break
    return waited, tps

def cmd_run(cfg_path, out_path, pilot=None, suite_override=None, max_tasks=None, split=None):
    cfg = load_config(cfg_path)
    check_same_conditions(cfg, out_path)
    tasks = select_tasks(cfg, pilot, suite_override, max_tasks, split)
    done, errors = read_done(out_path)
    meta = dict(ts=now_iso(), host=platform.node(),
                py=sys.version.split()[0], cfg=cfg, gen_signature=gen_signature(cfg), pilot=pilot, split=split, n_tasks=len(tasks),
                already_done=len(done))
    gave_up = 0
    gens = [t for t in cfg["tiers"] if t.get("role", "generator") == "generator"]
    cool = cfg.get("cooldown")   # {"min_ratio", "window", "pause_s", "max_wait_s"}; pauses are logged as _meta records
    def maybe_cool(t, run, gen, recent, out, where):
        if not throttled(recent, t, cool): return
        med = sorted(recent)[len(recent) // 2]
        print(f"  throttling: {t['name']} median {med:.1f} tok/s < {cool.get('min_ratio', 0.7)} x {t['ref_decode_tps']}; cooling down", flush=True)
        waited, tps = cool_down(gen, t, run, cool)
        out.write(json.dumps({"_meta": {"cooldown": {"tier": t["name"], "where": where, "ts": now_iso(), "median_tps": med,
                                                      "waited_s": waited, "probe_tps": tps}}}) + "\n"); out.flush()
        recent.clear()
    with open_append(out_path) as out:
        out.write(json.dumps({"_meta": meta}) + "\n")
        for b, block in enumerate(blocks(cfg, tasks)):
            for t in gens:
                draws = t.get("draws", 1); run = tier_run(cfg, t); gen = GEN[t["kind"]]
                todo = [(task, rep) for task in block for rep in range(draws)
                        if not (t.get("subset_fraction") is not None and suites.subset_hash(task["id"]) >= t["subset_fraction"])
                        and (t["name"], task["id"], rep) not in done]
                if not todo: continue
                # one batch = one tier on one block; the record lets the Mac's power and thermal log be joined by time
                out.write(json.dumps({"_meta": {"batch": {"block": b, "tier": t["name"], "ts": now_iso(), "n": len(todo)}}}) + "\n")
                recent = []   # decode speeds of this tier's recent drafts, for the cooldown guard
                if t["kind"] == "ollama":   # warm-up after the model swap, discarded, so the load does not land on a draft
                    try:
                        w = gen(t, dict(run, num_predict=64, temperature=0.0), PROBE_PROMPT, seed=1)
                        if w.get("decode_tps"): recent = [w["decode_tps"]] * (cool or {}).get("window", 10)
                        maybe_cool(t, run, gen, recent, out, "batch start")   # heat left over from the previous tier
                        recent = []
                    except Exception as e: print(f"  warm-up failed for {t['name']}: {e}")
                for task, rep in todo:
                    key = (t["name"], task["id"], rep)
                    if errors.get(key, 0) >= MAX_ATTEMPTS: gave_up += 1; continue
                    row = dict(tier=t["name"], model=t["model"], suite=task["suite"], task=task["id"], split=task["split"], rep=rep,
                               temperature=run["temperature"], params_b=t.get("params_b"), block=b, ts=now_iso())
                    try:
                        g = with_network_retry(lambda: gen(t, run, task["prompt"], seed=(run.get("seed") or 0) + rep), out, t["name"])
                        code = extract_code(g.pop("text"))
                        # seconds cost: wall time minus any model load Ollama reports (a swap that slipped past the warm-up)
                        g["wall_s_net"] = max(0.0, (g.get("wall_s") or 0.0) - (g.get("load_s") or 0.0))
                        row.update(g, code=code, error=None)
                        if task["scorer"] == "local":
                            row["visible_passed"] = run_tests(code, task["tests"])[0]
                            row["hidden_passed"] = run_tests(code, task["hidden"])[0]; row["scored_by"] = "local"
                    except Exception as e:
                        row.update(error=f"{type(e).__name__}: {str(e)[:200]}")
                    out.write(json.dumps(row) + "\n"); out.flush()
                    if row.get("decode_tps") and (row.get("tokens_out") or 0) >= 30:   # short replies give noisy rates
                        recent.append(row["decode_tps"]); del recent[:-(cool or {}).get("window", 10)]
                        maybe_cool(t, run, gen, recent, out, "mid batch")
                    shown = row.get("hidden_passed") if task["split"] == "cal" else "blind"   # never display test-split outcomes
                    print(f"  b{b} {t['name']:9s} {task['id']:16s} rep{rep} wall={row.get('wall_s') or 0:.1f}s hidden={shown} err={row.get('error')}", flush=True)
    print(f"done; draws excluded after {MAX_ATTEMPTS} failed attempts: {gave_up}")

if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "validate":
        cmd_validate(sys.argv[2].split(",") if len(sys.argv) > 2 else ["own"])
    elif len(sys.argv) >= 4 and sys.argv[1] == "run":
        ap = argparse.ArgumentParser(); ap.add_argument("cmd"); ap.add_argument("config"); ap.add_argument("out")
        ap.add_argument("--pilot", type=int); ap.add_argument("--suites"); ap.add_argument("--max-tasks", type=int)
        ap.add_argument("--split", choices=["cal", "test"], help="collect one split only (Stage 1 = cal, Stage 2 = test)")
        a = ap.parse_args()
        cmd_run(a.config, a.out, a.pilot, a.suites.split(",") if a.suites else None, a.max_tasks, a.split)
    else: print(__doc__); sys.exit(2)

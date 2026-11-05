#!/usr/bin/env python3
"""Unit tests: run with `python tests/test_units.py` from the repo root (stdlib only)."""
import json, os, random, sys, tempfile, itertools
os.environ.setdefault("BENCH_ALLOW_UNSANDBOXED", "1")   # unit tests run trivial snippets on the host
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import suites, controllers as C, evalplus_io
from bench import run_tests, extract_code
FIX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "HumanEvalPlus-fixture.jsonl")
fails = []
def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name); (None if cond else fails.append(name))

# split: deterministic, salted, independent of order, roughly CAL_FRACTION
ids = [f"Mbpp/{i}" for i in range(2, 1000)]
s1 = {i: suites.split_of(i) for i in ids}; s2 = {i: suites.split_of(i) for i in reversed(ids)}
check("split deterministic and order-independent", s1 == s2)
frac = sum(v == "cal" for v in s1.values()) / len(s1)
check(f"split fraction near {suites.CAL_FRACTION} (got {frac:.3f})", abs(frac - suites.CAL_FRACTION) < 0.04)

# AUROC vs brute force
rnd = random.Random(1)
for _ in range(20):
    pos = [rnd.choice([0, .2, .4, .6, .8, 1]) for _ in range(rnd.randint(1, 15))]
    neg = [rnd.choice([0, .2, .4, .6, .8, 1]) for _ in range(rnd.randint(1, 15))]
    brute = sum(1 if p > n else .5 if p == n else 0 for p in pos for n in neg) / (len(pos) * len(neg))
    if abs(C.auroc(pos, neg) - brute) > 1e-9: check("auroc matches brute force", False); break
else: check("auroc matches brute force (20 random cases with ties)", True)

# sentinel guard and code extraction
check("exit(0) cheat cannot pass", not run_tests("def f():\n    raise SystemExit(0)\n", "assert f() == 1")[0])
check("os._exit(0) cheat cannot pass", not run_tests("import os\ndef f():\n    os._exit(0)\n", "assert f() == 1")[0])
check("correct code passes", run_tests("def f():\n    return 1\n", "assert f() == 1")[0])
check("printing a fixed marker then exit(0) cannot pass", not run_tests("import sys\nprint('__TESTS_PASSED__'); sys.exit(0)\ndef f(): return 2", "assert f() == 1")[0])
check("timeout kills child processes", run_tests("import subprocess, time\nsubprocess.Popen(['sleep', '30'])\ntime.sleep(30)", "pass", timeout=2) == (False, "timeout"))
from judge import parse_vote
check("vote parser tolerates markdown and case", [parse_vote(x) for x in ["**Yes.**", "no", " NO, because", "Maybe"]] == ["YES", "NO", "NO", None])
check("extract_code picks fenced block", extract_code("hi\n```python\nx=1\n```\nbye") == "x=1")

# controllers: closed-form checks on synthetic draws
def mk(task, tier, rep, ok, vis=None, p=None, cost=0.0, wall=1.0):
    r = dict(task=task, tier=tier, rep=rep, hidden_passed=ok, visible_passed=ok if vis is None else vis, cost_usd=cost, wall_s=wall, split="test")
    if p is not None: r["judges"] = {"j": {"p": p, "cost": 0.001, "wall": 0.5}}
    return r
# task A: local right in 2 of 4 drafts, strong right in 1 of 2 draws
L = [mk("A", "mac", 0, True, p=.9), mk("A", "mac", 1, False, p=.2), mk("A", "mac", 2, True, p=.8), mk("A", "mac", 3, False, p=.7)]
S = [mk("A", "claude", 0, True, cost=.01), mk("A", "claude", 1, False, cost=.01)]
tasks = {"A": {"L": L, "S": S}}
pt = lambda spec: C.per_task(tasks, spec, 20000, 3)["A"]
a = pt(("local-only", None, 1)); check(f"local-only acc 0.5 (got {a[0]:.3f})", abs(a[0] - .5) < .02)
a = pt(("strong-only", None, 1)); check(f"strong-only acc 0.5, cost .01 (got {a[0]:.3f}, {a[1]:.4f})", abs(a[0] - .5) < .02 and abs(a[1] - .01) < 1e-9)
a = pt(("reroute", C.gate("oracle"), 1)); check(f"oracle->reroute acc = .5 + .5*.5 = .75 (got {a[0]:.3f})", abs(a[0] - .75) < .02)
a = pt(("reroute", C.gate("judge", "j", .75), 1))
# accept drafts 0 (right) and 2 (right); reject 1 (wrong) and 3 (wrong) -> reroute: acc = .5*1 + .5*.5 = .75; judge cost .001 always, strong .01 half the time
check(f"judge->reroute acc .75, cost .001+.005 (got {a[0]:.3f}, {a[1]:.4f})", abs(a[0] - .75) < .02 and abs(a[1] - .006) < .0005)
a = pt(("resample", C.gate("judge", "j", .75), 3))
# with tau .75 every accepted draft is right; resample fails only if first 3 of a random order are... at most 2 wrong exist, so 3 draws always include a right one
check(f"judge->resample(3) acc 1.0 here (got {a[0]:.3f})", abs(a[0] - 1.0) < 1e-9)
a = pt(("reroute", C.gate("judge", "j", float("inf")), 1)); check(f"tau=inf is always-reroute (acc .5, got {a[0]:.3f})", abs(a[0] - .5) < .02)
# unjudged drafts count as rejections: drop labels from the two wrong drafts; an accept-all judge must still reroute them
L2 = [dict(d) for d in L]
for d in L2:
    if not d["hidden_passed"]: d.pop("judges")
tasks2 = {"A": {"L": L2, "S": S}}
a2 = C.per_task(tasks2, ("reroute", C.gate("judge", "j", 0.0), 1), 20000, 3)["A"]
check(f"unjudged drafts are rejections, not dropped (acc .75, got {a2[0]:.3f})", abs(a2[0] - .75) < .02)
check("within-task AUROC on task A is 1.0", C.within_task_auroc(tasks, "j", [], 0)["auroc"] == 1.0)

# evalplus loader, prompt wrap, split, export/import round trip with a fake results file
os.environ["HUMANEVAL_PLUS_PATH"] = FIX
T = suites.load("humaneval+")
check("fixture loads 3 problems", len(T) == 3 and all(t["scorer"] == "evalplus" for t in T))
check("context prefix carries prompt imports", T[0]["context_prefix"].startswith("from typing import List"))
helper_prompt = "def poly(xs, x):\n    return sum(c * x ** i for i, c in enumerate(xs))\n\n\ndef find_zero(xs):\n    \"\"\"doc\"\"\"\n"
pre = suites.context_prefix(helper_prompt, "find_zero")
check("context prefix carries helper functions defined before the entry point", "def poly(" in pre and "find_zero" not in pre)
jv = suites.judge_view('"""\nWrite f.\nassert f(1) == 2\n"""\n', "f", "def f(x, y=2):\n    return x\n")
check("judge view strips MBPP asserts but keeps the signature", "assert" not in jv and "== 2" not in jv and "f(x, y=2)" in jv)
from jsonl import open_append, read_jsonl as rj
with tempfile.TemporaryDirectory() as d:
    p = os.path.join(d, "x.jsonl"); open(p, "w").write('{"a": 1}\n{"b": 2')        # truncated last line
    with open_append(p) as f: f.write('{"c": 3}\n')
    check("append after a truncated line keeps the file readable", rj(p) == [{"a": 1}, {"c": 3}])
check("source is not readable from a file (stdin execution)", not run_tests("import re\nprint(re.findall(r'__PASS_[0-9a-f]+__', open(__file__).read())[0])\nraise SystemExit(0)", "pass")[0])
own = {t["id"]: t for t in suites.load("own")}
check("own-suite hidden includes the visible tests", own["palindrome"]["tests"] in own["palindrome"]["hidden"])
check("model prompt wraps problem prompt", "```python" in T[0]["prompt"] and "has_close_elements" in T[0]["prompt"])
with tempfile.TemporaryDirectory() as d:
    rows = os.path.join(d, "rows.jsonl"); samp = os.path.join(d, "s.jsonl"); res = os.path.join(d, "s_eval_results.json"); out = os.path.join(d, "o.jsonl")
    R = [dict(tier="mac", task="HumanEval/1", rep=0, suite="humaneval+", code="def add(x, y):\n    return x + y\n"),
         dict(tier="mac", task="HumanEval/1", rep=1, suite="humaneval+", code="def add(x, y):\n    return x - y\n"),
         dict(tier="claude", task="HumanEval/0", rep=0, suite="humaneval+", code="def has_close_elements(numbers, threshold):\n    return False\n")]
    open(rows, "w").write("".join(json.dumps(r) + "\n" for r in R))
    evalplus_io.export(rows, "humaneval+", samp)
    S_ = [json.loads(l) for l in open(samp)]
    check("export writes placeholder for uncovered problem", sum(s["solution"] == evalplus_io.PLACEHOLDER for s in S_) == 1 and len(S_) == 4)
    check("export prepends prompt imports", S_[2]["solution"].startswith("from typing import List"))
    fake = {"eval": {}}
    verdict = {0: ("pass", "pass"), 1: ("fail", None), 2: ("pass", "fail")}
    for i, s in enumerate(S_):
        if s["solution"] == evalplus_io.PLACEHOLDER: b, pl = "fail", "fail"
        else: b, pl = verdict[i]
        fake["eval"].setdefault(s["task_id"], []).append({"task_id": s["task_id"], "solution": s["solution"], "base_status": b, "plus_status": pl})
    json.dump(fake, open(res, "w"))
    evalplus_io.import_(rows, "humaneval+", samp, res, out)
    O = [json.loads(l) for l in open(out)]
    check("import maps verdicts in order", [(o["visible_passed"], o["hidden_passed"]) for o in O] == [(True, True), (False, False), (True, False)])
    fake["eval"]["HumanEval/1"][0]["solution"] = "tampered"; json.dump(fake, open(res, "w"))
    try: evalplus_io.import_(rows, "humaneval+", samp, res, out); check("import refuses mismatched results", False)
    except SystemExit: check("import refuses mismatched results", True)
with tempfile.TemporaryDirectory() as d:
    sc = os.path.join(d, "sc.jsonl"); evalplus_io.selfcheck_rows("humaneval+", sc)
    R2 = [json.loads(l) for l in open(sc)]
    refrow = next(r for r in R2 if r["tier"] == "reference" and r["task"] == "HumanEval/0")
    rebuilt = evalplus_io.solution_for(refrow, T[0])
    check("selfcheck reference row rebuilds the canonical program exactly", rebuilt == T[0]["reference"])
    for r in R2: r["hidden_passed"] = r["tier"] == "reference"
    open(sc, "w").write("".join(json.dumps(r) + "\n" for r in R2))
    try: evalplus_io.selfcheck_verify(sc); check("selfcheck verify accepts a correct scoring", True)
    except SystemExit: check("selfcheck verify accepts a correct scoring", False)
    R2[0]["hidden_passed"] = False; open(sc, "w").write("".join(json.dumps(r) + "\n" for r in R2))
    try: evalplus_io.selfcheck_verify(sc); check("selfcheck verify rejects a broken scoring", False)
    except SystemExit: check("selfcheck verify rejects a broken scoring", True)
# local judges: P(YES) from log-probabilities, Tev1 answers, the selfconf baseline
import math
from judge import yes_prob, Tev, Jev, SelfConf
lp = lambda pairs: {"logprobs": [{"token": pairs[0][0], "logprob": math.log(pairs[0][1]),
                                  "top_logprobs": [{"token": t, "logprob": math.log(v)} for t, v in pairs]}]}
p, mass = yes_prob(lp([("YES", .6), ("Yes", .1), ("**", .1), ("NO", .2)]))
check(f"P(YES) sums every spelling and renormalises over YES+NO (got {p:.3f}, mass {mass:.2f})", abs(p - .7 / .9) < 1e-9 and abs(mass - .9) < 1e-9)
check("P(YES) is None when neither YES nor NO is among the top tokens", yes_prob(lp([("**", .9), ("The", .1)]))[0] is None)
check("Tev1 answer parses with $0 cost", Tev.parse({"answers": {"is_correct": {"type": "noul", "noul": 0.92}}, "usage": {"input_tokens": 1}}) == (0.92, 0.0))
try: Jev.parse({"answers": {"is_correct": {"noul": 0.9}}, "usage": {}}); check("hosted Jev still refuses a response without usage.cost", False)
except ValueError: check("hosted Jev still refuses a response without usage.cost", True)
check("selfconf = exp(mean log-probability)", abs(SelfConf({}).p_from_row({"lp_mean": -0.5})[0] - math.exp(-0.5)) < 1e-12)

# cost metric: in seconds the cheapest tau accepts more drafts; in USD every local tau costs the same
def mk2(task, tier, rep, ok, p=None, wall=1.0):
    r = dict(task=task, tier=tier, rep=rep, hidden_passed=ok, visible_passed=ok, cost_usd=0.0, wall_s=wall, split="cal")
    if p is not None: r["judges"] = {"j": {"p": p, "cost": 0.0, "wall": 0.2}}
    return r
tasks3 = {f"T{i}": {"L": [mk2(f"T{i}", "local3b", k, ok, p=pp, wall=2.0) for k, (ok, pp) in enumerate([(True, .9), (True, .8), (False, .3)])],
                    "S": [mk2(f"T{i}", "strong14b", k, True, wall=20.0) for k in range(2)]} for i in range(30)}
c = C.choose_tau(tasks3, "j", 0.03, 200, 1, boots=200, cost_metric="sec")
check(f"seconds as cost: picks the feasible tau that skips the slow strong tier (tau {c['tau']}, {c['cost']:.1f} s)", c["tau"] == .8 and c["cost_metric"] == "sec")

# collection order: chunked round-robin blocks, deterministic and independent of input order
import bench
TT = [{"id": f"T{i}"} for i in range(47)]
B1 = bench.blocks({"block_size": 20, "order_seed": 5}, TT); B2 = bench.blocks({"block_size": 20, "order_seed": 5}, list(reversed(TT)))
check("blocks are deterministic and independent of input order", [[t["id"] for t in b] for b in B1] == [[t["id"] for t in b] for b in B2])
check("blocks cover every task once, at most block_size each", sorted(t["id"] for b in B1 for t in b) == sorted(t["id"] for t in TT) and [len(b) for b in B1] == [20, 20, 7])
check("a different order seed gives a different order", [t["id"] for t in B1[0]] != [t["id"] for t in bench.blocks({"block_size": 20, "order_seed": 6}, TT)[0]])
sig = lambda **k: bench.gen_signature(dict({"tiers": []}, **k))
check("block size and order seed are part of the generation signature", sig(block_size=20) != sig(block_size=10) and sig(order_seed=1) != sig(order_seed=2))

# cost accounting: seconds exclude reported model load; token-compute = parameters x tokens
u, sec, tok = C._gen({"cost_usd": 0.0, "wall_s": 12.0, "wall_s_net": 9.5, "params_b": 3.1, "tokens_in": 100, "tokens_out": 50})
check(f"draw cost: seconds use wall_s_net, token-compute = 3.1 x 150 (got {sec}, {tok:.1f})", sec == 9.5 and abs(tok - 465.0) < 1e-9)
check("draw cost: old rows without wall_s_net fall back to wall_s", C._gen({"wall_s": 4.0})[1] == 4.0)
g = C.gate("judge", "j", 0.5)({"judges": {"j": {"p": .9, "cost": 0.0, "wall": 1.5, "tokens": 300, "params_b": 4.2}}})
check(f"judge cost carries token-compute 4.2 x 300 (got {g[4]:.1f})", abs(g[4] - 1260.0) < 1e-9 and g[3] == 1.5)
for d in (r for t in tasks3.values() for r in t["L"] + t["S"]):
    d["params_b"] = 3.1 if d["tier"] == "local3b" else 14.8; d["tokens_in"], d["tokens_out"] = 100, 100
ct = C.choose_tau(tasks3, "j", 0.03, 200, 1, boots=200, cost_metric="tok")
check(f"token-compute as cost picks the same feasible tau here (tau {ct['tau']})", ct["tau"] == .8 and ct["cost_metric"] == "tok")

# Mac hardware log joins to draws by time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import hwjoin
J = hwjoin.join([{"ts": "2026-10-23T01:00:45.123Z", "task": "a"}, {"ts": "2026-10-23T00:59:00.0Z", "task": "b"},
                 {"_meta": {"batch": {"ts": "2026-10-23T01:01:10.0Z"}}}],
                [{"ts": "2026-10-23T01:00:30Z", "power": "AC Power"}, {"ts": "2026-10-23T01:01:00Z", "power": "Battery Power"}])
check("hw log: latest entry at or before each draw, null before the log starts, batches too",
      J[0]["hw"]["power"] == "AC Power" and J[1]["hw"] is None and J[2]["_meta"]["batch"]["hw"]["power"] == "Battery Power")

# cooldown guard: pauses when the median decode speed of recent drafts falls below min_ratio x the cold reference
cool = {"min_ratio": 0.7, "window": 4, "pause_s": 10, "max_wait_s": 40}
tier = {"name": "x", "ref_decode_tps": 40.0}
check("throttled: needs a full window", not bench.throttled([10, 10, 10], tier, cool))
check("throttled: median below 0.7 x reference", bench.throttled([25, 26, 27, 40], tier, cool) and not bench.throttled([29, 30, 31, 10], tier, cool))
check("throttled: off without a reference or config", not bench.throttled([1] * 4, {"name": "x"}, cool) and not bench.throttled([1] * 4, tier, None))
slept = []; speeds = iter([20.0, 25.0, 35.0, 40.0])
w, tps = bench.cool_down(lambda t, run, p, seed=None: {"decode_tps": next(speeds)}, tier, {}, cool, sleep=slept.append)
check(f"cool_down probes until speed recovers (waited {w}s, last {tps})", w == 30 and tps == 35.0 and slept == [10, 10, 10])
w, tps = bench.cool_down(lambda t, run, p, seed=None: {"decode_tps": 1.0}, tier, {}, cool, sleep=lambda s: None)
check(f"cool_down gives up after max_wait_s (waited {w}s)", w == 40)

# variant framework (T16): deterministic, resumable, verified-by-construction for identity; blind by default
import variants, shutil
@variants.transform("_test_upper_first_line")
def _upper(task, rng, params):
    lines = task["raw_prompt"].split("\n"); i = next(k for k, l in enumerate(lines) if l.strip() and not l.startswith(("from", "import")))
    lines[i] = lines[i] + "  # " + params.get("tag", "x") + str(rng.randint(0, 9))
    return {"raw_prompt": "\n".join(lines)}
with tempfile.TemporaryDirectory() as d:
    variants.VARIANT_DIR = d
    try: variants.build("v_test", "humaneval+", "identity", log=lambda *a: None, split="test"); check("variant build refuses test split without --allow-test", False)
    except SystemExit: check("variant build refuses test split without --allow-test", True)
    try: variants.build("v_own", "own", "identity", split="all", allow_test=True, log=lambda *a: None); check("variant build refuses non-EvalPlus base", False)
    except SystemExit: check("variant build refuses non-EvalPlus base", True)
    m = variants.build("v_id", "humaneval+", "identity", split="all", allow_test=True, log=lambda *a: None)
    V = {t["id"]: t for t in suites.load("variant:v_id")}; B = {t["id"]: t for t in suites.load("humaneval+")}
    check("identity variant reproduces prompt, judge view, prefix, reference and split",
          m["n_tasks"] == 3 and all(V[i][k] == B[i][k] for i in B for k in ("prompt", "judge_task", "context_prefix", "reference", "split", "entry")))
    check("variant rows carry their suite and base", all(v["suite"] == "variant:v_id" and v["base_suite"] == "humaneval+" for v in V.values()))
    m1 = variants.build("v_up", "humaneval+", "_test_upper_first_line", seed=3, params={"tag": "q"}, split="all", allow_test=True, log=lambda *a: None)
    shutil.copytree(os.path.join(d, "v_up"), os.path.join(d, "v_up_copy")); shutil.rmtree(os.path.join(d, "v_up"))
    first = sorted(B)[:1]
    variants.build("v_up", "humaneval+", "_test_upper_first_line", seed=3, params={"tag": "q"}, split="all", ids=first, allow_test=True, log=lambda *a: None)
    m2 = variants.build("v_up", "humaneval+", "_test_upper_first_line", seed=3, params={"tag": "q"}, split="all", allow_test=True, log=lambda *a: None)
    check("variant build is deterministic and resumable (partial then full = full at once)", m1["tasks_sha256"] == m2["tasks_sha256"] and m2["n_tasks"] == 3)
    U = {t["id"]: t for t in suites.load("variant:v_up")}
    check("text transform changes prompt and judge view, keeps reference and tests", all(U[i]["prompt"] != B[i]["prompt"] and "# q" in U[i]["judge_task"] and U[i]["reference"] == B[i]["reference"] for i in B))
    try: variants.build("v_up", "humaneval+", "_test_upper_first_line", seed=4, split="all", allow_test=True, log=lambda *a: None); check("variant refuses a changed definition under the same name", False)
    except SystemExit: check("variant refuses a changed definition under the same name", True)
    rows = os.path.join(d, "r.jsonl"); samp = os.path.join(d, "s.jsonl")
    open(rows, "w").write(json.dumps(dict(tier="t", task=sorted(B)[0], rep=0, suite="variant:v_up", split=U[sorted(B)[0]]["split"], code="def f(): pass\n")) + "\n")
    evalplus_io.export(rows, "variant:v_up", samp)
    S2 = [json.loads(l) for l in open(samp)]
    check("variant export: one sample plus placeholders for every other base problem", len(S2) == 3 and sum(x["solution"] == evalplus_io.PLACEHOLDER for x in S2) == 2)

# T17 transforms on the HumanEval fixture and a synthetic MBPP task
import random as _r
from variants import transforms as VT
_he_raw = ('from typing import List\n\n\ndef has_close_elements(numbers: List[float], threshold: float) -> bool:\n'
           '    """ Check if in given list of numbers, are any two numbers closer to each other than\n    given threshold.\n'
           '    >>> has_close_elements([1.0, 2.0, 3.0], 0.5)\n    False\n    >>> has_close_elements([1.0, 2.8, 3.0], 0.3)\n    True\n    """\n')
he0 = {"id": "HumanEval/0", "entry": "has_close_elements", "split": "cal", "raw_prompt": _he_raw,
       "reference": _he_raw + "    s = sorted(numbers)\n    return any(b - a < threshold for a, b in zip(s, s[1:]))\n"}
mb0 = {"id": "Mbpp/9999", "entry": "add_nums", "split": "cal", "raw_prompt": '"""\nWrite a function to add two numbers. The result must be an integer.\nassert add_nums(1, 2) == 3\n"""\n',
       "reference": '"""\nWrite a function to add two numbers.\nassert add_nums(1, 2) == 3\n"""\n\ndef add_nums(first_num, b):\n    return first_num + b\n'}
def app(t, name, params=None, seed=1):
    ch = variants.TRANSFORMS[name](t, _r.Random(seed), params or {})
    return None if ch is None else variants.rebuild_task(t, ch)
v = app(he0, "rename_params")
fn = VT.entry_def(v["reference"], "has_close_elements"); names = [x.arg for x in fn.args.args]
check(f"rename_params: new parameter names in signature and reference body ({names})",
      "numbers" not in names and all(n in v["raw_prompt"].split("def has_close_elements(")[1].split(")")[0] for n in names)
      and all(n in v["reference"] for n in names) and not VT.check_text(he0, v))
check("rename_params: ordinary prose words are kept", "list of numbers" in v["raw_prompt"])
vm = app(mb0, "rename_params")
check("rename_params on MBPP: judge signature renamed, underscore name renamed in prose-free prompt", "first_num" not in vm["judge_task"] and "add_nums(" in vm["judge_task"] and not VT.check_text(mb0, vm))
v = app(he0, "distractor")
check("distractor: one known paragraph at the end of the description, examples intact", any(p_ in v["raw_prompt"] for p_ in VT.DISTRACTORS) and v["raw_prompt"].count(">>>") == he0["raw_prompt"].count(">>>") and not VT.check_text(he0, v))
for w in (100, 400):
    v = app(he0, "padding", {"words": w}); vm = app(mb0, "padding", {"words": w})
    check(f"padding {w}: at least {w} words added, prompt still valid", v["variant_notes"]["words"] >= w and not VT.check_text(he0, v) and not VT.check_text(mb0, vm) and "assert add_nums" in vm["raw_prompt"])
v = app(he0, "drop_example")
check("drop_example: one of two examples removed", v["raw_prompt"].count(">>>") == he0["raw_prompt"].count(">>>") - 1 and not VT.check_text(he0, v))
check("drop_example: not applicable to MBPP", app(mb0, "drop_example") is None)
vm = app(mb0, "drop_sentence")
check("drop_sentence: second sentence removed, assert kept", "must be an integer" not in vm["raw_prompt"] and "assert add_nums" in vm["raw_prompt"])
VT.ollama_text = lambda *a, **k: "Return True when any two values in the list are nearer than the threshold."
v = app(he0, "paraphrase", {"base_url": "x", "model": "y"})
check("paraphrase: description replaced, examples and signature kept", "nearer than the threshold" in v["raw_prompt"] and v["raw_prompt"].count(">>>") == 2 and not VT.check_text(he0, v))
bad = dict(he0, raw_prompt=he0["raw_prompt"].replace("def has_close_elements(", "def other_name("))
check("check_text catches a lost entry point", bool(VT.check_text(he0, variants.rebuild_task(bad, {}))))

# T18 candidate-code transforms: preserve and inject keep behaviour, mutators change it, payloads stay benign
from variants import codemods as CM
SRC = ('def helper(x):\n    """Square it."""\n    return x * x  # square\n\n\n'
       'def total(nums, limit):\n    """Sum squares below limit."""\n    if limit <= 0:\n        return 0\n    acc = 0\n'
       '    for i in range(0, len(nums)):\n        if nums[i] < limit:\n            acc = acc + helper(nums[i])\n    return acc\n')
TESTS = "assert total([1, 2, 3], 3) == 5\nassert total([], 1) == 0\nassert total([4, 1], 5) == 17\nassert total([-1, -2], 0) == 0\n"
ok_after = lambda code: run_tests(code, TESTS)[0]
check("codemod base program passes its tests", ok_after(SRC))
for name, (fn, kind, bug) in sorted(CM.CODE_TRANSFORMS.items()):
    new = fn(SRC, random.Random(3), {})
    if kind in ("preserve", "inject"):
        check(f"codemod {name}: applies and keeps behaviour", new is not None and new != SRC and ok_after(new))
    else:
        outs = [fn(SRC, random.Random(sd), {}) for sd in range(12)]
        outs = [o for o in outs if o is not None]
        check(f"codemod {name} ({bug}): applies and at least one seed breaks the tests", bool(outs) and any(not ok_after(o) for o in outs))
check("strip_comments removes docstrings and comments", '"""' not in CM.strip_comments(SRC, None, {}) and "# square" not in CM.strip_comments(SRC, None, {}))
check("rename_locals renames assigned locals, keeps parameters", "acc" not in CM.rename_locals(SRC, None, {}) and "nums" in CM.rename_locals(SRC, None, {}))
check("injection payloads are benign canaries", all(not any(w in p_.lower() for w in ("password", "delete", "exploit", "rm -rf")) for p_ in CM.PAYLOADS.values()))
rows_ = [dict(task="T", tier="reference", rep=0, split="cal", code=SRC, hidden_passed=True)]
mrows, sk = CM.apply_rows(rows_, "inject_direct")
check("apply_rows renames the tier, keeps the original verdict for comparison, drops old scores",
      mrows[0]["tier"] == "reference+inject_direct" and mrows[0]["orig_hidden_passed"] is True and "hidden_passed" not in mrows[0] and sk == 0)

check("rename_tokens renames tuple-assignment targets but not call keywords",
      VT.rename_tokens("def f(a, b):\n    a, b = b, a\n    return g(b=a)\n", {"a": "x", "b": "y"}) == "def f(x, y):\n    x, y = y, x\n    return g(b=x)\n")

mbp = dict(mb0, context_prefix="")
vp = variants.rebuild_task(mbp, VT.padding(mbp, random.Random(5), {"words": 1500}))
check("padding never leaks prose into the scoring prefix (MBPP)", vp["context_prefix"] == "" and "from " in vp["raw_prompt"] + "from ")

# network outages: retry the same draw instead of writing an error row; other errors still propagate
import urllib.error as _ue
calls = {"n": 0}
def flaky():
    calls["n"] += 1
    if calls["n"] < 3: raise _ue.URLError("host unreachable")
    return {"ok": True}
waits = []
check("network retry: same call retried after a URLError, then succeeds", bench.with_network_retry(flaky, sleep=waits.append) == {"ok": True} and waits == [30, 60])
try: bench.with_network_retry(lambda: (_ for _ in ()).throw(_ue.HTTPError("u", 500, "model error", {}, None)), sleep=lambda s: None); check("network retry: HTTP errors are not retried", False)
except _ue.HTTPError: check("network retry: HTTP errors are not retried", True)
try: bench.with_network_retry(lambda: (_ for _ in ()).throw(ConnectionRefusedError()), max_wait_s=60, sleep=lambda s: None); check("network retry: gives up after max_wait_s", False)
except ConnectionRefusedError: check("network retry: gives up after max_wait_s", True)

# T21: calibration metrics, Platt, isotonic, stacking
import judgestats as JS
check("Brier and ECE of a perfect predictor are 0", JS.brier([1, 0, 1], [1, 0, 1]) == 0 and JS.ece([1.0, 0.0], [1, 0]) == 0)
check("ECE of a constant 0.5 on all-correct rows is 0.5", abs(JS.ece([0.5] * 10, [1] * 10) - 0.5) < 1e-12)
rnd_ = random.Random(4); xs = [rnd_.random() for _ in range(400)]; ys_ = [int(rnd_.random() < x ** 2) for x in xs]
iso = JS.fit_isotonic(xs, ys_); vals = [v for _, v in iso]
check("isotonic fit is monotone and improves Brier on its training data", vals == sorted(vals) and JS.brier([JS.apply_isotonic(iso, x) for x in xs], ys_) <= JS.brier(xs, ys_))
ab = JS.fit_platt(xs, ys_)
check(f"Platt scaling improves Brier for a miscalibrated score (a={ab[0]:.2f})", JS.brier([JS.apply_platt(ab, x) for x in xs], ys_) < JS.brier(xs, ys_))
X = [[rnd_.gauss(0, 1), rnd_.gauss(0, 1)] for _ in range(300)]; Y = [int(x[0] - 0.2 * x[1] + rnd_.gauss(0, .3) > 0) for x in X]
w = JS.fit_logreg(X, Y)
check(f"stacked logistic regression recovers the informative input (w={[round(v, 2) for v in w]})", w[1] > 1 and abs(w[2]) < w[1])

import variants.quality as VQ
v = app(he0, "translate", {"base_url": "x", "model": "y", "lang": "French"})
check("translate: description replaced, examples kept, language recorded", v["variant_notes"]["lang"] == "French" and v["raw_prompt"].count(">>>") == 2 and not VT.check_text(he0, v))
check("cosine similarity", abs(VQ.cosine([1, 0], [1, 0]) - 1) < 1e-12 and abs(VQ.cosine([1, 0], [0, 1])) < 1e-12)

NEST = "def outer(xs):\n    def inner(s):\n        return len(s)\n    return [inner(s) for s in xs]\n"
check("rename_locals never renames a name that is a parameter elsewhere (HumanEval/6 bug)",
      CM.rename_locals(NEST, None, {}) is None or run_tests(CM.rename_locals(NEST, None, {}), "assert outer(['ab', 'c']) == [2, 1]")[0])

# S2: paired AUROC difference between two judges on the same drafts
T2 = {"A": {"L": [dict(hidden_passed=ok, judges={"x": {"p": px}, "y": {"p": py}}) for ok, px, py in
                  [(True, .9, .4), (True, .8, .6), (False, .2, .5), (False, .3, .7)]], "S": []}}
pd = C.paired_auroc_diff(T2, "x", "y", [[0]] * 5)
check(f"paired AUROC difference: perfect x vs weak y = 1.0 - 0.25 (got {pd['diff']})", abs(pd["diff"] - 0.75) < 1e-12)

print(f"\n{len(fails)} failures" + (": " + ", ".join(fails) if fails else ""))
sys.exit(1 if fails else 0)

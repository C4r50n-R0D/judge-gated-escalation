#!/usr/bin/env python3
"""Task suites and the fixed calibration/test split.

Suites
  own         the self-authored tasks in tasks.py, scored here (visible = tests, hidden = tests AND hidden tests).
              Role in the study: contamination check only (too few tasks for the main claims).
  humaneval+  EvalPlus HumanEval+ (164 problems), main study.
  mbpp+       EvalPlus MBPP+ (378 problems), main study.

EvalPlus data is NOT bundled. Fetch it on the machine that runs the study:
  python suites.py fetch            # downloads the pinned releases into data/
  python suites.py show             # counts per suite and split, plus the split manifest hash
EvalPlus problems are scored with the official `evalplus.evaluate` (see evalplus_io.py):
  visible = EvalPlus "base" tests (the original HumanEval / MBPP tests)
  hidden  = EvalPlus "plus" result (base AND extra tests), the standard HumanEval+/MBPP+ correctness.

Split: each task id is assigned to "cal" or "test" by a salted SHA-256 hash, so the split never depends
on file order, never changes when tasks are added, and can be checked by anyone. CAL_FRACTION and SALT
are pre-registered in PREREG.md; changing them after data collection invalidates the study.
"""
import gzip, hashlib, json, os, re, sys, urllib.request

SALT = "tiered-llm-bench/prereg-v1"
CAL_FRACTION = 0.28            # about 150 of 542 EvalPlus problems go to calibration
DATA_DIR = os.environ.get("BENCH_DATA_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "data"))
RELEASES = {  # pinned to the versions evalplus 0.3.1 uses
    "humaneval+": ("https://github.com/evalplus/humanevalplus_release/releases/download/v0.1.10/HumanEvalPlus.jsonl.gz",
                   "HumanEvalPlus-v0.1.10.jsonl.gz"),
    "mbpp+": ("https://github.com/evalplus/mbppplus_release/releases/download/v0.2.0/MbppPlus.jsonl.gz",
              "MbppPlus-v0.2.0.jsonl.gz"),
}
EVALPLUS_NAME = {"humaneval+": "humaneval", "mbpp+": "mbpp"}

PROMPT_WRAP = ("Complete the following Python function. Return the complete function definition, "
               "including any imports it needs, in a single ```python block.\n\n```python\n{prompt}\n```")

def subset_hash(task_id):
    """Uniform [0,1) value used to pick a fixed subset of tasks for secondary arms (e.g. the 3B tier)."""
    return int(hashlib.sha256(f"{SALT}|subset|{task_id}".encode()).hexdigest()[:8], 16) / 0x100000000

def split_of(task_id):
    h = int(hashlib.sha256(f"{SALT}|{task_id}".encode()).hexdigest()[:8], 16) / 0x100000000
    return "cal" if h < CAL_FRACTION else "test"

def _read_jsonl(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt") as f:
        return [json.loads(l) for l in f if l.strip()]

def data_path(suite):
    override = os.environ.get({"humaneval+": "HUMANEVAL_PLUS_PATH", "mbpp+": "MBPP_PLUS_PATH"}[suite])
    return override or os.path.join(DATA_DIR, RELEASES[suite][1])

def context_prefix(prompt, entry):
    """Everything in the problem prompt before the entry function: imports AND helper functions (for example
    HumanEval/10 is_palindrome, /32 poly, /38 encode_cyclic). Prepended to every solution before scoring, so a model
    that returns only the requested function is not failed for omitting helpers the task already supplied. A
    solution that redefines a helper overrides it, as in normal Python."""
    lines = prompt.splitlines(); out = []
    for l in lines:
        if l.startswith(f"def {entry}("): break
        out.append(l)
    else:
        out = [l for l in lines if l.startswith(("import ", "from "))]
    return "\n".join(out).rstrip() + "\n\n" if any(x.strip() for x in out) else ""

def judge_view(prompt, entry=None, reference=""):
    """What the judge sees: the problem text with any assert lines removed (MBPP+ prompts embed one base test,
    and judges must never see tests). Because that assert is the only place an MBPP+ prompt names the function,
    the function's signature (name and parameters, no expected output) is added, taken from the reference
    solution's def line. The generator sees the standard prompt, assert included."""
    kept = [l for l in prompt.splitlines() if not l.strip().startswith("assert ")]
    text = "\n".join(kept).rstrip()
    if len(kept) < len(prompt.splitlines()) and entry:
        m = re.search(rf"^\s*def\s+{re.escape(entry)}\s*\(([^)]*)\)", reference, re.M)
        sig = f"{entry}({m.group(1).strip()})" if m else f"{entry}(...)"
        text += f"\nRequired function signature: {sig}"
    return text + "\n"

def load(suite):
    """Return a list of task dicts with a common shape:
    id, suite, split, prompt (what the model sees), judge_task (what the judge sees), entry,
    scorer ('local' | 'evalplus'), and for local scoring: tests, hidden, reference."""
    if suite.startswith("variant:"):   # a verified transform of a base suite (variants/), same ids, splits and tests
        import variants
        return variants.load(suite.split(":", 1)[1])
    if suite == "own":
        from tasks import TASKS
        return [dict(id=t["id"], suite="own", split=split_of(t["id"]), prompt=t["prompt"], judge_task=t["prompt"], raw_prompt=t["prompt"],
                     entry=t["entry"], difficulty=t.get("difficulty"), scorer="local",
                     tests=t["tests"], hidden=t["tests"] + "\n" + t["hidden"], reference=t["reference"]) for t in TASKS]
    # hidden = visible AND extra tests, matching the EvalPlus definition (base and plus)
    if suite not in RELEASES: raise SystemExit(f"unknown suite {suite}; use own, humaneval+ or mbpp+")
    p = data_path(suite)
    if not os.path.exists(p): raise SystemExit(f"{p} missing: run `python suites.py fetch` on a machine with GitHub access")
    out = []
    for prob in _read_jsonl(p):
        out.append(dict(id=prob["task_id"], suite=suite, split=split_of(prob["task_id"]),
                        prompt=PROMPT_WRAP.format(prompt=prob["prompt"].rstrip()), judge_task=judge_view(prob["prompt"], prob["entry_point"], prob["prompt"] + prob["canonical_solution"]),
                        entry=prob["entry_point"], scorer="evalplus", context_prefix=context_prefix(prob["prompt"], prob["entry_point"]),
                        raw_prompt=prob["prompt"],
                        reference=prob["prompt"] + prob["canonical_solution"]))
    return out

def load_many(suites):
    tasks = []
    for s in suites: tasks += load(s)
    ids = [t["id"] for t in tasks]
    if len(ids) != len(set(ids)): raise SystemExit("duplicate task ids across suites")
    return tasks

def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""): h.update(chunk)
    return h.hexdigest()

def manifest(tasks):
    """Split manifest: sorted (id, split) pairs, their hash, and checksums of the data files. Commit before collecting."""
    pairs = sorted((t["id"], t["split"]) for t in tasks)
    files = {s: file_sha256(data_path(s)) for s in sorted({t["suite"] for t in tasks}) if s in RELEASES}
    return {"salt": SALT, "cal_fraction": CAL_FRACTION, "n": len(pairs), "data_sha256": files,
            "n_cal": sum(1 for _, s in pairs if s == "cal"), "n_test": sum(1 for _, s in pairs if s == "test"),
            "sha256": hashlib.sha256(json.dumps(pairs).encode()).hexdigest(), "pairs": pairs}

def fetch():
    os.makedirs(DATA_DIR, exist_ok=True)
    for suite, (url, name) in RELEASES.items():
        dst = os.path.join(DATA_DIR, name)
        if os.path.exists(dst): print("have", dst); continue
        print("downloading", url)
        urllib.request.urlretrieve(url, dst)
        print("  ->", dst, len(_read_jsonl(dst)), "problems")

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "fetch": fetch()
    elif cmd == "show":
        suites = sys.argv[2].split(",") if len(sys.argv) > 2 else ["humaneval+", "mbpp+"]
        m = manifest(load_many(suites))
        print(json.dumps({k: v for k, v in m.items() if k != "pairs"}, indent=1))
    elif cmd == "manifest":
        suites = sys.argv[2].split(","); out = sys.argv[3]
        json.dump(manifest(load_many(suites)), open(out, "w"), indent=0); print("wrote", out)
    else: print(__doc__)

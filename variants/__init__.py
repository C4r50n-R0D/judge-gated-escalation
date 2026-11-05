"""Variant suites: deterministic, verified transforms of the main task suites (KICKOFF2 T16).

A variant suite is defined by (base suite, transform name, seed, parameters, split). It keeps every task id, its
split and its EvalPlus tests, and changes only what models or judges see (the problem text, and for some transforms
parameter names in the signature and the reference). Scoring therefore stays the official evalplus.evaluate on the
base dataset.

  python3 -m variants build NAME --base mbpp+ --transform identity [--seed 1] [--param k=v] [--split cal] [--ids a,b]
  python3 -m variants show NAME
  python3 -m variants selfcheck-rows NAME out.jsonl   # canonical + stub rows for the EvalPlus bridge (see evalplus_io)

Files under data/variants/NAME/: tasks.jsonl (one task per line, same shape as suites.load), manifest.json
(definition, counts, content hash, transform failures, verification status). A build is resumable: tasks already
written are kept; a different definition under the same name is refused. Loading: suites.load("variant:NAME").

Blindness: variants of test-split tasks count as test-split data. build refuses split=test or all unless
--allow-test is given, which is only for after the confirmatory analysis (STOP C).
"""
import hashlib, json, os, random

import suites

VARIANT_DIR = os.path.join(suites.DATA_DIR, "variants")
TRANSFORMS = {}   # name -> fn(task, rng, params) -> dict of changed fields, or None if the transform does not apply
VERSIONS = {}     # name -> version; part of the definition, so changed transform code never reuses an old build


def transform(name, version=1):
    def reg(fn): TRANSFORMS[name] = fn; VERSIONS[name] = version; return fn
    return reg


@transform("identity")
def _identity(task, rng, params):
    """No change. Used to test the framework and as the control condition of every experiment."""
    return {}


FRAMEWORK_VERSION = 2   # 2: variants keep the base task's scoring prefix

def definition(base, tname, seed, params, split):
    return {"base": base, "transform": tname, "version": VERSIONS.get(tname, 1), "framework": FRAMEWORK_VERSION,
            "seed": seed, "params": params or {}, "split": split}


def def_hash(d): return hashlib.sha256(json.dumps(d, sort_keys=True).encode()).hexdigest()[:16]


def paths(name):
    d = os.path.join(VARIANT_DIR, name)
    return d, os.path.join(d, "tasks.jsonl"), os.path.join(d, "manifest.json")


def rebuild_task(task, changes):
    """Apply a transform's changes. A transform returns any of: raw_prompt (new problem text), reference (new
    canonical program, e.g. renamed parameters), judge_raw (text for judge_view, default = raw_prompt), notes."""
    t = dict(task)
    raw = changes.get("raw_prompt", task["raw_prompt"])
    ref = changes.get("reference", task["reference"])
    t["raw_prompt"] = raw
    t["reference"] = ref
    t["prompt"] = suites.PROMPT_WRAP.format(prompt=raw.rstrip())
    # the scoring prefix (imports and helpers before the entry point) is the base task's: transforms never change
    # it, and re-deriving it from transformed text can pick up prose lines that start with "from"/"import"
    t["context_prefix"] = changes.get("context_prefix", task.get("context_prefix", ""))
    t["judge_task"] = suites.judge_view(changes.get("judge_raw", raw), task["entry"], ref)
    if changes.get("notes"): t["variant_notes"] = changes["notes"]
    return t


def content_hash(path):
    return suites.file_sha256(path) if os.path.exists(path) else None


def build(name, base, tname, seed=1, params=None, split="cal", ids=None, allow_test=False, log=print):
    if tname not in TRANSFORMS: raise SystemExit(f"unknown transform {tname}; known: {sorted(TRANSFORMS)}")
    if base not in suites.RELEASES: raise SystemExit(f"variants are built from EvalPlus suites ({sorted(suites.RELEASES)}), not {base}")
    if split != "cal" and not allow_test:
        raise SystemExit("variants of test-split tasks are test-split data: build them only after STOP C (--allow-test)")
    d, tpath, mpath = paths(name); os.makedirs(d, exist_ok=True)
    df = definition(base, tname, seed, params, split)
    if os.path.exists(mpath):
        old = json.load(open(mpath))
        if old["definition"] != df: raise SystemExit(f"variant {name} exists with a different definition; use a new name")
    done = {json.loads(l)["id"] for l in open(tpath)} if os.path.exists(tpath) else set()
    base_tasks = [t for t in suites.load(base) if split == "all" or t["split"] == split]
    if ids: base_tasks = [t for t in base_tasks if t["id"] in set(ids)]
    failures = json.load(open(mpath)).get("failures", {}) if os.path.exists(mpath) else {}
    with open(tpath, "a") as f:
        for t in sorted(base_tasks, key=lambda t: t["id"]):
            if t["id"] in done or t["id"] in failures: continue
            rng = random.Random(f"{seed}|{tname}|{t['id']}")
            try:
                ch = TRANSFORMS[tname](t, rng, params or {})
            except Exception as e:
                ch = None; failures[t["id"]] = f"{type(e).__name__}: {str(e)[:160]}"
            if ch is None:
                failures.setdefault(t["id"], "transform not applicable"); continue
            v = rebuild_task(t, ch)
            errs = check_text(t, v)
            if errs: failures[t["id"]] = "text check: " + "; ".join(errs); continue
            v.update(suite=f"variant:{name}", base_suite=base, variant=name, transform=tname)
            f.write(json.dumps(v) + "\n"); f.flush()
    rows = [json.loads(l) for l in open(tpath)]
    m = {"name": name, "definition": df, "definition_sha": def_hash(df), "n_tasks": len(rows),
         "n_failed": len(failures), "failures": failures, "tasks_sha256": content_hash(tpath),
         "verification": json.load(open(mpath)).get("verification", {}) if os.path.exists(mpath) else {}}
    json.dump(m, open(mpath, "w"), indent=1)
    log(f"variant {name}: {len(rows)} tasks, {len(failures)} not transformed -> {d}")
    return m


def load(name):
    d, tpath, mpath = paths(name)
    if not os.path.exists(tpath): raise SystemExit(f"variant {name} not built ({tpath} missing)")
    return [json.loads(l) for l in open(tpath)]


def manifest(name): return json.load(open(paths(name)[2]))


def record_verification(name, key, result):
    """Store a verification result (selfcheck, invariance check, quality check) in the manifest."""
    mpath = paths(name)[2]; m = json.load(open(mpath))
    m.setdefault("verification", {})[key] = result
    json.dump(m, open(mpath, "w"), indent=1)


from variants.transforms import check_text   # noqa: E402  (registers the T17 transforms)

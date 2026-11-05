#!/usr/bin/env python3
"""Spec-driven runner for exploratory experiments (KICKOFF2 T22, PREREG v2 section 11).

  python3 tools/exprun.py new E2 --title "Judge zoo"       # creates ext/E2/{SPEC.md, spec.json, RESULT.md}
  python3 tools/exprun.py run E2 [--pilot]                 # runs spec.json steps in order; resumable
  python3 tools/exprun.py status [E2]
  python3 tools/exprun.py comparisons                      # rewrites ext/COMPARISONS.md from every spec.json

spec.json: {"id", "title", "split": "cal"|"any", "steps": [{"name", "cmd", "pilot_cmd"?, "timeout_s"?}],
            "comparisons": [{"name", "metric", "conditions": [...], "status": "planned"|"reported"}]}
Rules enforced by run:
  - SPEC.md and spec.json must be committed and unchanged in the working tree (predictions before data).
  - "split": "cal" experiments may run before STOP C; "any" refuses unless runs/STOP_C_DONE exists.
  - Steps run in order with a per-step timeout (the watchdog); each step's output goes to ext/<id>/logs/<step>.log,
    and its start and end times to ext/<id>/state.json, which also makes the run resumable (finished steps skip).
  - Every step's start and end are UTC timestamps, so tools/hwjoin.py can attach the Mac's power and thermal log.
Commands run with the repo root as the working directory and env.sh sourced (BENCH_SANDBOX).
"""
import argparse, datetime, json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXT = os.path.join(ROOT, "ext")
now = lambda: datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

SPEC_TEMPLATE = """# {id}: {title}

Status: SPEC (written before any data; exploratory by rule, PREREG v2 section 11)

## Question
(what this experiment asks)

## Manipulation
(conditions compared, and what stays fixed)

## Primary outcome
(one metric, with its unit)

## Analysis
Script: (path). Task-cluster bootstrap CIs; effect sizes only, no significance claims; transfer and recalibrated
modes where a gate is involved.

## Predictions (directional, written before data)
1.

## Planned size and estimated hours
(tasks, draws, judges; Mac hours; homelab hours)

## Comparisons counted in ext/COMPARISONS.md
(listed in spec.json)
"""

RESULT_TEMPLATE = """# {id}: {title}: result

Status: not run

## What was run
(commands, commit hash, dates, hardware log summary)

## Results
(effect sizes with CIs; tables or charts)

## Predictions vs outcome
(one line per prediction in SPEC.md: held / did not hold / unclear)

## Verification and caveats
(variant selfchecks, exclusions, timing caveats)
"""


def d(eid): return os.path.join(EXT, eid)


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)


def committed_unchanged(path):
    rel = os.path.relpath(path, ROOT)
    tracked = git("ls-files", "--error-unmatch", rel).returncode == 0
    clean = git("diff", "--quiet", "HEAD", "--", rel).returncode == 0
    return tracked and clean


def cmd_new(a):
    p = d(a.id); os.makedirs(os.path.join(p, "logs"), exist_ok=True)
    for name, body in (("SPEC.md", SPEC_TEMPLATE), ("RESULT.md", RESULT_TEMPLATE)):
        f = os.path.join(p, name)
        if not os.path.exists(f): open(f, "w").write(body.format(id=a.id, title=a.title))
    f = os.path.join(p, "spec.json")
    if not os.path.exists(f):
        json.dump({"id": a.id, "title": a.title, "split": "cal", "steps": [], "comparisons": []}, open(f, "w"), indent=1)
    print(f"created {p}: fill SPEC.md and spec.json, commit them, then run")


def load_state(eid):
    f = os.path.join(d(eid), "state.json")
    return json.load(open(f)) if os.path.exists(f) else {"steps": {}}


def save_state(eid, st): json.dump(st, open(os.path.join(d(eid), "state.json"), "w"), indent=1)


def cmd_run(a):
    p = d(a.id); spec = json.load(open(os.path.join(p, "spec.json")))
    for f in ("SPEC.md", "spec.json"):
        if not committed_unchanged(os.path.join(p, f)):
            raise SystemExit(f"{a.id}/{f} is not committed or has uncommitted changes: commit the spec (and predictions) before running")
    if spec.get("split", "cal") != "cal" and not os.path.exists(os.path.join(ROOT, "runs", "STOP_C_DONE")):
        raise SystemExit(f"{a.id} uses test-split data: only after the confirmatory analysis (STOP C)")
    st = load_state(a.id); key = "pilot" if a.pilot else "full"
    st.setdefault("runs", {}).setdefault(key, {"started": now(), "commit": git("rev-parse", "--short", "HEAD").stdout.strip()})
    for s in spec["steps"]:
        sk = f"{key}:{s['name']}"
        if st["steps"].get(sk, {}).get("status") == "done": print(f"skip {sk} (done)"); continue
        cmd = s.get("pilot_cmd", s["cmd"]) if a.pilot else s["cmd"]
        log = os.path.join(p, "logs", f"{key}_{s['name']}.log")
        st["steps"][sk] = {"status": "running", "start": now(), "cmd": cmd}; save_state(a.id, st)
        print(f"run {sk}: {cmd}", flush=True)
        try:
            with open(log, "a") as lf:
                lf.write(f"\n=== {now()} {cmd}\n"); lf.flush()
                r = subprocess.run(["bash", "-c", f"source env.sh 2>/dev/null; {cmd}"], cwd=ROOT, stdout=lf, stderr=subprocess.STDOUT,
                                   timeout=s.get("timeout_s", 6 * 3600))
            status = "done" if r.returncode == 0 else f"failed (exit {r.returncode})"
        except subprocess.TimeoutExpired:
            status = f"timed out after {s.get('timeout_s', 6 * 3600)} s"
        st["steps"][sk].update(status=status, end=now()); save_state(a.id, st)
        if status != "done": raise SystemExit(f"{sk} {status}; see {log}. Rerun to resume from this step.")
    st["runs"][key]["finished"] = now(); save_state(a.id, st)
    print(f"{a.id} {key} run complete")


def cmd_status(a):
    ids = [a.id] if a.id else sorted(x for x in os.listdir(EXT) if os.path.exists(os.path.join(EXT, x, "spec.json")))
    for i in ids:
        st = load_state(i); spec = json.load(open(os.path.join(d(i), "spec.json")))
        done = sum(1 for v in st["steps"].values() if v.get("status") == "done")
        print(f"{i:6s} {spec['title'][:40]:40s} steps {len(spec['steps'])}, finished step-runs {done}")
        for k, v in st["steps"].items(): print(f"    {k:30s} {v['status']:24s} {v.get('start', '')} -> {v.get('end', '')}")


def cmd_comparisons(a):
    rows = []
    for i in sorted(os.listdir(EXT)):
        f = os.path.join(EXT, i, "spec.json")
        if os.path.exists(f):
            for c in json.load(open(f)).get("comparisons", []):
                rows.append((i, c["name"], c.get("metric", ""), ", ".join(c.get("conditions", [])), c.get("status", "planned")))
    L = ["# Comparisons reported by the exploratory program", "",
         "Every comparison any experiment plans or reports is listed here, so a reader can see how many were made.",
         "Generated by `python3 tools/exprun.py comparisons` from each ext/<id>/spec.json; do not edit by hand.", "",
         f"Total: {len(rows)} ({sum(r[4] == 'reported' for r in rows)} reported, {sum(r[4] != 'reported' for r in rows)} planned).", "",
         "| experiment | comparison | metric | conditions | status |", "|---|---|---|---|---|"]
    L += [f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} |" for r in rows]
    open(os.path.join(EXT, "COMPARISONS.md"), "w").write("\n".join(L) + "\n"); print(f"{len(rows)} comparisons -> ext/COMPARISONS.md")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=["new", "run", "status", "comparisons"]); ap.add_argument("id", nargs="?")
    ap.add_argument("--title", default="untitled"); ap.add_argument("--pilot", action="store_true"); a = ap.parse_args()
    os.makedirs(EXT, exist_ok=True)
    {"new": cmd_new, "run": cmd_run, "status": cmd_status, "comparisons": cmd_comparisons}[a.cmd](a)

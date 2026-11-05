#!/usr/bin/env python3
"""Gate 1 v2 descriptives from Stage 1 calibration rows only (KICKOFF2 T14). Reads calibration rows, never test rows.
  python3 tools/gate1_v2.py runs/stage1.labeled.jsonl [--judges tev,llama,selfconf] [--boots 2000]
Prints, for every local tier against the strong tier: per-tier hidden pass rate (task-cluster bootstrap CI), the gap
to the strong tier (paired by task, CI), and for each judge pooled AUROC with CI and within-task AUROC with CI.
Descriptive only: no rule is attached to the gaps (PREREG v2 section 8)."""
import argparse, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import controllers as C
import judgestats as S
from jsonl import read_jsonl

ap = argparse.ArgumentParser(); ap.add_argument("path"); ap.add_argument("--judges", default="tev,llama,selfconf")
ap.add_argument("--strong", default="strong14b"); ap.add_argument("--locals", default="local3b,local1p5b,local7b")
ap.add_argument("--boots", type=int, default=2000); ap.add_argument("--seed", type=int, default=20261009); a = ap.parse_args()
assert all(r.get("split") == "cal" for r in read_jsonl(a.path) if "_meta" not in r), "Stage 1 file contains non-calibration rows; refusing"

def rate(draws): return sum(bool(d["hidden_passed"]) for d in draws) / len(draws)

for local in a.locals.split(","):
    tasks, excl, _, stats = C.load(a.path, local, a.strong, "cal")
    if not tasks: print(f"{local}: no calibration tasks with both tiers"); continue
    names = sorted(tasks); idx = C.boot_idx(len(names), a.boots, a.seed)
    lr = [rate(tasks[t]["L"]) for t in names]; sr = [rate(tasks[t]["S"]) for t in names]
    m, lo, hi = C.mean_ci(lr, idx); ms, los, his = C.mean_ci(sr, idx); g, glo, ghi = C.mean_ci([s - l for s, l in zip(sr, lr)], idx)
    nd = sum(len(tasks[t]["L"]) for t in names)
    print(f"\n== {local} vs {a.strong}: {len(names)} tasks ({len(excl)} excluded), {nd} local drafts; rows {stats}")
    print(f"   hidden pass rate {local} {m:.3f} [{lo:.3f}, {hi:.3f}]   {a.strong} {ms:.3f} [{los:.3f}, {his:.3f}]")
    print(f"   gap {a.strong} - {local}: {g:+.3f} [{glo:+.3f}, {ghi:+.3f}]  (per-task means, task-cluster bootstrap)")
    for j in a.judges.split(","):
        au = C.judge_auroc(tasks, j, idx, a.boots, a.seed + 2); w = C.within_task_auroc(tasks, j, idx, a.seed)
        un = C.unjudged(tasks, j)
        lab = [(d["judges"][j]["p"], int(bool(d["hidden_passed"]))) for t in names for d in tasks[t]["L"] if (d.get("judges") or {}).get(j)]
        br = S.brier([p for p, _ in lab], [y for _, y in lab]); ec = S.ece([p for p, _ in lab], [y for _, y in lab])
        print(f"   judge {j:9s} AUROC {C.fmt(au['auroc'])} [{C.fmt(au['lo'])}, {C.fmt(au['hi'])}] (correct {au['n_correct']}, wrong {au['n_wrong']}); "
              f"within-task {C.fmt(w['auroc'])} [{C.fmt(w['lo'])}, {C.fmt(w['hi'])}] over {w['tasks_with_pairs']} tasks; Brier {C.fmt(br)} ECE {C.fmt(ec)}; unjudged {un}")

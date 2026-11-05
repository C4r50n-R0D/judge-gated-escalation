#!/usr/bin/env python3
"""E11 generation prompts (DRAFT, written before any E11 draw). Each style returns (system, prompt) for bench.gen.
  direct            the main-study SYSTEM and PROMPT_WRAP, byte for byte (the reference condition)
  reasoning_first   at most five short lines of plain-text reasoning, then one code block (bench.extract_code takes
                    the first ```python block, so the reasoning never reaches scoring or the judge)
  few_shot          two worked examples from the CALIBRATION split of the same suite (problem as PROMPT_WRAP, answer
                    as the canonical solution), then the task; the task itself is never its own example
Other E11 factors are run settings, not prompts: temperature 0.0 / 0.8 (main) / 1.2, num_predict 256 / 768 (main) /
1536.
  python3 ext/E11/prompts.py show TASK_ID STYLE      # print the exact system and prompt
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import bench, suites

STYLES = ("direct", "reasoning_first", "few_shot")
SYSTEM_REASON = ("You are a careful Python programmer. First write at most five short lines of plain-text reasoning "
                 "about the approach and the edge cases. Then reply with a single ```python code block containing only "
                 "the requested code and its imports. No tests, no example usage.")
# short, ordinary calibration tasks, fixed before any E11 draw; a task never serves as its own example
EXEMPLARS = {"humaneval+": ["HumanEval/45", "HumanEval/13", "HumanEval/11"], "mbpp+": ["Mbpp/798", "Mbpp/93", "Mbpp/269"]}
_T = {}


def task_by_id(suite, tid):
    if suite not in _T: _T[suite] = {t["id"]: t for t in suites.load(suite)}
    return _T[suite][tid]


def exemplars(task, n=2):
    suite = "mbpp+" if task["id"].startswith("Mbpp/") else "humaneval+"
    out = []
    for tid in EXEMPLARS[suite]:
        if tid == task["id"]: continue
        t = task_by_id(suite, tid)
        assert t.get("split") == "cal", f"exemplar {tid} is not a calibration task"
        out.append(t)
        if len(out) == n: break
    return out


def build(task, style):
    if style == "direct": return bench.SYSTEM, task["prompt"]
    if style == "reasoning_first": return SYSTEM_REASON, task["prompt"]
    if style == "few_shot":
        shots = "".join(f"{t['prompt']}\n\n```python\n{t['reference'].strip()}\n```\n\n" for t in exemplars(task))
        return bench.SYSTEM, "Here are two solved examples.\n\n" + shots + "Now the task.\n\n" + task["prompt"]
    raise ValueError(style)


if __name__ == "__main__":
    if sys.argv[1:2] == ["show"]:
        tid, style = sys.argv[2], sys.argv[3]
        t = task_by_id("mbpp+" if tid.startswith("Mbpp/") else "humaneval+", tid)
        s, p = build(t, style); print("SYSTEM:", s, "\n---\n" + p)

#!/usr/bin/env python3
"""E6 input: the T18 injection canaries on local3b drafts of IN (E3's task subset), each re-scored with the official
evaluator in the network-less container (any verdict change stops the run), plus two code-side defense views.
  python3 ext/E6/inject.py IN OUT WORKDIR [--max-rep 2]
OUT rows (all local3b, rep < --max-rep):
  local3b, local3b+inject_<k>                     the code as written / with the payload ("none" view)
  <tier>@strip                                    comments and docstrings removed (T18 strip_comments)
  <tier>@san                                      sanitize() below
Defense views are what the judge sees; they keep the verdicts of the code they came from."""
import argparse, io, json, os, re, subprocess, sys, tokenize, unicodedata
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import evalplus_io, suites
from jsonl import read_jsonl
from variants.codemods import apply_rows, CODE_TRANSFORMS, parse

INJECT = ("direct", "authority", "fake_json", "role_tags", "multilingual", "hidden_chars", "homoglyph", "padding",
          "string", "identifier")
# Cyrillic and Greek letters that look like Latin ones
FOLD = str.maketrans("аеосрхуіјѕԁАЕОСРХУІЈЅВНКМТαοερτυνκΑΒΕΗΙΚΜΝΟΡΤΥΧ", "aeocpxyijsdAEOCPXYIJSBHKMTaoeptvvkABEHIKMNOPTYX")
FLAG = re.compile(r"review|valuat|approv|verdict|sign-off|\banswer\b|\byes\b|\boui\b|\bja\b|korrekt|is_correct|"
                  r"<\s*/?\s*(system|candidate_code)\b|\bcorrect\b", re.I)


def sanitize(code):
    """A generic pre-judge sanitizer: drop format characters (zero-width and similar), fold look-alike letters to
    Latin, delete comments that address a reviewer or claim a verdict or contain non-ASCII text (whole line if the line
    was only that comment), and blank string literals that do. Names are left alone. Judge view only."""
    code = "".join(ch for ch in code if unicodedata.category(ch) != "Cf").translate(FOLD)
    try: toks = list(tokenize.generate_tokens(io.StringIO(code).readline))
    except (tokenize.TokenError, SyntaxError, IndentationError): return code
    lines = code.splitlines(keepends=True); edits = []
    for t in toks:
        hit = FLAG.search(t.string) or any(ord(ch) > 127 for ch in t.string)
        if t.type == tokenize.COMMENT and hit:
            (r, c), (_, e) = t.start, t.end
            edits.append((r, 0, len(lines[r - 1]), "") if not lines[r - 1][:c].strip() else (r, c, e, ""))
        elif t.type == tokenize.STRING and FLAG.search(t.string) and t.start[0] == t.end[0]:
            (r, c), (_, e) = t.start, t.end; edits.append((r, c, e, '""'))
    for r, c, e, txt in sorted(edits, reverse=True):
        l = lines[r - 1]
        lines[r - 1] = "" if (c, e) == (0, len(l)) else (l[:c] + txt + l[e:] if txt else l[:c].rstrip() + l[e:])
    out = "".join(lines)
    return out if parse(out) is not None else code


def score(rows, suite, b):
    with open(b + ".rows.jsonl", "w") as f: f.writelines(json.dumps(r) + "\n" for r in rows)
    for stale in (b + ".samples_eval_results.json", b + ".scored.jsonl"):   # evalplus reuses an old results file
        if os.path.exists(stale): os.remove(stale)
    evalplus_io.export(b + ".rows.jsonl", suite, b + ".samples.jsonl")
    d, s = os.path.abspath(os.path.dirname(b)), os.path.basename(b) + ".samples.jsonl"
    cmd = ["docker", "run", "--rm", "--network", "none", "--memory", "6g", "-e", "EVALPLUS_MAX_MEMORY_BYTES=8589934592", "-v", f"{d}:/app",
           "-v", "evalplus-cache:/root/.cache/evalplus", "evalplus:0.3.1", "evalplus.evaluate", "--dataset", suites.EVALPLUS_NAME[suite],
           "--samples", f"/app/{s}", "--parallel", "1"]
    with open(b + ".evalplus.log", "w") as log: subprocess.run(cmd, check=True, stdout=log, stderr=subprocess.STDOUT)
    evalplus_io.import_(b + ".rows.jsonl", suite, b + ".samples.jsonl", b + ".samples_eval_results.json", b + ".scored.jsonl")
    return read_jsonl(b + ".scored.jsonl")


ap = argparse.ArgumentParser(); ap.add_argument("inp"); ap.add_argument("out"); ap.add_argument("wd"); ap.add_argument("--max-rep", type=int, default=2)
a = ap.parse_args(); os.makedirs(a.wd, exist_ok=True)
base = [r for r in read_jsonl(a.inp) if "_meta" not in r and r.get("tier") == "local3b" and r["rep"] < a.max_rep
        and r.get("hidden_passed") is not None and r.get("code")]
orig = {(r["task"], r["rep"]): r for r in base}
none, report, bad = list(base), {}, 0
for k in INJECT:
    name = f"inject_{k}"
    for suite in sorted({r["suite"] for r in base}):
        src = [r for r in base if r["suite"] == suite]
        mod, skipped = apply_rows(src, name, 1)
        sc = score(mod, suite, os.path.join(a.wd, f"{name}.{suite}"))
        changed = [(r["task"], r["rep"]) for r in sc if r["hidden_passed"] != r["orig_hidden_passed"]]
        vis = sum(r["visible_passed"] != orig[(r["task"], r["rep"])].get("visible_passed") for r in sc)
        report[f"{name}|{suite}"] = dict(input=len(src), injected=len(sc), not_applicable=skipped, verdict_changes=len(changed),
                                         visible_changes=vis, changed=changed[:30])
        print(name, suite, {x: v for x, v in report[f"{name}|{suite}"].items() if x != "changed"}, flush=True)
        bad += len(changed) + vis; none += sc
views = []
for r in none:
    for v, fn in (("strip", lambda c: CODE_TRANSFORMS["strip_comments"][0](c, None, {})), ("san", sanitize)):
        new = fn(r["code"])
        if new is None: report.setdefault(f"view_failed|{v}", []).append((r["tier"], r["task"], r["rep"])); continue
        o = {x: y for x, y in r.items() if x != "judges"}
        o.update(code=new, tier=f"{r['tier']}@{v}", view=v, view_of=r["tier"], view_changed=new != r["code"])
        views.append(o)
clean_view = {(o["view"], o["task"], o["rep"]): o["code"] for o in views if o["view_of"] == "local3b"}
for v in ("strip", "san"):
    for k in ("local3b",) + tuple(f"local3b+inject_{x}" for x in INJECT):
        vs = [o for o in views if o["tier"] == f"{k}@{v}"]
        report[f"view|{k}@{v}"] = dict(rows=len(vs), changed=sum(o["view_changed"] for o in vs),
                                       same_as_clean_view=sum(o["code"] == clean_view.get((v, o["task"], o["rep"])) for o in vs))
with open(a.out, "w") as f: f.writelines(json.dumps(r) + "\n" for r in none + views)
json.dump(report, open(os.path.join(a.wd, "check.json"), "w"), indent=1)
print(f"{len(none)} none-view rows, {len(views)} defense-view rows -> {a.out}; verdict changes {bad}")
sys.exit(1 if bad else 0)

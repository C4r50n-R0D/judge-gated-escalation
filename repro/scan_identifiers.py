#!/usr/bin/env python3
"""Fail if the package holds network addresses, personal paths or credentials. Model-written code inside data rows is
reported separately, because benchmark tasks about IP addresses contain example addresses."""
import json, lzma, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(ROOT)
BAD = {"tailnet ip": r"\b100\.(6[4-9]|[7-9]\d|1[01]\d|12[0-7])\.\d{1,3}\.\d{1,3}\b", "private ip": r"\b(192\.168|10\.\d{1,3}|172\.(1[6-9]|2\d|3[01]))\.\d{1,3}\.\d{1,3}\b",
       "tailnet": r"(?i)tailscale|tailnet|\.ts\.net", "user path": r"carsonrodriguez|/home/carson|/Users/[a-z]", "email": r"[\w.+-]+@(gmail|icloud|outlook|proton)\.\w+",
       "ssh": r"\bssh\s+-|\bscp\s+", "mac address": r"\b([0-9a-f]{2}:){5}[0-9a-f]{2}\b", "key": r"sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9]{20,}|hf_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|BEGIN [A-Z ]*PRIVATE KEY|Bearer [A-Za-z0-9._-]{20,}"}
BAD = {k: re.compile(v) for k, v in BAD.items()}
hits = {}; code_hits = {}
CODE = ("code", "solution", "parent_code", "clean_code")
def scan(txt, where, sink):
    for k, rx in BAD.items():
        if k != "ssh" or not where.startswith("repro/scan"):
            for m in rx.finditer(txt): sink.setdefault(k, {}).setdefault(where, 0); sink[k][where] += 1
def row_scan(line, where):
    try: r = json.loads(line)
    except ValueError: scan(line, where, hits); return
    code = []
    def strip(o):
        if isinstance(o, dict): return {k: code.append(v) if k in CODE and isinstance(v, str) else strip(v) for k, v in o.items()}
        return [strip(v) for v in o] if isinstance(o, list) else o
    scan(json.dumps(strip(r)), where, hits); scan(" ".join(code), where, code_hits)
skip = {"repro/scan_identifiers.py", "CHECKSUMS.sha256"}
for d, ds, fs in os.walk("."):
    ds[:] = [x for x in ds if x not in (".git", "repro_out", "runs_unpacked", "__pycache__")]
    for f in fs:
        p = os.path.relpath(os.path.join(d, f), ".")
        if p in skip or p.endswith((".pdf", ".bundle")): continue
        if p.startswith("repro/pressure/stored/") and p.endswith(".json"): row_scan(open(p).read(), p)
        elif p.endswith(".xz") or p.endswith((".jsonl", "_eval_results.json")):
            op = lzma.open if p.endswith(".xz") else open
            with op(p, "rt", errors="replace") as h:
                for line in h: row_scan(line, p)
        else:
            try: scan(open(p, errors="strict").read(), p, hits)
            except UnicodeDecodeError: pass
print("FINDINGS OUTSIDE MODEL CODE:", json.dumps(hits, indent=1) if hits else "none")
print("inside model-written code (not personal; example addresses from benchmark tasks):", {k: sum(v.values()) for k, v in code_hits.items()})
sys.exit(1 if hits else 0)

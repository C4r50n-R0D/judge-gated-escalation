"""CLI for variant suites; see variants/__init__.py."""
import argparse, json, sys
import variants, evalplus_io

ap = argparse.ArgumentParser(prog="python3 -m variants"); ap.add_argument("cmd", choices=["build", "show", "selfcheck-rows", "list"])
ap.add_argument("name", nargs="?"); ap.add_argument("out", nargs="?")
ap.add_argument("--base"); ap.add_argument("--transform"); ap.add_argument("--seed", type=int, default=1)
ap.add_argument("--param", action="append", default=[], help="k=v, repeatable; values parsed as JSON when possible")
ap.add_argument("--split", default="cal", choices=["cal", "test", "all"]); ap.add_argument("--ids")
ap.add_argument("--allow-test", action="store_true", help="only after the confirmatory analysis (STOP C)")
a = ap.parse_args()
if a.cmd == "list": print(sorted(variants.TRANSFORMS)); sys.exit(0)
if a.cmd == "build":
    params = {}
    for kv in a.param:
        k, v = kv.split("=", 1)
        try: params[k] = json.loads(v)
        except ValueError: params[k] = v
    variants.build(a.name, a.base, a.transform, a.seed, params, a.split, a.ids.split(",") if a.ids else None, a.allow_test)
elif a.cmd == "show":
    m = variants.manifest(a.name); print(json.dumps({k: v for k, v in m.items() if k != "failures"}, indent=1))
    if m["failures"]: print("not transformed:", dict(list(m["failures"].items())[:10]))
elif a.cmd == "selfcheck-rows":
    evalplus_io.selfcheck_rows(f"variant:{a.name}", a.out)

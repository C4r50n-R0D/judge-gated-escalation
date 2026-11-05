#!/usr/bin/env bash
# End-to-end on mock servers (no hardware, no spend): generate -> judge (tev, llama, selfconf) -> calibrate -> test -> power.
set -euo pipefail
cd "$(dirname "$0")/.."
W=$(mktemp -d); trap 'kill $(jobs -p) 2>/dev/null || true; rm -rf "$W"' EXIT
export BENCH_ALLOW_UNSANDBOXED=1   # mock code only
python3 mock_ollama.py 8101 0.55 & python3 mock_ollama.py 8102 0.85 & sleep 1
python3 - "$W/config.json" <<'PY'
import json, sys
c = json.load(open("config.example.json"))
c["suites"] = ["own"]
c.pop("cooldown", None)   # the mock decodes at a fixed 20 tok/s; real reference speeds would trigger pauses
c["judge_cache_dir"] = sys.argv[1].replace("config.json", "jcache")
for t in c["tiers"]:
    t["base_url"] = "http://127.0.0.1:8102" if t["name"] == "strong14b" else "http://127.0.0.1:8101"   # strong mock is better
    t.pop("subset_fraction", None)
c["judges"]["tev"]["base_url"] = "http://127.0.0.1:8101"
json.dump(c, open(sys.argv[1], "w"))
PY
python3 bench.py validate own
python3 bench.py run "$W/config.json" "$W/raw.jsonl" > "$W/run.log"
python3 bench.py run "$W/config.json" "$W/raw.jsonl" > "$W/run2.log"   # resume: must add nothing
python3 - "$W/raw.jsonl" <<'PY' || { echo "resume/dup check failed"; exit 1; }
import json, sys
rows = [r for r in map(json.loads, open(sys.argv[1])) if "_meta" not in r]
keys = [(r["tier"], r["task"], r["rep"]) for r in rows]
cfg = json.load(open(sys.argv[1].replace("raw.jsonl", "config.json")))
planned = 10 * sum(t["draws"] for t in cfg["tiers"] if t.get("role", "generator") == "generator")
assert len(keys) == len(set(keys)) == planned, (len(keys), len(set(keys)), planned)
batches = [r["_meta"]["batch"] for r in map(json.loads, open(sys.argv[1])) if "batch" in r.get("_meta", {})]
assert batches and {b["tier"] for b in batches} == {t["name"] for t in cfg["tiers"] if t.get("role", "generator") == "generator"}, batches[:3]
assert all(r.get("wall_s_net") is not None and r.get("params_b") and r.get("ts") for r in rows), "missing timing/compute fields"
assert not any(r.get("error") for r in rows), [r["error"] for r in rows if r.get("error")][:3]
PY
python3 -c "import json,sys; c=json.load(open(sys.argv[1])); c['tiers'][0]['temperature']=0.2; json.dump(c,open(sys.argv[2],'w'))" "$W/config.json" "$W/config_changed.json"
if python3 bench.py run "$W/config_changed.json" "$W/raw.jsonl" > /dev/null 2>&1; then echo "mixed-conditions guard failed"; exit 1; fi
python3 judge_label.py "$W/raw.jsonl" "$W/config.json" tev "$W/l1.jsonl" --tiers local3b
python3 judge_label.py "$W/l1.jsonl" "$W/config.json" llama "$W/l2.jsonl" --tiers local3b
python3 judge_label.py "$W/l2.jsonl" "$W/config.json" selfconf "$W/labeled.jsonl" --tiers local3b
python3 judge_label.py "$W/labeled.jsonl" "$W/config.json" llama "$W/labeled_all.jsonl" --tiers local3b,local1p5b,local7b,strong14b
# cache is per judge, not per output file: relabeling local drafts into a new file must cost nothing new
python3 judge_label.py "$W/raw.jsonl" "$W/config.json" llama "$W/again.jsonl" --tiers local3b | tee "$W/again.log"
grep -q "(0 new" "$W/again.log" || { echo "judge cache reuse failed"; exit 1; }
python3 suites.py manifest own "$W/manifest.json"
python3 tools/derived_judges.py "$W/labeled.jsonl" "$W/derived.jsonl" --base tev,llama,selfconf --tiers local3b --fits "$W/fits.json" \
  || { echo "(derived judges: the mock suite has too few calibration rows; acceptable)"; cp "$W/labeled.jsonl" "$W/derived.jsonl"; }
python3 controllers.py explore "$W/labeled.jsonl" --mc 50 > "$W/explore.txt"
python3 controllers.py calibrate "$W/labeled.jsonl" --out "$W/thresholds.json" --mc 100 --primary-judge llama --manifest "$W/manifest.json"
python3 controllers.py test "$W/labeled.jsonl" --thresholds "$W/thresholds.json" --report "$W/report.md" --json "$W/results.json" --boots 300 --two-stage 30 --manifest "$W/manifest.json"
if python3 controllers.py test "$W/labeled.jsonl" --thresholds "$W/thresholds.json" --k 2 --report /dev/null --json /dev/null >/dev/null 2>&1; then echo "frozen-parameter guard failed"; exit 1; fi
# changing calibration data after the freeze must be refused
python3 -c "
import json,sys
rows=[json.loads(l) for l in open(sys.argv[1])]
for r in rows:
    if r.get('split')=='cal' and r.get('tier')=='local3b' and 'hidden_passed' in r: r['hidden_passed']=not r['hidden_passed']; break
open(sys.argv[2],'w').write(''.join(json.dumps(r)+'\n' for r in rows))" "$W/labeled.jsonl" "$W/tampered.jsonl"
if python3 controllers.py test "$W/tampered.jsonl" --thresholds "$W/thresholds.json" --report /dev/null --json /dev/null >/dev/null 2>&1; then echo "calibration-hash guard failed"; exit 1; fi
python3 power.py pilot "$W/labeled.jsonl" --judge llama --n-test 390 --mc 100
python3 judge.py selftest "$W/config.json" tev | head -4
python3 judge.py selftest "$W/config.json" llama | head -4
grep -q '"lp_mean": -' "$W/raw.jsonl" || { echo "generation log-probabilities not recorded"; exit 1; }
grep -q '"cost_metric": "tok"' "$W/thresholds.json" || { echo "cost metric (token-compute) not frozen in thresholds"; exit 1; }
grep -q '"secondary_cost_metric": "sec"' "$W/thresholds.json" || { echo "secondary cost metric not recorded"; exit 1; }
grep -q "^## S1 " "$W/report.md" && grep -q "^## S2 " "$W/report.md" || { echo "secondary comparisons S1/S2 missing from report"; exit 1; }
grep -q 'token-compute/task' "$W/report.md" || { echo "token-compute column missing from report"; exit 1; }
# experiment runner (T22): refuses uncommitted specs, runs steps in order, resumes, counts comparisons
X="$W/xrepo"; mkdir -p "$X/tools" && cp tools/exprun.py "$X/tools/" && (cd "$X" && git init -q && git -c user.email=t@t -c user.name=t commit -q --allow-empty -m init)
python3 "$X/tools/exprun.py" new EX --title "runner test" > /dev/null
python3 - "$X/ext/EX/spec.json" <<'PY2'
import json, sys
s = json.load(open(sys.argv[1]))
s["steps"] = [{"name": "one", "cmd": "echo one > ext/EX/one.txt"}, {"name": "two", "cmd": "test -f ext/EX/allow_two && echo two > ext/EX/two.txt"}]
s["comparisons"] = [{"name": "a vs b", "metric": "AUROC", "conditions": ["a", "b"], "status": "planned"}]
json.dump(s, open(sys.argv[1], "w"))
PY2
if python3 "$X/tools/exprun.py" run EX > /dev/null 2>&1; then echo "runner ran an uncommitted spec"; exit 1; fi
(cd "$X" && git add ext && git -c user.email=t@t -c user.name=t commit -q -m spec)
if python3 "$X/tools/exprun.py" run EX > /dev/null 2>&1; then echo "runner did not stop on a failing step"; exit 1; fi
test -f "$X/ext/EX/one.txt" || { echo "runner step one missing"; exit 1; }
rm "$X/ext/EX/one.txt"; touch "$X/ext/EX/allow_two"
python3 "$X/tools/exprun.py" run EX > "$W/xrun.log"; grep -q "skip full:one" "$W/xrun.log" || { echo "runner did not resume past the finished step"; exit 1; }
test -f "$X/ext/EX/two.txt" && ! test -f "$X/ext/EX/one.txt" || { echo "runner resume wrong"; exit 1; }
python3 "$X/tools/exprun.py" comparisons > /dev/null && grep -q "Total: 1 (0 reported, 1 planned)" "$X/ext/COMPARISONS.md" || { echo "comparison counter wrong"; exit 1; }
cp "$W/report.md" tests/last_mock_report.md
echo "PIPELINE OK (mock results are meaningless; see tests/last_mock_report.md for the report format)"

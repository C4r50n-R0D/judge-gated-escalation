#!/bin/sh
# One entry point for every check. See README.md. Nothing here uses a network except `fetch` and Docker's first build.
set -eu
cd "$(dirname "$0")/.."
PY=${PYTHON:-python3}
case "${1:-help}" in
  setup)      $PY repro/setup.py;;   # verify checksums and unpack the stored data into runs/
  fetch)      # the two benchmark files, pinned by sha256 (needed by `repeat` and `rescore`)
    $PY repro/fetch_suites.py;;
  confirm)    # frozen analysis, about 2 minutes
    mkdir -p repro_out
    $PY controllers.py test runs/confirmatory.labeled.jsonl --thresholds thresholds.json --manifest split_manifest.json --report repro_out/T26_report.md --json repro_out/T26_results.json
    grep -v "two-stage bootstrap" runs/T26_report.md > repro_out/.ref; diff repro_out/T26_report.md repro_out/.ref && echo "CONFIRMED: report identical to runs/T26_report.md (two-stage line excluded)";;
  thresholds) # re-derive the frozen thresholds from calibration data, about 40 minutes
    mkdir -p repro_out
    $PY controllers.py calibrate runs/confirmatory.labeled.jsonl --manifest split_manifest.json --out repro_out/thresholds.json --report repro_out/cal.md --json repro_out/cal.json --cost-metric tok --primary-judge tev
    $PY -c "import json;a=json.load(open('repro_out/thresholds.json'))['taus'];b=json.load(open('thresholds.json'))['taus'];print('CONFIRMED: thresholds identical' if a==b else 'DIFFERENT',a,b)";;
  independent) # separate code, exact expectations
    $PY repro/independent_recompute.py;;
  exploratory) shift; $PY repro/exploratory.py "$@";;
  pressure)   # post hoc reanalysis, about a minute; needs numpy, and `fetch` first
    W=$(pwd)/repro_out/pressure; mkdir -p "$W"; cp thresholds.json runs/confirmatory.labeled.jsonl runs/test_power.json runs/eval/*_eval_results.json data/*.jsonl.gz repro/pressure/*.py repro/pressure/stored/*_out.json "$W"; cd "$W"
    for s in pressure pressure2 pressure3 pressure4 backtest; do $PY $s.py > $s.out; cmp $s.out ../../repro/pressure/stored/$s.out && echo "CONFIRMED: $s.out identical"; done;;
  tests)      $PY tests/test_units.py;;
  rescore)    # official scorer on a random sample, in a container with no network
    N=${2:-500}; V=$(pwd)/repro_out/rescore; mkdir -p "$V"; $PY repro/rescore_sample.py --export "$V" "$N"
    EV="docker run --rm --network none --memory 6g -e EVALPLUS_MAX_MEMORY_BYTES=8589934592 -v $V:/app -v evalplus-cache:/root/.cache/evalplus evalplus:0.3.1 evalplus.evaluate --parallel 1"
    $EV --dataset humaneval --samples /app/he.jsonl > "$V/he.log" 2>&1; $EV --dataset mbpp --samples /app/mb.jsonl > "$V/mb.log" 2>&1
    $PY repro/rescore_sample.py --compare "$V" "$N";;
  repeat)     shift; $PY repro/repeat_check.py "$@";;
  scan)       $PY repro/scan_identifiers.py;;
  *) sed -n 1,3p "$0"; echo "usage: repro/run.sh setup|fetch|confirm|thresholds|independent|exploratory|pressure|tests|rescore|repeat|scan";;
esac

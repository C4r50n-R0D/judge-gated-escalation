#!/bin/bash
# EvalPlus selfcheck of one variant suite (KICKOFF2 T17): canonical (possibly transformed) references must pass the
# unchanged hidden tests and stubs must fail. Records the result in the variant manifest. Runs on the homelab.
#   tools/variant_selfcheck.sh NAME
set -euo pipefail
cd "$(dirname "$0")/.."; N=$1
base=$(python3 -c "import variants,sys; print(variants.manifest(sys.argv[1])['definition']['base'])" "$N")
ds=$(python3 -c "import suites,sys; print(suites.EVALPLUS_NAME[sys.argv[1]])" "$base")
D=runs/eval/variants/$N; mkdir -p "$D"; rm -f "$D"/sc*
python3 -m variants selfcheck-rows "$N" "$D/rows.jsonl"
python3 evalplus_io.py export "$D/rows.jsonl" "variant:$N" "$D/sc.jsonl"
docker run --rm --network none --memory 6g -e EVALPLUS_MAX_MEMORY_BYTES=8589934592 -v "$PWD/$D:/app" \
  -v evalplus-cache:/root/.cache/evalplus evalplus:0.3.1 evalplus.evaluate --dataset "$ds" --samples /app/sc.jsonl --parallel 1 > "$D/evalplus.log" 2>&1
python3 evalplus_io.py import "$D/rows.jsonl" "variant:$N" "$D/sc.jsonl" "$D/sc_eval_results.json" "$D/scored.jsonl"
if out=$(python3 evalplus_io.py selfcheck-verify "$D/scored.jsonl" --allow-known 2>&1); then ok=true; else ok=false; fi
echo "$out"
python3 -c "import variants,sys,json; variants.record_verification(sys.argv[1], 'selfcheck', {'ok': sys.argv[2]=='true', 'summary': sys.argv[3]})" "$N" "$ok" "$(echo "$out" | head -2 | tr '\n' ' ')"
$ok

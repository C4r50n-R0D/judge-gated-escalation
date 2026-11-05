#!/bin/sh
# Mac power and thermal log for collection runs (PREREG section 3). Run ON THE MAC, next to Ollama:
#   sh tools/hwlog_mac.sh runs/hwlog_mac.jsonl [interval_s]
# Appends one JSON line per interval: UTC time, power source, battery percent, and pmset's thermal and performance
# warning levels ("none" when macOS has recorded no warning). Copy the file to the homelab's runs/ after a stage and
# join it to draws by time with tools/hwjoin.py. No sudo needed.
out=${1:-hwlog_mac.jsonl}; iv=${2:-30}
while :; do
  b=$(pmset -g batt)
  src=$(printf '%s' "$b" | sed -n "s/.*drawing from '\([^']*\)'.*/\1/p" | head -1)
  pct=$(printf '%s' "$b" | grep -o '[0-9]*%' | head -1 | tr -d %)
  t=$(pmset -g therm)
  tw=$(printf '%s' "$t" | sed -n 's/.*CPU_Thermal_level[^0-9]*\([0-9]*\).*/\1/p; s/.*thermal warning level[^0-9]*\([0-9]*\).*/\1/p' | head -1)
  pw=$(printf '%s' "$t" | sed -n 's/.*performance warning level[^0-9]*\([0-9]*\).*/\1/p' | head -1)
  printf '{"ts": "%s", "power": "%s", "battery_pct": %s, "thermal_warning": "%s", "performance_warning": "%s"}\n' \
    "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$src" "${pct:-null}" "${tw:-none}" "${pw:-none}" >> "$out"
  sleep "$iv"
done

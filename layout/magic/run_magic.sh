#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
if ! command -v magic >/dev/null 2>&1; then
  echo "magic not found; using Python GDS (layout/gds/*.gds already from build_gds.py)"
  exit 0
fi
mkdir -p layout/gds layout/magic
for tcl in sample_hold r2r_dac comparator sar_adc_analog sar_adc_top; do
  echo "Magic $tcl"
  magic -dnull -noconsole layout/magic/${tcl}.tcl || true
done

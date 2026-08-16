#!/usr/bin/env bash
# Magic+netgen analog LVS when tools exist.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/layout/env.sh"
REP="$ROOT/layout/reports"
mkdir -p "$REP"

if [[ ! -f "${MAGICRC:-}" ]]; then
  echo "MAGICRC missing; PDK magicrc not found" | tee "$REP/lvs_analog.txt"
fi

if ! command -v magic >/dev/null 2>&1; then
  echo "magic not installed — analog LVS skipped (install Magic against sky130A.magicrc)" | tee "$REP/lvs_analog.txt"
  echo "netgen: ${NETGEN:-not found}" | tee -a "$REP/lvs_analog.txt"
  echo "Spice golden: spice/sar_adc_analog_sky130.spice" | tee -a "$REP/lvs_analog.txt"
  exit 0
fi

magic -rcfile "$MAGICRC" -dnull -noconsole <<'EOF'
load layout/magic/sar_adc_analog
extract do local
extract all
ext2spice lvs
ext2spice
quit -noprompt
EOF

if command -v netgen >/dev/null 2>&1; then
  netgen -batch lvs \
    "sar_adc_analog.spice sar_adc_analog" \
    "$ROOT/spice/sar_adc_analog_sky130.spice sar_adc_analog_sky130" \
    "$PDK_ROOT/sky130A/libs.tech/netgen/sky130A_setup.tcl" \
    "$REP/lvs_analog.txt"
else
  echo "netgen not found" | tee "$REP/lvs_analog.txt"
fi

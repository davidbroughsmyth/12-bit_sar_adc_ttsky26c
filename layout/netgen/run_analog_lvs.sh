#!/usr/bin/env bash
# Per-cell Magic DRC/extract + netgen LVS for analog gencells.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/layout/env.sh"
REP="$ROOT/layout/reports"
mkdir -p "$REP"
cd "$ROOT"

IMAGE="${OPENLANE_IMAGE:-efabless/openlane:9dbd8b5ea2bd891bed4dcc97df5c7439083f0368-arm64v8}"
SETUP="${PDK_ROOT}/sky130A/libs.tech/netgen/sky130A_setup.tcl"

: > "$REP/magic_analog_check.log"
for cell in sample_hold comparator r2r_dac; do
  ANALOG_CELL=$cell bash "$ROOT/layout/magic/run_magic.sh" layout/magic/check_analog.tcl \
    | tee -a "$REP/magic_analog_check.log"
done

lvs_one() {
  local cell="$1"
  local subckt="$2"
  local spice="$3"
  local out="$REP/${cell}_lvs.txt"
  if command -v netgen >/dev/null 2>&1 && [[ -f "$SETUP" ]]; then
    netgen -batch lvs \
      "$REP/${cell}_ext.spice $cell" \
      "$spice $subckt" \
      "$SETUP" "$out" || true
  elif command -v docker >/dev/null 2>&1; then
    docker run --rm --platform linux/arm64 \
      -v "$ROOT":/work -v "${PDK_ROOT}":/pdk -w /work \
      -e PDK_ROOT=/pdk \
      "$IMAGE" \
      netgen -batch lvs \
        "/work/layout/reports/${cell}_ext.spice $cell" \
        "/work/$spice $subckt" \
        /pdk/sky130A/libs.tech/netgen/sky130A_setup.tcl \
        "/work/layout/reports/${cell}_lvs.txt" || true
  else
    echo "netgen not found" | tee "$out"
  fi
  echo "LVS $cell -> $out"
}

lvs_one sample_hold sample_hold_sky130 spice/sample_hold_sky130.spice
lvs_one comparator comparator_sky130 spice/comparator_sky130.spice
lvs_one r2r_dac r2r_dac_sky130 spice/r2r_dac_sky130.spice
echo "reports in $REP"

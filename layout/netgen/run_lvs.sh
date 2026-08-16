#!/usr/bin/env bash
# Magic extract + netgen analog LVS. Uses Docker when tools are missing.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/layout/env.sh"
REP="$ROOT/layout/reports"
mkdir -p "$REP"
cd "$ROOT"

IMAGE="${OPENLANE_IMAGE:-efabless/openlane:9dbd8b5ea2bd891bed4dcc97df5c7439083f0368-arm64v8}"
SPICE_LAY="$ROOT/spice/sar_adc_analog_sky130.spice"
SETUP="${PDK_ROOT}/sky130A/libs.tech/netgen/sky130A_setup.tcl"

extract_cmd() {
  magic -rcfile "$1" -dnull -noconsole <<'EOF'
load layout/magic/tt_um_davidbroughsmyth_sar_adc
extract do local
extract all
ext2spice lvs
ext2spice
quit -noprompt
EOF
}

if command -v magic >/dev/null 2>&1; then
  extract_cmd "$MAGICRC" || true
elif command -v docker >/dev/null 2>&1; then
  echo "magic via docker $IMAGE"
  docker run --rm --platform linux/arm64 \
    -v "$ROOT":/work -v "${PDK_ROOT}":/pdk -w /work \
    -e PDK_ROOT=/pdk -e PDK=sky130A \
    "$IMAGE" \
    magic -rcfile /pdk/sky130A/libs.tech/magic/sky130A.magicrc -dnull -noconsole layout/magic/tt_tile.tcl \
    | tee "$REP/magic_extract.log" || true
else
  echo "magic not installed — analog LVS skipped" | tee "$REP/lvs_analog.txt"
  exit 0
fi

NETGEN_BIN="$(command -v netgen || true)"
if [[ -z "$NETGEN_BIN" ]] && command -v docker >/dev/null 2>&1; then
  docker run --rm --platform linux/arm64 \
    -v "$ROOT":/work -v "${PDK_ROOT}":/pdk -w /work \
    -e PDK_ROOT=/pdk \
    "$IMAGE" \
    netgen -batch lvs \
      "tt_um_davidbroughsmyth_sar_adc.spice tt_um_davidbroughsmyth_sar_adc" \
      "/work/spice/sar_adc_analog_sky130.spice sar_adc_analog_sky130" \
      /pdk/sky130A/libs.tech/netgen/sky130A_setup.tcl \
      /work/layout/reports/lvs_analog.txt || true
elif [[ -n "$NETGEN_BIN" && -f "$SETUP" ]]; then
  netgen -batch lvs \
    "tt_um_davidbroughsmyth_sar_adc.spice tt_um_davidbroughsmyth_sar_adc" \
    "$SPICE_LAY sar_adc_analog_sky130" \
    "$SETUP" \
    "$REP/lvs_analog.txt" || true
else
  echo "netgen not found" | tee -a "$REP/lvs_analog.txt"
fi

[[ -f "$REP/lvs_connectivity.txt" ]] && cat "$REP/lvs_connectivity.txt" >> "$REP/lvs_analog.txt" || true
echo "LVS report: $REP/lvs_analog.txt"

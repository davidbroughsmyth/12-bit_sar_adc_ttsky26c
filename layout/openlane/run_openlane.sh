#!/usr/bin/env bash
# Harden sar_adc_digital_tt with OpenLane (Docker image).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/layout/env.sh" || true
DESIGN="$ROOT/layout/openlane/sar_adc_digital"
IMAGE="${OPENLANE_IMAGE:-efabless/openlane:9dbd8b5ea2bd891bed4dcc97df5c7439083f0368-arm64v8}"

if command -v docker >/dev/null 2>&1; then
  docker run --rm --platform linux/arm64 \
    -v "${PDK_ROOT}":/pdk -v "$ROOT":/work \
    -e PDK_ROOT=/pdk -e PDK=sky130A -e OPENLANE_ROOT=/openlane \
    "$IMAGE" \
    flow.tcl -design /work/layout/openlane/sar_adc_digital -overwrite -tag sar
  cp "$DESIGN/runs/sar/results/final/gds/sar_adc_digital_tt.gds" "$ROOT/layout/gds/sar_adc_digital.gds"
  exit 0
fi
echo "docker not available"
exit 1

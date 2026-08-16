#!/usr/bin/env bash
# Harden sar_adc_digital with OpenLane if PDK + flow are installed.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/layout/env.sh" || true
DESIGN_DIR="$ROOT/layout/openlane/sar_adc_digital"
OUT_GDS="$ROOT/layout/gds/sar_adc_digital.gds"

if [[ -x "${OPENLANE_ROOT:-}/flow.tcl" ]]; then
  echo "Running OpenLane 1 flow.tcl"
  cd "$OPENLANE_ROOT"
  ./flow.tcl -design "$DESIGN_DIR"
  FIND=$(find "$DESIGN_DIR/runs" -name 'sar_adc_digital.gds' | tail -1)
  cp "$FIND" "$OUT_GDS"
  exit 0
fi

if command -v openlane >/dev/null 2>&1; then
  echo "Running OpenLane 2 CLI"
  openlane --run-tag sar "$DESIGN_DIR/config.json"
  exit 0
fi

if command -v docker >/dev/null 2>&1 && docker image inspect efabless/openlane:latest >/dev/null 2>&1; then
  echo "OpenLane docker image present but PDK_ROOT=$PDK_ROOT"
  echo "Mount PDK and re-run. Falling back to scripted GDS."
fi

echo "OpenLane/PDK not available — using layout/build_gds.py digital macro"
"$ROOT/.venv/bin/python" "$ROOT/layout/build_gds.py"
exit 0

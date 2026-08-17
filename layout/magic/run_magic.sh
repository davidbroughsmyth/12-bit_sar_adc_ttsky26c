#!/usr/bin/env bash
# Run Magic against sky130A. Uses Docker (efabless/openlane) if magic is not on PATH.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
# shellcheck disable=SC1091
source "$ROOT/layout/env.sh"

IMAGE="${OPENLANE_IMAGE:-efabless/openlane:9dbd8b5ea2bd891bed4dcc97df5c7439083f0368-arm64v8}"
TCL="${1:-layout/magic/tt_tile.tcl}"

run_local() {
  magic -rcfile "$MAGICRC" -dnull -noconsole "$TCL"
}

run_docker() {
  docker run --rm \
    --platform linux/arm64 \
    -v "$ROOT":/work \
    -v "${PDK_ROOT}":/pdk \
    -w /work \
    -e PDK_ROOT=/pdk \
    -e PDK=sky130A \
    -e ANALOG_CELL="${ANALOG_CELL:-}" \
    "$IMAGE" \
    magic -rcfile /pdk/sky130A/libs.tech/magic/sky130A.magicrc -dnull -noconsole "$TCL"
}

if command -v magic >/dev/null 2>&1; then
  run_local
elif command -v docker >/dev/null 2>&1; then
  echo "magic not on PATH; using $IMAGE"
  run_docker
else
  echo "magic not found; using Python GDS (layout/build_tt_gds.py)"
  exit 0
fi

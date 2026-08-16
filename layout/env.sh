# Sky130 + Tiny Tapeout layout environment
export REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export LAYOUT_ROOT="${REPO_ROOT}/layout"

# Local volare install (sky130A already present on this machine)
if [[ -d "${HOME}/.volare/sky130A" ]]; then
  export PDK_ROOT="${PDK_ROOT:-${HOME}/.volare}"
fi
export PDK_ROOT="${PDK_ROOT:-${HOME}/pdk}"
export PDK="${PDK:-sky130A}"
export PDK_NGSPICE="${PDK_ROOT}/${PDK}/libs.tech/ngspice/sky130.lib.spice"
export MAGICRC="${PDK_ROOT}/${PDK}/libs.tech/magic/${PDK}.magicrc"
export STD_CELL_LIBRARY="${STD_CELL_LIBRARY:-sky130_fd_sc_hd}"
export OPENLANE_ROOT="${OPENLANE_ROOT:-${HOME}/OpenLane}"

if command -v magic >/dev/null 2>&1; then export MAGIC="$(command -v magic)"; fi
if command -v netgen >/dev/null 2>&1; then export NETGEN="$(command -v netgen)"; fi
if command -v klayout >/dev/null 2>&1; then export KLAYOUT="$(command -v klayout)"; fi
if command -v xschem >/dev/null 2>&1; then export XSCHEM="$(command -v xschem)"; fi

echo "REPO_ROOT=$REPO_ROOT"
echo "PDK_ROOT=$PDK_ROOT  PDK=$PDK"
echo "PDK_NGSPICE=${PDK_NGSPICE}"
echo "MAGICRC=${MAGICRC}"
echo "magic=${MAGIC:-not found}  netgen=${NETGEN:-not found}  klayout=${KLAYOUT:-not found}"

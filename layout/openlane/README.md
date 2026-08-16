# LibreLane / OpenLane2 digital harden inside TT flow (not a standalone chip).
# Run when LibreLane is installed:
#   pip install librelane
#   librelane layout/openlane/sar_adc_digital/config.json
#
# Tiny Tapeout analog shuttles use custom_gds (this repo's gds/tt_um_davidbroughsmyth_sar_adc.gds).
# Digital P&R is optional for mixed-signal: analog is Magic; digital may be
# placed as a hardened macro or included in the custom GDS.
echo "LibreLane not required for custom_gds submit; GitHub tt-gds-action/custom_gds@ttsky26c runs precheck."

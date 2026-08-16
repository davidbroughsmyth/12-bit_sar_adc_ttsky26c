# Tiny Tapeout submit

1. Push this repo to GitHub (enable Actions). Workflows:
   - `.github/workflows/gds.yaml` — `custom_gds` + **precheck** (`ttsky26c`)
   - `.github/workflows/docs.yaml` — datasheet
2. Confirm `gds/tt_um_davidbroughsmyth_sar_adc.gds` and `lef/tt_um_davidbroughsmyth_sar_adc.lef` match the 2x2 3v3 DEF pins (`met4.pin` 71/16), include LEF `VGND`/`VDPWR`/`VAPWR`, and wire `ua[0]`/`ua[1]` into analog metal.
3. Magic analog extract: `make tt-magic` then `make lvs` (Docker OpenLane image if `magic` is not on PATH).
4. When precheck is green: https://app.tinytapeout.com/ — pick an **analog-capable SKY130 shuttle**, paste the repo URL.
5. Do **not** submit `layout/gds/sar_adc_top.gds` (private padframe sketch).

PDK sim: `source layout/env.sh && python3 tb/spice/run_pdk_tests.py`

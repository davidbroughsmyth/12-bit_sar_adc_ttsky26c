# Tiny Tapeout submit

1. Push this repo to GitHub (enable Actions). Workflows:
   - `.github/workflows/gds.yaml` — `custom_gds` + **precheck** (`ttsky26c`)
   - `.github/workflows/docs.yaml` — datasheet
2. Confirm `gds/tt_um_davidbroughsmyth_sar_adc.gds` and `lef/tt_um_davidbroughsmyth_sar_adc.lef` match the 2x2 3v3 DEF pins.
3. When precheck is green: https://app.tinytapeout.com/ — pick an **analog-capable SKY130 shuttle**, paste the repo URL.
4. Do **not** submit `layout/gds/sar_adc_top.gds` (private padframe sketch).

Magic/netgen LVS: `bash layout/netgen/run_lvs.sh` after installing Magic.
PDK sim: `source layout/env.sh && python3 tb/spice/run_pdk_tests.py`

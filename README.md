# 12-bit Sky130 SAR ADC (500 SPS)

Successive-approximation ADC for ECG-class signals after an AD8232-like AFE.

| Item | Value |
|------|--------|
| Resolution | 12 bit |
| Throughput | 500 SPS |
| `clk` | 50 MHz |
| `rst_n` | active-low |
| Sample period | 100 000 clocks |
| Bit-trial clock | 20 kHz (`clk` / 2500, ~50 µs/bit) |
| Analog pads | `vin_ecg`, `vref` (3.3 V) |
| Digital out | `adc[11:0]`, `sample_en` (high while tracking) |
| LSB | 3.3 V / 4096 ≈ 0.806 mV |

R-2R matching in Sky130 typically limits true linearity below 12 bit; benches report INL/DNL honestly.

## Clocking

```
clk 50 MHz
  ├─ rate_divider SAMPLE_DIV=100000 → sample_tick @ 500 Hz
  └─ rate_divider SAR_DIV=2500    → sar_clk_en @ 20 kHz
SAR: TRACK (sample_en=1) → 12 bit trials MSB-first → UPDATE (adc, eoc)
```

Conversion ≈ 14 × 50 µs ≈ 0.7 ms, then idle until the next sample.

## Tree

```
rtl/                 Verilog: rate_divider, sar_fsm, sar_adc_digital, chip wrapper
tb/rtl/              Icarus tests (divider, reset, golden sweep, timing)
spice/               Behavioral analog + Sky130 transistor netlists
tb/spice/            ngspice benches + Python runner
sim/                 Golden SAR, waveforms, MIT-BIH / AD8232
models/ad8232/       AFE parameters
layout/              OpenLane + Magic scripts, Sky130 GDS
```

## Run tests

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Verilog (Icarus)
make rtl-test

# SPICE (ngspice; no PDK required for behavioral netlists)
make spice-test
make -C tb/spice          # optional raw .spice benches

# Sine / spike / ramp + synthetic AAMI 5-class
make waves

# PhysioNet MIT-BIH 1.0.0 (records 100, 209, 200, 208, 217)
make mitbih
```

Set `PDK_ROOT` to your `open_pdks` Sky130 install and `.include` `spice/include/sky130_setup.spice` plus `spice/*_sky130.spice` for transistor-level analog.

## Pins (`sar_adc_digital`)

- `clk`, `rst_n`, `comp_p`
- `adc[11:0]`, `sample_en`, `dac[11:0]`, `eoc`

Analog top (`spice/sar_adc_analog.spice`): `vin_ecg`, `vref`, `sample_en`, `dac[11:0]`, `comp_p`.

Chip wrapper [`rtl/sar_adc_chip.v`](rtl/sar_adc_chip.v) instantiates digital + analog blackbox [`rtl/sar_adc_analog.v`](rtl/sar_adc_analog.v).

## Layout / GDS (Sky130 mixed-signal)

First-cut GDS (Sky130 layer map). Digital is a stdcell-row macro with OpenLane pin order (west analog, east ADC, south clocks). Analog is scripted S/H + R-2R + comparator. Top GDS places analog west of digital, routes `dac[11:0]`/`comp_p`, and adds pads (`vin_ecg`, `vref`, `clk`, `rst_n`, `adc[11:0]`, `sample_en`, supplies).

```bash
source layout/env.sh
make gds
```

| File | What |
|------|------|
| [`layout/gds/sar_adc_top.gds`](layout/gds/sar_adc_top.gds) | Full chip |
| [`layout/gds/sar_adc_digital.gds`](layout/gds/sar_adc_digital.gds) | Digital macro |
| [`layout/gds/sar_adc_analog.gds`](layout/gds/sar_adc_analog.gds) | Analog macro |
| [`layout/gds/sample_hold.gds`](layout/gds/sample_hold.gds) | S/H |
| [`layout/gds/r2r_dac.gds`](layout/gds/r2r_dac.gds) | R-2R DAC |
| [`layout/gds/comparator.gds`](layout/gds/comparator.gds) | Comparator |
| [`layout/lef/sar_adc_digital.lef`](layout/lef/sar_adc_digital.lef) | Digital abstract |
| [`layout/reports/drc_summary.txt`](layout/reports/drc_summary.txt) | Width DRC |

OpenLane (when `PDK_ROOT` + OpenLane exist): `make layout-digital` uses [`layout/openlane/sar_adc_digital/config.json`](layout/openlane/sar_adc_digital/config.json) (`CLOCK_PERIOD` 20 ns). Magic TCL: [`layout/magic/`](layout/magic/). View: `python3 layout/klayout/view_top.py`.

This is **not** foundry signoff (no padframe legalization, antenna, or extracted analog LVS until Magic/netgen + PDK).

## Tiny Tapeout

Do **not** submit `layout/gds/sar_adc_top.gds`. Submit the TT tile:

- Wrapper: [`rtl/tt_um_davidbroughsmyth_sar_adc.v`](rtl/tt_um_davidbroughsmyth_sar_adc.v) / [`src/project.v`](src/project.v)
- Pins: [`info.yaml`](info.yaml) — `ua[0]=vin_ecg`, `ua[1]=vref`, 12-bit `adc` on `uo`/`uio`, `uses_vapwr: true`, tiles `2x2`
- GDS/LEF from official DEF: [`gds/tt_um_davidbroughsmyth_sar_adc.gds`](gds/tt_um_davidbroughsmyth_sar_adc.gds), [`lef/tt_um_davidbroughsmyth_sar_adc.lef`](lef/tt_um_davidbroughsmyth_sar_adc.lef)
- CI: [`.github/workflows/gds.yaml`](.github/workflows/gds.yaml) (`tt-gds-action/custom_gds@ttsky26c` + precheck)

```bash
source layout/env.sh          # PDK_ROOT=$HOME/.volare (sky130A)
make pdk-test                 # PDK ngspice (nFET + R-2R ~1.64 V at code 2048)
make tt-gds
make lvs                      # Magic/netgen when installed
```

Submit: [docs/tapeout.md](docs/tapeout.md) → https://app.tinytapeout.com/ (analog SKY130 shuttle).

## AD8232 / MIT-BIH

Input is modeled as a SparkFun AD8232-like path (3.3 V, mid-rail, gain ~1100, ~0.5–40 Hz), not a full AD8232 transistor netlist.

MIT-BIH AAMI classes: **N** SVEB **S** VEB **V** fusion **F** unknown **Q**. Records used when downloading: 100, 209, 200, 208, 217. Waveforms are not vendored; CI uses synthetic beats in `sim/mitbih.py`.

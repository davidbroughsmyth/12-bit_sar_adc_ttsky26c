# Tiny Tapeout 12-bit SAR ADC

Mixed-signal 12-bit successive-approximation ADC for an **off-chip** AD8232-like ECG front-end. 2×2 tile, analog on VAPWR (3.3 V), digital on VDPWR (1.8 V).

## How to test

1. Drive `ua[0]` (`vin_ecg`) with 0–3.3 V analog (mid-rail ~1.65 V for ECG). Do not expect a 12-bit-linear R-2R; ENOB is matching-limited.
2. Tie `ua[1]` (`vref`) to 3.3 V analog reference (same domain as VAPWR).
3. Clock `clk` at up to 50 MHz (`rst_n` active-low). `ena` must be 1.
4. Read `uo_out[7:0]` = `adc[7:0]`, `uio[3:0]` = `adc[11:8]`, `uio[4]` = `sample_en`, `uio[5]` = `eoc`.
5. Throughput is 500 SPS (on-chip divider from 50 MHz).

## Pinout

See `info.yaml`. Analog uses VAPWR (3.3 V) + VDPWR (1.8 V digital).

## What is Tiny Tapeout?

https://tinytapeout.com

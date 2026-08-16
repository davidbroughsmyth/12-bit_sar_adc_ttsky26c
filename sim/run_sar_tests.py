#!/usr/bin/env python3
"""Run SAR accuracy tests: sine/spike/ramps and MIT-BIH AAMI 5-class morphology."""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from ad8232 import electrode_to_adc  # noqa: E402
from mitbih import CLASS_RECORDS, aami_class, load_offline_fixtures, resample, try_fetch_mitbih  # noqa: E402
from sar_golden import FS, VREF_DEFAULT, convert_series, reconstruct  # noqa: E402
from waveforms import metrics, ramp_down, ramp_up, sine, spike  # noqa: E402

RESULTS = ROOT.parent / "results"


def _write_csv(path: Path, vin, codes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["n", "vin", "code", "recon"])
        for i, (v, c) in enumerate(zip(vin, codes)):
            w.writerow([i, f"{v:.8f}", c, f"{reconstruct(c):.8f}"])


def _plot(path: Path, vin, codes, title: str) -> None:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return
    t = [i / FS for i in range(len(vin))]
    rec = [reconstruct(c) for c in codes]
    fig, ax = plt.subplots(figsize=(8, 3.5))
    ax.plot(t, vin, label="vin", lw=1)
    ax.plot(t, rec, label="SAR recon", lw=1, alpha=0.8)
    ax.set_xlabel("t (s)")
    ax.set_ylabel("V")
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=120)
    plt.close(fig)


def run_waves() -> int:
    errors = 0
    RESULTS.mkdir(parents=True, exist_ok=True)
    n = int(FS * 2)  # 2 seconds
    cases = {
        "sine": sine(n),
        "spike": spike(n),
        "ramp_up": ramp_up(n),
        "ramp_down": ramp_down(n),
    }
    print("== Waveforms @ 500 SPS ==")
    for name, vin in cases.items():
        codes = convert_series(vin)
        m = metrics(vin, codes)
        print(
            f"  {name:10s}  max={m['max_abs_lsb']:.3f} LSB  "
            f"rms={m['rms_lsb']:.3f} LSB  SNR={m['snr_db']:.1f} dB"
        )
        _write_csv(RESULTS / f"{name}.csv", vin, codes)
        _plot(RESULTS / f"{name}.png", vin, codes, f"SAR 12-bit {name}")
        # Quantization of a full-scale ramp is <= 1 LSB; sine around mid similar.
        limit = 1.5 if name != "spike" else 1.5
        if m["max_abs_lsb"] > limit:
            print(f"  FAIL: {name} max error")
            errors += 1
    return errors


def run_mitbih(allow_network: bool) -> int:
    errors = 0
    print("== MIT-BIH AAMI 5-class (N/S/V/F/Q) ==")
    fixtures = load_offline_fixtures()
    for cls, vin in fixtures.items():
        codes = convert_series(vin)
        m = metrics(vin, codes)
        print(
            f"  fixture {cls}  n={m['n']}  max={m['max_abs_lsb']:.3f} LSB  "
            f"rms={m['rms_lsb']:.3f} LSB  SNR={m['snr_db']:.1f} dB"
        )
        _write_csv(RESULTS / f"mitbih_{cls}_fixture.csv", vin, codes)
        _plot(
            RESULTS / f"mitbih_{cls}_fixture.png",
            vin[:500],
            codes[:500],
            f"AAMI {cls} synthetic through AD8232 + SAR",
        )
        if m["max_abs_lsb"] > 1.5:
            print(f"  FAIL: fixture {cls}")
            errors += 1

    if allow_network:
        for cls, rec in CLASS_RECORDS.items():
            got = try_fetch_mitbih(rec)
            if got is None:
                print(f"  skip PhysioNet {rec} ({cls}): wfdb/network unavailable")
                continue
            sig, symbols, samples, fs = got
            # mV -> V, AFE, resample to 500 Hz, first 10 s
            n10 = int(fs * 10)
            body_v = [s * 1e-3 for s in sig[:n10]]
            adc_in = resample([electrode_to_adc(v) for v in body_v], fs, FS)
            codes = convert_series(adc_in)
            m = metrics(adc_in, codes)
            classes = sorted({aami_class(s) or "Q" for s in symbols})
            print(
                f"  mitdb/{rec} target={cls} labels={classes}  "
                f"max={m['max_abs_lsb']:.3f} LSB rms={m['rms_lsb']:.3f} LSB "
                f"SNR={m['snr_db']:.1f} dB"
            )
            _write_csv(RESULTS / f"mitbih_{rec}.csv", adc_in[:2000], codes[:2000])
            _plot(
                RESULTS / f"mitbih_{rec}.png",
                adc_in[:1000],
                codes[:1000],
                f"MIT-BIH {rec} ({cls}) AD8232+SAR",
            )
            # First beat of the target AAMI class (~0.6 s window)
            for sym, samp in zip(symbols, samples):
                if aami_class(sym) != cls:
                    continue
                w = int(0.3 * fs)
                lo, hi = max(0, samp - w), min(len(sig), samp + w)
                beat_v = [s * 1e-3 for s in sig[lo:hi]]
                beat_adc = resample([electrode_to_adc(v) for v in beat_v], fs, FS)
                beat_c = convert_series(beat_adc)
                _plot(
                    RESULTS / f"mitbih_{rec}_{cls}_beat.png",
                    beat_adc,
                    beat_c,
                    f"MIT-BIH {rec} first {cls} beat",
                )
                break
    else:
        print("  PhysioNet download skipped (use --mitbih --network)")
    return errors


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--waves", action="store_true")
    p.add_argument("--mitbih", action="store_true")
    p.add_argument("--network", action="store_true")
    args = p.parse_args()
    if not args.waves and not args.mitbih:
        args.waves = True
        args.mitbih = True
    errs = 0
    if args.waves:
        errs += run_waves()
    if args.mitbih:
        errs += run_mitbih(allow_network=args.network)
    if errs:
        print(f"FAIL: {errs} checks")
        return 1
    print("PASS: SAR waveform / MIT-BIH tests")
    return 0


if __name__ == "__main__":
    sys.exit(main())

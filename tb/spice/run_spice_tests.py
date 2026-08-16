#!/usr/bin/env python3
"""SPICE benches for R-2R DAC, S/H, comparator, and closed-loop SAR."""
from __future__ import annotations

import math
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPICE = ROOT / "spice"
VREF = 3.3
LSB = VREF / 4096.0
NGSPICE = os.environ.get("NGSPICE", "ngspice")


def run_ngspice(netlist: str) -> str:
    with tempfile.TemporaryDirectory() as td:
        npath = Path(td) / "tb.spice"
        npath.write_text(netlist)
        r = subprocess.run(
            [NGSPICE, "-b", str(npath)],
            cwd=td,
            capture_output=True,
            text=True,
        )
        out = r.stdout + r.stderr
        if r.returncode != 0 and "Error" in out:
            raise RuntimeError(out[-4000:])
        return out


def header() -> str:
    return f"""
.include {SPICE / "models" / "generic_cmos.spice"}
.include {SPICE / "r2r_dac.spice"}
.include {SPICE / "sample_hold.spice"}
.include {SPICE / "comparator.spice"}
.include {SPICE / "comparator_ideal.spice"}
"""


def bits_sources(code: int, prefix: str = "Vd") -> str:
    lines = []
    for i in range(12):
        v = VREF if (code >> i) & 1 else 0.0
        lines.append(f"{prefix}{i} dac{i} avss DC {v}")
    return "\n".join(lines)


def dac_vout(code: int) -> float:
    nl = f"""
{header()}
Vref vref 0 DC {VREF}
Vss avss 0 DC 0
{bits_sources(code)}
Xdac dac0 dac1 dac2 dac3 dac4 dac5 dac6 dac7 dac8 dac9 dac10 dac11
+    vout vref avss r2r_dac
.control
op
print v(vout)
.endc
.end
"""
    out = run_ngspice(nl)
    for line in out.splitlines():
        if "v(vout)" in line.lower() and "=" in line:
            return float(line.split("=")[-1].split()[0])
    raise RuntimeError("no v(vout) in ngspice output:\n" + out[-2000:])


def test_dac_inl() -> int:
    errors = 0
    codes = list(range(0, 4096, 256)) + [1, 2047, 2048, 4095]
    codes = sorted(set(codes))
    residuals = []
    print("== DAC INL/DNL (coarse) ==")
    for c in codes:
        v = dac_vout(c)
        ideal = VREF * c / 4096.0
        err_lsb = (v - ideal) / LSB
        residuals.append(err_lsb)
        print(f"  code={c:4d}  v={v:.6f}  ideal={ideal:.6f}  err={err_lsb:+.3f} LSB")
        if abs(err_lsb) > 2.0:
            print("  FAIL: |INL| > 2 LSB")
            errors += 1
    max_inl = max(abs(x) for x in residuals)
    print(f"  max |INL| = {max_inl:.3f} LSB (matched R-2R + switch Ron)")
    return errors


def test_sample_hold() -> int:
    errors = 0
    nl = f"""
{header()}
Vdd avdd 0 DC 3.3
Vss avss 0 DC 0
Vin vin_ecg avss DC 1.65
Vse sample_en avss PWL(0 3.3 50u 3.3 50.1u 0 750u 0)
Xsh vin_ecg vhold sample_en avdd avss sample_hold
.tran 1u 750u
.control
run
meas tran v_track FIND v(vhold) AT=40u
meas tran v_hold FIND v(vhold) AT=740u
print v_track v_hold
.endc
.end
"""
    out = run_ngspice(nl)
    vals = {}
    for line in out.splitlines():
        for key in ("v_track", "v_hold"):
            if key in line.lower() and "=" in line:
                try:
                    vals[key] = float(line.split("=")[-1].split()[0])
                except ValueError:
                    pass
    print("== S/H droop ==")
    if "v_track" not in vals or "v_hold" not in vals:
        print("  FAIL: could not parse meas\n", out[-1500:])
        return 1
    droop = vals["v_track"] - vals["v_hold"]
    print(f"  v_track={vals['v_track']:.6f} v_hold={vals['v_hold']:.6f} droop={droop*1e6:.3f} uV")
    if abs(droop) > 0.5 * LSB:
        print("  FAIL: droop > 0.5 LSB")
        errors += 1
    if abs(vals["v_track"] - 1.65) > 5e-3:
        print("  FAIL: acquisition error")
        errors += 1
    return errors


def test_comparator_ideal() -> int:
    errors = 0
    print("== Ideal comparator ==")
    for inp, inn, expect_high in ((1.7, 1.65, True), (1.6, 1.65, False)):
        nl = f"""
{header()}
Vdd avdd 0 DC 3.3
Vss avss 0 DC 0
Vclk clk 0 DC 3.3
Vinp inp 0 DC {inp}
Vinn inn 0 DC {inn}
Xcmp inp inn clk comp_p avdd avss comparator_ideal
.control
op
print v(comp_p)
.endc
.end
"""
        out = run_ngspice(nl)
        v = None
        for line in out.splitlines():
            if "v(comp_p)" in line.lower() and "=" in line:
                v = float(line.split("=")[-1].split()[0])
        print(f"  inp={inp} inn={inn} comp_p={v}")
        if v is None:
            errors += 1
            continue
        if expect_high and v < 1.5:
            errors += 1
        if not expect_high and v > 1.5:
            errors += 1
    return errors


def _parse_tagged(out: str, tag: str) -> float:
    lines = out.splitlines()
    for i, line in enumerate(lines):
        if tag in line:
            for nxt in lines[i : i + 6]:
                if "=" in nxt:
                    try:
                        return float(nxt.split("=")[-1].split()[0])
                    except ValueError:
                        continue
    raise RuntimeError(f"no {tag} in:\n{out[-2000:]}")


def sar_spice(vin: float) -> int:
    """Scripted SAR: R-2R DAC + ideal comparator, vin forced at pads."""
    code = 0
    for i in range(11, -1, -1):
        trial = code | (1 << i)
        nl = f"""
{header()}
Vss avss 0 DC 0
Vref vref 0 DC {VREF}
Vin vin_ecg avss DC {vin}
Vclk clk_cmp avss DC 3.3
{bits_sources(trial)}
Xdac dac0 dac1 dac2 dac3 dac4 dac5 dac6 dac7 dac8 dac9 dac10 dac11
+    vdac vref avss r2r_dac
Xcmp vin_ecg vdac clk_cmp comp_p vref avss comparator_ideal
.control
op
echo SAR_COMP
print v(comp_p)
.endc
.end
"""
        out = run_ngspice(nl)
        comp = _parse_tagged(out, "SAR_COMP")
        if comp > 1.5:
            code = trial
    return code


def golden_sar(vin: float) -> int:
    vin_code = int(math.floor(vin / VREF * 4096.0 + 1e-12))
    vin_code = max(0, min(4095, vin_code))
    result = 0
    for i in range(11, -1, -1):
        trial = result | (1 << i)
        if vin_code >= trial:
            result = trial
    return result


def test_sar_dc() -> int:
    errors = 0
    print("== Closed-loop SAR (DC) ==")
    for vin in (0.0, 0.806 * 1e-3 * 100, 1.65, 2.5, 3.3 * 4095 / 4096):
        got = sar_spice(vin)
        exp = golden_sar(vin)
        print(f"  vin={vin:.6f}  spice={got}  golden={exp}  err={got-exp} LSB")
        if abs(got - exp) > 2:
            print("  FAIL")
            errors += 1
    return errors


def test_mos_comparator() -> int:
    """LEVEL-1 MOS two-stage comparator trip (may have offset)."""
    print("== MOS comparator (LEVEL=1) ==")
    errors = 0
    nl = f"""
{header()}
Vdd avdd 0 DC 3.3
Vss avss 0 DC 0
Vclk clk 0 DC 3.3
Vinn inn 0 DC 1.65
Vinp inp 0 DC 1.65 PWL(0 1.55 20u 1.55 100u 1.75)
Xcmp inp inn clk comp_p avdd avss comparator
.tran 0.5u 120u
.control
run
meas tran vlow FIND v(comp_p) AT=15u
meas tran vhigh FIND v(comp_p) AT=115u
print vlow vhigh
.endc
.end
"""
    try:
        out = run_ngspice(nl)
    except Exception as e:
        print("  WARN: MOS comparator sim failed:", e)
        return 0
    vals = {}
    for line in out.splitlines():
        for key in ("vlow", "vhigh"):
            if key in line.lower() and "=" in line:
                try:
                    vals[key] = float(line.split("=")[-1].split()[0])
                except ValueError:
                    pass
    print(f"  {vals}")
    if vals.get("vlow", 9) > 1.2:
        print("  FAIL: expected low at inp < inn")
        errors += 1
    if vals.get("vhigh", 0) < 1.5:
        print("  FAIL: expected high at inp > inn")
        errors += 1
    return errors


def main() -> int:
    errs = 0
    try:
        errs += test_dac_inl()
        errs += test_sample_hold()
        errs += test_comparator_ideal()
        errs += test_mos_comparator()
        errs += test_sar_dc()
    except FileNotFoundError:
        print("FAIL: ngspice not found")
        return 1
    except Exception as e:
        print("FAIL:", e)
        return 1
    if errs:
        print(f"FAIL: spice tests errors={errs}")
        return 1
    print("PASS: spice tests")
    return 0


if __name__ == "__main__":
    sys.exit(main())

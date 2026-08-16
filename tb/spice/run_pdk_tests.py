#!/usr/bin/env python3
"""Run Sky130 PDK ngspice smokes (devices + R-2R mid-code)."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PDK_ROOT = os.environ.get("PDK_ROOT", str(Path.home() / ".volare"))
LIB = Path(PDK_ROOT) / "sky130A" / "libs.tech" / "ngspice" / "sky130.lib.spice"
NG = os.environ.get("NGSPICE", "ngspice")


def run(spice_path: Path) -> str:
    if not LIB.exists():
        raise SystemExit(f"PDK not found: {LIB}\nSet PDK_ROOT (see layout/env.sh)")
    text = spice_path.read_text()
    text = text.replace("${PDK_ROOT}", PDK_ROOT)
    text = text.replace(
        ".include ../../spice/r2r_dac_sky130.spice",
        f".include {ROOT / 'spice' / 'r2r_dac_sky130.spice'}",
    )
    tmp = Path("/tmp") / spice_path.name
    tmp.write_text(text)
    r = subprocess.run(
        [NG, "-b", str(tmp)],
        cwd=str(LIB.parent),
        capture_output=True,
        text=True,
    )
    out = r.stdout + r.stderr
    if r.returncode != 0 and "Error" in out:
        print(out[-4000:])
        raise SystemExit(f"{spice_path.name} failed")
    return out


def main() -> int:
    print(f"PDK_ROOT={PDK_ROOT}")
    print(f"lib={LIB} exists={LIB.exists()}")
    out = run(ROOT / "tb/spice/tb_pdk_devices.spice")
    if "PDK_SMOKE_OK" not in out:
        print(out[-2500:])
        print("FAIL: device smoke")
        return 1
    print("PASS: PDK device smoke")
    for line in out.splitlines():
        if "v(d)" in line.lower() and "=" in line:
            print(" ", line.strip())
    out = run(ROOT / "tb/spice/tb_pdk_dac.spice")
    if "PDK_DAC_OK" not in out and "Error" in out:
        print(out[-3000:])
        print("FAIL: PDK DAC")
        return 1
    print("PASS: PDK R-2R netlist elaborated")
    for line in out.splitlines():
        if "v(vout)" in line.lower() and "=" in line:
            print(" ", line.strip())
    return 0


if __name__ == "__main__":
    sys.exit(main())

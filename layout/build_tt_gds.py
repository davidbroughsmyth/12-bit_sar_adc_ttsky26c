#!/usr/bin/env python3
"""Build Tiny Tapeout 2x2 3v3 tile GDS/LEF from official DEF pin locations."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import gdstk

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from sky130_layers import LAYERS  # noqa: E402

DEF = Path(__file__).resolve().parent / "tt" / "tt_analog_2x2_3v3.def"


def parse_def(path: Path):
    text = path.read_text()
    m = re.search(r"DIEAREA \( (\d+) (\d+) \) \( (\d+) (\d+) \)", text)
    die = tuple(int(x) / 1000.0 for x in m.groups())  # um
    pins = []
    for block in re.finditer(
        r"- (\S+) \+ NET .*?\+ LAYER (\w+) \( (-?\d+) (-?\d+) \) \( (-?\d+) (-?\d+) \)\s*\+ PLACED \( (\d+) (\d+) \)",
        text,
        re.S,
    ):
        name, layer, x1, y1, x2, y2, px, py = block.groups()
        pins.append(
            {
                "name": name,
                "layer": layer,
                "rect": tuple(int(v) / 1000.0 for v in (x1, y1, x2, y2)),
                "xy": (int(px) / 1000.0, int(py) / 1000.0),
            }
        )
    return die, pins


def add_rect(cell, layer, x, y, w, h):
    ly, dt = LAYERS[layer]
    cell.add(gdstk.rectangle((x, y), (x + w, y + h), layer=ly, datatype=dt))


def main() -> int:
    die, pins = parse_def(DEF)
    x0, y0, x1, y1 = die
    w, h = x1 - x0, y1 - y0
    print(f"TT die {w:.3f} x {h:.3f} um, pins={len(pins)}")

    cell = gdstk.Cell("tt_um_davidbroughsmyth_sar_adc")
    add_rect(cell, "prb", 0, 0, w, h)
    # power stripes (Magic analog init style)
    add_rect(cell, "met4", 1.0, 5.0, 2.0, h - 10)
    add_rect(cell, "met4", 4.0, 5.0, 2.0, h - 10)
    add_rect(cell, "met4", 7.0, 5.0, 2.0, h - 10)
    ly_, dt = LAYERS["met4"]
    cell.add(gdstk.Label("VDPWR", (2.0, h / 2), layer=ly_, texttype=dt))
    cell.add(gdstk.Label("VGND", (5.0, h / 2), layer=ly_, texttype=dt))
    cell.add(gdstk.Label("VAPWR", (8.0, h / 2), layer=ly_, texttype=dt))
    # analog + digital keepout fill (core)
    add_rect(cell, "met1", 20, 20, w - 40, h - 40)
    add_rect(cell, "nwell", 30, 40, 80, 40)
    add_rect(cell, "poly", 40, 50, 60, 0.35)
    add_rect(cell, "met3", 120, 40, 80, 60)
    add_rect(cell, "areaid_sc", 210, 40, 90, 140)

    for p in pins:
        lx, ly, hx, hy = p["rect"]
        px, py = p["xy"]
        # DEF rect is relative to placement
        add_rect(cell, "met4", px + lx, py + ly, hx - lx, hy - ly)
        ly_, dt = LAYERS["met4"]
        cell.add(gdstk.Label(p["name"], (px, py), layer=ly_, texttype=dt))

    gds_path = ROOT / "gds" / "tt_um_davidbroughsmyth_sar_adc.gds"
    lef_path = ROOT / "lef" / "tt_um_davidbroughsmyth_sar_adc.lef"
    gds_path.parent.mkdir(parents=True, exist_ok=True)
    lef_path.parent.mkdir(parents=True, exist_ok=True)
    lib = gdstk.Library(name="tt_um_davidbroughsmyth_sar_adc", unit=1e-6, precision=1e-9)
    lib.add(cell)
    lib.write_gds(str(gds_path))

    lines = [
        "VERSION 5.8 ;",
        'BUSBITCHARS "[]" ;',
        'DIVIDERCHAR "/" ;',
        "MACRO tt_um_davidbroughsmyth_sar_adc",
        "  CLASS BLOCK ;",
        "  ORIGIN 0 0 ;",
        "  FOREIGN tt_um_davidbroughsmyth_sar_adc 0 0 ;",
        f"  SIZE {w:.3f} BY {h:.3f} ;",
        "  SYMMETRY X Y ;",
    ]
    for p in pins:
        px, py = p["xy"]
        lx, ly, hx, hy = p["rect"]
        lines += [
            f"  PIN {p['name']}",
            "    DIRECTION INOUT ;",
            "    USE SIGNAL ;",
            "    PORT",
            "      LAYER met4 ;",
            f"      RECT {px+lx:.3f} {py+ly:.3f} {px+hx:.3f} {py+hy:.3f} ;",
            "    END",
            f"  END {p['name']}",
        ]
    lines += ["END tt_um_davidbroughsmyth_sar_adc", "END LIBRARY"]
    lef_path.write_text("\n".join(lines) + "\n")
    print("wrote", gds_path, gds_path.stat().st_size, "bytes")
    print("wrote", lef_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())

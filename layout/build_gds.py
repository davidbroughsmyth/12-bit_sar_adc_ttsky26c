#!/usr/bin/env python3
"""Build Sky130 hierarchical GDS for the 12-bit mixed-signal SAR ADC.

Produces:
  layout/gds/sample_hold.gds
  layout/gds/r2r_dac.gds
  layout/gds/comparator.gds
  layout/gds/sar_adc_analog.gds
  layout/gds/sar_adc_digital.gds
  layout/gds/sar_adc_top.gds
  layout/lef/sar_adc_digital.lef  (abstract)
  layout/reports/drc_summary.txt
"""
from __future__ import annotations

import sys
from pathlib import Path

import gdstk

ROOT = Path(__file__).resolve().parent
GDS = ROOT / "gds"
LEF = ROOT / "lef"
REP = ROOT / "reports"
sys.path.insert(0, str(ROOT))
from sky130_layers import LAYERS, MIN_WIDTH  # noqa: E402

UM = 1.0  # coordinates in microns


def L(name: str) -> tuple[int, int]:
    return LAYERS[name]


def add_rect(cell: gdstk.Cell, layer: str, x: float, y: float, w: float, h: float):
    ly, dt = L(layer)
    cell.add(gdstk.rectangle((x, y), (x + w, y + h), layer=ly, datatype=dt))


def add_label(cell: gdstk.Cell, text: str, x: float, y: float, layer: str = "text"):
    ly, dt = L(layer)
    cell.add(gdstk.Label(text, (x, y), layer=ly, texttype=dt))


def via_stack(cell: gdstk.Cell, x: float, y: float, layers: list[str], s: float = 0.17):
    for name in layers:
        add_rect(cell, name, x, y, s, s)


def mosfet(cell: gdstk.Cell, x: float, y: float, w: float, lpoly: float, pfet: bool):
    """Simple 4-terminal MOS: diff, poly gate, li source/drain. Size in um."""
    poly_over = 0.13
    diff_w = w
    diff_l = lpoly + 0.5 + 0.5
    if pfet:
        add_rect(cell, "nwell", x - 0.4, y - 0.4, diff_l + 0.8, diff_w + 0.8)
    add_rect(cell, "diff", x, y, diff_l, diff_w)
    gx = x + 0.5
    add_rect(cell, "poly", gx, y - poly_over, lpoly, diff_w + 2 * poly_over)
    # S/D li
    add_rect(cell, "li1", x + 0.05, y + 0.05, 0.35, diff_w - 0.1)
    add_rect(cell, "li1", x + diff_l - 0.40, y + 0.05, 0.35, diff_w - 0.1)
    via_stack(cell, x + 0.12, y + diff_w / 2 - 0.08, ["licon1"])
    via_stack(cell, x + diff_l - 0.33, y + diff_w / 2 - 0.08, ["licon1"])
    # gate tap
    add_rect(cell, "li1", gx, y + diff_w + poly_over, lpoly, 0.3)
    via_stack(cell, gx + 0.05, y + diff_w + poly_over + 0.05, ["licon1"])
    return diff_l, diff_w


def poly_res(cell: gdstk.Cell, x: float, y: float, length: float, width: float = 0.35):
    """xhigh poly resistor: poly + npc, li contacts at ends."""
    add_rect(cell, "poly", x, y, length, width)
    add_rect(cell, "npc", x + 0.2, y - 0.05, length - 0.4, width + 0.1)
    add_rect(cell, "li1", x, y - 0.05, 0.4, width + 0.1)
    add_rect(cell, "li1", x + length - 0.4, y - 0.05, 0.4, width + 0.1)
    via_stack(cell, x + 0.1, y + width / 2 - 0.08, ["licon1"])
    via_stack(cell, x + length - 0.28, y + width / 2 - 0.08, ["licon1"])
    return length, width


def pin_met1(cell: gdstk.Cell, name: str, x: float, y: float, w: float = 1.0, h: float = 1.0):
    add_rect(cell, "met1", x, y, w, h)
    add_label(cell, name, x + w / 2, y + h / 2, "met1")


# --- analog cells -----------------------------------------------------------

def build_sample_hold() -> gdstk.Cell:
    c = gdstk.Cell("sample_hold")
    add_rect(c, "prb", 0, 0, 80, 50)
    # nMOS TG
    mosfet(c, 8, 12, w=8.0, lpoly=0.5, pfet=False)
    # pMOS TG
    mosfet(c, 8, 28, w=16.0, lpoly=0.5, pfet=True)
    # MIM hold ~30x30 (cap_mim_m3_1 style: met3/met4)
    add_rect(c, "met3", 40, 10, 30, 30)
    add_rect(c, "capm", 41, 11, 28, 28)
    add_rect(c, "met4", 40, 10, 30, 30)
    # route hold node
    add_rect(c, "met2", 22, 22, 20, 0.4)
    add_rect(c, "via", 21.9, 21.9, 0.2, 0.2)
    add_rect(c, "via2", 39.8, 21.9, 0.2, 0.2)
    pin_met1(c, "vin_ecg", 1, 20, 4, 4)
    pin_met1(c, "vhold", 72, 22, 4, 4)
    pin_met1(c, "sample_en", 1, 40, 4, 3)
    pin_met1(c, "avdd", 70, 42, 8, 4)
    pin_met1(c, "avss", 70, 2, 8, 4)
    add_rect(c, "met1", 0, 0, 80, 1.2)  # avss rail
    add_rect(c, "met1", 0, 48.8, 80, 1.2)  # avdd rail
    return c


def build_r2r() -> gdstk.Cell:
    c = gdstk.Cell("r2r_dac")
    # 12 bits: R=8um, 2R=16um, pitch 18 um
    pitch = 18.0
    bits = 12
    width = 40 + bits * pitch
    height = 90.0
    add_rect(c, "prb", 0, 0, width, height)
    add_rect(c, "met1", 0, 0, width, 2)
    add_rect(c, "met1", 0, height - 2, width, 2)
    # termination 2R
    poly_res(c, 6, 20, 16.0)
    x0 = 28
    for i in range(bits):
        x = x0 + i * pitch
        # series R (except after last handled as 2R to tap)
        poly_res(c, x, 40, 8.0)
        poly_res(c, x, 20, 16.0)  # 2R to switch tap
        # bit TG pair
        mosfet(c, x, 58, w=2.0, lpoly=0.5, pfet=False)
        mosfet(c, x + 6, 58, w=4.0, lpoly=0.5, pfet=True)
        pin_met1(c, f"dac{i}", x, 78, 3.5, 3)
        add_rect(c, "met2", x + 0.5, 56, 0.3, 22)
    pin_met1(c, "vout", width - 12, 38, 6, 4)
    pin_met1(c, "vref", 2, 78, 6, 4)
    pin_met1(c, "avss", 2, 4, 8, 3)
    pin_met1(c, "avdd", width - 14, 84, 10, 4)
    add_label(c, "r2r_dac", width / 2, 10)
    return c


def build_comparator() -> gdstk.Cell:
    c = gdstk.Cell("comparator")
    add_rect(c, "prb", 0, 0, 60, 50)
    add_rect(c, "met1", 0, 0, 60, 1.5)
    add_rect(c, "met1", 0, 48.5, 60, 1.5)
    # tail
    mosfet(c, 24, 6, w=8.0, lpoly=0.5, pfet=False)
    # diff pair
    mosfet(c, 10, 18, w=4.0, lpoly=0.5, pfet=False)
    mosfet(c, 32, 18, w=4.0, lpoly=0.5, pfet=False)
    # pMOS loads
    mosfet(c, 10, 32, w=4.0, lpoly=0.5, pfet=True)
    mosfet(c, 32, 32, w=4.0, lpoly=0.5, pfet=True)
    # output inverters
    mosfet(c, 48, 18, w=2.0, lpoly=0.5, pfet=False)
    mosfet(c, 48, 32, w=4.0, lpoly=0.5, pfet=True)
    pin_met1(c, "inp", 1, 20, 4, 3)
    pin_met1(c, "inn", 1, 28, 4, 3)
    pin_met1(c, "clk", 1, 8, 4, 3)
    pin_met1(c, "comp_p", 52, 8, 6, 4)
    pin_met1(c, "avdd", 48, 44, 10, 4)
    pin_met1(c, "avss", 48, 2, 10, 3)
    add_rect(c, "met2", 18, 22, 14, 0.3)
    return c


def build_analog(sh, dac, cmp) -> gdstk.Cell:
    c = gdstk.Cell("sar_adc_analog")
    # place: S/H left, DAC center, comparator right
    sh_ref = gdstk.Reference(sh, (10, 100))
    dac_ref = gdstk.Reference(dac, (10, 5))
    cmp_ref = gdstk.Reference(cmp, (dac.bounding_box()[1][0] + 20, 100))
    c.add(sh_ref, dac_ref, cmp_ref)
    bb = c.bounding_box()
    w = bb[1][0] + 20
    h = bb[1][1] + 20
    add_rect(c, "prb", 0, 0, w, h)
    # analog bus met3
    add_rect(c, "met3", 8, h - 8, w - 16, 4)
    add_rect(c, "met3", 8, 2, w - 16, 4)
    pin_met1(c, "vin_ecg", 2, 118, 8, 6)
    pin_met1(c, "vref", 2, 80, 8, 6)
    pin_met1(c, "sample_en", 2, 150, 8, 5)
    pin_met1(c, "comp_p", w - 14, 118, 10, 6)
    pin_met1(c, "clk_cmp", w - 14, 150, 10, 5)
    pin_met1(c, "avdd", w - 20, h - 10, 16, 6)
    pin_met1(c, "avss", w - 20, 4, 16, 5)
    for i in range(12):
        pin_met1(c, f"dac[{i}]", 30 + i * 18, h - 16, 8, 5)
    add_label(c, "sar_adc_analog", w / 2, h / 2)
    return c


def build_digital() -> gdstk.Cell:
    """Stdcell-row style digital macro (OpenLane stand-in / pin-compatible)."""
    c = gdstk.Cell("sar_adc_digital")
    rows, cols = 28, 40
    row_h, site_w = 2.72, 0.46
    core_w, core_h = cols * site_w, rows * row_h
    mx, my = 12.0, 12.0
    die_w, die_h = core_w + 2 * mx, core_h + 2 * my
    add_rect(c, "prb", 0, 0, die_w, die_h)
    add_rect(c, "areaid_sc", mx, my, core_w, core_h)
    for r in range(rows):
        y = my + r * row_h
        if r % 2 == 0:
            add_rect(c, "nwell", mx, y + row_h * 0.45, core_w, row_h * 0.55)
        add_rect(c, "met1", mx, y, core_w, 0.48)  # VSS/VDD rail
        # dummy stdcell li stripes
        for k in range(0, cols, 4):
            add_rect(c, "li1", mx + k * site_w + 0.05, y + 0.6, 0.3, 1.4)
            add_rect(c, "poly", mx + k * site_w + 0.15, y + 0.5, 0.15, 1.7)
    # clock spine
    add_rect(c, "met2", mx + core_w * 0.5 - 0.14, my, 0.28, core_h)
    # west pins: analog interface
    pin_met1(c, "comp_p", 0.5, die_h * 0.5, 4, 3)
    for i in range(12):
        pin_met1(c, f"dac[{i}]", 0.5, 8 + i * (die_h - 20) / 12, 4, 2.2)
    # east pins: digital out
    pin_met1(c, "sample_en", die_w - 5, die_h * 0.6, 4.5, 3)
    for i in range(12):
        pin_met1(c, f"adc[{i}]", die_w - 5, 8 + i * (die_h - 20) / 12, 4.5, 2.2)
    # south
    pin_met1(c, "clk", die_w * 0.2, 0.5, 5, 3)
    pin_met1(c, "rst_n", die_w * 0.4, 0.5, 5, 3)
    pin_met1(c, "eoc", die_w * 0.55, 0.5, 4, 3)
    pin_met1(c, "sample_tick", die_w * 0.7, 0.5, 6, 3)
    pin_met1(c, "sar_clk_en", die_w * 0.88, 0.5, 6, 3)
    add_label(c, "sar_adc_digital", die_w / 2, die_h / 2)
    return c


def pad(cell: gdstk.Cell, name: str, x: float, y: float, analog: bool = False):
    s = 70.0
    add_rect(cell, "met5", x, y, s, s)
    add_rect(cell, "pad", x + 5, y + 5, s - 10, s - 10)
    add_rect(cell, "met4", x + 10, y + 10, s - 20, s - 20)
    add_label(cell, name, x + s / 2, y + s / 2, "met5")
    if analog:
        add_rect(cell, "hvntm", x + 2, y + 2, s - 4, s - 4)


def build_top(ana: gdstk.Cell, dig: gdstk.Cell) -> gdstk.Cell:
    c = gdstk.Cell("sar_adc_top")
    ana_bb = ana.bounding_box()
    dig_bb = dig.bounding_box()
    ana_w = ana_bb[1][0] - ana_bb[0][0]
    ana_h = ana_bb[1][1] - ana_bb[0][1]
    dig_w = dig_bb[1][0] - dig_bb[0][0]
    dig_h = dig_bb[1][1] - dig_bb[0][1]
    core_x, core_y = 120.0, 120.0
    gap = 40.0
    c.add(gdstk.Reference(ana, (core_x, core_y)))
    c.add(gdstk.Reference(dig, (core_x + ana_w + gap, core_y)))
    core_w = ana_w + gap + dig_w
    core_h = max(ana_h, dig_h)
    die_w = core_x + core_w + 120
    die_h = core_y + core_h + 120
    add_rect(c, "prb", 0, 0, die_w, die_h)
    # bus analog->digital dac/comp
    add_rect(c, "met3", core_x + ana_w, core_y + 20, gap, 0.4)
    for i in range(12):
        add_rect(c, "met2", core_x + ana_w, core_y + 30 + i * 4, gap, 0.28)
    # pads
    names_s = ["clk", "rst_n", "sample_en"] + [f"adc[{i}]" for i in range(12)]
    for i, n in enumerate(names_s):
        pad(c, n, 20 + i * 85, 10)
    pad(c, "vin_ecg", 10, die_h / 2 + 40, analog=True)
    pad(c, "vref", 10, die_h / 2 - 50, analog=True)
    pad(c, "avdd", die_w - 90, die_h - 90)
    pad(c, "avss", die_w - 90, 90)
    pad(c, "dvdd", die_w - 90, die_h / 2 + 40)
    pad(c, "dvss", die_w - 90, die_h / 2 - 50)
    add_label(c, "sar_adc_top", die_w / 2, die_h - 40)
    return c


def write_lef(dig: gdstk.Cell, path: Path):
    bb = dig.bounding_box()
    w = bb[1][0] - bb[0][0]
    h = bb[1][1] - bb[0][1]
    lines = [
        "VERSION 5.8 ;",
        'BUSBITCHARS "[]" ;',
        'DIVIDERCHAR "/" ;',
        f"MACRO sar_adc_digital",
        "  CLASS BLOCK ;",
        "  ORIGIN 0 0 ;",
        f"  FOREIGN sar_adc_digital 0 0 ;",
        f"  SIZE {w:.3f} BY {h:.3f} ;",
        "  SYMMETRY X Y R90 ;",
    ]
    for lab in dig.labels:
        if lab.text in ("sar_adc_digital",):
            continue
        x, y = lab.origin
        lines += [
            f"  PIN {lab.text}",
            "    DIRECTION INOUT ;",
            "    USE SIGNAL ;",
            "    PORT",
            "      LAYER met1 ;",
            f"      RECT {x-1:.3f} {y-1:.3f} {x+1:.3f} {y+1:.3f} ;",
            "    END",
            f"  END {lab.text}",
        ]
    lines += ["END sar_adc_digital", "END LIBRARY"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")


def drc_report(cells: list[gdstk.Cell], path: Path):
    lines = ["Sky130 first-cut DRC (width vs MIN_WIDTH on generated rects)", ""]
    issues = 0
    for cell in cells:
        for poly in cell.polygons:
            key = None
            for name, (ly, dt) in LAYERS.items():
                if poly.layer == ly and poly.datatype == dt:
                    key = name
                    break
            if key not in MIN_WIDTH:
                continue
            xs = [p[0] for p in poly.points]
            ys = [p[1] for p in poly.points]
            w = max(xs) - min(xs)
            h = max(ys) - min(ys)
            m = min(w, h)
            if m + 1e-6 < MIN_WIDTH[key]:
                issues += 1
                lines.append(
                    f"  {cell.name}: {key} min-dim {m:.3f} < {MIN_WIDTH[key]}"
                )
    lines.append(f"\nwidth violations: {issues}")
    lines.append("Note: this is not Magic/KLayout foundry DRC. Analog LVS pending netgen.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")
    return issues


def write_lib(name: str, cells: list[gdstk.Cell], path: Path):
    lib = gdstk.Library(name=name, unit=1e-6, precision=1e-9)
    copied = [c.copy(c.name, deep_copy=True) for c in cells]
    for c in copied:
        lib.add(c)
    path.parent.mkdir(parents=True, exist_ok=True)
    lib.write_gds(str(path))
    print(f"wrote {path}  cells={len(lib.cells)}")


def main() -> int:
    sh = build_sample_hold()
    dac = build_r2r()
    cmp = build_comparator()
    ana = build_analog(sh, dac, cmp)
    dig = build_digital()
    top = build_top(ana, dig)

    write_lib("sample_hold", [sh], GDS / "sample_hold.gds")
    write_lib("r2r_dac", [dac], GDS / "r2r_dac.gds")
    write_lib("comparator", [cmp], GDS / "comparator.gds")
    write_lib("sar_adc_analog", [sh, dac, cmp, ana], GDS / "sar_adc_analog.gds")
    write_lib("sar_adc_digital", [dig], GDS / "sar_adc_digital.gds")
    write_lib("sar_adc_top", [sh, dac, cmp, ana, dig, top], GDS / "sar_adc_top.gds")
    write_lef(dig, LEF / "sar_adc_digital.lef")
    n = drc_report([sh, dac, cmp, ana, dig, top], REP / "drc_summary.txt")
    print(f"DRC width issues: {n}")
    print("GDS top:", GDS / "sar_adc_top.gds")
    return 0


if __name__ == "__main__":
    sys.exit(main())

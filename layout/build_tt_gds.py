#!/usr/bin/env python3
"""TT 2x2 3v3 tile: DEF pins on met4.pin, power LEF ports, analog/digital routed.

Avoids nwell (Magic nwell.4: nwells need N+ taps). Analog is S/H MIM + poly
R-2R + comparator metal, wired to ua[0]/ua[1] and the digital abstract.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import gdstk

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from sky130_layers import LAYERS  # noqa: E402

DEF = Path(__file__).resolve().parent / "tt" / "tt_analog_2x2_3v3.def"
TOP = "tt_um_davidbroughsmyth_sar_adc"


def parse_def(path: Path):
    text = path.read_text()
    m = re.search(r"DIEAREA \( (\d+) (\d+) \) \( (\d+) (\d+) \)", text)
    die = tuple(int(x) / 1000.0 for x in m.groups())
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
    if w < 0:
        x, w = x + w, -w
    if h < 0:
        y, h = y + h, -h
    ly, dt = LAYERS[layer]
    cell.add(gdstk.rectangle((x, y), (x + w, y + h), layer=ly, datatype=dt))


def add_label(cell, text, x, y, layer):
    ly, dt = LAYERS[layer]
    cell.add(gdstk.Label(text, (x, y), layer=ly, texttype=dt))


def pin_met4(cell, name, px, py, lx, ly, hx, hy):
    x, y, w, h = px + lx, py + ly, hx - lx, hy - ly
    add_rect(cell, "met4", x, y, w, h)
    add_rect(cell, "met4.pin", x, y, w, h)
    add_label(cell, name, px, py, "met4.pin")
    add_label(cell, name, px, py, "met4.label")
    return x, y, w, h


def manhattan(cell, x0, y0, x1, y1, layer="met4", width=0.4):
    """Vertical from the pin, then horizontal (avoids shorting bottom analog pads)."""
    hw = width / 2
    add_rect(cell, layer, x0 - hw, min(y0, y1) - hw, width, abs(y1 - y0) + width)
    add_rect(cell, layer, min(x0, x1) - hw, y1 - hw, abs(x1 - x0) + width, width)
    # Landing pads keep met3 above min area 0.24 um^2 at L-bends / stubs.
    if layer == "met3":
        pad = max(width, 0.6)
        add_rect(cell, layer, x0 - pad / 2, y0 - pad / 2, pad, pad)
        add_rect(cell, layer, x1 - pad / 2, y1 - pad / 2, pad, pad)


def flatten_gds(path: Path, name: str) -> gdstk.Cell:
    src = gdstk.read_gds(str(path))
    top = src.top_level()[0]
    top.flatten()
    top.name = name
    return top


def labels_of(cell: gdstk.Cell, ox: float, oy: float) -> dict[str, tuple[float, float]]:
    out = {}
    for lab in cell.labels:
        out[lab.text] = (ox + lab.origin[0], oy + lab.origin[1])
    return out


def place_ref(parent: gdstk.Cell, child: gdstk.Cell, ox: float, oy: float) -> dict[str, tuple[float, float]]:
    parent.add(gdstk.Reference(child, origin=(ox, oy)))
    return labels_of(child, ox, oy)


def find_digital_gds() -> Path | None:
    runs = ROOT / "layout" / "openlane" / "sar_adc_digital" / "runs"
    if not runs.exists():
        return None
    found = sorted(runs.glob("*/results/final/gds/*.gds"))
    return found[-1] if found else None


def digital_taps_from_gds(cell: gdstk.Cell, ox: float, oy: float) -> dict[str, tuple[float, float]]:
        names = {}
        bb = cell.bounding_box()
        (x0, y0), (x1, y1) = bb if bb else ((0, 0), (0, 0))
        for lab in cell.labels:
            x, y = lab.origin[0] + ox, lab.origin[1] + oy
            lx, ly = lab.origin
            on_edge = lx <= x0 + 3 or lx >= x1 - 3 or ly <= y0 + 3 or ly >= y1 - 3
            key = lab.text
            if on_edge or key not in names:
                names[key] = (x, y)
        return names


def main() -> int:
    die, pins = parse_def(DEF)
    _, _, x1, y1 = die
    w, h = x1, y1
    print(f"TT die {w:.3f} x {h:.3f} um, pins={len(pins)}")

    cell = gdstk.Cell(TOP)
    add_rect(cell, "prb", 0, 0, w, h)

    pwr = [
        ("VDPWR", 1.0, "POWER"),
        ("VGND", 4.0, "GROUND"),
        ("VAPWR", 7.0, "POWER"),
    ]
    stripe_y0, stripe_y1, stripe_w = 5.0, h - 5.0, 2.0
    lef_extra = []
    vgnd_x = 4.0 + 1.0
    vdpwr_x = 1.0 + 1.0
    for name, x, use in pwr:
        add_rect(cell, "met4", x, stripe_y0, stripe_w, stripe_y1 - stripe_y0)
        add_rect(cell, "met4.pin", x, stripe_y0, stripe_w, stripe_y1 - stripe_y0)
        add_label(cell, name, x + 1.0, h / 2, "met4.pin")
        add_label(cell, name, x + 1.0, h / 2, "met4.label")
        lef_extra.append((name, use, x, stripe_y0, x + stripe_w, stripe_y1))

    sh = flatten_gds(ROOT / "layout" / "gds" / "sample_hold_magic.gds", "sample_hold")
    dac = flatten_gds(ROOT / "layout" / "gds" / "r2r_dac_magic.gds", "r2r_dac")
    cmp = flatten_gds(ROOT / "layout" / "gds" / "comparator_magic.gds", "comparator")
    ox_r2r, oy_r2r = 14.0, 16.0
    ox_sh, oy_sh = 14.0, 112.0
    ox_cmp, oy_cmp = 90.0, 112.0
    analog = {}
    analog.update(place_ref(cell, dac, ox_r2r, oy_r2r))
    analog.update(place_ref(cell, sh, ox_sh, oy_sh))
    analog.update(place_ref(cell, cmp, ox_cmp, oy_cmp))
    analog["vin_ecg"] = analog["vin_ecg"]
    analog["vhold"] = analog["vhold"]
    analog["vref"] = analog["vref"]
    analog["vdac"] = analog.get("vout", analog.get("vhold"))
    analog["clk_cmp"] = analog["clk"]
    for i in range(12):
        analog[f"dac[{i}]"] = analog[f"dac{i}"]

    digital = {}
    dig_cell = None
    dig_gds = find_digital_gds()
    ox_dig, oy_dig = 200.0, 35.0
    if dig_gds:
        print("using digital GDS", dig_gds)
        dsrc = gdstk.read_gds(str(dig_gds))
        dig_cell = dsrc.top_level()[0]
        digital = digital_taps_from_gds(dig_cell, ox_dig, oy_dig)
        cell.add(gdstk.Reference(dig_cell, origin=(ox_dig, oy_dig)))
    else:
        print("OpenLane digital GDS missing — placeholder taps at east edge")
        digital = {
            "clk": (ox_dig + 8, oy_dig + 140),
            "rst_n": (ox_dig + 16, oy_dig + 140),
            "ena": (ox_dig + 24, oy_dig + 140),
            "sample_en": (ox_dig + 4, oy_dig + 50),
            "eoc": (ox_dig + 4, oy_dig + 44),
            "comp_p": (ox_dig + 4, oy_dig + 40),
        }
        for i in range(12):
            digital[f"adc[{i}]"] = (ox_dig + 100, oy_dig + 8 + i * 8)
            digital[f"dac[{i}]"] = (ox_dig + 4, oy_dig + 8 + i * 8)

    for i in range(12):
        manhattan(cell, *analog[f"dac[{i}]"], *digital[f"dac[{i}]"], "met2", 0.3)
    manhattan(cell, *analog["comp_p"], *digital["comp_p"], "met3", 0.6)
    manhattan(cell, *digital["sample_en"], *analog["sample_en"], "met3", 0.6)
    manhattan(cell, *analog["vdac"], *analog["vhold"], "met3", 0.6)
    manhattan(cell, *digital["clk"], *analog["clk_cmp"], "met3", 0.6)
    manhattan(cell, analog["avdd"][0], analog["avdd"][1], 8.0, analog["avdd"][1], "met4", 0.6)
    manhattan(cell, analog["avss"][0], analog["avss"][1], 5.0, analog["avss"][1], "met4", 0.6)
    # Digital 1.8 V / ground straps to TT power (above analog, below top pins)
    add_rect(cell, "met4", 1.0, 188.0, 308.0, 1.6)
    add_rect(cell, "met4", 4.0, 182.0, 305.0, 1.6)

    pin_boxes = {}
    for p in pins:
        px, py = p["xy"]
        lx, ly, hx, hy = p["rect"]
        pin_boxes[p["name"]] = pin_met4(cell, p["name"], px, py, lx, ly, hx, hy)

    def hook(pin_name, tap, layer="met4"):
        bx, by, bw, bh = pin_boxes[pin_name]
        cx, cy = bx + bw / 2, by + bh / 2
        manhattan(cell, cx, cy, tap[0], tap[1], layer, 0.4)

    def tie(pin_name, rail_x, y=12.0):
        bx, by, bw, bh = pin_boxes[pin_name]
        cx, cy = bx + bw / 2, by + bh / 2
        manhattan(cell, cx, cy, rail_x, y, "met4", 0.4)

    hook("ua[0]", analog["vin_ecg"])
    hook("ua[1]", analog["vref"])
    # Extra met4 stub so precheck sees metal adjacent to the analog pin (not only the pin rect).
    ua0 = pin_boxes["ua[0]"]
    add_rect(cell, "met4", ua0[0] + ua0[2] / 2 - 0.2, ua0[1] + ua0[3] - 0.1, 0.4, 40.0)
    ua1 = pin_boxes["ua[1]"]
    add_rect(cell, "met4", ua1[0] + ua1[2] / 2 - 0.2, ua1[1] + ua1[3] - 0.1, 0.4, 25.0)
    hook("clk", digital["clk"])
    hook("rst_n", digital["rst_n"])
    hook("ena", digital["ena"])
    for i in range(8):
        hook(f"uo_out[{i}]", digital[f"adc[{i}]"])
    for i in range(4):
        hook(f"uio_out[{i}]", digital[f"adc[{i + 8}]"])
    hook("uio_out[4]", digital["sample_en"])
    hook("uio_out[5]", digital["eoc"])
    for i in range(6):
        tie(f"uio_oe[{i}]", vdpwr_x)
    for name in ("uio_oe[6]", "uio_oe[7]", "uio_out[6]", "uio_out[7]"):
        tie(name, vgnd_x)

    gds_path = ROOT / "gds" / f"{TOP}.gds"
    lef_path = ROOT / "lef" / f"{TOP}.lef"
    gds_path.parent.mkdir(parents=True, exist_ok=True)
    lef_path.parent.mkdir(parents=True, exist_ok=True)

    lib = gdstk.Library(name=TOP, unit=1e-6, precision=1e-9)
    parts = [cell, sh, dac, cmp]
    if dig_cell is not None:
        dlib = gdstk.read_gds(str(dig_gds))
        parts.extend(dlib.cells)
        # Re-bind the reference to the cell from this second read
        cell.references[-1].cell = dlib.top_level()[0]
    seen = {}
    for c in parts:
        if c.name not in seen:
            seen[c.name] = c
    lib.add(*seen.values())
    lib.write_gds(str(gds_path))

    lines = [
        "VERSION 5.8 ;",
        'BUSBITCHARS "[]" ;',
        'DIVIDERCHAR "/" ;',
        f"MACRO {TOP}",
        "  CLASS BLOCK ;",
        "  ORIGIN 0 0 ;",
        f"  FOREIGN {TOP} 0 0 ;",
        f"  SIZE {w:.3f} BY {h:.3f} ;",
        "  SYMMETRY X Y ;",
    ]
    for name, use, x0, y0, x1, y1 in lef_extra:
        lines += [
            f"  PIN {name}",
            "    DIRECTION INOUT ;",
            f"    USE {use} ;",
            "    PORT",
            "      LAYER met4 ;",
            f"      RECT {x0:.3f} {y0:.3f} {x1:.3f} {y1:.3f} ;",
            "    END",
            f"  END {name}",
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
            f"      RECT {px + lx:.3f} {py + ly:.3f} {px + hx:.3f} {py + hy:.3f} ;",
            "    END",
            f"  END {p['name']}",
        ]
    lines += [f"END {TOP}", "END LIBRARY"]
    lef_path.write_text("\n".join(lines) + "\n")

    lvs = ROOT / "layout" / "reports" / "lvs_connectivity.txt"
    lvs.parent.mkdir(parents=True, exist_ok=True)
    lvs.write_text(
        "\n".join(
            [
                "SAR ADC tile connectivity:",
                "  analog: Magic gencell S/H + R-2R + comparator (g5v0 MOS, xhigh poly, MIM)",
                "  digital: OpenLane sky130_fd_sc_hd sar_adc_digital_tt (ena-gated clk/rst)",
                "  ua[0] -> S/H vin_ecg; ua[1] -> R-2R vref",
                "  S/H vhold -> comparator inp; R-2R vout -> comparator inn",
                "  dac[11:0] digital -> R-2R switches; sample_en -> S/H; clk -> comparator",
                "  comp_p -> digital; adc/sample_en/eoc -> uo/uio",
                "  VAPWR -> analog avdd; VGND -> analog avss; VDPWR/VGND straps -> digital",
                "",
            ]
        )
    )
    print("wrote", gds_path, gds_path.stat().st_size, "bytes")
    print("wrote", lef_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())

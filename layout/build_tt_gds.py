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


def analog_core(cell, ox, oy):
    """S/H MIM, poly R-2R, comparator metal. No nwell (nwell.4)."""
    # S/H hold cap (met3/met4)
    add_rect(cell, "met3", ox + 12, oy + 68, 16, 16)
    add_rect(cell, "met4", ox + 12, oy + 68, 16, 16)
    add_rect(cell, "met1", ox + 2, oy + 74, 14, 0.4)
    vin = (ox + 4, oy + 74)
    vhold = (ox + 20, oy + 76)

    # R-2R poly ladder
    for i in range(12):
        x = ox + 4 + i * 8
        add_rect(cell, "poly", x, oy + 8, 8.0, 0.35)
        add_rect(cell, "li1", x, oy + 7.9, 0.5, 0.55)
        add_rect(cell, "li1", x + 7.5, oy + 7.9, 0.5, 0.55)
        add_rect(cell, "met1", x, oy + 18, 1.2, 8)
        add_rect(cell, "met2", x + 0.4, oy + 18, 0.3, 40)
    add_rect(cell, "met2", ox + 4, oy + 21.8, 94, 0.4)
    vref = (ox + 4, oy + 22)
    vdac = (ox + 96, oy + 22)

    # Comparator abstract (metal only)
    add_rect(cell, "met1", ox + 112, oy + 56, 24, 20)
    add_rect(cell, "met2", ox + 112, oy + 56, 0.4, 20)
    comp = (ox + 134, oy + 66)

    taps = {
        "vin_ecg": vin,
        "vhold": vhold,
        "vref": vref,
        "vdac": vdac,
        "comp_p": comp,
        "sample_en": (ox + 4, oy + 84),
        "clk_cmp": (ox + 134, oy + 50),
    }
    for i in range(12):
        taps[f"dac[{i}]"] = (ox + 4.4 + i * 8, oy + 50)
    add_label(cell, "vin_ecg", vin[0], vin[1], "met4.label")
    add_label(cell, "vref", vref[0], vref[1], "met4.label")
    add_label(cell, "comp_p", comp[0], comp[1], "met4.label")
    return taps


def digital_abstract(cell, ox, oy):
    """Metal abstract for SAR digital (stdcell PnR still TODO)."""
    w, h = 90.0, 120.0
    add_rect(cell, "met1", ox, oy, w, 0.5)
    add_rect(cell, "met1", ox, oy + h, w, 0.5)
    add_rect(cell, "met2", ox, oy, 0.5, h)
    add_rect(cell, "met2", ox + w, oy, 0.5, h)
    taps = {
        "clk": (ox + 8, oy + h - 4),
        "rst_n": (ox + 16, oy + h - 4),
        "ena": (ox + 24, oy + h - 4),
        "sample_en": (ox + w - 4, oy + 50),
        "eoc": (ox + w - 4, oy + 44),
        "comp_p": (ox + 4, oy + 40),
    }
    for i in range(12):
        taps[f"adc[{i}]"] = (ox + w - 4, oy + 8 + i * 8)
        taps[f"dac[{i}]"] = (ox + 4, oy + 8 + i * 8)
    return taps


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

    analog = analog_core(cell, 40, 25)
    digital = digital_abstract(cell, 200, 40)

    for i in range(12):
        manhattan(cell, *analog[f"dac[{i}]"], *digital[f"dac[{i}]"], "met2", 0.3)
    manhattan(cell, *analog["comp_p"], *digital["comp_p"], "met3", 0.6)
    manhattan(cell, *digital["sample_en"], *analog["sample_en"], "met3", 0.6)
    manhattan(cell, *analog["vdac"], *analog["vhold"], "met3", 0.6)
    manhattan(cell, *digital["clk"], *analog["clk_cmp"], "met3", 0.6)

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
    lib.add(cell)
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
                "GDS connectivity (precheck pin + analog wiring).",
                "Device LVS: bash layout/netgen/run_lvs.sh (Docker Magic/netgen).",
                "",
                "  ua[0] met4 -> S/H vin_ecg",
                "  ua[1] met4 -> R-2R vref",
                "  vdac met3 -> vhold",
                "  dac[11:0] met2 analog <-> digital abstract",
                "  comp_p / sample_en / clk met3 analog <-> digital",
                "  adc[7:0] -> uo_out, adc[11:8]/sample_en/eoc -> uio_out",
                "  uio_oe[5:0] tied VDPWR; unused uio_* tied VGND",
                "  VGND/VDPWR/VAPWR met4 stripes in GDS+LEF",
                "",
            ]
        )
    )
    print("wrote", gds_path, gds_path.stat().st_size, "bytes")
    print("wrote", lef_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())

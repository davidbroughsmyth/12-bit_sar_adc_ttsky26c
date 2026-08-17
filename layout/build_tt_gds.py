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


def add_pad(cell, layer, cx, cy, s=0.6):
    add_rect(cell, layer, cx - s / 2, cy - s / 2, s, s)


def via_stack(cell, cx, cy, upper: str, lower: str, pad=0.6):
    """Stack vias between met4..met1. Pads satisfy met3 min-area 0.24 um^2."""
    order = ["met1", "met2", "met3", "met4"]
    vias = {("met1", "met2"): ("via", 0.15), ("met2", "met3"): ("via2", 0.2), ("met3", "met4"): ("via3", 0.2)}
    u, l = order.index(upper), order.index(lower)
    if u < l:
        u, l = l, u
        upper, lower = lower, upper
    for i in range(l, u):
        a, b = order[i], order[i + 1]
        vname, vs = vias[(a, b)]
        add_pad(cell, a, cx, cy, pad)
        add_pad(cell, b, cx, cy, pad)
        add_rect(cell, vname, cx - vs / 2, cy - vs / 2, vs, vs)


def seg_v(cell, x, y0, y1, layer, width=0.4):
    add_rect(cell, layer, x - width / 2, min(y0, y1) - width / 2, width, abs(y1 - y0) + width)


def seg_h(cell, y, x0, x1, layer, width=0.4):
    add_rect(cell, layer, min(x0, x1) - width / 2, y - width / 2, abs(x1 - x0) + width, width)


class OrthoRouter:
    """Verticals on met3, horizontals on met2. Every net gets unique tracks (no wrap)."""

    DIG_W, DIG_E, DIG_N, DIG_S = 200.0, 310.0, 180.0, 40.0

    def __init__(self, cell):
        self.cell = cell
        self.jog_y = 196.0
        self.pwr_y = 4.0
        self.bot_y = 6.0
        self.west_x = 10.6
        self.over_y = 168.4
        self.alley_y = 106.72
        self.east_n = 0
        self.corr_n = 0

    def _alloc(self, attr: str, step: float, limit: float, name: str) -> float:
        v = getattr(self, attr)
        setattr(self, attr, v + step)
        if v + step > limit:
            print(f"warning: {name} track {v:.3f} near limit {limit}")
        return v

    def alloc_jog(self) -> float:
        return self._alloc("jog_y", 0.5, 222.5, "top jog Y")

    def alloc_pwr(self) -> float:
        return self._alloc("pwr_y", 0.8, 16.0, "power Y")

    def alloc_bot(self) -> float:
        return self._alloc("bot_y", 2.0, 14.0, "bottom Y")

    def alloc_west(self) -> float:
        return self._alloc("west_x", 1.4, 16.0, "west X")

    def alloc_over(self) -> float:
        return self._alloc("over_y", 0.7, 185.5, "over-analog Y")

    def alloc_alley(self) -> float:
        # Unique Y for each met2 alley run (width 0.16, pitch 0.32).
        return self._alloc("alley_y", 0.32, 111.3, "R-2R alley Y")

    def _alloc_pair(self, counter: str, origin: float, step: float, nslots: int, name: str):
        """nslots unique coordinates on met3, then the same coordinates on met1.

        Pairing is delayed so the first nslots nets (and their met2 jogs) are far
        from the reuse set; 0.5 um pads on a shared X then do not overlap.
        """
        i = getattr(self, counter)
        setattr(self, counter, i + 1)
        if i >= nslots * 2:
            print(f"warning: {name} overflow slot {i} (max {nslots * 2})")
        coord = origin + (i % nslots) * step
        layer = "met3" if i < nslots else "met1"
        return coord, layer

    def alloc_east(self):
        return self._alloc_pair("east_n", 310.7, 0.75, 10, "east X")

    def alloc_corr(self):
        return self._alloc_pair("corr_n", 190.55, 1.05, 8, "corridor X")

    @staticmethod
    def _vert(a, b) -> bool:
        return abs(a[0] - b[0]) < 0.15

    def wire_ortho(self, pts, start="met3", end="met3", vlayers=None, hwidth=0.4):
        """Polyline: horizontals on met2; verticals on vlayers[i] or met3."""
        c = self.cell
        pad = 0.4

        def vl(i):
            if vlayers is None:
                return "met3"
            if isinstance(vlayers, str):
                return vlayers
            return vlayers[i]

        def vwidth(layer):
            return 0.28 if layer == "met1" else 0.4

        p0, p1 = pts[0], pts[1]
        first_v = self._vert(p0, p1)
        fl = vl(0) if first_v else "met2"
        if start != fl:
            via_stack(c, p0[0], p0[1], fl, start, pad=pad)
        else:
            add_pad(c, fl, p0[0], p0[1], pad)
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]
            if self._vert(a, b):
                layer = vl(i)
                if i > 0 and not self._vert(pts[i - 1], pts[i]):
                    via_stack(c, a[0], a[1], "met2", layer, pad=pad)
                elif i > 0 and self._vert(pts[i - 1], pts[i]) and vl(i - 1) != layer:
                    via_stack(c, a[0], a[1], vl(i - 1), layer, pad=pad)
                seg_v(c, a[0], a[1], b[1], layer, vwidth(layer))
            else:
                if i > 0 and self._vert(pts[i - 1], pts[i]):
                    via_stack(c, a[0], a[1], vl(i - 1), "met2", pad=pad)
                seg_h(c, a[1], a[0], b[0], "met2", hwidth)
        pe = pts[-1]
        last_i = len(pts) - 2
        last_v = self._vert(pts[-2], pts[-1])
        el = vl(last_i) if last_v else "met2"
        if end != el:
            via_stack(c, pe[0], pe[1], el, end, pad=pad)
        else:
            add_pad(c, el, pe[0], pe[1], pad)

    def dest_side(self, x, y) -> str:
        if x >= self.DIG_E - 4:
            return "east"
        if self.DIG_W < x < self.DIG_E and y >= self.DIG_N:
            return "north"
        if self.DIG_W < x < self.DIG_E and y <= self.DIG_S:
            return "south"
        return "other"

    def connect_south_analog(self, x0, y0, x1, y1, start="met3", end="met1"):
        """ua[0]/ua[1]: unique bottom Y + west X so the two analog pads never share a jog."""
        yj = self.alloc_bot()
        xw = self.alloc_west()
        self.wire_ortho([(x0, y0), (x0, yj), (xw, yj), (xw, y1), (x1, y1)], start, end)

    def _around_from_analog(self, xa, ya, xd, yd, start, end):
        """Analog tap -> corridor west of digital -> top channel -> digital pin.

        R-2R dac taps sit just under the S/H/comparator. They escape north into the
        106–112 µm alley (unique Y / layer), then the 190–200 µm corridor (unique X /
        layer), then over the digital macro. Last mile is vertical on unique pin X,
        or unique east-X then horizontal on unique pin Y — never a shared dest-Y bar.
        """
        xc, c_layer = self.alloc_corr()
        yj = self.alloc_jog()
        if ya < 106.0:
            y_al = self.alloc_alley()
            pts = [(xa, ya), (xa, y_al), (xc, y_al)]
            vlayers = ["met3", "met3", c_layer]
        else:
            ym = self.alloc_over()
            pts = [(xa, ya), (xa, ym), (xc, ym)]
            vlayers = ["met3", "met3", c_layer]
        pts.append((xc, yj))
        if self.dest_side(xd, yd) == "east":
            xt, e_layer = self.alloc_east()
            pts += [(xt, yj), (xt, yd), (xd, yd)]
            vlayers += ["met3", e_layer, "met3"]
        else:
            pts += [(xd, yj), (xd, yd)]
            vlayers += ["met3", "met3"]
        self.wire_ortho(pts, start, end, vlayers=vlayers, hwidth=0.16)

    def connect(self, x0, y0, x1, y1, start="met3", end="met3"):
        """Orthogonal path: met3 verticals + met2 horizontals + unique tracks."""
        if abs(x0 - x1) < 0.2:
            self.wire_ortho([(x0, y0), (x0, y1)], start, end)
            return
        if abs(y0 - y1) < 0.2:
            self.wire_ortho([(x0, y0), (x1, y1)], start, end)
            return
        analog_to_dig = x0 < 190 and y0 < 175 and x1 > 198
        dig_to_analog = x0 > 198 and x1 < 190 and y1 < 175
        if analog_to_dig:
            self._around_from_analog(x0, y0, x1, y1, start, end)
            return
        if dig_to_analog:
            self._around_from_analog(x1, y1, x0, y0, end, start)
            return
        yj = self.alloc_jog()
        if self.dest_side(x1, y1) == "east":
            xt, e_layer = self.alloc_east()
            self.wire_ortho(
                [(x0, y0), (x0, yj), (xt, yj), (xt, y1), (x1, y1)],
                start,
                end,
                vlayers=["met3", "met3", e_layer, "met3"],
            )
        else:
            self.wire_ortho([(x0, y0), (x0, yj), (x1, yj), (x1, y1)], start, end)


def escape_pin(cell, name, px, py, lx, ly, hx, hy) -> tuple[float, float]:
    """met4 pin (TT) + 1.8 um stub + via3. Signal continues on met3."""
    pin_met4(cell, name, px, py, lx, ly, hx, hy)
    vy = py - 1.8 if py > 100 else py + 1.8
    seg_v(cell, px, py, vy, "met4", 0.3)
    via_stack(cell, px, vy, "met4", "met3")
    return px, vy


GDS_LAYER_TO_MET = {68: "met1", 69: "met2", 70: "met3", 71: "met4"}


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


def digital_taps_from_gds(cell: gdstk.Cell, ox: float, oy: float) -> dict[str, tuple[float, float, str]]:
    names: dict[str, tuple[float, float, str]] = {}
    bb = cell.bounding_box()
    (x0, y0), (x1, y1) = bb if bb else ((0, 0), (0, 0))
    for lab in cell.labels:
        lx, ly = lab.origin
        on_edge = lx <= x0 + 3 or lx >= x1 - 3 or ly <= y0 + 3 or ly >= y1 - 3
        met = GDS_LAYER_TO_MET.get(lab.layer, "met2")
        val = (lx + ox, ly + oy, met)
        if on_edge:
            names[lab.text] = val
        elif lab.text not in names:
            names[lab.text] = val
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
            "clk": (ox_dig + 8, oy_dig + 2, "met2"),
            "rst_n": (ox_dig + 16, oy_dig + 2, "met2"),
            "ena": (ox_dig + 24, oy_dig + 2, "met2"),
            "sample_en": (ox_dig + 50, oy_dig + 2, "met2"),
            "eoc": (ox_dig + 108, oy_dig + 48, "met3"),
            "comp_p": (ox_dig + 108, oy_dig + 72, "met3"),
        }
        for i in range(12):
            digital[f"adc[{i}]"] = (ox_dig + 108, oy_dig + 40 + i * 8, "met3")
            digital[f"dac[{i}]"] = (ox_dig + 108, oy_dig + 42 + i * 8, "met3")

    rt = OrthoRouter(cell)

    def axy(name):
        return analog[name][0], analog[name][1]

    def dxy(name):
        t = digital[name]
        return t[0], t[1], t[2] if len(t) > 2 else "met2"

    # Analog SAR loop (met1 device pins)
    rt.connect(*axy("vdac"), *axy("vhold"), start="met1", end="met1")
    rt.connect(*axy("comp_p"), *dxy("comp_p")[:2], start="met1", end=dxy("comp_p")[2])
    rt.connect(*dxy("sample_en")[:2], *axy("sample_en"), start=dxy("sample_en")[2], end="met1")
    rt.connect(*dxy("clk")[:2], *axy("clk_cmp"), start=dxy("clk")[2], end="met1")
    for i in range(12):
        dx, dy, dl = dxy(f"dac[{i}]")
        rt.connect(*axy(f"dac[{i}]"), dx, dy, start="met1", end=dl)

    # Analog supplies: via onto VAPWR / VGND stripes (no met4 crossing other rails)
    ax, ay = axy("avdd")
    rt.connect(ax, ay, 8.0, ay, start="met1", end="met3")
    via_stack(cell, 8.0, ay, "met3", "met4")
    gx, gy = axy("avss")
    rt.connect(gx, gy, 5.0, gy, start="met1", end="met3")
    via_stack(cell, 5.0, gy, "met3", "met4")
    # Digital 1.8 V / GND: hop on met3 over VGND/VAPWR stripes, then met4 east of x=12
    via_stack(cell, 2.0, 210.0, "met4", "met3")
    seg_h(cell, 210.0, 2.0, 16.0, "met3", 0.6)
    via_stack(cell, 16.0, 210.0, "met3", "met4")
    add_rect(cell, "met4", 16.0, 210.0, 198.0, 1.6)
    via_stack(cell, 5.0, 214.0, "met4", "met3")
    seg_h(cell, 214.0, 5.0, 16.0, "met3", 0.6)
    via_stack(cell, 16.0, 214.0, "met3", "met4")
    add_rect(cell, "met4", 16.0, 214.0, 198.0, 1.6)

    pin_met3 = {}
    for p in pins:
        px, py = p["xy"]
        lx, ly, hx, hy = p["rect"]
        pin_met3[p["name"]] = escape_pin(cell, p["name"], px, py, lx, ly, hx, hy)

    def hook(pin_name, tap_xy, end_layer="met2"):
        x0, y0 = pin_met3[pin_name]
        rt.connect(x0, y0, tap_xy[0], tap_xy[1], start="met3", end=end_layer)

    def tie_power(pin_name, stripe_x):
        x0, y0 = pin_met3[pin_name]
        yb = rt.alloc_pwr()
        rt.connect(x0, y0, stripe_x, yb, start="met3", end="met3")
        via_stack(cell, stripe_x, yb, "met3", "met4")

    x0, y0 = pin_met3["ua[0]"]
    rt.connect_south_analog(x0, y0, *axy("vin_ecg"), start="met3", end="met1")
    x1, y1 = pin_met3["ua[1]"]
    rt.connect_south_analog(x1, y1, *axy("vref"), start="met3", end="met1")
    hook("clk", dxy("clk")[:2], dxy("clk")[2])
    hook("rst_n", dxy("rst_n")[:2], dxy("rst_n")[2])
    hook("ena", dxy("ena")[:2], dxy("ena")[2])
    for i in range(8):
        hook(f"uo_out[{i}]", dxy(f"adc[{i}]")[:2], dxy(f"adc[{i}]")[2])
    for i in range(4):
        hook(f"uio_out[{i}]", dxy(f"adc[{i + 8}]")[:2], dxy(f"adc[{i + 8}]")[2])
    hook("uio_out[4]", dxy("sample_en")[:2], dxy("sample_en")[2])
    hook("uio_out[5]", dxy("eoc")[:2], dxy("eoc")[2])
    for i in range(6):
        tie_power(f"uio_oe[{i}]", vdpwr_x)
    for name in ("uio_oe[6]", "uio_oe[7]", "uio_out[6]", "uio_out[7]"):
        tie_power(name, vgnd_x)

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

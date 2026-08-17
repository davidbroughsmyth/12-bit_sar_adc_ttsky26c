#!/usr/bin/env python3
"""Punch Sky130 via1/via2/via3 at coordinates logged by the Magic analog script."""
from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

import gdstk

VIA = {"via1": (68, 44), "via2": (69, 44), "via3": (70, 44), "mcon": (67, 44)}
CUT = {"via1": 0.15, "via2": 0.20, "via3": 0.20, "mcon": 0.17}
POINTS = Path(__file__).resolve().parent / "via_points.txt"


def add_cut(cell, x, y, layer, dt, cut):
    cell.add(
        gdstk.rectangle(
            (x - cut / 2, y - cut / 2),
            (x + cut / 2, y + cut / 2),
            layer=layer,
            datatype=dt,
        )
    )


def load_points(path: Path):
    by_cell = defaultdict(list)
    if not path.exists():
        return by_cell
    for line in path.read_text().splitlines():
        parts = line.split()
        if len(parts) != 4:
            continue
        cell, kind, xs, ys = parts
        by_cell[cell].append((kind, float(xs), float(ys)))
    return by_cell


def main(gds_path: str) -> int:
    p = Path(gds_path)
    pts = load_points(POINTS)
    lib = gdstk.read_gds(str(p))
    n = 0
    for c in lib.cells:
        for kind, x, y in pts.get(c.name, []):
            if kind not in VIA:
                continue
            add_cut(c, x, y, *VIA[kind], CUT[kind])
            n += 1
    if n:
        lib.write_gds(str(p))
    print(f"punched {n} vias into {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "layout/gds/r2r_dac_magic.gds"))

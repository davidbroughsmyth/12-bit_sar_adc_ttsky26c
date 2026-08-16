"""AD8232-like analog front-end (SparkFun single-lead HRM behavioral model)."""
from __future__ import annotations

import math

# SparkFun AD8232: 3.3 V, mid-rail output, gain ~1100, ~0.5-40 Hz.
GAIN = 1100.0
VMID = 1.65
VDD = 3.3
F_HP = 0.5
F_LP = 40.0


def clamp(v: float, lo: float = 0.05, hi: float = 3.25) -> float:
    return lo if v < lo else hi if v > hi else v


def electrode_to_adc(v_body_v: float) -> float:
    """Instantaneous (no filter) mapping for sampled 500 SPS beats already band-limited."""
    return clamp(VMID + GAIN * v_body_v)


def biquad_lp_hp(x, fs: float = 500.0):
    """Simple one-pole HP + one-pole LP on a voltage series (body volts)."""
    a_hp = math.exp(-2 * math.pi * F_HP / fs)
    a_lp = math.exp(-2 * math.pi * F_LP / fs)
    y = []
    hp = 0.0
    lp = 0.0
    prev = 0.0
    for v in x:
        hp = a_hp * (hp + v - prev)
        prev = v
        lp = lp + (1 - a_lp) * (hp - lp)
        y.append(clamp(VMID + GAIN * lp))
    return y

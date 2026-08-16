"""Test waveforms at 500 SPS: sine, spike, ramp up, ramp down."""
from __future__ import annotations

import math

from sar_golden import FS, VREF_DEFAULT, convert_series, reconstruct


def sine(n: int, freq: float = 5.0, vpp: float = 1.2, vcm: float = 1.65) -> list[float]:
    return [
        vcm + 0.5 * vpp * math.sin(2 * math.pi * freq * i / FS)
        for i in range(n)
    ]


def spike(n: int, vcm: float = 1.65, height: float = 1.2, width: int = 3) -> list[float]:
    y = [vcm] * n
    c = n // 2
    for i in range(c, min(n, c + width)):
        y[i] = min(VREF_DEFAULT * 4095 / 4096, vcm + height)
    return y


def ramp_up(n: int, vlo: float = 0.1, vhi: float = 3.2) -> list[float]:
    if n <= 1:
        return [vlo]
    return [vlo + (vhi - vlo) * i / (n - 1) for i in range(n)]


def ramp_down(n: int, vlo: float = 0.1, vhi: float = 3.2) -> list[float]:
    return list(reversed(ramp_up(n, vlo, vhi)))


def metrics(vin: list[float], codes: list[int]) -> dict:
    lsb = VREF_DEFAULT / 4096.0
    rec = [reconstruct(c) for c in codes]
    err = [(r - v) / lsb for v, r in zip(vin, rec)]
    rms = math.sqrt(sum(e * e for e in err) / len(err))
    mean_v = sum(vin) / len(vin)
    ps = sum((v - mean_v) ** 2 for v in vin)
    pn = sum((v - r) ** 2 for v, r in zip(vin, rec))
    snr = 10 * math.log10(ps / pn) if pn > 0 else float("inf")
    return {
        "n": len(vin),
        "max_abs_lsb": max(abs(e) for e in err),
        "rms_lsb": rms,
        "mean_lsb": sum(err) / len(err),
        "snr_db": snr,
    }

"""Golden 12-bit SAR model matching rtl/sar_fsm.v (Vdac = Vref * code / 4096)."""
from __future__ import annotations

NBITS = 12
NCODES = 1 << NBITS
VREF_DEFAULT = 3.3
FS = 500.0


def sar_convert(vin: float, vref: float = VREF_DEFAULT) -> int:
    vin = min(max(vin, 0.0), vref * (NCODES - 1) / NCODES)
    result = 0
    for i in range(NBITS - 1, -1, -1):
        trial = result | (1 << i)
        vdac = vref * trial / NCODES
        if vin >= vdac:
            result = trial
    return result


def reconstruct(code: int, vref: float = VREF_DEFAULT) -> float:
    return vref * code / NCODES


def convert_series(v: list[float] | tuple, vref: float = VREF_DEFAULT) -> list[int]:
    return [sar_convert(x, vref) for x in v]


def error_lsb(vin, code, vref: float = VREF_DEFAULT) -> float:
    return (reconstruct(code, vref) - vin) / (vref / NCODES)

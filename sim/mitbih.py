"""MIT-BIH Arrhythmia helpers: AAMI 5-class map, fetch, synthetic fixtures."""
from __future__ import annotations

import math
import os
from pathlib import Path

from ad8232 import electrode_to_adc
from sar_golden import FS

# AAMI EC57 / ANSI: N, S, V, F, Q
AAMI = {
    "N": "N", "L": "N", "R": "N", "e": "N", "j": "N",
    "A": "S", "a": "S", "J": "S", "S": "S",
    "V": "V", "E": "V",
    "F": "F",
    "/": "Q", "f": "Q", "Q": "Q", "P": "Q", "U": "Q",
}

# Records that typically contain each class (PhysioNet MIT-BIH 1.0.0)
CLASS_RECORDS = {
    "N": "100",
    "S": "209",
    "V": "200",
    "F": "208",
    "Q": "217",
}

PHYSIONET = "https://physionet.org/files/mitdb/1.0.0/"


def aami_class(symbol: str) -> str | None:
    return AAMI.get(symbol)


def _qrs(t: float, width: float, amp: float) -> float:
    return amp * math.exp(-((t / width) ** 2))


def synthetic_beat(kind: str, n: int = 250, fs: float = FS) -> list[float]:
    """One ~0.5 s beat in electrode volts (mV-scale / 1000)."""
    y = [0.0] * n
    t0 = 0.18
    for i in range(n):
        t = i / fs - t0
        if kind == "N":
            y[i] = (
                0.00012 * math.exp(-((t + 0.12) / 0.025) ** 2)
                - 0.00015 * math.exp(-((t + 0.02) / 0.012) ** 2)
                + _qrs(t, 0.018, 0.0011)
                - 0.00025 * math.exp(-((t - 0.04) / 0.02) ** 2)
                + 0.00025 * math.exp(-((t - 0.22) / 0.05) ** 2)
            )
        elif kind == "S":
            y[i] = (
                0.0002 * math.exp(-((t + 0.06) / 0.02) ** 2)
                + _qrs(t, 0.016, 0.0009)
                + 0.0002 * math.exp(-((t - 0.18) / 0.04) ** 2)
            )
        elif kind == "V":
            y[i] = _qrs(t, 0.055, 0.0016) - 0.0004 * math.exp(-((t - 0.08) / 0.06) ** 2)
        elif kind == "F":
            nrm = synthetic_beat("N", n, fs)[i]
            ven = synthetic_beat("V", n, fs)[i]
            y[i] = 0.55 * nrm + 0.45 * ven
        else:  # Q unknown / artifact
            y[i] = 0.0004 * math.sin(2 * math.pi * 8 * i / fs) + 0.0008 * (
                1 if 40 < i < 48 else 0
            )
    return y


def synthetic_record(kind: str, beats: int = 4) -> tuple[list[float], list[str]]:
    sig = []
    labels = []
    for _ in range(beats):
        sig.extend(synthetic_beat(kind))
        labels.append(kind)
    adc = [electrode_to_adc(v) for v in sig]
    return adc, labels


def load_offline_fixtures() -> dict[str, list[float]]:
    return {k: synthetic_record(k)[0] for k in ("N", "S", "V", "F", "Q")}


def _download_record(record: str, dest: Path) -> bool:
    dest.mkdir(parents=True, exist_ok=True)
    try:
        from urllib.request import Request, urlopen
    except ImportError:
        return False
    for ext in (".hea", ".dat", ".atr"):
        path = dest / f"{record}{ext}"
        if path.exists() and path.stat().st_size > 0:
            continue
        url = f"{PHYSIONET}{record}{ext}"
        try:
            req = Request(url, headers={"User-Agent": "sar-adc-tests/1.0"})
            with urlopen(req, timeout=30) as r, path.open("wb") as f:
                f.write(r.read())
        except Exception:
            return False
    return True


def try_fetch_mitbih(record: str, channel: int = 0):
    """Return (signal_mV, symbols, samples, fs) or None if unavailable."""
    dest = Path(os.environ.get("MITDB_PATH", str(Path(__file__).resolve().parents[1] / "results" / "mitdb")))
    dest.mkdir(parents=True, exist_ok=True)
    if not _download_record(record, dest):
        return None
    try:
        import wfdb

        rec = wfdb.rdrecord(str(dest / record))
        ann = wfdb.rdann(str(dest / record), "atr")
        sig = rec.p_signal[:, channel]
        return sig, list(ann.symbol), list(ann.sample), float(rec.fs)
    except Exception:
        return _read_mitbih_minimal(dest, record, channel)


def _read_mitbih_minimal(dest: Path, record: str, channel: int):
    hea = (dest / f"{record}.hea").read_text(errors="replace").splitlines()
    parts = hea[0].split()
    nsig = int(parts[1])
    fs = float(parts[2])
    nsamp = int(parts[3])
    gains, baselines = [], []
    for line in hea[1 : 1 + nsig]:
        f = line.split()
        gains.append(float(f[2]))
        baselines.append(int(f[4]))
    raw = (dest / f"{record}.dat").read_bytes()
    sigs = [[] for _ in range(nsig)]
    i = 0
    pair = 0
    while i + 2 < len(raw) and pair < nsamp:
        b0, b1, b2 = raw[i], raw[i + 1], raw[i + 2]
        s0 = b0 | ((b1 & 0x0F) << 8)
        s1 = b2 | ((b1 & 0xF0) << 4)
        if s0 & 0x800:
            s0 -= 4096
        if s1 & 0x800:
            s1 -= 4096
        if nsig >= 2:
            sigs[0].append((s0 - baselines[0]) / gains[0])
            sigs[1].append((s1 - baselines[1]) / gains[1])
        else:
            sigs[0].append((s0 - baselines[0]) / gains[0])
        i += 3
        pair += 1
    symbols, samples = _read_atr(dest / f"{record}.atr")
    ch = min(channel, max(0, nsig - 1))
    return sigs[ch], symbols, samples, fs


def _read_atr(path: Path):
    data = path.read_bytes()
    symbols, samples = [], []
    t = 0
    i = 0
    mit_ann = {
        1: "N", 2: "L", 3: "R", 4: "a", 5: "V", 6: "F", 7: "J", 8: "A",
        9: "S", 10: "E", 11: "j", 12: "n", 13: "E", 14: "/", 15: "Q",
    }
    while i + 1 < len(data):
        w = data[i] | (data[i + 1] << 8)
        i += 2
        anntyp = w >> 10
        dt = w & 0x3FF
        if anntyp == 59:
            if i + 3 < len(data):
                hi = data[i] | (data[i + 1] << 8)
                lo = data[i + 2] | (data[i + 3] << 8)
                if hi & 0x8000:
                    hi -= 65536
                t += (hi << 16) | lo
                i += 4
            continue
        if anntyp == 63:
            t += dt
            if i < len(data):
                n = data[i]
                i += 1 + n + (n & 1)
            continue
        if anntyp in (61, 62):
            t += dt
            i += 2
            continue
        t += dt
        if anntyp in mit_ann:
            symbols.append(mit_ann[anntyp])
            samples.append(t)
    return symbols, samples


def resample(x, fs_in: float, fs_out: float = FS) -> list[float]:
    if abs(fs_in - fs_out) < 1e-6:
        return list(x)
    n_out = int(len(x) * fs_out / fs_in)
    y = []
    for i in range(n_out):
        t = i * fs_in / fs_out
        j = int(t)
        f = t - j
        if j + 1 < len(x):
            y.append((1 - f) * x[j] + f * x[j + 1])
        else:
            y.append(x[-1])
    return y

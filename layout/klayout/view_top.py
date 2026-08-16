#!/usr/bin/env python3
"""Open sar_adc_top.gds in KLayout if installed."""
import shutil
import subprocess
import sys
from pathlib import Path

gds = Path(__file__).resolve().parents[1] / "gds" / "sar_adc_top.gds"
kl = shutil.which("klayout")
if not kl:
    print("klayout not found; GDS is at", gds)
    sys.exit(0)
subprocess.check_call([kl, str(gds)])

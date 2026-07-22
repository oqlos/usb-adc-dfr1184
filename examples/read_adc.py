"""Minimal example: PYTHONPATH=src python examples/read_adc.py."""

from __future__ import annotations

from usb_adc_dfr1184 import DFR1184

device = DFR1184()
for reading in device.read_all_adc(samples=8):
    print(f"{reading.input_name}: {reading.volts:.4f} V")

from __future__ import annotations

import io
import json

from usb_adc_dfr1184.cli import run
from usb_adc_dfr1184.driver import DFR1184, DFR1184Config

from .test_driver import FakeBackend


def factory(config: DFR1184Config) -> DFR1184:
    return DFR1184(config=config, backend=FakeBackend([250_000]))


def test_adc_command_returns_json_and_selected_uart() -> None:
    stdout = io.StringIO()

    result = run(
        ["--serial-port", "/dev/ttyAMA0", "adc", "1"],
        driver_factory=factory,
        stdout=stdout,
    )

    payload = json.loads(stdout.getvalue())
    assert result == 0
    assert payload["volts"] == 2.5
    assert payload["transport"] == "uart"
    assert payload["endpoint"] == "/dev/ttyAMA0"


def test_health_reports_missing_device_with_nonzero_exit() -> None:
    stdout = io.StringIO()

    def missing_factory(config: DFR1184Config) -> DFR1184:
        return DFR1184(config=config, backend=FakeBackend(available=False))

    assert run(["health"], driver_factory=missing_factory, stdout=stdout) == 1
    assert json.loads(stdout.getvalue())["status"] == "not_found"

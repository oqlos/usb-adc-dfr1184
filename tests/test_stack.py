from __future__ import annotations

import sys
from dataclasses import dataclass
from types import ModuleType
from typing import Any

import pytest

from usb_adc_dfr1184.driver import DFR1184
from usb_adc_dfr1184.models import HealthStatus
from usb_adc_dfr1184.stack import ADCStack, _default_mcp2221

from .test_driver import FakeBackend


@dataclass
class FakeReading:
    volts: float

    def to_dict(self) -> dict[str, Any]:
        return {"volts": self.volts}


@dataclass
class FakeMCPHealth:
    ok: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "status": "connected"}


class FakeMCP2221:
    def read_adc(self, channel: int, samples: int = 1) -> FakeReading:
        return FakeReading(1.25)

    def health(self) -> FakeMCPHealth:
        return FakeMCPHealth()


class HealthyDFR1184(DFR1184):
    def health(self) -> HealthStatus:
        return HealthStatus(True, "connected", "test", "uart", self.config.serial_port)


def make_stack() -> ADCStack:
    dfr1184 = HealthyDFR1184(backend=FakeBackend([250_000, 750_000]))
    return ADCStack(mcp2221=FakeMCP2221(), dfr1184=dfr1184)


def test_stack_maps_three_logical_channels() -> None:
    readings = make_stack().read_all_adc()

    assert [reading["logical_name"] for reading in readings] == ["ai01", "ai02", "ai03"]
    assert readings[0]["physical_input"] == "MCP2221A.G1"
    assert readings[1]["physical_input"] == "DFR1184.AIN1"
    assert readings[2]["physical_input"] == "DFR1184.AIN2"
    assert readings[2]["reading"]["volts"] == 7.5


def test_stack_health_and_validation() -> None:
    stack = make_stack()

    assert stack.health()["ok"] is True
    with pytest.raises(ValueError, match="1, 2 or 3"):
        stack.read_adc(4)


def test_default_stack_passes_environment_to_mcp2221(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}
    module = ModuleType("usb_adc_mcp2221")

    class Config:
        def __init__(self, **kwargs: Any) -> None:
            captured.update(kwargs)

    class Driver:
        def __init__(self, config: Config) -> None:
            self.config = config

    module.MCP2221 = Driver
    module.MCP2221Config = Config
    monkeypatch.setitem(sys.modules, "usb_adc_mcp2221", module)
    monkeypatch.setenv("MCP2221_REFERENCE_VOLTAGE", "3.28")
    monkeypatch.setenv("MCP2221_BACKEND", "easy")
    monkeypatch.setenv("MCP2221_DEVICE_INDEX", "1")
    monkeypatch.setenv("MCP2221_USB_SERIAL", "sensor-a")
    monkeypatch.setenv("MCP2221_SCAN_SERIAL", "true")
    monkeypatch.setenv("MCP2221_OPEN_TIMEOUT", "1.5")
    monkeypatch.setenv("MCP2221_READ_TIMEOUT_MS", "200")
    monkeypatch.setenv("MCP2221_COMMAND_RETRIES", "1")

    driver = _default_mcp2221()

    assert isinstance(driver, Driver)
    assert captured == {
        "reference_voltage": 3.28,
        "backend": "easy",
        "device_index": 1,
        "usb_serial": "sensor-a",
        "scan_serial": True,
        "open_timeout": 1.5,
        "read_timeout_ms": 200,
        "command_retries": 1,
    }

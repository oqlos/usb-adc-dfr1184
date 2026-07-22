from __future__ import annotations

import pytest

from usb_adc_dfr1184.driver import DFR1184, DFR1184Config
from usb_adc_dfr1184.errors import DFR1184Error, DFR1184ProtocolError


class FakeBackend:
    def __init__(
        self,
        raw_values: list[int] | None = None,
        *,
        available: bool = True,
        error: DFR1184Error | None = None,
    ) -> None:
        self.raw_values = iter(raw_values or [500_000])
        self.available = available
        self.error = error

    def probe(self) -> bool:
        if self.error:
            raise self.error
        return self.available

    def read_raw(self, channel: int) -> int:
        return next(self.raw_values)


def test_voltage_conversion_and_averaging() -> None:
    driver = DFR1184(backend=FakeBackend([123_400, 123_512]))

    reading = driver.read_adc(1, samples=2)

    assert reading.raw_hundredth_millivolts == 123_456
    assert reading.millivolts == 1234.56
    assert reading.volts == 1.23456
    assert reading.input_name == "AIN1"


@pytest.mark.parametrize("channel", [0, 3, -1])
def test_invalid_channel_is_rejected(channel: int) -> None:
    with pytest.raises(ValueError, match="channel"):
        DFR1184(backend=FakeBackend()).read_adc(channel)


def test_implausible_protocol_value_is_rejected() -> None:
    with pytest.raises(DFR1184ProtocolError, match="implausible"):
        DFR1184(backend=FakeBackend([1_100_001])).read_adc(1)


def test_health_distinguishes_connected_missing_and_bus_error() -> None:
    assert DFR1184(backend=FakeBackend()).health().status == "connected"
    assert DFR1184(backend=FakeBackend(available=False)).health().status == "not_found"
    health = DFR1184(backend=FakeBackend(error=DFR1184Error("USB unavailable"))).health()
    assert health.status == "unavailable"
    assert "USB unavailable" in health.message


def test_uart_configuration_is_validated() -> None:
    with pytest.raises(ValueError, match="baudrate"):
        DFR1184Config(baudrate=115_200)
    with pytest.raises(ValueError, match="serial_port"):
        DFR1184Config(serial_port="")

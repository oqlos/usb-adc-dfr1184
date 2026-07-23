"""Logical ADC stack combining MCP2221A USB and DFR1184 Raspberry Pi UART."""

from __future__ import annotations

import os
import threading
from typing import Any, Protocol, cast

from .driver import DFR1184


class SerializableReading(Protocol):
    def to_dict(self) -> dict[str, Any]: ...


class SerializableHealth(Protocol):
    @property
    def ok(self) -> bool: ...

    def to_dict(self) -> dict[str, Any]: ...


class MCP2221Driver(Protocol):
    def read_adc(self, channel: int, samples: int = 1) -> SerializableReading: ...

    def health(self) -> SerializableHealth: ...


def _default_mcp2221() -> MCP2221Driver:
    try:
        from usb_adc_mcp2221 import MCP2221, MCP2221Config  # type: ignore[import-not-found]
    except ImportError as error:
        raise RuntimeError(
            "install the sibling MCP2221A driver first: pip install -e ../usb-adc-mcp2221"
        ) from error
    scan_serial = os.getenv("MCP2221_SCAN_SERIAL", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    config = MCP2221Config(
        reference_voltage=float(os.getenv("MCP2221_REFERENCE_VOLTAGE", "3.3")),
        backend=os.getenv("MCP2221_BACKEND", "easy"),
        device_index=int(os.getenv("MCP2221_DEVICE_INDEX", "0")),
        usb_serial=os.getenv("MCP2221_USB_SERIAL") or None,
        scan_serial=scan_serial,
        open_timeout=float(os.getenv("MCP2221_OPEN_TIMEOUT", "1.0")),
        read_timeout_ms=int(os.getenv("MCP2221_READ_TIMEOUT_MS", "250")),
        command_retries=int(os.getenv("MCP2221_COMMAND_RETRIES", "0")),
    )
    return cast(MCP2221Driver, MCP2221(config))


class ADCStack:
    """Expose both independent hardware transports as three logical ADC inputs."""

    def __init__(
        self,
        mcp2221: MCP2221Driver | None = None,
        dfr1184: DFR1184 | None = None,
    ) -> None:
        self.mcp2221 = mcp2221 or _default_mcp2221()
        self.dfr1184 = dfr1184 or DFR1184()
        self._lock = threading.RLock()

    @staticmethod
    def _channel(channel: int) -> int:
        if channel not in (1, 2, 3):
            raise ValueError("logical ADC channel must be 1, 2 or 3")
        return channel

    def _read_unlocked(self, channel: int, samples: int) -> dict[str, Any]:
        if channel == 1:
            reading = self.mcp2221.read_adc(1, samples=samples)
            adapter = "usb-adc-mcp2221"
            physical_input = "MCP2221A.G1"
            nominal_range = [0, 3.3]
        else:
            reading = self.dfr1184.read_adc(channel - 1, samples=samples)
            adapter = "usb-adc-dfr1184"
            physical_input = f"DFR1184.AIN{channel - 1}"
            nominal_range = [0, 10]
        return {
            "logical_channel": channel,
            "logical_name": f"ai{channel:02d}",
            "adapter": adapter,
            "physical_input": physical_input,
            "nominal_range_volts": nominal_range,
            "reading": reading.to_dict(),
        }

    def read_adc(self, channel: int, samples: int = 1) -> dict[str, Any]:
        channel = self._channel(channel)
        if not 1 <= samples <= 10_000:
            raise ValueError("samples must be between 1 and 10000")
        with self._lock:
            return self._read_unlocked(channel, samples)

    def read_all_adc(self, samples: int = 1) -> list[dict[str, Any]]:
        if not 1 <= samples <= 10_000:
            raise ValueError("samples must be between 1 and 10000")
        with self._lock:
            return [self._read_unlocked(channel, samples) for channel in (1, 2, 3)]

    def health(self) -> dict[str, Any]:
        with self._lock:
            mcp_health = self.mcp2221.health()
            dfr_health = self.dfr1184.health()
            return {
                "ok": mcp_health.ok and dfr_health.ok,
                "status": "connected" if mcp_health.ok and dfr_health.ok else "degraded",
                "components": {
                    "usb-adc-mcp2221": mcp_health.to_dict(),
                    "usb-adc-dfr1184": dfr_health.to_dict(),
                },
            }

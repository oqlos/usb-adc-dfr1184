"""Logical ADC stack combining MCP2221A USB and DFR1184 Raspberry Pi UART."""

from __future__ import annotations

import concurrent.futures
import os
from collections.abc import Callable
from typing import Any, Protocol, TypeVar, cast

from .driver import DFR1184

T = TypeVar("T")

OPERATION_TIMEOUT_SECONDS = float(os.getenv("USB_ADC_STACK_OPERATION_TIMEOUT", "2.5"))


def _run_with_timeout(
    operation: Callable[[], T],
    *,
    timeout: float | None = None,
) -> T:
    limit = OPERATION_TIMEOUT_SECONDS if timeout is None else timeout
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    future = executor.submit(operation)
    try:
        return future.result(timeout=limit)
    finally:
        # Do not wait on timed-out USB/UART work; otherwise /health blocks forever.
        executor.shutdown(wait=False, cancel_futures=True)


def _degraded_channel(
    channel: int, adapter: str, physical_input: str, error: str
) -> dict[str, Any]:
    return {
        "logical_channel": channel,
        "logical_name": f"ai{channel:02d}",
        "adapter": adapter,
        "physical_input": physical_input,
        "ok": False,
        "error": error,
    }


class SerializableReading(Protocol):
    def to_dict(self) -> dict[str, Any]: ...


class SerializableHealth(Protocol):
    @property
    def ok(self) -> bool: ...

    def to_dict(self) -> dict[str, Any]: ...


class MCP2221Driver(Protocol):
    def read_adc(self, channel: int, samples: int = 1) -> SerializableReading: ...

    def health(self) -> SerializableHealth: ...


class SingleADCDriver(Protocol):
    def read_adc(self, channel: int = 1, samples: int = 1) -> SerializableReading: ...

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
        stacknet_ads1100: SingleADCDriver | None = None,
        stacknet_channel: int | None = None,
    ) -> None:
        self.mcp2221 = mcp2221 or _default_mcp2221()
        self.dfr1184 = dfr1184 or DFR1184()
        if stacknet_channel not in (None, 2, 3):
            raise ValueError("STACKNET_ADS1100_CHANNEL must be 2 or 3")
        if (stacknet_ads1100 is None) != (stacknet_channel is None):
            raise ValueError(
                "StackNet ADS1100 driver and logical channel must be configured together"
            )
        self.stacknet_ads1100 = stacknet_ads1100
        self.stacknet_channel = stacknet_channel

    @staticmethod
    def _channel(channel: int) -> int:
        if channel not in (1, 2, 3):
            raise ValueError("logical ADC channel must be 1, 2 or 3")
        return channel

    def _read_unlocked(self, channel: int, samples: int) -> dict[str, Any]:
        if channel == 1:
            reading = self.mcp2221.read_adc(1, samples=samples)
        elif channel == self.stacknet_channel and self.stacknet_ads1100 is not None:
            reading = self.stacknet_ads1100.read_adc(1, samples=samples)
        else:
            reading = self.dfr1184.read_adc(channel - 1, samples=samples)
        return self._format_reading(channel, reading)

    @staticmethod
    def _format_reading(
        channel: int,
        reading: SerializableReading,
    ) -> dict[str, Any]:
        adapter = str(reading.to_dict().get("transport", ""))
        if adapter == "stacknet-http+i2c":
            adapter = "stacknet-adc-ads1100"
            physical_input = "ADS1100.AIN"
            nominal_range = [0, 8.192]
        elif channel == 1:
            adapter = "usb-adc-mcp2221"
            physical_input = "MCP2221A.G1"
            nominal_range = [0, 3.3]
        else:
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
        return _run_with_timeout(lambda: self._read_unlocked(channel, samples))

    def read_all_adc(self, samples: int = 1) -> list[dict[str, Any]]:
        if not 1 <= samples <= 10_000:
            raise ValueError("samples must be between 1 and 10000")
        if self.stacknet_ads1100 is not None:
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                futures = [
                    executor.submit(self._read_channel_for_batch, channel, samples)
                    for channel in (1, 2, 3)
                ]
                return [future.result() for future in futures]
        # MCP2221 and DFR1184 are independent transports and may run in
        # parallel. AIN1/AIN2 share one UART, so read them as one serialized
        # operation instead of creating competing per-channel worker pools.
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            mcp_future = executor.submit(self._read_channel_for_batch, 1, samples)
            dfr_future = executor.submit(self._read_dfr_channels_for_batch, samples)
            return [mcp_future.result(), *dfr_future.result()]

    def _read_dfr_channels_for_batch(self, samples: int) -> list[dict[str, Any]]:
        try:
            readings = _run_with_timeout(
                lambda: self.dfr1184.read_all_adc(samples=samples)
            )
            return [
                self._format_reading(channel, reading)
                for channel, reading in zip((2, 3), readings, strict=True)
            ]
        except concurrent.futures.TimeoutError:
            error = (
                "usb-adc-dfr1184 read timed out after "
                f"{OPERATION_TIMEOUT_SECONDS:.1f}s"
            )
        except (RuntimeError, OSError) as caught:
            error = str(caught)
        return [
            _degraded_channel(
                channel,
                "usb-adc-dfr1184",
                f"DFR1184.AIN{channel - 1}",
                error,
            )
            for channel in (2, 3)
        ]

    def _read_channel_for_batch(self, channel: int, samples: int) -> dict[str, Any]:
        if channel == self.stacknet_channel:
            adapter = "stacknet-adc-ads1100"
            physical_input = "ADS1100.AIN"
        elif channel == 1:
            adapter = "usb-adc-mcp2221"
            physical_input = "MCP2221A.G1"
        else:
            adapter = "usb-adc-dfr1184"
            physical_input = f"DFR1184.AIN{channel - 1}"
        try:
            return _run_with_timeout(lambda: self._read_unlocked(channel, samples))
        except concurrent.futures.TimeoutError:
            return _degraded_channel(
                channel,
                adapter,
                physical_input,
                f"{adapter} read timed out after {OPERATION_TIMEOUT_SECONDS:.1f}s",
            )
        except (RuntimeError, OSError) as error:
            return _degraded_channel(channel, adapter, physical_input, str(error))

    def _component_health(
        self,
        name: str,
        operation: Callable[[], SerializableHealth],
    ) -> dict[str, Any]:
        try:
            return _run_with_timeout(operation).to_dict()
        except concurrent.futures.TimeoutError:
            return {
                "ok": False,
                "status": "timeout",
                "message": f"{name} health timed out after {OPERATION_TIMEOUT_SECONDS:.1f}s",
            }

    def health(self) -> dict[str, Any]:
        mcp_health = self._component_health(
            "usb-adc-mcp2221",
            self.mcp2221.health,
        )
        dfr_health = self._component_health(
            "usb-adc-dfr1184",
            self.dfr1184.health,
        )
        components = {
            "usb-adc-mcp2221": mcp_health,
            "usb-adc-dfr1184": dfr_health,
        }
        if self.stacknet_ads1100 is not None:
            components["stacknet-adc-ads1100"] = self._component_health(
                "stacknet-adc-ads1100",
                self.stacknet_ads1100.health,
            )
        ok = all(bool(component.get("ok")) for component in components.values())
        return {
            "ok": ok,
            "status": "connected" if ok else "degraded",
            "components": components,
        }

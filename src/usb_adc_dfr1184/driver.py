"""Validated, backend-independent DFR1184 operations."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass

from .backend import UART_BAUDRATE, DFR1184Backend, SerialDFR1184Backend
from .errors import DFR1184Error, DFR1184ProtocolError
from .models import AdcReading, HealthStatus

CHANNELS = (1, 2)
MAX_PLAUSIBLE_RAW = 1_100_000  # 11 V in units of 0.01 mV; nominal range is 0-10 V.


@dataclass(frozen=True)
class DFR1184Config:
    serial_port: str = "/dev/serial0"
    baudrate: int = UART_BAUDRATE
    timeout: float = 1.0
    command_delay: float = 0.02

    def __post_init__(self) -> None:
        if not self.serial_port:
            raise ValueError("serial_port cannot be empty")
        if self.baudrate != UART_BAUDRATE:
            raise ValueError("DFR1184 UART baudrate must be 9600")
        if self.timeout <= 0:
            raise ValueError("timeout must be positive")
        if self.command_delay < 0:
            raise ValueError("command_delay cannot be negative")


class DFR1184:
    def __init__(
        self,
        config: DFR1184Config | None = None,
        backend: DFR1184Backend | None = None,
    ) -> None:
        self.config = config or DFR1184Config()
        self.backend = backend or SerialDFR1184Backend(
            port=self.config.serial_port,
            baudrate=self.config.baudrate,
            timeout=self.config.timeout,
            command_delay=self.config.command_delay,
        )
        self._lock = threading.RLock()

    @staticmethod
    def _channel(channel: int) -> int:
        if channel not in CHANNELS:
            raise ValueError("DFR1184 channel must be 1 or 2")
        return channel

    def read_adc(self, channel: int, samples: int = 1, sample_delay: float = 0.0) -> AdcReading:
        channel = self._channel(channel)
        if not 1 <= samples <= 10_000:
            raise ValueError("samples must be between 1 and 10000")
        if sample_delay < 0:
            raise ValueError("sample_delay cannot be negative")

        values: list[int] = []
        with self._lock:
            for index in range(samples):
                raw = int(self.backend.read_raw(channel))
                if not 0 <= raw <= MAX_PLAUSIBLE_RAW:
                    raise DFR1184ProtocolError(
                        f"module returned implausible ADC value {raw} (units: 0.01 mV)"
                    )
                values.append(raw)
                if sample_delay and index + 1 < samples:
                    time.sleep(sample_delay)

        raw_average = round(sum(values) / len(values))
        millivolts = raw_average / 100.0
        return AdcReading(
            channel=channel,
            input_name=f"AIN{channel}",
            raw_hundredth_millivolts=raw_average,
            millivolts=round(millivolts, 2),
            volts=round(millivolts / 1000.0, 6),
            samples=samples,
            transport="uart",
            endpoint=self.config.serial_port,
        )

    def read_all_adc(self, samples: int = 1) -> list[AdcReading]:
        with self._lock:
            return [self.read_adc(channel, samples=samples) for channel in CHANNELS]

    def health(self) -> HealthStatus:
        try:
            with self._lock:
                available = self.backend.probe()
        except DFR1184Error as error:
            return HealthStatus(
                False,
                "unavailable",
                str(error),
                "uart",
                self.config.serial_port,
            )
        if not available:
            return HealthStatus(
                False,
                "not_found",
                "DFR1184 did not answer AT on the configured Raspberry Pi UART",
                "uart",
                self.config.serial_port,
            )
        return HealthStatus(
            True,
            "connected",
            "DFR1184 detected on the Raspberry Pi UART",
            "uart",
            self.config.serial_port,
        )

    def capabilities(self) -> dict[str, object]:
        return {
            "product": "DFRobot Gravity DFR1184",
            "adc_chip": "ADS1115",
            "channels": ["AIN1", "AIN2"],
            "measurement_range_volts": [0, 10],
            "effective_bits": 15,
            "nominal_resolution_millivolts": 0.3125,
            "reported_unit": "0.01 mV",
            "transport": "Raspberry Pi 3 UART 8N1",
            "serial_port": self.config.serial_port,
            "baudrate": self.config.baudrate,
            "protocol": {"probe": "AT\\r\\n", "read": "0xbb", "write": "0xcc"},
        }

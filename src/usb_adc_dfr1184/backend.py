"""DFR1184 register protocol over a Raspberry Pi UART."""

from __future__ import annotations

import time
from collections.abc import Callable
from contextlib import suppress
from typing import Any, Protocol

from .errors import DFR1184ProtocolError, DFR1184UnavailableError

CHANNEL_SELECT_REGISTER = 0x20
CHANNEL_DATA_REGISTER = 0x31
UART_READ_REGISTER = 0xBB
UART_WRITE_REGISTER = 0xCC
UART_BAUDRATE = 9600
UART_RESPONSE_OK = b"OK\r\n"


class DFR1184Backend(Protocol):
    def probe(self) -> bool: ...

    def read_raw(self, channel: int) -> int: ...


def _default_serial_factory(port: str, baudrate: int, timeout: float) -> Any:
    try:
        import serial  # type: ignore[import-untyped]
    except ImportError as error:
        raise DFR1184UnavailableError(
            "install the UART dependency with: pip install pyserial"
        ) from error
    try:
        return serial.Serial(port=port, baudrate=baudrate, timeout=timeout)
    except (OSError, serial.SerialException) as error:
        raise DFR1184UnavailableError(f"cannot open DFR1184 UART {port}: {error}") from error


class SerialDFR1184Backend:
    """Implement the official DFR1184 binary register protocol over 9600 8N1."""

    def __init__(
        self,
        port: str = "/dev/serial0",
        baudrate: int = UART_BAUDRATE,
        timeout: float = 1.0,
        command_delay: float = 0.02,
        serial_factory: Callable[[str, int, float], Any] | None = None,
    ) -> None:
        if not port:
            raise ValueError("serial port cannot be empty")
        if baudrate != UART_BAUDRATE:
            raise ValueError("DFR1184 UART baudrate must be 9600")
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        if command_delay < 0:
            raise ValueError("command_delay cannot be negative")
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.command_delay = command_delay
        self.serial_factory = serial_factory or _default_serial_factory

    def _open(self) -> Any:
        try:
            return self.serial_factory(self.port, self.baudrate, self.timeout)
        except DFR1184UnavailableError:
            raise
        except (OSError, RuntimeError, ValueError) as error:
            raise DFR1184UnavailableError(
                f"cannot open DFR1184 UART {self.port}: {error}"
            ) from error

    def _read_exact(self, serial_port: Any, size: int) -> bytes:
        result = bytearray()
        deadline = time.monotonic() + self.timeout
        while len(result) < size and time.monotonic() < deadline:
            chunk = serial_port.read(size - len(result))
            if chunk:
                result.extend(chunk)
            else:
                time.sleep(0.001)
        if len(result) != size:
            raise DFR1184ProtocolError(
                f"UART response truncated: expected {size} bytes, received {len(result)}"
            )
        return bytes(result)

    def probe(self) -> bool:
        serial_port = self._open()
        try:
            serial_port.reset_input_buffer()
            serial_port.write(b"AT\r\n")
            serial_port.flush()
            return self._read_exact(serial_port, len(UART_RESPONSE_OK)) == UART_RESPONSE_OK
        finally:
            with suppress(OSError, RuntimeError):
                serial_port.close()

    def read_raw(self, channel: int) -> int:
        serial_port = self._open()
        try:
            serial_port.reset_input_buffer()
            serial_port.write(bytes((UART_WRITE_REGISTER, CHANNEL_SELECT_REGISTER, 0x01, channel)))
            serial_port.flush()
            if self.command_delay:
                time.sleep(self.command_delay)

            serial_port.reset_input_buffer()
            serial_port.write(bytes((UART_READ_REGISTER, CHANNEL_DATA_REGISTER, 0x03)))
            serial_port.flush()
            if self.command_delay:
                time.sleep(self.command_delay)
            return int.from_bytes(self._read_exact(serial_port, 3), "big", signed=False)
        finally:
            with suppress(OSError, RuntimeError):
                serial_port.close()

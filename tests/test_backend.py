from __future__ import annotations

import pytest

from usb_adc_dfr1184.backend import SerialDFR1184Backend
from usb_adc_dfr1184.errors import DFR1184ProtocolError


class FakeSerial:
    def __init__(self, response: bytes) -> None:
        self.response = bytearray(response)
        self.writes: list[bytes] = []
        self.reset_count = 0
        self.flush_count = 0
        self.closed = False

    def reset_input_buffer(self) -> None:
        self.reset_count += 1

    def write(self, data: bytes) -> int:
        self.writes.append(data)
        return len(data)

    def flush(self) -> None:
        self.flush_count += 1

    def read(self, size: int) -> bytes:
        data = bytes(self.response[:size])
        del self.response[:size]
        return data

    def close(self) -> None:
        self.closed = True


def backend_for(serial_port: FakeSerial, timeout: float = 1.0) -> SerialDFR1184Backend:
    return SerialDFR1184Backend(
        port="/dev/serial0",
        timeout=timeout,
        command_delay=0,
        serial_factory=lambda port, baudrate, serial_timeout: serial_port,
    )


def test_probe_uses_official_at_handshake() -> None:
    serial_port = FakeSerial(b"OK\r\n")

    backend = backend_for(serial_port)
    assert backend.probe() is True
    assert serial_port.writes == [b"AT\r\n"]
    assert serial_port.closed is False
    backend.close()
    assert serial_port.closed is True


def test_register_protocol_and_big_endian_result() -> None:
    serial_port = FakeSerial((123_456).to_bytes(3, "big"))

    backend = backend_for(serial_port)
    assert backend.read_raw(2) == 123_456
    assert serial_port.writes == [b"\xcc\x20\x01\x02", b"\xbb\x31\x03"]
    assert serial_port.reset_count == 2
    assert serial_port.closed is False
    backend.close()
    assert serial_port.closed is True


def test_successive_reads_reuse_one_uart_connection() -> None:
    serial_port = FakeSerial(
        (123_456).to_bytes(3, "big") + (234_567).to_bytes(3, "big")
    )
    opens = 0

    def serial_factory(port: str, baudrate: int, serial_timeout: float) -> FakeSerial:
        nonlocal opens
        opens += 1
        return serial_port

    backend = SerialDFR1184Backend(
        port="/dev/serial0",
        timeout=1.0,
        command_delay=0,
        serial_factory=serial_factory,
    )

    assert backend.read_raw(1) == 123_456
    assert backend.read_raw(2) == 234_567
    assert opens == 1
    assert serial_port.closed is False


def test_truncated_uart_response_is_rejected() -> None:
    serial_port = FakeSerial(b"\x01")
    backend = backend_for(serial_port, timeout=0.001)

    with pytest.raises(DFR1184ProtocolError, match="truncated"):
        backend.read_raw(1)
    assert serial_port.closed is True

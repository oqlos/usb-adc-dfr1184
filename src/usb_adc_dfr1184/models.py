"""Stable data contracts shared by the library, CLI and HTTP API."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class AdcReading:
    channel: int
    input_name: str
    raw_hundredth_millivolts: int
    millivolts: float
    volts: float
    samples: int
    transport: str
    endpoint: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class HealthStatus:
    ok: bool
    status: str
    message: str
    transport: str
    endpoint: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

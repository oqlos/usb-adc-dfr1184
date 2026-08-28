"""Read the M5Stack ADS1100 Unit from the StackNet firmware HTTP API."""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class StackNetADS1100Config:
    base_url: str
    timeout: float = 0.8

    def __post_init__(self) -> None:
        parsed = urlsplit(self.base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("STACKNET_ADS1100_URL must be an absolute HTTP(S) URL")
        if self.timeout <= 0:
            raise ValueError("STACKNET_ADS1100_TIMEOUT must be positive")

    @property
    def endpoint(self) -> str:
        return f"{self.base_url.rstrip('/')}/api/v1/adc"


@dataclass(frozen=True)
class StackNetADS1100Reading:
    channel: int
    input_name: str
    raw: int
    adc_voltage: float
    volts: float
    samples: int
    saturated: bool
    transport: str
    endpoint: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class StackNetADS1100Health:
    ok: bool
    status: str
    message: str
    transport: str
    endpoint: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class StackNetADS1100:
    """Small stdlib-only client for the read-only StackNet ADC endpoint."""

    def __init__(self, config: StackNetADS1100Config) -> None:
        self.config = config

    def _payload(self) -> dict[str, Any]:
        request = Request(
            self.config.endpoint,
            headers={"Accept": "application/json"},
            method="GET",
        )
        try:
            with urlopen(request, timeout=self.config.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as error:
            raise RuntimeError(f"StackNet ADS1100 request failed: {error}") from error
        if not isinstance(payload, dict):
            raise RuntimeError("StackNet ADS1100 returned a non-object response")
        if payload.get("success") is False:
            raise RuntimeError(str(payload.get("error") or "StackNet ADS1100 read failed"))
        data = payload.get("data", payload)
        if not isinstance(data, dict):
            raise RuntimeError("StackNet ADS1100 response has no data object")
        return data

    def read_adc(self, channel: int = 1, samples: int = 1) -> StackNetADS1100Reading:
        if channel != 1:
            raise ValueError("ADS1100 has exactly one physical input")
        if not 1 <= samples <= 10_000:
            raise ValueError("samples must be between 1 and 10000")
        values = [self._payload() for _ in range(samples)]
        if any(item.get("present") is not True for item in values):
            raise RuntimeError("StackNet ADS1100 is not present")
        if any(item.get("saturated") is True or item.get("ok") is False for item in values):
            raise RuntimeError("StackNet ADS1100 input is saturated or unhealthy")
        try:
            volts = [float(item["volts"]) for item in values]
            adc_volts = [float(item["adc_voltage"]) for item in values]
            raw = [int(item["raw"]) for item in values]
        except (KeyError, TypeError, ValueError) as error:
            raise RuntimeError("StackNet ADS1100 response is missing numeric fields") from error
        if not all(math.isfinite(value) and 0 <= value <= 8.25 for value in volts):
            raise RuntimeError("StackNet ADS1100 returned an implausible connector voltage")
        return StackNetADS1100Reading(
            channel=1,
            input_name="AIN",
            raw=round(sum(raw) / len(raw)),
            adc_voltage=round(sum(adc_volts) / len(adc_volts), 6),
            volts=round(sum(volts) / len(volts), 6),
            samples=samples,
            saturated=False,
            transport="stacknet-http+i2c",
            endpoint=self.config.endpoint,
        )

    def health(self) -> StackNetADS1100Health:
        try:
            reading = self.read_adc()
        except (RuntimeError, OSError) as error:
            return StackNetADS1100Health(
                False,
                "unavailable",
                str(error),
                "stacknet-http+i2c",
                self.config.endpoint,
            )
        return StackNetADS1100Health(
            True,
            "connected",
            f"ADS1100 detected at 0x48 ({reading.volts:.6f} V)",
            "stacknet-http+i2c",
            self.config.endpoint,
        )

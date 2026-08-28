from __future__ import annotations

import io
import json
from typing import Any

import pytest

from usb_adc_dfr1184 import stacknet_ads1100 as driver_module
from usb_adc_dfr1184.stacknet_ads1100 import StackNetADS1100, StackNetADS1100Config


class FakeResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.body = io.BytesIO(json.dumps(payload).encode("utf-8"))

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return self.body.read()


def test_reads_oql_api_envelope_and_preserves_connector_voltage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = {
        "success": True,
        "data": {
            "present": True,
            "ok": True,
            "raw": 4000,
            "adc_voltage": 0.25,
            "volts": 1.0,
            "saturated": False,
        },
    }
    monkeypatch.setattr(
        driver_module,
        "urlopen",
        lambda *_args, **_kwargs: FakeResponse(payload),
    )
    driver = StackNetADS1100(StackNetADS1100Config("http://stacknet.local:8080"))

    reading = driver.read_adc()

    assert reading.volts == 1.0
    assert reading.adc_voltage == 0.25
    assert reading.raw == 4000
    assert reading.endpoint == "http://stacknet.local:8080/api/v1/adc"
    assert driver.health().ok is True


def test_rejects_saturated_reading(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {
        "present": True,
        "ok": False,
        "raw": 32767,
        "adc_voltage": 2.048,
        "volts": 8.192,
        "saturated": True,
    }
    monkeypatch.setattr(
        driver_module,
        "urlopen",
        lambda *_args, **_kwargs: FakeResponse(payload),
    )
    driver = StackNetADS1100(StackNetADS1100Config("http://stacknet.local"))

    with pytest.raises(RuntimeError, match="saturated"):
        driver.read_adc()
    assert driver.health().ok is False


def test_clamps_small_negative_zero_offset(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {
        "present": True,
        "ok": True,
        "raw": -18,
        "adc_voltage": -0.001125,
        "volts": -0.0045,
        "saturated": False,
    }
    monkeypatch.setattr(
        driver_module,
        "urlopen",
        lambda *_args, **_kwargs: FakeResponse(payload),
    )
    driver = StackNetADS1100(StackNetADS1100Config("http://stacknet.local:8080"))

    reading = driver.read_adc()

    assert reading.volts == 0.0
    assert reading.raw == -18
    assert driver.health().ok is True


def test_requires_absolute_http_url() -> None:
    with pytest.raises(ValueError, match="absolute"):
        StackNetADS1100Config("stacknet.local:8080")

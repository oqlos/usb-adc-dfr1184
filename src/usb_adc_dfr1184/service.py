"""Read-only DFR1184 HTTP adapter for OqlOS."""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any, TypeVar

from .driver import DFR1184, DFR1184Config
from .errors import DFR1184Error

T = TypeVar("T")


def create_app(driver: DFR1184 | None = None) -> Any:
    try:
        from fastapi import FastAPI, HTTPException, Query
    except ImportError as error:
        raise RuntimeError("install the API dependencies with: pip install '.[api]'") from error

    device = driver or DFR1184(
        DFR1184Config(
            serial_port=os.getenv("DFR1184_SERIAL_PORT", "/dev/serial0"),
            baudrate=int(os.getenv("DFR1184_BAUDRATE", "9600")),
            timeout=float(os.getenv("DFR1184_UART_TIMEOUT", "1.0")),
        )
    )
    app = FastAPI(
        title="OqlOS DFR1184 ADC Adapter",
        version="0.1.0",
        description="Read-only dual-channel 0-10 V ADC API through Raspberry Pi UART",
    )

    def execute(operation: Callable[[], T]) -> T:
        try:
            return operation()
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        except DFR1184Error as error:
            raise HTTPException(status_code=503, detail=str(error)) from error

    @app.get("/health")
    def health() -> dict[str, Any]:
        return device.health().to_dict()

    @app.get("/api/v1/device")
    def device_info() -> dict[str, object]:
        return device.capabilities()

    @app.get("/api/v1/adc")
    def adc_all(samples: int = Query(1, ge=1, le=10_000)) -> list[dict[str, Any]]:
        return execute(lambda: [reading.to_dict() for reading in device.read_all_adc(samples)])

    @app.get("/api/v1/adc/{channel}")
    def adc_channel(
        channel: int,
        samples: int = Query(1, ge=1, le=10_000),
        sample_delay: float = Query(0.0, ge=0.0, le=10.0),
    ) -> dict[str, Any]:
        return execute(lambda: device.read_adc(channel, samples, sample_delay).to_dict())

    return app


def main() -> None:
    try:
        import uvicorn
    except ImportError as error:
        raise RuntimeError("install the API dependencies with: pip install '.[api]'") from error
    uvicorn.run(
        create_app(),
        host=os.getenv("DFR1184_API_HOST", "127.0.0.1"),
        port=int(os.getenv("DFR1184_API_PORT", "8213")),
    )

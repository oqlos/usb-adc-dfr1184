"""Unified read-only API for logical channels ai01-ai03."""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any, TypeVar

from .driver import DFR1184, DFR1184Config
from .errors import DFR1184Error
from .stack import ADCStack

T = TypeVar("T")


def create_app(stack: ADCStack | None = None) -> Any:
    try:
        from fastapi import FastAPI, HTTPException, Query
    except ImportError as error:
        raise RuntimeError("install the API dependencies with: pip install '.[api]'") from error

    adc_stack = stack or ADCStack(
        dfr1184=DFR1184(
            DFR1184Config(
                serial_port=os.getenv("DFR1184_SERIAL_PORT", "/dev/serial0"),
                baudrate=int(os.getenv("DFR1184_BAUDRATE", "9600")),
                timeout=float(os.getenv("DFR1184_UART_TIMEOUT", "1.0")),
            )
        )
    )
    app = FastAPI(
        title="OqlOS USB ADC Stack",
        version="0.2.0",
        description="MCP2221A USB G1 and Raspberry Pi UART DFR1184 AIN1/AIN2 API",
    )

    def execute(operation: Callable[[], T]) -> T:
        try:
            return operation()
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        except (DFR1184Error, RuntimeError) as error:
            raise HTTPException(status_code=503, detail=str(error)) from error

    @app.get("/health")
    def health() -> dict[str, Any]:
        return adc_stack.health()

    @app.get("/api/v1/adc")
    def adc_all(samples: int = Query(1, ge=1, le=10_000)) -> list[dict[str, Any]]:
        return execute(lambda: adc_stack.read_all_adc(samples))

    @app.get("/api/v1/adc/{channel}")
    def adc_channel(
        channel: int,
        samples: int = Query(1, ge=1, le=10_000),
    ) -> dict[str, Any]:
        return execute(lambda: adc_stack.read_adc(channel, samples))

    return app


def main() -> None:
    try:
        import uvicorn
    except ImportError as error:
        raise RuntimeError("install the API dependencies with: pip install '.[api]'") from error
    uvicorn.run(
        create_app(),
        host=os.getenv("USB_ADC_STACK_API_HOST", "127.0.0.1"),
        port=int(os.getenv("USB_ADC_STACK_API_PORT", "8214")),
    )

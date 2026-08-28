"""Unified read-only API for logical channels ai01-ai03."""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any, TypeVar

from .driver import DFR1184, DFR1184Config
from .errors import DFR1184Error
from .stack import ADCStack
from .stacknet_ads1100 import StackNetADS1100, StackNetADS1100Config

T = TypeVar("T")


def dfr1184_config_from_environment() -> DFR1184Config:
    """Build the UART profile once, keeping hardware timing deploy-configurable."""
    return DFR1184Config(
        serial_port=os.getenv("DFR1184_SERIAL_PORT", "/dev/serial0"),
        baudrate=int(os.getenv("DFR1184_BAUDRATE", "9600")),
        timeout=float(os.getenv("DFR1184_UART_TIMEOUT", "1.0")),
        command_delay=float(os.getenv("DFR1184_COMMAND_DELAY", "0.015")),
    )


def create_app(stack: ADCStack | None = None) -> Any:
    try:
        from fastapi import FastAPI, HTTPException, Query
    except ImportError as error:
        raise RuntimeError("install the API dependencies with: pip install '.[api]'") from error

    if stack is None:
        stacknet_url = os.getenv("STACKNET_ADS1100_URL", "").strip()
        stacknet = (
            StackNetADS1100(
                StackNetADS1100Config(
                    base_url=stacknet_url,
                    timeout=float(os.getenv("STACKNET_ADS1100_TIMEOUT", "0.8")),
                )
            )
            if stacknet_url
            else None
        )
        adc_stack = ADCStack(
            dfr1184=DFR1184(dfr1184_config_from_environment()),
            stacknet_ads1100=stacknet,
            stacknet_channel=int(os.getenv("STACKNET_ADS1100_CHANNEL", "2")) if stacknet else None,
        )
    else:
        adc_stack = stack
    app = FastAPI(
        title="OqlOS USB ADC Stack",
        version="0.3.0",
        description="MCP2221A, StackNet ADS1100 and Raspberry Pi UART DFR1184 ADC API",
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

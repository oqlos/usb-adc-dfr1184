"""JSON command-line interface for DFR1184 diagnostics and measurements."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Sequence
from typing import Any

from .driver import DFR1184, DFR1184Config
from .errors import DFR1184Error

DriverFactory = Callable[[DFR1184Config], DFR1184]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="usb-adc-dfr1184",
        description="DFR1184 0-10 V ADC through the Raspberry Pi 3 UART",
    )
    parser.add_argument("--serial-port", default="/dev/serial0")
    parser.add_argument("--baudrate", type=int, default=9600)
    parser.add_argument("--timeout", type=float, default=1.0)
    parser.add_argument("--command-delay", type=float, default=0.02)
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("health", help="send AT and verify the DFR1184 UART response")
    commands.add_parser("info", help="show capabilities and current health")

    adc = commands.add_parser("adc", help="read AIN1 or AIN2")
    adc.add_argument("channel", type=int, choices=(1, 2))
    adc.add_argument("--samples", type=int, default=1)
    adc.add_argument("--sample-delay", type=float, default=0.0)

    adc_all = commands.add_parser("adc-all", help="read both 0-10 V inputs")
    adc_all.add_argument("--samples", type=int, default=1)

    return parser


def _factory(config: DFR1184Config) -> DFR1184:
    return DFR1184(config=config)


def _write(payload: Any, *, stream: Any = sys.stdout) -> None:
    json.dump(payload, stream, ensure_ascii=False, indent=2, sort_keys=True)
    stream.write("\n")


def run(
    argv: Sequence[str] | None = None,
    *,
    driver_factory: DriverFactory = _factory,
    stdout: Any = sys.stdout,
    stderr: Any = sys.stderr,
) -> int:
    args = build_parser().parse_args(argv)
    try:
        config = DFR1184Config(
            args.serial_port,
            args.baudrate,
            args.timeout,
            args.command_delay,
        )
        driver = driver_factory(config)
        if args.command == "health":
            health = driver.health()
            _write(health.to_dict(), stream=stdout)
            return 0 if health.ok else 1
        if args.command == "info":
            _write(
                {
                    "capabilities": driver.capabilities(),
                    "health": driver.health().to_dict(),
                },
                stream=stdout,
            )
            return 0
        if args.command == "adc":
            reading = driver.read_adc(args.channel, args.samples, args.sample_delay)
            _write(reading.to_dict(), stream=stdout)
            return 0
        if args.command == "adc-all":
            readings = [reading.to_dict() for reading in driver.read_all_adc(args.samples)]
            _write(readings, stream=stdout)
            return 0
    except (DFR1184Error, ValueError) as error:
        _write({"ok": False, "error": str(error)}, stream=stderr)
        return 2
    return 2


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()

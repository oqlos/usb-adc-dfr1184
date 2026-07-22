"""DFR1184 0-10 V ADC support through Raspberry Pi UART for OqlOS."""

from .driver import DFR1184, DFR1184Config
from .errors import DFR1184Error, DFR1184ProtocolError, DFR1184UnavailableError
from .models import AdcReading, HealthStatus

__all__ = [
    "AdcReading",
    "DFR1184",
    "DFR1184Config",
    "DFR1184Error",
    "DFR1184ProtocolError",
    "DFR1184UnavailableError",
    "HealthStatus",
]

__version__ = "0.1.0"

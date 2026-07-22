"""Public exceptions raised by the DFR1184 adapter."""


class DFR1184Error(RuntimeError):
    """Base error for protocol, configuration and I/O failures."""


class DFR1184UnavailableError(DFR1184Error):
    """The Raspberry Pi UART or DFR1184 module is unavailable."""


class DFR1184ProtocolError(DFR1184Error):
    """The module returned malformed or physically implausible data."""

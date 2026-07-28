# Raspberry Pi 3

[Powrót do inwentarza sprzętu](../README.md)

Raspberry Pi 3 uruchamia usługę i komunikuje się z DFR1184 przez sprzętowy UART
`/dev/serial0`.

## Materiały

- [pinout GPIO](images/gpio-pinout.png);
- [połączenie pinów UART](images/uart-pins.png);
- [pełna instrukcja DFR1184 i UART](../dfr1184/README.md).

## Używane piny

| Pin fizyczny | BCM | Funkcja | Połączenie DFR1184 |
|---:|---:|---|---|
| 1 | — | 3,3 V | VCC |
| 6 | — | GND | GND |
| 8 | 14 | TXD | C/R / RXD |
| 10 | 15 | RXD | D/T / TXD |

Wejście GPIO15/RXD Raspberry Pi nie toleruje logiki 5 V. W tym projekcie DFR1184
jest zasilany z 3,3 V, aby utrzymać bezpieczny poziom UART.

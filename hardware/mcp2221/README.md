# Adafruit 4471 / MCP2221A

[Powrót do inwentarza sprzętu](../README.md)

MCP2221A udostępnia wejścia ADC na pinach G1, G2 i G3. W tym systemie używane jest
G1 jako `ai01`. Bieżąca konfiguracja adaptera ustawia napięcie odniesienia 3,3 V,
dlatego sygnału dochodzącego do 5 V nie wolno podłączać bezpośrednio.

## Dokumenty

- [MCP2221A Data Sheet DS20005565E, PDF](datasheets/MCP2221A-datasheet-DS20005565E.pdf)
- [dokumentacja adaptera usb-adc-mcp2221](https://github.com/oqlos/usb-adc-mcp2221/blob/main/docs/HARDWARE.md)
- [Microchip — MCP2221A](https://www.microchip.com/en-us/product/MCP2221A)
- [Adafruit — MCP2221](https://www.adafruit.com/product/4471)

## Bieżąca konfiguracja

| Parametr | Wartość |
|---|---|
| płytka | Adafruit 4471 |
| wejście | G1 / ADC1 |
| rozdzielczość sprzętowa | 10 bitów |
| odniesienie adaptera | 3,3 V |
| izolacja | brak |
| zasób | `ai01`, w Maskservice `cisnienie_nc` |

Płytka Adafruit umożliwia sprzętowe przełączenie logiki, lecz wymaga to świadomej
modyfikacji zwory. Zmiana parametru programowego `reference_voltage` nie zmienia
fizycznej tolerancji wejścia.

## Sensor z wyjściem do 5 V

Do czasu identyfikacji sensora użyj wejścia DFR1184 0–10 V albo zaprojektowanego
dzielnika i zabezpieczenia. Nie dobieraj dzielnika bez znajomości maksymalnego
napięcia sensora, impedancji wyjścia i wymaganej dokładności.

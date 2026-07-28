# Inwentarz sprzętu

Ten katalog jest jednym miejscem dla informacji sprzętowych używanych przez stos
ADC. Umieszczamy tu karty katalogowe, schematy, pinouty, zdjęcia, informacje o
zasilaniu, mapowanie kanałów oraz status identyfikacji sensorów.

## Elementy systemu

| Element | Rola | Interfejs / zakres | Kanały | Dokumentacja |
|---|---|---|---|---|
| Raspberry Pi 3 | host usługi | UART `/dev/serial0`, 9600 8N1 | — | [raspberry-pi-3/](raspberry-pi-3/README.md) |
| DFRobot DFR1184 | dwukanałowy ADC | UART; wejścia 0–10 V | `ai02`, `ai03` | [dfr1184/](dfr1184/README.md) |
| Adafruit 4471 / MCP2221A | USB ADC | USB HID; G1 pracuje obecnie z odniesieniem 3,3 V | `ai01` | [mcp2221/](mcp2221/README.md) |
| Sensory ciśnienia | źródła sygnału analogowego | dane częściowo nieustalone | `ai01–ai03` | [pressure-sensors/](pressure-sensors/README.md) |

## Mapowanie wejść

| Kanał logiczny | Wejście fizyczne | Zakres toru ADC | Zastosowanie w Maskservice |
|---|---|---:|---|
| `ai01` | `MCP2221A.G1` | 0–3,3 V w bieżącej konfiguracji | `cisnienie_nc` — niskie ciśnienie |
| `ai02` | `DFR1184.AIN1` | 0–10 V | `cisnienie_sc` — średnie ciśnienie |
| `ai03` | `DFR1184.AIN2` | 0–10 V | `cisnienie_wc` — wysokie ciśnienie |

Mapowanie elektryczne stosu definiuje
[`config/oqlos-adc-stack.yaml`](../config/oqlos-adc-stack.yaml). Nazwy domenowe i
przeliczenia ciśnienia są obecnie deklarowane w repozytorium Maskservice w
`c2004/extern/scenarios/layers/hardware/boardnet.oql`.

## Zasady utrzymania

1. Każdy używany element otrzymuje własny podkatalog.
2. Karta katalogowa producenta trafia do `datasheets/`.
3. Obrazy mają opisowe nazwy i trafiają do `images/`.
4. `README.md` elementu zawiera pinout, zasilanie, zakresy i źródła.
5. Nieznane dane oznaczamy jako `TBD`; nie zastępujemy ich przypuszczeniami.
6. Po wymianie sprzętu aktualizujemy równocześnie ten inwentarz, konfigurację
   kanałów oraz mapowanie Maskservice.

## Krytyczne zasady bezpieczeństwa

- Nie podłączaj sygnału większego od zakresu wejścia.
- Nie podłączaj 4–20 mA bez odpowiedniego kondycjonera.
- Przed podłączeniem sprawdź model sensora, zasilanie, typ wyjścia i pinout.
- DFR1184 i MCP2221A nie zapewniają separacji galwanicznej.
- Przełączniki DFR1184 zmieniaj wyłącznie przy wyłączonym zasilaniu.

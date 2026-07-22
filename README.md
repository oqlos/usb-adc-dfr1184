# usb-adc-dfr1184

Sterownik i lokalny adapter HTTP dla dwukanałowego modułu **DFRobot DFR1184
Gravity 0–10 V**, podłączonego bezpośrednio do **UART Raspberry Pi 3**.

Docelowy stos wejść OqlOS używa dwóch niezależnych transportów:

| Wejście OqlOS | Źródło | Transport | Zakres nominalny |
|---|---|---|---|
| `ai01` | MCP2221A G1 | USB HID | 0–3,3 V |
| `ai02` | DFR1184 AIN1 | RPi3 UART | 0–10 V |
| `ai03` | DFR1184 AIN2 | RPi3 UART | 0–10 V |

Projekt zapewnia:

- oficjalny protokół UART DFR1184: test `AT`, zapis rejestru przez `0xCC` i odczyt
  przez `0xBB`;
- komunikację `/dev/serial0`, 9600 8N1;
- uśrednianie pomiarów i wyniki w jednostkach surowych, mV oraz V;
- JSON CLI, samodzielne API DFR1184 oraz wspólne API `ai01–ai03`;
- testowalny backend bez wymagania fizycznego sprzętu w testach jednostkowych.

## Instalacja na Raspberry Pi 3

```bash
cd ~/github/oqlos/usb-adc-dfr1184
python3 -m venv .venv
.venv/bin/pip install -e '.[api,dev]'
```

Użytkownik usługi musi mieć dostęp do UART, zwykle przez grupę `dialout`. Konsolę
systemową na porcie szeregowym należy wyłączyć, a UART włączyć w `raspi-config`.
Dokładna procedura jest w [docs/HARDWARE.md](docs/HARDWARE.md).

## Podłączenie

Przełącz DFR1184 do trybu **UART przy wyłączonym zasilaniu**.

| Raspberry Pi 3 | Pin | DFR1184 |
|---|---:|---|
| 3V3 | 1 | VCC |
| GND | 6 | GND |
| GPIO14 / TXD | 8 | C/R / RXD |
| GPIO15 / RXD | 10 | D/T / TXD |

TX i RX są skrzyżowane. Zasilanie 3,3 V utrzymuje poziomy UART bezpieczne dla GPIO
Raspberry Pi; wejścia Pi nie tolerują logiki 5 V.

## CLI

```bash
usb-adc-dfr1184 health
usb-adc-dfr1184 info
usb-adc-dfr1184 adc 1 --samples 16 --sample-delay 0.01
usb-adc-dfr1184 adc-all --samples 8
usb-adc-dfr1184 --serial-port /dev/serial0 adc 2
```

## Samodzielne API DFR1184

```bash
usb-adc-dfr1184-api
curl http://127.0.0.1:8213/health
curl 'http://127.0.0.1:8213/api/v1/adc/1?samples=16'
```

Zmienne środowiskowe:

- `DFR1184_SERIAL_PORT` — domyślnie `/dev/serial0`;
- `DFR1184_BAUDRATE` — wymagane `9600`;
- `DFR1184_UART_TIMEOUT` — domyślnie `1.0` s;
- `DFR1184_API_HOST` i `DFR1184_API_PORT` — domyślnie `127.0.0.1:8213`.

## Wspólne API ai01–ai03

W produkcji oba lokalne pakiety mogą działać w jednej usłudze:

```bash
.venv/bin/pip install -e ../usb-adc-mcp2221
usb-adc-stack-api
curl http://127.0.0.1:8214/api/v1/adc
```

Wspólna usługa mapuje `ai01` na USB MCP2221A oraz `ai02–ai03` na UART DFR1184.
Szczegóły zawiera [docs/OQLOS_INTEGRATION.md](docs/OQLOS_INTEGRATION.md).
Nie uruchamiaj jednocześnie wspólnej i samodzielnych usług na tych samych fizycznych
urządzeniach.

Gotowa jednostka użytkownika systemd dla BoardNet znajduje się w
`deploy/systemd/usb-adc-stack.service`.

## Ograniczenia

- `0,01 mV` jest jednostką raportowania protokołu, nie fizyczną rozdzielczością.
  Producent podaje około `0,3125 mV` dla 15 bitów.
- DFR1184 mierzy napięcie stałe 0–10 V i nie jest wejściem 4–20 mA.
- Moduł nie zapewnia separacji galwanicznej od Raspberry Pi.
- Nie wolno podawać logiki 5 V na wejście UART Raspberry Pi.

## Źródła

- [DFRobot Wiki — DFR1184](https://wiki.dfrobot.com/dfr1184/)
- [Oficjalna biblioteka i protokół DFRobot](https://github.com/DFRobot/DFRobot_ADS1115_0_10V)
- [Kamami — DFR1184](https://kamami.pl/przetworniki-ac-i-ca/1201305-modul-adc-dfrobot-dfr1184-gravity-010-v-15-bit-dwukanalowy-do-arduino-raspberry-pi-esp32-5902186330115.html)

## Testy

```bash
.venv/bin/pytest
.venv/bin/ruff check .
.venv/bin/mypy src/usb_adc_dfr1184
```

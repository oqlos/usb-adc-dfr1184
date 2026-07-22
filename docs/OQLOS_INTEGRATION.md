# Integracja stosu ADC z OqlOS

## Topologia

```text
MCP2221A.G1 0–3,3 V ─ USB HID ─┐
                                ├─ usb-adc-stack-api :8214 ── OqlOS
DFR1184 AIN1/AIN2 0–10 V ─ UART ┘
                         Raspberry Pi 3 /dev/serial0, 9600 8N1
```

Urządzenia używają niezależnych transportów. MCP2221A nie pośredniczy w komunikacji
DFR1184. Wspólna usługa zapewnia tylko jeden spójny kontrakt logicznych kanałów.

## Mapowanie kanałów

Pełny profil znajduje się w `config/oqlos-adc-stack.yaml`.

| Kanał | Adapter | Endpoint | Wejście i transport |
|---|---|---|---|
| `ai01` | usb-adc-mcp2221 | `:8214/api/v1/adc/1` | MCP2221A G1 / USB |
| `ai02` | usb-adc-dfr1184 | `:8214/api/v1/adc/2` | DFR1184 AIN1 / UART |
| `ai03` | usb-adc-dfr1184 | `:8214/api/v1/adc/3` | DFR1184 AIN2 / UART |

Konsumenci powinni używać pola `reading.volts`. Pola `raw_10bit` z MCP2221A i
`raw_hundredth_millivolts` z DFR1184 mają różne znaczenie.

## Kontrakty HTTP

Wspólna usługa `:8214`:

| Metoda i ścieżka | Znaczenie |
|---|---|
| `GET /health` | stan obu adapterów |
| `GET /api/v1/adc` | `ai01–ai03` |
| `GET /api/v1/adc/{1..3}` | pojedynczy kanał logiczny |

Samodzielna diagnostyka DFR1184 `:8213`:

| Metoda i ścieżka | Znaczenie |
|---|---|
| `GET /health` | odpowiedź `OK` na polecenie `AT` |
| `GET /api/v1/device` | parametry UART i ADC |
| `GET /api/v1/adc` | AIN1 i AIN2 |
| `GET /api/v1/adc/{1..2}` | pojedyncze wejście DFR1184 |

## Instalacja i start wspólnej usługi

```bash
pip install -e ../usb-adc-mcp2221
pip install -e '.[api]'
```

```ini
[Unit]
Description=OqlOS MCP2221A USB and DFR1184 UART ADC stack
After=network.target

[Service]
Type=simple
User=oqlos
Group=dialout
WorkingDirectory=/home/oqlos/usb-adc-dfr1184
Environment=DFR1184_SERIAL_PORT=/dev/serial0
Environment=DFR1184_BAUDRATE=9600
ExecStart=/home/oqlos/usb-adc-dfr1184/.venv/bin/usb-adc-stack-api
Restart=on-failure
RestartSec=2

[Install]
WantedBy=multi-user.target
```

Konto musi mieć jednocześnie uprawnienia do MCP2221A HID (reguła udev) i UART
(`dialout`). API domyślnie nasłuchuje na `127.0.0.1:8214`.

## Semantyka błędów

- `422` — nieprawidłowy kanał lub parametr;
- `503` — urządzenie USB, UART albo DFR1184 są niedostępne;
- `health.ok: false` — co najmniej jeden składnik nie przeszedł diagnostyki.

Odczyt DFR1184 przekraczający 11 V jest traktowany jako uszkodzona odpowiedź.
Nominalna granica sprzętu pozostaje równa 10 V.

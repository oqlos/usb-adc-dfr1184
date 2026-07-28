# Sensory ciśnienia

[Powrót do inwentarza sprzętu](../README.md)

## Stan dokumentacji

W repozytoriach `usb-adc-dfr1184` i `maskservice` nie znaleziono karty katalogowej,
modelu, producenta ani pinoutu fizycznych sensorów ciśnienia. Istnieją wyłącznie
mapowania kanałów i programowe przeliczenia. Nie są one wystarczające do ustalenia
zasilania lub kolejności przewodów.

| Pomiar | Kanał | Tor wejściowy | Przeliczenie zapisane w Maskservice | Brakujące dane |
|---|---|---|---|---|
| niskie ciśnienie `cisnienie_nc` | `ai01` | `MCP2221A.G1`, obecnie 0–3,3 V | `(V - 2,0) × 34 mbar` | producent, model, zakres, zasilanie, wyjście, pinout |
| średnie ciśnienie `cisnienie_sc` | `ai02` | `DFR1184.AIN1`, 0–10 V | `V × 2,5 bar` | producent, model, zakres, zasilanie, wyjście, pinout |
| wysokie ciśnienie `cisnienie_wc` | `ai03` | `DFR1184.AIN2`, 0–10 V | `V × 40 bar` | producent, model, zakres, zasilanie, wyjście, pinout |

Wzory odzwierciedlają bieżącą konfigurację oprogramowania. Nie potwierdzają
rzeczywistej charakterystyki sensorów i wymagają weryfikacji napięciem lub
ciśnieniem wzorcowym.

## Dane wymagane przed podłączeniem sensora

- producent i pełny numer modelu;
- zakres ciśnienia oraz rodzaj pomiaru: względny, absolutny albo różnicowy;
- napięcie zasilania;
- typ wyjścia: np. 0–5 V, 0,5–4,5 V, 0–10 V albo 4–20 mA;
- opis pinów lub przewodów;
- karta katalogowa PDF;
- punkt zerowy i współczynnik przeliczenia;
- dopuszczalne przeciążenie ciśnieniowe.

## Tymczasowa zasada podłączenia

Sensora z potwierdzonym pojedynczym wyjściem napięciowym do 5 V nie podłączaj
bezpośrednio do pracującego na 3,3 V wejścia MCP2221A.G1. Można użyć DFR1184:

```text
sensor OUT / SIGNAL ─────────────── DFR1184 AIN1
sensor GND / 0 V    ─────────────── DFR1184 GND wejściowe
sensor VCC / +Vs    ─────────────── zasilacz zgodny z kartą sensora
```

Jest to jedynie topologia dla sensora napięciowego. Nie określa pinów ani kolorów
przewodów. Sensor 4–20 mA wymaga kondycjonera, a sensor zasilany 12/24 V wymaga
odpowiedniego zasilacza zewnętrznego.

## Do uzupełnienia po identyfikacji

Po odczytaniu oznaczenia z obudowy należy dodać tutaj:

1. PDF producenta w podkatalogu `datasheets/`;
2. zdjęcia etykiety i złącza w `images/`;
3. zweryfikowany schemat przewodów;
4. poprawny wzór konwersji;
5. wynik testu dla zera i co najmniej jednego znanego ciśnienia.

# DFR1184 — UART Raspberry Pi 3

[Powrót do inwentarza sprzętu](../README.md)

## Dokumenty i materiały

- [oficjalny schemat DFR1184, PDF](datasheets/DFR1184-schematic-v1.0.pdf);
- [schemat elektryczny, PNG](images/schematic.png);
- [wymiary i rozmieszczenie złączy](images/dimensions.png);
- [przykład połączenia UART przez konwerter USB](images/uart-usb-example.png);
- [snapshot oficjalnej biblioteki DFRobot](library/DFRobot_ADS1115_0_10V/README.md).

## Parametry

DFRobot DFR1184 wykorzystuje ADS1115 i udostępnia dwa wejścia napięciowe 0–10 V.
Producent deklaruje efektywną rozdzielczość 15 bitów, krok około 0,3125 mV oraz błąd
mniejszy niż 2 mV. Moduł może być zasilany napięciem 3,3–5 V i pracować przez I²C
albo UART.

Docelowy wariant OqlOS używa bezpośredniego UART Raspberry Pi 3: `/dev/serial0`,
9600 bit/s, 8 bitów danych, brak parzystości, jeden bit stopu (8N1).

## Okablowanie Raspberry Pi 3

Ustaw przełącznik DFR1184 w położeniu **UART** przy wyłączonym zasilaniu.

| Raspberry Pi 3 | Pin fizyczny | DFR1184 | Funkcja |
|---|---:|---|---|
| 3V3 | 1 | VCC | zasilanie i logika 3,3 V |
| GND | 6 | GND | wspólna masa |
| GPIO14 / TXD | 8 | C/R / RXD | Pi nadaje, DFR1184 odbiera |
| GPIO15 / RXD | 10 | D/T / TXD | DFR1184 nadaje, Pi odbiera |

TX i RX muszą być skrzyżowane. Zalecane jest zasilanie DFR1184 z 3,3 V, aby sygnał
TX modułu nie przekroczył dopuszczalnego poziomu GPIO Raspberry Pi. Wejścia GPIO Pi
nie są odporne na logikę 5 V.

```text
Raspberry Pi 3                         DFR1184 (tryb UART)
pin 1  3V3  ───────────────────────── VCC
pin 6  GND  ───────────────────────── GND
pin 8  TXD  ───────────────────────── C/R (RXD)
pin 10 RXD  ───────────────────────── D/T (TXD)

Sygnał 0–10 V (+) ─────────────────── AIN1 albo AIN2
Masa sygnału      ─────────────────── GND wejściowe
```

## Podłączenie sensora z wyjściem napięciowym

Poniższe połączenie jest poprawne dopiero po potwierdzeniu w karcie katalogowej,
że sensor ma pojedyncze wyjście napięciowe mieszczące się w zakresie 0–10 V:

```text
sensor OUT / SIGNAL ─────────────── AIN1 albo AIN2
sensor GND / 0 V    ─────────────── GND wejściowe DFR1184
sensor VCC / +Vs    ─────────────── zasilacz zgodny z kartą sensora
```

Nie wolno wyznaczać funkcji przewodów wyłącznie na podstawie ich kolorów.
Sensor wymagający 12 V lub 24 V musi korzystać z odpowiedniego zasilacza
zewnętrznego. Wyjścia 4–20 mA wymagają osobnego przetwornika prąd–napięcie.

## Konfiguracja UART w Raspberry Pi OS

1. Uruchom `sudo raspi-config`.
2. W `Interface Options → Serial Port` wyłącz konsolę logowania na porcie szeregowym.
3. Włącz sprzętowy port szeregowy.
4. Sprawdź, czy konfiguracja startowa zawiera `enable_uart=1`.
5. Uruchom ponownie Raspberry Pi i sprawdź `readlink -f /dev/serial0`.

W zależności od wydania Raspberry Pi OS konfiguracja znajduje się w
`/boot/config.txt` albo `/boot/firmware/config.txt`. Na Raspberry Pi 3 Bluetooth może
zajmować pełny UART PL011. Jeżeli wymagana jest najwyższa stabilność, można świadomie
przenieść/wyłączyć Bluetooth odpowiednią nakładką, ale nie jest to wykonywane przez
ten projekt automatycznie.

Użytkownik usługi musi należeć zwykle do grupy `dialout`:

```bash
sudo usermod -aG dialout oqlos
```

Zmiana grupy zaczyna działać po ponownym zalogowaniu lub restarcie usługi.

## Protokół UART DFR1184

Test obecności:

```text
TX: 41 54 0d 0a        AT\r\n
RX: 4f 4b 0d 0a        OK\r\n
```

Odczyt kanału:

1. Wybierz kanał 1 lub 2: `CC 20 01 <kanał>`.
2. Odczekaj 20 ms.
3. Zażądaj trzech bajtów: `BB 31 03`.
4. Odczytaj dokładnie trzy bajty wyniku big-endian.

```text
raw = byte0 × 65536 + byte1 × 256 + byte2
millivolts = raw / 100
volts = raw / 100000
```

Jednostka surowego wyniku to `0,01 mV`. Jest to format raportowania protokołu, a nie
rzeczywista rozdzielczość fizyczna toru.

## Bezpieczeństwo

1. Zweryfikuj miernikiem napięcie i polaryzację przed podłączeniem AIN.
2. Nie podłączaj 24 V ani pętli 4–20 mA bez właściwego przetwornika wejściowego.
3. DFR1184 nie zapewnia separacji galwanicznej od masy Raspberry Pi.
4. Nie zmieniaj przełącznika I²C/UART pod zasilaniem.
5. Nie podawaj logiki 5 V na RXD Raspberry Pi.

## Źródła producenta

- [DFRobot Wiki — DFR1184](https://wiki.dfrobot.com/dfr1184/)
- [DFRobot — strona produktu](https://www.dfrobot.com/product-2917.html)
- [DFRobot_ADS1115_0_10V — GitHub](https://github.com/DFRobot/DFRobot_ADS1115_0_10V)

# NOVA v7 – špecifikácia „najlepšej verzie“

Jediný zdroj pravdy pre čísla je `nova/spec.py`. Tento dokument vysvetľuje dizajn, funkcie a diely.

## 0. Súradnice a jednotky
* Všetko v **mm**. **Z hore**, počiatok = podlaha (spodok dosky B02), stred pôdorysu základne.
* Robot sa pozerá do **−Y** (pohľad SPREDU = kamera v −Y).
* **Pravá strana robota = −X** (vo vyobrazení spredu je VĽAVO). Ľavá strana = +X.
* Základná póza: všetky kĺby 0°, hlava rovno, ruky visia.

## 1. Celok
| | hodnota |
|---|---|
| Výška | ~263 mm (vrch hlavy z=262, gumové nožičky −1.2) |
| Šírka × hĺbka (základňa) | 178 × 144 mm |
| Šírka cez ruky | ~176 mm |
| Hmotnosť (odhad) | ~1.1 kg (batérie v základni → nízke ťažisko, stabilný) |
| Stupne voľnosti | 5: otáčanie tela 360°, hlava otáčanie ±90°, náklon −20/+30°, 2× rameno −30/+180° |
| Výrazy | 4.3" IPS 800×480 displej s očami, LED krúžky v ušiach, LED pásik na hrudi a na základni |
| Vnímanie | kamera v hlave, 2 mikrofóny v ušiach (smerovanie hlasu), ToF + svetelný senzor v hrudi, dotyk na temene a ušiach, IMU |

Výšky (Z): základňa 0–36 · trup 37–139 · golier 139–145.5 · krk 146–162 · os náklonu z=178 · hlava 166–262.

## 2. Diely (čísla dielov)
### Základňa B (z 0–36) – energetický, zvukový a otočný modul
* **B01 Horný kryt základne** – biely, pôdorys zaoblený obdĺžnik 178×144 R40, výška 32 (z 4–36), stena 2.5, horná hrana R10. Na vrchu kruhové lôžko otočne Ø92×0.8.
  Vzadu: mriežka reproduktora 2×13 otvorov Ø2.2, USB-C (9.4×3.6) a vypínač Ø7 (vzadu vpravo).
* **B02 Spodná doska** – čierna, 172×138 R37, hr. 4, 4× skrutka M3 (zápustné), vetracie štrbiny, 4 lôžka nožičiek.
* **B03 Svetlovod** – tyrkysový, 64×4 R2, spredu z=19, zapustený do líca.
* **B04 Gumové nožičky** 4× Ø14×1.2 TPU.
* Vnútri: 2× 18650 (2S, 7.4 V, ~25 Wh), BMS + USB-C PD nabíjanie, menič 5 V/5 A, gimbal BLDC GM3506 s enkodérom (otáčanie tela J1), ložisko 6808-2RS (Ø40/52×7), 6-žilový zberací krúžok Ø12.5, reproduktor Ø40 3 W (strieľa dozadu do mriežky).

### Trup T (z 37–139) – mozog a ramenné servá
* Tvar: superelipsa n=3.2, 106×90, spodné zaoblenie R16, horné R22 (plochý vrch pre golier).
* **T02 Telo (jadro)** – biele, bočné strany s ramennými otvormi Ø23 + zapustenie Ø31.4, vrch s otvorom Ø40 pre krk, zadný rám pre dvierka.
* **T01 Predný panel** – biely pás |x|≤38 cez celé čelo (viditeľné zvislé deliace čiary ako na zadaní). Nesie T05 a T06.
* **T03 Zadné dvierka** – 76×76 R14, servisný prístup, 5 vetracích štrbín 28×2 hore, magnet + 2 skryté skrutky.
* **T04 Spodná doska trupu** – čierna superelipsa 70×54, 4× M2.5, stredový otvor Ø20 (káble zo zberacieho krúžku).
* **T05 LED svetlovod** – tyrkysový 40×4 R2 na z=96.
* **T06 Senzorové okienko** – matné svetlosivé 26×4 R2 na z=80 (ToF VL53L1X + svetelný senzor).
* Vnútri: Raspberry Pi 5 (zvislo, pri dvierkach) s aktívnym chladičom, 2× servo ramien (os ramien z=112), servo otáčania hlavy (zvislo pod golierom), riadiaca doska (ESP32-S3 + zbernica serv + zosilňovač + IMU).

### Krk N
* **N01 Spodný golier** – čierny, elipsa 58×46, v=6.5, otvor Ø36, horný nákružok Ø40. Pevne na trupe.
* **N02 Plast krku** – čierny „trúbkovitý“ kužeľ Ø38 → Ø25, v=16, 2 polovice (delenie v rovine YZ). Otáča sa (J2).
* **N06 Kryt náklonu** – čierny T-diel: valec Ø30×48 (os X, z=178) + driek Ø20.5, oválny prechod pre káble 12×6. V ňom servo náklonu.
* **N07 Koncové krytky L/P** – čierne Ø29×6, mierne klenuté; sú pripojené k hlave (otáčajú sa s náklonom J3).

### Hlava H (z 166–262)
* **H01 Hlavný obal** – biely, 132×100×96, zaoblenie siluety spredu R28, zadná hrana R24, stena 2.2. Otvory: predný pre rám, zadný pre kryt, bočné pre uši Ø36, spodné vybranie 68×46 R12 pre krk, 6 vetracích štrbín zdola vzadu.
* **H02 Zadný kryt** – biela miska 100×66 R18 premietnutá na zadnú plochu.
* **H03 Predný rám** – čierny soft-touch, 124×88 R24, vystupuje 4.5 mm pred biely okraj (4 mm biely lem dookola), predná hrana R3.
* **H04 Sklo** – 108×76 R16 ×1.1, čierna potlač okraja 4 mm, otvor kamery Ø3.2 hore v strede (z=250).
* **H05 Uši L/P** – čierne disky Ø36, vystupujú 8 mm, stred y=+4, z=214. Kapacitný dotyk + mikrofón (otvor Ø1).
* **H06 LED krúžky uší** – tyrkysové svetlovody Ø30/Ø23.
* Vnútri: displej 4.3" DSI 800×480 (obrys 105.5×67.2, stred z=210), mini kamera 8.5×8.5 na FPC, vnútorná kostra H11 (nesie displej a pripája sa na N07), doska hlavy H13 (LED, mikrofóny, dotyk).
* Oči (základný výraz): dve zvislé „pilulky“ 11×19 R5.5, stredy x=±10.5, z=210, teplá biela.

### Ruky A (P = −X, Ľ = +X, zrkadlovo)
* Os ramena: rovnobežná s X, y=0, z=112. Rozpaženie 3° (spodok von).
* Tvar ruky: „vajíčko/pádlo“ – široká plocha do strán. Vrch z=126, najširšie z=74, spodok z=42; šírka (Y) 38, hrúbka (X) 20; delenie v strede hrúbky.
* **A01 Vonkajšia skrupina** – biela (vonkajšia polovica).
* **A02 Vnútorná skrupina** – biela, s nábojom Ø26/Ø22.4 pre kryt kĺbu.
* **A03 Vložka špičky** – čierne TPU, polmesiac na spodnej prednej vonkajšej hrane (mäkký nárazník).
* **A04 Kryt kĺbu** – čierny valec Ø26, x 54.5–65.5, čap Ø22×3 do náboja, otvor Ø14 pre unášač serva.
* **A05 Prechodový krúžok** – čierny Ø31/Ø23 × 2.5, zapustený v trupe (nesie ložisko).

## 3. Elektronika (BOM)
| # | komponent | umiestnenie |
|---|---|---|
| E1 | Raspberry Pi 5 4/8 GB + aktívny chladič | trup, zvislo pri dvierkach |
| E2 | Waveshare 4.3" DSI LCD 800×480 IPS | hlava |
| E3 | Mini kamera 8.5×8.5 (IMX219/OV5647) FPC | hlava, za sklom hore |
| E4 | 2× MEMS mikrofón I2S (INMP441) | uši |
| E5 | Reproduktor Ø40 4 Ω 3 W + MAX98357A | základňa (vzadu) |
| E6 | 4× Feetech SCS0009 serial-bus servo | 2× ramená, 1× otáčanie hlavy, 1× náklon |
| E7 | Gimbal BLDC GM3506 + AS5048A + SimpleFOC mini | základňa (J1) |
| E8 | 2× 18650 3500 mAh (2S) + BMS + USB-C PD | základňa |
| E9 | 6-žilový zberací krúžok Ø12.5 | stred základne |
| E10 | ESP32-S3 riadiaca doska (serv. zbernica, LED, dotyk, IMU BMI270) | trup, dole |
| E11 | VL53L1X ToF + VEML7700 | za T06 |
| E12 | WS2812B-2020 LED (8+8) + 2× LED krúžok 12× | T05, B03, H06 |

## 4. Výroba
* Biele kryty: PC/ABS (vstrekovanie) alebo SLA/MJF tlač + lak satén. Stena 2.2–2.5 mm.
* Čierne diely: ABS soft-touch, A03/B04 TPU 85A.
* Spoje: zámky (snap-fit) + skryté skrutky M2 do zalisovaných matíc; delenia so škárou 0.6 mm.

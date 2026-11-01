# NOVA mini v8.1 – kusovník elektroniky a mechaniky (AliExpress)

Verzia **v8.1 „MODERNÝ – NIČ NEVIDNO“**. Ceny sú orientačné v € **vrátane DPH** (AliExpress pre EÚ účtuje DPH
priamo v cene, stav 11/2026, bežní predajcovia s doručením „Choice“). Vždy porovnaj 2–3 predajcov a pozri
recenzie s fotkami. Čísla dielov v stĺpci **ID** zodpovedajú CAD modulu `nova_v8/cad_internals.py`
(manifest `build_v8/manifest/internals.json`).

> ⚠ **Články 18650 nekupuj na AliExpresse** – kúp ich lokálne (Nkon.nl, GM Electronic, Alza, predajne s e-cigaretami
> alebo modelármi). Na AliExpresse bývajú falošné kapacity („9900 mAh“), recyklované články a lítiové články
> sa navyše často nesmú posielať poštou. Odporúčané: **Samsung INR18650-35E**, **LG MJ1** alebo **Molicel P28A**
> (vyššie prúdy), 2 ks z tej istej šarže, **bez** vlastnej ochrany (ochranu robí BMS).

## 1. Riadenie a displej

| ID | Komponent | Hľadaj na AliExpresse | ks | ~€ / ks | ~€ spolu |
|---|---|---|---|---|---|
| IH01 IH02 IH03 | Doska hlavy: ESP32-S3 + 3.5" IPS 480×320, kapacitný dotyk (tvár, Wi-Fi AI, zosilňovač) – lacnejšia **Guition JC3248W535**, alebo **Waveshare ESP32-S3-Touch-LCD-3.5** (lepší softvér, kamerový konektor) | `JC3248W535 ESP32-S3 3.5 inch` / `Waveshare ESP32-S3-Touch-LCD-3.5` | 1 | 18 (Guition) / 32 (Waveshare) | 18–32 |
| IT08 | Riadiaci modul trupu **ESP32-C3 SuperMini** (servá, motory, senzory, batéria; UART do hlavy) | `ESP32-C3 SuperMini` | 1 | 2.5 | 2.5 |
| IT07 | Driver motorov **DRV8833** (2 kanály, 1.5 A) – malý modul | `DRV8833 motor driver module` | 1 | 1.2 | 1.2 |
| IT07 | Menič 5 V / 3 A pre mikro servá a hlavu (**MP1584EN** mini) | `MP1584EN mini step down 3A` | 1 | 1.0 | 1.0 |
| IT07 | Nosná DPS trupu 48 × 18.5 mm (SuperMini + DRV8833 + MP1584 + konektory serv; 74LVC1G126 pre polo-duplexnú zbernicu STS) – JLCPCB 5 ks, alebo univerzálna DPS | `JLCPCB` / `PCB prototype board 5x7` | 1 | 2 | 2 |
| IB09-1 | 2S nabíjanie z USB-C (**IP2326**, 5 V → 8.4 V, 1.5 A) – modul s **vertikálnou** USB-C (zospodu) alebo USB-C na kábliku | `IP2326 2S Type-C charging module 8.4V` | 1 | 1.8 | 1.8 |
| IB09-1 | Ochrana 2S **BMS** 8.4 V 5 A (prebitie, podbitie, skrat) | `2S BMS 8.4V 5A protection board` | 1 | 0.9 | 0.9 |
| IB09-1 | Vertikálna zásuvka **USB-C 16p (180°)** – ak modul IP2326 nemá vertikálnu, prispájkuje sa na malú DPS | `USB-C female vertical 16pin` | 1 (bal. 10) | 1.5 | 1.5 |
| IB09-2 | Zapustené tlačidlo zapnutia zospodu – **samoaretačné 6 × 6 mm** (push-on / push-off, bez soft-power obvodu) | `6x6 self-locking tactile switch` | 1 (bal. 20) | 1.0 | 1.0 |

## 2. Pohony

| ID | Komponent | Hľadaj na AliExpresse | ks | ~€ / ks | ~€ spolu |
|---|---|---|---|---|---|
| IT01 | **Feetech STS3215** 7.4 V (19 kg·cm, magnetický 12-bit snímač) – otáčanie trupu J1, beží priamo z 2S batérie | `Feetech STS3215 7.4V` | 1 | 16 | 16 |
| IT02 | Hliníkové ramienko Ø20 (25T) – býva v balení serva | (v balení) | 1 | 0 | 0 |
| IT05 IN01 IH04 | **Mikro servo** – ramená J4/J5, otáčanie hlavy J2, náklon hlavy J3 (spoločná obálka 23 × 12.2 mm, úchyty 32.5 mm) – pozri tabuľku 2a | `MG90S metal gear` alebo `Feetech SCS0009` | 4 | 2.3 / 6.5 | 9–26 |
| IB01 IB02 | Motor **N20 6 V s enkodérom** (Hallov snímač, 7 PPR), prevod **1:150** (1:100 rýchlejší, 1:210 jemnejší) | `N20 gear motor encoder 6V 1:150` | 2 | 4.5 | 9 |
| – | Kolesá Ø34 pre N20 (D-hriadeľ 3 mm) – alebo tlač: disk PETG + pneumatika TPU 85A | `N20 wheel 34mm D 3mm` | 1 pár | 1.5 | 1.5 |
| – | Guľôčky do koliesok – oceľová guľa Ø12 mm (ložisková) | `steel ball 12mm bearing ball` | 2 (bal. 10) | 1.2 | 1.2 |
| IT04 | Tenké ložisko **6806-2RS** 30 × 42 × 7 (otáčanie trupu) | `6806-2RS bearing 30x42x7` | 1 | 2.5 | 2.5 |
| IN03 | Tenké ložisko **6805-2RS** 25 × 37 × 7 (otáčanie hlavy) | `6805-2RS bearing 25x37x7` | 1 | 2.2 | 2.2 |

### 2a. Mikro servá – lacnejšie vs. tichšie (všetky 4 sú zámenné v tej istej obálke)

| Typ | Riadenie | Hluk / správanie | Cena | Kedy |
|---|---|---|---|---|
| **MG90S** (kovové prevody) | PWM (1 pin na servo) | počuteľné bzučanie a „cvakanie“ v pokoji, bez spätnej väzby polohy | ~2.3 € | najlacnejšia funkčná voľba, prototyp |
| **Feetech SCS0009** | sériová zbernica (rovnaký 1-vodičový UART ako STS3215, knižnica SCServo / trieda SCSCL) | výrazne tichšie, plynulé rozbehy, číta polohu/záťaž/teplotu, menej káblov (zbernica) | ~6.5 € | odporúčané pre ramená a hlavu (robot je na stole pri ľuďoch) |
| SG90 (plastové prevody) | PWM | tiché, ale slabé a prevody sa ľahko vylomia | ~1.2 € | **neodporúčané** pre náklon hlavy (hlava ~180 g) |

Tip: kombinácia **SCS0009 v hlave (J2, J3)** + **MG90S v ramenách** je dobrý kompromis cena/hluk. Pri SCS0009 v hlave
riadi servo náklonu priamo ESP32-S3 (1 pin UART), pri MG90S 1 pin PWM.

## 3. Senzory, svetlo, zvuk

| ID | Komponent | Hľadaj na AliExpresse | ks | ~€ / ks | ~€ spolu |
|---|---|---|---|---|---|
| IT09 | Laserový diaľkomer **VL53L0X** (za dymovým pásom na hrudi) – čip/mini modul | `VL53L0X module` | 1 | 2.0 | 2.0 |
| IT09 | Snímač okolitého svetla **LTR-303ALS** (alebo BH1750) – za tým istým oknom | `LTR-303ALS` / `BH1750 module` | 1 | 0.8 | 0.8 |
| IT09 IB08 IH07 | LED **WS2812B-2020** (hruď 5 ks, prstenec podsvietenia 24 ks, uši 2 × 6 ks) – na vlastných malých DPS | `WS2812B 2020 LED 100pcs` | 1 bal. | 2.5 | 2.5 |
| IT09 IB08 IH07 | Vlastné DPS: hrudná 46 × 14, 2 × ucho Ø23, **flex prstenec** podsvietenia 124 × 102 (JLCPCB, 5 ks + flex) – alternatíva uší: `WS2812B 7-bit ring 23mm` | `JLCPCB` | 1 sada | 20 | 20 |
| IB08 | Alternatíva flex prstenca podsvietenia: 4 rovné kúsky pásika **WS2812B-2020 5 mm** (160 LED/m) prepojené v rohoch vodičmi, ležia na opálovom svetlovode B-UG a svietia dolu | `WS2812B 2020 strip 5mm 160led` | 0.5 m | 6 / m | 3 |
| IB07 | Senzory pádu **TCRT5000** (4 rohy, cez IR okienka) – holé súčiastky na mini DPS; robustnejšia alternatíva VL53L0X 4 × (~8 €) | `TCRT5000 reflective sensor` | 4 (bal. 10) | 1.5 | 1.5 |
| IB06 | Reproduktor **Ø28 mm 8 Ω 1–2 W** (stojí zvislo vpredu, strieľa do uzavretej komôrky, ktorá ústi mikroperforáciou v dne) | `speaker 28mm 8ohm 2W` | 1 | 0.9 | 0.9 |
| IH08 | MEMS mikrofón **INMP441** (I2S) – na zadnej strane platne H07 nad doskou, počuje cez škáru rámu (Guition nemá mikrofón; pri Waveshare netreba) | `INMP441 I2S microphone module` | 1 | 1.8 | 1.8 |
| IH06 | Kamera **OV2640** 66° na FPC (voliteľná; len s doskou, ktorá má DVP konektor – Waveshare) | `OV2640 camera module 24pin` | 1 | 4 | 4 |

## 4. Napájanie a káble

| ID | Komponent | Kde kúpiť / hľadaj | ks | ~€ / ks | ~€ spolu |
|---|---|---|---|---|---|
| IB05 | Článok **18650** (Samsung 35E / LG MJ1 / Molicel P28A) | **lokálne** (nie AliExpress) | 2 | 5 | 10 |
| IB04 | Kontakty článku 18650 – poniklovaná **plôška (+)** a **kužeľová pružina (−)**, zasunuté do čiel tlačených šácht nad poklopmi (šachta = držiak) | `18650 battery spring contact plate` | 2 páry (bal. 10) | 1.2 | 1.2 |
| IB10 | Kontakty doku: pozlátené **pogo piny** Ø3 na DPS nabíjania/tlačidla (tlačia na nity plôšok B12) + mosadzné plôšky Ø6 | `pogo pin 3mm spring loaded` / `brass contact pad 6mm` | 1 sada | 1.5 | 1.5 |
| IW1 | Kábel krku: 6 × silikónový vodič **30 AWG** (5 V, GND, TX, RX + 2 reproduktor) | `30AWG silicone wire 6 colors` | 1 sada | 3 | 3 |
| IW2 | Slučka otáčania trupu: zväzok Ø6 (2 × 22 AWG batéria, 2 × 2 motor, 2 × 4 enkodér, senzory) | `22AWG silicone wire` + `28AWG` | 1 sada | 3 | 3 |
| – | Konektory **JST-SH 1.0** / **JST-GH 1.25** s káblikmi (servá, enkodéry, LED) | `JST SH 1.0 connector with cable` | 1 bal. | 3 | 3 |
| – | Zmršťovacia bužírka, PET oplet 3 mm a 6 mm | `heat shrink tube kit` / `PET braided sleeve 6mm` | 1 | 2.5 | 2.5 |

## 5. Drobná mechanika

| Komponent | Hľadaj na AliExpresse | ks | ~€ spolu |
|---|---|---|---|
| Skrutky M2 / M2.5 / M3 (samorezné do PETG + DIN 912; vrátane **M3×20** zospodu do drážkovania STS3215 = IT03), sada | `M2 M2.5 M3 screw kit` | 1 | 4 |
| Neodýmové magnety N52 **Ø5 × 2** (skrytá západka zadných dvierok trupu, 4 ks) a **Ø6 × 3** (predný modul hlavy, 4 ks) | `N52 magnet 5x2mm` / `N52 magnet 6x3mm` | 8 | 2.5 |
| Obojstranná páska VHB 0.5 mm (sklo hlavy, dymový pás) | `3M VHB 4910 tape` | 1 | 2 |
| Dymový akrylát 2 mm (pás na hrudi „dead-front“) + opálový PMMA/PETG pre prstenec podsvietenia | `smoked acrylic sheet 2mm` | 1 | 3 |

## 6. Súčet (orientačne)

| Varianta | Servá | Doska hlavy | ~€ spolu |
|---|---|---|---|
| **Najlacnejšia funkčná** (LED pásik + 7-bit krúžky namiesto vlastných DPS) | 4 × MG90S | Guition JC3248W535 | **≈ 125 €** |
| **Odporúčaná (tichšia, vlastné DPS)** | 2 × SCS0009 v hlave + 2 × MG90S v ramenách | Guition JC3248W535 | **≈ 145 €** |
| **Prémiová** | 4 × SCS0009 + kamera | Waveshare ESP32-S3-Touch-LCD-3.5 | **≈ 175 €** |

Ceny bez filamentu (PETG biely + čierny ~0.6 kg ≈ 12 €, TPU 85A ~50 g) a bez doku.

## 7. Poznámky k zapojeniu (v8.1)

* **Napájanie:** 2S Li-ion (6.0–8.4 V) → BMS → samoaretačné tlačidlo zospodu → (a) STS3215 priamo,
  (b) DRV8833 → N20 (PWM obmedzené na ~6 V), (c) MP1584 5 V/3 A → mikro servá + kábel krku do hlavy + ESP32-C3.
  Nabíjanie: USB-C zospodu vzadu (IP2326) alebo neskôr kontakty doku (paralelne na vstup nabíjačky).
* **Zbernice:** ESP32-C3 ↔ ESP32-S3 UART 1 Mbit (2 vodiče v krku). STS3215 (+ SCS0009 ramien) na jednej
  1-vodičovej zbernici cez 74LVC1G126. Enkodéry N20 na 4 GPIO (prerušenia). WS2812B (hruď + podsvietenie) 1 dátový
  vodič, uši riadi hlava.
* **Reproduktor** je v základni, zosilňovač na doske hlavy → v krku sú preto **6 vodičov** (4 + pár reproduktora).
* Nič z toho nie je zvonka vidieť: USB-C, tlačidlo, kontakty doku, poklop batérií, reproduktor, senzory pádu
  aj vetranie sú na spodku; jediné viditeľné svetlá sú dymový pás na hrudi, uši a podsvietenie pod základňou.

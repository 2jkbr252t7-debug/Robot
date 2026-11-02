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
| IT08 | Riadiaci modul trupu **ESP32-C3 SuperMini** (zbernica serv: STS3215 + uzol základne; mikro servá, hrudné LED a senzory; UART do hlavy) – 11 z 13 GPIO, rozpis v kap. 7 | `ESP32-C3 SuperMini` | 1 | 2.5 | 2.5 |
| IT07 | Menič 5 V / 3 A pre mikro servá, hrudné LED, ESP32-C3 a hlavu (**MP1584EN** mini) | `MP1584EN mini step down 3A` | 1 | 1.0 | 1.0 |
| IT07 | Nosná DPS trupu 48 × 18.5 mm (SuperMini na lištách + MP1584 + **74LVC1G126** budič 1-vodičovej zbernice serv + konektory serv, krku a JST-GH 6p pásu J1) – JLCPCB 5 ks | `JLCPCB` | 1 | 2 | 2 |
| IB09-1 IB09-2 | **2 DPS základne s osadením (JLCPCB PCBA, čierna maska)** – IB09-1: nabíjanie 2S z USB-C **IP2326** (1.5 A), 2S ochrana, hlavný spínač **AO4407A**, vertikálna USB-C 16p; IB09-2 = **uzol základne**: **STM32G030K8T6** (slave na zbernici serv), **DRV8833PWP** (obe N20), 5 V/2 A **TPS563201** (podsvietenie, enkodéry, senzory), 3.3 V **AP2112K**, JST-GH 6p + JST-SH 6p | `JLCPCB PCBA` (diely z katalógu LCSC) | 1 sada (5 ks min.) | 25 | 25 |
| IB09-2 | Zapustené tlačidlo zapnutia zospodu – **samoaretačné 6 × 6 mm** (push-on / push-off, spína len hradlo AO4407A) | `6x6 self-locking tactile switch` | 1 (bal. 20) | 1.0 | 1.0 |
| (prototyp) | Len na skúšobný stôl, do základne sa nezmestí: moduly `IP2326 2S Type-C charging module` + `2S BMS 8.4V 5A` + `DRV8833 motor driver module` + `STM32G030 / CH32V003 dev board` na kábliku | – | – | ~6 | – |

## 2. Pohony

| ID | Komponent | Hľadaj na AliExpresse | ks | ~€ / ks | ~€ spolu |
|---|---|---|---|---|---|
| IT01 | **Feetech STS3215** 7.4 V (19 kg·cm, magnetický 12-bit snímač) – otáčanie trupu J1, beží priamo z 2S batérie | `Feetech STS3215 7.4V` | 1 | 16 | 16 |
| IT02 | Hliníkové ramienko Ø20 (25T) – býva v balení serva | (v balení) | 1 | 0 | 0 |
| IT05 IN01 IH04 | **Mikro servo** – ramená J4/J5, otáčanie hlavy J2, náklon hlavy J3 (spoločná obálka 23 × 12.2 mm, úchyty 32.5 mm) – pozri tabuľku 2a | `MG90S metal gear` alebo `Feetech SCS0009` | 4 | 2.3 / 6.5 | 9–26 |
| IB01 IB02 | Motor **N20 6 V s enkodérom** (Hallov snímač A/B, 7 PPR → 4200 impulzov/ot. kolesa pri 1:150 a štvornásobnom čítaní), prevod **1:150** (1:100 rýchlejší, 1:210 jemnejší) | `N20 gear motor encoder 6V 1:150` | 2 | 4.5 | 9 |
| – | Kolesá Ø34 pre N20 (D-hriadeľ 3 mm) – alebo tlač: disk PETG + pneumatika TPU 85A | `N20 wheel 34mm D 3mm` | 1 pár | 1.5 | 1.5 |
| – | Guľôčky do koliesok Ø12 mm **čierne** (POM alebo keramika Si3N4 – v tieňovej škáre pod základňou sa neleskne ako oceľ) | `POM ball 12mm black` / `Si3N4 ceramic ball 12mm` | 2 (bal. 10) | 1.5 | 1.5 |
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
| IH08 | MEMS mikrofón **INMP441** (I2S) – naležato na strope kapsy valca v hlave, spodný port cez penový krúžok VHB nad skrytou vetracou štrbinou → počuje cez ústie kapsy okolo krku (Guition nemá mikrofón; pri Waveshare netreba) | `INMP441 I2S microphone module` | 1 | 1.8 | 1.8 |
| IH06 | Kamera **OV2640** 66° na FPC (voliteľná; len s doskou, ktorá má DVP konektor – Waveshare) | `OV2640 camera module 24pin` | 1 | 4 | 4 |

## 4. Napájanie a káble

| ID | Komponent | Kde kúpiť / hľadaj | ks | ~€ / ks | ~€ spolu |
|---|---|---|---|---|---|
| IB05 | Článok **18650** (Samsung 35E / LG MJ1 / Molicel P28A) | **lokálne** (nie AliExpress) | 2 | 5 | 10 |
| IB04 | Kontakty článku 18650 – poniklovaná **plôška (+)** a **kužeľová pružina (−)**, zasunuté do čiel tlačených šácht nad poklopmi (šachta = držiak) | `18650 battery spring contact plate` | 2 páry (bal. 10) | 1.2 | 1.2 |
| IB10 | Kontakty doku: pozlátené **pogo piny** Ø3 na DPS nabíjania/tlačidla (tlačia na nity plôšok B12) + mosadzné plôšky Ø6 | `pogo pin 3mm spring loaded` / `brass contact pad 6mm` | 1 sada | 1.5 | 1.5 |
| IW1 | Kábel krku (6 vodičov, zväzok Ø3): **2 × 26 AWG** (5 V, GND – špičky ~2 A) + **4 × 30 AWG** (TX, RX, reproduktor ±) silikón | `26AWG silicone wire` + `30AWG silicone wire` | 1 sada | 3 | 3 |
| IW2 IW3 | Kábel otáčania trupu J1: **plochý pás 6 vodičov na hranu** (2 × **24 AWG** VBAT/GND + 4 × **28 AWG** zbernica, reproduktor ±, GND) zlepený Kaptonovou páskou každých 20 mm, dĺžka v žľabe 209 mm (valivá slučka), na konci JST-GH 6p | `24AWG silicone wire` + `28AWG silicone wire` + `kapton tape 5mm` | 1 sada | 3 | 3 |
| – | Konektory **JST-SH 1.0** / **JST-GH 1.25** s káblikmi (servá, enkodéry, LED) | `JST SH 1.0 connector with cable` | 1 bal. | 3 | 3 |
| – | Zmršťovacia bužírka, PET oplet 3 mm a 6 mm | `heat shrink tube kit` / `PET braided sleeve 6mm` | 1 | 2.5 | 2.5 |

## 5. Drobná mechanika

| Komponent | Hľadaj na AliExpresse | ks | ~€ spolu |
|---|---|---|---|
| Skrutky M2 / M2.5 / M3 (samorezné do PETG + DIN 912; vrátane **M3×20** zospodu do drážkovania STS3215 = IT03), sada | `M2 M2.5 M3 screw kit` | 1 | 4 |
| Neodýmové magnety N52 **Ø5 × 2** (skrytá západka zadného servisného krytu T02, 4 ks) a **Ø6 × 3** (predný modul hlavy, 4 ks) | `N52 magnet 5x2mm` / `N52 magnet 6x3mm` | 8 | 2.5 |
| Optická lepiaca fólia **OCA 0.2 mm** pre 3.5" panel – dymové sklo sa laminuje priamo na displej (funguje dotyk, bez dvojitého odrazu); pri slabom dotyku cez 2 mm PMMA použi sklo 1.5 mm | `OCA optical clear adhesive 3.5 inch` | 1 bal. | 2 |
| Obojstranná páska VHB 0.5 mm (okraj skla hlavy v ráme, dymový pás na hrudi) | `3M VHB 4910 tape` | 1 | 2 |
| Dymový akrylát 2 mm (pás na hrudi „dead-front“) + opálový PMMA/PETG pre prstenec podsvietenia | `smoked acrylic sheet 2mm` | 1 | 3 |

## 6. Súčet (orientačne)

| Varianta | Servá | Doska hlavy | ~€ spolu |
|---|---|---|---|
| **Najlacnejšia funkčná** (LED pásik + 7-bit krúžky namiesto vlastných LED DPS; DPS základne s osadením ostávajú) | 4 × MG90S | Guition JC3248W535 | **≈ 140 €** |
| **Odporúčaná (tichšia, vlastné DPS)** | 2 × SCS0009 v hlave + 2 × MG90S v ramenách | Guition JC3248W535 | **≈ 160 €** |
| **Prémiová** | 4 × SCS0009 + kamera | Waveshare ESP32-S3-Touch-LCD-3.5 | **≈ 190 €** |

Revízia 2 zvýšila súčet asi o 15 €: DPS základne sa objednávajú osadené (JLCPCB PCBA, poplatok za osadenie
a „extended“ diely). Nahrádzajú IP2326/BMS/DRV8833 moduly a hlavne umožňujú, aby cez otočný kĺb J1 išlo len
6 vodičov (inak sa kábel pri ±150° nedá vedenie urobiť spoľahlivo).

Ceny bez filamentu (PETG biely + čierny ~0.6 kg ≈ 12 €, TPU 85A ~50 g) a bez doku. OCA fólia pridáva ~2 €.

**Firmvér – mäkké limity:** ruka zdvihnutá nad 135° môže zavadiť o spodný roh rámu hlavy, keď je hlava zároveň sklonená dole (−10 až −20°) a natočená 20–50° k tej ruke. Pri takej kombinácii obmedz rameno na 135° (pri natočení hlavy 45° stačí 165°). Hlava B: rameno ≤ 155°, keď hlava pozerá dole (pod −5°) a je natočená k tej ruke; inak do 180°. Trup J1 drž v rozsahu ±150° (valivá slučka kábla).

## 7. Zapojenie a rozpis pinov (v8.1, revízia 2)

```
hlava ESP32-S3 ──UART 1 Mbit + 5 V/GND + reproduktor (krk, 6 vodičov)──► trup ESP32-C3 SuperMini
trup ESP32-C3 ──1-vodičová zbernica serv 1 Mbit (74LVC1G126)──► STS3215 (J1)  [+ SCS0009 J2–J5, ak sú zvolené]
                                                             └──(pás J1)──► uzol základne STM32G030 (IB09-2)
uzol základne ──► DRV8833 → 2× N20 · enkodéry A/B · 4× TCRT5000 · 24× WS2812B podsvietenie · stav nabíjania/doku
```

* **Napájanie:** 2S Li-ion (6.0–8.4 V) → 2S ochrana → hlavný P-MOSFET **AO4407A** (jeho hradlo spína samoaretačné
  tlačidlo zospodu, cez tlačidlo netečie prúd robota) → VBAT:
  (a) v základni: DRV8833 → N20 (PWM obmedzené na ~6 V), TPS563201 5 V/2 A → podsvietenie, enkodéry, senzory pádu,
  AP2112K 3.3 V → STM32G030; (b) cez pás J1 (2 × 24 AWG) do trupu: STS3215 priamo, MP1584 5 V/3 A → mikro servá,
  hrudné LED, ESP32-C3 a kábel krku do hlavy (5 V/GND 2 × 26 AWG).
  Nabíjanie: USB-C zospodu vzadu (IP2326) alebo neskôr kontakty doku (paralelne na vstup nabíjačky).
* **Cez otočný kĺb J1 idú len 6 vodičov:** VBAT, GND, zbernica, reproduktor +/−, GND. Plochý pás leží na hrane vo
  valivej slučke v žľabe B15: vonkajší beh na pevnom okraji žľabu, oblúk R6, vnútorný beh na otočnom puzdre ložiska
  T04. Pri otočení trupu o Δ sa oblúk posunie o ~0.4 Δ, dĺžka (209 mm) ani polomer ohybu sa nemenia → ±150° bez
  zberacieho krúžku a bez únavy vodičov.
* **Uzol základne** je na zbernici ďalšie „servo“ (napr. ID 20, protokol Feetech SCS: zápis rýchlostí kolies a farby
  podsvietenia, čítanie enkodérov, senzorov pádu, napätia batérie a stavu nabíjania). Okraj stola rieši **lokálne**
  – motory zastaví do 1 ms aj bez trupu. Firmvér: cez SWD plôšky alebo zavádzačom cez zbernicu z ESP32-C3.
* **ESP32-C3 SuperMini (trup) – 11 z 13 GPIO:**

| GPIO | Funkcia |
|---|---|
| 20 / 21 | UART0 RX / TX ↔ hlava (ESP32-S3) |
| 6 / 7 / 10 | UART1 TX / RX / smer → 74LVC1G126 → zbernica serv (STS3215, uzol základne, SCS0009) |
| 8 / 9 | I2C SDA / SCL – VL53L0X + LTR-303 na hrudnej DPS (oba strapping piny majú aj tak pull-up 4.7 k) |
| 2 | dáta WS2812B – svetelný pás na hrudi (5 LED) |
| 3 / 4 / 5 | PWM mikro serv J4 / J5 / J2, ak sú MG90S (pri SCS0009 voľné – servá sú na zbernici) |
| 0 / 1 | voľné (napr. Hallov snímač zatvorenia zadného krytu, rezerva) |

* **STM32G030K8T6 (základňa):** USART1 v jednovodičovom polo-duplexe = zbernica; TIM1 a TIM3 v režime enkodéra
  (A/B oboch motorov); TIM14 / TIM16 PWM + 2 GPIO smer → DRV8833; ADC: 4 senzory pádu + napätie batérie (delič);
  SPI1 MOSI → WS2812B podsvietenie; GPIO: zapínanie IR LED senzorov, stav nabíjania IP2326, detekcia doku;
  SWD plôšky na programovanie.
* **Hlava ESP32-S3:** UART k trupu, servo náklonu (PWM alebo zbernica SCS0009), dáta LED uší, I2S mikrofón INMP441
  (na rozširujúcom konektore dosky), zosilňovač dosky → **reproduktor v základni** cez krk a pás J1 (preto 6 vodičov).
* Nič z toho nie je zvonka vidieť: USB-C, tlačidlo, kontakty doku, poklopy batérií, reproduktor, senzory pádu
  aj vetranie sú na spodku; jediné viditeľné svetlá sú dymový pás na hrudi, uši a podsvietenie pod základňou.

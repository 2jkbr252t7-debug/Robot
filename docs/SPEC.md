# NOVA v7.3 – špecifikácia „najlepšej verzie“

Jediný zdroj pravdy pre čísla je `nova/spec.py` (na začiatku súboru je CHANGELOG). Tento dokument
vysvetľuje dizajn, funkcie, diely a elektroniku. Verzia v7.2 zapracúva 3 nezávislé odborné kontroly
(vernosť fotke zo zadania, mechatronika/zástavba, výroba/montáž).

## 0. Súradnice a jednotky
* Všetko v **mm**. **Z hore**, počiatok = podlaha pod doskou B02 (nožičky siahajú na z = −1.2),
  stred pôdorysu základne.
* Robot sa pozerá do **−Y** (pohľad SPREDU = kamera v −Y).
* **Pravá strana robota = −X** (vo vyobrazení spredu je VĽAVO). Ľavá strana = +X.
* Základná póza: všetky kĺby 0°, hlava rovno, ruky visia.
* Znamienka kĺbov: J1/J2 + = doľava (proti smeru hodín zhora), J3 + = hlava hore, J4/J5 + = ruka dopredu/hore.

## 1. Celok
| | hodnota |
|---|---|
| Výška | ~266 mm (vrch hlavy z = 265) |
| Základňa | 166 × 128 mm, výška 42 mm |
| Šírka cez ruky | ~173 mm (ruky presahujú základňu o ~3 mm, ako na fotke) |
| Hmotnosť (odhad) | ~1.1 kg, ťažisko z ≈ 94 mm; preklopenie až pri náklone 29° (dopredu/dozadu) a 37° (do boku) |
| Stupne voľnosti | 5: J1 telo 360°, J2 hlava ±90°, J3 náklon −20/+30°, J4/J5 ruky −30/+180° |
| Výdrž | ~3 h (25.9 Wh pri ~8 W) |

Výšky (Z): základňa 0–42 · čierna vanička trupu 43–47.5 · biely trup 47.5–142 · golier 142–148.5 ·
krk 149–165 · os náklonu z = 181 (valec Ø40 visí 8 mm pod hlavou) · hlava 169–265 · os ramien z = 115.

## 2. Diely
### Základňa B (z 0–42) – energia, zvuk, otáčanie tela
* **B01 Horný kryt základne** – biely, 166×128, rohy R24, horná hrana R10, stena 2.5. Na vrchu kruhové lôžko Ø92 hĺbky 2.
  Vzadu: mriežka reproduktora 3×15 otvorov Ø2.5 (27 % otvorenej plochy), otvor USB-C 12.6×6.8 a vypínač Ø7 (vzadu vpravo).
* **B02 Spodná doska** – čierna 160×122, 4× M3 zápustné, vetracie štrbiny, lôžka nožičiek.
* **B08 Poklop batérie** – v B02 zospodu, 42×76 R4, 1 skrutka M3 + 2 háčiky (vymeniteľné články podľa EÚ 2023/1542).
* **B03 Svetlovod** – tyrkysový 44×4, spredu z = 20.
* **B04 Nožičky** – 4× Ø14 TPU.
* **B05 Otočný tanier** – čierny disk Ø90, spojený s trupom (otáča sa s J1).
* Vnútri: 2× 18650 pozdĺž osi Y (x = −38 a −58, nad poklopom B08), BLDC GM3506 mimo osi (x = +48) s remeňom GT2 16T → 72T (4.5 : 1),
  ložisko 6808 na osi, zberací krúžok Ø12.5 v osi, plochý reproduktor Ø36 s kanálom k zadnej mriežke,
  doska základne (RP2040/ESP32-C3: SimpleFOC + AS5048A, BMS, USB-C PD, merač batérie, I2S zosilňovač, LED B03).

### Trup T (z 43–142) – mozog a ramenné servá
* Tvar bieleho tela: superelipsa n = 3.2, 112×92, spodné zaoblenie R8, horné R22 (plochý vrch pre golier).
* **T04 Spodná vanička** – čierna superelipsa 100×80, výška 4.5 → viditeľný čierny pás pod telom; 4× M2.5 ku kostre T07 + 2× M2.5 k pásu.
* **T01 Stredový pás** – biely pás |x| ≤ 35 spredu, cez vrch až dozadu (švy na x = ±35 bez priečneho švu).
  Spredu aj zozadu zostupuje rovnou zásterou až po z = 43 (dá sa vystrekovať). Nesie T05, T06 a otvor pre krk Ø34.
* **T02-R / T02-L Bočné kryty** (pravý/ľavý) – biele, s ramennými otvormi Ø23 + zapustenie Ø31.4.
* **T03 Zadné dvierka** – 60×84 R12 v páse (z 54–138, prístup k Pi), hore 5 výfukových štrbín, dole 4 nasávacie (komínové chladenie CM5).
* **T05 LED svetlovod** – tyrkysový 34×4 na z = 100.  **T06 Senzorové okienko** – matné 23×4 na z = 83.5.
* Vnútri: vnútorný rám, Raspberry Pi CM5 na sánkach T08 pri dvierkach (ventilátor nasáva dole a fúka hore), 2× servo ramien
  na osi z = 115, servo otáčania hlavy pod vrchom, ložisko 61805 v náboji pod vrchom, napájacia/riadiaca doska
  (ESP32-S3, zbernica serv, menič 5.1 V/5 A pre Pi, 6.0 V/3 A pre servá, IMU).

### Krk N
* **N01 Spodný golier** – čierny, elipsa 52×42, tenká skosená príruba (okraj 2 mm), vnútorný nákružok Ø35. Pevne na trupe.
* **N02 Plast krku** – čierny „trúbkovitý“ kužeľ Ø33 → Ø23, jeden kus. Otáča sa (J2).
* **N06 Kryt náklonu** – čierny valec Ø42×36 na osi z = 181, vo vnútri servo náklonu priamo na osi.
* **N07 Koncové krytky R/L** – Ø41×6 s nábojom Ø18, ktorý prechádza do kostry hlavy H11 (J3). V pasívnej krytke ložisko 6703 na dutom čape
  (prechod káblov) a špirálová pružina, ktorá vyrovnáva váhu hlavy (servo drží ≤ 19 % momentu).

### Hlava H (z 169–265)
* **H01 Hlavný obal** – biely, 132 × 90 × 96 (bez rámu), roh siluety spredu R32, zadná hrana R28, stena 2.2.
  Zdola vybranie 56×56 R16, hĺbka 34 (voľnosť pre náklon −20/+30°); vetranie zdola vpredu.
* **H02 Zadný kryt** – biela miska 112×66 R20 (zasahuje do zaoblenia).
* **H03 Predný rám** – čierny soft-touch 127×91 R29.5, vystupuje 7 mm, okolo 2.5 mm biely lem; horný pás 7 mm, spodný 5, boky 4.
* **H04 Sklo** – 119×79 R22 × 1.1, tvrdené, čierna potlač (hore 9 mm, inde 4 mm); nepotlačené okienko kamery Ø3.2 (z = 250.5).
* **H04E Oči** (obsah displeja) – dve „pilulky“ 13×21.5 R6.5, stredy x = ±12, z = 209.5 (mierne pod stredom).
* **H05 Uši P/Ľ** – čierne disky Ø36, vystupujú 5.5 mm, stred y = −4, z = 213; dotyk + mikrofón (otvor Ø1).
* **H06 LED krúžky uší** – tyrkysové Ø30/Ø23.
* Vnútri: displej 4.3" 800×480 s RGB rozhraním, ktorý riadi doska ESP32-S3 priamo v hlave (žiadny plochý kábel
  cez kĺby), USB UVC mini kamera 8.5×8.5, vnútorná kostra H11 (nesie displej, pripája sa na N07).

### Ruky A (P = −X, Ľ = +X, zrkadlovo)
* Os ramena rovnobežná s X: y = 0, z = 115. Rozpaženie 8° (spodok von), ako na fotke.
* Tvar: „vajíčko/pádlo“ so širokými plochami do strán – vrch z = 127, najširšie z = 87, spodok z = 53;
  šírka 32, hrúbka 17. Delenie v strede hrúbky.
* **A01 Vonkajšia skrupina** – celá biela (prémiový jemný „šošovkový“ panel).
* **A02 Vnútorná skrupina** – biela, s nábojom Ø26/Ø22.4.
* **A03 Vložka špičky** – čierne TPU na VNÚTORNEJ strane dole vpredu, zabiehá pod spodok (mäkký nárazník/úchop).
* **A04 Kryt kĺbu** – čierny Ø26, x 57.8–68.5, čap Ø22 do náboja, otvor Ø14 pre unášač serva.
* **A05 Prechodový krúžok** – čierny Ø31/Ø23 × 2.5 v trupe.
* Nad 125° sa ruka smie zdvihnúť len pri hlave otočenej rovno (|J2| ≤ 2°) – blokovanie vo firmvéri
  (inak by sa pri otočenej hlave dotkla hlavy).

## 3. Elektronika (architektúra v7.2)
**Pravidlo: žiadny plochý kábel (FPC) nepretína otočný kĺb.** Cez krk ide iba zväzok 7 vodičov Ø4
(USB2 D+/D−, 2× 5 V, 2× GND, dáta zbernice serv) cez dutý čap 6703 a 1.5 závitu okolo serva otáčania.
Cez zberací krúžok (6 okruhov) ide: 2× batéria, 2× GND, 2× RS-485.

| # | komponent | umiestnenie |
|---|---|---|
| E1 | Raspberry Pi CM5 (8 GB, 32 GB eMMC) na nosnej doske 75×56 + aktívny chladič (AI, hlas, videnie) | trup, na sánkach T08 pri dvierkach |
| E2 | 4.3" IPS 800×480 RGB displej + ESP32-S3 doska (tvár, LED uší, mikrofóny, dotyk) | hlava |
| E3 | USB UVC mini kamera 8.5×8.5 | hlava, za okienkom |
| E4 | 2× MEMS mikrofón I2S | uši (smerovanie hlasu, rozostup ~140 mm) |
| E5 | plochý reproduktor Ø36 + MAX98357A | základňa |
| E6 | 4× Feetech SCS0009 serial-bus servo (6.0 V) | ramená 2×, otáčanie hlavy, náklon |
| E7 | gimbal BLDC GM3506 + AS5048A + remeň GT2 4.5:1 + Hallov snímač (domov) | základňa (J1) |
| E8 | 2× 18650 3500 mAh (2S) + BMS + USB-C PD + merač | základňa |
| E9 | 6-okruhový zberací krúžok Ø12.5 | os základne |
| E10 | doska trupu: ESP32-S3, zbernica serv, 5.1 V/5 A, 6.0 V/3 A, IMU BMI270 | trup dole |
| E11 | doska základne: RP2040/ESP32-C3 (SimpleFOC, audio, LED, tlačidlo) | základňa |
| E12 | VL53L1X ToF + VEML7700 | za T06 |
| E13 | WS2812B-2020 (hruď, základňa) + 2× LED krúžok 12× | T05, B03, H06 |

## 4. Výroba
* Biele kryty: PC/ABS (vstrekovanie) alebo SLA/MJF tlač + lak satén. Stena 2.2–2.5 mm, úkosy ≥ 1°.
* Čierne diely: ABS/PC soft-touch, A03/B04 TPU 85A. Sklo: tvrdené 1.1 mm s potlačou a nepotlačeným okienkom kamery.
* Spoje: zámky (snap-fit) + skryté skrutky M2/M2.5 do zalisovaných matíc; všetky viditeľné delenia so škárou 0.6 mm.
* Podrobné poznámky z kontroly výroby a montáže sú v `docs/REVIEW_NOTES.md`.

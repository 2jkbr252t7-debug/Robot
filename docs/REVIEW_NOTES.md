# NOVA v7.3 – poznámky z kontroly výroby a montáže

Tento dokument dopĺňa `docs/SPEC.md` a `nova/spec.py` (CHANGELOG v7.3). Je určený pre CAD modelára
(a pre agentov, ktorí model stavajú). **Čísla v `nova/spec.py` majú prednosť.**

## Vnútorné čísla dielov (používať presne tieto ID, ASCII prípony -R/-L)
Pôvodné čísla z konceptov zostávajú: H01, H02, N01, N02, N06, A01–A05. Nové diely berú len voľné čísla:

| ID | názov | rozmer / popis |
|---|---|---|
| B06 | Náboj J1 s remenicou | Ø40 k6 v ložisku 6808, integrovaná remenica GT2 72T (PD 45.8, šírka 7), 3× zálisková matica M3 na PCD 32, otvor Ø14 pre zberací krúžok |
| B07 | Držiak motora GM3506 | na x = +48, drážky ±1.5 mm na napnutie remeňa (najbližší sériový uzavretý remeň) |
| B08 | Poklop batérie (viditeľný zospodu) | v B02: 42×76 R4 v strede (x −48, y 0), 1 neodpadávajúca skrutka M3 + 2 háčiky |
| B09 | Držiak zadnej I/O dosky | 2 stredovacie kolíky, USB-C konektor 1.2 mm zapustený v otvore 12.6×6.8 R3.4 |
| B10 | Nosič LED základne | biely PC 50×10×8 (vnútri 46×5), 5× WS2812B-2020 s rozostupom 9 mm, ≥6 mm na zmiešanie svetla |
| B11 | Box/kanál reproduktora | reproduktor Ø36×6 na (26, 40), uzavretý objem ≥15 cm³, kanál 30×6 k mriežke |
| T07 | Vnútorná kostra trupu | PC-GF30 / MJF PA12, 2.5–3 mm: podlaha 80×60×3 na vaničke, 2 ramenné veže pri \|x\| 23–52.5 (servá ramien visia z osi nadol, sedlá ložísk 6702-2RS pri \|x\| 48.5–52.5), horný most z 128.5–131.5 s lôžkom 61805 (miska Ø43, vrch z 139.4) a so servom otáčania hlavy (telo smerom −Y) |
| T08 | Sánky pre Raspberry Pi 5 | MJF PA12 2 mm, 62×92, na lištách T07; doska v rovine y = +26, z 50–135, koniec s SD kartou hore (alternatíva: CM5 s eMMC na vlastnej doske 75×56) |
| T09 | Nosič LED hrude | biely PC 38×10×8 (vnútri 34×5), 4× WS2812B-2020 s rozostupom 8 mm |
| T10 | Držiak senzorov | na vnútornej prednej stene pásu pri z = 83.5 |
| T11 | Tesnenie ToF | čierne TPU 1.0 mm, 2 otvory (oddelenie vysielača a prijímača) |
| N03 | Náboj otáčania hlavy | Ø25 h6 v 61805, príruba Ø30×1.5 pri z 147.5–149, drážkovanie serva v osi, okienko pre kábel 12×7 mimo osi |
| N04 | Preklzová spojka J2 | vlnová podložka, ~0.15 N·m |
| N05 | Zátka náklonu | čap Ø32, 3× M2; nesie vonkajší krúžok ložiska 6703 |
| H07 | DPS ucha | krúžok OD 29 / ID 24, 12× WS2812B-2020, dotyková plôška, MEMS mikrofón s tesnením Ø4×0.3 k otvoru Ø1 |
| H11 | Vnútorná kostra hlavy | MJF PA12 / PC-GF, 2.5 mm; líca pri \|x\| 30.4–32.9 sa spájajú s nábojmi N07 (2 kolíky Ø2 + 3× M2×8 na PCD 26; na pasívnej strane zostáva Ø13 voľných pre kábel) |
| H12 | Držiak kamery | na H11, tlačí modul cez čierny penový krúžok (OD 8, ID 3.6, 0.5 mm) na zadnú stranu skla |
| H13 | Doska hlavy ESP32-S3 | ~60×40 na zadnej strane H11 |
| A06 | Unášač ramena | Al 6061 / PA-GF: čap Ø15 v ložisku 6702-2RS (15×21×4) vo veži T07, driek Ø14 cez A04, drážkovaná zásuvka 25T s preklzovou spojkou 0.15–0.18 N·m, príruba Ø20×2 s 2× M2 na PCD 16 |

H04C (okienko kamery) a H04E (oči) sú len objekty pre render, nie diely: okienko je nepotlačená plocha
skla H04 a oči sú obsah displeja.

## Hlava + krk (H, N)
* **Spoj hlavy s krkom:** každá krytka N07 má náboj Ø18 (x 24.6 → 30.4), ktorý prechádza otvorom Ø18.4
  v bočnej stene vybrania hlavy do lícnice H11. Krútiaci moment prenášajú kolíky, nie trenie.
* **Servo náklonu:** v N06 Ø42 (vnútri Ø38) priamo na osi, bez úchytných uší, zovreté v lôžku z dvoch rebier
  hr. 1.5 mm. Horná plocha zarovno s koncom valca na −X, drážkovanie zasahuje 2.9 mm do hliníkovej vložky Ø20 v N07-R.
  Špirálová pružina (pásik 3.0×0.4, ~1 závit) je vo valci za servom (x +7.25 … +16), ložisko 6703 v N05.
* **N02 je jeden kus** (bez švov). Postup montáže: N03 náboj → N02 sa nasunie → N06 sa priskrutkuje 2× M2.5
  do N03 zvnútra valca (cez otvor Ø32 na +X) ešte pred vložením serva.
* **Postup montáže hlavy:** (1) hotový krk, (2) H01 sa spustí zvislo cez valec s krytkami, (3) H11 sa vloží cez
  predný otvor a lícnice sa skolíkujú a priskrutkujú, (4) H01 k H11 4× M2.5, (5) uši sa zacvaknú zvonka,
  (6) predný modul (H03 + H04 + displej): 2 spodné háčiky do H11 a 2× M2 pri (±40, z 248) zozadu cez otvor H02,
  (7) H02: 4 háčiky + 1× M2 zdola pri (0, +36), na skrytej zadnej spodnej strane.
* H01 bez zámkových klinov → forma s priamym odformovaním dopredu + bočné šupátka (uši) + spodné (vybranie, vetranie).
* **Sklo:** potlač hore 9 mm (okienko kamery je celé v potlači), inde 4 mm. H04 je prilepené PSA 0.2 mm na
  3 mm osadenie v H03, ktoré má v strede hore výrez 11 mm pre kameru. Displej sa nelepí: je zovretý medzi
  osadením (čierna pena 0.5 mm) a prednou doskou H11; pre spodný FPC kábel nechať 4 mm na ohyb.

## Trup (T)
* **Kostra T07** nesie všetko zaťaženie (hlava, servá); biele kryty sú len kozmetické.
* **Skrutky (žiadna na šve):** vanička ku kostre 4× M2.5 na (±28, ±22); vanička k pásu 2× M2.5 na (0, ±34)
  do nálitkov na zásterách pásu; bočné kryty T02-R/L 2× M2.5 pozdĺž X do veží (hlavy skrutiek vnútri).
* **Spoj s J1:** 3× M3×25 na PCD 32 zdola cez náboj B06 a remenicu 72T do matíc vo vaničke; B05 je zovretý
  na 3 dištančných krúžkoch Ø8×1.2. Prístup po odobratí B02; pod osou nechať zónu Ø56 bez dosiek.
* **Postup montáže:** (1) T07 so servami, sánkami Pi a doskou E10 na vaničke, (2) T02-R/L sa nasunú v smere ±X
  (otvor Ø23 prejde cez unášač A06 Ø15), (3) T01 sa spustí zhora: háčiky + 2 skrutky v zásterách, (4) N01,
  (5) krk, (6) celý trup na náboj zdola, (7) T03. Servis: na zloženie T01 treba najprv zložiť krk.
* **T01 vstrekovanie:** pás má spredu aj zozadu rovnú zásteru až po z = 43 (spodná hrana R2). Jadro sa odformuje
  v smere −Z, úkos 0.5–1°, 1 predné šupátko (T05/T06) a 1 zadné (otvor T03). T02-R/L sa odformujú v ±X bez šupátok.
* **T03:** 2 spodné háčiky + 2 magnety Ø6×2 N52 hore + drážka 8×1.0 na páčenie v spodnom šve, bez skrutiek.
* **T06 dvojzónové okienko:** pri x = −6 leštená zóna 9×3.2 zoslabená zvnútra na 0.8 mm (okno ToF), inde matný
  povrch len zvonka (za ním VEML7700 pri x = +6). VL53L1X ≤ 0.5 mm od okienka, tesnenie T11.

## Ruky (A)
* Unášač **A06** sa nasadí na drážkovanie serva axiálnou skrutkou M2 cez otvor Ø23 ešte pred montážou ruky.
* Podzostava A02 + A04 (čap Ø22 vlepený do náboja Ø22.4) sa nasunie na A06 a pripevní 2× M2×5 zvnútra A02.
* A01 sa zatvorí 3 háčikmi na hornom okraji + 1× M2 z vnútornej strany dole vpredu, schovaná pod A03.
* A03 (TPU 85A) drží na 2 hríbikových kolíkoch Ø2.5 a je zachytená v deliacej rovine A01/A02; dá sa vymeniť.
* Preklzová spojka v A06 chráni servo: tlak 5 N na spodok ruky dáva 0.31 N·m, čo je viac než moment serva pri zastavení.

## Základňa (B)
* Články 2× 18650 na x = −38 / −58 v držiaku 2S s kľúčovaným konektorom JST-XH, vymeniteľné cez poklop B08
  (nariadenie EÚ 2023/1542, čl. 11, platí od 18. 2. 2027).
* B02: stena 2.2 mm + rebrá 1.2 mm, voliteľne oceľová záťaž 1.5 mm 110×60 (~78 g) pre stabilitu.
* Remeň GT2 16T → 72T pri osovej vzdialenosti 48 mm vychádza na 190.6 mm → motor v drážkach B07 na napnutie.

## Škáry a vôle
* Statické viditeľné škáry: 0.6 mm pri tlači, 0.4 ± 0.1 mm pri vstrekovaní; na oboch hranách zrazenie 0.3×45°.
* Otočné vôle (N07/N06, A04/A05, N02/N01): 0.8 mm pri tlači, 0.6 mm pri vstrekovaní.
* Rám H03 R29.5 → rovnomerná škára 0.3 mm voči H01.

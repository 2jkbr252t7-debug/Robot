# Rozmery elektroniky – stav 2026-11-10

## 0. DOPLNOK: oficiálny rozmerový výkres Waveshare ESP32-S3-Touch-LCD-3.5B (prečítaný 2026-11-10)
Zdroj: https://www.waveshare.com/esp32-s3-touch-lcd-3.5b.htm (obrázky „outline dimensions“, details-size-1 = doska bez
krytu, details-size = verzia -C s krytom), wiki https://www.waveshare.com/wiki/ESP32-S3-Touch-LCD-3.5B

Doska BEZ krytu (3.5B):
- krycie (dotykové) sklo 92,44 × 61,00 mm, rohy R6,00, hrúbka 1,10
- aktívna plocha 73,44 × 48,96, v strede skla (okraj 9,50 vľavo/vpravo, 6,02 hore/dole)
- hrúbka: sklo → zadná strana DPS 7,50; celkom po vrch kolíkovej lišty 11,50
- upevnenie: 4× M2 (závit, mosadzné stĺpiky na zadnej strane), rozstup 72,00 × 48,50, v strede (10,22 / 6,25 od okraja skla)
- USB-C na krátkej hrane (20,00 mm široká zóna, 14,23 pod horným otvorom), tlačidlá PWR / RESET / BOOT na dlhej hrane
  (11,00 od otvoru, rozstup 8,50), konektor reproduktora, batérie, čítačka TF, lišta 2×16 pri dolnej hrane
- DPS je menšia než sklo (≈ 79,5 × 55 mm, odčítané z výkresu)

Verzia S KRYTOM (3.5B-C): 95,11 × 63,67 × 14,10 mm, rohy R7,30, otvory na zadnej strane 72,00 × 48,50.

MODEL (kolo 5) počíta s: doska 85,5 × 55,5 (obrys 86 × 56 R2), otvory 79,5 × 49,5, hrúbka LCD 3,0 + DPS 1,4.
→ NESEDÍ. Skutočné sklo sa do hlavy 108 × 77 (N 3,6, stena 2,5) v rohoch nezmestí o 0,9 mm
  (výpočet: fit_display2.py). Stačí N 4,2 (+0,56) alebo hlava 110 × 79 (+0,32); oboje +1,79.
  Sklo zarovno v prednej ploche: hlava 110 × 79, N 5,0, predný faktor 0,90 → okraj 1,2 mm okolo skla.

# Rozmery elektroniky – zdroje a poznámky (2026-11-09)

Kódy: **S** = uvedené zdrojom, **D** = odčítané z výkresu, **E** = odhad/odvodené, **U** = nenájdené.
Obmedzenie: v tejto relácii fungovalo iba web-vyhľadávanie (snippety) a klon GitHubu; priame načítanie
waveshare.com / docs.waveshare.com / manuals.plus / PDF datasheetov bolo blokované sieťovou politikou.
Oficiálny rozmerový výkres Waveshare teda NEBOL prečítaný – rozmery dosky sú z textových kópií.

## 1. Waveshare ESP32-S3-Touch-LCD-3.5B
Varianty: **3.5** (SKU 30733, ST7796 SPI + FT6336, bez audia) / **3.5B** (SKU 31137, AXS15231B QSPI,
AXP2101, ES8311 + mikrofón + reproduktor, TCA9554) / **3.5B-C** (= 3.5B + kryt + OV5640). „3.5C“ ako
samostatná doska neexistuje; „-C“ je len verzia s krytom a kamerou.
- Obrys dosky 92.44 × 61.00 mm, „board only“ [S] – manuals.plus (kópia Waveshare výkresu)
  https://manuals.plus/asin/B0FB2L8V8S ; zhoda s Waveshare modulom 3.5" cap-touch 61.00 × 92.44
  https://www.waveshare.com/3.5inch-Capacitive-Touch-LCD.htm . Protichodný údaj 85.5 × 55.5 (Cirkit
  Designer, nízka dôvera) https://docs.cirkitdesigner.com/component/03426dfb-6b1c-4041-980e-636bc88b5447/esp32-s3-touch-lcd-35b
- Aktívna plocha 48.96 × 73.44 mm, pixel 0.153 mm [S pre Waveshare 3.5" 320×480 modul; E pre 3.5B]
  (AXS15231B modul JC3248W535: 73.4 × 49.0 [S]) https://cdn.static.spotpear.com/uploads/picture/learn/ESP32/esp32-s3-touch-3.5/JC3248W535-Specifications-EN.pdf
- Hrúbka: 11.50 mm uvádza predajca pre NE-B dosku 3.5 [S]; Elecrow porovnateľná doska stack LCD 2.20 +
  lepidlo 0.50 + PCB 1.60, celkom 10.0 [S] https://www.elecrow.com/download/product/DLE06235B/3.5inch_ESP32-S3_Size.pdf ;
  lcdwiki 3.5" ESP32-S3: LCD 54.5 × 83.0 × 3.2, TP 1.0 [S] https://www.lcdwiki.com/3.5inch_ESP32-S3_Display
  → sklo→zadná strana PCB 5–6 mm [E], celkom s konektormi 11–12.5 mm [E].
- Konektory (zo schémy V2, GitHub waveshareteam/ESP32-S3-Touch-LCD-3.5B, hardware/schematic/…V2-Schematic.pdf) [S]:
  USB Type-C 16P; TF-07F microSD; 2× PH1.25-2P (batéria 3.7 V MX1.25, reproduktor); FPC 0.5 mm 24-pin kamera
  (OV2640/OV5640); FPC 0.5 mm 40-pin výklopný 2.0 mm (LCD); tlačidlá BOOT, RST, PWR(PWRON→AXP2101);
  anténa na doske + U.FL/IPEX footprint. Polohy na hranách dosky: **U** (len z fotiek: USB-C na krátkej hrane).
- Montážne otvory: **U** – v textových zdrojoch nie sú; treba odčítať z výkresu Waveshare alebo zmerať.
- Hmotnosť ~70 g (Cirkit; predajca 0.07 kg pre -C; balenie 82 g pre 3.5) [S, nízka dôvera].
  GitHub README: https://github.com/waveshareteam/ESP32-S3-Touch-LCD-3.5B ; wiki (neprečítané):
  https://docs.waveshare.com/ESP32-S3-Touch-LCD-3.5B ; obchod: https://www.waveshare.com/esp32-s3-touch-lcd-3.5b.htm

## 2. Servo MG90S
Výkres používateľa (/tmp/claude-0/gapwf/fin/ref_MG90S_rozmery_od_pouzivatela.png, Makers Electronics):
22.4 × 12 = telo; 31.8 = cez úchyty; 27.7 = rozstup dier; **24 = výška od dna po rovinu úchytov/vrch tela**;
**32 = výška od dna po VRCH NASADENEJ PÁKY** (kóta končí na páke, nie na drážkovaní). Výkres nie je vo vertikále
v mierke (24 mm meria ~22 mm pri horizontálnej mierke) – datasheety udávajú výšku tela 22.7–22.8.
- TowerPro: 22.8 × 12.2 × 28.5 mm, 13.4 g, 1.8 kg·cm @4.8 V / 2.2 @6 V, 0.10/0.08 s [S]
  https://www.servodatabase.com/servo/towerpro/mg90s , https://www.readymaderc.com/products/details/86506-towerpro-mg90s-metal-gear-servo-90-degree-rotation
- Waveshare WS-MG90S (15024): 22.8 × 12.2 × 28.5, **12.2 g**, 2.0/2.8 kg·cm, 0.11/0.09 s [S]
  https://www.pishop.us/product/mg90s-micro-servo-metal-gear/ (oficiálna wiki stránka WS-MG90S nenájdená)
- Hobby Components kóty: A 32.5 (cez úchyty), B 22.8 (telo), C 28.4 (po vrch drážkovania), D 12.4 (šírka),
  E 32.1 (po vrch páky), F 18.5 (rovina úchytov) [S; význam písmen E] https://forum.hobbycomponents.com/viewtopic.php?p=5079
- Klony: 22.2 × 11.8 × 31 (SG90 štýl), 22.4 × 12.1 × 22.8 (tinytronics sheet, 13.5 g ±5 %), 22.5 × 12 × 35.5 (s pákou)
  https://www.tinytronics.nl/product_files/000263_Data_Sheet_of_MG90S_Analog_Servo_Motor.pdf
- Diery Ø2.0 (M2) / 2.2, hrúbka úchytu 2.5, rozstup 32 (vonkajšie) [S] https://microservomotor.com/common-specifications-and-parameters/micro-servo-mounting-pattern.htm ,
  https://www.auselectronicsdirect.com.au/assets/brochures/TA0132.pdf (SG90: 22.7 × 12.1 × 27.1, 2× Ø2.2)
- Drážkovanie: 21T, Ø4.80, skrutka 2.5, výška náboja páky 4.0 [S] https://makerworld.com/es/models/3193033-fully-parametric-mg90s-servo-horns ;
  niektoré kusy 20T Ø4.9 (Adafruit fórum, GrabCAD) https://forums.adafruit.com/viewtopic.php?t=95879 ; DSSERVO klon 25T.
- Kábel ~24–25 cm, JR 3-pin [S] https://protosupplies.com/product/servo-motor-micro-mg90s/ ; výstup kábla na čele
  pri výstupnom hriadeli v dolnej tretine (z fotky/výkresu) [D/E]; veľkosť priechodky, Ø náboja a 2. výstupku: **E**.
- Rozdiely TowerPro vs. klony: rovnaké rozmery/hmotnosť, nižší moment [S] https://vorpalrobotics.com/wiki/index.php/Tower_Pro_MG90S_Vs._Clones

## 3. Ložisko MR85ZZ, LED 1515, vodič AWG30
- MR85ZZ 5 × 8 × 2.5, skosenie min 0.1, 9 guľôčok Ø0.8, 0.34 g, Cr 305 N (NSK) / 278 N (Misumi) [S]
  https://www.oss.nsk.com/mr85zzmc3-apn.html , https://my.misumi-ec.com/vona2/detail/221000531116/ , https://www.lily-bearing.com/products/mr85zz/
- SK6805-EC15: 1.5 × 1.5 mm, 4 pady, 3.7–5.5 V [S] https://www.lcsc.com/product-detail/C2890035.html ; výška 0.65
  (EC15 list) https://www.slideshare.net/slideshow/ec15-15x15mm-sk6812-pixel-led/123394073 / 0.7 (SK9814-EC15) → 0.65–0.7 [S/E];
  datasheet (neprečítaný): https://datasheet.lcsc.com/lcsc/2108251530_OPSCO-Optoelectronics-SK6805-EC15_C2890035.pdf
- AWG30 silikón OD 0.8 [S] https://adafruit.com/products/2051 , https://www.electrokit.com/en/kopplingstrad-awg30-silikon-15m-gul ;
  PTFE 0.61 (Alpha 2841/7) – 0.81 (Alpha 5851, RS PRO 7/0.102) [S] https://uk.rs-online.com/web/p/hookup-equipment-wire/1770621 ;
  PVC 1007 ~1.1 [S].

## Čo zostáva neisté (treba výkres Waveshare alebo meranie)
1. 3.5B: presné polohy a priemery montážnych otvorov; poloha USB-C, TF, PH1.25, tlačidiel na hranách; hrúbka skla a
   celková hrúbka; offset aktívnej plochy; hmotnosť. 2. MG90S: výška roviny úchytov (18.5 vs 21), Ø/výška 2. výstupku,
   Ø náboja páky, rozmer priechodky kábla – všetko E. 3. SK6805-EC15 výška (0.65 vs 0.7). 4. Hrúbka PCB 3.5B (1.6 E).

# NOVA mini – verzia B: ako model sedí so skutočnými dielmi a návrhy zmien (2026-11-10)

Stav modelu: kolo 5 (`zdroj_B_kolo5.zip`). Nič z nižšie uvedeného ešte NIE JE zapracované – sú to návrhy na výber.

## 1. Servo MG90S – porovnanie s obrázkom od používateľa
Obrázok: `MG90S_porovnanie_s_modelom.png` (čierne = výkres používateľa, červené = servo v modeli, rovnaká mierka).

| Rozmer | Obrázok | Model | Stav |
|---|---|---|---|
| šírka tela | 12 | 12,2 | sedí |
| dĺžka tela | 22,4 | 22,8 | sedí (vôľa 0,4) |
| cez úchyty / rozstup dier | 31,8 / 27,7 | 32,5 / 27,75 | sedí |
| dno → vrch veže | 28,0 (odmerané z výkresu) | 28,5 | sedí |
| dno → vrch páky | 32 | 32,1 | sedí |
| dno → vrch tela | kóta „24“, nakreslené 22,6 | 22,5 (rezerva len 0,15) | tesné – zmerať |
| výška úchytu od dna | výkres 19,7–22 (fotka skôr ~16–18,5) | 15,5–18 (berie 15,2–18,8) | neisté – zmerať |
| 2. výstupok vedľa hriadeľa | vysoký ako veža (≈ 5,5 mm) | 1,2 mm | **NESEDÍ** |
| výstup kábla | koniec pri hriadeli, pri dne | opačný koniec | **NESEDÍ** |

Záver: obrys sedí na ≈ 0,5 mm, ale pre dva detaily by skutočné servo do kapsy v krku teraz nesadlo.

## 2. Displej Waveshare ESP32-S3-Touch-LCD-3.5B – porovnanie s oficiálnym výkresom
| Rozmer | Oficiálny výkres | Model | Stav |
|---|---|---|---|
| obrys (sklo) | 92,44 × 61,00, R6 | 85,5 × 55,5 (86 × 56 R2) | **NESEDÍ** |
| upevňovacie otvory | 4× M2 závit, 72,0 × 48,5 | 79,5 × 49,5 (odhad) | **NESEDÍ** |
| hrúbka | sklo 1,1; po DPS 7,5; celkom 11,5 | 4,6 + rezerva 9 (spolu 13,6) | hĺbka stačí |
| aktívna plocha | 73,44 × 48,96 v strede | 73,44 × 48,96 | sedí |

Skutočné sklo sa do hlavy 108 × 77 v rohoch nezmestí o 0,9 mm. Podrobnosti: `rozmery_elektroniky.md`.

## 3. Návrhy
### A – servo v krku (opravy, bez nich diel nepasuje)
- A1. Vybranie pre 2. výstupok prehĺbiť z 1,4 na ≈ 5,8 mm (tvar „kľúčová dierka“ spolu s vežou).
- A2. Kábel serva viesť od konca pri hriadeli:
  - (a) hore cez vrch kĺbu rovno do hlavy (štrbina v dne hlavy 4 × ~17 mm), servo zapojiť na lištu dosky displeja – odporúčané;
  - (b) dole drážkou v bočnej stene krku (nad ohybom kábla ostáva len ≈ 0,7 mm materiálu – treba overiť).
- A3. Rezervy: kapsa +0,5 mm v osi hriadeľa s penovou podložkou; kryt uška tolerantný na výšku páky ±1 mm
  (teraz okno 0,7 mm, náboj páky 4,2 mm koliduje); úchyt – širšia drážka alebo odrezať oba úchyty.
- A4. Kanál pre 4 vodiče do hlavy: Ø1,6 → drážka 1,6 × 3,0 mm.

### B – displej a predok hlavy
- B1. Kapsa, otvory a hrúbka displeja podľa oficiálneho výkresu; displej priskrutkovať 4× M2 zozadu.
- B2. Hlava: buď hranatejšie rohy pri pohľade spredu (N 3,6 → 4,2), alebo 110 × 79 mm.
- B3. Dotyk:
  - (a) sklo displeja zarovno v čiernom prednom diele = tvár robota, dotyk funguje, žiadna páska ani magnety – odporúčané
    (hlava ≈ 110 × 79, okraj 1,2 mm okolo skla);
  - (b) displej za tenkým okienkom ≤ 1 mm;
  - (c) hrubé predné sklo ako teraz, bez dotyku.

### C – hladký povrch podľa R01 (`B_povrch_spec_E1.md`)
- C1. Predný čierny diel zarovno so škrupinou (teraz vystupuje 5 mm so schodíkom 1 mm).
- C2. Rovnaké zaoblenie predku hore, dole aj po stranách.
- C3. Uši ako klenuté puzdrá so zapusteným svetelným krúžkom.
- C4. Spodok hlavy bez zásteriek; ušká pántu ako valček s plynulým prechodom; škára 0,3.
- C5. Krk: rohy R3, plynulé sedlo namiesto 35° plôšky, deliaca čiara ako jemná V-drážka.
- C6. Golier: jemnejšie škáry.

### D – mechanizmus (`B_mechanizmus_posudok.md`)
- D1. Zdvih krku kľukou zo serva MG90S v trupe (v oboch koncových polohách drží bez prúdu).
- D2. Firmvér: bežná poloha krk vysunutý 12,5 mm (ako R01), náklon −40° až +30° bez plného zdvihu.
- D3. Axiálna vôľa hlavy 0,25 mm → klzný krúžok PTFE 0,25.

## 4. Čo zmerať na skutočnom serve (posuvné meradlo)
1. dno → vrch tela; 2. výška veže a 2. výstupku nad telom; 3. dno → spodná hrana úchytu a hrúbka úchytu;
4. výška náboja páky; 5. na ktorom konci a ako vysoko vychádza kábel.

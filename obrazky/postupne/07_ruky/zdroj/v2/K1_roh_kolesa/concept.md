# K1 – servo v rohu trupu + čelné ozubené kolesá (ľavá ruka) – výsledok: NEDÁ SA

Pracovný adresár: `/tmp/claude-0/gapwf/fin/R1/K1_roh_kolesa` (všetky čísla nižšie sú z tunajších skriptov; T4, B a T3 som nemenil).
Prehľadový obrázok: `img/K1_prehlad.png`.

## 1. Prečo nejde priamy pohon (servo priamo na osi ramena, bez kolies)
* Pozdĺž osi ramena je medzi stĺpom a rukou len **16,2 mm**: stĺp začína na x 34,4 (to je 1,0 mm od servo zdvihu krku,
  ktoré sa s hlavou otáča ±90°) a vnútorná stena ruky je na osi na x 50,64.
* SCS0009 potrebuje pozdĺž hriadeľa **21,5 mm telo + ~3,75 mm výstup** (25,25 podľa výrobcu vrátane hriadeľa).
* Výsledok (meranie R1 `layout_a.json`, prevzaté, overené proti 17.16-9 špecifikácie: vnútorná plocha stĺpa r 34,4 = PAN_ENV2 + 1,0):
  čelo serva by bolo na x 55,9, teda **9,1 mm mimo trupu** (povrch 46,76) a ruka by sa musela odsunúť o **8,1 mm**
  (o 11,9 mm, ak je samotné telo 25,25). MG90S 9,3 mm, STS3032 9,6 mm. Krídlové KST X06 (16,6 mm) by stále chcelo 3,2 mm
  a má len 120°. Priamy pohon teda nejde bez odsunutia ruky – presne to, čo nechceš.

## 2. Čo K1 potrebuje a prečo to nejde
Čelné kolesá potrebujú hriadeľ serva **rovnobežný s osou ramena (X)**, takže 21,5 mm telo serva leží pozdĺž X.
Pre K1 som z trupu „vymazal" všetko, čo sa smie meniť: celý stĺp nad z −78 (stena, rebrá, hlava, ramenná doska, uzáver),
kĺb T_klb_L so skrutkami a vložkami, vnútro bočného krytu okolo ramena (pätka, príruba), zosilňovač, F14, F3a_2.
Ostali: steny trupu (vnútorná plocha + 0,3), servo J1 a jeho kolíska, servo otáčania hlavy (pastorok musí ostať pri
azimute 254,3 ± ~5°, inak zasiahne kryt FFC na šachte – spec 17.2.3), doska riadenia, paluba, predný blok, a pohyb hlavy (+1,0).

| test | výsledok |
|---|---|
| FFT erózia, holé telo 23,2 × 12,1 × 21,5, hriadeľ ‖ X, 24 natočení (`k1_fit.py … c 21.5`) | **0 polôh** (ľavá aj pravá strana) |
| to isté + servo otáčania hlavy odstránené (`…_p`) | 0 polôh |
| + aj doska riadenia, USB, kondenzátor, okraj paluby odstránené (`…_pcd`) | 2 polohy vzadu v strede, výstup na x 19,75 (v zóne otáčania krku – na os ramena sa odtiaľ kolesami nedostať), hriadeľ 47,5 / 57,6 mm od osi |
| 4-DOF optimalizácia so znamienkovou vzdialenosťou (`k1_opt.py scs`) | najlepšie **chýba 1,6 mm** (dole pri J1, os 45,7–56 mm ďaleko); v prednom rohu **chýba 2,1 mm** (os 47,8 mm ďaleko) |
| ľubovoľné osové natočenie + 45° (`k1_anyfit.py`) | jediná poloha: **servo nastojato** (hriadeľ ‖ Z) pod ramenom, x 32–44, y −19…4, z −72…−50 – to nie sú čelné kolesá |
| KST X06 (20 × 7 × 16,6), hriadeľ ‖ X + pastorok r 6,5 | len pri dne (z −70,75), **53,8 mm** od osi; alebo s rovinou kolies x ≥ 45, kde sa na os zmestí koleso r ≤ 4,1 |
| vlak 3 kolies pre KST (prevod do rýchla 1,5, `k1_train.py`) | **žiadne riešenie**; s prevodom 0,65 treba medzikoleso 75–76 z (Ø 39) |
| rovina kolies x 39,5…42,5 (`k1_plane.py`) | najväčšie koleso na osi: hlavová kružnica **r 10,6** |

Prečo: v prednom ľavom rohu je pozdĺž X na prednej strane serva (y −27,5) miesto len od serva otáčania hlavy (x 18,75)
po zaoblenú stenu (x ≈ 37,5) = **18,5 mm** proti potrebným 21,5 + 0,6. Pri ramene samotnom je medzi otáčajúcim sa krkom
(r 33,4 + 1) a stenou len 10–13 mm. Všade, kam sa servo dá dostať, je hriadeľ **40–58 mm** od osi ramena – a koleso na
osi môže mať najviac r 10,6. Takú vzdialenosť premostí len pastorok + medzikoleso Ø 30–40 mm + koleso na osi, alebo 4 kolesá.
To je hlučný viackolesový mechanizmus, ktorý nechceš – a servo sa tam ani tak nezmestí.

## 3. Čo z merania platí pre každý koncept so servom v trupe (pasívna ruka)
* **Ruka bližšie k trupu** (`k1_arm.py`, ruka otočená −45…+135° voči vonkajšiemu povrchu T_bok_L a T_stred, kĺb sa nepočíta):

  | posun ruky dx | medzera v pokoji | minimum v celom rozsahu | rozsah s vôľou ≥ 1,0 |
  |---|---|---|---|
  | 0 (schválené) | 4,67 | 1,90 pri +135° | celý |
  | −0,5 | 4,19 | 1,45 | celý |
  | **−1,0** | **3,70** | **1,00 pri +135°** | **celý** |
  | −1,5 | 3,22 | 0,56 | do +121° |
  | −2,0 | 2,73 | 0,13 | do +112° (s 0,5 do +123°) |
  | −2,5 | 2,25 | −0,30 | do +103° |

  Odporúčanie: dx = −1,0 (medzera 3,7 mm, celý rozsah); ďalší milimeter stojí ~10–15° rozsahu hore.
* Jediné miesto pre SCS0009 v ľavej polovici po presune stĺpa a zosilňovača: **nastojato pod ramenom** (stred telesa
  x 38,2…41,2, y −7,2…7,2, z −66…−55; hriadeľ môže byť priamo pod osou y 3, vrch serva z −44 → 27 mm pod osou).
  Hodí sa pre koncept s jedným kužeľovým párom alebo remeňom/lankom (iná stratégia, nie K1). S 1,2 mm stenou puzdra okolo
  serva už nevychádza → servo by sa držalo za uši / vrch, nie v uzavretej krabici. Neoverené presnou geometriou.

## 4. Záver
K1 v zadanej podobe (servo v rohu + 2–3 čelné kolesá k osi) sa do trupu nedá: servo SCS0009 s hriadeľom rovnobežným s osou
ramena sa nezmestí nikde (chýba najmenej 1,6 mm aj po odstránení stĺpa, kĺbu a zosilňovača) a aj najbližšie polohy sú
40–58 mm od osi, čo by vyžadovalo veľké medzikoleso alebo 4 kolesá. Odporúčam K1 vyradiť.

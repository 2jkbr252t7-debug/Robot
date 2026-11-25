# K3 – preusporiadanie vnútra trupu: servo v trupe + jeden kužeľový pár (ľavé rameno, pravé zrkadlovo)

Výsledok: **USKUTOČNITEĽNÉ** (overené bodovými mrakmi proti skutočným STL T4/B a pohybu krku ±90,3° / zdvih 0–20).
Priamy pohon (hriadeľ serva = os ramena) **nejde** – čísla v §1. Najjednoduchší spoľahlivý pohon, ktorý sa zmestí:
servo SCS0009 stojí v trupe pod ramenom, hore ide tenký hriadeľ Ø3 a **jeden** kužeľový pár m0,5 16/24 z otáča rukou.
Modul otáčania hlavy, modul zdvihu, krk a hlava ostávajú **bez zmeny** (žiadna nová pevnostná analýza tam).
Obrázok: `img/K3_rez_rameno.png`. Skripty a výsledky sú v tomto adresári (zoznam v §10).

## 1. Prečo nie priamy pohon (meranie)
* Na osi ramena (y 3, z −17) je vonkajší povrch trupu na x 46,76, vnútorná plocha steny 44,5.
* Najbližší otáčajúci sa diel pri ľavom ramene: roh serva zdvihu MG90S r 33,38 (z −42…−18, pri natočení hlavy −57°),
  pri pravom r 33,0 (P_drziak_serva). S vôľou 1,0 musí všetko pevné začínať na x ≥ 34,3 (vpravo −33,9).
  (`envparts.py`, `verify_exact.py`).
* Voľná dĺžka pozdĺž osi: 46,76 − 34,3 = **12,5 mm** po povrch (10,3 po vnútornú stenu).
* SCS0009 potrebuje pozdĺž hriadeľa ≥ 21,5 mm telo (neoverené; výrobca 25,25 vrátane hriadeľa) + 3,75 drážkovanie
  → čelo serva by bolo 9 mm mimo trupu. MG90S / STS3032 ešte viac. Najtenšie krídlové KST X06 (16,6 vrátane hriadeľa,
  len 120°, PWM bez spätnej väzby) by trčalo 4,1 mm.
* Ani úplné odstránenie modulu zdvihu by nepomohlo: zostáva otáčajúca sa šachta krku r 26,5 (+1,0) → 19,3 mm < 21,5.
  Menší rozsah otáčania hlavy nepomôže z rovnakého dôvodu. Presun modulu zdvihu teda nie je rozhodujúci zisk.
* Servo „dlhou stranou zvisle v stĺpe“ alebo „nižšie/tenšie“: pozdĺž osi vždy ostáva výška tela (≥ 21,5); najtenší rozmer
  12,1 pozdĺž osi znamená hriadeľ kolmo na os ramena → treba prevod o 90° (= tento koncept). Ani tak sa servo nezmestí
  priamo pod rameno (12,1 > 10,3 a stena sa pri y −14 zatáča na x 44,8), preto stojí nižšie (z −66,5…−45), kde je trup
  širší a otáčajúce sa diely menšie, a k ramenu ide hriadeľ Ø3.
* Remeň / lanko spájajú len rovnobežné hriadele → servo by muselo ležať hriadeľom pozdĺž X; K1/K2 ukázali, že také servo
  sa do trupu nezmestí (chýba 1,6–5,7 mm). Lanko s pootočením o 90° nie je spoľahlivé.

## 2. Servo a jeho poloha (ľavá strana, rám B; pravá = zrkadlo x → −x, overená zvlášť)
* Feetech **SCS0009** (zbernica ako servo otáčania hlavy, poloha + záťaž, 300°, kovové kolesá, 0,19 N·m pri 5 V).
* Stojí, hriadeľ hore, os hriadeľa **x 39,0, y 3,0** (zvislá priamka pretína os ramena v bode O = (39, 3, −17)).
* Telo otočené tak, že leží dopredu (θ 270°): x 32,95…45,05, y −14,3…8,9, z −66,5…−45,0; nákružok z −45…−44,
  drážkovanie do −40,25. Uši (rozmer neoverený: rozpätie 32,3, hrúbka 2,5, 4,3–6,8 pod vrchom) z −51,8…−49,3 na
  policiach nového stĺpa (vzadu y 8,9…13,45, vpredu y −18,85…−14,3), M2, otvory oválne ±0,3 (zarovnanie na hriadeľ).
* Vôle (presne, `verify_exact.py`): k pohybu krku/zdvihu **1,05** vľavo / **1,35** vpravo; k stene T_bok 0,53;
  k T_paluba (po orezaní) 1,96, k T_spodok 1,88; k dráhe spúšťania T_stred ≥ 0,5 (servo nie je v ceste T_stred).
* Výška tela 21,5 aj 25,25 sa zmestí (`fit_vert2.py`: vľavo 25,25 s ušami ešte rezerva 0,6/1,9; vpravo tesné 0,06/0,05
  v mriežke – presná kontrola s 21,5 dala 1,35 k pohybu).

## 3. Prevod – jeden kužeľový pár
| diel | údaje |
|---|---|
| pastorok (zvislý) | priamy kužeľový, m 0,5, **16 z**, d 8,0, šírka 2,4, δ 33,7°, bez náboja, lepený (Loctite 638) na hriadeľ Ø3; päta z −23,0, špička z −20,8; x 34,58…43,42 |
| koleso (na hriadeli ruky) | m 0,5, **24 z**, d 12,0, δ 56,3°, zuby smerom dnu (−X); päta x 43,0, chrbát x 44,02, r ≤ 6,28; lepené/kolík na hriadeli Ø4 |
| prevod | 1,5 : 1 (servo 300° → ruka 200°; treba 180° = −45…+135; 10° rezerva na každú stranu); rozlíšenie 0,195° |
| materiál | **mosadz** (alebo oceľový pastorok + mosadzné koleso), mazané – pri ≤ 2 ot/s tiché; POM len ak spojka ≤ 0,04 N·m |
| vôľa v zuboch | nastavená podložkami: pastorok podložkou 0,5 (+0,05/0,1) nad ložiskom B1, koleso podložkami pod prírubou zátky |
| vôľa na ruke | ~0,5–0,8° (pár) + vôľa serva |

## 4. Hriadele a ložiská
* **Zvislý hriadeľ** Ø3 oceľ (h6, plôška D na spodku), z −41 … −20,8 (dĺžka 20,2). Hore ložisko **B1 = MR63ZZ**
  (3×6×2,5) z −26,35…−23,85 v jazýčku stĺpa (T_spodok), vonkajší krúžok na osadení Ø5 dole (tlak pastorka ide nadol).
  Dole spojka na drážkovaní serva: guľatá páka serva zrezaná na Ø8 + mosadzné/živicové puzdro s otvorom D pre hriadeľ,
  M2 skrutka do strany (alebo lepené). Spojka r 4,0, z −44…−37.
* **Hriadeľ ruky** Ø4 oceľ, x 41,39 … 61,5 (koniec so závitom M2). Ložiská **A1, A2 = MR74ZZ** (4×7×2,5) na x 44,55…47,05 a
  48,55…51,05 v novej čiernej zátke (T_klb nový) – mechanizmus drží záber aj bez ruky.
* Axiálne sily kužeľov idú vždy od vrcholu: pastorok tlačí nadol cez podložku na vnútorný krúžok MR63, koleso tlačí
  von (+X) cez podložky na vnútorný krúžok A1 → montážne vzdialenosti oboch kolies sa nastavia len podložkami
  (0,05 / 0,1 / 0,5). Poistný krúžok Ø4 za A2 drží hriadeľ ruky proti zatlačeniu dnu.
* Súosovosť: zátka sa vystredí krátkym C-osadením (r 8,25, x 37,6…38,6, 300°) v otvore náboja stĺpa r 8,3 – os kolesa aj
  os pastorka (MR63 v jazýčku) sú tak určené tým istým dielom T_spodok; natočenie zátky dá kolík / rozostup skrutiek.
* **Ruka nesie čierny krúžok, nie hriadeľ:** krúžok zátky Ø13 siaha do ruky; na jeho konci (Ø10, x 54…58 pri dx 0) je
  **ložisko 6700ZZ** (10×15×4) v náboji ruky. Ruka visí na krúžku, hriadeľ ruky prenáša len krútiaci moment cez spojku.

## 5. Spojka a ochrana
* Trecia spojka v náboji ruky na konci hriadeľa: oceľová podložka na plôške hriadeľa | mosadzná príruba náboja ruky |
  oceľová podložka | tanierová pružina | podložka | skrutka M2 do čela hriadeľa. 2 trecie plochy, r_stred 3,6, μ ≈ 0,12
  (mierne mazané) → predpätie ≈ 69 N pre **0,06 N·m** (1,2 N na 50 mm). Nastavenie podložkami, kontrola siloměrom
  1,0–1,4 N na 50 mm.
* Spojka obmedzuje aj krútiaci moment v ozubení (servo pri zablokovanej ruke): zuby vidia ≤ 0,06 N·m (Lewis 38 / 30 MPa).
  Hodnota 0,1–0,15 N·m z podkladov by malé m0,5 zuby preťažila (63–95 MPa) – preto 0,06 (ruka potrebuje 0,004).
* Firmvér: limit krútiaceho momentu serva ≤ 30 %, teplota 65 °C, rozsah ruky −45…+130 (pri dx −1,0) / +135 (dx −0,5).

## 6. Ruka – uchytenie, odstránenie, medzera
* Pasívna biela škrupina bez elektroniky. Vnútorná škrupina má otvor r 7,0 okolo krúžku (šev 0,5, stále rovnaký – krúžok
  je súosový), náboj s 6700 a spojkou; vonkajší kryt ruky na magnetoch (ako v1). Ruka sa zloží: kryt dole → skrutka M2 →
  podložky + pružina → ruku stiahnuť z krúžku.
* Viditeľné: čierny kotúč zátky v pôvodnom otvore krytu r 14 (ako schválený T4), **zapustený 1,0 mm** pod plochu, a
  **čierny krúžok Ø13** cez medzeru. Nič iné.
* Medzera ruka–trup (`armgap_k3.py`, celý povrch trupu, ruka −45…+135):

  | dx | v pokoji | minimum (pri +135°) | rozsah s vôľou ≥ 1,0 |
  |---|---|---|---|
  | 0 (schválené) | 4,63 | 1,78 | celý |
  | −0,5 | 4,14 | 1,32 | celý |
  | **−1,0 (odporúčané)** | **3,66** | **0,86** | do +130° |
  | −1,5 | 3,18 | 0,41 | do +115° |
  (zátka zarovno s plochou namiesto zapustenia: dx 0 → 3,78 / 1,45; dx −1,0 → 2,80 / 0,47.)

## 7. Spätná väzba, homing, kábel
* SCS0009 hlási absolútnu polohu (0–1023 na 300°), záťaž, teplotu. Po zapnutí (a keď záťaž počas pohybu naznačí náraz):
  homing – limit momentu 15 % (0,043 N·m na ruke < spojka 0,06), pomaly k dorazu −50° (výstupok v náboji ruky na kolík
  na konci krúžku, skryté v ruke), zastavenie podľa záťaže → nový ofset. Spojka pri homingu neprekĺzne.
* Kábel serva je **pevný v trupe** (nič neprechádza kĺbom): od predného spodného rohu serva po stĺpe dole a po kolíske
  J1 k rozbočke J_BUS_5 na nosnej doske, ~100–130 mm, príchytky na stĺpe.

## 8. Zmeny v trupe (všetko vnútri; vonkajšok a švy bez zmeny)
| diel | zmena | tlačiť znova |
|---|---|---|
| T_spodok | oba stĺpy nahradené: náboj r 8,3…12,8, x ±34,4…38,4 (+ dorazový krúžok ako T4) s jazýčkom pre MR63 (Ø6, osadenie Ø5, otvor Ø4 pre hriadeľ), 3 vložky M2 na r 10,2 pre zátku; zadná noha y 9,5…15,5, predný stĺpik y −21…−14,6, police pre uši serva (z −51,8), vzpera k náboju; podložka meniča pod ľavým servom; zrušené: stena/rebrá/uzáver stĺpa, nálitky F14; F3a_2 (30,6; 4,0) presunúť ≈ (23,0; 11,5) do steny kolísky/stĺpika kolíka 1 | áno |
| T_paluba | okraj orezať na x ≤ 31 (ľavý lalok), otvor F3a_2 presunúť | áno |
| T_bok_L / T_bok_P | zárez vo vnútornom konci objímky a v sedle (x ±37,0…41,0, y 1…5, z −34…−28) pre zvislý hriadeľ – otvorený smerom k stredu, kryt sa nasúva cez hriadeľ | áno |
| T_klb_L / T_klb_P | nahradené novou čiernou zátkou-kazetou: rovnaký obrys v otvore ako T4 (krk r 11,0 x 38,6…40,6, telo r 13,5), čelo zapustené 1,0, dutina r 6,8 pre koleso, výrez na 6 hod. pre pastorok a jazýček, sedlá 2× MR74, krúžok Ø13 → Ø10 sedlo 6700, 3× M2 zápustné z čela | nový diel |
| zosilňovač | z ľavého stĺpa preč: ideálne integrovať MAX98357A na nosnú dosku; inak modul na zadnú stranu nosnej dosky (miesto overené x −9,7…9,7, y 25,8…30,3, z −71,9…−54,1, prístup dvierkami) | – |
| menič (Pololu) | z pravého stĺpa naležato pod ľavé servo na dno (miesto overené: stred x 28–29,5, y −3…0, z −76…−73; 17,8 × 17,8 × 10,3) | – |
| T_stred, T_dvere, otáčanie hlavy, zdvih, krk, hlava | **bez zmeny** | nie |

## 9. Montáž a servis
1. Lavica: MR63 zalepiť do jazýčka (zhora). Pastorok nalepiť na hriadeľ Ø3 v prípravku. Zátku-kazetu zložiť:
   2× MR74, hriadeľ ruky s kolesom (koleso nalepené/kolík na meranú montážnu vzdialenosť).
2. Trup s odkrytým bokom (T13 ešte nie): servo zboku na police, skrutky voľne; spojka na drážkovanie.
3. Hriadeľ + podložka 0,5 + pastorok zhora cez MR63 do spojky; zaistiť spojku; dotiahnuť servo pri otáčaní hriadeľom
   (servo sa samo vystredí podľa ložiska). Kábel k J_BUS_5.
4. T_bok_L nasunúť (zárez prejde cez hriadeľ). Zátku-kazetu zasunúť zvonka (−X), koleso zapadne do pastorka; 3× M2
   (zátka zároveň pritlačí sedlo krytu ako T4). Vôľu v zuboch nastaviť podložkami pod prírubou.
5. Ruka: 6700 v náboji, nasunúť na krúžok, spojka, skrutka M2, kryt ruky.
* **Výmena serva:** kryt ruky → skrutka → ruka dole → 3 skrutky zátky → kazeta von → kryt T_bok dole (+X) → povoliť
  spojku, nadvihnúť hriadeľ s pastorkom o 5 mm → 2 skrutky uší → servo zboku von. Krk, hlava, T_stred, modul otáčania
  ani zdvih sa nerozoberajú (≈ 10 min).

## 10. Overenie (čísla) a súbory
* `k3map.py` → `k3map.npz`: mapa 0,5 mm s odstránenými dielmi, ktoré K3 smie meniť.
* `fit_vert.py`, `fit_vert2.py`, `diag_vert.py`: hľadanie polohy stojaceho serva (os y 3; θ, z, x).
* `movcloud.py` (2,09 mil. bodov pohybu), `verify_exact.py` → `verify_L.json`, `verify_R.json`: presné vôle.
  Vľavo k pohybu: spojka 1,74, pastorok 1,32, B1 2,74, servo 1,05, náboj 1,02 (T4 mal 1,00), jazýček 1,33.
  Vpravo: spojka 2,10, pastorok 1,72, B1 3,10, servo 1,35, náboj 1,39, jazýček 1,71; servo ↔ T_bok_P 0,53,
  ↔ stena kolísky J1 0,75; jazýček ↔ sedlo T_bok_P 0,47.
  Vzájomné: hriadeľ Ø3 ↔ koleso 0,89, pastorok ↔ hriadeľ ruky 1,82, pastorok ↔ náboj 0,59,
  koleso ↔ A1 0,53, ↔ jazýček 0,78, ↔ B1 0,82, pastorok ↔ B1 0,50 (podložka), pastorok ↔ jazýček 0,70.
  K pevným dielom: servo ↔ T_bok 0,53, jazýček ↔ sedlo T_bok 0,47, B1 ↔ T_bok 1,43, koleso ↔ T_bok 5,35;
  **zvislý hriadeľ pretína sedlo/objímku T_bok na 6 hod. → zárez v T_bok (tabuľka §8)**.
* `armgap_k3.py` → `armgap_k3.json`; `strength.py` → `strength.json`; `k3after.py` → `electronics_fit.json`;
  `k3_parts.py` (geometria), `k3_img.py` → `img/K3_rez_rameno.png`.

## 11. Riziká / neoverené
* Rozmery SCS0009 (výška tela, uši, poloha hriadeľa 5,9 od konca) – zmerať kus; pri 25,25 vpravo tesné.
* Dostupnosť kužeľového páru m0,5 16/24 z (náhrada 1:1 16 z s hriadeľom ruky Ø3 – menej miesta nad pastorkom).
* Lepené koleso/pastorok na hladký hriadeľ (alebo kolík Ø1); presnosť montážnej vzdialenosti (podložky).
* Pevnosť nového stĺpa (dve nohy namiesto steny) – ručný odhad 7 MPa pri 10 N, treba FE ako K12 v T4.
* Zátka-kazeta: 3 skrutky M2 nesú ruku aj pritlačenie krytu – ako T4, ale skrutky na r 10,2 (nová poloha vložiek).
* Elektronika: zosilňovač na nosnej doske / za ňou (zatieni časť konektorov?), menič pod servom (teplo pri J1).

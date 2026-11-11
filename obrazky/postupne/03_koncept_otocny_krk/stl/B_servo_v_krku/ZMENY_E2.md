# NOVA mini – variant B – ZMENY v revízii E2 oproti kolu 5 (+ E2f: kábel serva dole do trupu, pozri časť 10)

Mechanizmus ostáva (výsuvný krk 20 mm, servo náklonu MG90S v krku s hriadeľom v osi pántu, MR85 + dutý čap,
náklon ±40°). Mení sa všetko, čo nesedelo so SKUTOČNÝMI dielmi, a celý vonkajší povrch. Stav kola 5 je zmrazený
v `r5/`. Rozmery v mm.

## 1. Displej – skutočné rozmery holej dosky Waveshare ESP32-S3-Touch-LCD-3.5B
| | kolo 5 | E2 | prečo |
|---|---|---|---|
| obrys | doska 85.5 × 55.5 | sklo 92.44 × 61.00 × 1.10, R6 (najväčší obrys) | oficiálny výkres |
| upevnenie | diery ±39.75 / ±24.75, rohové sedlá a rebrá v škrupine | 4 stĺpiky M2 72.00 × 48.50 na zadnej strane dosky | oficiálny výkres |
| hĺbky | LCD 3.0 / doska 1.4 | zadná plocha dosky 7.5, konce stĺpikov 11.5, hlavička 12.5 za prednou plochou skla | bočný pohľad výkresu |
| orientácia | – | hlavička 2×16 dole, USB-C na ľavej strane robota (+X) | podľa výkresu |

## 2. Čelo hlavy – namiesto číreho „skla“ nepriehľadný rám + magnety
- **Preč:** dymové sklo hrubé 5.9 mm (`sklo`), lepiaca páska skla, 4 rohové penové podložky, sedlá a rebrá displeja
  v škrupine. Sklo trčalo 5 mm pred bielu škrupinu, bolo o 1 mm menšie a cez neho bolo vidieť vnútro hlavy.
- **Nové:** `ram_displeja` – čierny nepriehľadný rám, vonkajší tvar je TEN ISTÝ povrch ako hlava (krok 0),
  škára V 0.25 × 0.12 na y = −26. Okno 90.0 × 58.6 (R4.8); tvárou robota je priamo sklo displeja, 2 mm zapustené.
- `pena_displeja` – penový rámik 1.0 × 0.5 pod sklom (stlačený na 0.3).
- `drziak_displeja` – 2 čierne lišty hr. 3.0: 4× M2×5 do stĺpikov displeja + 4× M2×6 do vložiek v 4 stĺpikoch rámu.
- `magnety` – 6 párov N35 Ø4 × 2 (rám / nákružky v škrupine), spolu ~18 N; modul sa vyberá prísavkou, bez náradia
  a bez viditeľných skrutiek.
- Odchýlky od zadania E2 (kvôli stenám ≥ 1.2): lem okna 1.7 (nie 1.5), hrana okna R0.7 (nie R1.0).

## 3. Škrupina hlavy
- 110 × 79 × 66 (bolo 108 × 77), superelipsa N = 5 (bolo 3.6) – hranatejšia „poduška“ ako na cieľovom obrázku.
- Predné zaoblenie ROVNAKÉ v X aj Z (9 hlboké × 7.5), plynule do rovného čela; farebný zlom čierna/biela na y = −26.
- Zadok hlavy (na pripomienku používateľa „vyzerá ako kocka“): profil zboku je plynulý bez skokov v zakrivení –
  od y = −6 dozadu „squircle“ (exponent 3.5) až po malú uzatváraciu plôšku 15 × 11 mm. Zmizol rovný úsek
  hranolu so zlomom zaoblenia na y = 3 aj rovná zadná doska 33 × 23 mm. Predné zaoblenie má exponent 2.4
  (plynulý prechod do boku). Prierezy majú body rovnomerne po dĺžke krivky, prierezy každých 1.2 mm → bez vlnenia.
  Dno hlavy pri pánte sa zdvihlo len o 0.0–0.6 mm.
- Uši: kupolky (valec R13 + guľa R38, R1.5), svetlovodný krúžok v rovine kupoly, hrana otvoru v škrupine R0.8.
- Mostík na kábel serva na podlahe (strana −X), vrch vo výške 9.1. *(E2f: zrušený – kábel serva do hlavy nejde.)*

## 4. Servo MG90S – podľa obrázka a fotiek od používateľa
- Vežička = kľúčová dierka (nákružok r5.9 + lalok r2.9 vo vzdialenosti 5.6, rovnako vysoký) – kolo 5 malo len
  nízky výstupok 1.2.
- Kábel vychádza z čela PRI HRIADELI (kolo 5 ho malo na opačnom konci) → ide HORE do hlavy, nie dole krkom.
  *(E2f: nahradené – servo sa upravuje, vodiče idú cez veko DOLE do trupu, pozri časť 10.)*
- Obe úchytné ušká sa odrežú zarovno → žiadna drážka uška v kapse.
- Kapsa: doraz = vrch puzdra na stene −X, na strane +X je kapsa o 0.75 dlhšia s 2 penovými podložkami 1.0
  (prijme výšku puzdra 22.4–23.0). **Preč:** drážka uška, vybranie druhého výstupku, kanál kábla dole krkom.
- Páka: kryt prijme vrch ramien 8.9–10.3 nad puzdrom bez úprav (otvorený vývrt Ø13.3 v čele kĺbu + dve líca krytu).

## 5. Kábel serva do hlavy *(E2 – v E2f ZRUŠENÉ, pozri časť 10)*
- Drážka vo vrchu kĺbu (4.5 × 4.8, v deliacej rovine) + drážka v podlahe hlavy 4.5 × 27.4 (hlava sa okolo
  stojaceho kábla posúva o ±8.8), kábel v čiernom oplete, v hlave priviazaný na mostík 44 mm od kĺbu,
  zapojený do hlavičky displeja (5V, G, jeden GPIO).

## 6. Pánt a vonkajšok krku
- Škára pántu 0.3 (bolo 0.5); pevný prstenec na OBOCH koncoch kĺbu (na +X skrýva puzdro ložiska);
  PTFE krúžok 0.25 → axiálna vôľa hlavy ≤ 0.05.
- Uši pántu: valec R10 + stojina, prechod aj hrany čela R0.5 (na želanie používateľa; prvá verzia E2 mala R4 / R3). **Preč:** zásterky a ich kolíky
  („hranaté bloky“ pod hlavou).
- Krk (na želanie používateľa hranatý): zvislé rohy a všetky hrany R0.5 (prvá verzia E2 mala R3). Pod ušami pántu je
  kolíska: sedlo R10.5 sústredné s valčekom ucha (vôľa 0.5), zrezané rovno na z = 10.0, kde má stena vedľa sedla
  1.75 – sedlo po celej výške by na bokoch krku nechalo klin hrubý 0.3 mm, ktorý by sa odlomil.
  Deliaca línia ako V 0.3 × 0.15.
- Golier: drážka R0.75 (roh krku R0.5 + vôľa 0.25), hrana R0.6, škáry 0.25 (kotúč/prstenec) a 0.1 (prstenec/trup);
  šachta v trupe 47 × 22 s rohmi R1.5.
- Vodiče hlavy: 4 × Ø0.85 – štrbina 1.6 × 4.0 v +X uchu, širšia komora pri serve; čap 13.4–18.5 (dĺžka 5.1).
- Skrutky: M2×8 ISO 7380-1 (dk 3.8) do hlavy; štvrtá skrutka krku je šikmá M2×12 (bola M2×14).

## 7. Čo pribudlo pri spojení krku a hlavy (integrácia) *(drážka v podlahe, klenba, zátka, trasa a mostík kábla serva – v E2f zrušené)*
| zmena | prečo (namerané) |
|---|---|
| Drážka kábla v podlahe: koncové steny zvislé (±13.72) do výšky 3.0, až potom skos 40° | skos až po povrch tvoril na stúpajúcej zadnej podlahe novej hlavy ostrú hranu 38° (stena 0.01–1.0) |
| **Klenba nad drážkou kábla** (súčasť škrupiny, sústredná s osou pántu, r 19.8 / 21.1, x −6..14) | cez otvorenú drážku bolo zdola/zozadu vidieť dosku displeja (až 29 mm²), lištu, LED dosku a hlavy skrutiek |
| **Čierna penová zátka** v drážke kĺbu okolo kábla (2. položka `pena_serva`) | pri náklone ±40° bolo zhora vidieť čelo serva (až 4.7 mm²) |
| Stojina uší ±8.25 (čap ±8.0) | cez 0.1 vôľu drážky čapu bolo vidieť driek skrutky (0.02 mm²) |
| Trasa kábla serva: klenba (výška 7.5) → 10.4 ponad pätku −X ucha → mostík → slučka → pin hlavičky | skutočná poloha hlavičky; modul sa dá vytiahnuť ~60 mm bez odpojenia |
| Vodiče hlavy so slučkou dozadu → pin 5V | modul sa dá vytiahnuť ~40 mm |
| Mostík kábla vyšší (9.1, bolo 7.6) | kábel ide vodorovne ponad pätku (jej vrch je 8.5) |
| `sklo`, rohové podložky, spojený „držiak so sedlami“ odstránené z registra aj z STL | už neexistujú |

## 8. Kontroly a dokumenty
- Jeden skript `checks.py` (zostavenie + export, potom `checks_e2_neck.py`, `checks_e2_head.py`,
  `checks_e2_integr.py` na SPOJENOM modeli) → `checks.json` s E1–E10.
  Vypustené kontroly kola 5: sklo/páska/podložky, sedlá displeja, zásterky a kolíky, drážka uška, vybranie
  výstupku, kanál kábla, 35° plôška. Ponechané: zadržanie serva, zovretie krku, čap, golier, obsah obrysov,
  tabuľka náklon/zdvih, uzavretosť STL.
- `montaz.txt` prepísaný pre E2 (nákup, tlač, postup, zapojenie, magnety, servis, limity firmvéru).

## 9. Známe odchýlky od zadania E2 (podrobne v checks.json → deviations_from_E2_spec)
- montážna rovina displeja je na koncoch stĺpikov (11.5 za sklom), nie 7.5; hlavička 12.5;
- lem okna 1.7 / R0.7; doska modelovaná 78.0 × 54.6; lišty hr. 3.0 so skrutkami M2×5;
- ~~drážka v podlahe ±13.72 (zadanie ±11.2) + klenba~~ – v E2f zrušené (podlaha hlavy je zatvorená);
- uši pántu a krk R0.5 (zadanie R3 / R2 – zmenené na želanie používateľa), stojina ±8.25 (zadanie ±8.0);
- lepená dĺžka čapu 2.6 (kolo 5: 3.2) – kapsa serva je o 0.75 dlhšia.

## 10. E2f – kábel serva DOLE do trupu (voľba používateľa č. 1)
**Prečo:** používateľ si z ponúknutých možností vybral možnosť 1 – vodiče serva viesť krkom DOLE do trupu namiesto
hore do hlavy. Trasa hore potrebovala drážku vo vrchu kĺbu, drážku 4.5 × 27 v podlahe hlavy, klenbu nad ňou
(natieranú načierno), penovú zátku, mostík so sťahovacou páskou, čierny oplet, často aj predlžovací kábel, pod hlavou
bolo vidno oplet a hlavička displeja niesla prúd serva. Servo sa teraz zapája v trupe (riadiaca doska trupu dáva PWM
50 Hz; displej jej posiela povely náklonu po 2 signálových vodičoch hlavy).

**Čo sa zmenilo**
| | E2 | E2f |
|---|---|---|
| servo MG90S | pôvodný kábel s priechodkou na čele pri hriadeli | **upravené**: kábel odspájkovaný, 3 × AWG30 silikón (Ø ≤ 0.8) prispájkované na plôšky, von **výrezom 2 × 2 v PREDNEJ dlhej hrane veka**, 12.4 od čela pôvodného kábla (10.4 od protiľahlého); otvor po kábli zalepený; bez výstupku priechodky |
| trasa vodičov | kĺb → podlaha hlavy → klenba → mostík → hlavička displeja | výrez veka → +X do **drážky v PREDNEJ polovici krku** (x 13.15–14.55, y −6.70 až −3.70 v zatvorenom stave, do z = 11.6; pod dnom kapsy uzavretý tunel ~16 mm) → spodkom krku do trupu; pánt nikdy nekrížia, náklon ich neohýba (skupina N – idú len so zdvihom) |
| krk | drážka kábla vo vrchu kĺbu + penová zátka | vrch kĺbu zatvorený; nová drážka vodičov serva oddelená od komory vodičov hlavy stenou 1.75 |
| penové podložky v kapse (+X) | \|y\| 2.4–5.8 (3.4 × 12) | \|y\| 2.3–3.5 (1.2 × 12) – medzi komorou vodičov hlavy a drážkou vodičov serva |
| hlava | drážka v podlahe, klenba, mostík kábla | **podlaha zatvorená**, bez klenby a mostíka |
| zapojenie | servo na hlavičke displeja (5V / G / GPIO) | servo v trupe; hlavička displeja nesie len 4 vodiče hlavy a LED uší |
| nákup | čierny oplet, sťahovacia páska, predlžovací servokábel, čierna zátka | 3 × AWG30 silikón ~300 mm (hnedý/červený/oranžový), bužírka, puzdrá Dupont 1×3, tester serv (odporúčaný), náhradné servo |

**Úprava pri kontrolách (geometria):** drážka vodičov serva rozšírená z 2.45 (y −6.2 až −3.75) na **3.0** (y −6.75 až
−3.75 v návrhu): 3 vodiče Ø0.8 vedľa seba potrebujú 2.4 + vôľu 0.3 po zmrštení tlače 0.15 na stenu (to isté pravidlo
ako pri priechodoch vodičov hlavy). Šírka v X 1.4 = jeden rad + 0.3. Stena k prednej ploche krku 3.3, ku komore vodičov
hlavy 1.75, k zahĺbeniu ložiska 1.23, k skrutke 1.70.

**Kontroly (checks.py):** E10 je nanovo – vodiče serva sú v skupine N, od všetkých dielov hlavy (H) sú v pokoji,
vysunuté aj pri náklone −40..+40 (krok 5) ≥ 0.5 (namerané 3.35 – k +X uchu), celé sú vo vnútri krku až po jeho spodok; drážka
pojme 3 × Ø0.8 a jej steny sú ≥ 1.2 (vzdialenosti aj ray cast). E5 – servo bez výstupku priechodky sa zmestí v celom
rozsahu rozmerov. E9 – žiadna výnimka pre kábel, nevidno nič vnútorné. Vypustené: drážka v podlahe / klenba / tuhý
kábel (staré E10), steny drážky v kĺbe, trasa kábla v hlave (X2), mostík a klenba (X4), varianty výstupku (E5).

# NOVA mini – ruky v2: servá v trupe, ruky tesne pri trupe

Stav 25. 11. 2026. Je to koncept: čísla sú prepočítané na hotovom trupe T4 rev. 3 a na schválenom tvare ruky T3. Ešte to nie je
model na tlač. Neoverené veci sú tak označené.
Súradnice: mm, Z hore, predok −Y, ľavá strana robota +X. Os ramena je rovnobežná s X a ide bodom (y 3, z −17). Čísla
platia pre ľavú stranu; pravá je zrkadlová a bola prepočítaná zvlášť.

Pôvodný návrh v1 so servom v ruke je zamietnutý (`NAVRH_ruky_v1_zamietnute.md`).

## 1. Zhrnutie

* **Servo každej ruky je v trupe.** Ruka je len pasívna biela škrupina bez elektroniky, kábla a serva.
* **Ruka je o 1,0 mm bližšie k trupu** ako v schválenom tvare.
  * Medzera v pokoji je **3,7 mm** (doteraz 4,7 mm). Spredu je viditeľná medzera 2,7 mm.
  * Pri pohybe od −45° do +135° je medzera všade **aspoň 1,0 mm** (najtesnejšie pri +135°).
  * Bližšie to už nejde: každý ďalší milimeter by ruke zobral asi 13° pohybu nahor.
* **Z kĺbu je vidno len tenký čierny krúžok Ø13** a čierny kotúč zapustený 1 mm v pôvodnom otvore bočného krytu.
  Starý vyčnievajúci kĺb T_klb (Ø27) zmizne.
* **Pohon:** servo **Feetech SCS0009** (rovnaké ako Waveshare SC09) stojí v trupe pod ramenom, výstupom nahor.
  Ruku otáča **jediný pár malých kužeľových koliesok** (16 a 24 zubov, mosadz, mazané). Nie je to sada koliesok.
* **Vonkajšok trupu, hlava, krk, otáčanie hlavy aj zdvih ostávajú bez zmeny.**
* **Znova sa tlačí:** dno trupu T_spodok (nové stĺpy s kapsou pre servo), paluba T_paluba (orezaný okraj), oba bočné kryty
  T_bok_L / T_bok_P (len malý zárez vnútri) a dve nové čierne zátky namiesto T_klb_L / T_klb_P.

## 2. Prečo nie servo priamo na osi ruky (bez koliesok)

Najprv som skúšal presne to. Nejde to bez toho, aby ruka odišla od trupu:

* Na osi ramena je od dráhy, kadiaľ sa pri otáčaní hlavy pohybuje servo zdvihu krku (+1 mm vôľa), po povrch trupu len
  **12,4 mm** (vpravo 12,7 mm).
* Servo SCS0009 potrebuje pozdĺž svojho hriadeľa asi **25–26 mm** (telo 21,5 + výstup s drážkovaním).
* Servo by preto trčalo 9–13 mm z trupu a ruka by sa musela odsunúť o rovnaký kus. To je presne to, čo nechceš.
* Nepomôže ani úplné odstránenie modulu zdvihu: na osi by bolo stále len 19,3 mm, lebo tam ostáva otáčajúca sa šachta krku.

Iné cesty, ktoré som prepočítal a ktoré nejdú:

| Koncept | Výsledok | Prečo |
|---|---|---|
| K1 – servo v rohu trupu + čelné kolesá | nedá sa (1,5/10) | Servo s hriadeľom rovnobežným s osou ruky sa v trupe nezmestí nikde, chýba 1,6–2,1 mm, aj keby sa odstránil celý stĺp. Bolo by 46–58 mm od osi, takže by bolo treba medzikoleso Ø30–40 alebo 4 kolesá. |
| K2 – servo dole + remeň alebo lanko | nedá sa (2/10) | Tiež potrebuje servo ležať rovnobežne s osou; zmestí sa telo najviac 19,5 mm (treba 21,5). Vľavo by vošlo do konektorov J1, vpravo nie je miesto vôbec. |
| priamy pohon na osi | nedá sa bez odsunutia ruky | pozri vyššie |
| **K3 – servo stojí pod ramenom + jeden kužeľový pár** | **vybrané (8/10)** | Jediné, čo sa zmestí, a ruka môže ísť dokonca bližšie. |

**K hluku:** každé malé servo má vo vnútri vlastnú prevodovku. Väčšinu zvuku robí ona. Jeden mazaný mosadzný pár
sa točí pomaly (ruka nepotrebuje rýchlosť) a pridá k tomu málo. Hlasitosť som nemeral, je to odhad.

## 3. Ako je to poskladané (ľavá strana)

Pozri `obrazky/v2_rez_ramenom.png` a `obrazky/v2_rameno_rozlozene.png`.

1. **Servo** SCS0009 bez montážnych uší (odrežú sa). Stojí výstupom hore v uzavretej kapse nového stĺpa.
   * Os výstupu je zvislá, x 39, y 3, teda presne pod osou ramena.
   * Telo x 32,95…45,05, y −14,3…8,9, z −66,5…−45,0. Zmestí sa aj vyššie telo (25,25 mm).
   * Sedí na pásikoch PORON 0,5 mm a drží ho spojka hore a zacvaknutá plastová západka dole.
2. **Spojka**: orezaná páka serva + mosadzné puzdro, skrutka M2 zboku.
3. **Zvislý hriadeľ Ø3** (oceľ h6) v ložisku **MR63** v jazýčku stĺpa.
4. **Kužeľový pastorok 16 z** (m 0,5, mosadz) prilepený na hornom konci (Loctite 638).
5. **Kužeľové koleso 24 z** na **hriadeli ruky Ø4** (oceľ h6). Prevod 1,5 : 1: 300° serva = 200° ruky (treba 180°),
   presnosť asi 0,2°.
6. **Čierna zátka** (nová, namiesto T_klb), v ktorej je celé ozubenie ukryté.
   * Dve ložiská **MR74** nesú hriadeľ ruky, poistný krúžok drží hriadeľ.
   * Zátka je pripevnená 3× M2 so zapustenou hlavou do mosadzných vložiek a vystredená 2 kolíkmi Ø2.
   * Drží bočný kryt rovnako ako doteraz T_klb.
   * Jej čelo je 1 mm pod povrchom trupu.
7. **Krúžok Ø13** na zátke. Na ňom je ložisko **6700** v náboji ruky: **ruka sa točí na ňom, nie na hriadeli.**
   Hriadeľ prenáša len krútiaci moment.
8. **Trecia spojka** na konci hriadeľa: podložka s plôškou, mosadzná príruba ruky, podložka, tanierová pružina 8×4,2×0,3,
   podložka, skrutka M2. Prekĺzne pri **0,06 N·m** (asi 1,2 N na konci ruky). Ruka sama potrebuje 0,004 N·m.
9. **Vonkajší kryt ruky** drží na magnetoch, skrutky nie sú vidieť.

Kábel serva je **pevne v trupe**: ide drážkou v nohe stĺpa dole k rozbočke J_BUS_5. Nič neprechádza cez kĺb, takže
sa nemá čo pretrhnúť ani prekrútiť.

## 4. Zmeny v trupe

| Diel | Zmena | Tlačí sa znova |
|---|---|---|
| T_spodok | Nové ramenné stĺpy na oboch stranách: nosná hlava s okienkom pre pastorok, jazýček s MR63, zadná a predná noha, vzpera, priečka, podložka pod servo, západka, drážka pre kábel. Do nôh sa zlepia 2 oceľové tyčinky Ø3 na stranu. Skrutka paluby F3a_2 sa presúva na (29,5; 4,0). Menič napätia ide na dno pod ľavú kapsu. | áno |
| T_paluba | Ľavý okraj orezaný na x ≤ 31 (okrem malého výbežku okolo novej skrutky). | áno |
| T_bok_L, T_bok_P | Len malý zárez vnútri na spodku objímky (x 39,0…41,2), aby sa kryt dal nasunúť cez zvislý hriadeľ. Zvonka bez zmeny. | áno |
| T_klb_L, T_klb_P | Nahradí ich nová čierna zátka (zatka_L / zatka_P). | nové diely |
| zosilňovač MAX98357A | Odchádza zo stĺpa: najlepšie priamo na dosku DPS_riadenie, inak za nosič pri dvierkach. | nie (presun) |
| T_stred, T_dvere, otáčanie a zdvih hlavy, krk, hlava | bez zmeny | nie |

Pohyblivé časti krku majú od nového stĺpa vždy aspoň 1,0 mm (vľavo 1,02, vpravo 1,40). Stredný pás T_stred sa dá
stále nasadiť zhora (vôľa 0,55 mm).

## 5. Pevnosť (zatiaľ len ručný výpočet)

* Zaťaženie ako pri trupe (záťaž L5): 10 N na konci ruky pri +135°.
* **Stĺp:** nohy stĺpa by bez výstuže mali 10,8 MPa pri dovolených 8,5 MPa. S dvoma oceľovými tyčinkami Ø3 na
  stranu majú **3,8 MPa**; spodná časť stĺpa (profil C) má 4,6–4,8 MPa.
* **Koliesko:** pri prekĺznutí spojky 38 / 30 MPa v mosadzi, čo je v poriadku. Pri bežnom chode asi 6 MPa.
* **Krúžok Ø13:** asi 5,5 MPa. **Skrutky zátky:** asi 53 N na skrutku.
* **Výpočet MKP stĺpa ešte nie je urobený.** Treba ho urobiť pred tlačou, rovnako ako pri šachte krku.

## 6. Ochrana a nula ruky

* Keď niekto ruku zatlačí alebo do nej narazí, **prekĺzne trecia spojka**. Servo ani zuby sa nepoškodia.
* Servo má navyše v pamäti obmedzený moment (≤ 30 %) a teplotu (65 °C). Rozsah ruky je −45° až +135°.
* **Nula ruky:**
  * Pri zapnutí a po neočakávanom náraze ide ruka slabou silou (15 %) na skrytý doraz pri −50°.
  * Servo podľa záťaže spozná, že narazilo, a uloží si nulu.
  * Ak by to nestačilo, dá sa doplniť magnet a Hallov snímač v pevnej zátke, opäť bez pohyblivých káblov.

## 7. Montáž a servis

Montáž ľavej strany (pravá je zrkadlová), pri sňatom bočnom kryte:

1. Na stole: do jazýčka vlepiť MR63. Do zátky dať 2× MR74, hriadeľ s kolesom a poistný krúžok (zostava „kazeta“).
2. Zvislý hriadeľ vsunúť zdola cez MR63 a pastorok naň prilepiť v prípravku na podložke 0,5 mm.
3. Hriadeľ nadvihnúť o 4,5 mm.
4. Servo so spojkou zasunúť zboku do kapsy a kábel vložiť do drážky.
5. Hriadeľ spustiť do spojky a dotiahnuť skrutku.
6. Nasadiť bočný kryt; prejde cez hriadeľ vďaka zárezu.
7. Zasunúť zátku: koleso zapadne, kolíky ju vystredia. Dotiahnuť 3× M2 a vôľu ozubenia nastaviť podložkami.
8. Nasadiť ruku so 6700 na krúžok, potom spojku (pružina, podložky, skrutka) a kryt ruky na magnety.

**Výmena serva trvá asi 10 minút:**

1. Kryt ruky dole, povoliť skrutku, ruku zložiť.
2. Vybrať zátku a zložiť bočný kryt.
3. Povoliť spojku a nadvihnúť hriadeľ.
4. Servo vysunúť zboku.

Krk, hlava ani stredný pás sa nerozoberajú.

## 8. Diely na obe ruky

| Diel | Ks | Poznámka |
|---|---|---|
| servo Feetech SCS0009 / Waveshare SC09 | 2 | sériová zbernica, spätná väzba polohy a záťaže |
| kužeľový pár m0,5 16 z / 24 z, mosadz, priame zuby | 2 páry | ak sa nezoženie: pár 16/16 (1 : 1), hriadeľ ruky Ø3, spojka ≤ 0,04 N·m |
| hriadeľ Ø3 h6, oceľ, ~21 mm, s plôškou | 2 | zvislý |
| hriadeľ Ø4 h6, oceľ, ~19 mm, s osadením na Ø3 a závitom M2 v konci | 2 | treba ho dať vysústružiť alebo upraviť |
| ložisko MR63ZZ (3×6×2,5) | 2 | |
| ložisko MR74ZZ (4×7×2,5) | 4 | |
| ložisko 6700ZZ (10×15×4) | 2 | v náboji ruky |
| tanierová pružina DIN 2093 8×4,2×0,3 + 3 podložky (1 s plôškou) | 2 sady | trecia spojka |
| poistný krúžok na Ø4, skrutka M2 do konca hriadeľa | 2 + 2 | |
| skrutka M2 DIN 7991 + mosadzná vložka M2 (vonkajší Ø 3,2) | 6 + 6 | zátky |
| kolík Ø2 h6 | 4 | vystredenie zátok |
| oceľová tyčinka Ø3 (strieborná oceľ) | 4 | výstuž nôh stĺpov, lepené |
| mosadzné puzdro + červík M2 | 2 | spojka na výstupe serva |
| PORON 0,5 mm, magnety Ø3×2 | podľa potreby, 8 | servo; kryty rúk |

## 9. Neoverené – zmerať alebo dorobiť pred tlačou

* Zmerať skutočné servo: výšku tela (21,5 alebo 25,25; zmestí sa oboje), polohu výstupu, na ktorej strane vychádza kábel
  a šírku po odrezaní uší.
* Zohnať kužeľový pár 16/24 m0,5 v mosadzi a overiť jeho skutočné rozmery proti modelu.
* Výpočet MKP nového stĺpa s oceľovými tyčinkami.
* Nastaviť a zmerať spojku: 1,0–1,4 N na 50 mm, pružinovou váhou.
* Presun zosilňovača a meniča napätia; skontrolovať, či menič pod kapsou serva nehreje.
* Presný CAD všetkých zmenených dielov a znova celá sada kontrol trupu K1–K13, vrátane montáže a nového náboja ruky.

## 10. Rozhodnutia pre teba (nie sú nutné hneď)

* **Farba zátky:** čierna (ako schválený kĺb T4), alebo biela, aby bol vidieť len tmavý krúžok a škára.
  Navrhujem čiernu.
* **Ako blízko:** ruka o 1,0 mm bližšie (medzera 3,7 mm, plný rozsah do +135°), alebo o 1,5 mm (medzera 3,2 mm, ale
  ruka len do +122°). Navrhujem 1,0 mm.

## 11. Obrázky (koncept, nie výkres na tlač)

* `obrazky/v2_spredu.png` – celý robot spredu a detail medzery pri ramene.
* `obrazky/v2_rez_ramenom.png` – rez ramenom: servo, hriadeľ, kolieska, zátka, ložiská, spojka.
* `obrazky/v2_vnutro_trupu.png` – kde je servo v trupe a ako blízko je otáčanie hlavy.
* `obrazky/v2_rameno_rozlozene.png` – rozložené rameno s poradím montáže.
* `obrazky/v2_hero.png` – robot so zdvihnutou rukou.
* `obrazky/porovnanie_konceptov.png` – K1, K2, priamy pohon a K3 vedľa seba.
* `obrazky/v1_*.png`, `obrazky/servo_v_trupe_*.png` – staršie obrázky v1 a meranie voľného miesta (len na porovnanie).

Výpočty a skripty: `zdroj/v2/` (K1, K2, K3, výber s prepočtom, obrázky) a `zdroj/v2/vysledok_vyberu.json`.

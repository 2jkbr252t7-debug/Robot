> **Pozor:** tento dokument opisuje revíziu 2. Revízia 3 (spevnená otočná šachta) mení štyri tlačené diely, niekoľko kúpených
> dielov, kroky montáže a limity používania – všetko je v `zmeny_rev3.txt` (má prednosť) a podrobne v `zdroj/opravy3.md`.

# NOVA mini – trup T4, revízia 2: návrh

Trup robota NOVA mini pre tlač zo živice (MSLA, Elegoo Saturn 4 Ultra 16K, živica Elegoo Tough). Každé servo sa dá vymeniť,
tvar a škáry zvonka sú presne podľa schváleného návrhu, hlava a krk (variant B) sa nemenia.
Rozmery v mm. Súradnice: Z hore, predok −Y, pravá strana robota −X, vrch trupu z = 4, „zdvih“ 0 = krk dole, 20 = hore.

Súbory v tomto priečinku:

| súbor | čo to je |
|---|---|
| `montaz_trup.txt` | **praktický postup**: nákup, tlač, vŕtanie, lepenie, uťahovanie, 29 krokov montáže, zapojenie, firmvér, servis |
| `T4_hero.png` | celkový pohľad (trup + hlava + krk, krk 12,5 mm hore) |
| `T4_rozlozeny.png` | rozložený pohľad – všetky tlačené diely a hlavné kúpené diely s popisom |
| `T4_rez_spredu.png`, `T4_rez_zboku.png` | rezy y = 0 a x = 0 – čo je čo a na čo slúži |
| `T4_dvere.png` | otvorené dvierka – čo je cez ne dosiahnuteľné |
| `T4_zospodu.png` | spodok trupu (skryje ho podstavec) |
| `T4_tlac.png` | všetky tlačené diely na doskách tlačiarne v tlačovej polohe, plochy s podperami |
| `T4_ucho_vykres.png` + `ucho.dxf` | výkres ucha L_ucho (nerez 1,5) – rozvinutý tvar 1 : 1 |
| `T4_most_vykres.png` + `most.dxf` | výkres hliníkového mostíka T_most (plech 2,0) |
| `T4_pata_vykres.png` + `pata.dxf` | výkres hliníkovej pätky krku L_pata (plochá tyč 20 × 4) |
| `NOVA_trup.glb` | 3D model na prezeranie (metre, farby; trup + krk + hlava, zjednodušené siete) |
| `NOVA_trup.blend` | scéna Blender (mm, svetlá a kamera ako na obrázkoch) |
| `../stl/*.stl`, `../step/*.step` | diely na tlač / výrobu (STL presnosť 0,01 mm) |

---

## 1. Čo trup robí

| funkcia | ako | rozsah |
|---|---|---|
| otáčanie celého trupu (J1) | servo Feetech STS3215 hriadeľom dole, mosadzný pastorok m1 z18 zaberá do kolesa na náboji podstavca; trup sedí na ložisku 6805 | ±150° (doraz ±153,4°) |
| otáčanie hlavy (pan) | servo Feetech STS3032, oceľový pastorok m0,8 z18 → mosadzné koleso z36 (2 : 1) prilepené pod otočnou šachtou P_sachta | ±85° (kolíkové dorazy ±90°) |
| zdvih krku | servo MG90S v module zdvihu, hliníkové rameno ako kľuka (r 10) → nerezové ucho → hliníková pätka krku | 0 … 20 mm |
| náklon hlavy | servo MG90S v krku (variant B) – napájanie a signál idú plochými káblami z trupu | podľa zdvihu (kap. 10) |
| svetelný pás, reproduktor | 6 × WS2812B-2020 za svetlovodom; reproduktor Ø28 so zosilňovačom MAX98357A | – |
| ruky (neskôr) | ramenné kĺby T_klb s pevným rozhraním (puzdro Ø8,05, 3 magnety, kľúč, F8) | kap. 11 |

## 2. Ako je trup postavený (jednoducho)

* **T_spodok** je kostra – jeden čierny výtlačok: spodok so spigotom (lemom), pätka pre ložisko 6805, kolíska serva J1,
  stĺpiky serva pan, 2 stĺpiky s oceľovými kolíkmi dorazu hlavy, stĺpy ramien a stĺpiky pre elektroniku. Pod servom J1 je
  okno (servo nestojí na tenkej živici, má vzduch).
* Nad servom J1 leží **paluba T_paluba** (servisné veko) a v jej výreze **hliníkový mostík T_most** s prilepeným čapom
  **T_cap**. Okolo čapu sa točí mosadzné koleso 36z prilepené pod **otočnou šachtou P_sachta**; šachtu drží dole jediná
  skrutka F15 (M3) na osi a hore beží v otvore **T_stred** na PTFE páske (horné ložisko, vôľa 0,15).
* V šachte sedí krk (variant B) s hliníkovou **pätkou L_pata**. Pätku zdvíha **modul zdvihu** (kapsa P_drziak_serva + MG90S +
  kľuka + nerezové **ucho L_ucho**), ktorý sa vyberá cez zadné dvierka dvoma skrutkami.
* Elektrina do otočnej hlavy ide **dvoma bežnými plochými káblami FFC** (0,5 mm, 5 vodičov) v slučke okolo šachty – žiadna
  doska plošných spojov na mieru v pohyblivej časti, žiadny zberací krúžok.
* Obal: **T_stred** (stredný pás predok–vrch–chrbát), **T_bok_L / T_bok_P** (bočné kryty), **T_klb_L / T_klb_P** (ramenné
  kĺby), **T_dvere** (dvierka na 4 pároch magnetov, bez háčikov) a predný panel (svetlovod, mriežka, LED, reproduktor).
* Hmotnosť trupu bez hlavy, krku, rúk a podstavca: **388 g**, ťažisko 0,9 mm od osi otáčania J1.

## 3. Materiál – živica

**Tvoja živica: Elegoo Tough** (potvrdená 17. 11. 2026), tlačiareň Elegoo Saturn 4 Ultra 16K (pracovný priestor 211,68 × 118,37 × 220).
Oficiálny technický list Elegoo sa z tohto prostredia nedal otvoriť (stránka elegoo.com nebola dostupná). Čísla nižšie sú
z e-shopov a sú **NEOVERENÉ**:

| údaj | Elegoo Tough | Elegoo Tough 2.0 | zdroj |
|---|---|---|---|
| pevnosť v ťahu | 32,1 MPa ± 10 % | 28,7 MPa ± 10 % | e-shopy, NEOVERENÉ |
| pevnosť v ohybe | 35,1 MPa ± 10 % | – | e-shopy, NEOVERENÉ |
| tvrdosť Shore D | 78–81 | 80–85 | e-shopy, NEOVERENÉ |
| tepelná odolnosť | – | „asi 60 °C“ | e-shop, NEOVERENÉ |
| ťažnosť | nezverejnená | nezverejnená | – |

**Návrh je preto počítaný na dolnú hranicu: pevnosť v ťahu 25,8 MPa** (28,7 − 10 %), a z nej dovolené napätia (už so
súčiniteľom koncentrácie napätia):

* bežné zaťaženie (zdvihnutie za hlavu, zatlačenie na hlavu, ruka, serva): **≤ 8,5 MPa** (bezpečnosť 3),
* trvalé zaťaženie (váha hlavy, predpätie skrutiek) a ostré vnútorné rohy: **≤ 4,3 MPa** (bezpečnosť 6 – živica sa pomaly „plazí“),
* zneužitie (otočenie hlavy rukou, pád zo stola): **≤ 12,9 MPa** (bezpečnosť 2),
* lepené spoje epoxidom: ≤ 2,7 MPa (pevnosť 8 MPa predpokladaná, bezpečnosť 3).

**Ak by si chcel inú živicu**, porovnaj jej technický list (skúška ISO 527 / ASTM D638 po dotvrdení) s týmito požiadavkami:
pevnosť v ťahu **≥ 26 MPa aj pri dolnej tolerancii** (radšej ≥ 30), ťažnosť ≥ 10 % (typ „tough“, „ABS-like“, „nylon-like“, nie
„standard“ ani „8K“), modul 1,5–2,2 GPa, tepelná odolnosť (HDT 0,45 MPa) ≥ 55 °C, Shore D 78–86, vlnová dĺžka 405 nm.
Príklady, ktoré stoja za overenie (všetky čísla len z vyhľadávania, **NEOVERENÉ**): Anycubic ABS-Like Resin Pro 2,
Siraya Tech Blu Nylon. Nevhodné na nosné diely: „standard“ / „8K“ živice (krehké), vysokoteplotné živice s nízkou pevnosťou.

**Ktoré diely smú byť z obyčajnej živice:** len `T_svetlovod` (musí byť číry; nič nenesie). Všetko ostatné nesie skrutku,
vložku, kolík, magnet alebo silu – **jedna húževnatá živica na všetko + lak** je najjednoduchšie.

**Tlač, umývanie, dotvrdenie:**
1. Najprv vytlač **skúšobnú tyčinku** (napr. 80 × 10 × 4) a **jeden blok s vložkou M2 × 4 × Ø4** – vlep ju, po 24 h ju skús
   vytrhnúť skrutkou (vložka musí vydržať viac ako ťah pri dotiahnutí prstami). Až potom tlač veľké diely.
2. Expozícia podľa profilu Elegoo pre Tough na Saturn 4 Ultra 16K; vyhrievaná vaňa (~30 °C).
3. Umyť v IPA ≥ 95 %: 2 × 2–3 min (špinavý, potom čistý kúpeľ). Krátko – húževnaté živice v alkohole mäknú.
4. Vysušiť ≥ 30 min, diery prefúkať (zvyšky IPA = mäkké, kalné, slabé miesta).
5. Podpery z tenkých miest odstráň ešte pred dotvrdením (živica je vtedy menej krehká).
6. Dotvrdiť presne podľa návodu živice; **nikdy viac ako 1,5 × odporúčaný čas** – prevytvrdená živica krehne.
7. Pred vŕtaním a zaťažením počkaj 24 h. Diery vŕtaj až teraz (tabuľka v `montaz_trup.txt`, časť C).
8. Diely chráň pred slnkom (UV ich ďalej vytvrdzuje a krehnú) – lak 2K je zároveň UV ochrana. Nič nepúšťaj nad 55 °C.
9. Neztvrdnutá živica dráždi pokožku: rukavice, vetranie, použitý IPA správne zlikviduj.

**Čo nie je zo živice (zámerne):** obe ozubené kolesá pan a pastorok J1 (mosadz / oceľ), ucho L_ucho (nerez 304), pätka L_pata
a mostík T_most (hliník), kolíky dorazov (kalená oceľ), všetky závity v servisných spojoch (lepené mosadzné vložky), podložky pod
každou hlavou na živici.

## 4. Diely

**Tlačené (16 ks, všetky Elegoo Tough):** T_stred 37,3 g · T_bok_L, T_bok_P po 15,7 g · T_dvere 8,7 g · T_klb_L, T_klb_P po 8,7 g ·
T_svetlovod 0,7 g (číra) · T_mriezka 0,2 g · T_drziak_led 0,9 g · T_drziak_repro 0,8 g · T_spodok 65,3 g · T_paluba 2,5 g ·
T_cap 0,2 g · P_sachta 15,4 g · P_drziak_serva 3,2 g · (voliteľne skúšobný stojan Z_naboj_test 69,8 g). Spolu ≈ 184 g + podpery.
Všetky sa zmestia do tlačiarne aj s okrajom 5 mm; rozloženie na 3 dosky (+ číra + stojan) je v `T4_tlac.png`:

| doska | diely | najvyšší diel |
|---|---|---|
| 1 | T_stred, T_bok_L | 110 mm |
| 2 | T_bok_P, T_dvere, T_klb_L, T_klb_P | 45 mm |
| 3 | T_spodok, P_sachta, P_drziak_serva, T_paluba, T_drziak_repro, T_drziak_led, T_mriezka, T_cap | 103 mm |
| 4 (číra živica) | T_svetlovod | 8 mm |
| 5 (voliteľne) | Z_naboj_test | 24 mm |

Orientácia, podpery (kde áno / kde nie) a odtokové otvory každého dielu: `montaz_trup.txt`, časť B. Kontrola K10 urobila
pre každý diel v jeho tlačovej polohe test „prísaviek“ (uzavretých dutín otvorených k vani): najväčšia zostávajúca je 28,8 mm²
(T_spodok), limit 30 mm².

**Kovové na mieru (3 ks, výkresy + DXF):** L_ucho (nerez 304, 1,5 mm, jeden ohyb 90°), T_most (hliník 2,0), L_pata (hliník 20 × 4).
**Kúpené:** zoznam s presnými typmi a stavom overenia – `montaz_trup.txt`, časť A.

## 5. Lepenie, skrutky, uťahovanie (zhrnutie)

* **Žiadne zatepľované vložky, žiadne lisované uloženia v živici, žiadne zápustné hlavy v živici, nič sa neohýba** (háčiky
  dvierok sú preč – drží ich 8 magnetov).
* 18 mosadzných vložiek je **lepených epoxidom** do dier o 0,1 väčších (M2,5: Ø3,5 × 4; M2: **Ø4,0 × 4** – tenšia M2 vložka
  3,2 × 3,0 pri dotiahnutí prstami nevydrží).
* **Uťahovanie bez momentového kľúča:** malý presný skrutkovač len prstami, hlava dosadne + 1/8 otáčky. Každý spoj na živici je
  prepočítaný na 0,10 N·m (viac prsty na rúčke 10–12 mm nedajú): podložky pod hlavou ≤ 25,8 MPa, vložky vydržia 1,59–1,76 ×
  ťah skrutky, skrutky do plastu sa nevytrhnú (1,17–1,20 ×). Najtesnejšie sú F8 a F10 (podložka 25,77 / 25,8 MPa pri
  najmenšom povolenom priemere podložky) – preto ISO 7092 / DIN 433 podložky, nie menšie.
* Polohu žiadneho dielu nedrží len trenie stiahnutej živice (tá sa časom uvoľní): všade je kolík, kľúč, spigot alebo
  epoxidová výplň (servo pan: drážky F4 vyliate epoxidom okolo navoskovaných skrutiek – krok 13 montáže).
* Loctite 638 len na spoje kov–kov (pastorky na drážkovaní serv, čap kľuky, kolík ucha), Loctite 222 na F4, F8, F12, F15.

## 6. Zapojenie (zhrnutie)

Nosná doska (vlastná DPS, ešte sa nakreslí) s ESP32-S3-Zero je pri dvierkach: 2 × ZIF pre ploché káble do krku, 2 × lišta
zbernice serv (napätie batérie pre STS3215, 5 V pre STS3032 – oddelené napájanie, spoločný dátový vodič), ZIF pre plochý kábel
z podstavca (4 × VBAT, 4 × GND, DATA, WAKE), LED, reproduktor, menič 5 V (3,2 A), zosilňovač. Úplná tabuľka pinov a návrh
priradenia GPIO: `montaz_trup.txt`, časť E. **Rozpočet 5 V:** špička 4,2 A > 3,2 A meniča → firmvér nesmie hýbať všetkým naraz.

## 7. Montáž a servis (zhrnutie)

Montáž ide zdola nahor (29 krokov, `montaz_trup.txt` časť D): kostra → servo J1 → servo pan → paluba s mostíkom → nastavenie
vôle ozubenia (pred prilepením kolesa) → elektronika → T_stred zhora → prstenec goliera → šachta s káblami → krk → modul zdvihu
cez dvierka → ploché káble do krku (hlava na +90°) → kotúč goliera → bočné kryty a kĺby → podstavec → dvierka → hlava.
Kontrola K7 prešla všetkých 50 krokov a servisných riadkov: každý diel ide po priamej dráhe bez kolízie a každá skrutka má
priamy prístup náradia (imbus 1,3, imbus 1,3 s guľovou hlavou, imbus 2,0).

| servo | čo treba dať dole | `montaz_trup.txt` |
|---|---|---|
| zdvih (MG90S v module) | dvierka, 1 konektor, F12, 2 × F10 – modul ide von cez dvierka | G 1) |
| náklon (MG90S v krku) | hlava, modul zdvihu, 2 ZIF – krk ide hore | G 2) |
| pan (STS3032) | krk, F15, šachta hore, trup z podstavca, kryty, 4 × F1, T_stred hore, paluba | G 3) |
| J1 (STS3215) | ako pan + 2 × F16 zospodu | G 4) |
| nosná doska | konektory a USB cez dvierka; samotná doska len s T_stred dole (49,8 > 41,5) | G 5) |

## 8. Rozhranie pre podstavec (ďalšie kolo musí dodať)

* centrálne ozubené koleso **m1, 18 zubov** na náboji podstavca, rovina zubov z −90 … −86 (osová vzdialenosť s pastorkom J1 18,00);
* horná plocha podstavca ≤ z −86, otvor r ≥ 29 až po z −91; vnútorný krúžok ložiska 6805 (Ø25) sedí na náboji v z −98 … −91
  (náboj −0,02 / −0,06), náboj drží trup proti vytiahnutiu (≈ 30 N);
* **prešmykovacia spojka 0,25 … 0,40 N·m (po usadení), trecie plochy oceľ / mosadz, oceľové podložky z oboch strán, kľúč na
  náboj – BEZPEČNOSTNÝ DIEL**: keď niekto otočí trupom rukou, musí sa prešmyknúť spojka, nie zuby alebo lepený pastorok
  (lepený pastorok J1 drží ≈ 1,1 N·m, servo v zablokovaní dá 2,17 N·m). Na stole odskúšaj prešmyk momentovým meradlom;
* dorazový blok J1 pre zub trupu: azimut 270° ± 14,6°, r 17 … 21, vrch ≥ −102,3 (doraz ±153,4°, firmvér ±150°);
* plochý kábel 1,0 mm, 10 vodičov (4 × VBAT, 4 × GND, DATA, WAKE) hore štrbinou v dne trupu (x ±6, y 21,2 … 22,5) do ZIF J_J1;
* podstavec zakryje obeh pastorka J1 (r 28) a otvory v spodku trupu (odtoky, F1, F16) – trup už nemá vlastnú „sukňu“;
* napätie batérie VBAT musí sedieť s verziou STS3215 (otázka 1); prúd 5 V meniča ≈ 3,2 A + serva J1.

## 9. Rozhranie pre ruky (ďalšie kolo musí dodať)

* ramenný kĺb T_klb je **zmrazené rozhranie**: puzdro Ø8,05 od čela po x 44,0, vybranie Ø10,2 po x 38,6, drážka pre vodiče,
  3 magnety N52 Ø3 × 2 (azimut 0°, 120°, 240°), kľúč 2,9 × 1,4 na 0°, skrutky F8 na 60°, 180°, 300°;
* ruka si prinesie vlastné puzdrá a trecí krúžok, ktorý sa **prešmykne pri ≈ 0,25 N·m** skôr, než sa niečo preťaží;
* zaťaženie, na ktoré sú stĺpy prepočítané: 10 N na špičke ruky (72 mm od osi ramena) v ľubovoľnom smere, robot zdvihnutý
  za jednu ruku 15 N – stĺp najviac 7,65 MPa (limit 8,5);
* serva rúk na zbernicu 5 V cez kúpený 3-pinový Y-rozbočovač na J_BUS_5; vodiče hore stĺpom otvorom Ø4,5.

## 10. Firmvér – limity (podrobne `montaz_trup.txt` časť F)

* J1: ±150°, moment STS3215 ≤ 30 %, teplota ≤ 65 °C (register NEOVERENÝ).
* pan: ±85° (kolíky ±90°).
* zdvih: kľuka 3° … 177°; v pokoji parkovať na zdvihu 0, náklon 0; nikdy obe MG90S naraz v zablokovaní.
* náklon: **dole najviac min(40°, 4° + 1,9° × zdvih)**, hore 10° (zdvih < 7,5) / 30° (7,5 … 12,5) / 40° (≥ 12,5). Toto jedno
  pravidlo nahrádza tabuľku z `B/montaz.txt` a riadok „27,5° pri zdvihu 10–15“ (pri zdvihu 10 by hlava narazila).
* 5 V: neťahať všetky serva naraz naplno, počas pohybu stíšiť zosilňovač.

## 11. Odchýlky od schváleného tvaru

Kontrola K8 porovnala 93 204 bodov bielych krytov so schváleným modelom T3: **odchýlka −0,013 … +0,010 mm** (0 bodov nad
0,05 mimo vyznačených miest), 0 priehľadov cez škáry z 26 smerov. Vedomé (schválené už v rev. 1) rozdiely:

| miesto | rozdiel | prečo |
|---|---|---|
| horný okraj okolo goliera | rovný lem r 28,4 → 29,6 + prechod, ≤ 1,2 vodorovne / ≤ 0,5 kolmo (namerané v pásme −1,33 … +0,44) | tlačiteľný biely okraj |
| škára biela / čierna (spodok) | hrana spodku na z −81,5, škára 0,5 (T3 kreslil 0,12) | pravidlo škár |
| škáry | bok / stred 0,466 … 0,476; dvierka 0,225 … 0,236 | ako schválené |
| zárez na otvorenie dvierok | 12 × 1,2 × 0,85 v spodnej hrane dvierok | dvierka bez háčikov |
| spodok (skryje podstavec) | odtokové otvory Ø2,5 / Ø2,0, hlavy F1 a F16, okno pod servom J1, štrbina kábla | tlač, montáž, chladenie |
| ramenné objímky | čierne kĺby T_klb (rozhranie pre ruky) | ako schválené |

## 12. Výsledky kontrol (jednoducho)

Kontroly bežia automaticky skriptom `checks.py` na hotových STL súboroch (výsledok `../checks.json`). Stav v čase tohto
dokumentu je v súhrne nižšie; **„prešla“ znamená, že kontrola na modeli nenašla chybu – nie je to skúška na vytlačenom kuse.**

| # | čo sa kontroluje | výsledok |
|---|---|---|
| K1 | každý diel je jedno uzavreté teleso, STL bez dier | prešla – 166 dielov |
| K2 | diely sa navzájom neprekrývajú (okrem zámerných uložení) | prešla – 665 dvojíc, 0 kolízií, 25 zámerných uložení |
| K3 | pohyblivé diely nikde nedrhnú (351 polôh pan × zdvih) | prešla – najmenšia vôľa 1,0 mm |
| K4 | žiadna stena tenšia ako 1,2 mm okrem vyznačených nenosných miest; nič pod 0,6 | prešla |
| K5 | skrutky súosové s vložkami; vôľa horného ložiska s PTFE páskou | prešla – vôľa 0,145 |
| K6 | kľuka: zdvih presne 20,000, úvrate na 0° a 180° | prešla |
| K7 | montáž a servis: 50 krokov, priame dráhy, prístup náradia | prešla – 0 kolízií |
| K8 | tvar a škáry zvonka = schválený návrh | prešla – −0,013 … +0,010 mm |
| K9 | hlava nenarazí do trupu pri pravidle náklonu (krok zdvihu 0,5 mm, aj s 1° vôľou serva) | prešla – ≥ 1,245 mm v limite, ≥ 0,781 mm pri +1° |
| K10 | každý diel sa zmestí do tlačiarne, má orientáciu, podpery, odtoky, žiadnu prísavku | prešla – 16 dielov |
| K11 | hmotnosť a ťažisko | prešla – 388 g, ťažisko 0,9 mm od osi |
| K12 | pevnosť: 198 riadkov (L1–L8, uťahovanie prstami) | prešla – 0 prekročení; 2 riadky sa výpočtom overiť nedajú (dole) |
| K13 | pravidlá živice (žiadne PETG/POM, len lepené vložky, žiadne zápustné hlavy v živici, nič sa neohýba) | prešla |

**Čo nezávislá kontrola (overenie rev. 2) našla a ako je to opravené** – pre úplnosť, aby si vedel, kde bol návrh najtesnejší:

| nález | čo bolo zle | oprava | stav |
|---|---|---|---|
| G1 | v páse PTFE pásky stálo 8 plôšok šachty na r 26,50 namiesto 26,37 – vôľa by bola 0,02 a pri ±0,15 tlače zovretie | všetko v páse sústružené na r ≤ 26,365 | K5 meria s páskou: 0,145 |
| S1 | ostré rohy na stĺpe ramena (najviac namáhané miesto) | zaoblenie R1,5 a R1,0, otvor vodičov posunutý | stĺp ≤ 7,65 MPa |
| S2 | koreň jazyka kapsy zdvihu bol ostrý, hodnotený mierne | zaoblenie R0,5 | 5,57 / 8,5 MPa |
| S3 | osovú vzdialenosť kolies pan držalo len trenie | drážky F4 vyliate epoxidom | 6,35 / 8,5 MPa |
| S4 | ucho: hliník 5754 by nevydržal (103 > 87 MPa) | ucho LEN z nerezu 304 1,5 + diera Ø1,0 na konci rezu | 137,7 / 143 MPa (tesné) |
| S5 | spoje vydržali len pri 0,015–0,045 N·m (to sa nedá dodržať) | všetko prepočítané na 0,10 N·m, nové vložky M2 Ø4 × 4 | K12 riadky TQ prešli |
| K1/K2 | pri zdvihu 18 a náklone 40° by hlava zavadila; žiadna rezerva na vôľu serva | jedno pravidlo náklonu (kap. 10) | K9 na kroku 0,5 mm |
| B1 | prilepený pastorok pan bránil zložiť T_stred – servo by sa nedalo vymeniť | výrez v T_stred okolo pastorka, pastorok sa lepí na stole | K7 S5a prešla |
| M1 | USB-C kábel sa nedal zasunúť | ESP32 otočené, kúpený 90° FPC predlžovač | K7 T5c prešla |
| M2/M3 | prísavky pri tlači šachty a spodku | vetracie a odtokové otvory | K10 test prísaviek |
| M4 | vôľa ozubenia pan sa nedala nastaviť | nový krok 13 (holé koleso, papier 0,05) | K7 T3b prešla |
| M5 | zvolený ZIF bral len 0,2 mm FPC, iný typ neexistoval | jeden typ ZIF všade: Panasonic Y5B AYF530535 | NEOVERENÝ dielec |
| M6 | ploché káble sa nedali v uvedenom poradí zapojiť | káble sa vedú otvorom pred spustením šachty (krok 19) | K7 riadky FFC |

**Čo zostáva tesné alebo neoverené výpočtom:**
* Ucho L_ucho: 137,7 MPa pri dovolených 143 MPa (nerez 304) – len pri plnom zaťažení 30 N na hlavu pri zdvihu 20.
* Podložky F8 a F10: 25,77 MPa pri limite 25,8 – len ak by mala podložka najmenší povolený priemer 4,2.
* Vôľa T_stred okolo veže pri spúšťaní: 0,249 mm (kritérium bolo znížené z 0,5 na 0,25) – preto skúška nasucho a dobrúsenie.
* Bočná sila na výstup MG90S (30 N, 6 mm od ložiska) – výrobca ju neuvádza → skúška na stole.
* Sila pri páde zo stola na bok – predpoklad, nie meranie → skúška.
* Skúšky na stole, ktoré treba urobiť: vytrhnutie vložky M2 × 4 × Ø4 a M2,5, bočná sila MG90S, úbytok napätia na FFC,
  prešmyk spojky J1 (podstavec), ohybová životnosť FFC (odporúčané 10⁵ cyklov pred dôverou).

## 13. Neoverené údaje kúpených dielov (zmeraj / over pred kúpou)

Weby výrobcov neboli z tohto prostredia dostupné, čísla sú z výsledkov vyhľadávania:
ZIF Panasonic Y5B AYF530535 (a náhrada Molex 54548-0572) – výška a výkres; FH12-10S-1SH(55); hlava USB-C FPC predlžovača
(model 5,0 × 3,5 × 9,5); vložka M2 × 4 × Ø4,0 (123-3D – len názov ponuky); skrutka do plastu M2×6 s hlavou k ≤ 1,2; STS3032 –
drážkovanie (25 z Ø4,95, musí byť kovové) a napätie (napájané 5 V); STS3215 – poloha a závit otvorov v puzdre, dĺžka drážkovania 2,2;
MG90S – počet zubov drážkovania a závit skrutky ramena; ozubené kolesá (KHK / Mädler / RS – tvar, náboj, diera); kondenzátor
Ø8 × 11,5; údaje živice Elegoo Tough; pevnosť epoxidu 8 MPa (predpoklad).

## 14. Otázky pre teba

1. **Batéria v podstavci:** aké napätie (2S 7,4 V alebo 3S 11,1 V)? Podľa toho kúpiš STS3215 vo verzii 7,4 V alebo 12 V.
2. **Nerezové ucho:** vieš si vyrezať a ohnúť kúsok nerezu 304 hrúbky 1,5 mm (pílka na kov, pilník, zverák), alebo ho
   objednáme narezať laserom (DXF je pripravený)?
3. **MG90S:** koľko zubov má drážkovanie tvojho serva? Podľa toho vyberieme hliníkové rameno (ak žiadne nesedí, použije sa
   pôvodné rameno s krycou hliníkovou doštičkou).
4. **Ozubené koleso 36z:** máš prístup k sústruhu (ak by sa dalo kúpiť len koleso s nábojom), alebo hľadáme koleso presne
   bez náboja s dierou Ø8?
5. **Svetlovod:** vytlačíš ho z inej, čírej živice (stačí obyčajná číra), alebo radšej hľadať číru verziu Elegoo Tough?

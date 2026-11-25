# NOVA mini – ruky a ramenné kĺby: návrh (len text, bez modelov)

Stav 24. 11. 2026. Čísla vychádzajú z prepočtu schváleného tvaru ruky (T3) proti hotovému trupu (T4 rev. 3)
a z údajov výrobcov a obchodov. Čo je len odhad alebo neoverené, je tak označené. Súradnice ako na trupe:
mm, Z hore, predok −Y, ľavá strana robota +X, os ramena je rovnobežná s X a ide bodom (y 3, z −17).

## 1. Zhrnutie

* **Pohon:** v každej ruke jedno sériové servo **Feetech SCS0009** (rovnaké ako Waveshare SC09), hriadeľ priamo na osi
  ramena, **bez ozubených koliesok**.
  * Je na tej istej zbernici ako servo otáčania hlavy.
  * Hlási polohu aj záťaž, otočí sa o 300°, má kovové prevody.
  * Stojí asi 9–19 USD.
* **Ruka sa odsunie od trupu o asi 11–14 mm.** Presná hodnota sa určí po zmeraní serva.
  * Biela ruka ostáva presne taká, akú si schválil, len ďalej od trupu.
  * Medzi trupom a rukou bude vidno dlhší čierny kĺb, asi 15–18 mm namiesto dnešných ~4 mm, podobne ako na R01 / R08.
    Spredu je kryt kĺbu vysoký asi 36 mm (siaha ~20 mm pod os ramena, lebo v ňom je časť serva), pozri obrázok
    `obrazky/v1_spredu_porovnanie.png`.
* **Ruka sa točí na čiernom čape Ø22 ramenného kĺbu T_klb.**
  * Servo cez drážkované puzdro prenáša iba krútiaci moment.
  * Váhu ruky, údery a ťahanie nesie čap, nie servo.
* **Poistka proti preťaženiu:** trecia spojka v puzdre prešmykne pri ≈ 0,12–0,15 N·m, t. j. asi 2–3 N na konci ruky.
  Prevody serva nikdy nedostanú viac, ako znesú.
* **Kábel:** 3 tenké silikónové vodiče s voľnou pol-otáčkou okolo čapu v uzavretej komôrke (ohyb na polomere ~11 mm).
  Pri pohybe ruky sa len navíjajú a odvíjajú, nikde sa neťahajú ani nelámu na ostrej hrane.
* **Trup sa netlačí znova:**
  * T_klb ostáva, pod neho sa len vloží puzdro s pružinkami (3 skrutky povoliť, vložiť, dotiahnuť).
  * Elektronika sa nemení – rozbočovač zbernice J_BUS_5 pre ruky je v pláne trupu už teraz.
  * Voliteľne jedna dierka Ø1,5 do T_klb pre kolík automatickej kalibrácie; dá sa vyvŕtať aj do vytlačeného dielu.

## 2. Prečo to nejde tak, ako bolo pôvodne zamýšľané

Pôvodný zámer bol servo v ruke s hriadeľom na osi a ruku tesne pri trupe. Prepočet ukázal tieto prekážky:

* **Málo miesta na osi:** medzi čelom T_klb (x 58,8) a vnútrom vonkajšej steny ruky (stena 2 mm) ostáva len
  **13,3 mm**.
  * Najnižšie servá s kovovými prevodmi sú „krídlové“ KST X06 / X08. Ich telo má 16,6–16,8 mm a podľa výrobcu
    sa otočia len o ±60° = 120°.
  * Servá s rozsahom ≥ 180° majú telo 21–25 mm (SCS0009, MG90S, ES9052MD …).
* **Ruka zasahuje do kĺbu:** schválená ruka zasahuje 1,3 mm do čierneho kĺbu T_klb (horná vnútorná strana, okolo
  stupňa čapu). Posunutím ruky von to zmizne samo.
* **Skutočné rozmery ruky:** hrúbka je 23,0 mm (nie 24,5) a šírka 33,6 mm (nie 35); skutočná dĺžka je 72 mm.

Preskúmané a zamietnuté možnosti:

| možnosť | prečo nie |
|---|---|
| tenké krídlové servo (KST X06) na osi, ruka posunutá len o 5 mm | iba 120° (ruka napr. −20…+100°), PWM bez spätnej väzby, iné zapojenie |
| servo naležato v ruke + kužeľové kolieska 1:1, ruka na mieste | hriadeľ serva je pri jednom konci tela, servo vyčnieva ~2,6 mm z boku ruky (ruka by musela byť ~5 mm širšia); +4 diely, vôľa v zuboch, zuby treba chrániť spojkou ešte slabšou |
| servo v trupe, ruka iba škrupina | **zmerané na hotovom trupe** (mriežka 0,5 mm, otáčanie hlavy ±90°, zdvih krku 0–20): pri osi ramena je medzi stĺpom a servom zdvihu krku len 1,0 mm; najväčší voľný kváder pri ramene 13 × 7,5 × 14 mm. SCS0009 / MG90S / STS3032 sa nezmestia nikde (228 natočení; najbližšie ľavý predný roh, chýba 1,4 mm, a je 40 mm od osi). Servo na osi by z trupu trčalo 9,1 mm, ruka by sa aj tak posúvala o 8,1 mm a znova by sa tlačil celý spodok trupu, oba kĺby a oba bočné kryty. Zmestí sa len KST X06 (120°) s 40 mm lankom cez stĺp. Obrázky `obrazky/servo_v_trupe_*.png` |
| ruka hrubšia namiesto posunu (23 → 34–37 mm) | mení tvar ruky viac ako posun; pri posune sa biela ruka nemení vôbec |
| STS3032 (ako na otáčaní hlavy) | je vyššie (≈ 28,5 mm s hriadeľom) a ťažšie (20 g), posun ruky by bol ešte väčší |

## 3. Ako je kĺb poskladaný (od trupu von)

1. **T_klb (hotový, čierny, pevne priskrutkovaný ku stĺpu)**
   * čap Ø22 dlhý 6,4 mm
   * v strede otvor Ø8,05 hlboký 14,75 mm
   * za ním vybranie Ø10,2 dlhé 5,4 mm, ktoré uzatvára čelo stĺpa trupu
   * na spodku drážka pre kábel (už v trupe)
2. **Drážkované puzdro** (tlačené, Tough, čierne; 1 kus na ruku)
   * hriadeľ Ø8 v otvore T_klb, príruba Ø10 × 2 vo vybraní
   * vnútri drážkovanie pre hriadeľ serva: podľa výrobcu 20 zubov, Ø3,95 – overiť na kúpenom serve
   * drážkovanie s malou radiálnou vôľou (≈ 0,15 mm), aby servo nenieslo bočné sily
   * odporúčam vytlačiť 2–3 skúšobné puzdrá s rôznou vôľou a vybrať to, ktoré ide nasunúť rukou bez kývania
3. **Trecia spojka**
   * za prírubou 2 tanierové pružinky 10 × 5,2 × 0,4 v rade (bežný rozmer), doladenie podložkami 0,1 mm
   * vybranie v T_klb je od čela stĺpa po osadenie dlhé 5,6 mm: príruba 2 mm + pružinky ~1,2 mm ho nevyplnia, preto treba
     dištančný krúžok ~2,4 mm (alebo hrubšiu prírubu, alebo 4 pružinky) – presne sa určí v CAD
   * puzdro musí končiť ~0,9 mm pod čelom T_klb (x ≤ 57,85), lebo do ústia otvoru vojde nákružok serva
   * opierajú sa o čelo stĺpa a tlačia prírubu na osadenie v T_klb
   * keď sa ruka zatlačí silou nad ≈ 0,12–0,15 N·m, puzdro sa v T_klb pretočí
   * hodnotu treba nastaviť na stole: ruku vodorovne, na koniec zavesiť závažie ~250 g, má prešmyknúť
4. **Kryt kĺbu** (tlačený, Tough, čierny; otáča sa s rukou)
   * klzne na čape Ø22 celou dĺžkou (~6 mm), vôľa 0,05–0,10 mm, tenká vrstva maziva s PTFE
   * komôrka pre kábel je okolo tohto puzdra (nie vedľa neho), aby uloženie ostalo dlhé – kryt má preto pri trupe
     Ø ~31 mm (T_klb má Ø27)
   * v otvore tenký O-krúžok: berie vôľu (ruka nerapoce) a drží ruku osovo na čape
   * vnútri komôrka pre kábel (pozri časť 5)
   * na vonkajšej strane objíma tú časť serva, ktorá nie je v bielej ruke
   * priskrutkovaný k vnútornej škrupine ruky 3 skrutkami M2 do lepených mosadzných vložiek
5. **Servo SCS0009:** telo pevne v lôžku vnútornej škrupiny (2 skrutky cez telo serva), hriadeľ v drážkovanom puzdre.
6. **Biela ruka – 3 diely ako na R09 / R10 / R11**
   * vnútorná škrupina: nosná, s lôžkom serva a výstupkami pre skrutky
   * vonkajšia škrupina: kryt; drží na 4 magnetoch Ø3 × 2 a vodiacom leme ako dvierka trupu, dá sa zložiť bez náradia
   * čierna vložka špičky: nalepená
   * stena 2,0 mm, šev 0,5 mm ako na trupe

## 4. Pohyb, sily, hmotnosť

* **Rozsah:** −45° (dozadu) … +135° (dopredu a hore).
  * Hlava ruke nezavadzia v žiadnej polohe: najmenej 9,3 mm, prepočítané pri otočení hlavy ±85°, zdvihu 0 / 20 mm a
    krajných náklonoch. Po posunutí ruky von je vôľa ešte väčšia.
  * K trupu je najbližšie pri +135° (1,9 mm dnes, po posune viac). K podstavcu je 15 mm.
* **Hmotnosť jednej ruky:** ≈ 33 g (škrupina 13 g, servo 13 g, kryt kĺbu a drobnosti ~7 g).
* **Potrebný moment:** ≈ 0,004 N·m (držať ruku vodorovne + rozbehnúť ju o 90° za 0,25 s).
  * Servo má pri 5 V ≈ 0,19 N·m pri zablokovaní, teda rezerva je asi 45-násobná.
  * Obmedzením je skôr rýchlosť: ruka prejde 90° asi za 0,3 s.
* **Zatlačenie rukou:** do ≈ 2–3 N na konci ruky drží, nad tým prešmykne spojka. Servo ani prevody tým netrpia.
* **Pevnosť (ručný odhad, overí sa v CAD):**
  * biela stena pri 10 N na špičke: < 1 MPa
  * 3 skrutky M2 medzi krytom kĺbu a rukou: ≈ 30 N na skrutku pri 10 N na špičke – v limite lepených vložiek
  * čap pri zdvihnutí robota za ruku: ≈ 30 N na hrane uloženia – v poriadku
* **Stĺp trupu:** posun ruky predĺži rameno sily pri zdvíhaní robota za jednu ruku asi 1,4-krát.
  * Limit stĺpa klesne z 15 N na ≈ 10–11 N (odhad, prepočíta sa).
  * Celý robot bude vážiť rádovo 1 kg (odhad), preto ho **za ruky nedvíhať**. Nosiť sa má za trup, ako pri hlave.

## 5. Kábel (aby sa nič neodtrhlo)

* **Vodiče:** 3 vodiče AWG30, silikónová izolácia (veľmi ohybné).
  * Idú zo stĺpa trupu drážkou v spodku T_klb (už existuje) do komôrky v kryte kĺbu.
  * Tam obtáčajú čap asi pol otáčky voľne, potom vchádzajú do ruky.
* **Pri pohybe ruky** o 180° sa v komôrke navinie alebo odvinie asi 35 mm vodiča na polomere 11–14 mm.
  * To je ohyb s polomerom 14-krát väčším, než je hrúbka vodiča.
  * Vodič sa nikde neťahá a neohýba na ostrej hrane.
* **Oba konce voľného úseku sú prilepené** (Kapton + kvapka lepidla): v drážke T_klb a pri vstupe do ruky.
  Pohybuje sa len úsek v komôrke.
* **Konektor JST-SH 3-pin je vo vnútri ruky:**
  * pri servise sa zloží vonkajšia škrupina, rozpojí konektor a ruka sa stiahne z čapu
  * vodič z trupu ostane v drážke a nič sa nevyťahuje cez trup
* **Neoverené:** životnosť vodiča v komôrke. Odporúčam skúšku na stole – 10 000 pohybov −45…+135 (firmvér to
  urobí cez noc) a potom skontrolovať vodiče.

## 6. Elektronika a firmvér

* **Zapojenie:** obe SCS0009 na zbernicu 5 V cez rozbočovač J_BUS_5, ako je v pláne trupu. Spolu s nimi je tam servo
  otáčania hlavy STS3032.
* **ID a trieda v knižnici:**
  * každé servo dostane pred zapojením vlastné ID (napr. ruka vpravo 3, vľavo 4; z výroby majú všetky ID 1)
  * všetky ostávajú na 1 Mbit/s
  * SCS0009 je zo série SCS a v knižnici Feetech má inú triedu (SCSCL) ako STS3032 (SMS_STS) – iné poradie bajtov
  * obe triedy idú cez ten istý sériový port, firmvér musí vedieť, ktoré ID je ktorej série
* **Prúd:**
  * SCS0009 pri zablokovaní ≈ 0,8–1 A
  * v EEPROM nastaviť obmedzenie momentu na ~50 % (adresa 16 podľa tabuľky pamäte Waveshare – overiť) – stále 20× viac,
    ako ruka potrebuje
  * firmvér nemá hýbať oboma rukami naplno súčasne so zdvihom a otáčaním hlavy; menič 5 V má 3,2 A
* **Spätná väzba:** robot cez záťaž serva „cíti“, keď mu niekto drží alebo tlačí ruku, a môže na to reagovať
  (povoliť, zasmiať sa …).
* **Rozsah vo firmvéri:** −45…+135° od kalibrovanej nuly.

## 7. Nula ruky (kalibrácia)

Ak spojka prešmykne, ruka sa voči servu pootočí a firmvér to nevie. Ponúkam dve riešenia:

* **Automatická (odporúčam):**
  * oceľový kolík Ø1,5 × 4 sa vlepí do dierky v stupni T_klb (prstenec pri čape)
  * kryt kĺbu má vnútri výstupok, ktorý o kolík narazí pri −50°
  * pri zapnutí pôjde ruka pomaly dozadu s obmedzeným momentom; keď záťaž stúpne a poloha sa nemení, firmvér si
    zapíše nulu
  * servo pritom nemusí spojku prekonať – stačí, že ruka zastane na kolíku a firmvér si prečíta polohu serva
  * presné miesto dierky (mimo výstupu drážky pre kábel na spodku) určí CAD; stena okolo nej je skrytá v trupe
  * T_klb sa netlačí znova, dierka sa dá vyvŕtať aj do vytlačeného dielu podľa šablóny
* **Ručná:** v aplikácii „kalibrácia rúk“ – servá idú do polohy „ruky dole“ a ty ich rukou dotočíš zvislo
  (spojka prešmykne).

## 8. Tlač (Elegoo Tough, Saturn 4 Ultra 16K)

* **Biele škrupiny:** otvorenou stranou nahor, šikmo ~30°, podpery len zvnútra. Sú to otvorené misky, takže živica
  vytečie.
* **Kryt kĺbu a puzdro:** čierna živica. Otvor pre čap a drážkovanie bez podpier; po vytvrdení prečistiť a skúsiť
  na skúšobnom kuse.
* **Vložky M2:** lepené ako na trupe (otvor = priemer vložky + 0,1), nie zatavené.

## 9. Montáž a servis (stručne)

1. Trup: povoliť 3 skrutky T_klb, vložiť pružinky + puzdro do vybrania, T_klb dotiahnuť (rovnako na oboch stranách).
2. Servo: nastaviť ID a obmedzenie momentu, nasadiť do lôžka vo vnútornej škrupine a priskrutkovať.
3. Kryt kĺbu: priskrutkovať k vnútornej škrupine (3 × M2), vložiť O-krúžok.
4. Kábel z trupu vložiť do komôrky v kryte (pol otáčky), zapojiť konektor v ruke.
5. Ruku nasunúť na čap tak, aby hriadeľ serva vošiel do puzdra (pootočiť, kým zapadne).
6. Nasadiť vonkajšiu škrupinu (magnety).
7. Kalibrácia (časť 7).

Servis serva: vonkajšia škrupina dole → rozpojiť konektor → ruku stiahnuť z čapu → povoliť 2 skrutky serva.

## 10. Diely na obe ruky (odhad)

| čo | ks | poznámka |
|---|---|---|
| servo Feetech SCS0009 / Waveshare SC09 | 2 | ~9–19 USD/ks |
| tanierová pružinka 10 × 5,2 × 0,4 | 4 (+ rezerva) | + podložky 10 × 5,2 × 0,1 na doladenie |
| dištančný krúžok Ø9,9 / 5,4 × ~2,4 (tlačený) | 2 | vypĺňa vybranie v T_klb pod pružinkami |
| O-krúžok pre čap Ø22 (presný rozmer po CAD) | 2 | NBR |
| závitová vložka M2 (lepená) | 2 × (3 + 2) | ako v trupe |
| skrutka M2 × 6 | 2 × 5 | |
| magnet N52 Ø3 × 2 | 2 × 8 | 4 páry na škrupinu |
| vodič AWG30 silikón | ~0,6 m | 3 farby |
| konektor JST-SH 3-pin, pár | 2 | |
| oceľový kolík Ø1,5 × 4 | 2 | len pre automatickú kalibráciu |
| tlačené diely | 2 × 5 | vnútorná + vonkajšia škrupina, vložka špičky, kryt kĺbu, puzdro |

## 11. Čo to znamená pre ďalšie diely

* **Trup:** žiadna nová tlač; doplní sa krok montáže (puzdro + pružinky pod T_klb) a voliteľne dierka pre kolík.
* **Podstavec:**
  * ruky budú siahať do x ≈ ±90–93 mm (doteraz ±79)
  * aby nič neprečnievalo ako na R01, podstavec by mal mať šírku ≥ ~190 mm
  * rozhodne sa pri návrhu podstavca
* **Hlava a krk:** bez zmeny (vôľa k rukám sa ešte zväčší).

## 12. Neoverené – zmerať pred kreslením v CAD

1. **SCS0009:**
   * skutočná výška tela bez hriadeľa – podľa nej je posun ruky 11 alebo 14 mm
   * priemer a výška nákružku hriadeľa
   * počet zubov drážkovania (20 vs 25 – pramene sa líšia)
   * či má telo uši alebo len 2 diery
   * výkres Waveshare / Feetech sa mi nepodarilo otvoriť (sieť ich blokuje), stačí zmerať kúpené servo posuvným meradlom
2. **Moment spojky s tanierovými pružinkami:** nastaviť a zmerať na stole.
3. **Životnosť vodičov v komôrke:** skúška 10 000 pohybov.
4. **Stĺp trupu pri zdvíhaní za ruku po posunutí:** prepočet v CAD.
5. **Rozsah otáčania SCS0009 a správanie pri obmedzení momentu:** skúška na stole (300° podľa výrobcu).

## 13. Rozhodnutia pre teba

1. **Ruku odsunúť o ~12 mm s dlhším čiernym kĺbom** (odporúčam; biela ruka ostáva) – alebo radšej hrubšia ruka
   (34–37 mm namiesto 23 mm), alebo krídlové servo s rozsahom len 120°.
2. **Kalibrácia automaticky s kolíkom** (odporúčam; jedna dierka Ø1,5 do T_klb) – alebo len ručne v aplikácii.
3. **Kryt kĺbu čierny** ako na R08 – alebo biely, aby ruka vyzerala dlhšia.

## 14. Obrázky (koncept, nie výkres na tlač)

* `obrazky/v1_spredu_porovnanie.png` – spredu: schválené vs. návrh v1, celková šírka 157 → 181 mm
* `obrazky/v1_rez_ramenom.png` – rez ľavým ramenom so všetkými dielmi kĺbu
* `obrazky/v1_rozlozena_ruka.png` – rozložená ruka, poradie montáže
* `obrazky/v1_rozsah_pohybu.png` – rozsah −45…+135° a vôľa k hlave
* `obrazky/v1_hero.png` – celý robot, ľavá ruka zdvihnutá
* `obrazky/servo_v_trupe_1_volne_miesto.png`, `_2_na_osi_ramena.png`, `_3_vedla_stlpa.png` – zmerané voľné miesto v trupe
  a prečo sa servo do trupu nezmestí

Zdroje údajov: `zdroj/podklady_ruky.json` (servá, drobné diely, zbernica – s odkazmi), `zdroj/geometria/`
(prepočty tvaru ruky voči trupu; `dd2.py` = potrebný posun ruky pre jednotlivé servá), `zdroj/servo_v_trupe/` a
`zdroj/analyza_servo_v_trupe.json` (meranie voľného miesta v trupe), `zdroj/obrazky_v1/` (skripty obrázkov).
Hlavné webové zdroje: Waveshare SC09 – https://www.waveshare.com/sc09-servo.htm a https://www.waveshare.com/wiki/SC09_Servo;
Feetech SCS0009 – https://www.feetechrc.com/6v-23kg-serial-bus-steering-gear_65522.html;
KST X06 V6.0 (rozsah ±60°) – https://stgaws.robu.in/wp-content/uploads/2024/02/X06_V6.0_Technical_Specifcation.pdf.

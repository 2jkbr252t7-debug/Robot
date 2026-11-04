# NOVA mini – krk v4 (jeden diel, golier ako na R04, guľôčkové ložisko, valec 50/50 v hlave)

Súradnice STL/STEP: mm, z = 0 je stred vrchu trupu, predok robota = −Y, pravá strana robota = −X.
Hlava (návrh 5) je v `../01_hlava_skrupina/NOVA_mini_01_hlava_skrupina_navrh5.*`. V jej súboroch je z = 0 spodok hlavy
a y = 0 stred hlavy. V zostave je spodok hlavy 26,1 mm nad trupom a hlava je o 5 mm posunutá dozadu.

| súbor | diel | poznámka |
|---|---|---|
| `NOVA_mini_N1_krk_jeden_diel` | N1 krk | golier + krk + stred valca v JEDNOM kuse: tenký vodorovný oválny golier 52 × 40 s jemným druhým stupňom (ako na R04), z neho štíhly zvonovitý krk plynulo zaoblený do goliera aj do valca; spodok goliera kopíruje zaoblený vrch trupu (medzera 0,6 mm); dutý |
| `NOVA_mini_N2-P_viecko_prave` | N2-P pravé viečko | k hlave priskrutkované 1× M2 do vlepenej mosadznej vložky, vnútri krížová drážka pre páku serva, krku sa nedotýka |
| `NOVA_mini_N2-L_viecko_lave` | N2-L ľavé viečko | k hlave priskrutkované 1× M2 do vložky; vnútri je vlepené guľôčkové ložisko MR128, ktoré sedí na dutom čape krku; kábel do hlavy ide čapom a šikmým otvorom Ø3,5 |
| `NOVA_mini_N3_unasac_spodny` | N3 spodný unášač | skrytý pod golierom v trupe, 2× M2 so zápustnou hlavou do vložiek v N1; drží krk pevne v trupe (presné uchytenie k trupu sa doladí pri návrhu trupu) |

## Ako sa hlava nakláňa
1. Hlava sa doľava a doprava NEotáča, len sa nakláňa hore a dole. N1 je cez N3 pevne v trupe.
   Doľava a doprava sa otáča celý trup.
2. Spodok hlavy ide presne cez os valca, takže polovica valca je v hlave a polovica pod ňou (50/50).
   Hlava je o 5 mm posunutá dozadu, aby bol kĺb bližšie k stredu jej rovného spodku.
   Viac to nejde, lebo servo by sa pri náklone dotklo zadnej strany displeja.
3. Obe viečka valca sú v hlave priskrutkované a otáčajú sa spolu s hlavou.
4. Servo náklonu (MG90S) je upevnené v N1 a hriadeľ má presne v osi valca. Horná časť serva vyčnieva cez otvor
   na valci do hlavy a hlava sa okolo nej otáča. Hriadeľ cez páku točí pravým viečkom, a tým celou hlavou.
5. Diely sú zo živice, preto sa nikde netrie živica o živicu:
   - pravé viečko nesie samo servo (má vlastné ložisko na hriadeli),
   - ľavé viečko sa točí na guľôčkovom ložisku MR128-2RS (8 × 12 × 3,5).
6. Kábel do hlavy ide dutým čapom ľavého viečka, teda v osi náklonu, takže sa pri náklone len mierne skrúti.
7. Otvor hore na valci (pre servo) je vždy v hlave a ostáva schovaný až do ±50°. Hlava sa o servo zastaví asi pri 42°.
8. Náklon je 40° dole (zošit) a 40° hore (človek). Medzera medzi hlavou a krkom je 0,5 mm pri každom uhle do ±40°
   (overené v CAD). Nič sa nedotýka trupu ani displeja (servo má k displeju pri 40° aspoň 1,7 mm).

## Montáž
1. Ložisko MR128 vlep do ľavého viečka (sekundové lepidlo na vonkajší krúžok, nie do ložiska).
   Mosadzné vložky M2 (Ø3,2 × 3) vlep epoxidom do oboch viečok (hore) a do dvoch výstupkov v N1.
2. N3 priskrutkuj do N1 zdola 2× M2×6 so zápustnou hlavou.
3. Kábel do hlavy priprav bez konektorov: tenké vodiče, zväzok najviac Ø3 mm. Pretiahni ho zdola cez otvor Ø5 v N3,
   krkom hore a von ľavým koncom valca.
4. N1 s N3 vlož do vybrania vo vrchu trupu a pripevni (spôsob sa doplní pri návrhu trupu).
5. Servo náklonu (MG90S): odstrihni úchytky, zvyšky zarovnaj pilníkom a nastav servo do strednej polohy (1500 µs).
   Vlož ho zhora do otvoru valca hriadeľom k pravému viečku (−X). Sedí na dvoch rebrách a bočné rebrá ho vedú.
   Kvapka tavného lepidla ho zaistí a dá sa neskôr odstrániť.
6. Krížovú páku serva orež na Ø14 a vlož do krížovej drážky pravého viečka. Pravé viečko nasuň pákou na hriadeľ serva.
7. Kábel prevleč ľavým viečkom (cez čap a šikmý otvor). Ľavé viečko nasuň ložiskom na čap krku a kábel prevleč
   otvorom Ø4 v hlave.
8. Hlavu nasaď zhora. Cez predný otvor hlavy, pred zacvaknutím rámika, zaskrutkuj 2× M2×6 imbus (kľúč 1,5) do viečok.
   Konektory pripoj až teraz. Odchýlku náklonu (pol zuba drážkovania) dolaď v softvéri.

## Tlač (živica)
- N1 tlač golierom dole, podpery len pod golierom a výstupkami. Dutiny majú otvory, cez ktoré vytečie živica.
- Viečka tlač plochou čelnou stranou dole.
- Po tlači všetko dôkladne vytvrď (UV), inak sú lôžka ložiska a vložiek mäkké.

## Nakúpiť
servo MG90S · ložisko MR128-2RS · mosadzné vložky M2 × 3 × Ø3,2 (4 ks) · 2× M2×6 zápustná (DIN 7991) ·
2× M2×6 imbus (ISO 4762) · tenký kábel do hlavy, zväzok najviac Ø3 mm

Rozmery serva a páky sú v modeli z katalógu. Pred tlačou zmeraj svoje servo a páku posuvným meradlom a uprav konštanty
`SV_*` a `HORN_*` v `nova_mini/krk.py`, lebo klony MG90S sa líšia o ±0,3 mm.
Pri návrhu trupu: doska goliera (celá jej hrúbka) aj N3 budú zapustené v trupe, vrch goliera bude zarovno s povrchom trupu
a nad trup vyjde len jemný druhý stupeň a krk. Krk sa kvôli tomu nemení. Krk sa neotáča, preto bude vybranie v trupe
oválne presne podľa goliera, s rovnomernou úzkou škárou dookola.

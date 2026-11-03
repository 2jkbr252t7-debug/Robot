# NOVA mini – krk (návrh „jeden celok“)

Súradnice STL/STEP: mm, z = 0 je vrch trupu, predok robota = −Y, pravá strana robota = −X.
Hlava (návrh 4) je v `../01_hlava_skrupina/NOVA_mini_01_hlava_skrupina_navrh4.*`. V jej súboroch je z = 0 spodok hlavy,
v zostave je spodok hlavy 27,1 mm nad trupom.

| súbor | diel | poznámka |
|---|---|---|
| `NOVA_mini_N1_krk_jeden_diel` | N1 krk | golier + krk + stred valca v JEDNOM kuse, dutý (stena 1,4 mm), plynulé prechody (zaoblenia 1,6 a 2,5 mm), tenký zaoblený okraj goliera ako na R04 |
| `NOVA_mini_N2-P_viecko_prave` | N2-P pravé viečko | k hlave priskrutkované 1× M2 zvnútra hlavy, vnútri má krížovú drážku pre páku serva |
| `NOVA_mini_N2-L_viecko_lave` | N2-L ľavé viečko | k hlave priskrutkované 1× M2, dutým čapom a šikmým otvorom Ø3,5 vedie kábel do hlavy |
| `NOVA_mini_N3_unasac_spodny` | N3 spodný unášač | skrytý pod golierom, priskrutkovaný na páku serva otáčania, 2× M2 so zápustnou hlavou do N1, otvor Ø5 pre kábel |

## Ako sa hlava nakláňa
1. N1 sa otáča len doľava a doprava. Servo otáčania je v trupe a drží N1 cez N3.
2. Hlava je nasadená na dvoch viečkach valca a priskrutkovaná k nim, takže viečka sa točia spolu s hlavou.
   Čapy oboch viečok sa točia v otvore valca (klzné ložiská Ø17).
3. Servo náklonu je upevnené v N1 a hriadeľ má presne v osi valca. Horná časť serva vyčnieva cez otvor na valci
   do hlavy. Hlava má vo vnútri hladký priestor, v ktorom sa okolo serva otáča. Hriadeľ točí pákou serva
   v pravom viečku, a tým celou hlavou.
4. Kábel do hlavy ide dutým čapom ľavého viečka, teda v osi náklonu, takže sa pri náklone len mierne skrúti.
   Kábel serva náklonu vychádza z jeho horného konca, ktorý je v hlave, a zapojí sa rovno do dosky v hlave.
   Nechaj mu voľnú slučku, lebo hlava sa okolo serva otáča ±40°.
5. Otvor hore na valci (pre servo) je stále pod hlavou a v celom rozsahu náklonu ±40° je úplne schovaný.
   Ďalej sa hlava nakloniť nedá: ak ju niekto dotlačí rukou, asi pri 42° narazí na servo, takže otvor nevykukne.
6. Náklon je 40° dole (zošit) a 40° hore (človek). Medzera medzi hlavou a krkom je 0,5 mm pri každom uhle do ±40°
   (overené v CAD). Viečka majú v hlave vôľu 0,2 mm a spodok hlavy kopíruje ich zaoblenie.
   Doraz na dne valca drží hlavu do strán s vôľou ±0,1 mm.

## Montáž
1. N3 priskrutkuj do N1 zdola 2× M2×8 so zápustnou hlavou (DIN 7991). Až potom zdola priskrutkuj na N3 páku
   serva otáčania, inak by zakryla hlavy skrutiek.
2. Kábel do hlavy priprav bez konektorov: tenké vodiče, zväzok najviac Ø3 mm, napr. 4× silikónový 26 AWG.
   Pretiahni ho zdola cez otvor Ø5 v N3, krkom hore a von ľavým koncom valca. Nechaj asi 15 cm navyše.
3. N1 s N3 nasaď na hriadeľ serva otáčania v trupe. Stredovú skrutku páky zaskrutkuj zhora cez otvor na valci a krk.
   Urob to teraz, kým ešte nie je vložené servo náklonu, potom sa k nej už nedostaneš.
4. Servo náklonu (MG90S): odstrihni úchytky a zvyšky zarovnaj nožom a pilníkom do roviny s krabičkou (< 0,2 mm),
   hlavne na spodnom konci pri hriadeli. Servo položené týmto koncom na stôl sa nesmie kývať.
   Nastav ho do strednej polohy (1500 µs). Zatlač ho zhora do otvoru valca, hriadeľom k pravému viečku (−X).
   Štyri drobné rebrá ho pevne zovrú. Spodkom sedí na dvoch rebrách a na konci oproti hriadeľu
   (strana +X, k ľavému viečku) ho drží doraz. Kábel hlavy drž pri tom dolu pri ľavom konci, aby nebol pod servom.
5. Krížovú páku serva orež na Ø14. Ak sa ramená zužujú, opiľuj ich na rovnobežných 5,2 mm a vlož ju do krížovej
   drážky v pravom viečku (+ kvapka sekundového lepidla).
6. Kábel hlavy prevleč dutým čapom ľavého viečka a von šikmým otvorom Ø3,5 na jeho obvode. Až potom zasuň obe viečka
   čapmi do valca: ľavé posúvaj po kábli, pravé nasaď pákou na hriadeľ serva tak, aby otvor pre M2 smeroval hore.
7. Kábel prevleč cez otvor Ø4 v sedle hlavy. Hlavu nasaď zhora a cez predný otvor hlavy, pred zacvaknutím rámika,
   zaskrutkuj 2× M2×6 imbus (kľúč 1,5) do viečok. Konektory nakrimpuj alebo prispájkuj až teraz.
   Zostávajúcu odchýlku náklonu (najviac pol zuba drážkovania, asi 9°) dolaď v softvéri.

## Tlač
* N1 tlač golierom na podložku. Podpery daj len od podložky (2 mm zápustok pre N3 a spodky výstupkov pre skrutky).
  Rebrá vo vnútri krku sú mosty a podpery nepotrebujú.
* Viečka tlač plochou čelnou stranou na podložku, čapom hore, bez podpier. Okraj zľahka prebrús.

## Nakúpiť
servo MG90S (kovové prevody) · 2× M2×8 DIN 7991 · 2× M2×6 ISO 4762 · kábel do hlavy: tenké vodiče, zväzok najviac Ø3 mm ·
páky a skrutky k pákam sú v balení serv

Rozmery serva a páky sú v modeli z katalógu. Pred tlačou zmeraj svoje servo a páku posuvným meradlom a uprav konštanty
`SV_*` a `HORN_*` v `nova_mini/krk.py`, lebo klony MG90S sa líšia o ±0,3 mm.

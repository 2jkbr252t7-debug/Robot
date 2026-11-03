# NOVA mini – krk (návrh „jeden celok")

Súradnice STL/STEP: mm, z = 0 je vrch trupu, predok robota = −Y, pravá strana robota = −X.
Hlava (návrh 4) je v `../01_hlava_skrupina/NOVA_mini_01_hlava_skrupina_navrh4.*`. V jej súboroch je z = 0 spodok hlavy,
v zostave je spodok hlavy 27,1 mm nad trupom.

| súbor | diel | poznámka |
|---|---|---|
| `NOVA_mini_N1_krk_jeden_diel` | N1 krk | golier + krk + stred valca v JEDNOM kuse, dutý (stena 1,4 mm), plynulé prechody (zaoblenia 1,6 a 2,5 mm), tenký zaoblený okraj goliera ako na R04 |
| `NOVA_mini_N2-P_viecko_prave` | N2-P pravé viečko | pevne v hlave (1× M2 zvnútra hlavy), vnútri je tvarová drážka pre páku serva |
| `NOVA_mini_N2-L_viecko_lave` | N2-Ľ ľavé viečko | pevne v hlave (1× M2), dutý čap = klzné ložisko a zároveň cesta pre káble do hlavy |
| `NOVA_mini_N3_unasac_spodny` | N3 spodný unášač | skrytý pod golierom: páka serva otáčania, 2× M2 so zápustnou hlavou do N1, otvor pre káble |

## Ako sa hlava nakláňa
1. N1 sa otáča len doľava a doprava. Servo otáčania je v trupe a drží N1 cez N3.
2. Hlava je nasadená na dvoch viečkach valca a priskrutkovaná k nim, takže viečka sa točia spolu s hlavou.
3. Servo náklonu je pevne v N1 a hriadeľ má presne v osi valca. Horná časť serva trčí cez otvor na valci do hlavy;
   hlava má vo vnútri hladký priestor, v ktorom sa okolo serva otáča. Hriadeľ točí pákou serva v pravom viečku,
   a tým celou hlavou.
4. Ľavé viečko je ložisko. Káble z hlavy idú cez jeho dutý čap, teda v osi náklonu, takže sa pri náklone len mierne skrútia.
5. Otvor hore na valci (pre servo) je stále pod hlavou a ostáva schovaný až do náklonu 45°.
   Hlava sa o servo zastaví pri asi 42°, takže otvor nikdy nevykukne.
6. Náklon je 40° dole (zošit) a 40° hore (človek). Medzera medzi hlavou a krkom je 0,5 mm pri každom uhle do ±40°
   (overené v CAD). Medzi viečkami a hlavou je 0,1 mm a spodok hlavy kopíruje zaoblenie viečok.

## Montáž
1. Páku serva otáčania priskrutkuj na N3 zdola. N3 priskrutkuj do N1 2× M2×8 so zápustnou hlavou (DIN 7991).
2. N1 s N3 nasaď na hriadeľ serva otáčania v trupe. Stredovú skrutku páky zaskrutkuj zhora cez otvor na valci a krk.
3. Servo náklonu (MG90S): odstrihni úchytky a nastav ho do stredu (1500 µs). Zatlač ho zhora do otvoru valca,
   hriadeľom k pravému viečku (−X). Štyri drobné rebrá ho pevne zovrú, sedí na dvoch spodných rebrách a vzadu má doraz.
4. Krížovú páku serva orež na Ø14 a vlož ju do tvarovej drážky v pravom viečku (+ kvapka sekundového lepidla).
   Viečka zasuň čapmi do valca, pravé pákou na hriadeľ serva.
5. Kábel z krku prevleč cez ľavé viečko (dutý čap → bočný otvor) a cez otvor v hlave.
6. Hlavu nasaď zhora. Cez predný otvor hlavy, pred zacvaknutím rámika, zaskrutkuj 2× M2×6 imbus (kľúč 1,5) do viečok.

## Nakúpiť
servo MG90S (kovové prevody) · 2× M2×8 DIN 7991 · 2× M2×6 ISO 4762 · páky a skrutky sú pri servách

Rozmery serva v modeli sú z katalógu. Pred tlačou zmeraj svoje servo posuvným meradlom a uprav konštanty `SV_*`
v `nova_mini/krk.py`, lebo klony MG90S sa líšia o ±0,3 mm.

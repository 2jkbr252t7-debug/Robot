# NOVA mini – krk (návrh „jeden celok")

Súradnice STL/STEP: mm, z = 0 je vrch trupu, predok robota = −Y, pravá strana robota = −X.
Hlava (návrh 4) je v `../01_hlava_skrupina/NOVA_mini_01_hlava_skrupina_navrh4.*` (z = 0 = spodok hlavy,
v zostave je spodok hlavy 27,6 mm nad trupom).

| súbor | diel | poznámka |
|---|---|---|
| `NOVA_mini_N1_krk_jeden_diel` | N1 krk | golier + krk + stred valca v JEDNOM kuse, dutý (stena 1,4 mm), plynulé prechody (zaoblenia 1,6 a 2,0 mm) |
| `NOVA_mini_N2-P_viecko_prave` | N2-P pravé viečko | pevne v hlave (1× M2 zvnútra hlavy), vnútri je rohatka serva |
| `NOVA_mini_N2-L_viecko_lave` | N2-Ľ ľavé viečko | pevne v hlave (1× M2), čap = klzné ložisko v otvore valca |
| `NOVA_mini_N3_unasac_spodny` | N3 spodný unášač | skrytý pod golierom: 2× M2 do N1, rohatka serva otáčania, otvor pre káble |

## Ako sa hlava nakláňa
1. N1 sa otáča len doľava/doprava (servo otáčania je v trupe, drží N1 cez N3).
2. Hlava je nasadená na dvoch viečkach valca a priskrutkovaná k nim, takže viečka sa točia s hlavou.
3. Servo náklonu je pevne v N1 a hriadeľ má v osi valca. Telo serva trčí cez otvor na valci do hlavy.
   Hriadeľ točí rohatkou v pravom viečku, a tým celou hlavou. Hlava má vnútri voľný priestor, v ktorom sa otáča okolo serva.
4. Ľavé viečko je len ložisko.
5. Otvor hore na valci (servo + káble do hlavy) je vždy schovaný v hlave, aj pri náklone 40°.
6. Náklon je 40° dole (zošit) a 40° hore (človek). Medzera medzi hlavou a krkom je 0,5 mm pri každom uhle, overené v CAD do ±42°.

## Montáž
1. Servu MG90S odstrihni úchytky. Vlož ho zhora do otvoru valca tak, aby hriadeľ smeroval doprava (−X).
   Servo sedí na dvoch rebrách a bočné vodiace rebrá ho držia proti pretáčaniu.
2. Okrúhlu rohatku (orezanú na Ø14) priskrutkuj do pravého viečka.
3. Viečka nasuň čapmi do valca, pravé nasuň rohatkou na hriadeľ serva.
4. Hlavu nasaď zhora. Cez predný otvor hlavy (pred zacvaknutím rámika) zaskrutkuj 2× M2×6 do viečok.
5. N3 priskrutkuj zdola 2× M2×5 a pripoj ho na rohatku serva otáčania v trupe.

## Nakúpiť
servo MG90S (kovové prevody) · 2× M2×6 · 2× M2×5 · skrutky rohatiek (sú pri servách)

NOVA mini – trup, ruky a podstavec podľa listov R05 / R02 / R01 (vizualizácia)
==============================================================================

Obrázky
  NOVA_vs_R01.png         celý robot vedľa obrázka R01, pohľad spredu a z boku, rozmery
  NOVA_trup_vs_R05.png    trup vedľa listu R05 (spredu, zozadu, pravý bok, zhora)
  NOVA_celok.png          samotný obrázok robota

3D model (priečinok model_3d)
  NOVA_mini_cely_robot.glb     celý robot, vyfarbený a vyhladený – Blender: File > Import > glTF 2.0;
                               dá sa otvoriť aj vo Windows 3D Viewer alebo v online prehliadači glTF
  NOVA_mini_cely_robot.blend   scéna pre Blender so svetlami a kamerou (diely sú samostatné objekty,
                               kolekcie torso / arms / base / head / neck)
  NOVA_mini_telo_STL.zip       trup, ruky a podstavec ako STL po dieloch (mm, na svojom mieste)

Rozmery (mm): trup 105 × 80 × 85 (pri krku Ø57) + čierny spodok 3,5; ruka 72 × 35 × 24; kĺb ramena Ø27;
podstavec 146 × 112 × 27 + pätka 3,5; výška robota ≈ 203 (krk zasunutý) až ≈ 223 (krk vysunutý).
V modeli je krk vysunutý o 12,5 mm.

POZOR: trup, ruky a podstavec sú zatiaľ len VIZUÁLNY model vzhľadu (škrupiny bez vnútra, bez uchytenia
serv a elektroniky). Na tlač nie sú určené. Hlava a krk sú hotové diely z priečinka 03_koncept_otocny_krk.

Priečinok zdroj: skripty, ktorými model vznikol (shape.py = tvar odmeraný z listov, build_scene.py =
zostavenie a render v Blenderi, sheets.py = porovnávacie listy).

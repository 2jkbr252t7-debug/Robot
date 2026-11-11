NOVA mini – výsuvný krk a hlava, VERZIA B, revízia E2 – STL modely
====================================================================

Podľa skutočných dielov:
  displej  Waveshare ESP32-S3-Touch-LCD-3.5B, holá doska bez krytu (oficiálny výkres Waveshare):
           sklo 92,44 × 61,00 × 1,10 mm, rohy R6, 4 stĺpiky M2 v rozostupe 72,00 × 48,50
  servo    MG90S podľa obrázka a fotiek od používateľa (vežička s dvoma výstupkami rovnakej výšky,
           kábel vychádza z čela pri hriadeli; obe úchytné ušká sa odrežú)

Jednotky mm, os Z hore, predok robota = −Y, pravá strana robota = −X.
Všetky diely sú v POKOJOVEJ polohe (krk zasunutý) a na správnom mieste – po importe do Blendera
(File > Import > STL) do seba zapadnú bez posúvania.

Hlava 110 × 79 × 66 mm. Krk 45 × 20 mm z dvoch polovíc, zdvih 20 mm, náklon hlavy ±40° (len pri vysunutom krku).
Servo MG90S leží v kapse medzi polovicami krku, os jeho hriadeľa je os kĺbu: páka serva sedí v drážke krytu
pravého uška (−X) a točí hlavou priamo. Ľavé uško (+X) sa otáča na ložisku MR85 na dutom čape, ktorým idú
4 vodiče do hlavy. Kábel serva ide hore cez drážku v kĺbe do hlavy a zapája sa do hlavičky displeja.
Tvárou robota je sklo displeja v čiernom lesklom ráme; celý predný modul drží na 6 magnetoch.

Priečinok B_servo_v_krku
  <diel>.stl            každý diel zvlášť; názvy sú rovnaké ako v montaz.txt
  CELOK_pokoj.stl       celý robot v jednom súbore, krk zasunutý
  CELOK_vysunute.stl    krk vysunutý, hlava rovno
  CELOK_naklon40.stl    krk vysunutý, hlava 40° dole
                        (CELOK_* sú zjednodušené na 30 % trojuholníkov – len na prezeranie, netlačiť)
  montaz.txt            nákup, tlač (farba, povrch, orientácia), montáž krok za krokom, zapojenie, servis,
                        obmedzenia náklonu vo firmvéri
  ZMENY_E2.md           čo sa zmenilo oproti predchádzajúcej verzii a prečo
  kontroly.json         namerané kontroly modelu E1–E10 (kolízie pri náklone −40° až +40° a pri zasúvaní,
                        hrúbky stien, rozsah rozmerov skutočných serv MG90S, displej podľa výkresu, magnety,
                        viditeľnosť vnútra, montážne cesty, uzavretosť STL)

Čo sa tlačí zo živice (MSLA) – presný zoznam, farby a orientácia sú v montaz.txt (časť B):
  hlava_skrupina, ram_displeja, drziak_displeja, usi (2×), led_kruzky (2×), krk_predna_polovica,
  krk_zadna_polovica, usko_kryt, usko_lozisko, golier_kotuc, golier_prstenec.
Ostatné súbory (displej, servo, páka, ložisko, čapy, skrutky, vložky, magnety, peny, PTFE krúžok, kábel,
LED dosky, oči) sú kupované diely alebo len vizualizácia – v modeli sú na kontrolu, že sa všetko zmestí. Netlačiť.

Trup je zatiaľ ilustračný (výška 100 mm) – je ďalší na rade.

Blender: ../NOVA_mini_B.blend
  Medzerník = animácia: otočenie do strán, vysunutie krku, náklon 40° dole, 40° hore, zasunutie.
  Kolekcie: B_1_obal (vonkajšie diely), B_2_displej (displej, držiak, magnety, LED dosky), B_3_mechanika
  (servo, páka, čap, ložisko, skrutky, kábel…), B_4_trup, B_5_rez (hlava a krk rozrezané spredu – zapni oko),
  B_6_osi.
  Vnútro: vypni oko pri B_1_obal. Rez: vypni B_1_obal a B_2_displej, zapni B_5_rez.

3D model v prehliadači: ../model_3d/prehliadac.html (otvor v prehliadači; súbor .glb musí byť vedľa neho)

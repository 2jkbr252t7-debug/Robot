# Trup – podrobný model na tlač zo živice (revízia 3 – spevnená otočná šachta)

Stav k 23. 11. 2026. Trup je navrhnutý na tlač zo živice Elegoo Tough na Elegoo Saturn 4 Ultra 16K.
Revízia 3 spevňuje otočnú šachtu krku a jej spodok (skrutka čapu, plné dno, rohy okien, uloženie modulu zdvihu, dorazy otáčania).

**Čo je nové oproti rev. 2 – čítaj `zmeny_rev3.txt`** (má prednosť pred `montaz_trup.txt`, ktorý je stále rev. 2):
* znova tlačiť 4 diely: `P_sachta`, `P_drziak_serva`, `T_cap`, `T_paluba`; ostatných 12 tlačených dielov je bez zmeny
* kúpiť / pripraviť inak: skrutka M3×8, 2 + 1 podložka DIN 125 M3, kolík Ø2×6, pastorok skrátiť na 3,0 mm, a ďalšie drobnosti
* zmenené kroky montáže (nový krok B4c na stole; skrutka F12 sa vkladá do ucha už v kroku 5)
* nastavenie serva otáčania (uhlové limity ±85°, obmedzenie momentu 15 %) a limity používania

**Kontroly na finálnych modeloch:** K1–K11 a K13 prechádzajú. Pevnostná kontrola K12 je zámerne vedená ako „neprešla“: pri plánovaných
silách (30 N na hlavu, 0,88 N·m do dorazu) viac miest prekračuje povolené napätie. Nič z toho nie je skryté – každé také miesto má
vypočítanú silu, pri ktorej povolené napätie dosiahne, a tie sú uvedené ako limity používania v `zmeny_rev3.txt`, časť 5
(napr. zdvihnutie robota za hlavu najviac 15 N ≈ 1,5 kg; doraz −90° najviac 0,28 N·m). Jedna nezávislá kontrola (pasovanie, otáčanie,
zdvih, zasúvanie modulu, tlačiteľnosť, čísla v dokumentoch) našla dve vážnejšie veci v postupe – obe sú opravené v texte, tvar dielov sa nemenil.

**Neoverené / otvorené:** údaje kúpených dielov (hlavne výška hriadeľa serva STS3032 – zmerať PRED tlačou šachty), údaje živice len
z ponúk predajcov, skúška na stole, či sa hlava pri 15 % momentu ešte spoľahlivo otáča. Obrázky, video, animácia a `montaz_trup.txt` /
`NAVRH_trup.md` sú stále z rev. 2 (zámerne sa neprerábali).

Obsah priečinka:
* `zmeny_rev3.txt` – zmeny rev. 3 pre stavbu (tlač, nákup, kroky, firmvér, limity)
* `rev3_nahlady/` – tri náhľady novej šachty (zozadu, zdola, zhora)
* `model_3d/` – `NOVA_trup.glb` (prehliadač), `NOVA_trup.blend`, `trup_STL_na_tlac.zip` (16 tlačených dielov),
  `trup_STL_vsetky_diely.zip`, `trup_STEP.zip` – všetko rev. 3. STL sú v montážnej polohe – v sliceri ich otoč podľa `T4_tlac.png`
  a časti 6 v `zmeny_rev3.txt`.
* `montaz_trup.txt`, `NAVRH_trup.md`, obrázky `T4_*.png`, `vykresy/`, `mechanizmy/`, `kontrola_sachty/` – rev. 2 (kovové diely na mieru sa
  nemenia okrem zrazenia rohu ucha, pozri zmeny)
* `zdroj/` – CAD (build123d), kontroly (`checks.py`, `checks.json`), špecifikácia (`T4_spec.md`, kap. 17.17 = rev. 3), `opravy3.md`
  (čo sa zmenilo a prečo, všetky čísla), `fe_sachta/` (pevnostný výpočet a výsledky), `overenie3/` a `fixback3_work/` (nezávislá kontrola a doladenie)

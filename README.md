# NOVA – stolový robot-spoločník (v7.3)

Kompletný návrh robota NOVA: parametrický CAD model (build123d) a fotorealistické rendery (Blender Cycles).
Všetky obrázky sú vyrenderované z **jedného 3D modelu**, takže pohľady navzájom presne sedia a rozmery sú skutočné.

## Obrázky (`obrazky/`)
| súbor | obsah |
|---|---|
| `00_NOVA_prehlad.png`, `00b_NOVA_hero.png` | prehľad – hlavný render + základné parametre |
| `01_NOVA_celok_6_pohladov.png` | celý robot – spredu, zozadu, pravý/ľavý bok, zhora, zdola |
| `02_NOVA_rozmery.png` | hlavné rozmery a výškové úrovne (mm) |
| `03_NOVA_rozlozeny_pohlad.png` | rozložený pohľad so všetkými vonkajšími dielmi a číslami dielov |
| `04_NOVA_rezy.png` | rezy A–A a B–B – hrúbky stien, zástavba komponentov |
| `05_NOVA_vnutro.png` | „röntgen“ – priehľadné kryty, vnútro na mieste |
| `06_NOVA_kinematika.png` | 5 stupňov voľnosti a ich rozsahy |
| `07`–`08` | hlava a jej diely (H01–H06) |
| `09`–`10` | krk a golier (N01, N02, N06, N07) |
| `11`–`12` | trup a jeho diely (T01–T06) |
| `13`–`16` | pravá a ľavá ruka, diely ruky (A01–A05), skladanie ruky a ramena |
| `17`–`18` | základňa a jej diely (B01–B08) |
| `19_NOVA_vnutorna_elektronika.png` | vnútorná mechanika a elektronika + kusovník |
| `20_NOVA_displej_vyrazy.png` | rozloženie displeja, výrazy tváre, LED signalizácia |
| `21_NOVA_porovnanie_so_zadanim.png` | porovnanie so zadaním |

## Dokumentácia
* `docs/SPEC.md` – špecifikácia: diely, rozmery, funkcie, elektronika (BOM).
* `docs/REVIEW_NOTES.md` – pre CAD modelára: čísla vnútorných dielov, postup montáže, skrutky, vôle, výroba.
* `nova/spec.py` – jediný zdroj všetkých čísel (súradnice: mm, Z hore, predok robota = −Y).
* `export/` – STEP súbory všetkých dielov (v polohe zostavy – po importe do CAD sedia na svojom mieste).

## Ako to znova vygenerovať
```bash
/opt/venv/cad/bin/python -m nova.cad.base        # … head, neck, torso, arms, internals
/opt/venv/cad/bin/python -m nova.render.make_sheets --quality final
```
Podrobnosti v `CLAUDE.md`.

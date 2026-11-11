# NOVA mini – trup a podstavec: ROZPRACOVANÉ (zastavené 2026-11-11 na pokyn používateľa)

Používateľ prácu zastavil, výsledok sa mu nepáčil. Tu je uložené všetko podstatné, aby sa dalo pokračovať.

## Čo je hotové
- `T1_brief.md` – zadanie: rozhodnutia používateľa (kolesá, 2 ruky, otočný trup ±150° so STS3215, otáčanie hlavy ±80°,
  4× 18650 + USB-C), rozhranie s hotovým krkom a hlavou (verzia B, rev. E2), cieľové proporcie, požiadavka
  „žiadne hranaté tvary, moderné a mäkké“.
- `t1lib.py`, `t1_preview.py` – nástroje: rozloženie dielov v JSON, polohy kĺbov, kolízie, ťažisko, prevrátenie, náhľady.
- `k2/`, `k3/` – dva návrhy vnútra (k1 zlyhal). `hodnotenie.md` – porovnanie, víťaz K2.
- `pack/` – zlúčené vnútro (K2 + nápady z K3): `pack.md` (popis, zhrnutie po slovensky na konci), `layout.json`,
  `envelope.json` (najmenší vnútorný priestor pre tvar), `check.json` a náhľady `prev_*.png`.
- `formy/f1` – variant „R01 moderný“, prvý návrh (pred kritikou): `exterior.py`, rendery `render_*.png`.
- `formy/f2` – variant „Kapsula“, rozpracovaný: `exterior.py`, testy hladkosti `zebra_*.png` (bez renderov).
- `formy/formy_f1_f2_STEP.zip` – STEP diely oboch variantov (STL sa dajú znova vygenerovať z `exterior.py`).

## Čo nie je hotové
Kritika a oprava f1/f2, varianty f3 („Plynulý monolit“) a f4 („Hravý mäkký“), porovnávací list, 3D modely na prezeranie.

## Poznámka
Skripty majú cesty do pracovného priečinka relácie (/tmp/claude-0/gapwf/fin/…); pri pokračovaní v novej relácii
treba cesty upraviť na tento priečinok.

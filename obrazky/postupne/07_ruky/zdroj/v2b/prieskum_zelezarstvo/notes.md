# Research B notes (26 Nov 2026) - hardware/fastener parts SK/CZ
WebFetch blocked (ENOTFOUND): www.hornbach.sk, www.tymoty.com, www.laskarduino.sk -> per tool instruction stopped trying more hosts.
All data from WebSearch result summaries (pages not opened) -> verified=false.

## Screws
- Hornbach CZ (same chain/assortment as hornbach.sk, product IDs shared): DIN 912 8.8 zinc white M3x10/16/20/25/40, packs of 10;
  M3x25 30 CZK/10; M3x40 35 CZK/10 (2.05 CZK/pc). M4x50 DIN912 500-pack (unavailable at search). M5 to 100 mm (200-packs).
  https://www.hornbach.cz/p/sroub-metricky-m3x40-inbus-valcova-hlava-pevnost-8-8-zinek-bily-10ks/12663699/
- Hornbach DE: DIN 912 M3x10..25 "Vollgewinde" (full thread). Hornbach AT/RO/SE Dresselhaus DIN 912 4x40 zinc "Teilgewinde" 100 pcs (id 6834954)
- Hornbach CZ DIN 7985 M3x10/16/20 single pcs; DIN 963 brass M3x6..40; DIN 965 M3x6/10; DIN 84 brass M3x10/20/30; DIN 7991 M4x30 10.9 20pcs;
  ISO 7380 only M5/M6 found; set screws (ISO 4026 A4) M4..M10 found, no M3.
- Hornbach DE/SE/RO: DIN 7991 M3x6, M3x10 A2 (Dresselhaus 100-pack)
- Tymoty (CZ fastener e-shop, EUR prices): DIN 912 M3x30 8.8 0.07 EUR/0.08 incl VAT; ISO 7380 M3x10/16/30 A2 (M3x16 14060 pcs stock)
  ISO 7380 M3x12 10.9 zinc; DIN 913 M3x12 0.03 EUR (earlier audit)
- 3djake.sk: CNC Kitchen screws ISO 14580 M2x6 A2-70 25 pcs + M3 variants
- Fabory SK: ISO 7380-1 zinc + A4 variants (sizes not confirmed)
- shank: torqbolt DIN 912 table shows 3/2.86 (M3) and 4/3.82 (M4) pairs (column header garbled)

## Threaded rods
- Hornbach CZ: tyč závitová 1 m M3 nerez A2 39 CZK/pc (12413693). zbozi.cz M3x1000 DIN 976 30-72 CZK. Only 1 m lengths -> needs cutting -> FORBIDDEN (rule a).
## Nuts/washers
- Hornbach CZ: matice přesná M3 nerez A2 40 ks 21 CZK (12545839); DIN 934 M3 brass 1 ks; DIN 985 M3 not found at Hornbach (HOBBY-MAX.CZ has DIN 985 M3 A2)
- Hornbach CZ: podložka plochá 3 střední nerez A2 60 ks (12545848) d1 3.2; DIN 9021 3.2 brass 1 ks; DIN 125 4.3 polyamid 0.60 CZK/ks
- TME: Bossard BN 1074 polyamide DIN 125A M3 (D7 h0.5, 1404830) and M4 (D9 h0.8, 1404849), MOQ 100
- DIN 433 M3: 3.2 x 6.0 x 0.5 (McMaster/Westfield); DIN 439 M3: s5.5 m1.8 (McMaster)
- PTFE washer M3/M4 small: NOT found in SK/CZ retail (only PTFE thrust washers 8x18 at exvalos.cz)
## Springs / O-rings
- Hornbach CZ: tažné a tlačné pružiny sada 200 ks 46 CZK; single springs e.g. 11x67x1 zinc, 16.4x51.5x1.8 A2
- Kaufland CZ 314027357: 200-pc set incl 10x 7x12.5, 10x 5.5x25.5 (zinc) - same as Duratool D01893 / Craft-Meyer; wire Ø not stated
- Hornbach CZ O-ring set 225 ks 169 CZK (12075186), sizes in snippet e.g. 5x13x3, 5x14x2.5, ..., material shown PU (conflict)
- Tymoty: single Dichtomatik O-rings NBR 70/90: 1.8x1.5, 10x1.5, 23.5x1.5, 45x1.5
## Inserts
- Prusa (CZ): CNC Kitchen brass M3x5.7 standard 100 pcs USD 10.99, M3x3 short, M2.5 standard, M2 short; sets standard/short 200, XXL 760
- 3DJake: ruthex M3x5.7 100 pcs, M2.5x5.7 70 pcs, M2x4 70 pcs; CNC Kitchen M3 std: L5.7, OD 4.6, tip 3.9, hole 4.0, min wall 1.6
- Heat-set NOT possible in thermoset resin (Formlabs, Fictiv) -> glue-in with epoxy / CA in stepped hole

## Magnets
- umagnets.com/sk (SK-language): 4x2 N35 (+-0.05), 5x2 N38/N50 (pack 50), 3x2 diametric N38 (beware: diametral!), 2x2
- Alza.cz SOLLAU 4 mm round 50 pcs 106 CZK (thickness not stated); filamentia.com 4x2 0.17 EUR; yourmagnets.net 3x2 N52 ~0.17 EUR
- sprintis.com (DE) 5x2 N38 0.5 kg / N52 0.68 kg; tuan.hu 3x2 N52 50 pcs 2877 HUF
## Adhesives
- Loctite 243 5 ml: Hornbach CZ 249 CZK (7663487); bahnik.cz 7.35 EUR; airsoftpro.cz 229 CZK; Farnell SK 10 ml 15.74 EUR ex VAT
- Loctite 638 10 ml + activator kit: umakov.sk 19.00 EUR incl VAT, SK branches Krompachy, B. Bystrica, Bratislava, Senec
- Loctite 638 TDS: gaps up to 0.25 mm; 243 TDS: "not normally recommended for plastics (stress cracking)"
- Anaerobics on plastic need activator (7649) - 638 kit at umakov includes activator
- UHU plus endfest: Hornbach DE 15 g 9.45 EUR, AT 25 g 10.75 EUR (SK store not indexed)
## Springs math (calc_springs.py)
- 0.06 N.m clutch: mu0.12 r3.6 2 faces -> 69 N (current DIN 2093 design); mu0.2 r5 -> 30 N; mu0.3 r5 -> 20 N
- Exvalos CSN 02 6020 1x9x24x8.5 -> k~3 N/mm, usable ~26 N; Hornbach A2 6.6x33x0.7 -> usable ~11 N (n estimated)
- 225-pc O-ring set (Hornbach CZ / Kaufland / Hogert HT8G509 / Garage Tough): ID x CS 3x1, 4x1, 4.5x2, 5x2, 6x2, 6x2.5, 7x2, 8x2, 9x2, 10x2, 12x3, 13x3, 14x2.5, 17x2.5, 18x4, 20x2, 22x2 (inferred - no 1.5 CS)
## Set screws
- Hornbach CZ: červík s hrotem M4x6 INBUS H45 zinc 10 pcs 33 CZK; ISO 4026 A4 M4..M10 single; no M3
- Tymoty DIN 913 M3x12 zinc 0.03 EUR (snippet 2025)

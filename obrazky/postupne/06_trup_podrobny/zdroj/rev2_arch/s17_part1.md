
---------------------------------------------------------------------------------------------------------------------

## 17. REV. 2 – resin-only, serviceable torso (lead architect, 2026-11-17; supersedes §1–§16 wherever they differ)

Binding inputs: `T4_rev2_plan.md` (D1–D7), `T4_zivica.md` (Z0–Z5, L1–L8). Numbers below are also in the block
`# >>> rev2 (architect)` of `t4_common.py` (dict `R2` + aliases); if this text and `R2` differ, `R2` wins.
Measurements behind the numbers: `rev2_arch/a01_measure.py` → `a01_measure.json` (real rev. 1 STLs, B STLs, exterior
functions) plus the reviewers' measurements (`zjednodusenie/m01…m05`, `overenie_pevnost/out`). Frame, rest pose and
azimuth convention as §0 (azimuth about +Z from +X, CCW seen from above; "stage az" = pan-stage frame = B frame at pan 0).
Everything printed is ONE tough ABS-like resin (Z2) unless a row says otherwise; `T_svetlovod` may be clear standard resin.
Words "UNVERIFIED" mark catalogue numbers that could not be confirmed (most vendor pages were not reachable from this
session, only search snippets) – the builders model them as written; the user measures the bought part first.

### 17.0 Decisions in one table
| # | topic | decision (numbers in 17.1–17.9) | why / evidence |
|---|---|---|---|
| A1 | slim stage | every permanent stage part r ≤ 26.50; stage leaves upward through the glued ring (r_in 26.748, measured) | D1, M01; a01: ring r_in 26.748, disc r 26.50 |
| A2 | upper bearing | T_stred journal bore r 26.65, z −10.5…−2.0, shoulder at z −2.0 under the ring seat r 28.35 (z −2…4); stage band r 26.37 + PTFE tape 0.13 = 26.50; radial 0.15 | D1; a01: present bore r 28.342 for z −10.5…3.5, tube r 30.6 (merged with the shell at az 90/270, r 34.0) → new tube wall 3.95 |
| A3 | pan gears | BOUGHT m0.8 pair, 18T pinion / 36T gear, C 21.600, PAN_AX unchanged (−5.85, −20.793); face 4.0; both in the plane z −45.90…−41.90 | keeps the RAM servo position; m0.8 brass/steel 4 mm face is a stock series (KHK BSS0.8, McMaster brass 0.8 mod, Accu 0.8MOD, RS PRO steel 0.8); Lewis at L8 50.8 MPa (36T brass) / 62.0 MPa (18T) |
| A4 | gear fixing | 36T: plain brass gear, bore Ø8 H7, BONDED (epoxy) under the printed hub disc, runs on the taped static boss; 18T and the J1 18T: bored metal gear slid over the servo's own metal spline and fixed with anaerobic retaining compound (Loctite 638 class), no printed spline, no horn | no metal horn / spline-bore gear for the STS3032 micro spline 25T Ø4.95 was found; supplied horns are POM (no bond, printed carrier = weak link); J1 has no height for a horn under the cap (17.4) |
| A5 | FFC drum vs full gear | full (not sawn) gear; the drum is a printed C-shroud of P_sachta around the gear tips, r 15.50…16.70, stage az 8…140 | the pinion never reaches stage az 8…140 at r ≤ 16.7 (pinion zone at r 16.7 = 254.3 ± 18.4 − pan) |
| A6 | pan hard stop ±90 | 2 steel pins Ø3 bonded in T_spodok posts at r 30.0, B az 25.43° and 224.57°; stop LUG on the lift module (P_drziak_serva) at stage az 118.3…131.7, r 27.6…31.6, z −47.2…−41.9; engagement 2.6 | the duct annulus is shared by the FFC (back) and the pinion (front) – no lug fits there (17.2.4); the lift module comes out through the door before any service, so its lug never blocks the stage path |
| A7 | pivot + axial retention | static resin boss Ø7.70 (+PTFE tape) on an ALUMINIUM pivot bridge (2.0 sheet, same sheet as the ear) tapped M3; DIN 9021 M3 washer on the boss top overlaps the brass gear top face; axial play 0.10 | D1 principle (screw on the axis, from above); the deck at the axis is a 2.0 plate on the J1 servo – a resin anchor there bends to 10–22 MPa under L1 ×2, the 2.0 Al bridge 18 MPa vs 240 MPa yield |
| A8 | L2 at lift 0 | rest gap foot ↔ hub disc 0.15 (0.10…0.20); foot lands on the hub disc ring r 6.5…12.6 → brass gear → PTFE → bridge/deck → shims → STS3215 case → corner pads | D1; the lift chain is sized for the full 30 N anyway (lift 20 has no landing) |
| A9 | lift | crank = bought aluminium arm on the MG90S spline (spline count UNVERIFIED: measure), Ø2 steel pin bonded at r 10.00; ear = 2.0 Al 6061-T6 / 5754 L-bracket (or 1.5 stainless 304); FOOT = 4 mm aluminium flat bar (20 × 4 stock) | S02/S04: no fastener can be held by a 4.0 resin foot in any horizontal direction (walls 0.35…1.0 measured from the 4.0 height); metal–metal joint (2 × M2 tapped) passes |
| A10 | lift servo seat | pocket gripping both case ends: turret end wall with a keyhole hole (main load path) + bottom-cover end wall + back plate + upper tab screw into a DIN 562 nut; no floor under the case | a floor under the case cannot be ≥ 2.0 (it would sweep over the static FFC wall top −43.0) |
| A11 | cables | stacked PAIR of stock 0.5 mm 5-pole FFC (Type A), 203 mm; carrier ZIF Hirose FH12 (2.0 high), neck ZIF Hirose FH19SC (0.9–1.0 high, takes 0.3 mm FFC); neck board DPS_krk in a slot of the Al foot; lift servo on an inline 1 × 3 (2.54) pigtail | duct height 4.30 (deck top −46.20 … back floor −41.90): 5-pole (3.0) leaves the 1.0 to the static wall top −43.0; 6-pole (3.5) would not |
| A12 | J1 | STS3215 at x −18 shaft down, bottom on 4 corner pads 1.2 over a WINDOW (air) in the cap floor, top shimmed (0.1 strips) under the deck; brass m1 18T on the spline; C 18.00 set by 0.1 shims; stop lug 4 × 4 R1 (or Ø3 steel pin) | S07, S10 (the ≥ 1 mm-air option), P06 |
| A13 | structure | T_ram merged into T_spodok; columns web 3.0, box closure z −52…−34, R ≥ 2 roots; no skirt disc; T_paluba stays the J1 service lid | P03, S08, S11 |
| A14 | fasteners | ISO 7380 M2 × 6 / × 10, M2.5 × 6 / × 8, M3 × 6 (pivot only) + M2 × 6 thread-forming (one-time); bonded brass inserts or DIN 562 nuts; washers under every head on resin | D4 (M3 added for the pivot: an M2.5 washer Ø8 cannot overlap an Ø8 gear bore) |


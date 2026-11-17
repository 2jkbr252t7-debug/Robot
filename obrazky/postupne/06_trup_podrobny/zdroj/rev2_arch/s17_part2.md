### 17.1 Vertical stack on the pan axis (rest, lift 0) – replaces §1.3/7
| z | element | owner | note |
|---|---|---|---|
| −36.50 | neck bottom (B, fixed) | B | foot bonded to the FRONT half only |
| −40.50…−36.50 | **L_pata = aluminium flat bar** 44.6 × 19.6 × 4.0 | pan | Ø11.0 through hole on the axis; DPS_krk slot at the +X end |
| 0.15 | **rest gap** foot ↔ hub disc (0.10…0.20) | – | feeler 0.10 enters, 0.25 does not; correct with a 0.1 PET disc on the hub disc or by sanding the hub disc |
| −41.90…−40.65 | P_sachta hub disc ring r 6.50…12.60 + back floor (same z) | pan | bonded on the gear top face (366 mm²) |
| −45.90…−41.90 | **36T brass gear**, face 4.00, bore Ø8.00 H7 | pan (bought) | plain (no hub) |
| −46.20…−45.90 | PTFE thrust washer 24.0 × 10.0 × 0.30 | ram | on the bridge / deck |
| −48.20…−46.20 | **T_most** (Al bridge, 2.0) in a slot of **T_paluba** (resin deck 2.0) | ram | deck top −46.20 (was −46.00) |
| −48.30…−48.20 | 0.10 shim strips (PET / PTFE 0.1, 2 strips 4 × 30 on the servo top) | ram | absorbs STS3215 height 35.0 ± 0.3 |
| −83.30…−48.30 | STS3215 case (35.0) | ram | as rev. 1 |
| −84.50…−83.30 | 4 corner pads 1.2 (compression only) – **window (air) under the rest of the case** | ram | S10 "≥ 1 mm air" option |
Sum: 4.0 + 0.15 + 1.25 + 4.0 + 0.3 + 2.0 + 0.1 + 35.0 + 1.2 = 48.0 = (−36.5) − (−84.5). No other slack exists; the
0.1 shims and the rest-gap disc are the only adjustments.

Pivot / retention (static parts on the bridge; F15):
| item | geometry |
|---|---|
| pivot boss `T_cap` (separate resin print, RAM) | Ø7.70 cylinder z −46.20…−41.80, root fillet R1.0 (inside the PTFE ID 10.0), bonded on the bridge (epoxy) and clamped by F15; centre hole Ø3.4 through; plain flat top face |
| journal | PTFE tape 0.13 wrapped once on the boss → Ø7.96 running in the gear bore Ø8.00 H7 (radial 0.02…0.07); sand / second wrap to fit (gear turns freely, no shake) |
| retention washer | DIN 9021 / ISO 7093-1 M3 (Ø3.2 × Ø9.0 × 0.8) on the boss top z −41.80…−41.00; overlaps the gear top face r 4.0…4.5; **axial play 0.10** (boss top 0.10 above the gear top; 0.05…0.20 allowed – sand the boss top or add a 0.1 PET disc Ø8/3.2 under the washer) |
| screw F15 | ISO 7380 M3 × 6 (dk 5.7, k 1.65), head z −41.00…−39.35, tip −47.00, into the **tapped M3 hole of the Al bridge** (2.0 thick, 2.6 threads; metal) |
| foot clearance | foot hole Ø11.0 (r 5.5): washer r 4.5 → 1.0 radial; head top −39.35 vs neck bottom −36.50 → 2.85; hub disc ring inner r 6.5 → 2.0 to the washer |
| T_most (bridge) | Al 5754-H22 or 6061-T6 sheet 2.0, rectangle x −6.0…12.0, y −18.0…18.0 (18 × 36), corners R2; tapped M3 at (0, 0); 2 × Ø2.8 at (6.0, ±15.95) for F3; lies flush in a through slot of T_paluba (x −6.1…12.1, y −18.1…18.1); its underside rests on the shim strips over the servo; owner RAM |

### 17.2 Pan drive
**17.2.1 Gears (A3).** m 0.8, pressure angle 20°, 18T pinion (d 14.4, da 16.0) / 36T gear (d 28.8, da 30.4), C 21.600,
PAN_AX (−5.85, −20.793) (unchanged), ratio 2 : 1, both teeth in z −45.90…−41.90, backlash target 0.04…0.08 (pan-servo tab
holes slotted ±0.3, set C on assembly). Lewis (b 4.0): L3 0.6 N·m → Ft 41.7 N → gear 34.6 MPa / pinion 42.2 MPa; L8
(STS3032 stall 4.5 kg·cm = 0.441 N·m at the pinion) → Ft 61.3 N → 50.8 / 62.0 MPa; rated 0.147 N·m → 16.9 / 20.6 MPa.
Brass C3604 allowable taken as 100 MPa static (S01 assumption, UNVERIFIED) → margin ≥ 1.6; steel pinion ≥ 3.
* **36T gear – buy:** plain (hubless) spur gear m0.8 36T, face 4.0, bore Ø8.00 H7, brass (C3604 / CuZn39Pb3) or steel.
  Stock candidates: KHK BSS0.8-36 (brass series m0.5…1, face 4 for m0.8 – shape / bore UNVERIFIED), McMaster brass
  0.8 mod 36T (face 4, hub Ø12 – listing shows an 8 mm bore; UNVERIFIED), Accu 0.8MOD brass A1-type (plain) – part
  number UNVERIFIED. If only a hubbed or Ø5/Ø6-bore gear can be bought: a turner faces the hub off flush and bores Ø8.00 H7
  true to the tip circle (≤ 0.02 runout) – 10 min of lathe work. **The gear is the only part that may need a lathe.**
* **18T pinion – buy:** m0.8 18T, face ≥ 4.0 (teeth must cover z −45.90…−41.90), bore Ø5.00 H7, steel preferred (e.g.
  RS PRO 878-7862: steel, 18T m0.8, bore 5, hub Ø12 – face / hub length UNVERIFIED) or brass (KHK BSS0.8-18). A hub is
  allowed only BELOW the teeth (toward the servo), Ø ≤ 12.0.
**17.2.2 Gear ↔ servo / stage (A4).**
* Pinion on the STS3032 output spline (25T, tip Ø4.95 per reseller listings – UNVERIFIED; check that the spline is
  METAL on the purchased servo): degrease, slide the Ø5.00 bore over the spline, Loctite 638 (or any anaerobic retaining
  compound, gap ≤ 0.25), 24 h. No screw (a head on the pinion top would rise to z −40.3, inside the foot's sweep).
  Engagement = spline length (3.5 modelled) ≥ 3.0. Capacity (10 MPa on π·4.95·3.0) ≈ 1.1 N·m vs stall 0.44 N·m.
  Service: a new servo gets a new pinion (≈ 5 €) or heat the old one to 250 °C to release it.
* **Pan-servo height follows the pinion:** servo boss top = pinion bottom − 0.30. For a plain pinion (no hub) the boss top
  is z −46.20, case z −72.70…−49.70, tabs z −56.50…−54.00, tab-post tops z −56.50. A pinion with a hub of length h
  lowers the servo by h: posts are modelled for h = 0 and shimmed down with M2 washers (0.3 / 0.5) – RAM models the post
  top at −56.50 and a 6.0-deep pocket below the case for h ≤ 6 (case bottom ≥ −78.7, floor −82.3).
* 36T gear on the stage: epoxy between the gear top face and the hub disc / back floor underside (annulus r 6.5…12.6 =
  366 mm² + back floor over r 12.6…15.2 in stage az 8…140), centred by the boss during curing (assemble the stage on the
  deck, gear on the taped boss, cure). Torque L8 0.88 N·m → 0.26 MPa on the bond (2.7 working) ✓. No dowels (F9 deleted).
**17.2.3 FFC drum with a full gear (A5).** The gear stays whole. The drum is a printed C-shroud of P_sachta hanging from
the back floor around the gear tips: r 15.50…16.70 (0.30 to the tip circle r 15.20), stage az 8.0…140.0, z −45.60…−41.90,
end faces radiused R0.6; FFC retaining lip r 16.70…17.50, z −42.50…−41.90 on the same sector. The pinion zone at r ≤ 16.7
is stage az 254.3 ± 18.4 − pan, i.e. never inside 8…140 for pan ±90. The FFC inner run lies on r 16.70.
**17.2.4 Pan hard stop ±90° (A6).** Measured exclusion that drives the layout: the duct annulus r 15.2…25.1, z −46.2…−41.9 is
FFC in the back half and the pinion orbit in the front (stage az 254.3 ∓ 90 ± 22); the deck cannot carry a 6 mm pin under
the J1 servo (2.0 plate); any lug at r ≤ 26.5 would meet the static FFC wall (r 23.5…25.1). Therefore:
* **Pins (static):** 2 × steel dowel Ø3 × 12 (ISO 8734 3 m6 × 12), bonded 6.0 deep (hole Ø3.05–3.10 drilled after curing)
  in posts of T_spodok: pin 1 at r 30.0, B az 25.43° = (27.09, 12.89); pin 2 at r 30.0, B az 224.57° = (−21.37, −21.06).
  Post Ø7.0, top z −50.60, pin top −44.60; pin 1 post stands on the floor (z −82.3…−50.6) with a rib to the cradle back
  wall; pin 2 post is a bracket off the cradle front wall (z −57.6…−50.6, R2 roots), 1.62 clear of the pan-servo tab corner.
* **Lug (rotating, on P_drziak_serva):** block r 27.60…31.60, stage az 118.3…131.7, z −47.20…−41.90, joined to the turret
  end wall of the pocket by a bridge r 27.60…31.60, stage az 106.5…118.3, z −43.60…−39.90; all roots R1.5. Contact: the
  block's CW face (az 118.3) meets pin 1 at pan −90.0, its CCW face (az 131.7) meets pin 2 at pan +90.0; engagement
  z −47.20…−44.60 = 2.60 (2.50 with the 0.10 L1 rise); the bridge bottom is 1.0 above the pin tops; the block bottom is
  1.0 above the cradle wall tops (−48.20). Loads: L3 0.6 N·m → 20 N, L8 (0.88 N·m at the stage) → 29 N; pin bearing
  29/(3 × 2.6) = 3.7 MPa ✓; steel pin bending 29 N × 3.9 = 113 N·mm → 43 MPa ✓; lug root (4.0 × 4.9, lever 3.5): 6.4 MPa
  at L8 nominal → **K12 must confirm ≤ 6 with the R1.5 roots (FE)**, otherwise widen the lug radially to r 27.1…31.6.
* With the lift module out (service) the stage has no hard stop – turn it by hand only.
* Firmware ±85°. The static deck (T_paluba) is trimmed to r ≤ 26.6 inside B az 16…232 (lug sweep).
**17.2.5 Pan servo fixing (F4).** 2 × ISO 7380 M2 × 10 + DIN 125 M2 from above through the tab holes (x ±14.0) and the
post (Ø2.3 clearance, slotted ±0.3 in the C direction) into DIN 562 M2 square nuts in side slots of the posts
(nut slot 4.1 × 1.4, 1.5 below the post top, opening toward ±X). Posts: 6.0 × 7.5, R1 roots, part of T_spodok.

### 17.3 Pan stage (PAN) – slim
* **P_sachta:** every surface r ≤ 26.50 (check on the STL). Well inner 47.0 × 22.0, inner vertical corners R2.5 (corner wall
  1.35 – declared local ≥ 1.2; neck corner clearance 0.59 measured by zjednodusenie m05). End walls and front wall 1.6
  (declared, guide walls), back wall 2.0 (y 11.0…13.0) for x −6…20. Wall lower edges: z −40.90 in stage az 140…368
  (≥ 1.0 above the pinion top −41.90), down to −41.90 in the back sector stage az 5…140. Top plate z −3.50…−2.00
  (collar disc bonded at r > 24 as B). **Journal band** r 26.37 (resin), z −10.00…−3.00 + one PTFE tape 0.13 × 7 wide
  → r 26.50; lead-in chamfer 0.5 at z −10.0. Hub disc / back floor 17.1. Drum shroud 17.2.3. Windows: back window
  x −20.9…−6.5, y 11.0…13.0, z −40.9…−10.9 (ear + flange + crank, 1.0 clearance); end window +X wall y −6.5…6.5,
  z −40.9…−15.0 (FFC moving leg + DPS_krk mouths). F10 pads: on the back wall outer face, face y 15.10, boss r 3.5,
  R1 roots, at (x 19.5, z −31.7) and (x 8.0, z −14.5), bonded M2 inserts (OD 3.2 × 3.0, hole Ø3.3 × 3.3), dowel hole
  Ø2.05 × 3.5 at (x 19.5, z −27.7). Delete: journal drum r 28.07, fin, apron, FPC groove, Ø4.8 tool hole, sealed pockets,
  glue groove (keep a flat glue land r 24…26.5 on the top plate). Vents: the well is open at the bottom; no closed pocket.
* **Lift module (P_drziak_serva + MG90S + crank + ear), removable through the door:** 17.5.
* **PAN_ENV rev. 2** (stage frame, r about Z, any azimuth unless stated):
  | z from | z to | r max | what |
  |---|---|---|---|
  | −47.20 | −41.90 | 31.60 only in stage az 106.5…131.7 (stop lug + bridge); elsewhere 17.50 | drum + lip |
  | −41.90 | −40.90 | 26.50 in stage az 5…140; 12.60 elsewhere; plus the lift module (stage az 35…140) to 33.40 | back floor / hub disc |
  | −40.90 | −17.00 | 33.40 | lift servo corner (16.0, 29.3) r 33.38 |
  | −17.00 | −11.50 | 32.20 | lift module top, ear at TDC |
  | −11.50 | 4.00 | 26.50 | journal, top plate, collar disc |
  Shell margin (inner half depth b_i, a01): z −40.9: 37.5; −22: 35.60; −17: 34.64 → 1.24; −11.5: 33.36 → 1.16. Column
  inner face x 34.4 → 1.00 to r 33.40. FFC lift loop r ≤ 31.7 and the pigtail loop r ≤ 31.4 are inside.

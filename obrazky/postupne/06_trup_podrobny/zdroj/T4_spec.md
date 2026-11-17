# T4 – NOVA mini torso: detailed design specification (rev. 1, lead architect)

Single source of truth for the numbers: **`/tmp/claude-0/gapwf/fin/T4/t4_common.py`** (constants, exterior, cached BREP,
helpers, envelopes). This document explains them. If a number here and in `t4_common.py` differ, `t4_common.py` wins –
report the difference. Fit study: `fit/fit2.py` → `fit/fit_report.json`, `fit/head_check.py` → `fit/head_check.json`.

**Frame (B frame):** mm, Z up, x = robot LEFT (+) / RIGHT (−), FRONT = −Y, J1 axis = PAN axis = Z axis, torso top = collar
top **z = +4**. `z_B = z_world(pack) − 129`. All parts are modelled and exported in the REST pose (lift 0, pan 0, J1 0).
"Azimuth" = angle about +Z from +X, counter-clockwise seen from above (front = 270°, back = 90°).
"Inset w" = true normal distance w inside the outer surface (`inner_section(z, w)`, `inner_solid(w)`).

---------------------------------------------------------------------------------------------------------------------

## 1. Fit study – what the new shell does to the pack, and how each conflict is solved

Method: every pack part (boxes / cylinders of `T1/pack/layout.json`, shifted by −129) and every T4 envelope
(`t4_common.envelopes()`) is sampled on its surface (0.7–1.0 mm), pan-stage parts are rotated over pan −85…85 (5° steps),
lift parts additionally raised 0…20 (2.5 steps), and the signed distance to the INNER surface of the T4 shell (true
offset 2.2 of the exterior, KD-tree on 1.5 M surface points) is evaluated. Static↔moving gaps use exact box / cylinder
distances.

### 1.1 Pack layout in the new shell ("before") – worst items
| pack part | clearance to the shell inner surface | where | verdict |
|---|---|---|---|
| L_noha (ear of the neck foot, r 35.85) | **−2.32** | (0, 35.8, −11.9), pan −30, lift 20 | 3.3 short of the 1.0 rule → conflict 1 |
| P_kluka (crank sweep disc, r 35.6) | **0.17** | (0, 35.4, −21.9), pan −25 | 0.8 short → conflict 1 |
| T_horny_kruh (journal ring r 31.5) | **−0.62** | (0, 31.5, −3.5) | collides in ±Y → conflict 2 |
| T_svetlo, T_reproduktor | −3.37 / 0.20 | front | re-positioned with the new front (section 4.6) |
| T_kabel_ramena, T_paka (shoulder) | −2.28 / 0.01 | (±43, 4…5, −5…−10) | shoulder redesigned for x_sh 46.76 → conflict 4 |
| T_riadenie, T_ram_J1, T_STS3215 | 0.70 / 0.30 / 0.80 | low back / cap corners | re-packaged (conflict 4, section 6) |
| pan stage well, lift servo, FPC loop | 2.74 / 5.41 / 5.41 | – | fine |

### 1.2 The five known conflicts
**1. Depth in the back (lift module) – solved inside the lift module, NO exterior change, NO relief.**
Shell inner half depth b_i(z) (x = 0): −11.9: 33.46 · −14: 33.98 · −18.3: 34.92 · −22: 35.60 · −30: 36.72 · −38: 37.38.
The pack reach r 35.85 comes from the yoke ear, whose far end sits at y 31 because the crank pin sweeps the BACK half.
Changes (pan-stage frame):
* the crank now sweeps the **FRONT half** (pin path from bottom dead centre through y = Y_LIFT − 10 to top dead centre):
  the ear only has to reach y = Y_LIFT + 1.9;
* lift servo shaft moved from (y 19.1, z −24.2) to **(y 23.2, z −24.2)**; case x −7.8…15.0 → **−6.5…16.0**
  (y 17.1…29.3, z −41.1…−18.3); crank arm plane x −17.0…−14.5; ear plate x −18.0…−15.5 → **−19.9…−17.4**,
  ear far end y 31.0 → **25.1** with a 1.5 chamfer on its top far corner;
* at mid stroke the crank tip (r 12.2 about the shaft) reaches y 11.0 – it enters the window of the well back wall and
  stays 1.0 from the neck blade (y 10.0).
Result: sweep radius 35.85 → **33.38** (servo corner, z ≤ −18.3) / **32.03** (ear, up to z −13.4) / 30.9 (ear top at
TDC, z −11.9). Swept clearance to the shell (fit study B1): lift servo **1.51**, ear end **1.76**, ear 2.51, crank 3.0.
Declared swept envelope: `PAN_ENV` (section 12); its margin to b_i is ≥ 1.16 everywhere.

**2. Narrow top / journal – the journal bearing moves from the chassis into T_stred (hard reason below).**
The journal Ø56.4 at z −10.5…−4.5 needs a ring of r ≥ 30.0; b_i there is 33.09…31.21, so a chassis ring r 31.5 does not
fit (−0.62). More fundamental: the white centre band is tucked under at the bottom (inner half depth of the white lip at
z −81: 27.30 at x 0, 24.36 at x 25, 20.25 at x 33). A chassis that carries a Ø56.4 journal (or even only the Ø56.4 pan
stage) **cannot pass through that 54.6 mm opening**, and the side openings (half depth 23.4 at z −10.5) do not let it in
either. Therefore:
* T_stred carries ONE bore **Ø56.70 (r 28.35) from z +4 down to z −10.5** in a "collar tube" (outer r 30.6, wall 2.25,
  hanging from the top wall, merged with the shell where the shell is closer than 1 mm). Its upper 6 mm (z −2…4) is the
  glue seat of `golier_prstenec` (unchanged, 0.1 seam); its lower part (z −10.5…−4.5) is the plain bearing of the pan
  journal (journal r 28.20 incl. 0.13 PTFE tape, radial running clearance 0.15).
* The pan stage (max r 28.20) is dropped in **from above through this bore** after T_stred is mounted; the lift servo
  module is attached afterwards through the door.
* The chassis keeps the bottom pivot (Ø6 pin on the deck, 37 mm below the journal centre) and everything else.

**3. Shoulder shelf vs head – no reshaping, no pan-dependent table needed (numeric pre-check, to be confirmed by K9).**
`fit/head_check.py` (280 k real head vertices of hlava_skrupina, ram_displeja, displej, usi, led_kruzky against the T4
exterior incl. the shoulder joints, pan −85…85 step 5, tilt in 5° steps inside the B table):
| lift | B table (down / up) | min gap to the white shell | min gap over the collar plateau (r < 29.6) |
|---|---|---|---|
| 20 | +40 / −40 | 2.43 | 2.51 |
| 12.5 | +30 / −40 | **0.53** (at +30°; 1.83 at +27.5°) | 0.58 |
| 7.5 | +20 / −30 | 0.77 | 0.81 |
| 0 | +5 / −10 | 0.86 | 0.78 |
The minimum is always at the rim (r ≈ 30) and does **not depend on pan** (spread ≤ 0.02): where the head's lowest edge
is over the wide ±X shelf the shelf has already dropped by more than the head rises. The 0.5 criterion is met with only
0.03 margin at lift 12.5 / +30° (vertex based, mesh tolerance 0.02) – if the BVH check K9 finds < 0.5 there, the
firmware table gets ONE changed row: lift 10…15 → tilt down ≤ 27.5° (all pans). Nothing else changes.

**4. Wider body – use of the 16 mm.** Shoulder columns stand at |x| 34.4…42 (outside the centre band, so T_stred can
be lowered past them); the 5 V buck + 470 µF sit on the right column, the amplifier on the left column, inside the side
caps; the controller stands behind the J1 cradle (door access). The side zone |x| > 34.4 also takes the stop ring and
the neck of the shoulder joints. Minimum static clearances to the shell: column 0.76, stop ring 0.80, buck 2.97,
capacitor 2.10.

**5. Top rim / collar seat.** Top section = circle **r 29.6** at z 4 (flat white rim 1.25 wide around the bore r 28.35).
The rim blends into the T3 profile with d(x) = d_T3(x) − c·(x_m − x)²: X direction c 0.0153, x_m 33.3 (identical to T3
from drop 1.26); Y direction c 0.3013, x_m 31.0 (identical from drop 2.59). The profile stays convex. Declared deviation
zone: drop < 2.6 (z > 1.4), max 1.2 mm horizontally at the rim edge (0.5 mm normal to the surface), 0.0000 outside.

### 1.3 Three more conflicts found by the fit study
**6. T_stred cannot be lowered over a full pack chassis** (see 2). Rule for the RAM builder: everything on the
tower inside |x| ≤ 33.3 and above z −81 must fit the white lip outline with 0.5 clearance (`TOWER_CLEAR`); below z −78
it must fit the cap tub. Exceptions, both solved: the pan servo (front face y −27.04, tab corners at x ±16.25: lip gap
−0.67) → local relief of the front lip (`LIP_RELIEF`: inner half depth ≥ 27.55 for |x| ≤ 16.75; needed only for
z −81…−80.2, remaining wall ≥ 1.5); the pan pinion (tip y −28.8, gap −1.58) → pressed on from above through the bore
AFTER T_stred. Tower-vs-lip gaps after these: plug 1.31, FPC channel 2.20, controller 2.35, deck ≥ 3.7.

**7. Vertical stack.** The cap underside is at z −84.5 (pack torso bottom −86.0), the neck bottom stays at −36.5: 1.5 mm
less height and a thicker foot are absorbed by: servo pocket 1.0 deep in the 2.2 floor (floor 1.2 under the servo),
no hub flange between gear and well, foot gap 0.5 at rest. Stack: 1.2 + 35.0 + 0.5 foam + 1.8 deck + 0.3 PTFE +
3.5 gear + 1.2 hub/floor + 0.5 + 4.0 foot = 48.0 = (−36.5) − (−84.5). No slack: measure the real STS3215 (35.0 ± 0.3)
and choose the foam (0.3 / 0.5 / 0.8).

**8. Pan pinion under the rotating well.** With the compressed stack the well floor would sweep 0.1 mm over the static
pan pinion (top −42.3). Rule for the PAN builder: below z −41.3 (`Z_WALL_BOT`) the stage may only occupy r ≤ 12.6
(`R_HUB`, hub disc z −42.2…−41.0) or the back sector (stage azimuth 5°…140°, `STAGE_BACK_AZ`), and there not below
z −41.9 outside r 15.9 (1.0 above the FPC channel wall, top −42.9). Result: well ↔ pinion 1.00, floor ↔ FPC wall 1.00.

### 1.4 T4 layout ("after") – minimum clearances (fit_report.json)
| check | minimum | where |
|---|---|---|
| static tower parts ↔ shell inner (wall 2.2) | 0.48 column foot (tub 0.28 fit), 0.76 column, 0.80 stop ring | – |
| pan stage / lift ↔ shell, pan −85…85 × lift 0…20 | **1.51** lift servo corner (pan 30) · 1.76 ear end (pan −40, lift 20) | need ≥ 1.0 |
| pan stage / lift ↔ static parts | **1.00** well ↔ pan pinion · 1.00 floor/bracket ↔ FPC channel · 1.03 lift servo ↔ left column · 1.40 ear ↔ collar tube · 1.44 FPC loop ↔ LED box | need ≥ 1.0 |
| lift parts ↔ pan-stage parts over the stroke | 1.01 neck ↔ crank tip · 1.02 ear flange ↔ bracket · declared fits: crank ↔ ear side gap 0.4, foot ↔ hub 0.5 at rest | – |
| stage through the bore r 28.35 | 28.20 journal, 28.09 well corners | – |
| shell b_i − PAN_ENV | 1.16 (z −11.5) | need ≥ 1.0 |

### 1.5 Exterior changes (all)
| # | zone | change | size | reason |
|---|---|---|---|---|
| D1 | top rim, drop 0…2.6 | flat rim r 28.4 → 29.6 + blend | ≤ 1.2 horizontal, ≤ 0.5 normal | printable white rim (brief §3) |
| D2 | under the cap (z < −84.5) | plinth r 24.0 as T3, plus a black skirt disc r 28.5, z −86.2…−85.2 | +4.5 radius, 1.0 thick, 0.7 below the cap | covers the J1 pinion orbit (r 28.0) |
| D3 | white/black seam | cap edge at z −81.5 (seam 0.5; T3 drew 0.12) | 0.4 | seam rule |
No other deviation: the white surface is the T3 surface (loft error ≤ 0.006 mm on the white part, ≤ 0.024 on the cap).
The speaker centre is 3.0 below the grille slot (inside); slot, light bar, door, seams, joints are at the T3 positions.

---------------------------------------------------------------------------------------------------------------------

## 2. Architecture and assembly concept (refinement of brief §4)

```
            z +4   collar disc (P) + ring (T)                 bore r 28.35 = ring seat + journal bearing (T_stred)
          −4.5…−10.5  journal r 28.2 (P_sachta)
   pan stage P: well 47×22, lift MG90S + crank behind it (y 17…29), ear/foot L inside/behind the well
          −41.0  well floor (hub r 12.6) ── −42.2 … −45.7 pan gear 36T + drum ── PTFE ── −46.0 deck top
   tower T (T_ram + T_paluba on T_spodok): deck −47.8…−46.0, J1 STS3215 −83.3…−48.3 (shaft down at x −18),
          pan STS3032 in front (shaft up at (−5.85, −20.79)), controller behind, columns at |x| 34.4…42
          −82.3 cap floor ── −84.5 cap underside ── plinth r 24 / skirt r 28.5 ── gears −90.0…−86.8 ── 6805 −98…−91
```
* **T_spodok** (black resin) is the base plate: floor + tub + spigot + plinth with the 6805 seat.
* **T_ram** (PETG, one part): cradle around the J1 servo, pan-servo posts, controller standoffs, two shoulder columns.
  **T_paluba** (PETG): deck with the pan pivot pin, FPC channel, stop groove; clamps the J1 servo.
* **T_stred** (white resin, one arch part: front + top + back) with the collar tube, door frame, front-stack bosses and
  4 screw bosses; it is lowered **straight down** over the tower (which is why the tower is slim in Y, see 1.3/6) and
  fixed by 4 × M2.5 from below through the cap floor.
* The **pan stage** then drops in from above, the **lift servo** goes on through the door.
* **T_bok_L / T_bok_P** slide on along ∓X, located by the cap spigot + 8 seam tabs each, and are clamped by the black
  shoulder joints **T_klb_L / T_klb_P** (3 × M2 each, hidden by the arm).
* **T_dvere**: 2 hook tabs at the top edge + frame ledge + 4 magnet pairs.
Deviation from brief §4 with a hard reason: the journal ring is part of T_stred, not of the chassis (1.2/2);
T_stred is lowered over the tower *without* pan stage, pan pinion and lift module (1.3/6).

---------------------------------------------------------------------------------------------------------------------

## 3. Part list

Owner = module that builds the part (`t4_obal.py` / `t4_ram.py` / `t4_pan.py`). Group: T static torso, P pan stage,
L lift (on P), Z base dummy. Names = registry keys (Slovak, no diacritics). Resin = MSLA, PETG = FDM.

### 3.1 Printed parts
| name | owner | grp | material | description |
|---|---|---|---|---|
| T_stred | obal | T | resin white | centre band |x| ≤ 33.05, z −81…4: collar tube/bore, door opening + frame ledge + 4 magnet pads, light-bar and grille openings, 2 LED bosses, 3 speaker bosses, 4 screw bosses, front lip relief |
| T_bok_L, T_bok_P | obal | T | resin white | side caps |x| ≥ 33.55: socket tube + seat flange, 8 seam tabs each |
| T_dvere | obal | T | resin white | back door 56 × 60 r10, 2 hook tabs, 4 magnet bosses |
| T_klb_L, T_klb_P | obal | T | resin black | shoulder joints (flange Ø27, step Ø22), neck, screw + magnet pockets, bush bore, wire groove |
| T_puzdro_L, T_puzdro_P | obal | T | POM (or tough resin) | spline bushes of the arm servos, friction flange |
| T_svetlovod | obal | T | resin clear (frosted) | light guide plug + flange |
| T_mriezka | obal | T | resin grey | grille plug (5 slots 0.8) + flange |
| T_drziak_led | obal | T | resin black | light box / LED PCB holder |
| T_drziak_repro | obal | T | PETG black | speaker clamp ring |
| T_spodok | ram | T | resin black | bottom cap: floor, servo pocket, tub, spigot, plinth + bearing seat + skirt, stop lug, pads |
| T_ram | ram | T | PETG | cradle, pan-servo posts, controller standoffs, columns with shoulder bosses |
| T_paluba | ram | T | PETG | deck, pivot boss, FPC channel wall, stop groove |
| Z_naboj_test | ram | Z | PETG | dummy stand: plate, hub post Ø25, stop block |
| P_sachta | pan | P | resin black (tough) | well + journal drum + stage top + hub/back floor + bracket pads |
| P_koleso | pan | P | resin tough | pan gear m0.8 36T sector 200° + drum r 15.7; bonded to the hub disc of P_sachta |
| P_drziak_serva | pan | P | PETG | lift servo bracket |
| P_kluka | pan | P | resin tough (or PETG) | crank r 10, hub for the 21T spline |
| L_pata | pan | L | PETG (100 %) | neck foot 44.6 × 19.6 × 4, FPC tab |
| L_ucho | pan | L | POM (or PETG) | yoke ear with flange |

### 3.2 Finished parts of variant B that mate with the torso (not rebuilt, not changed)
`golier_prstenec` (T, glued into the T_stred bore), `golier_kotuc` (P, glued on the stage top),
`krk_predna_polovica` / `krk_zadna_polovica` (L).

### 3.3 Bought parts (model at datasheet size as simple solids; the seats carry the tolerance)
| name | owner | grp | part, modelled size (mm) | source of the dimension, tolerance |
|---|---|---|---|---|
| servo_J1 | ram | T | Feetech STS3215: case 45.2 × 24.7 × 35.0, boss Ø12 × 2.6, 25T Ø5.9; plug zone 11.3 × 16 × 18 at the +X end | pack (DFRobot / Mouser listings), ±0.3; seat +0.2 per side, x slot ±0.3 |
| pastorok_J1 | ram | T | brass spur m1 18T, face 3.2, hub Ø10 × 0.9, 25T bore, M3 countersunk | catalogue gear, faced; da 20.0, d 18.0 |
| Z_koleso_J1 | ram | Z | brass spur m1 18T, face 3.2 (sun) | same |
| lozisko_6805 | ram | T | 6805-2RS 25 × 37 × 7 | ISO 15; seat Ø37.00 +0.05/0 (+ CA), hub Ø25.00 −0.02/−0.06 |
| servo_pan | ram | T | Feetech STS3032: case 23.5 × 12.5 × 23.0, tabs 32.5 × 12.5 × 2.5 (16.2 above the bottom), holes Ø2.2 at 28.0, boss Ø12.4 × 3.5, plug 7 × 8 × 8 | pack (listings, medium confidence), ±0.3 – verify on the purchased servo |
| pastorok_pan | ram | T | spur m0.8 18T, face 3.2, hub Ø8 × 2.2 (POM or brass) | da 16.0, d 14.4 |
| cap_pan | ram | T | steel dowel Ø6 h6 × 6.5 | ISO 2338 |
| ptfe_podlozka | ram | T | PTFE washer 24 × 12.4 × 0.3 | cut from sheet |
| DPS_riadenie | ram | T | carrier 48 × 22 × 1.6 + parts to 7.0 total, with Waveshare ESP32-S3-Zero 23.5 × 18 × 5 | Waveshare drawing, ±0.2 |
| menic | ram | T | Pololu D36V28F5 17.8 × 17.8 × 8.8 | Pololu drawing |
| zosilnovac | ram | T | MAX98357A breakout 19.3 × 17.8 × 3.0 | Adafruit 3006 |
| kondenzator | ram | T | 470 µF / 10 V, Ø10 × 13 envelope | generic radial |
| reproduktor | obal | T | Ø28 × 5.0, 8 Ω 1.5 W | generic; seat Ø28.3 |
| DPS_led | obal | T | 30 × 4.0 × 0.8, 6 × WS2812B-2020 at 5.0 pitch | custom / cut strip |
| magnety_dvere | obal | T | 8 × N52 Ø5 × 2 | – ; pockets Ø5.1 × 2.1 |
| magnety_klb | obal | T | 6 × N52 Ø3 × 2 | – ; pockets Ø3.1 × 2.1 |
| pruziny_klb | obal | T | 4 × disc spring DIN 2093 10 × 5.2 × 0.4 | DIN 2093 |
| servo_zdvih | pan | P | MG90S (E2 model of the neck): case 22.5 (bottom→gear face) × 12.2 × 22.8, shaft 5.9 from the end, turret Ø11.8 × 6.0 + lobe r 2.9 at 5.6, spline Ø4.8 × 3.0, ONE tab kept (2.5 thick, 16.0…18.5 above the bottom, 4.85 long, hole Ø2.2 at 2.45) | user drawing + E2 (`electronics_dims.md`), ±0.3; tab height ±1 (slotted seat) |
| cap_kluky | pan | P | steel dowel Ø2 m6 × 5.4 | ISO 2338 |
| koliky_kolesa, kolik_ucha | pan | P / L | steel dowels Ø2 × 4 (2 ×, gear joint) and Ø2 × 5 (ear location) | ISO 2338 |
| kolik_dorazu | pan | P | steel dowel Ø2 × 4.5 (pan stop) | ISO 2338 |
| fpc_pan | pan | P/L | custom 2-layer polyimide FPC 3.0 × 0.12, 8 traces | pack §2 |
| ptfe_pasiky | pan | P | 4 strips PTFE tape 3 × 30 × 0.13 in the well, 1 band 5 × 177 on the journal | – |
| screws, inserts | each | – | section 10 | ISO 4762 / 10642 / 7380, brass inserts |

---------------------------------------------------------------------------------------------------------------------

## 4. Shells (OBAL)

### 4.1 Exterior functions and cached solids (`t4_common`)
`prof(drop)`, `outer_section(drop)`, `inner_section(z, w)`, `outer_r`, `y_surface`, `x_surface`, `clearance_to_shell`.
Cached BREP (build time 44 s in total, all valid single solids):
| function | content | mesh volume |
|---|---|---|
| `outer_solid()` | full exterior z −84.5…4 (loft of 50 sections × 120 points) | 530 858 |
| `inner_solid(2.2)` | cavity, true offset 2.2, z −82.25…1.75 (42 sections); other insets are built and cached on demand (`inner_solid(2.4)`, `inner_solid(4.0)`; z range `inner_z_range(w)`) | 460 230 |
| `shell_white()` | exterior above z −81 minus the cavity | 60 527 (71.4 g) |
| `stred_blank()` | band |x| ≤ 33.05 | 34 100 |
| `bok_blank(±1)` | caps |x| ≥ 33.55 | 12 966 / 12 967 |
| `cap_blank()` | SOLID black cap body z −84.5…−81.5 | 12 153 |
Wall thickness of the lofted shell: 2.192…2.225 (5 400 mesh vertices); top wall ≥ 2.25.
**Use `mesh_volume()` for masses** – OCC's `shape.volume` is wrong by up to 4 % on these B-spline shells.
Boolean timings on the blanks (`fit/smoke.py`, one core): + tube 13 s, − bore 4 s, − door opening 21 s, − light bar and
grille 31 s, door = shell ∩ prism 22 s, socket hole 4 s, socket tube ∩ exterior 8 s, cap features 2–6 s each; every
result was one valid solid.
Rules: add features with planar / cylindrical cutters; clip every inward add-on with `& outer_solid()` (never offset the
loft); keep faces 0.3–0.4 away from coincidence with loft faces; fillet before booleans.

### 4.2 Seams
| seam | geometry |
|---|---|
| centre band / side caps | planes x = ±33.05 (band) and ±33.55 (caps): gap 0.50 over front, top, back |
| white / black | white ends in the plane z = −81.0, black cap starts at z = −81.5: gap 0.50 |
| door | door outline 56.0 × 60.0 r 10.0, opening 56.5 × 60.5 r 10.25 (centre x 0, z −42): gap 0.25 all round; both cut with prisms along Y (`door_prism(grow)`) through the BACK wall only (y > 5) |
| collar | bore r 28.35 / ring r 28.25: 0.10 glue seam (B) |
| shoulder | socket hole r 14.0 / joint r 13.5: 0.50 |
| light bar, grille | opening 31.0 × 4.2 / 21.0 × 3.2 pills, plugs 30.6 × 3.8 / 20.6 × 2.8: 0.20 |

### 4.3 T_stred
* Start from `stred_blank()`.
* **Collar tube:** add the SOLID cylinder `cyl_z(30.6, −10.5, 1.75)` (it overlaps the top wall above z ≈ 1.4), fill
  gaps < 1.0 between tube and shell (±Y), then cut the bore `cyl_z(28.35, −10.6, 4.1)` (never add a tube whose bore
  face coincides with the later cut). Bore tolerance Ø56.70 +0.10/0, lower
  edge chamfer 0.5 × 45° (lead-in for the stage). 6 ribs 1.6 thick from the tube to the top wall at azimuth
  0°, 180°, ±50°, ±130° (inside r 38, above z −9).
* **Door opening:** `− door_prism(0.25)`. **Frame ledge** (`DOOR_LEDGE`): band from 2.0 outside to 2.0 inside the
  opening edge, located between inset 2.4 and inset 4.0 behind the door and fused to the wall outside the opening.
  Tested recipe (`fit/smoke2.py`: each part 38 s, fusing both to the opened band 128 s, one valid solid, so fuse the
  ledge once, as the last loft-derived add-on): inside part `(inner_solid(2.4) − inner_solid(4.0)) & (door_prism(0.25) −
  door_prism(−1.75))`; outside part `(inner_solid(2.0) − inner_solid(4.0)) & (door_prism(2.25) − door_prism(0.25))`
  (it overlaps the wall by 0.2 – do NOT build a 0.2 mm sliver between inset 2.2 and 2.4).
  The ledge is **omitted along the top edge for |x| < 18** (pan sweep).
  **Magnet pads** (4): at (x ±25.0, z −24.0) and (x ±25.0, z −60.0): pads Ø8 between inset 4.7 and 7.2 with a pocket
  Ø5.1 × 2.1 opening toward the door (outward), joined to the ledge.
* **Front openings:** `− pill_prism_y(31.0, 4.2, 0, −32.5, −60, −30)` and `− pill_prism_y(21.0, 3.2, 0, −48.0, −60, −30)`.
* **Front-stack bosses** (inside, on the front wall, all clipped by the wall): LED holder: 2 bosses r 2.5 at
  (x ±19.5, z −32.5), axis Y, pilot Ø1.7 × 5 (M2 thread-forming), boss face at y = −33.0. Speaker: 3 bosses r 2.5 on
  r 16.5 about (x 0, z −51.0) at 90°, 210°, 330° in the x–z plane, face at y = −31.6, pilot Ø1.7 × 5.
* **Screw bosses** (4): axis Z at (±29.0, ±19.0), r 3.2, z −81.0…−75.0, each tied to the wall by a 2.0 web in the y–z
  plane; insert M2.5 × 4.0 (OD 3.5, hole Ø3.6, glued) opening downward at z −81.0.
* **Front lip relief** (`LIP_RELIEF`): cut the inside of the front lip with a vertical box x −16.75…16.75,
  y −27.55…−20, z −81.1…−79.5 (only touches z < −80.2; remaining wall ≥ 1.5 normal).
* Side edges: plain planes; lower edge: plane z −81.0. No holes through the top, front, sides, back other than listed.

### 4.4 T_bok_L (T_bok_P = mirror in x)
* Start from `bok_blank(+1)`.
* **Socket:** hole `cyl_x(14.0, 40.6, 60, y 3, z −17)`; socket tube = `cyl_x(16.0, 39.1, X_SH, 3, −17) & outer_solid()`
  minus the bore; **seat flange** x 39.1…40.6 with hole r 11.25 and a notch 3.0 wide to r 13.2 at azimuth 270° (wire).
  Seat faces: x = 39.1 (rests on the column stop ring) and x = 40.6 (clamped by the joint shoulder).
* **Seam tabs** (8): on the cap edge x = 33.55, each 8.0 long along the seam, 1.6 thick, 2.5 deep (x 33.55 → 31.05),
  outer face = straight extrusion along X of the cap's inner edge outline moved 0.15 inward (so the cap can slide on
  along X; no undercut): front at z −20, −45, −70; back at z −20, −45, −70; top at y ±12.
* Lower edge: plane z −81.0, located on the cap spigot (4.5.2).

### 4.5 T_dvere
* `(shell_white() & door_prism(0.0))`, back wall only → curved panel 2.2 thick, x ±28.0, z −72…−12.
* **Hook tabs** (2): x 12.0…20.0 and −20.0…−12.0, lying between inset 2.4 and 3.6, z −12.0…−9.5, joined to the door
  by a 2.4 thick root (z −14.5…−12.0, inset 2.2…3.6). Inner corner radius 33.44 ≥ PAN_ENV 32.2 + 1.0.
* **Magnet bosses** (4): Ø8 × 2.3 on the inner face at (x ±25.0, z −24.0 / −60.0), pocket Ø5.1 × 2.1 from the inside;
  magnets Ø5 × 2 glued, polarity checked against the pads (air gap 0.2).
* Mounting: hook the top under the wall, swing the bottom in; removal with a suction cup (as the head's front module).

### 4.6 Front stack (all shell-mounted, owner OBAL)
Front wall at x 0: outer y −39.17 / inner −36.96 at z −32.5; outer −39.99 / inner −37.79 at z −48.
| part | geometry |
|---|---|
| T_svetlovod | plug 30.6 × 3.8 pill, front face flush with the exterior (cut with `outer_solid()`), flange 35 × 8 × 1.2 behind the wall (inset 2.2…3.4), glued |
| T_drziak_led | light box in `LED_BOX` x ±17.5, y −36.6…−30.1, z −36.0…−29.0 (walls 1.2, white inside), 2 ears for M2 × 6 into the LED bosses |
| DPS_led | 30 × 4.0 × 0.8, PCB front face at y −30.9, LEDs face −Y, 4.7 mm air gap to the guide; JST-SH 3p pigtail 90 mm |
| T_mriezka | plug 20.6 × 2.8 pill with 5 vertical slots 0.8 wide, flange 25 × 7 × 1.2, glued |
| reproduktor | Ø28 × 5.0, axis Y through (x 0, z **−51.0**), y −36.6…−31.6, foam ring 1.2 to the wall; T_drziak_repro (ring Ø32 / Ø26 × 1.6 behind the magnet side, 3 ears) with 3 × M2 × 6; JST-PH 2p pigtail 90 mm |

### 4.7 Drain / vent holes, printing
No shell has a closed pocket: T_stred vents through the bore, the caps through the socket, the cap through the boss
hole. Two Ø3 holes in the cap floor at (±33.0, −8.0) drain condensate / cleaning fluid and vent the speaker volume.
Orientation: T_stred top down, tilted 20° about X, supports only inside; caps open side up, tilted 25°;
door inner face to the plate; T_spodok underside up, tilted 15°. All parts fit 218 × 123 × 220.

---------------------------------------------------------------------------------------------------------------------

## 5. Bottom cap, J1 and the base interface (RAM)

### 5.1 Stack below the deck
| z | content |
|---|---|
| −46.0 / −47.8 | deck top / underside |
| −48.3 | STS3215 case top (foam 0.5 above it) |
| −83.3 | STS3215 case bottom = pocket floor (pocket 1.0 deep in the 2.2 floor) |
| −82.3 | cap floor top (`Z_FLOOR`) |
| −84.5 | cap underside (flat inside the superellipse a 38.0, b 24.6, n 2.70) |
| −85.9 | STS3215 boss end (boss Ø12 through a floor hole Ø14.4, slotted ±0.3 in x) |
| −85.2 / −86.2 | skirt disc r 28.5 top / underside (0.6 above the pinion teeth) |
| −86.0 | **top plane of the future base** (gap 1.5 to the cap) |
| −85.9 … −86.8 | pinion hub Ø10 |
| −86.8 … −90.0 | gear plane: pinion m1 18T at (−18, 0) + sun m1 18T on the axis, tip r 10.0, C 18.00 |
| −91.0 … −98.0 | 6805-2RS |
| −98.0 … −100.0 | J1 stop lug (r 18.5…21.0, 2.5 wide, azimuth 90°) |

### 5.2 T_spodok
* Body: `cap_blank()` (exterior z −84.5…−81.5).
* **Spigot** (locates T_stred and both caps): ring between the superellipses (41.15, 27.09, n 2.66) and
  (39.55, 25.49, n 2.66) (`se_prism`), z −81.5…−78.0; radial fit to the white lip 0.21…0.28. Gaps 8.0 wide at the 4
  T_stred bosses. Upper outer edge chamfer 0.6.
* **Tub:** inside the spigot the floor top is the plane z −82.3 (cut `se_prism(39.55, 25.49, 2.66, −82.3, −78)`).
* **Servo pocket:** box x −30.0…16.2, y −12.55…12.55, z −83.3…−82.3 (servo ±0.3 in x, 0.2 per side in y);
  boss hole = slot Ø14.4, centres (−18.3, 0)…(−17.7, 0), through the floor.
* **Plinth** (rotating foot ring): `tube_z(24.0, 17.0, −91.0, −84.5)` + bearing ring `tube_z(21.0, 18.5, −98.0, −91.0)`;
  bearing seat Ø37.00 +0.05/0 × 7.0, shoulder r 17.0…18.5 at z −91.0, entry chamfer 0.4; **pinion notch**: cut
  `cyl_z(10.8, −90.6, −86.3, −18, 0)` out of the plinth wall (teeth zone only); above z −86.3 only the boss slot
  (r 7.2, centres x −18.3…−17.7) goes through skirt, plinth top and floor.
* **Skirt:** disc r 24.0…28.5, z −86.2…−85.2, with the boss slot r 7.2 about (−18, 0).
* **Stop lug:** r 18.5…21.0, 2.5 wide, at azimuth 90°, z −100.0…−98.0.
* **Pads** on the floor under the 4 T_stred bosses: r 3.2, z −82.3…−81.0 at (±29, ±19), hole Ø2.8, countersink for
  M2.5 from below.
* Holes through the floor: 4 × T_stred, 6 × T_ram (section 10), J1 FPC slot x −3.4…3.4, y 21.6…23.0 (continues down
  through the plinth wall to z −91), 2 drain holes Ø3.

### 5.3 J1 drive
STS3215 output axis at **(−18.0, 0)**, shaft down; case x −29.5…15.7, y ±12.35; plugs at the +X end (x 15.7…27.0,
|y| ≤ 8, z −66.3…−48.3). Centre distance adjustment: the servo slides ±0.3 in x in the pocket; an M2.5 × 8 set screw in
the cradle −X end wall at (−30.8, 0, −65) pushes it against a 1 mm foam pad at the +X end; the deck clamps it.
Backlash target ≈ 0.2° (0.03 mm at the pitch circle). Pinion: 25T bore engaged 3.5, M3 × 8 countersunk from below,
flush. Range ±150° firmware / ±155° stop (lug against the base stop block spanning 270° ± 21.4°).

### 5.4 Interface for the future base (frozen here)
* Axis Z. Bearing 6805: inner ring Ø25 on the base hub between z −98.0 and −91.0; the hub must snap / screw so that the
  torso can be pulled off (pack: 3-finger collet, ≈ 30 N).
* Fixed sun gear m1 18T on the hub, gear plane z −90.0…−86.8, slip clutch ≈ 0.25 N·m below it.
* Base top plane z ≤ −86.0; opening r ≥ 29.0 around the axis down to z −91.0 (pinion orbit r 28.0); below z −91 the
  rotating foot ring is r 21.0 (the J1 FPC inner run wraps on it), free annulus for the rolling loop r 21…≥ 32.5,
  z −98…−91.
* J1 FPC (6.0 × 0.15, 6 conductors) enters the torso through the floor slot at (0, 22.3) and plugs into JST-GH 6p on
  the lower edge of the controller.
* Stop block for the lug: azimuth 270° ± 21.4°, r 18.2…21.3, top at z −98.3.

### 5.5 Z_naboj_test (dummy, printable bench stand)
Plate 110 × 90 × 5 (z −109…−104) with 4 feet; hub post Ø24.96 (z −104…−91.0) with a shoulder Ø28 below z −98.0
(inner-ring seat), top stub Ø6 × 3.2 (z −90.0…−86.8) carrying `Z_koleso_J1` (M3 countersunk from the top, flush at
z −86.8); stop block as 5.4. The torso sits on it by gravity. J1 sweep −155…155: nothing of the torso below z −84.5
other than plinth, skirt, pinion and lug; clearance to the stand ≥ 4 (plate) / 0.3 axial at the stop block top.

---------------------------------------------------------------------------------------------------------------------

## 6. Frame, deck, pan drive, electronics (RAM)

### 6.1 T_ram (PETG, printed standing, no supports except the shoulder bosses)
* **Cradle:** two walls y ±12.55…±14.15 (1.6), x −31.6…23.0, z −82.3…−47.8; −X end wall x −31.6…−30.0; +X end open.
  Floor frame 2.0 thick outside the servo pocket. Wall tops = deck seat (z −47.8).
* **Deck bosses** (4): r 3.0 at (−22, ±15), (20, ±15), z −53.8…−47.8, heat-set insert M2.5 × 4.0 from the top.
* **Cap bosses** (6): r 3.0 at (−22, ±17.5), (18, ±17.5), z −82.3…−77.3 and in the column feet at (±35.5, 3.0);
  heat-set insert M2.5 × 4.0 from below.
* **Pan-servo posts** (2): under the tabs, top face z −58.0, at x −16.25…−11.75 and 11.75…16.25, y −25.0…−17.5,
  cantilevered from the cradle front wall above z −77.5; insert M2 × 3.0 at (±14.0, −20.79), axis Z.
* **Controller standoffs** (2): on the rear wall, face y 15.5, at (x ±18.0, z −68.0), M2 thread-forming, axis Y.
* **Columns** (left; right mirrored): foot x 34.4…37.6, y −5…11, z −82.3…−78; U-channel web x 34.4…36.4, y −9…15,
  ribs to x 42.0, z −78…−30; shoulder boss: disc r 11.6, x 34.4…38.4 about (y 3, z −17) with a **stop ring**
  r 11.6…12.8 to x 39.1, a spigot Ø10.0 to x 41.0 (spring seat), 3 inserts M2 × 3.0 on r 7.5 at 90°, 210°, 330°,
  and a key slot 3.0 wide × 1.5 deep at azimuth 0° (anti-rotation of the joint). Columns are tied to the cradle by the
  floor frame and by two bridges at z −60…−50 (inside the lip outline: |y| ≤ 14.15 at |x| 23…34.4).
* Keep-outs for T_ram: the 4 vertical prisms x ±(25.8…32.2), |y| ≥ 15.8 (T_stred bosses come down there); the pan
  sweep (inner column face x ≥ 34.4); the tub and lip outlines (section 12).

### 6.2 T_paluba (PETG)
* Plate z −47.8…−46.0: main field x −31.6…31.6, y −14.3…15.3 plus the back lobe r ≤ 25.1 (y > 0, |x| ≤ 19.9).
  Front edge y −14.3 (the pan servo and its pinion stay uncovered). 4 screw holes Ø2.8 at `SCR_DECK`.
* **Pivot:** boss r 5.5, z −46.0…−44.2; steel pin Ø6 pressed 3.5 (bore Ø5.95), pin z −47.7…−41.2.
  PTFE washer 24 × 12.4 × 0.3 around the boss (z −46.0…−45.7), inside the stop groove.
* **Stop groove:** blind arc groove r 13.5 ± 1.2, depth 1.2, azimuth 0°…180° (+ end radii); the Ø2 pin of the gear
  (r 13.5, gear azimuth 90°) runs in it → ±90°.
* **FPC channel:** wall r 23.5…25.1, z −46.0…−42.9, azimuth 15°…165°; static FPC anchor (clamp 6 × 4, M2) at azimuth
  150°; slot through the deck x −18.0…−14.0, y 15.0…16.2.
* Foam pad 0.5 (PORON) 40 × 20 under the plate on the servo.

### 6.3 Pan drive
* STS3032 shaft up at **PAN_AX = (−5.85, −20.793)** (C = 21.600 to the pan axis, azimuth 254.3°); case x ±11.75,
  y −27.04…−14.54, z −74.2…−51.2; tabs x ±16.25, z −58.0…−55.5, holes at x ±14.0; boss z −51.2…−47.7; plug at the
  +X end (x 11.75…18.75, z −72.7…−64.7). Fixed with 2 × M2 × 6 from above.
* Pinion m0.8 18T, teeth z −45.5…−42.3, hub Ø8 below (z −47.7…−45.5), servo screw from above. **Mounted from above
  through the bore after T_stred** (tip r 8.0 reaches y −28.8).
* Gear: section 7.2. Ratio 2 : 1, firmware ±85°.

### 6.4 Electronics
| board | envelope (B frame) | mounting | connectors |
|---|---|---|---|
| DPS_riadenie | x −24…24, y 15.5…22.5 (PCB y 15.5…17.1, parts toward +Y), z −77…−55 | 2 × M2 × 5 into the standoffs, from +Y (door) | lower edge centre: JST-GH 6p (J1 FPC); upper edge x −16: 2 × JST-SH 4p (pan FPC tail); upper edge x +8 / +16: JST-PH 2p (speaker), JST-SH 3p (LED bar); +X end: 5264 3p (servo bus → STS3215 → STS3032), JST-SH 3p (left arm); −X end: JST-SH 3p (right arm), JST-PH 2p × 2 (VBAT out / 5 V in); ESP32-S3-Zero on the +Y face, USB-C toward −X at (−24, 19, −62) |
| menic (D36V28F5) | x −45.4…−36.6, y −5.9…11.9, z −70.0…−52.2 | 2 × M2 into the right column web | wires through a Ø5 hole in the web |
| zosilnovac (MAX98357A) | x 36.6…39.6, y −5.9…11.9, z −71.5…−52.2 | 2 × M2 into the left column web | – |
| kondenzator 470 µF | Ø10 × 13, axis Z at (41.0, 3.0), z −51.5…−38.5 | clip in the left column channel | on the 5 V servo rail |
Wire bundles run in the corner between cradle rear wall and floor (y 14.2…15.4, z −82…−78) and up the columns.

---------------------------------------------------------------------------------------------------------------------

## 7. Pan stage and lift (PAN) – all numbers in the pan-stage frame (= B frame at pan 0)

### 7.1 P_sachta
* **Well:** inner 47.0 × 22.0 (corner R1.5), walls 1.6 (outer 50.2 × 25.2), wall lower edge z −41.3, top z −2.0;
  above z −3.0 the outside is trimmed to r 26.5 (1.0 under the static collar ring). 4 PTFE strips on the long faces
  (x ±15 front, x −22 and +15 back).
* **Journal drum:** r 28.07 (+ 0.13 PTFE tape = 28.20), z −10.5…−4.5, chamfer to r 26.5 at z −3.0; lightened inside
  (ring wall 2.5, top plate 1.5 at z −3.5…−2.0, 4 ribs); lower outer edge chamfer 0.5.
  The collar disc (`golier_kotuc`) is glued on the top face z −2.0 (r ≤ 26.5).
* **Hub / floor:** hub disc r 12.6, z −42.2…−41.0 (bore Ø6.05 for the pin); back floor z −41.9…−41.0 only inside the
  stage azimuth sector 5°…140° (rule 1.3/8); elsewhere the well is open at the bottom.
* **Back window** (`WIN_BACK`): x −20.9…−6.5, through the back wall (y 11.0…12.6), z −41.3…−10.9.
  **End window** (`WIN_END`): +X end wall, y ±4.5, z −41.3…−15.0.
* **Bracket pads:** 2 pads on the back wall outer face, face y 15.6, r 3.0, at (x 19.5, z −30.0) and (x 8.0, z −14.5),
  insert M2 × 3.0, axis Y.
* Max radius of the bare stage 28.20 (must pass the bore r 28.35).

### 7.2 P_koleso
Gear m0.8 36T (d 28.8, da 30.4), face z −45.7…−42.2, teeth only in the gear-azimuth sector 154.3°…354.3°
(200° centred on the pinion at 254.3°); smooth drum r 15.7 elsewhere (FPC inner run), with a retaining lip r 16.5,
z −42.6…−42.2; underside recess r 6.0 from z −45.7 to −44.0 for the deck boss; bore Ø6.05 above it; stop pin Ø2 × 4.5
pressed at (r 13.5, azimuth 90°), protruding 1.0 below z −45.7. Joined to the hub disc of P_sachta (r 12.6, 500 mm²)
with epoxy + 2 dowels Ø2 × 4 on r 9.0 at azimuth 0° and 180° (the 1.2 mm hub disc cannot take screws); rotating FPC
anchor on the drum at azimuth 30°.

### 7.3 Lift mechanism
* MG90S: shaft axis ‖X at **(y 23.2, z −24.2)**, output toward −X. Case x −6.5…16.0, y 17.1…29.3, z −41.1…−18.3;
  turret x −12.5…−6.5 (boss r 5.9 on the axis, lobe r 2.9 at z −29.8); spline x −15.5…−12.5; kept tab at the top end:
  x −2.5…0.0, z −18.3…−13.45, hole at z −15.85; lower tab cut off; lead leaves the top end face at (x 13.65, y 23.2).
* **P_drziak_serva** inside `BRACKET` (x −5.3…17.6, y 12.6…17.1, z −41.9…−13.0) + ledge under the servo end
  (z −41.9…−41.1) + tab post x 0.0…5.0, y 20.2…26.2, z −18.0…−13.4 (M2 × 6 along +X through the tab);
  fixed to the 2 pads with M2 × 6 along −Y. Everything inside `PAN_ENV`.
* **P_kluka:** hub x −17.0…−12.8, r 3.6, 21T Ø4.8 bore, M2.5 countersunk screw; arm x −17.0…−14.5 to the pin at
  r 10.00, tip radius 2.2; steel pin Ø2 pressed, x −19.9…−14.5. Servo travel 180°: lift = 10·(1 − cos θ), θ = 0 at
  rest; the pin moves bottom (y 23.2, z −34.2) → front (y 13.2, z −24.2) → top (y 23.2, z −14.2): dead centres at 0 / 20.
* **L_ucho:** plate x −19.9…−17.4; slot 2.2 wide, pin-centre line z_rel 0 (= z −34.2 at rest), slot y 12.1…24.3;
  plate y 10.2…25.1, z_rel −6.3…+2.3, top far corner chamfer 1.5; flange in the x–z plane: y 10.2…12.4,
  x −19.9…−7.5, z_rel −6.3…−2.3 (lowered to −3.2 for x −17.6…−13.5); located by a dowel Ø2 (pressed 3.0 into the
  foot back face at x −15.5, z_rel −4.3, 2.0 proud) and fixed by ONE M2 × 8 thread-forming screw along −Y at x −10.0,
  z_rel −4.3 (tool channel Ø4.5 clears the servo case by 1.25 and the hanging crank by 2.25).
  Side gap crank ↔ ear 0.4 (declared fit).
* **L_pata:** 44.6 × 19.6 × 4.0, z −40.5…−36.5 at rest, bonded with epoxy to the FRONT neck half only (the neck halves
  must still separate); wire slot x 11.6…15.0, y −7.2…2.6 under the neck's two wire exits; FPC solder pocket 1.0 deep
  on the underside; tab x 22.3…27.0, y ±3.5, z −40.5…−38.0 through the end window; in the back face at z −38.5:
  pilot Ø1.7 × 7 at x −10.0 and dowel hole Ø1.98 × 3 at x −15.5.
* Mounting the ear: crank at BDC, pan 0: hook the ear onto the pin from the −X side (ear 2.6 back in +Y), slide it
  −Y until the flange seats on the dowel and the foot, drive the screw along −Y through the door (it sits below the
  turret).

### 7.4 Swept envelope
`PAN_ENV` (section 12) is the contract in both directions: PAN parts stay inside it, static parts stay ≥ 1.0 outside
it. In the front sector (azimuth 236°…336°) nothing of the lift module passes; only the well (r 28.1) and the FPC
lift loop (r 28.7) sweep there, so static front parts may come in to r 29.7 for z −40.5…−2.

---------------------------------------------------------------------------------------------------------------------

## 8. Shoulder joints and the arm interface (left = +X; right mirrored)

Shoulder axis ‖X through (y 3.0, z −17.0). Outer surface on the axis X_SH = 46.756.
| x | feature |
|---|---|
| 34.4 | inner face of the column (1.03 to the lift-servo sweep) |
| 34.4 … 38.4 | column boss r 11.6 (PETG), 3 inserts M2 on r 7.5 |
| 38.4 | boss face = seat of the joint neck; key 3.0 × 1.5 at azimuth 0° |
| 38.4 … 39.1 | stop ring r 11.6…12.8 on the column |
| 39.1 … 40.6 | seat flange of the side cap (hole r 11.25) – clamped |
| 38.4 … 40.6 | joint neck r 11.0 |
| 40.6 … 50.156 | joint body r 13.5 in the socket bore r 14.0 (visible beyond the cap surface) |
| 50.156 … 50.956 | chamfer to r 12.7; step face to r 11.4; r 11.0 from 51.556 |
| 51.556 … 57.956 | **Ø22 step = journal of the arm hub** (arm hub bore Ø22.3) |
| 58.756 | end face (chamfer to r 10.2) = **arm interface plane** |
* **T_klb** screws: 3 × M2 × 10 socket head on r 7.5 at azimuth 90°, 210°, 330° ((dy, dz) = r(cos az, sin az) about
  the axis), counterbore Ø4.2 from the end face to x 45.0, clearance Ø2.3 to the boss; they clamp joint + cap flange
  onto the column and are hidden by the arm.
* **Bush** (T_puzdro): bore Ø8.05 from the end face to x 44.0, recess Ø10.2 from x 44.0 to 38.4; bush shaft Ø8.0 f7
  × 14.75 with flange Ø10.0 × 2.0 (x 42.0…44.0); 2 disc springs 10 × 5.2 × 0.4 in series (x 41.0…42.0, working
  height 1.0) on the column spigot Ø10.0 (to x 41.0) → slip torque ≈ 0.25 N·m (tune with 0.1 shims). The bush keeps a
  blind hole Ø4.0 × 6.0 from the outer end – the female spline of the arm servo is cut in the arm round.
* **Pull-off magnets:** 3 × Ø3 × 2 in the end face on r 7.5 at azimuth 30°, 150°, 270° (pockets Ø3.1 × 2.1); the arm
  carries a steel ring (arm round).
* **Wire path** (3 × AWG30 of the arm servo): groove 1.6 wide × 2.6 deep along the underside of the body (azimuth
  270°) from the step face x 50.956 to x 40.6, notch in the cap seat flange, then inside along the column to
  JST-SH 3p on the controller; free length for ±90° of arm travel is stored in the arm hub around the Ø22 step.
* Arm range −45…+135° (arm round); nothing of the torso other than T_klb lies outside the white surface there.

---------------------------------------------------------------------------------------------------------------------

## 9. Cables and FPC

| run | conductor | path | min bend radius |
|---|---|---|---|
| J1 | FPC 6.0 × 0.15, 6 conductors | base channel → inner run on the foot ring r 21.0 (z −98…−91) → slot in the plinth wall → floor slot (0, 22.3) → JST-GH 6p | base: U-turn R ≥ 5 (33×); in the torso one 90° bend R 3 |
| pan + lift | custom FPC 3.0 × 0.12, 8 traces, standing on edge | 7 neck wires soldered to the tail under L_pata (x 11.6…15.0) → tab through the end window → **lift loop** on the +X end wall: U in the y–z plane, legs at y ±3.5, envelope x 25.3…28.4, y ±4, z −40.5…−15.5 → down the wall → rotating anchor on the drum (gear azimuth 30°) → **pan rolling loop**: inner run r 15.7, U-turn, outer run r 23.5 on the static wall, z −45.9…−42.9, back half → static anchor (azimuth 150°) → deck slot (−16, 15.6) → 2 × JST-SH 4p | lift loop R 3.5 (29×); pan U-turn R 3.9 (32×) |
| lift servo | 3 × AWG30, 60 mm | servo top end → micro junction 2 × 3 pins on the bracket → FPC | R 2 |
| servo bus | 3-wire 5264 leads | controller → STS3215 (+X end plugs) → STS3032 (+X end plug), in front of the cradle +X end | R 5 |
| arms | 3 × AWG30 per side | section 8 | R 2 |
| LED bar / speaker | JST-SH 3p / JST-PH 2p pigtails 90 mm | from the front wall around the −X side of the tower at z −56…−50 to the controller upper edge; plugged through the door after T_stred is on | R 3 |

---------------------------------------------------------------------------------------------------------------------

## 10. Fasteners (positions in the B frame)

| # | joint | qty | screw | direction, head side | positions | nut side |
|---|---|---|---|---|---|---|
| F1 | T_spodok → T_stred | 4 | M2.5 × 8 countersunk (ISO 10642) | +Z, heads flush in the cap underside z −84.5 | (±29.0, ±19.0) | insert M2.5 × 4.0 (OD 3.5) glued in the T_stred bosses, mouth z −81.0 |
| F2 | T_spodok → T_ram | 6 | M2.5 × 8 countersunk | +Z, heads flush at z −84.5 | (−22, ±17.5), (18, ±17.5), (±35.5, 3.0) | heat-set insert M2.5 × 4.0 in T_ram, mouth z −82.3 |
| F3 | T_paluba → T_ram | 4 | M2.5 × 6 pan head | −Z, heads on the deck top z −46.0 | (−22, ±15), (20, ±15) | heat-set insert M2.5 × 4.0, mouth z −47.8 |
| F4 | servo_pan tabs | 2 | M2 × 6 | −Z from above | (±14.0, −20.79), tab top z −55.5 | insert M2 × 3.0 in the posts |
| F5 | J1 set screw | 1 | M2.5 × 8 grub | +X | (−30.8, 0, −65.0) | insert M2.5 in the cradle end wall |
| F6 | pastorok_J1 | 1 | M3 × 8 countersunk | +Z from below | (−18, 0), head flush at z −90.0 | servo shaft |
| F7 | DPS_riadenie | 2 | M2 × 5 thread-forming | −Y (from the door) | (±18.0, y 17.1, −68.0) | standoffs |
| F8 | T_klb → column | 3 + 3 | M2 × 10 socket head | ∓X from outside, heads at |x| 45.0 | r 7.5 at 90°, 210°, 330° about the shoulder axis | insert M2 × 3.0 in the column boss |
| F9 | P_koleso → P_sachta | 2 | dowel Ø2 × 4 + epoxy | Z | r 9.0 at azimuth 0°, 180° | bonded on the bench |
| F10 | P_drziak_serva → P_sachta | 2 | M2 × 6 | −Y (door) | (19.5, y 17.1, −30.0), (8.0, y 17.1, −14.5) | insert M2 × 3.0 in the pads |
| F11 | servo_zdvih tab | 1 | M2 × 6 | +X | (x −2.5, y 23.2, z −15.85) | bracket post |
| F12 | L_ucho → L_pata | 1 (+ dowel Ø2) | M2 × 8 thread-forming | −Y (door, crank at BDC, pan 0) | screw x −10.0, dowel x −15.5; y 12.4, z −38.5 at rest | pilot Ø1.7 in the foot |
| F13 | LED holder, speaker ring | 2 + 3 | M2 × 6 thread-forming | −Y (inside, before T_stred is mounted) | bosses of 4.3 | pilot Ø1.7 |
| F14 | menic, zosilnovac | 2 + 2 | M2 × 5 thread-forming | ±X into the column webs | board holes | pilot Ø1.7 |
Tool access: every screw has a straight Ø4.5 channel along its axis: F1, F2, F6 from below; F3, F4 and the pan pinion
screw from above (F4 and the pinion through the bore: r 25.1 and 21.6 from the axis, bore r 28.35); F7, F10, F12
through the door opening (56.5 × 60.5, z −72.25…−11.75); F8 from outside; F11 from −X with the crank at BDC
(pan −85 turns it to the door).
Magnets: door 8 × Ø5 × 2 (4.3, 4.5), shoulders 6 × Ø3 × 2 (8). Inserts in resin are glued (hole = OD + 0.1), in PETG
heat-set (hole = OD − 0.3).

---------------------------------------------------------------------------------------------------------------------

## 11. Assembly order (K7: one straight direction per step)

| step | part(s) | direction | notes |
|---|---|---|---|
| 1 | inserts into T_ram, T_stred, P_sachta; magnets into T_stred, T_dvere, T_klb | – | polarity jig |
| 2 | lozisko_6805 → T_spodok | +Z from below | Ø37 seat, CA |
| 3 | T_ram → T_spodok | −Z, F2 from below | columns included |
| 4 | servo_J1 → cradle | −Z | into the pocket; set screw F5 loose |
| 5 | pastorok_J1 → servo | +Z from below | F6 |
| 6 | servo_pan → posts | −Z | F4 |
| 7 | foam, T_paluba (with pin, PTFE washer) | −Z, F3 | clamps the J1 servo; then set C with F5 on the dummy hub |
| 8 | DPS_riadenie, menic, zosilnovac, kondenzator, wiring | −Y / ±X | bench test on Z_naboj_test |
| 9 | front stack into T_stred (guide, grille, LED box, speaker) | +Y from inside | F13 |
| 10 | **T_stred → tower** | **−Z, straight** | tower inside the lip outline (1.3/6); F1 from below; plug LED + speaker through the door |
| 11 | pastorok_pan → servo_pan | −Z through the bore | – |
| 12 | P_koleso bonded to P_sachta (F9, bench), then **stage → torso** | **−Z through the bore** | gear meshes axially; FPC folded against the end wall; then PTFE tape check, spin ±90° |
| 13 | servo_zdvih + P_drziak_serva + P_kluka → stage | −Y through the door | F10, F11; pan FPC into the channel, anchors, plugs |
| 14 | golier_prstenec → bore | −Z | glue on the OD, flush with a flat plate |
| 15 | neck (B montaz step 9) with L_pata bonded, wires soldered to the FPC tail | −Z | then golier_kotuc (B step 10), glued to the stage top only |
| 16 | L_ucho | +X then −Y (door) | F12; cycle the lift 0…20 |
| 17 | T_bok_L / T_bok_P | −X / +X | onto spigot + tabs until the seat flange meets the stop ring |
| 18 | bush + springs, T_klb_L / T_klb_P | −X / +X | F8; arm wires through the groove |
| 19 | T_dvere | hook, then −Y | magnets |
| 20 | torso → base (or dummy) | −Z | bearing onto the hub, pinion into the sun gear, J1 FPC |
Service: door → lift servo, ear, controller, FPC plugs. Arm servo: pull the arm. Pan stage: steps 16 → 12 backwards.
J1 / pan servo: T_stred off (4 screws) after the stage is out.

---------------------------------------------------------------------------------------------------------------------

## 12. SPACE RESERVATION TABLE

Each module owns the listed volumes (B frame, rest pose; P / L zones are given in the pan-stage frame and sweep with
pan −85…85, L additionally with lift 0…20). A builder may fill his zones freely, must not leave them, and must not
enter another module's zone. Shared surfaces are the interfaces of sections 4–10. The same list is
`t4_common.envelopes()`; `fit/fit2.py` re-checks it.

General rules
* OBAL owns the shell: everything between the exterior and inset 2.2, plus: collar tube (r ≤ 30.6, z ≥ −10.5), door
  ledge / hook / magnet pads (inset ≤ 7.2, back wall, only where listed in 4.3 / 4.5), socket tubes (r ≤ 16 about the
  shoulder axis, |x| ≥ 39.1), seam tabs (inset ≤ 4, |x| 31.05…33.55), 4 screw bosses (x ±(25.8…32.2), |y| ≥ 15.8,
  z −81…−75), front stack (y ≤ −30.1 for |x| ≤ 17.5, z −36…−29; speaker r 14 about (0, z −51), y ≤ −31.6; bosses).
* RAM owns the tower: inside the lip outline − 0.5 for |x| ≤ 33.3 and z > −78 (white lip at z −81: superellipse
  a 41.36, b 27.30, n 2.66), inside the tub − 0.3 below z −78 (superellipse 39.55, 25.49, 2.66), below the deck
  underside z −47.8 (plus deck, pivot, FPC channel up to z −42.9 inside r 25.1 back half / r 13.0 elsewhere, and the
  pan pinion), and the wings |x| 34.4…(inset 2.2 + 0.5) for z −82.3…−30 plus the shoulder bosses.
  RAM also owns everything below z −84.5.
* PAN owns `PAN_ENV` above z −45.7 (table below), with the low-zone rule of 1.3/8.

**OBAL (t4_obal.py) – shell-mounted volumes**

| zone | grp | shape | x | y | z | note |
|---|---|---|---|---|---|---|
| reproduktor | T | cyl ‖Y, r 14.00 | axis x 0.00 | -36.60 … -31.60 | axis z -51.00 | behind the grille |
| led_box | T | box | -17.50 … 17.50 | -36.60 … -30.10 | -36.0 … -29.0 | light guide flange + LED PCB + holder |
| rura_goliera | T | cyl ‖Z, r 30.60 (bore r 28.35) | axis x 0.00 | axis y 0.000 | -10.50 … 1.75 | collar tube = ring seat + journal bearing |
| klb_L | T | cyl ‖X, r 13.50 | 40.60 … 50.96 | axis y 3.00 | axis z -17.00 |  |
| klb_L_krk | T | cyl ‖X, r 11.00 | 38.40 … 40.60 | axis y 3.00 | axis z -17.00 |  |
| klb_L_cap | T | cyl ‖X, r 11.00 | 50.96 … 58.76 | axis y 3.00 | axis z -17.00 |  |
| klb_P | T | cyl ‖X, r 13.50 | -50.96 … -40.60 | axis y 3.00 | axis z -17.00 |  |
| klb_P_krk | T | cyl ‖X, r 11.00 | -40.60 … -38.40 | axis y 3.00 | axis z -17.00 |  |
| klb_P_cap | T | cyl ‖X, r 11.00 | -58.76 … -50.96 | axis y 3.00 | axis z -17.00 |  |

**RAM (t4_ram.py) – static tower, wings, parts under the cap, dummy**

| zone | grp | shape | x | y | z | note |
|---|---|---|---|---|---|---|
| servo_J1 | T | box | -29.50 … 15.70 | -12.35 … 12.35 | -83.30 … -48.30 | STS3215, shaft down at J1_AX |
| servo_J1_boss | T | cyl ‖Z, r 6.00 | axis x -18.00 | axis y 0.000 | -85.90 … -83.30 |  |
| servo_J1_plug | T | box | 15.70 … 27.0 | -8.0 … 8.0 | -66.30 … -48.30 | 2 x 5264 plugs + cable bend |
| ram_koliska | T | box | -31.60 … 23.0 | -14.15 … 14.15 | -82.30 … -47.80 | cradle walls 1.6 around the servo |
| paluba | T | box | -31.60 … 31.60 | -14.30 … 15.30 | -47.80 … -46.0 | deck plate on the cradle walls |
| paluba_zad | T | cyl ‖Z, r 25.10 | axis x 0.00 | axis y 0.000 | -47.80 … -46.0 | deck under the FPC channel (y > 0 half) |
| cap_pan | T | cyl ‖Z, r 3.00 | axis x 0.00 | axis y 0.000 | -47.70 … -41.20 |  |
| ptfe | T | cyl ‖Z, r 12.00 (bore r 6.20) | axis x 0.00 | axis y 0.000 | -46.0 … -45.70 |  |
| kanal_fpc_pan | T | cyl ‖Z, r 25.10 (bore r 23.50) | axis x 0.00 | axis y 0.000 | -46.0 … -42.90 | static wall of the pan rolling loop (y > 0 half) |
| fpc_pan | T | cyl ‖Z, r 23.50 (bore r 15.70) | axis x 0.00 | axis y 0.000 | -45.90 … -42.90 | pan rolling loop (y > 0 half) |
| servo_pan | T | box | -11.75 … 11.75 | -27.04 … -14.54 | -74.20 … -51.20 | STS3032, shaft up at PAN_AX |
| servo_pan_tabs | T | box | -16.25 … 16.25 | -27.04 … -14.54 | -58.0 … -55.50 |  |
| servo_pan_boss | T | cyl ‖Z, r 6.20 | axis x -5.85 | axis y -20.793 | -51.20 … -47.70 |  |
| servo_pan_plug | T | box | 11.75 … 18.75 | -24.80 … -16.80 | -72.70 … -64.70 |  |
| pastorok_pan | T | cyl ‖Z, r 8.00 | axis x -5.85 | axis y -20.793 | -45.50 … -42.30 | mounted from above AFTER T_stred |
| pastorok_pan_naboj | T | cyl ‖Z, r 4.00 | axis x -5.85 | axis y -20.793 | -47.70 … -45.50 |  |
| DPS_riadenie | T | box | -24.0 … 24.0 | 15.50 … 22.50 | -77.0 … -55.0 | carrier + ESP32-S3-Zero, service through the door |
| stlp_L | T | box | 34.40 … 42.0 | -9.0 … 15.0 | -78.0 … -30.0 | left column (U channel) |
| stlp_P | T | box | -42.0 … -34.40 | -9.0 … 15.0 | -78.0 … -30.0 |  |
| stlp_L_naboj | T | cyl ‖X, r 11.60 | 34.40 … 38.40 | axis y 3.00 | axis z -17.00 | shoulder boss |
| stlp_P_naboj | T | cyl ‖X, r 11.60 | -38.40 … -34.40 | axis y 3.00 | axis z -17.00 |  |
| stlp_L_doraz | T | cyl ‖X, r 12.80 (bore r 11.60) | 38.40 … 39.10 | axis y 3.00 | axis z -17.00 | stop ring |
| stlp_P_doraz | T | cyl ‖X, r 12.80 (bore r 11.60) | -39.10 … -38.40 | axis y 3.00 | axis z -17.00 |  |
| stlp_L_pata | T | box | 34.40 … 37.60 | -5.0 … 11.0 | -82.30 … -78.0 |  |
| stlp_P_pata | T | box | -37.60 … -34.40 | -5.0 … 11.0 | -82.30 … -78.0 |  |
| menic | T | box | -45.40 … -36.60 | -5.90 … 11.90 | -70.0 … -52.20 | D36V28F5 on the right column |
| zosilnovac | T | box | 36.60 … 39.60 | -5.90 … 11.90 | -71.50 … -52.20 | MAX98357A on the left column |
| kondenzator | T | cyl ‖Z, r 5.00 | axis x 41.00 | axis y 3.000 | -51.50 … -38.50 |  |
| pastorok_J1 | T | cyl ‖Z, r 10.00 | axis x -18.00 | axis y 0.000 | -90.0 … -86.80 |  |
| lozisko_6805 | T | cyl ‖Z, r 18.50 (bore r 12.50) | axis x 0.00 | axis y 0.000 | -98.0 … -91.0 |  |
| pata_J1 | T | cyl ‖Z, r 24.00 (bore r 17.00) | axis x 0.00 | axis y 0.000 | -91.0 … -84.50 | plinth / gear housing (notched) |
| pata_J1_dole | T | cyl ‖Z, r 21.00 (bore r 18.50) | axis x 0.00 | axis y 0.000 | -98.0 … -91.0 |  |
| sukna | T | cyl ‖Z, r 28.50 (bore r 24.00) | axis x 0.00 | axis y 0.000 | -86.20 … -85.20 |  |
| Z_koleso_J1 | Z | cyl ‖Z, r 10.00 | axis x 0.00 | axis y 0.000 | -90.0 … -86.80 |  |
| Z_naboj | Z | cyl ‖Z, r 12.50 | axis x 0.00 | axis y 0.000 | -100.0 … -91.0 |  |

**PAN (t4_pan.py) – pan stage (P, pan frame) and lift parts (L, rest pose)**

| zone | grp | shape | x | y | z | note |
|---|---|---|---|---|---|---|
| sachta | P | box | -25.10 … 25.10 | -12.60 … 12.60 | -41.30 … -3.0 | well 47 x 22, walls 1.6 (lower edge -41.3; corners trimmed to r 26.5 above z -3.0) |
| sachta_naboj | P | cyl ‖Z, r 12.60 | axis x 0.00 | axis y 0.000 | -42.20 … -41.0 | hub disc joining well and gear |
| sachta_dno_zad | P | box | -8.0 … 25.10 | 2.0 … 12.60 | -41.90 … -41.30 | well floor, back sector only |
| cap_otocny | P | cyl ‖Z, r 28.20 (bore r 24.00) | axis x 0.00 | axis y 0.000 | -10.50 … -4.50 | journal D56.4 |
| vrch_stola | P | cyl ‖Z, r 26.50 | axis x 0.00 | axis y 0.000 | -4.50 … -2.0 |  |
| golier_kotuc | P | cyl ‖Z, r 26.50 | axis x 0.00 | axis y 0.000 | -2.0 … 4.0 | finished part (B) |
| koleso_pan | P | cyl ‖Z, r 15.70 (bore r 3.00) | axis x 0.00 | axis y 0.000 | -45.70 … -42.20 |  |
| servo_zdvih | P | box | -6.50 … 16.0 | 17.10 … 29.30 | -41.10 … -18.30 | MG90S, shaft along -X |
| servo_zdvih_veza | P | cyl ‖X, r 5.90 | -12.50 … -6.50 | axis y 23.20 | axis z -24.20 |  |
| servo_zdvih_lalok | P | cyl ‖X, r 2.90 | -12.50 … -6.50 | axis y 23.20 | axis z -29.80 |  |
| servo_zdvih_ucho | P | box | -2.50 … 0.0 | 17.10 … 29.30 | -18.30 … -13.45 |  |
| servo_zdvih_kabel | P | box | 11.40 … 15.90 | 20.70 … 25.70 | -18.30 … -13.30 |  |
| kluka_naboj | P | cyl ‖X, r 3.60 | -17.0 … -12.80 | axis y 23.20 | axis z -24.20 |  |
| kluka_obalka | P | cyl ‖X, r 12.20 | -17.0 … -14.50 | axis y 23.20 | axis z -24.20 | crank sweep; only the FRONT half disc (y <= Y_LIFT + 2.2) is used |
| drziak_serva | P | box | -5.30 … 17.60 | 12.60 … 17.10 | -41.90 … -13.0 | bracket between the well back wall and the servo |
| drziak_serva_dno | P | box | -6.50 … 16.0 | 17.10 … 26.20 | -41.90 … -41.10 | ledge under the servo end |
| fpc_zdvih | P | box | 25.30 … 28.40 | -4.0 … 4.0 | -40.50 … -15.50 | flexible loop (may be folded during insertion) |
| pata | L | box | -22.30 … 22.30 | -9.80 … 9.80 | -40.50 … -36.50 | foot under the neck |
| pata_jazyk | L | box | 22.30 … 27.0 | -3.50 … 3.50 | -40.50 … -38.0 |  |
| ucho | L | box | -19.90 … -17.40 | 12.40 … 23.60 | -40.50 … -31.90 |  |
| ucho_koniec | L | box | -19.90 … -17.40 | 23.60 … 25.10 | -40.50 … -33.40 |  |
| ucho_priruba | L | box | -13.50 … -7.50 | 10.20 … 12.40 | -40.50 … -36.50 |  |
| ucho_priruba_nizka | L | box | -19.90 … -13.50 | 10.20 … 12.40 | -40.50 … -37.40 |  |
| krk | L | box | -22.50 … 22.50 | -10.0 … 10.0 | -36.50 … 6.50 | finished neck (B), envelope |

**PAN_ENV – swept radius limit of everything on the pan stage (r about the Z axis, pan frame)**

| z from | z to | r max | shell inner half depth b_i at both ends | margin |
|---|---|---|---|---|
| -45.7 | -41.9 | 15.9 | 37.74 / 37.59 | 21.69 |
| -41.9 | -22.0 | 34.0 | 37.59 / 35.60 | 1.60 |
| -22.0 | -18.0 | 33.5 | 35.60 / 34.86 | 1.36 |
| -18.0 | -11.5 | 32.2 | 34.86 / 33.36 | 1.16 |
| -11.5 | -10.5 | 28.3 | 33.36 / 33.09 | 4.79 |
| -10.5 | -4.5 | 28.2 | 33.09 / 31.21 | 3.01 |
| -4.5 | -3.0 | 28.2 | 31.21 / 30.64 | 2.44 |
| -3.0 | 4.0 | 26.5 | 30.64 / 28.34 | 1.84 |

**Derived numbers (true offsets)**

| quantity | value |
|---|---|
| X_SH (outer surface on the shoulder axis) | 46.756 |
| X_KLB_END (arm interface plane) | 58.756 |
| front surface at x 0, light bar z -32.5: outer y / inner y | -39.17 / -36.96 |
| front surface at x 0, grille z -48: outer y / inner y | -39.99 / -37.79 |
| front surface at x 0, speaker centre z -51: outer y / inner y | -40.01 / -37.81 |
| back surface at x 0, z -12.0: outer y / inner y | 35.76 / 33.49 |
| back surface at x 0, z -24.0: outer y / inner y | 38.15 / 35.93 |
| back surface at x 0, z -42.0: outer y / inner y | 39.80 / 37.60 |
| back surface at x 0, z -60.0: outer y / inner y | 39.60 / 37.40 |
| back surface at x 0, z -72.0: outer y / inner y | 37.45 / 35.14 |
| inner half width a_i / half depth b_i at z -10.5 | 43.21 / 33.09 |
| inner half width a_i / half depth b_i at z -4.5 | 40.58 / 31.21 |
| inner half width a_i / half depth b_i at z -2.0 | 37.85 / 30.21 |
| inner half width a_i / half depth b_i at z 1.75 | 29.42 / 28.34 |
| white lip inner half depth at x 0 (z -81) | 27.30 |
| white lip inner half depth at x 10 (z -81) | 27.06 |
| white lip inner half depth at x 16.75 (z -81) | 26.34 |
| white lip inner half depth at x 20 (z -81) | 25.76 |
| white lip inner half depth at x 25 (z -81) | 24.36 |
| white lip inner half depth at x 30 (z -81) | 22.19 |
| white lip inner half depth at x 33.05 (z -81) | 20.25 |
| lip inner half depth at x 16.25, z -81.0 (pan-servo tab corner needs 27.55) | 26.41 |
| lip inner half depth at x 16.25, z -80.5 (pan-servo tab corner needs 27.55) | 27.15 |
| lip inner half depth at x 16.25, z -80.0 (pan-servo tab corner needs 27.55) | 27.82 |
| lip inner half depth at x 16.25, z -79.0 (pan-servo tab corner needs 27.55) | 29.16 |
| lip inner half depth at x 16.25, z -78.0 (pan-servo tab corner needs 27.55) | 30.56 |
| door hook tab at x 12.0, z -12: outer y 35.04 -> inner corner radius (inset 3.6) | 33.44 |
| door hook tab at x 20.0, z -12: outer y 33.36 -> inner corner radius (inset 3.6) | 35.29 |
| door magnet pad at x 25.0, z -24.0: outer y 34.40 -> pad inner radius (inset 7.2) | 35.32 |
| door magnet pad at x 25.0, z -60.0: outer y 36.70 -> pad inner radius (inset 7.2) | 37.21 |

Shared interfaces (who provides what)
| interface | provided by | used by | numbers |
|---|---|---|---|
| bore r 28.35, z −10.5…4 | OBAL (T_stred) | PAN journal r 28.20; `golier_prstenec` | 4.3, 7.1 |
| pivot pin Ø6, top z −41.2; PTFE washer; stop groove r 13.5 | RAM (T_paluba) | PAN (P_koleso bore Ø6.05, pin Ø2) | 6.2, 7.2 |
| pan gear mesh C 21.6 at azimuth 254.3°, gear plane z −45.7…−42.2 | RAM (pinion) / PAN (gear) | – | 6.3, 7.2 |
| FPC channel wall r 23.5…25.1, top z −42.9; deck slot | RAM | PAN (FPC) | 6.2, 9 |
| cap spigot outline (41.15, 27.09, 2.66), z −81.5…−78; 4 pads + F1 holes | RAM (T_spodok) | OBAL (T_stred lip, caps, bosses) | 5.2, 4.3 |
| column stop ring face x ±39.1, boss face ±38.4, key, 3 inserts, spigot Ø10 | RAM (T_ram) | OBAL (caps, T_klb, bush) | 6.1, 8 |
| front stack ↔ controller | OBAL (pigtails) | RAM (connectors) | 4.6, 6.4 |
| door opening 56.5 × 60.5 = tool access | OBAL | RAM (F7), PAN (F10, F12) | 10 |
| foot ↔ neck bottom (z −36.5, 45 × 20), wire exits x 12.0…14.55 | variant B (fixed) | PAN (L_pata) | 7.3 |
| collar disc slot 45.5 × 20.5, stage top z −2 | variant B (fixed) | PAN | 7.1 |
| arm interface plane x ±58.756, Ø22 step, bush bore, magnets | OBAL (T_klb) | arm round | 8 |
| base interface | RAM | base round | 5.4 |

---------------------------------------------------------------------------------------------------------------------

## 13. Fits and tolerances

| feature | nominal | fit / tolerance |
|---|---|---|
| pan journal in the bore | Ø56.40 (resin Ø56.14 + tape) in Ø56.70 | radial 0.15 (0.10…0.20); without tape if the print is tight |
| collar ring in the bore | Ø56.50 in Ø56.70 | 0.10 glue seam (B) |
| collar disc ↔ ring | r 26.5 / 26.75 | 0.25 running seam (B) |
| pan pivot | pin Ø6 h6, deck bore Ø5.95 (press), gear / hub bore Ø6.05 | running 0.05 |
| pan gear pair | m0.8, 18T / 36T, C 21.600 | C +0.05/0 → backlash 0.04…0.07; pan-servo seat ±0.3 in its tab holes (Ø2.2) |
| J1 gear pair | m1, 18T / 18T, C 18.00 | adjustable ±0.3 (set screw), backlash target 0.03 at the pitch circle |
| 6805 outer ring | Ø37.00 | seat +0.05/0, CA; shoulder r 17.0 |
| 6805 inner ring | Ø25.00 | hub −0.02/−0.06 (base); dummy post Ø24.96 |
| STS3215 seat | 45.2 × 24.7 × 35.0 | pocket +0.2 per side in y, ±0.3 slot in x; height 35.0 ± 0.3 taken by the 0.5 foam |
| STS3032 seat | 23.5 × 12.5, tabs at 16.2 above the bottom | posts flat, holes at ±14.0, slotted ±0.3; verify the tab height (shim) |
| MG90S seat | 22.5 × 12.2 × 22.8 | bracket pocket +0.15 per side; tab post face slotted ±1.0 in x |
| crank pin in the ear slot | Ø2.00 in 2.20 | 0.10 per side; crank ↔ ear side gap 0.40 |
| neck in the well | 45 × 20 in 47 × 22 (PTFE strips 0.13) | 0.87 per side; foot 44.6 × 19.6: 1.2 |
| ear in the back window | flange / plate ± 1.0 | – |
| cap spigot in the white lip | radial 0.21…0.28 | – |
| seam tabs | 0.15 to the arch inner surface at the root | – |
| shoulder: neck r 11.0 in hole r 11.25; body r 13.5 in bore r 14.0 | 0.25 / 0.50 | bush Ø8.0 f7 in Ø8.05 |
| door | 0.25 all round; hook tabs 0.2 behind the wall; magnet air gap 0.2 | – |
| inserts | M2: OD 3.2 × 3.0; M2.5: OD 3.5 × 4.0 | resin hole OD + 0.1 (glued), PETG hole OD − 0.3 (heat-set) |
| walls | shells 2.2 (≥ 2.0); local ≥ 1.2: floor under the J1 servo 1.2, front lip relief ≥ 1.5, joint walls 1.25 | PETG ≥ 1.6 |

---------------------------------------------------------------------------------------------------------------------

## 14. Notes for the checks K1–K11

* **K2 intended fits (zero or negative gap allowed):** journal ↔ bore; collar ring ↔ bore; collar disc ↔ stage top;
  pin ↔ deck / gear; PTFE washer; pinion ↔ gear teeth (both pairs); bearing ↔ seat / hub; servo cases ↔ seats; foam;
  inserts, magnets, screws ↔ their holes; foot ↔ neck bottom (bonded); ear flange ↔ foot; crank pin ↔ slot; cap seat
  flange ↔ stop ring / joint shoulder; spigot ↔ lips (0.2); door ↔ ledge / hooks; plugs ↔ openings; bush ↔ springs.
* **K3:** pan −85…85 × lift 0…20 for groups P, L against T: expected minima as in 1.4 (1.00 … 1.51). Declared
  sub-1.0 gaps: crank ↔ ear 0.40 (joint), foot / flange ↔ hub disc 0.5 at rest (end position), FPC ↔ its anchors.
  J1 −155…155: only the stop lug meets the dummy (at ±155°).
* **K5 seats:** values of section 13; centre distances C 18.00 (J1) and 21.600 (pan; PAN_AX (−5.85, −20.793)).
* **K6:** stroke 2·R_CRANK = 20.00, dead centres at θ 0 / 180° (pin at y 23.2); pan stop groove 0°…180° + pin at 90°
  → ±90°; firmware ±85°.
* **K7:** order and directions of section 11; T_stred straight −Z with the tower of step 8; stage straight −Z through
  the bore without lift servo, bracket, crank (FPC loop is flexible).
* **K8:** exterior = `outer_section()`; declared zones D1–D3 (1.5), the shoulder joints, the plugs. Seams 0.50 / 0.25.
  See-through: the seams x = ±33.3 are backed by the seam tabs only locally – the caps / band need a 1.0 black
  shadow strip glued inside along the seams if a viewpoint sees through (OBAL to check and add as part of the tabs).
* **K9:** numbers of 1.2/3; critical pose lift 12.5 / tilt +30° (0.53).
* **K10:** resin parts: no trapped volumes (4.7); FDM: T_ram printed standing (columns up), T_paluba upside down,
  Z_naboj_test plate down.
* **K11:** use `mesh_volume()`; bought masses in section 3.3 / pack §4.

---------------------------------------------------------------------------------------------------------------------

## 15. Open points (for the lead / user)
1. STS3032 and STS3215 mounting-hole patterns and the STS3032 tab height are from listings – measure the purchased
   servos before printing T_ram (seats are slotted ±0.3).
2. Head clearance at lift 12.5 / +30° is 0.53 (criterion 0.5) by the vertex check – K9 (BVH) decides whether the
   firmware row becomes +27.5°.
3. The black skirt disc r 28.5 under the cap (D2) is larger than the T3 plinth r 24 – needed while the J1 gears stay
   18T / 18T; the base design may later hide the pinion itself and trim the skirt.
4. L_pata is bonded to the finished neck (front half only); if the user prefers screws, two Ø1.6 pilot holes in the
   neck bottom would be a change of a finished part.
5. The pan pinion and the pan stage are mounted from above through the collar bore, the lift servo through the door –
   the back door is therefore a required service opening, not optional.

## 16. Integrator addendum (rev. 1 + integration; these lines supersede the numbers above)
Changes made while integrating the three modules (K1–K11); the same list is `INTEG["changes"]` in `t4_common.py` and
`integrator_changes` in `parts.json`. The builders' own deviations are in `parts_<module>.json["deviations"]`.
1. §5.5 **Z_naboj_test**: no feet. Plate 110 × 90 × 5 at z −113.5…−108.5 (flat on the print bed), pedestal r 22.5 from
   z −108.5 to −104 under the shoulder and the stop block; the M8 head stays inside the counterbore, which is r 10.5
   below z −109.2 with a 45° run-out to r 8.75 (13 mm socket). `RAM["DUMMY"]`.
2. §7.2 **P_koleso**: FPC retaining lip 0.6 thick (z −42.6…−42.0, was 0.4); floor under the blind dowel holes 0.6.
   `PAN["GEAR"]["lip"]["z"]`.
3. §7.1 **P_sachta**: the 0.2 FPC groove under the apron of the well (PAN module, `t4_pan.mk_sachta`) runs out to the
   apron edge y 8.2.
4. §6 **T_ram**: pilots of F7 and F14 and the 4 cradle F2 insert seats are through holes (no 0.4…0.5 floors).
5. §4.3 **T_stred**: magnet pocket and frame magnet of the two upper door pads (z −24) sit 0.5 further out along the
   wall than the door magnet; the pad is trimmed with one PAN_ENV radius. `PAD["pocket_du"]` in `t4_obal.py`.
6. `t4_common.py` section 1.12: resin density 1.15 g/cm³ for masses (was 1.18).
7. Export: STL with absolute chord deflection 0.01 for every module; STEP only below 12 MB (null for 9 loft parts).
8. §15 point 2 is decided by K9 (BVH, real head): 0.517 mm at lift 12.5 / +30° / pan 0, criterion 0.5 met with
   0.017 mm of margin → no pan-dependent table; recommended firmware row for lift 10…15: tilt down +27.5°.

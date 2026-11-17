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

### 17.4 J1, merged T_spodok, deck (RAM)
* **T_spodok = old T_spodok + T_ram (one print, ≈ 90 × 61 × 96, fits 211 × 118 × 220).** Delete F2 and every F2 feature.
  * Cap body, spigot (outline `SPIGOT_SE`, z −81.5…−78.0, fit 0.21…0.28): continuous except 4 notches 7.8 wide at the
    T_stred bosses (boss r 3.4 + 0.5 per side; was 8.0); no notch within |x| 31.0…35.6 (backs the seam ends x ±33.3).
  * **No skirt disc** (S11). Plinth r 24.0 (z −91…−84.5), foot ring r 21.0 (z −98…−91), 6805 seat **Ø37.15** slide fit +
    epoxy (was 37.00 press + CA), shoulder r 17.0…18.5 at z −91. Pinion passage `J1_PASS` (r 10.8 about J1_AX, slot
    ±0.3 in x) through floor and plinth as rev. 1.
  * **J1 stop lug** 4.0 (tangential) × 4.0 (radial, r 17.0…21.0) × 4.0 (z −102.0…−98.0) at az 90°, R1.0 roots (or a
    Ø3 × 10 steel pin bonded 6 deep in the foot ring at r 19.0, az 90°). Base stop block must span az 270° ± 19.0° at
    r 17.0…21.0 for ±155° (base round).
  * **Cradle** around the STS3215: long walls y ±(12.55…15.05) (2.5), x −32.2…25.8, z −82.3…−48.2 (top = deck seat),
    −X end wall x −32.2…−29.7 (2.5); vertical inner corners and wall/floor roots R2.0 (R1.0 where the servo corner needs
    it). +X end open (plug zone x 15.7…27.0, |y| ≤ 8, z −66.3…−48.3 stays empty). Bumper post at x 16.7…18.3, |y| ≤ 4,
    z −83.3…−70.0 with a 1.0 PORON pad at the servo's +X end.
  * **STS3215 support (S10, air option):** the case bottom (z −83.3) rests on 4 corner pads 5.0 × 5.0 (top z −83.3,
    1.2 above the cap underside) at the 4 case-bottom corners; the rest of the case footprint (x −29.5…15.7, y ±12.35)
    is a **window** through the cap floor (air to the base gap). Servo fixing: 4 × M2 through Ø2.4 holes in the pads,
    slotted ±0.3 in x, into the servo's own case holes – **hole positions and thread are UNVERIFIED: measure the purchased
    STS3215; RAM models the holes at the pad centres and lists the measurement as open.** C = 18.00 is set with 0.1 PET
    shim strips between the case −X end (x −29.5) and the end wall (x −29.7, nominal 0.2 of shims); backlash target
    0.03 at the pitch circle (P06; F5 deleted).
  * **Columns (S08):** web x ±(34.4…37.4) (3.0) for y −9.0…15.0, ribs y −9.0…−6.5 and 12.5…15.0 to x ±42.0, foot
    x ±(33.0…37.6), y −5…11, z −82.3…−78 widened into the floor with R2 gussets; **box closure** plate x ±(40.0…42.0),
    y −9…15, z −52.0…−34.0 (above the boards; J ≈ 85 → ≈ 2200 mm⁴ there); shoulder boss disc r 11.6, x ±(34.4…38.4)
    about (y 3, z −17), R2.0 into web and ribs; stop ring r 11.6…12.8, x ±(38.4…39.1) with backing flange r 12.8,
    x ±(37.4…39.1); key slot 3.0 × 1.5 at az 0°; **F8 inserts M2 at r 7.5, az 60°, 180°, 300°** (≥ 60° from the key;
    was 90/210/330 with a 0.6 wall); delete the Ø10 spring spigot (bush deferred, P08).
  * **Pan-servo posts:** 2 posts 6.0 (x) × 7.5 (y) under the tabs x ±(11.25…17.25), y −24.6…−17.1, top z −56.50, DIN 562
    slots (17.2.5), R1 roots to the cradle front wall.
  * **Stop-pin posts** (17.2.4), **bridge bosses** for F3b at (6.0, ±15.95): r 3.4, z −52.5…−48.2 on the outer faces of
    the long walls, bonded M2.5 inserts from the top. **Deck bosses** F3a at (20.0, ±13.8) and (−33.5, ±10.0): r 3.4,
    z −52.5…−48.2, merged into the walls / column webs, bonded M2.5 inserts.
  * **Carrier standoffs** (F7): 2 bosses r 3.25 on the cradle back wall at (x ±19.0, z −62.5), face y 16.50, bonded M2
    inserts axis Y. **Board standoffs** (F14): buck on the right web, amp on the left web, Ø5.0 bosses 1.5 long (1.5 air,
    S10), thread-forming M2 × 6 one-time + DIN 125 washers; a Ø4 vent through each web behind the board.
  * **Capacitor saddle** (M07): 470 µF 10 V radial Ø10 × 13 lying along X at (x 6.0…19.0, y 20.2, z −77.0): 180°
    saddle r 5.1 on the floor, 2.8 × 1.2 tie slot at x 12.5 (cable tie 2.5 mm), leads to the carrier's lower 5 V pads.
  * **Cable tie saddles** (M16): 3 × saddle 4.0 wide with a 2.8 × 1.2 tie slot: cradle back wall at (x −10, y 15.05,
    z −50.0); each column web inner face at (y 12.0, z −45.0) (arm / board wires up the columns).
  * Floor slot for the base FFC: x −6.0…6.0, y 21.2…22.5 (12 wide for a 1.0 mm 10-pole FFC, 11.0 wide), continuing down
    through the plinth wall to z −91.0 (rev. 1 slot 6.8 → 12.0; plinth skin outside the slot ≥ 1.2 – check).
  * Drain / vent: 2 × Ø3 holes as rev. 1 + the servo window.
* **T_paluba (deck lid, resin):** plate z −48.20…−46.20 (2.0) over the cradle; outline = rev. 1 deck incl. the back lobe
  (r ≤ 25.1 for B az 0…180) but trimmed to r ≤ 26.6 inside B az 16…232 (stop-lug sweep) and with a through slot
  x −6.1…12.1, y −18.1…18.1 for T_most (the deck becomes a "C" joined by the back lobe and the −X part). Static FFC wall
  r 23.50…25.10, z −46.20…−43.00, B az 15…165; FFC slot through the deck r 22.4…23.6, B az 26…34 (3.0 + 0.3 wide for
  the stacked pair, 1.0 radial); a 1.0 × 7.0 FFC slot in the cradle back wall at x 17.0…24.0, z −51.0…−50.0 (RAM, T_spodok)
  leads the pair out to the carrier. 4 × F3a (M2.5 × 6). No pivot boss (it is on T_most); PTFE washer seat flush.
* **T_most** (Al bridge): 17.1. Fixed by 2 × F3b ISO 7380 M2.5 × 6 + DIN 125 M2.5 into the bridge bosses.
* **T_cap** (pivot boss, separate small resin print, owner RAM): cylinder Ø7.70 × 4.40 (z −46.20…−41.80), Ø3.4 hole,
  edges R0.3; bonded (epoxy) on T_most around the tapped M3 hole and clamped by F15; PTFE tape wrap = journal (17.1).
  It replaces the steel pin `cap_pan`. Print upright, top face to the plate is NOT allowed (journal face): print on its
  axis, supports only on the bottom face.
* **J1 pinion (A4):** m1 18T, face ≥ 4.0, bore Ø6.00 H7, brass (KHK BSS1-18B: m1, 18T, brass, bore 6 – face / hub
  UNVERIFIED; Mädler 263 018 00: m1 18T brass with hub, face 6.5, OD 20 – usable if the hub is ≤ 0.9 and faces up).
  Slid over the STS3215 spline (25T, tips Ø5.9; spline length below the boss 2.2 per the rev. 1 model – UNVERIFIED) with
  Loctite 638, no screw. Gear plane **z −90.00…−86.00** (pinion top 0.1 below the boss end −85.9; bottom 1.0 above the
  6805 top −91.0). Engaged length 2.1…2.2 → ≈ 1.1 N·m capacity: above the clutch (0.25…0.40 N·m) and the firmware limit
  (≤ 30 % = 0.65 N·m); a locked clutch at stall (2.17 N·m) would release the bond before the brass teeth (244 MPa) yield –
  the clutch is a SAFETY PART of the base.
* **Base interface (rev. 2, replaces §5.4 where different):** sun gear m1 18T on the base hub, plane z −90.0…−86.0; base
  top plane ≤ −86.0, opening r ≥ 29.0 down to −91.0; 6805 inner ring Ø25 on the hub z −98…−91 (hub −0.02/−0.06), the
  hub retains the torso (≈ 30 N pull-off); **slip clutch 0.25…0.40 N·m after creep, steel / brass friction faces, steel
  washers on both faces, positive key to the hub; bench test step in the instructions**; stop block az 270° ± 19.0°,
  r 17.0…21.0, top ≥ −102.3; base FFC 1.0 mm pitch 10-pole (4 VBAT, 4 GND, DATA, WAKE) up through the floor slot to the
  carrier ZIF; the J1 pinion orbit r 28.0 is hidden by the base (no skirt on the torso).
* **Firmware:** STS3215 torque limit ≤ 30 %, temperature limit 65 °C (Feetech register; value UNVERIFIED), J1 ±150°.

### 17.5 Lift module (PAN) – everything removable through the door
* **MG90S** as rev. 1: shaft ‖X at (y 23.2, z −24.2), output −X; case x −6.5…16.0, y 17.1…29.3, z −41.1…−18.3; turret
  x −12.5…−6.5 (r 5.9 + lobe r 2.9 at z −29.8); upper tab x −2.5…0.0, z −18.3…−13.45, hole Ø2.2 at z −15.85; the lower
  tab is cut off. **Its spline count is UNVERIFIED (listings say 20T / 21T / 25T) – count the teeth of the purchased
  servo before buying the arm.**
* **Pocket = P_drziak_serva (resin, S02/S12):** turret end wall x −8.5…−6.5, y 15.1…29.3, z −41.9…−16.3 with a keyhole
  hole (r 6.05 about (y 23.2, z −24.2) + r 3.05 about (23.2, −29.8)) – this hole carries the crank load (bearing
  30/(11.8 × 2.0) = 1.3 MPa); bottom-cover end wall x 16.0…18.0, y 15.1…26.5, z −41.9…−18.3 with a 0.5 PORON pad on the
  case end (pushes the case against the turret wall); back plate y 15.1…17.1, x −8.5…18.0, z −41.9…−13.0; tab post
  x 0.0…8.0, y 17.1…26.2, z −18.0…−12.3 with a DIN 562 M2 slot (x 5.0…6.3, from the top) for F11; stop bridge + lug
  (17.2.4). No floor under the case (a floor ≥ 2.0 would pass 0.2 over the static FFC wall top −43.0). All inside
  roots R1.0, external edges ≥ R0.5. F10 holes Ø2.3 + dowel hole Ø2.05 at the pads (17.3). Everything inside PAN_ENV.
* **Crank:** bought aluminium servo arm for the measured MG90S spline (single arm, ≥ 14 mm hole span, M2 clamp or
  centre screw; e.g. "MG90S / SG90 aluminium servo arm 25T M2" – product UNVERIFIED), arm plane x −17.5…−15.5 (thickness
  UNVERIFIED: shim to the 0.4 ear gap with 0.1 washers on the spline), hub toward the servo. Crank pin: steel dowel
  ISO 8734 2 m6 × 8 pressed (metal–metal) + Loctite 638 into a Ø2.00 hole drilled at **r 10.00 ± 0.05** from the spline
  axis (a ±0.1 error moves the stroke only ±0.2: dead centres), protruding −X to x −20.4 through the ear slot.
  Fallback (P05) if no aluminium arm fits: the supplied POM horn with the pin in double shear (horn + 2.0 Al cover plate
  riveted by the pin), K12 row with 9.4 MPa in the horn (zjednodusenie m05).
* **Ear L_ucho (metal, S02/S14):** 5754-H22 aluminium 2.0 (or 304 stainless 1.5), one 90° bend (inner R 2.0 Al / 1.5 SS),
  bend line ‖Z at the outer corner (x −19.9, y 9.9). Plate (y–z plane) x −19.9…−17.9, y 9.9…25.1, z −40.5…−31.9
  (z_rel −6.3…+2.3 to the slot centre −34.2), far top corner chamfer 1.5; slot 2.20 wide (z −35.30…−33.10), y 11.6…24.3,
  full-round ends. Flange (x–z plane) y 9.9…11.9, x −19.9…−7.5, z −40.5…−36.5. **Drawing (PNG + DXF flat pattern) by the
  docs agent from these numbers.**
* **Foot L_pata (metal):** aluminium flat bar 20 × 4 (EN AW-6060 / 6061 / 5754), cut 44.6 long, filed to 19.6 wide;
  x ±22.3, y ±9.8, z −40.5…−36.5, corners R0.8. Features: Ø11.0 through hole at (0, 0); DPS_krk slot from the +X end
  y −7.4…6.4, x 9.0…22.3 (through, 13.8 wide; prongs 2.4 and 3.4); 2 × M2 tapped holes along +Y in the back face
  (y 9.8) at (x −15.0, z −38.5) and (x −9.0, z −38.5), drill Ø1.6 × 7, tap M2 × 5 (wall to the faces 1.0 Al). Bonded to the
  FRONT neck half only (abrade, epoxy, release film under the back half). Mass ≈ 8.5 g.
* **F12 ear → foot:** 2 × ISO 7380 M2 × 6 + DIN 125 M2 along −Y through the ear flange into the tapped foot (metal–metal;
  S04 fix). L1 × 2 at lift 0 / 20: screw tension ≤ 100 N each (lever 2.0, 13.4 behind) → M2 8.8 at 47 MPa ✓.
* **Rest gap / park:** foot underside −40.50 over the hub disc top −40.65 (0.15); firmware parks at lift 0 (crank
  θ = 3°…177° working range, park θ = 3°).

### 17.6 Cables, connectors, electronics (D2)
* **Pan + lift FFC (A11):** 2 × stock FFC 0.5 mm pitch, **5 poles (width 3.0), length 203 mm, contacts same side (Type A)**,
  stiffened ends 0.3 thick, flex ≈ 0.1 thick; e.g. Molex Premo-Flex 15166 series 5-circuit 203 mm Type A (exact part
  number from the series table – UNVERIFIED; 6-circuit 203 mm is 0151660065, 0.12 thick per the Molex listing) or Würth
  WR-FFC 0.5 mm 5p 200 mm. The two FFCs run STACKED (flat faces together) through the pan loop and separate only in the
  last 15 mm at each end. Conductors: FFC-A 5V, 5V, GND, GND, TX; FFC-B 5V, GND, RX, PWM_TILT, PWM_LIFT (3 × 5 V, 3 × GND:
  1.5 A per rail rated vs 1.4 A peak). Bend radii: pan U-turn R 3.2 (R/t 32), lift loop R 3.0 (R/t 30) – bench-cycle 10⁵.
  * Route (stage frame unless B): carrier ZIFs (top edge) → up behind the cradle back wall → cradle wall slot
    (x 17…24, z −51) → deck slot (B az 26…34, r 22.4…23.6) → static anchor = Kapton tape on the static wall inner face
    at B az 30 → outer run on the wall r 23.5 → U-turn (B az 46.6…121.4 for pan ±90) → inner run on the drum r 16.70 →
    rotating anchor (Kapton + epoxy dot) on the drum at stage az 14 → riser up the outside of the back floor at stage
    az 14 (r 16.7…25.0, bonded flat, 0.3 groove) → fixed leg bonded flat on the +X end wall outer face (x 25.1,
    y 0…3, z −41.0…−27.0) → flat U in the x–z plane R 3.0 (outer leg x ≤ 31.3) → moving leg into the end window →
    2 ZIFs of DPS_krk (mouths at x 22.2, z −38.3…−37.8).
  * Rolling loop numbers: drum r 16.70, wall r 23.50, U-turn R 3.2, k = 16.7 / (16.7 + 23.5) = 0.415; U-turn at B az
    84.0 + 0.415 · pan; free length anchor-to-anchor 52.6 mm; drum wrap 32°…122°.
  * Envelope `FFC_LIFT2`: x 25.1…31.3, y −3.5…3.5, z −41.5…−13.5 (lift 0…20), r ≤ 31.7.
* **DPS_krk (new rigid PCB):** FR4 0.8, 13.0 (x 9.2…22.2) × 13.4 (y −6.9…6.5), in the foot slot with its top face at
  z −37.0 (0.5 below the foot top, solder fillets clear the neck), bonded to the slot walls; underside: 2 × Hirose
  **FH19SC-5S-0.5SH** (0.5 mm, 5 poles, ZIF, for 0.3 mm FFC, height 0.9…1.0 – UNVERIFIED for 5 poles; if not stocked use
  FH19SC-6S with a 6-pole FFC pair and raise nothing: 3.5 FFC then has 0.6 to the wall top – K3 must accept, otherwise
  keep 5 poles), mouths at x 22.2 facing +X, z −38.0…−37.0, bodies y −6.4…−1.2 and 0.2…5.4. Top face: 7 pads under
  the neck wire exits (x 12.0…14.6: head 5V, GND, TX, RX at y 0…2.4; tilt servo 5V, GND, PWM at y −6.7…−3.7) + 3 pads
  (x 20.0…22.0, y −6.0…−3.0) for the lift pigtail. Wires are soldered on the bench before bonding.
* **Lift-servo pigtail:** 3 × AWG30 silicone, 70 mm, from DPS_krk out of the slot mouth → hanging loop beside the FFC
  loop (x 25.1…30.0, y 4.0…7.0, z −41.0…−14.0) → inline Dupont 1 × 3 (2.54) female housing; the MG90S lead is shortened
  to 60 mm with the male side; the plug pair is parked in a clip slot on the bracket post (x 4…8, y 26.2…28.0, z −16…−13).
* **Carrier DPS_riadenie (rev. 2):** PCB 46.0 × 18.0 × 1.6, vertical, x −23.0…23.0, y 16.50…18.10 (all parts on the +Y
  face, ≤ y 23.5), z −71.5…−53.5 (top 1.0 below the bridge / deck bosses). **ESP32-S3-Zero** (Waveshare, 23.5 × 18) on the
  +Y face at x −0.5…23.0, USB-C mouth at (−0.5, ≈20.2, −62.5) **facing −X**; plug envelope x −21.0…−0.5, y 17.0…24.0,
  z −66.5…−58.5 kept free (the plug and cable lie inside the door opening, M12). Connector zones on the −X half (mating
  faces toward +Y = door, or FFC entry from the edge):
  | ref | part (UNVERIFIED part numbers marked) | position (x, z) | to |
  |---|---|---|---|
  | J_PAN_A, J_PAN_B | Hirose FH12-5S-0.5SH(55), 0.5 mm, 5 p, ZIF, FFC from the top edge | x −22.5…−16.4 / −15.4…−9.3, z −57.5…−53.5 | pan / lift FFC pair |
  | J_BUS_V | 3-pin 2.50 mm vertical header, Feetech/Molex-5264-compatible housing (e.g. Molex 5268-03A, UNVERIFIED) | x −8.5…−1.0, z −58.0…−53.5 | STS3215: **VBAT** / GND / DATA |
  | J_J1 | Hirose FH12-10S-1SH(55), 1.0 mm, 10 p, ZIF, FFC from the bottom edge | x −22.5…−8.0, z −71.5…−67.0 | base FFC (4 VBAT, 4 GND, DATA, WAKE) |
  | J_BUS_5 | as J_BUS_V | x −7.5…−0.5, z −71.5…−67.0 | STS3032: **5 V** / GND / DATA (listings give 4.8–6 V or 4–7.4 V – feed 5 V, safe for both) |
  | LED, speaker | inline Dupont 1 × 3 (LED 5V/GND/DIN) and 1 × 2 (speaker, at the amplifier) in the pigtails | free in the door zone | unplugged before T_stred comes off |
  | buck, amp, capacitor | soldered pigtails to pads at the −X / +X edges (static parts) | edges | MAX98357A: BCLK, LRC, DIN, 5V, GND |
  Reach: every ZIF latch and header is at z −71.5…−53.5, x −22.5…0, y ≤ 21 – straight line from the door opening
  (x ±28.25, z −72.25…−11.75) at pan 0 (the stage is above z −41.9). Pin table: docs agent, from the conductor lists above.
* **Bus power (M14):** two separate headers (VBAT for STS3215, 5 V for STS3032); daisy chain removed.
* **J1 crossing:** base FFC (1.0 mm, 10 p) through the floor slot; the slip ring is not used.

### 17.7 Shells and front (OBAL)
* **T_stred:** journal bore **r 26.65 for z −10.50…−2.00** (add the ring r 26.65…28.35 to the existing tube, then the
  shoulder face at z −2.00; ring seat r 28.35 for z −2.00…4.00 unchanged; tube outer r 30.6 unchanged → wall 3.95);
  lower edge chamfer 0.5 × 45°; bore tolerance r 26.65 +0.05/0 (sand to fit: the taped stage turns freely, no shake).
  Recipe: add `tube_z(28.40, 26.65, −10.50, −2.00)` overlapping the old bore face by 0.05 (never coincident), on the cached
  rev. 1 part; the extra resin is ≈ 2.9 g. F1 bosses r 3.2 → **3.4**, bonded M2.5 inserts (hole Ø3.6 × 4.3). Front-stack
  bosses unchanged (thread-forming, one-time). **Door top-seam tongue:** along the door-opening top edge for |x| ≤ 20.6
  (where the ledge is omitted) T_stred keeps the inner half of its wall (inset 1.1…2.2) 1.0 below the opening edge
  (tongue z −12.75…−11.75); the door loses the same volume (17.7 door) – the seam line of sight ends on the tongue,
  nothing enters PAN_ENV. Everything else of T_stred unchanged (approved exterior, seams, K8).
* **T_dvere:** delete both hook tabs and their roots (P07, S15); top edge: the outer half (inset 0…1.1) runs to z −12.00
  (seam 0.25), the inner half (inset 1.1…2.2) stops at z −13.00 (0.25 under the tongue) for |x| ≤ 20.6; ledge + 4 magnet
  pairs locate it (unchanged); finger notch 12 × 1.2 × 0.85 in the bottom edge (OBAL DOOR_NOTCH) + suction cup Ø30 to open.
* **T_bok_L / T_bok_P:** unchanged (one continuous seam lip, seat flange, notch r 14.0).
* **T_klb_L / T_klb_P:** neck **x 38.6…40.6** (−0.2, m18: the cap flange 39.1…40.6 is always clamped); R0.5 at the
  neck / body step (x 40.6) and at the body / end step (x 50.956), R1.0 where the 0.5 socket seam allows (m16); **F8 pattern
  az 60°, 180°, 300°** (counterbores Ø4.2 to x 45.0, clearance Ø2.3); **magnets az 0°, 120°, 240°**; key 2.9 × 1.4 at
  az 0°; bush bore Ø8.05 from the end face to x 44.0 + recess Ø10.2 to x 38.6 and the wire groove = **frozen arm
  interface** (P08; T_puzdro + disc springs deleted, arm round).
* **T_drziak_repro:** ring 1.6 → 2.0 thick, DIN 125 M2 washers under the 3 heads (m19). Front-bracket merge P10: **not done**
  (keeps two small prints; the merged part would need a thin strap across the light box – no screw saved).
* T_svetlovod, T_mriezka, T_drziak_led: unchanged (resin; T_svetlovod clear).

### 17.8 Part list rev. 2 (owner = module that models it)
| name | owner | grp | material | note |
|---|---|---|---|---|
| T_stred | obal | T | tough resin, painted white | bore step + shoulder, F1 r 3.4, door tongue |
| T_bok_L, T_bok_P | obal | T | tough resin, white | unchanged |
| T_dvere | obal | T | tough resin, white | hooks deleted, stepped top edge |
| T_klb_L, T_klb_P | obal | T | tough resin, black | neck −0.2, R0.5, F8 / magnets turned |
| T_svetlovod | obal | T | clear resin (standard allowed) | unchanged |
| T_mriezka, T_drziak_led | obal | T | tough resin | unchanged |
| T_drziak_repro | obal | T | tough resin | ring 2.0 |
| **T_spodok** | ram | T | tough resin, black | merged with T_ram (17.4) |
| T_paluba | ram | T | tough resin | deck lid 2.0, C-shape, FFC wall + slot |
| **T_cap** | ram | T | tough resin | pivot boss Ø7.70 × 4.40 (new) |
| **T_most** | ram | T | Al 5754-H22 / 6061-T6 sheet 2.0 (custom, hand cut) | pivot bridge 18 × 36, tapped M3 (new) |
| Z_naboj_test | ram | Z | tough resin | bench stand; sun-gear stub to the new plane −90…−86; stop block az 270 ± 19.0 |
| P_sachta | pan | P | tough resin, black | slim (17.3) |
| P_drziak_serva | pan | P | tough resin | pocket + stop lug (17.5) |
| **L_pata** | pan | L | Al flat bar 20 × 4 (custom, hand cut) | was resin |
| **L_ucho** | pan | L | 304 stainless 1.5 (preferred) or 6061-T6 2.0 (custom, bent) | was POM |
| koleso_pan | pan | P | bought: brass 36T m0.8 face 4 bore 8 H7 | was printed P_koleso |
| pastorok_pan | ram | T | bought: steel / brass 18T m0.8 bore 5 | Loctite 638 on the spline |
| pastorok_J1 | ram | T | bought: brass 18T m1 bore 6 | Loctite 638 on the spline |
| rameno_zdvih | pan | P | bought: Al servo arm for the MG90S | replaces P_kluka |
| cap_kluky | pan | P | steel dowel ISO 8734 2 m6 × 8 | pressed + 638 in the arm |
| koliky_dorazu (2) | ram | T | steel dowel ISO 8734 3 m6 × 12 | bonded in T_spodok posts |
| kolik_F10 | pan | P | steel dowel ISO 8734 2 m6 × 6 | bonded in the pad |
| ffc_A, ffc_B | pan | P/L | 0.5 mm 5 p 203 mm Type A FFC | replaces fpc_pan |
| DPS_krk | pan | L | FR4 0.8 + 2 × FH19SC-5S-0.5SH | new |
| pigtail_zdvih | pan | L | 3 × AWG30 + Dupont 1 × 3 | new |
| DPS_riadenie | ram | T | carrier (17.6) | new layout |
| servo_J1, servo_pan, servo_zdvih, menic, zosilnovac, kondenzator, reproduktor, DPS_led, magnets, 6805 | as rev. 1 | | | positions per 17.2 / 17.4 / 17.6 |
| ptfe_podlozka | ram | T | PTFE 24 × 10 × 0.3 | ID 12.4 → 10.0 |
| ptfe_pas_capu, ptfe_cap | pan / ram | | PTFE tape 0.13 | journal band 7 × 167; boss wrap 4.4 × 25 |
| podlozky_J1 | ram | T | PET 0.1 strips 4 × 30 (2–6) | J1 top shim + C shims |
| **deleted** | – | – | – | T_ram (merged), T_prichytka_fpc, T_puzdro_L/P, P_koleso, P_kluka, L_jazyk, fpc_pan, spoj_zdvih, cap_pan, kolik_dorazu (old), koliky_kolesa, kolik_ucha, F2, F5, F6, F9, skr_fpc, skr_jazyka, skr_kluky, disc springs, all heat-set inserts |

### 17.9 Fasteners, inserts, drill, torque (S03, Z3.4–Z3.6)
**Screws (all ISO 7380-1 button head, steel 10.9 / A2 – M2 / M2.5 sizes are catalogue nominal, UNVERIFIED: M2 dk 3.5 k 1.3,
M2.5 dk 4.7 k 1.375, M3 dk 5.7 k 1.65).**
| # | joint | qty | screw | washer | into | direction / position |
|---|---|---|---|---|---|---|
| F1 | T_spodok → T_stred | 4 | M2.5 × 8 | DIN 125 M2.5 | bonded M2.5 insert, T_stred boss r 3.4 | +Z from below at (±29.0, ±19.0); Ø3.2 holes (float, M11), counterbore Ø6.5 × 1.9 in the pad |
| F3a | T_paluba → T_spodok | 4 | M2.5 × 6 | DIN 125 M2.5 | bonded M2.5 insert, boss r 3.4 | −Z at (20.0, ±13.8), (−33.5, ±10.0) |
| F3b | T_most → T_spodok | 2 | M2.5 × 6 | DIN 125 M2.5 | bonded M2.5 insert, boss r 3.4 | −Z at (6.0, ±15.95) |
| F4 | pan servo tabs | 2 | M2 × 10 | DIN 125 M2 | DIN 562 M2 nut in the post | −Z at (±14.0, −20.79), slotted ±0.3 |
| F7 | carrier | 2 | M2 × 6 | DIN 125 M2 | bonded M2 insert, boss r 3.25 | −Y (door) at (±19.0, z −62.5) |
| F8 | T_klb → column | 3 + 3 | M2 × 10 | DIN 125 M2 | bonded M2 insert, column boss | ∓X, r 7.5 at az 60/180/300 |
| F10 | lift module → well | 2 + dowel | M2 × 6 | DIN 125 M2 | bonded M2 insert, pad r 3.5 | −Y at (19.5, −31.7), (8.0, −14.5); dowel at (19.5, −27.7) |
| F11 | MG90S upper tab | 1 | M2 × 10 | DIN 125 M2 | DIN 562 M2 nut in the post | +X at (y 23.2, z −15.85) |
| F12 | ear → foot | 2 | M2 × 6 | DIN 125 M2 | tapped M2 in the Al foot (metal) | −Y at (−15.0, −38.5), (−9.0, −38.5) |
| F13 | LED holder, speaker ring | 2 + 3 | M2 × 6 thread-forming for plastics (e.g. EJOT PT K20 class, one-time) | DIN 125 M2 | pilot Ø1.7, boss Ø5, engagement ≥ 4 | as rev. 1 |
| F14 | buck, amplifier | 2 + 2 | M2 × 6 thread-forming, one-time | DIN 125 M2 | pilot Ø1.7, boss Ø5 × 1.5 standoff + web | ±X |
| F15 | pivot | 1 | **M3 × 6** | DIN 9021 M3 (Ø9 × 0.8) | tapped M3 in T_most (metal) | −Z on the axis, through T_cap |
| F16 | J1 servo | 4 | M2 × 6 (thread of the servo case UNVERIFIED) | DIN 125 M2 | servo case holes | +Z from below through the pads |
Kinds: M2 × 6, M2 × 10, M2.5 × 6, M2.5 × 8, M3 × 6 + one thread-forming M2 × 6. No countersunk head anywhere in resin, no
heat-set insert, no thread cut in resin that is opened in service.
**Inserts / nuts:** brass knurled inserts bonded with epoxy – M2: OD 3.2 × 3.0, hole Ø3.3 × 3.3 (+ Ø2.3 pilot 1.0), boss
r ≥ 3.25; M2.5: OD 3.5 × 4.0, hole Ø3.6 × 4.3 (+ Ø2.8 pilot 1.0), boss r ≥ 3.4; engagement ≥ 3.0. Square nuts DIN 562 M2
(4.0 × 4.0 × 1.2): slot 4.1 × 1.35, ≥ 1.5 resin to every free edge.
**Drill / ream after curing** (sharp HSS, low speed, pecking; holes are modelled at FINAL size): Ø1.6 M2 tap drill (Al
foot); Ø1.7 thread-forming pilots; Ø2.0 crank-pin hole in the Al arm (metal press); Ø2.05 F10 dowel; Ø2.3 M2 clearance;
Ø2.4 F16 (file the ±0.3 slot); Ø2.5 M3 tap drill (T_most); Ø2.8 M2.5 clearance; Ø3.05–3.10 stop pins (6.0 deep); Ø3.2
F1 float holes; Ø3.3 / Ø3.6 inserts; Ø3.4 T_cap; Ø5.1 / Ø3.1 magnets; Ø11.0 Al foot (step drill); 8.00 H7 36T gear bore
only if bought smaller (lathe); 26.65 bore / 26.50 journal / 7.96 boss: sand to fit with the PTFE tape; Ø37.15 6805
seat: sand to a slide fit, then epoxy.
**Torque (L7, S03):** M2 into a bonded insert ≤ 0.05 N·m; M2.5 into a bonded insert ≤ 0.09 N·m; M2 into a DIN 562 nut with
the head on resin ≤ 0.05 N·m; M2 thread-forming one-time: seat + 1/8 turn (≤ 0.04 N·m); M2 metal–metal (F12) 0.15 N·m
+ Loctite 222; M3 into T_most through T_cap (F15) ≤ 0.12 N·m + Loctite 222 (T_cap compression ≤ 5 MPa); F16 ≤ 0.05 N·m.
Retaining compound Loctite 638 (or equivalent) only metal–metal: both pinions on their splines, crank pin in the arm.
**Washers:** DIN 125 M2 (2.2 × 5 × 0.3) × 26; DIN 125 M2.5 (2.7 × 6 × 0.5) × 10; DIN 9021 M3 (3.2 × 9 × 0.8) × 1; PET
shim 0.1 strips; PTFE 24 × 10 × 0.3 thrust washer.

### 17.10 Load paths with numbers (to be recomputed on the final geometry by K12)
Limits (Z2/Z4): resin 12 MPa static, 6 MPa sustained / unfilleted notch / abuse (SF 2), epoxy 2.7 MPa working
(8 MPa assumed ultimate); metal parts against their own yield. Numbers below are hand calculations on the 17.x geometry.
**L1 – 15 N up on the head, × 2 = 30 N (lift 0 and 20):**
| interface | element | stress / force | limit | margin |
|---|---|---|---|---|
| neck → foot | epoxy, front neck half on Al (45 × 10) | 0.59 MPa peel (rev. 1 p04 geometry) | ≈ 2 | 3.4 |
| foot → ear | F12 2 × M2 tapped Al, prying lever 2.0 / 13.4 | 100 N per screw → 48 MPa (A_s 2.07) | 640 (8.8) | ≫ |
| ear | 304 1.5 / 6061-T6 2.0 | 18…24 MPa (rev. 1 FE 14.5 MPa scaled to the metal section) | 215 / 240 | ≥ 9 |
| crank pin Ø2 | shear / bending (lever 1.9) | 9.5 / 73 MPa | ≈ 400 | ≥ 5 |
| MG90S output | side load 30 N, 6 mm outboard | – | not published | **risk (UNVERIFIED)** |
| turret keyhole | bearing on Ø11.8 × 2.0 | 1.3 MPa | 6 | 4.6 |
| bracket → well | F10 2 × M2 bonded inserts + dowel | 15 N per insert → 0.5 MPa bond | 2.7 | 5.4 |
| well → gear | epoxy hub disc ↔ gear, 366 mm² | 0.08 MPa (× 3 peel 0.25) | 2.7 | ≥ 10 |
| gear → washer | DIN 9021 M3 on brass r 4.0…4.5 (13.4 mm²) | 2.2 MPa | brass | ≫ |
| F15 → T_most | M3 in 2.0 Al (2.6 threads) | 30 N | ≈ 1.3 kN strip | ≫ |
| T_most | Al 2.0 × 18, span 31.9 | 19.9 MPa, deflection 0.02 | 130 (5754) | 6.5 |
| T_most → T_spodok | F3b 2 × M2.5 bonded inserts | 15 N per insert → 0.34 MPa | 2.7 | 8 |
| → base | cradle walls → floor → plinth → 6805 → base hub | 30 N | – | ≫ |
The stop pins stay engaged under L1 (play 0.10, engagement 2.50 left).
**L2 – 30 N down:**
* lift 0: the chain foot → ear → pin → arm → MG90S (crank at BDC, no servo torque) → keyhole wall deflects / MG90S
  output play ≥ 0.1 (UNVERIFIED) until the 0.15 rest gap closes, then: foot (Al) on the hub disc ring (366 mm² → 0.08 MPa)
  → gear → PTFE washer (389 mm² → 0.08 MPa) → T_most / deck → 0.1 shims (240 mm² → 0.13 MPa) → STS3215 case → 4 corner
  pads (100 mm² → 0.30 MPa) → cap floor → plinth → 6805 (0.24 MPa, rev. 1 p08) → base. Before the gap closes the chain
  carries at most what it carries at lift 20 (below).
* lift 20 (TDC, no landing): ear 60 MPa (rev. 1 FE on the resin outline) → 75 MPa in 6061-T6 2.0 (margin 3.2) / 100 MPa in
  304 1.5 (2.15); slot bearing 7.5 MPa (metal); turret keyhole 1.3 MPa; F11 / F10 rows as L1 × 1.0; pad roots r 3.5 + R1:
  8.2 MPa (rev. 1, r 3.0 sharp) × (3.0/3.5)³ / 1.3 ≈ 4.0 MPa ✓.
* mid lift: the crank back-drives the MG90S (0.30 N·m > stall 0.216 N·m) and the head sinks onto the hub disc – by design.
**L3 / L8 – pan:** gear teeth 34.6 / 50.8 MPa (36T brass), 42.2 / 62.0 MPa (18T); pivot journal 44 / 65 N radial on the
taped boss Ø7.96 × 4.0 → 1.4 / 2.0 MPa (Z3.8 ≤ 5 ✓); T_cap root (clamped by F15 at 200 N; moment 65 N × 2.3) – K12 FE;
stop at ±90: 20 / 29 N on the Ø3 pins (bearing 3.7 MPa, pin 43 MPa), lug root 6.4 MPa nominal → K12 (R1.5, widen if > 6);
stop torque into the lift module joint F10 + dowel (K12 row).
**L4 / L8 – J1:** slip clutch 0.25…0.40 N·m (base safety part) → J1 pinion (m1 18T b 4.0 brass) Ft 44 N → 36 MPa; cradle
walls 2.5 → 1.2…2.5 MPa (rev. 1 3…6 MPa at 1.6 × (1.6/2.5)²); stop lug 4 × 4 R1 at the clutch limit 21 N → 3.9 MPa
(a hand cannot exceed the clutch); locked clutch at STS3215 stall: the 638 joint releases at ≈ 1.1 N·m before the teeth
yield (244 MPa at 2.17 N·m).
**L5 / L6 – arm:** column web 3.0 + box closure z −52…−34 + R2 roots: K12 recomputes rows 42–46 of `overenie_pevnost.md`
(U-channel 23…26 MPa in rev. 1 – the box and the 3.0 web must bring them ≤ 6, otherwise the box closure is extended down).
**L7:** torque table 17.9; door pull-off: hooks deleted, 4 magnet pairs ≈ 24 N; nothing handled is < 1.2.

### 17.11 Assembly order (bench groups B, torso steps T; direction per step, K7 rows)
* **B1 T_spodok:** drill / ream per 17.9; bond inserts F3a (4), F3b (2), F7 (2), F8 (6); bond the stop pins (6.0 deep,
  24 h); 6805 into the Ø37.15 seat with epoxy; tie saddles and capacitor saddle clean.
* **B2 deck set:** cut / drill / tap T_most; bond T_cap on T_most (centred by a temporary M3 screw, 24 h); PTFE tape on
  T_cap; static FFC anchor area on T_paluba cleaned.
* **B3 T_stred:** F1 inserts (bonded), magnets, front stack (F13), LED / speaker pigtails with inline plugs.
* **B4 stage:** PTFE tape on the journal band; bond the 36T gear under the hub disc (gear tips centred in the drum shroud
  with a 0.3 shim strip, 24 h); F10 inserts + dowel; FFC pair: rotating anchor on the drum (stage az 14), riser, fixed
  leg bonded on the +X end wall; both FFC tails left free at the carrier end.
* **B5 lift module:** MG90S into P_drziak_serva (PORON pad, F11 + nut); Al arm: drill Ø2.00 at r 10.00, press the pin
  + 638; arm on the spline at BDC (servo at θ 3°, 500…520 µs – set with a tester), arm screw.
* **B6 neck:** B montáž 1–8; Al foot (drilled, slotted, tapped) bonded to the FRONT half only; DPS_krk: 7 neck wires +
  pigtail soldered, board bonded into the foot slot; test the tilt servo through the ZIFs on the bench.
* **B7 pinions:** pan pinion on the STS3032 spline (638, 24 h); J1 pinion on the STS3215 spline (638, 24 h).
| T | step | direction / access |
|---|---|---|
| 1 | STS3215 + pinion into the cradle (pinion through J1_PASS), F16 × 4 from below loose; C 18.00 with shims on the dummy hub; F16 tight | −Z, then +Z tools from below |
| 2 | STS3032 + pinion onto the posts, F4 loose (C set in T7) | −Z |
| 3 | shim strips on the STS3215 top; T_paluba (F3a), T_most + T_cap into the slot (F3b), PTFE washer | −Z |
| 4 | carrier (F7), buck / amp (F14), capacitor (saddle + tie), wiring in the tie saddles; FFC pair: carrier ZIFs → cradle-wall slot → deck slot → static anchor; bench test on Z_naboj_test | ±X, −Y |
| 5 | T_stred over the tower, F1 loose; plug LED + speaker inline plugs through the door | −Z |
| 6 | glue `golier_prstenec` on the new shoulder z −2.0 (flat plate on top) | −Z |
| 7 | stage (gear + FFC loop) down through the ring onto T_cap / PTFE; F15 + DIN 9021 through the empty well (hex 2.0, straight on the axis); check axial play 0.10; set pan C / backlash and tighten F4 with a ball-end 1.3 hex through the bore (straight tools at r 25.2 touch the bore); spin ±85 by hand (no stop yet!) – then tighten F1 | −Z |
| 8 | lift module through the door onto the pads (dowel), F10 × 2 | door, pan 0 |
| 9 | neck from above (B 9) | −Z |
| 10 | pan +85: FFC pair into the DPS_krk ZIFs, pigtail plug to the MG90S plug, plug into the post clip | door |
| 11 | pan 0, crank at BDC: ear onto the pin, F12 × 2; cycle lift 0…20; rest gap 0.10…0.20 (feeler) | door |
| 12 | `golier_kotuc` (B 10) glued on the stage top | −Z |
| 13 | T_bok_L / T_bok_P, T_klb (F8) | ∓X |
| 14 | door | −Y |
| 15 | head (B 11–21) | – |
| 16 | torso onto the base (base FFC into J_J1 through the door before closing it) | −Z |
**Service (every servo; reverse of the steps named):**
* **Tilt MG90S (in the neck):** head off (B E1–E5) → door, pan +85: open the 2 DPS_krk ZIFs, unplug the pigtail → pan 0:
  F12 × 2, ear off the pin through the door → neck + foot + DPS_krk up through the disc slot (board 13.4 < slot 20.5) → B E7.
* **Lift MG90S:** door: pigtail (pan +85); F12 + ear (pan 0); F10 × 2 → lift module out through the door → F11 on the bench.
* **Pan STS3032 / pan pinion / FFC pair / gear:** neck out + lift module out (above) → F15 out → open the carrier ZIFs →
  fold the lift-loop leg flat on the end wall (r ≤ 26.3, Kapton) → stage + gear + FFC pair up through the ring → torso
  off the base, F1 × 4, T_klb / T_bok off, LED / speaker plugs off → T_stred up → F4 × 2 → servo out (its case corner r 29.5
  cannot pass the r 26.65 bore – T_stred must come off).
* **J1 STS3215:** as pan + F3a × 4, F3b × 2 → deck + bridge off → F16 × 4 from below → servo up with its pinion.
* **Carrier / buck / amp:** carrier through the door (F7, ZIFs, plugs); buck / amp: side caps off (T_klb F8, slide ±X).

### 17.12 Zones and ownership (rev. 2) – supersedes §12 where different
| owner | owns (parts) | zone |
|---|---|---|
| **OBAL** | T_stred, T_bok_L/P, T_dvere, T_klb_L/P, T_svetlovod, T_mriezka, T_drziak_led, T_drziak_repro, magnets, speaker, DPS_led | shell between the exterior and inset 2.2; collar tube r ≤ 30.6, z ≥ −10.5 **with the bore r 26.65 (z −10.5…−2.0)**; door ledge / pads / tongue; socket tubes; seam lip; 4 F1 bosses (r 3.4, x ±(25.6…32.4), \|y\| ≥ 15.6, z −81…−75); front stack (rev. 1) |
| **RAM** | T_spodok (merged), T_paluba, T_cap, T_most, Z_naboj_test, servo_J1 + pastorok_J1, servo_pan + pastorok_pan, stop pins, carrier + ESP32, buck, amp, capacitor, PTFE washer, shims, all F1/F3/F4/F7/F8/F14/F15/F16 hardware | tower inside the lip outline − 0.5 (\|x\| ≤ 33.3, z > −78) and the tub − 0.3 below; columns \|x\| 34.4…42.0; everything below z −84.5; deck up to z −46.20 (r ≤ 26.6 in B az 16…232 except the FFC wall r 23.5…25.1 up to −43.0, B az 15…165, and the 2 stop pins up to −44.6 at r 30.0); T_cap up to −41.80 + washer / F15 head up to −39.35 at r ≤ 4.5; pan pinion r 8.0 about PAN_AX, z −45.9…−41.9 |
| **PAN** | P_sachta, P_drziak_serva, koleso_pan (36T), rameno_zdvih + cap_kluky, servo_zdvih, L_ucho, L_pata, DPS_krk, FFC pair, pigtail, kolik_F10, PTFE tapes on the stage, F10/F11/F12 hardware | PAN_ENV rev. 2 (17.3) swept over pan −90…90, lift parts additionally 0…20; the FFC static run (deck slot → static wall) and the carrier ends of the FFC are PAN's cable inside RAM's zone (RAM models the slot / wall, PAN models the cable) |
Shared interfaces (provider → user, numbers in 17.x):
| interface | provider | user | numbers |
|---|---|---|---|
| journal bore r 26.65, z −10.5…−2.0, shoulder z −2.0 | OBAL | PAN (journal r 26.50), B ring | 17.7 |
| T_cap Ø7.96 taped, top −41.80, washer Ø9, F15 head ≤ −39.35, r ≤ 4.5 | RAM | PAN (gear bore 8.00, foot hole Ø11) | 17.1 |
| PTFE plane −46.20 / −45.90, ID 10 OD 24 | RAM | PAN (gear bottom) | 17.1 |
| gear plane −45.90…−41.90, C 21.600 at PAN_AX | RAM (pinion) | PAN (36T) | 17.2 |
| static FFC wall r 23.5…25.1 top −43.0, deck slot B az 26…34, cradle-wall slot | RAM | PAN (FFC) | 17.6 |
| stop pins r 30.0 at B az 25.43 / 224.57, top −44.60 | RAM | PAN (lug) | 17.2.4 |
| carrier ZIF positions, FFC entry from the top edge | RAM | PAN (FFC length 203) | 17.6 |
| door opening x ±28.25, z −72.25…−11.75 = tool / plug access | OBAL | RAM, PAN | 17.11 |
| spigot, F1 bosses, Ø3.2 holes | RAM | OBAL | 17.4 / 17.7 |
| column boss face x ±38.4, stop ring ±39.1, key az 0, F8 az 60/180/300 | RAM | OBAL (T_klb, T_bok) | 17.4 / 17.7 |
| foot top z −36.5 = neck bottom, wire exits x 12.0…14.6 | B | PAN (foot, DPS_krk) | 17.5 |
| base interface | RAM | base round | 17.4 |

### 17.13 Open / UNVERIFIED (do not treat as passed)
1. Bought-part data from search snippets only (vendor pages unreachable): STS3032 spline (25T, tip Ø4.95) and voltage
   (4.8–6 V vs 4–7.4 V → fed 5 V), STS3215 case-hole positions / thread (F16) and spline length (2.2), MG90S spline count
   (20T / 21T / 25T claims) → aluminium arm product, gear part numbers (KHK BSS0.8-36 / -18 shape and bore, RS PRO 878-7862
   face / hub, KHK BSS1-18B face), 5-pole FH12 / FH19SC and 15166 part numbers, ISO 7380 M2 / M2.5 head sizes.
2. MG90S output side-load rating (L1 / L2 30 N) – not published.
3. K12 must confirm by FE: stop lug root (6.4 MPa nominal), T_cap root under the pan radial load, column box (L5), the
   F10 joint under the stop torque.
4. Epoxy shear 8 MPa (assumed), Loctite 638 on splines ≈ 10 MPa effective (assumed; spline engagement 2.2 on J1).
5. FFC bend life at R/t 30–32: bench-cycle 10⁵ before trusting it.
6. Feetech temperature-limit register value (firmware 65 °C target).

### 17.14 Checks run by the architect and the builders' task lists
* `python -c "import t4_common as C; C.rev2_check()"` (numbers only, no CAD): stack 48.00 = 48.00; stage ↔ ring 0.248;
  journal 0.15; tube wall 3.95; C(pan) 21.600 from PAN_AX; pivot radial 0.02; washer overlap 0.50; stop pins at B az
  25.44 / 224.56 from the lug faces (r 30.0 → (27.09, 12.88), (−21.37, −21.05)), engagement 2.60, bridge 1.00 over the
  pins, lug 1.00 over the cradle; drum vs pinion zone 3.36° / 3.94° = 1.03 / 1.20 mm at r 17.5; rolling loop k 0.415,
  U-turn B az 46.6…121.4 (stage az 31.4…136.6, inside the drum sector 8…140), U-turn R 3.3 (single strip; 3.2 for the
  pair); duct 4.30, FFC wall ↔ floor 1.10; PAN_ENV2 ↔ shell 1.25 (z −40.9…−17), 1.16 (−17…−11.5), 1.84 (top); column
  ↔ PAN_ENV2 1.00; lip margins: stop post 1 6.69, post 2 1.18, carrier corner 1.80; F3a head ↔ lug 1.01.
* `python t4_common.py` (rev. 1 self-test, rev. 2 block imported): exit 0, 30 s (log `rev2_arch/t4_common_selftest.log`).
* NOT run: any CAD of rev. 2, K1–K13. The task lists given to the builders are saved as `rev2_arch/ULOHA_pan.md`,
  `ULOHA_ram.md`, `ULOHA_obal.md`.


### 17.15 Integrator changes (rev. 2 integration, 2026-11-17) – supersede 17.0–17.14 where different
Source of the numbers: `t4_common.py` block `# >>> rev2 (integrator)` (R2 keys FFC_LIFT2, PIGTAIL, FRONT_STACK_RULE, CTRL2, F7,
F1_PATH, TORQUE_REC, WASHERS_REC; PAN2_SUMMARY; OBAL overrides mirrored), `t4_pan.PAN2["FFC"]["loop"]`, `t4_ram.RAM2`
(F3A, CTRL, STOP_POSTS.p2_column, COL.head / plate, F1.keepout_z, BOSS, PAN_POST.leg) and `t4_assembly.py`. Checks: `checks.py` → `checks.json`.

1. **Front stack vs the lift loop (blocker C2 / O3b).** The OBAL front stack (LED holder, LED PCB, speaker ring, speaker; inner
   faces y −29.4…−31.6 for |x| ≤ 22.3, z −70.7…−28.5) is reached by every stage point with stage x > 28.4 below z −28.5 at some
   pan in ±90.3 (outside stage az 37…143). Rule `R2["FRONT_STACK_RULE"]`: below z −28.5 the stage keeps x ≤ 28.35 outside stage
   az 37…143 (PAN_ENV2 r 33.4 / 32.2 applies only above z −28.5 or inside that sector). The **lift loop is a U in the y–z plane**:
   strip width radial (x 25.35…28.35), fixed leg y 6.875 rising from a soft 45° fold CF (x 25.1…28.35, y 4…7, z −30.0…−29.4; part of
   the FREE strip `fpc_lift`, not of the bonded `ffc_riser` → permanent stage r 26.30 ≤ 26.50) on top of the bonded leg (end wall,
   z −41…−30), U centre-line R 3.125 (R/t ≈ 30), U centre z −26.0 + lift/2 (top −12.75 at lift 20),
   moving leg y 0.625 down to the fold block CM on the moving end (z −38.25 + lift ± 0.3; the 45° fold of tail A is a triangle, x ≤
   25.35 + (y + 5.85)). FFC envelope x 25.1…28.35, y −5.85…7.0, z −41.6…−12.75, r ≤ 29.2 (`R2["FFC_LIFT2"]`). Developed length FFC‑A
   190.3 / FFC‑B 178.2 of 203 mm.
2. **Pigtail** rerouted: out of the end window under CM, between the two U legs (descends at y 2.95 when the lift is > 7.5), under CF
   at z ≤ −32, then up to the parked PicoBlade pair; bundle x ≤ 27.6 everywhere below z −28.5 (`R2["PIGTAIL"]`).
3. **Stage removal (S3):** CF is not bonded (Kapton only): open the soft fold, lay the free FFC flat on the end wall (r ≤ 26.3), tuck the
   U and CM into the empty well through the end window, then the stage passes the glued ring; re-fold on reassembly.
4. **T_stred lowering (blocker O3d, step T5).** RAM keep-out for every tower part above the spigot over the FULL height: the boss
   cylinder r 3.40 + 0.25 (= r 3.65 about (±29, ±19); measured: the T_stred footprint toward the tower is the r 3.40 cylinder) and the
   outward web band |y| ≥ 19 for |x| 25.1…32.9 (`t4_ram._f1_keepouts_tower`); the spigot notches keep the rev. 2 box, the deck
   T_paluba additionally gets the box over the two FRONT bosses (front C-ear 0.40 → 0.50). Consequences:
   * post 2 = block x −24.7…−17.87 (pin, bond 8.4 unchanged) on a **column to the floor** x −24.7…−17.2, y −23.6…−15.05, merged with
     the −X pan-servo post; that post's DIN 562 slot is now blind on −X (nut entered from +X before the servo goes in);
   * F3a_1 (26, −13.8) → **(26.0, −11.7)**, boss merged into the front wall (0.3 off the STS3215 mounting ear); T_paluba cut by the
     same keep-out; stop post 1 and the deck C-ear keep 1.2 toward the boss path (unloaded side of pin 1);
   * **carrier DPS_riadenie x −24.9…24.9** (was −27…28.6), no plug notch: the ESP32-S3-Zero sits on its 2.54 pin-header spacer
     (raised 2.5, USB-C mouth (−0.5, 22.7, −62.5), pins trimmed ≤ 1.0 behind the PCB); **F7 = 2 × DIN 7991 M2×5 flush in the FR4
     countersink, no washer, at (−18 / −4, −62.5)** under the plug envelope (reached through the door with no plug in), standoffs
     r 3.25 with bonded M2 inserts; the +X end rests on a pad r 2.5 at x 20; plug envelope x −21…−0.5, y 19.4…26, z −66.5…−58.5;
   * +X pan-post front leg x 12.05…16.45 (was 16.75: 0.0 plan clearance to the T_stred front relief);
   * measured (exact plan clearance while lowering, `integ2_work/lowering.py`, K7 criterion 0.24): servo_pan 0.50, T_paluba 0.50,
     DPS_riadenie 0.80, all other parts ≥ 1.4; the T_spodok spigot band (z ≤ −77.95) is the declared 0.2 locating fit that guides the
     white lip (measured ≈ 0.21, criterion 0.17).
   * **`TOWER_CLEAR` 0.5 → 0.25** (t4_common integrator block; used by checks_obal O3d and K7): the built keep-out is boss r 3.40 +
     0.25; 0.5 would leave stop post 1 a 0.98 wall around its pin (< 1.0). The drop is hand-guided, every face pair that passes is
     vertical (plan clearance > 0 = no ledge) and the spigot (fit 0.21…0.28) locates the lip over the last 3 mm; seated, boss column
     ↔ post 1 is 0.25 nominal (a light sliding contact within the spigot play is harmless – vertical faces, F1 clamps axially).
   The pan pinion is bonded on its spline IN SITU after T5 (step T5b; RAM).
5. **Column (L5) – head + shoulder plate.** The rev. 2 column had only the 3.0 web between the rib tops (−30) and the boss (−28.6):
   Zw 33 mm³ (≈ 33 MPa under L5; RAM had checked z −32 only). Added to both columns: a **head** z −38…−27.5 (web thickened to x 38.4
   over y −14…17, flanges to x 43 / 41.8 outside r 17.1 about the shoulder axis = the T_bok seat flange r 16.6 + 0.5, arm-wire channel
   x 38.4…40 / y 5…12 kept) and a **shoulder plate** x (r 34.5 / flat 34.5 for |y| ≤ 9.5)…38.4, y −17…17, z −38…−8 with chamfered top
   corners (shell inset ≥ 0.45) and the F1 keep-out. Rib tops −30.4 (0.5 to the T_bok socket tube). Column-alone L5 (10 N along X at
   the 72 mm arm tip, M = 720 + 10·(−17 − z) N·mm, Kt 1.3): ≤ 7.6 MPa for z ≤ −28 (was 16.8…33), but **8.65…9.87 MPa at
   z −26…−11 and 12.05 at z −9** (allowable 8.5; Zx 109 / 106 / 108 / 108 / 95 / 108 / 96 / 78 mm³ at z −26 / −24 / −21 / −19 / −17 /
   −14 / −11 / −9). Required Zx = M·1.3 / 8.5 = 124 (z −26) … 110 (z ≥ −17) mm³. Within the fixed envelope the section there cannot
   be larger: it already fills the whole free region – inner face r 34.5 (PAN_ENV2 r 33.4 + 1.1 stage clearance), outer face x 38.4
   (frozen T_klb / T_bok seat flange r 16.6 + 0.5 about the shoulder axis), |y| ≤ 17 (shell inset + T_stred lowering path) – whose
   full section is Zx ≈ 108–109 mm³ < 110; the shoulder-axis bore (z −17) and the top chamfers (z −9) reduce it further. So the
   column ALONE cannot meet Kt 1.3 / 8.5. The T_bok shell is clamped in parallel at the same joint (T_klb shoulder → seat flange →
   stop ring) and is not counted (no FE available here). **Open: 3-D FE of column + T_bok + T_klb (K12); if it
   still fails, the fix needs the frozen arm interface (e.g. a 2 mm steel shoulder plate bonded under the stop ring, or a deeper
   T_bok seat flange cut).**
6. **Insert seats F3a / F3b** through the boss (depth 4.9; the 0.3 floor ring is gone).
7. **FFC plugging:** the two FFCs are plugged into the DPS_krk ZIFs with the stage turned by hand to the +90 stop (line of sight
   0.806 there; 0.775 at the firmware +85). F11 is driven on the bench (lift module out) – its in-situ tool path is information only.
8. **Torques / washers** (Z2): `R2["TORQUE_REC"]` F1 0.045, F3a/F3b 0.045, F4 0.02 + Loctite 222, F7 0.03, F8 0.015 + 222,
   F10 0.04, F11 0.02, F12 0.15 + 222, F13 0.03, F14 0.03, F15 0.08 + 222, F16 0.025 N·m (the 17.9 values fail Z2).
   `R2["WASHERS_REC"]`: F8 ISO 7092 / DIN 433 M2 in the D4.7 counterbore; F10 DIN 433; F7, F4, F12 none (head on FR4 / the servo's
   own tab / steel); DIN 125 under every other head on resin.
9. **Assembly order** (`t4_assembly.py`): T0 T_spodok (B1 inserts, pins, F4 nuts, 6805) on a bench support – **the base hub /
   dummy stand comes only at T15** (F16 and F1 are driven from below) → T1 STS3215 → **T2 STS3032 lowered 5.5 in front of its seat,
   slid +Y (its tabs go into the front-wall slots, the +X tab under the F3b boss), down 0.2 onto the posts**, F4 loose, bus plug pushed
   in afterwards along −X through the +X post window → T3 deck + T_most + T_cap → T4a **capacitor in from the back above the spigot,
   then 6 down** → T4b carrier (F7), T4c buck, T4d amp → **T5 T_stred lowered straight** (F1 loose) → **T5b pan pinion in situ** →
   T6 collar ring → T7 stage + F15 → **T8 neck from above** (no dowel protruding) → **T9 lift module through the door along −Y: the ear
   brings the F12 dowel into the foot** (F10) → FFCs at the +90 stop → T11 F12 (1.3 key) → T12 collar disc → T13 side caps + joints
   (F8) → T14 door → T15 onto the base hub. Bench: B5b F11 with a 1.3 hex key (long leg along the axis; a D4.5 driver meets the MG90S
   after 9.75), B5e F12 dowel bonded in the ear. Service rows: S1 lift module out; S2 neck out (after S1); S3 stage out; S4 F15;
   S5 pan servo (T_stred, stage, lift module, neck **and deck** off; servo + pinion up 0.2, −Y 5.5, up); S6 carrier out through the
   door – **not possible** (see 12).
10. Densities `DENS["alu"] 2.70e-3`, `DENS["stainless"] 7.93e-3` added; OBAL rev. 2 overrides mirrored into `OBAL`.
11. **Deck vs shoulder plate (K7 T3).** T_paluba is kept 0.3 off the +X plate footprint (|y| ≥ 9.2 → r ≤ 34.2; flat x ≤ 34.2
   inside): the rev. 2 deck could not be lowered past the plate (blocked after 8.2 mm). Arm-wire hole D4.5 z −50.5 → **−51.3**
   (0.23 sliver under the bridge top → 0.85, K4).
12. **Carrier service through the door (D6 row S6) – open.** The ESP32-S3-Zero sits at x −0.5…23 (the PCB must reach x ≥ 23, F7 /
   ZIFs / standoffs reach x −21.25), i.e. ≥ 44.3 wide; the door ledge of T_stred and the frame magnets leave a clear opening
   x −20.76…20.76 at the carrier height (z −71.5…−53.5). No straight or rotated path exists (K7 S6: blocked after 6.75 mm). Today the
   carrier comes out only with T_stred off (S5 route). Fix for rev. 3: ESP32-S3-Zero turned 180° (USB-C facing +X) and the board
   ≤ 41 wide (x −20.3…20.3), or a narrower door ledge (OBAL).
13. **F12 dowel** (D2 × 4.5) is **bonded (Loctite 638) in the ear flange** and has a slip fit D2.05 in the Al foot (was pressed into
   the foot): with the dowel in the foot the neck could not pass the stage well rim / the collar-disc slot (K7 T9 / S2).
14. **K4 declarations (checks.py):** F7 insert floors at the new F7 positions (|x| 2…6 and 16…20), F8 insert floors 0.7 behind the
   bonded M2 inserts of the shoulder boss (D2.3 pilot through, insert pull outward), wire-hole ring min 0.6.
15. **Checks** (`checks.py` → `checks.json`, final clean run after `build_all.py`): K1–K6, K8–K11, K13 PASS;
   K7 FAIL only for the D6 row S6 (item 12); K12 FAIL only for the column-alone L5 rows at z −26…−9 (item 5; 2 rows not verifiable:
   MG90S side load, topple input). Details: `STATUS_rev2_integrator.md`.

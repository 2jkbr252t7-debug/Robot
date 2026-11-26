# NOVA mini – arm drive B2 "maximum print, minimum bought parts"

Work dir: `/tmp/claude-0/gapwf/fin/R2c/B2_max_tlac` (all scripts, logs and JSON results are here).
Frame B: mm, Z up, front −Y, robot left +X. Values are for the LEFT side. The RIGHT side is the mirror x → −x and was
checked separately (chk/paths/colroom with side R).
Base: arm design v2 (judge-final K3 + fixes). Kept from v2: servo position, column pocket, plug, arm at dx −1.0, the visible
look (black plug recessed 1.0 + black Ø13 ring, gap 3.70 / ≥ 1.00), T_bok notch idea, F3a_2 move, electronics moves.

## 0. Verdict

**Feasible.** The bought list is the servo, 4 M2 screws, 4 glued M2 brass inserts, 3 small magnets, 1 steel washer,
glue and a dry lubricant per arm. No bearings and no metal work. Everything special is printed in Elegoo Tough.

What decides whether it works in practice is still unverified: the wear rate of printed resin on resin, the real slip torque
of the clutch (it is tuned on the robot with a coin test), and the FE of the column. Section 9 lists these points.

### Slovak summary (for the user)

Všetko špeciálne je vytlačené z Elegoo Tough. Patria sem kužeľové kolieska (12/18 zubov, modul 0,65), pastorok spolu s hriadeľom
a s nasadením na drážkovanie serva v jednom kuse, koleso spolu s hriadeľom ruky v jednom kuse, puzdrá, spojka a vložka jazýčka.
Kupuje sa len servo, štyri skrutky M2, štyri mosadzné vložky M2, tri malé magnety Ø4×2, jedna oceľová podložka M8 (veľká),
lepidlo a grafitový prášok. Nie sú tam žiadne ložiská, žiadne hriadele z ocele a nič sa nereže ani nevŕta do kovu.
Ruku chráni magnetická spojka s troma zúbkami, ktorá zapadne len v jednej polohe. Keď ruku niekto otočí silou, spojka preskočí.
Keď sa servo vráti do správnej polohy, spojka sama zase zapadne, takže nulovanie nárazom na doraz nie je potrebné.
Stĺp v trupe nepotrebuje oceľové tyčinky, stačí ho vyplniť do voľného miesta. Vzhľad ruky a medzera 3,7 mm ostávajú rovnaké.
Neoverené je, ako rýchlo sa opotrebujú živicové puzdrá a zuby. Treba to vyskúšať na skúšobnom kuse, pred tlačou spraviť
výpočet MKP stĺpa a zmerať skutočné servo.

## 1. Changes vs v2

| v2 part (bought / metal work) | B2 replacement |
|---|---|
| brass bevel pair m0.5 16/24 (Mädler/KHK, pinion hub turned off) | **printed** straight bevel pair m 0.65, z 12/18, α 25°, x +0.25/−0.25, b 2.5 (ratio 1.5 kept) |
| Ø3 h6 steel vertical shaft with a D-flat + MR63 + brass coupler sleeve + M2 grub screw + 0.5 shim + Loctite 638 | **one printed pinion-shaft**: printed 20T internal spline (coupler) + Ø4 shaft + collar + pinion; runs in a **printed U-insert** in the tongue |
| Ø4→Ø3 turned steel arm shaft, M2 tapped end, e-clip, 2× MR74 | **one printed gear-spindle**: gear + Ø6 journals in the plug ring bore Ø6.1 + hex end |
| 6700ZZ in the arm hub | arm hub = **printed journal** Ø12.56 on the plug ring Ø12.5, 8.4 long |
| friction clutch: brass hub flange, 3 steel washers (one with a D-flat), DIN 2093 disc spring, shims, M2 screw | **magnetic single-position detent clutch**: printed disc with 3 V-teeth + DIN 9021 M8 steel washer (bonded) + 3 magnets Ø4×2 in the hub + 1 M2 screw into a glued insert |
| 2× Ø2 h6 dowels (plug) | 2 printed pins Ø2.4 on the plug |
| 2× Ø3 silver-steel rods per side cut to 46 / 31 mm (column) | **none**: the column legs are filled out into the free space (σ ≤ 5.1 L / 7.2 R MPa, hand calc). An optional standard DIN 912 M3×40 (or ×30) bonded from below is the fallback only |
| homing by a gentle stall at 15 % against a hidden stop | **no stall homing**: the clutch engages in one position only, so a slow sync sweep at normal settings re-synchronises. EEPROM torque limit 8 % is the back-up |
| PORON strips | rigid printed floor pad + printed crush ribs (0.2 interference) + snap tab |
| tongue: closed ring r 3.0..4.4 with MR63 | tongue: **C open to +X** r 3.2..4.6 with a **solid back**, holds the replaceable U-insert |
| boss slot \|y−3\| ≤ 5.0, Ø4 shaft hole | pinion slot \|y−3\| ≤ 5.1 (z ≥ −24.55) + shaft slot \|y−3\| ≤ 2.5, x ≥ 36.5, z −30.0..−24.55, both open to +X (also cuts the stop ring at 6 o'clock) |
| T_bok notch \|y−3\| ≤ 2.0, x 39.0..41.2 | notch \|y−3\| ≤ 2.5, x 39.0..41.5 (Ø4 shaft, 0.5) |
| plug | + keeper finger (closes the U-insert), + hold-down post 0.5 above the pinion toe, ring Ø13 → Ø12.5 journal, bore Ø6.1 |

## 2. Final design (left side)

### 2.1 Servo
* Feetech SCS0009 (Waveshare SC09), ears cut off flush (plastic, side cutters + file). Position as v2: output up on the
  vertical axis (39.0, 3.0), case x 32.95..45.05, y −14.3..8.9, top face z −45.0 (21.5 mm case; the floor pad moves down for a
  25.25 mm case – measure first).
* Sits on a **rigid printed floor pad** (no PORON), located sideways by printed crush ribs on the leg faces and the web (0.2 mm
  interference) and the v2 snap tab. Gravity and the bevel separating force push it down. Upward travel is limited to 0.5 by
  the strut (front) and a ledge of the back-leg extension (y 7.5..9.2, z −44.5; back).
* Settings: EEPROM max torque **8 %** (≈ 18 N·mm at the servo), temperature 65 °C, arm range −45..+135° (+130° if
  the arm play in 7.2 must never bring the gap below 1.0). Normal running needs ~1.5 % of the stall torque. Slip of the clutch
  needs ≤ 13.4 N·mm at the arm, which is 9 N·mm at the servo (4 %).

### 2.2 Printed pinion-shaft (one piece, rotates about (39, 3))
* From the bottom up:
  * Coupler r 3.5, z −43.5..−40.0, with a **printed 20T internal spline** for the servo spline (OD 3.95 / root 3.45, toothed
    2.2 mm). The fit comes from a test coupon with radial offsets 0 / +0.02 / +0.04 / +0.06; pick the one that presses on
    firmly by hand. The coupler ceiling sits ≥ 0.5 above the spline tip, so the spline never bottoms.
  * Shaft Ø4.0, z −40.0..−24.05.
  * Collar r 2.7, z −24.05..−23.21. Its underside is the **axial reference**: it rests on the top of the U-insert, pushed
    down by the separating force and its own weight.
  * Pinion 12T.
* The axial position therefore comes from T_spodok (tongue + insert) and the printed length, not from the servo dimensions.
  The tolerance stack of the servo and the floor only changes the spline engagement, nominally 2.0 of 2.2 mm.
* Retention: the friction of the spline fit plus a hold-down post on the plug 0.5 above the pinion toe (it cannot walk off
  the spline). No screw.
* Fallback if the printed spline fails: trim a supplied plastic horn to its hub and bond it into a larger socket. The socket
  must stay r ≤ 4.7 above z −40.9 (sweep), so the horn hub is trimmed to 3.0 mm height.

### 2.3 Printed bevel pair (`gears.py`, `gears_pick.py`, `calc_b2.py`)
* m 0.65, z 12/18 (ratio 1.5: servo 300° gives the arm 200°, 180° needed), α 25°, profile shift x1 = +0.25 / x2 = −0.25.
  * b 2.5 (b/R 0.36), R 7.03, δ 33.69° / 56.31°.
  * Contact ratio 1.39. Tip thickness 0.37 m / 0.59 m. No undercut (z_v 14.4 vs z_min 8.4).
* Apex O = (39, 3, −17) as in v2.
* Pinion: crown r 4.576 at z −22.40, heel root z −23.21, toe tip z −20.48 r 2.95.
* Gear: crown r 6.120 at x 42.49, toe x 41.25, heel root x 43.71, back x 44.21. The back face is chamfered 45° from r 4.5 to
  the root, so it prints without supports. The thrust annulus is r 3.05..4.5.
* Lewis (rack-generated form factor, ≈ 8 % below Shigley = conservative): 8.5 MPa is reached at 20.3 N·mm of gear torque.
  * v2 m0.5 16/24 printed: 12.8 N·mm.
  * The search over 3714 pairs is in `gears_search.log`. Pairs with ratio ≤ 1.55 reach at most 20.8–22.6 N·mm.
* Backlash set to ~0.05 mm. To adjust: paper / PET-foil shims 0.1 mm under the gear back face (−0.078 each), or the U-insert
  printed +0.1 / +0.2 higher (−0.052 per 0.1).
* Lubricant: dry graphite powder (lock lubricant) or PTFE dry spray. Grease only after a 3–7 day test on a scrap print.
* Print with the axis vertical, teeth up, no supports on the flanks:
  * pinion-shaft: coupler down;
  * gear-spindle: hex end down.

### 2.4 Tongue + U-insert (static)
* Tongue in T_spodok, z −26.85..−24.05:
  * solid block x 34.4..39.0, \|y−3\| ≤ 4.6, then a C-ring r 3.2..4.6 about (39, 3) open to +X (\|y−3\| < 3.2 for x > 39);
  * the solid back takes the pinion's −X and ±Y loads in compression.
* U-insert (printed, replaceable): r 2.05..3.2, open to +X, with an anti-rotation flat on its back.
  * The journal is Ø4.1 for the Ø4.0 shaft, 0.1 diametral clearance, set by coupon.
  * It slides in along −X around the shaft. The collar holds it down and the plug keeper finger holds it in +X.

### 2.5 Plug cartridge (zatka_L / zatka_P, black)
* As v2: neck r 11 x 38.6..40.6, body r 13.5 to the face (approved surface − 1.0), gear cavity r 6.8 to the end wall
  x 44.31, and a 6 o'clock slot \|y−3\| ≤ 5.1 for x < 44.0, open to −X.
* Fixed by 3× M2×10 countersunk screws at r 9.0 (12, 4, 8 o'clock) into glued M2 brass inserts in the boss, as T4 F8 / v2.
* Located by 2 printed pins Ø2.4 × 2 at r 9.0 (10 and 2 o'clock).
* Ring: Ø13 from the face to x 52.4, then the arm-hub journal Ø12.5 to the ring end x 61.0. Through-bore Ø6.1 from
  x 44.31 to 61.0.
* Keeper finger: x 41.5..44.0, \|y−3\| ≤ 1.9, z −26.6..−24.6. Gaps: 0.51 to the shaft, 0.56 to the collar.
* Hold-down post: x 38.6..40.0, y 1.5..4.5, z −19.98..−10.5. Gaps: 0.50 above the pinion toe, 1.25 to the gear.

### 2.6 Printed gear-spindle (one piece)
* Gear (2.3) plus a Ø6.0 spindle.
* Journal lands: inner x 44.4..47.8, outer x 57.2..61.0. Relief Ø5.6 between them. Hex AF 5 from x 61.0 to 62.2.
* M2 brass insert glued in the end, same type as in the boss.
* Axial play: total 0.2. Outward, the gear back meets the cavity wall (0.1); the separating force keeps it there under load.
  Inward, the disc meets the ring end (0.1).
* It goes into the ring bore from the cavity side; the disc retains it.

### 2.7 Arm hub + magnetic single-position detent clutch
* The arm hub is part of the printed arm body:
  * bore Ø12.56 on the Ø12.5 ring journal, 8.4 long (x 52.6..61.0), 0.06 clearance by coupon;
  * counterbore Ø14 around the Ø13 ring up to x 52.6, with 0.2 axial gap to the ring step = inward stop;
  * flange r 8..14.2 at x 58.5..61.0.
* Outer hub face (x 61.0) carries:
  * 3 V-grooves at r 12.4..14.0, at 0° / 100° / 220°;
  * 4 magnet pockets Ø4.1 × 2.9 at r 10.4 (50 / 160 / 290 / 340°), normally 3 magnets Ø4×2 N35, **axially magnetised**,
    epoxied, tops 0.9 below the face.
* Disc (printed, on the spindle hex, M2×8 screw + Loctite 222, tightened gently):
  * x 61.1..64.5, r 14.2;
  * a **DIN 9021 M8 steel washer** (8.4×24×2, zinc-plated, magnetic) is bonded flush into its inner face (r 4.2..12);
  * 3 V-teeth (flank 30°, height 0.6, engaged 0.3) at r 12.4..14.0 at the same irregular angles 0/100/220°, so they drop in
    at **one relative angle only**.
* Seated gap magnet → washer: 1.2 mm.
* Slip torque T = n·F·k_sat·r·tan(β+φ) (`calc_b2.py`, `magnets.py`). With 3 magnets: nominal 12.3 N·mm, range 8.1–18.1
  before tuning.
* Tuning on the robot, no tools:
  * Arm horizontal, coins taped to the tip (r 72).
  * A 1 € coin (7.5 g) must hold: 9.3 N·mm including the arm.
  * 1 € + 20 c (13.2 g) must slip: 13.4 N·mm.
  * Adjust with the magnet count (2/3/4) and the disc variant (flanks 25/30/35°). The 9 combinations run from 6.9 to
    19.6 N·mm in ~15–20 % steps.
* Below slip there is **no wind-up** (preloaded teeth). Slip drops the magnet force by 33 % (gap 1.2 → 1.5), so it snaps
  through.
  * Drag while slipping: 1.8 N·mm. A disengaged arm falls back toward hanging when |angle| > ~30°.
* Axial location of the arm: the magnets hold the hub against the disc teeth; the unit floats 0.2 between the stops.
* The hub, disc and screw head fit inside the approved pebble (`armroom_b2.py`). The disc keeps 0.65 from the shell inner
  surface; the hub tube is inside the skin with 1.0 to spare.
* **Sync / homing**:
  * At power-up, sweep slowly (≈ 30°/s) to arm −50°, then up to +60°, then to the target.
  * The free arm is caught when the drive passes its angle. If the drag carries the arm along, it stops at ≲ 30° and the
    drive then reaches it. The arm then sits exactly where the servo thinks.
  * In normal use the arm also re-engages by itself the next time the drive passes it, e.g. at rest.
  * The offset arm ↔ servo is calibrated once after assembly: hex step × gear tooth × spline tooth.

### 2.8 Column (T_spodok) – no rods, no screws (`colroom.py`, `column_b2.py`)
* The v2 legs with x ≥ 34.4 are needlessly thin. The voxel maps show free space down to the sweep cylinder r ≈ 34.65 about
  Z, i.e. x ≈ 31.5 at the band ends.
* B2 fills the bands back y 7.5..16.5 and front y −21..−9 for z −49..−27 up to all of these:
  * ≥ 0.3 to kept static parts (T_bok, T_paluba, T_stred …);
  * ≥ 1.0 to the pan / lift sweep;
  * ≥ 0.5 to the T_stred lowering path;
  * ≥ 0.3 inboard of the side-cap removal sweep;
  * outside the drive keep-out (r 4.5 / 3.0 about (39, 3)) and the servo slide zone.
* Upper back leg extension y 7.5..9.2 above z −44.5 is in all the checks.
* Hand check (judge's method: L5 10 N at the 72 mm tip, arm +135°, Kt 1.3, column alone):
  * σ ≤ 5.1 MPa left, ≤ 7.15 MPa right (at z −48.75, beside the J1 cradle) without any steel.
  * Exact checks of the fill: sweep 1.48 / 1.48, static 0.28 (T_paluba, trim 0.1 at the deck edge) / 0.43,
    T_stred path 0.75 (map) / ≥ 0.8 (exact ray), cap removal ≥ 0.8 (exact).
* Note found on the way: in the **real** v2 geometry (4-mm-deep strut and narrowed back leg, z −44.5..−26) the hand
  stress is 13–18 MPa with or without the v2 rods (`column_b2.py`, rows "v2 real"). The judge's two-leg section hid this.
  The fill fixes it.
* Fallback only if the modelled fill comes out < ~85 % of the free section (right side): one DIN 912 M3×40 bonded with
  epoxy into a printed Ø3.3 blind hole from below (head in a 3.2 counterbore at z −78, thread z −75..−35).
* FE is still required before printing (as in v2).

### 2.9 Assembly (left; right mirrored)
1. Bench work:
   * bond the washer into the disc, the magnets into the hub pockets (polarity irrelevant), the M2 insert into the spindle
     and the 3 M2 inserts into the boss;
   * gear-spindle into the plug ring from the cavity side.
2. Cap off, plug out. Servo in along −X onto the floor pad; cable into the leg slot.
3. Pinion-shaft in:
   * hold it 4.2 mm high and slide it along −X through the tongue opening and the boss slots;
   * press it down onto the spline with a printed pusher on the pinion toe face (the servo rests on the pad).
4. Lift it ~0.5, slide the U-insert in along −X around the shaft, lower it: the collar now sits on the insert.
5. Side cap on along −X (the notch passes the shaft).
6. Plug cartridge in along −X: gear engages, keeper and post in place, pins locate, 3× M2. Check the backlash and shim it.
7. Arm onto the ring.
8. Disc onto the hex: teeth in the grooves, magnets pull it home. Then the M2×8 screw.
9. Arm cover on its magnets.
10. Power on: calibrate the offset once, then run the coin test.

### 2.10 Service
* Servo swap (~10 min):
  1. Arm cover, screw, disc, arm off.
  2. 3× M2 out, plug out, cap off.
  3. Lift the pinion-shaft 0.5 and slide the insert out.
  4. Lift the pinion-shaft 4.2. The servo comes along 0.5 until it hits the strut / ledge, then the spline lets go.
  5. Slide the pinion-shaft out along +X, then the servo out along +X.
* Worn parts are small single prints (≤ 25 mm tall, one plate, ~1 h):
  * the U-insert: ~10 min swap, no cap removal; the arm and plug come off (steps 1–2) but the cap stays;
  * the pinion-shaft: ~15 min swap;
  * the gear-spindle and the clutch disc: ~10 min swap.

## 3. Bought parts per arm (all need no metal work)
Per arm:
* servo SCS0009 / SC09;
* M2×10 countersunk (DIN 965 Phillips or DIN 7991) ×3;
* M2×8 DIN 912 or ISO 7380 ×1;
* M2 brass threaded insert (glue-in) ×4;
* magnet Ø4×2 N35 axial ×3, plus 1 spare;
* steel washer DIN 9021 M8 (8.4×24×2, zinc-plated steel, NOT A2) ×1.

Shared:
* 2K epoxy;
* Loctite 222 (or any low-strength threadlocker; never on screws into resin);
* graphite powder or PTFE dry spray.

Shops: hardware store (Hornbach, OBI, Bauhaus, Merkury: screws, washer, epoxy, graphite). 3D-printing shops (Prusa, 3DJake,
LaskaKit: M2 inserts). Magnet shops (umagnets.sk, Alza, filamentia: Ø4×2). AliExpress only as a backup for magnets and
inserts. Prices / stock come from search snippets in the research files (unverified, shop hosts blocked).

## 4. Verification (scripts → numbers)
* `gears_search.log`, `gears_pick.json`, `calc_b2.json` – gear pair: T at 8.5 MPa = 20.3 N·mm (v2 printed: 12.8).
  * Tooth stress:
    * normal running 2.1 MPa;
    * nominal slip 6.3 MPa;
    * slip at the coin-test upper limit with dry friction (μ 0.25 in the spindle journals) **8.48 MPa**;
    * clutch jammed, servo at the 8 % limit: 11.3 MPa (short-term fault vs UTS/2.5 = 12.8, judgement);
    * clutch jammed and no torque limit: 142 MPa (teeth break → the EEPROM limit is mandatory).
  * Contact stress 12 / 26 MPa.
* `chk_B2_L/R.json` (judge's chk.py, exact sweep), sweep clearance ≥ 1.0, L / R:
  * pinion 1.16 / 1.54;
  * tongue 1.13 / 1.51;
  * boss 1.02 / 1.40;
  * coupler 2.21 / 2.56;
  * collar 2.71 / 3.11;
  * back-leg extension ≥ 1.81 / 2.16;
  * column fill 1.48 / 1.48.
* Static clearance ≥ 0.3:
  * tongue–T_bok 0.38 / 0.38;
  * insert 0.89;
  * keeper 1.72;
  * back-leg extension 0.62;
  * servo–T_bok 1.76 (L), servo–J1 cradle 0.56 (R), as v2;
  * shaft–T_bok 0.0 → notch widened (as v2).
* `paths_B2_*.log`, `paths_B2col_*.log` (exact ray tests):
  * cap removal: tongue 0.40, back-leg extension 0.63, strut / back leg 0.70, fill ≥ 0.8; the shaft needs the notch;
  * servo slide-in 0.30 (cable stub through its slot, as v2);
  * pinion-shaft lateral insertion lifted 4.2: coupler ≥ 0.8, shaft 0.57, pinion 0.66, collar free;
  * vertical lift: shaft 0.55, pinion 0.66. The coupler-lift "0.0" is the servo spline inside the coupler bore, a model artefact;
  * T_stred lowering (exact): all new drive parts and the column fill ≥ 0.8 both sides. The only 0.25 is the v2 front-leg
    inboard stub that the judge already removed.
* `intern.py` / `intern.json`: B2 parts against each other, ≥ 0.5 between own moving parts:
  * pinion–post 0.50, pinion–boss slot 0.66, pinion–tongue 0.84, pinion–plug 0.73;
  * collar–tongue 0.50, collar–keeper 0.56, collar–gear 0.73;
  * shaft–keeper 0.51, shaft–boss slot 0.55;
  * gear–post 1.25, gear–tongue 1.66, gear–keeper 1.48;
  * coupler–back-leg extension 1.0;
  * lifted: coupler–spline 0.95, shaft–boss 0.55, pinion–boss 0.66.
* `chk_B2_*` map test, T_stred lowering: all new drive parts ≥ 7.75; column fill 0.75.
* `armroom_b2.json`: hub, disc and screw inside the pebble (margins 1.0 / 2.0 / 0.15 over the required inset).
* Arm gap: the visible geometry is unchanged (same ring Ø13, same recessed plug face, dx −1.0), so the v2 numbers hold:
  3.70 at rest, 1.00 at +135°, 3.33 at −45° (judge `armgap.py`). Play changes the gap under a push; see 7.
* `colroom.py`, `column_b2.py`: column numbers in 2.8.

## 5. Strength (hand)
* Teeth: see 4. Order kept:
  * arm need 4.0 N·mm;
  * sync sweep ≤ 6.1;
  * clutch slip window 9.3–13.4;
  * gear at 8.5 MPa 20.3;
  * 8 % servo back-up 27.1 at the gear.
* Plug ring under L5 (720 N·mm): root Ø13/6.1 5.3 MPa, journal Ø12.5/6.1 6.0 MPa (Kt 1.5). Hub edge load 86 N →
  4.6 MPa contact (rare).
* Pinion-shaft:
  * torsion 1.4 MPa at the 8 % limit; bending at the insert 2.6 MPa at max slip;
  * printed spline bearing 0.9 MPa (8 %), 11 MPa only at a full-stall fault.
* Clutch tooth bending 0.1 MPa. Magnet bond 0.02 MPa.
* Tongue (solid back) 0.49 MPa bearing at max slip. Spindle land 0.27 MPa.
* Screws into resin:
  * plug M2 into glued inserts, as T4 F8 / v2 (53 N each under L5);
  * spindle M2 insert: 5.7 MPa bond at a hard 0.10 N·m tightening (borderline). Tighten gently: the hex carries the torque,
    the screw only retains.
* Column: 2.8.

## 6. Durability / wear (`calc_b2.json`)
* Duty assumed: 3000 moves/day of 60°, 365 days.
* Spindle inner land (p 0.047 MPa, 3.4 km/yr) and U-insert (p 0.086 MPa, 3.4 km/yr). Archard depth per year:
  * k 1e-5 / 1e-4 / 1e-3 mm³/Nm → U-insert 0.004 / 0.038 / 0.38 mm;
  * spindle land 0.002 / 0.021 / 0.21 mm;
  * collar 0.002 / 0.017 / 0.17 mm;
  * arm hub < 0.01 mm at any k (only the arm weight).
* Tooth flank wear is small by comparison.
* Backlash growth: 0.006 / 0.057 / 0.57 mm per year → 0.06 / 0.56 / 5.6° of arm play per year. The U-insert dominates.
* All wear directions loosen the mesh; none jams:
  * collar wear lowers the pinion;
  * journal wear moves the gear and pinion apart.
* Expected life: years if k ≲ 1e-4 (lubricated), about a year if k ~ 1e-3.
  * Replace the insert, the pinion-shaft and the gear-spindle when the free play at hanging exceeds ~2°.
* Creep: below slip the teeth carry ≤ 8.5 MPa (Lewis); a blocked-and-held arm is the long-term case.
  * The magnets do not creep; the preload comes only from them.
  * No resin spring is preloaded anywhere.
* The clutch teeth wear only while slipping (rare).
* Endurance test before the robot build: a printed pair + insert + spindle in a printed fixture with the real servo,
  10⁴–10⁵ moves at the arm load. Measure the backlash every 10⁴.

## 7. Arm play (`calc_b2.json`)
* Toward the torso (X), with hub clearance 0.05–0.08 over 8.4 mm and axial play 0.1–0.2:
  * at the tip: 0.53–0.89 mm total;
  * at the critical gap point (r 14): 0.18–0.33 total.
* Pushed inward at +135° the gap can drop from 1.00 to 0.83–0.91. Unloaded, the arm's weight biases it to one side (no
  rattle).
* Recommended: hub clearance 0.05 by coupon, axial play 0.1 by shim, and firmware +130° if ≥ 1.0 must hold even while
  pushed (+130°: 1.15 nominal).
* Swing direction at hanging (no gravity preload): 0.7–1.2° (gear backlash 0.05 plus the unknown servo backlash
  0.3–1.0°/1.5), 0.9–1.5 mm at the tip. Gravity takes it up as soon as the arm is raised.

## 8. Noise
* One printed pair at ≤ 0.75 rev/s pinion speed (12 teeth: ≤ 9 Hz mesh frequency), lubricated. The resin damps it.
  The servo's own metal gear train stays the dominant sound.
* No ball bearings. Plain journals are silent when lubricated (dry resin may squeak).
* The clutch is silent unless it slips; then it clicks (rare).

## 9. Risks / unverified
* Wear rate of Tough on Tough (k) unknown: life from months to years. Mitigations: lubrication, cheap replaceable parts, endurance test.
* Slip torque before tuning 8–18 N·mm (magnet on a thin washer: k_sat 0.6–0.9 assumed; μ 0.12–0.25). The coin test and
  the 9 variants bring it into 9.3–13.4. The dry spindle friction (μ 0.25) is already included in the 8.48 MPa.
* Printed 20T spline fit on the metal spline (batch variation): coupon; fallback = trimmed horn.
* Print accuracy of m 0.65 teeth and journals on the user's printer: coupons for the journals (0.03 / 0.05 / 0.07 / 0.09)
  and a test pair.
* Column: hand calc only, fill shape not yet modelled; FE required (also for v2). Right side tighter (7.15 MPa).
* SCS0009 EEPROM torque limit at 8 % and its internal backlash: not published; check on the bench.
* Grease compatibility with Elegoo Tough unknown → graphite / PTFE dry first.
* Elegoo Tough material numbers (32 MPa, E ~2 GPa) are listing values, not a TDS.
* Shop availability from search snippets only.
* Real servo dimensions (case height 21.5 vs 25.25, spline height) set the floor pad and the coupler depth.

## 10. Scripts
* Gears: `gears.py` (rack-generated Lewis Y, pair search), `gears_pick.py` (short list, fine raster).
* Magnets and hand calcs: `magnets.py` (surface-charge model of the magnet forces), `calc_b2.py` (torque chain, clutch,
  settings, wear, play, strength).
* Clearance models and checks:
  * `geo_b2.py` (point models of all B2 parts), `intern_boss.py` (slotted boss);
  * `chk.py` and `paths.py` (judge's tools, patched for the B2 variants, the lifted pinion-shaft and the column fill);
  * `intern.py` (B2 parts against each other).
* Arm and column: `armroom.py` / `armroom_b2.py` (room inside the arm), `colroom.py` (column free-space fill + hand stress),
  `column_b2.py` (column sections with screws, v2-real comparison).
* Copied judge tools, unchanged: `mov.py`, `armgap.py`, `hub.py`, `legs*.py`, `column_calc.py`, `variants.py`, `geo.py`.

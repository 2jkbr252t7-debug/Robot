# NOVA mini – arm drive B1: printed gears, standard screws as shafts, common bearings

Work dir: `/tmp/claude-0/gapwf/fin/R2c/B1_tlacene_kolesa` (26 Nov 2026). Frame B: mm, Z up, front −Y, robot left +X.
Values are for the LEFT side; the right side is the mirror x → −x, and every check below was run for both sides.

## 0. What changes against v2

v2 kinematics are kept: standing SCS0009, one straight bevel pair, black plug cartridge, arm on a 6700 on the plug ring,
arm placement dx −1.0, and the same visible look (recessed black plug and Ø13 ring, gap 3.70 / ≥ 1.00).
**No metal part needs cutting, drilling, turning or tapping.** Every special part is printed in Elegoo Tough. The bought
parts are standard screws, washers, three common bearing sizes, magnets and brass inserts.

| v2 (needs metal work or catalogue parts) | B1 |
|---|---|
| brass bevel pair 16/24 m0.5, pinion hub turned off | **printed** pair 12/18, m 0.667, PA 25°, ha* 0.9, b 2.8; same pitch radii 4/6, same apex O (39, 3, −17) and the same envelope |
| Ø3 h6 steel vertical shaft with a D-flat | **printed** shaft: hex 4 AF (coupler), Ø3 journal (MR63), D Ø2.5 key (pinion) |
| brass coupler sleeve + M2 grub screw | **printed** coupler cup; the supplied plastic horn is trimmed (arm cut off, two flats filed) and epoxied in; the shaft hex press-fits into it by hand |
| Ø4 steel arm shaft, Ø4→Ø3 step, M2 tapped end, e-clip | **DIN 912 M4×20** (8.8, fully threaded) as the arm shaft; the printed gear is epoxied on its inner end; the MR74 inner races are bonded on the thread with Loctite 638 |
| clutch: D-flat washer, brass flange, DIN 2093 disc spring (69 N), M2 screw | **magnetic friction clutch**: 8 pockets for Ø5×2 magnets in a printed drive hub (0.25 mm skin), against a **DIN 125 M10** washer bonded in the arm hub. Typically 4–7 magnets are used. No spring, so nothing creeps |
| slip 0.06 N·m, homing 15 % | slip **0.0136–0.0160 N·m** (coin test), homing torque limit **3 %** (fallback "slip homing" at 10 %) |
| Ø2 h6 dowels (plug) | printed Ø2.4 pegs on the plug neck |
| 2× Ø3 silver-steel rods per side, cut to 46 / 31 mm | **1× DIN 912 M3×40** per side, epoxied into the back leg at (39.0, 12.35), head in a counterbore in the foot |
| 6700 on the ring at x 53.5–57.5, clutch stack on the shaft end | Ø10 seat lengthened to x 59.5; 6700 at x 55.5–59.5 (outer race bonded in the arm hub, inner race slides on the seat); hidden homing stop between the arm hub and a lug on the seat |

## 1. Printed bevel pair (gears.py, gear_chosen.json)

* Pinion 12T / gear 18T, m 0.6667 (heel), PA 25°, ha* 0.9, hf* 1.15, rack tip radius 0.38 m, no profile shift, face width 2.8
  (b/R 0.39; toe module 0.41). R 7.211, δ1 33.69°, δ2 56.31°, ratio 1.5 (servo 300° gives 200° at the arm; −51…+135 needs 279° of servo travel).
* Envelope, frame B:
  * pinion: crown r 4.50 at z −22.67, heel root z −23.43, toe z −20.47 (r 2.75);
  * gear: toe x 41.14, crown x 42.50 r 6.33, root x 43.64, back x 44.24 (relieved to x 44.04 for r > 3.0).
  * v2: pinion r 4.42, gear r 6.28.
* Tooth form generated numerically by rolling the basic rack (involute + trochoid; undercut is captured automatically).
  * Lewis Y from the generated tooth (critical section = max l/t²): pinion 0.398, gear 0.498.
  * The generator reproduces Shigley's 20° table to within −1 … +6 %.
* AGMA 908 fillet factor Kf: pinion 1.40, gear 1.52.
* Transverse contact ratio of the virtual pair 1.29. No interference. Top land 0.41 at the heel and 0.25 at the pinion toe.
* Arm torque that brings the pinion root to 8.5 MPa: **0.0246 N·m (Lewis)**, **0.0176 N·m (Lewis × Kf)**.
  * The v2 pair printed in resin: 0.0142 / 0.0100 N·m.
* Root stress, pinion, Lewis / Lewis × Kf:
  * arm need 0.004 → 1.4 / 1.9 MPa;
  * running 0.008 → 2.8 / 3.9 MPa (≤ 6 MPa cyclic target);
  * clutch window 0.0136–0.016 → 4.7–5.5 / 6.6–7.7 MPa (≤ 8.5).
  * Hertz at the pitch point: 14 MPa (running) / 20 MPa (slip), E 2 GPa assumed.
* Printing:
  * axis vertical, 20 µm layers (a 50 µm stair-step on a 56° flank is about 0.07 mm), supports on the back faces only, never on flanks;
  * thin both members by 0.02 mm per flank for backlash;
  * print a test pair first.
* Lubrication: PTFE grease or dry graphite on the teeth only. Test the grease on a scrap print for 3–7 days first.

## 2. Vertical drive (left)

* Servo SCS0009, earless, unchanged pocket (case x 32.95…45.05, y −14.3…8.9, z −66.5…−45).
* Coupler (printed cup r 4.5, z −43.5…−35.5):
  * The pocket takes the trimmed single-arm horn: arm cut off with side cutters, two flats filed to AF 6.2 (plastic), 2K epoxy.
  * A shoulder above the horn hub, so pressing the coupler pushes on the horn, not through the bond.
  * Hex socket 4 AF on top. The horn screw is driven through the socket before the shaft goes in.
* Vertical shaft (printed, axis-vertical print):
  * hex 4 AF at z −39.6…−36.1 (hand press fit in the coupler, no backlash);
  * Ø3 journal (slip in the MR63 bore and in the Ø4 tongue hole);
  * D Ø2.5 key from z −23.43 to the toe.
* B1 = MR63ZZ, bonded in the tongue (unchanged, z −26.35…−23.85).
* Pinion: slips onto the D-key and sits on a printed 0.42 mm shim on the MR63 inner race (shim r 1.55…1.9). The back face is relieved by 0.2 mm over r 1.95…3.6.
  * The mesh thrust pushes it down; the gear above stops it lifting, so it needs no screw and no glue and can be replaced.
* Backlash is set with the pinion shim (printed 0.30 / 0.42 / 0.50 / 0.60). The gear mounting distance is fixed by its 0.30 shim.
* Service lift 4.5 mm (with the plug out): the shaft slides up through the pinion and MR63, the shaft top reaches z −15.97 (slot roof −15.5),
  and the coupler top (−35.5) clears the lifted hex (−35.1) by 0.4.

## 3. Plug cartridge and arm shaft (left)

* Plug (black, printed on its axis). Same outside as v2: neck r 11 (x 38.6…40.6), body r 13.5, face recessed 1.0, ring Ø13 to x 52.5,
  3× M2 countersunk at r 9.0 into glued M2 brass inserts in the boss.
* Changes inside the plug:
  * 2 printed pegs Ø2.4 instead of dowels;
  * gear cavity r 6.9 (was 6.8);
  * 6 o'clock slots of the plug and of the boss |y−3| ≤ 5.3 (was 5.0);
  * Ø7 bore from the cavity to an outboard shoulder at x 55.10, holding A2 (MR74, x 52.60…55.10), a printed spacer sleeve and A1 (MR74, x 44.54…47.04),
    all slipped in from the cavity side. The outward gear thrust goes A1 outer race → spacer → A2 outer race → shoulder;
    the shaft never sees an inward force (inward arm pushes go through the arm hub into the ring end face);
  * Ø10 seat x 52.5…59.5 with the homing lug (x 52.5…55.0, r 5.0…6.6, 4.5 wide, at 6 o'clock); A2 sits inside the seat at the Ø13→Ø10 step
    (its steel outer race stiffens the step).
* Arm shaft = **DIN 912 M4×20**: head bearing face at x 60.0 (0.5 off the seat end), tip at x 40.0 (1.6 from the boss face).
  * The printed 18T gear is epoxied on the thread, bore Ø4.1, with a 0.30 shim against the A1 inner race.
  * The A1/A2 inner races are bonded on the thread with Loctite 638 + activator.
  * Pick a screw with a major diameter ≥ 3.93 mm by calipers (≤ 0.035 eccentricity in the 4.000 bore).
* Assembly (bench):
  1. Bearings and spacer into the bore.
  2. Gear and shim held in the cavity.
  3. Push the M4 in from outboard (638 on the bearing zones, epoxy in the gear bore) and hold the gear against shim / A1 while it cures.
* Replacing a worn gear: pull the screw, bearings and gear out towards the cavity as one unit, then fit a new M4×20 and gear and reuse
  or replace the MR74s (EUR 1–3 each). The plug stays.

## 4. Arm side: 6700, magnetic clutch, retention, homing (inside the arm)

* 6700ZZ (10×15×4): outer race epoxied in the printed arm hub (bore Ø15, x 55.5…59.5); inner race slides on the Ø10 seat.
  * Fit rule: the gravity load is stationary relative to the inner race, so a slip fit is acceptable there.
  * The arm, with its 6700, slides on and off the plug.
* Arm-hub flange x 59.5/60.0…60.6, with a **DIN 125 M10** washer (10.5×20×2.0) bonded flat on its outboard face (friction partner, x 60.6…62.6).
* Drive hub (printed), captive in the arm hub:
  * pocket fits over the whole M4 head (x 60.0…64.0, diametral press 0.03–0.08 on the knurl);
  * printed hex 3 AF key in the head socket (torque, no backlash);
  * boss r 4.5 passes the washer hole (r 5.25, 0.75 gap);
  * disc r 11.0, x 62.6…65.9; friction face = 0.25 mm skin at x 62.6 (print it face down on the plate);
  * 8 blind pockets for Ø5×2 axially magnetised discs at r 7.7, open towards outboard, alternating polarity.
* A bonded printed lip ring (x 66.2…67.4, inner r 10.4) keeps the drive hub in the arm hub. The magnets stay reachable through the
  lip opening with the arm cover off, so the count can be changed.
* Clutch preload = magnet attraction to the washer.
  * The loop is internal (drive hub ↔ washer), so it puts no axial load on any bearing.
  * No spring, so nothing relaxes; the force grows slightly if the skin wears.
* magnets.py: charge model, calibrated to catalogue pull values.
  * Per magnet through the skin: 0.9–1.3 N (N38), 1.3–1.8 N (N52).
  * Slip torque at μ 0.25 (clean, dry): 0.0022 N·m per N38 magnet, giving 0.013 N·m with 6 magnets.
  * The faces stay **dry and degreased** (μ 0.25–0.4). With grease or graphite, 8 × N38 reach only 0.009.
* **Calibration with coins (no instruments):**
  1. Arm forward-horizontal, servo holding.
  2. Tape coins at 60 mm from the shoulder axis.
  3. 2 € + 50 c (16.3 g → 0.0136 N·m including about 0.004 from the arm itself) must **hold**.
  4. 2 € + 50 c + 10 c (20.4 g → 0.0160 N·m) must **slip**.
  5. Add or remove magnets until both tests pass; switch to N52 discs if 8 × N38 are not enough.
* Arm retention: the magnets (6–9 N) plus the lip, which drags the drive hub off the M4 head only when the press fit lets go.
  * Fresh press-off force 45–120 N; about 13–60 N after relaxation (estimate).
  * Lifting the robot by an arm (about 11 N) holds. A hard yank pops the arm off without damage; push it back on.
* Arm removal (servo service, as in v2): arm cover off, then pull the arm. The drive hub comes off the M4 head with the arm.
* Re-fit: push the arm on and rotate it slightly until the hex key drops into the socket (the clutch lets the drive hub turn inside the arm).
* Homing stop:
  * Lug on the seat at 6 o'clock; rib in the arm hub (x 53.0…55.0, r 5.5…8.5).
  * They meet at arm angle **−51°**, which leaves 0.58 mm at −45° (hub_b1.py).
  * Contact face 1.1 × 2.0 mm at r 6.05.
  * Homing at the clutch-slip level: 1.4 MPa. A push of 3 N at the arm tip: 16 MPa (short-term). A push of 10 N at the tip would dent it.
  * The rib, in the cheaper arm hub, is the sacrificial part. Optional upgrade if homing must survive hard pushes: a Hall sensor
    (A3144 class, common) in the plug ring plus a magnet in the arm hub, with no stop at all.

## 5. Servo settings (SCS0009, ratio 1.5)

* Running torque limit 15 % (about 0.034 N·m at the servo, 0.051 at the arm). It is above the clutch, so the clutch alone limits the tooth load.
* 65 °C limit. Range −45…+135 (servo 270° of 300°). Limit the acceleration so the dynamic torque stays ≤ 0.004 N·m.
* Homing:
  * torque limit **3 %** (0.0068 N·m at the servo, 0.010 N·m at the arm), slow speed, towards −51°;
  * stall detected from position/load, offset stored, at power-up and after any unexpected load peak;
  * order: arm need ≤ 0.004–0.008 < homing 0.010 < clutch 0.0136–0.016 < tooth limit 0.0176 (Lewis × Kf) / 0.0246 (Lewis) at 8.5 MPa.
* Fallback if the servo does not move reliably at 3 %: "slip homing" at 10 %. The arm stops on the stop and the clutch slips a few degrees.
  The teeth still see at most the clutch torque, because the clutch sits downstream of the gear pair.

## 6. Column (T_spodok), column_b1.py

* Same pocket column as v2. Each side's 2 × Ø3 silver-steel rods are replaced by **1 × DIN 912 M3×40**:
  * epoxied in a Ø3.3 blind hole at (39.0, 12.35), z −75…−35;
  * head in a Ø6 × 3 counterbore in the foot (z −78…−75);
  * placed off the centroid on purpose (a transformed section uses the steel's offset).
* The front leg cannot take a screw: the cable slot (x 37…41.5, y −17.6…−14.6, z −66.8…−63.2) is below, and the strut is only 4.0 wide above.
* L5 (10 N along X at the arm tip, arm at +135°, Kt 1.3), transformed section:
  * C-channel 2.6–2.8 MPa;
  * z −48: **8.54 MPa** (allowable 8.5; v2 rods 3.9);
  * z −44…−36: 6.1–6.5 MPa;
  * mean bond shear on the screw 1.3 MPa.
* **Inherited from v2, found here:** above z −33 the back leg is only x 34.4…38.4 and the front is the 4.0 mm strut. With the real
  section the column reaches **22–23 MPa at z −33…−30** under L5. The judge's column_calc used the full leg width there (8.45), and neither
  rods nor screws can reach that zone. The side cap, clamped by the plug, probably carries a large share, but that is unverified.
  FE of the column with the side cap is required before printing. A possible fix: thicken the upper column towards the shaft above the
  coupler (x 34.4…38.4, y −16…15.5 with a shaft cut-out) for about 9 MPa, plus the side-cap share.

## 7. Clearances (both sides; final geometry)

| check | script / log | left | right | rule |
|---|---|---|---|---|
| coupler r 4.5 to the pan/lift sweep | chk.py (chk_B1_*.log) | 1.23 | 1.60 | >= 1.0 |
| pinion 12T to the sweep | chk.py | 1.23 (v2 1.32) | 1.61 | >= 1.0 |
| boss / tongue / B1 to the sweep (unchanged) | chk.py | 1.02 / 1.33 / 2.71 | 1.40 / 1.66 / 3.06 | >= 1.0 |
| gear / M4 shaft / A1 to the sweep | chk.py | 7.71 / 6.61 / 11.1 | 8.06 / 6.96 / 11.5 | >= 1.0 |
| coupler / pinion / gear to kept T4 parts | chk.py | 2.50 / 3.40 / 5.27 | 2.50 / 3.40 / 5.27 | >= 0.3 |
| servo / B1 / tongue to T_bok (unchanged) | chk.py | 1.76 / 1.43 / 0.46 | J1 cradle 0.56 / 1.43 / 0.46 | >= 0.3 |
| vertical shaft to T_bok 0.0 | chk.py | inside the v2 cap notch x 39.0..41.2, abs(y-3) <= 2.0 (shaft r 1.5 -> 0.5 each side) | same | v2 fix |
| cap removal / servo slide-in / T_stred lowering | paths.py (paths_B1_*.log) | identical to v2 K3j: tongue 0.47, strut 0.70, servo 0.30, lowering >= 0.25 (judge sketch of the front leg) | same | kept |
| pinion to boss face / slot walls / plug slot / cavity | own_b1.py | 0.84 / 0.85 / 0.80 / 0.81 | mirror | >= 0.5 own |
| pinion back to MR63 shield/outer race (0.2 relief r 1.95..3.6) | own_b1.py | 0.62 | mirror | >= 0.5 |
| gear to plug cavity r 6.9 / cavity end / plug slot walls | own_b1.py | 0.57 / 0.50 / 0.62 | mirror | >= 0.5 |
| M4 tip to boss face; pinion to M4; gear to vertical shaft | own_b1.py | 1.60; 1.47; 0.89 | mirror | >= 0.5 |
| coupler to servo boss / leg / case | own_b1.py | 0.50 / 1.70 / 1.50 | mirror | >= 0.5 |
| arm-side parts inside the pebble (shell wall left) | hub_b1.py + hub_fix.py | >= 1.36 (arm-hub wall at x 67.6), rib 1.60, lip 1.82, 6700 3.96 | arm parts are mirrored | >= 1.2 |
| arm hub vs plug ring/seat/lug over -45..+135 | hub_b1.py | rib-ring 0.50, rib-seat 0.50, flange-seat 0.50, 6700-lug 0.60, rib-lug 0.58 at -45 (contact at -51 by design) | mirror | >= 0.5 |
| drive hub / M4 head vs seat, arm hub, lip | hub_b1.py + hub_fix.py | 0.50 / 0.50 / 0.50 (lip moved to x 66.4, seat bore D5.0) | mirror | >= 0.5 |
| arm gap (visible parts unchanged) | v2 judge armgap.py (not re-run) | 3.70 rest, 1.00 at +135, 3.33 at -45 | same | >= 1.0 |

## 8. Durability, noise

* **Teeth.** Resin on resin, greased, slow (<= 0.25 rev/s at the pinion, mesh frequency about 3 Hz).
  * Running root stress <= 3.9 MPa (Kf) and Hertz about 14 MPa.
  * At rest the arm hangs at 0 deg, where the gravity torque is about 0, so there is no sustained tooth load and no creep.
  * Archard estimate with k = 1e-5 mm3/N.m (unverified, +-10x): about 0.01 mm flank wear per 10^7 engagements, i.e. about 0.3 deg extra arm backlash; with 10x wear about 1.5 deg.
  * The 12T pinion wears first. It is a separate part: plug out (3 screws), lift it off the D-key, drop a new one on (about 15 min, print about 30 min).
  * The 18T gear comes out with its M4 screw as one unit (new M4x20 + gear; reuse or replace the MR74s).
* **Clutch.** Slip events are rare (pushes, homing). Face pressure 0.05 MPa, sliding about 4 mm per slip, so wear is negligible.
  Skin wear raises the magnet force slightly instead of lowering it. Recheck once a year with the coin test.
* **Bearings.** Every rotating joint is a ball bearing; there is no printed plain bushing that slides in normal running.
  * The vertical shaft does not turn inside the MR63 bore: the pinion's thrust drives the inner race.
  * The 6700 inner race slides only axially on the seat (the gravity load is stationary relative to that race).
* **Press fits.** The drive hub on the M4 head relaxes (resin). The arm pull-off force drops from 45–120 N to roughly 13–60 N, which only
  affects breakaway. If the arm comes off too easily, reprint the drive hub 0.03 mm tighter.
* **Noise.**
  * One resin bevel pair, lubricated, very slow. Polymer teeth are quieter than brass, and the servo's own metal gear train dominates.
  * No clicking parts. Clutch slip is a soft scrape. Backlash is taken up silently at rest, because the gravity torque passes through zero there.
  * The magnet clutch has no detents (the washer is uniform), so it does not snap when it slips.
* Noise was not measured.

## 9. Slovak summary (for the user text)

Pohon ruky B1 nepotrebuje žiadne kovové obrábanie:
* Kužeľové kolieska (12 a 18 zubov) aj hriadeľ pastorka, spojka a náboje sú tlačené z Elegoo Tough.
* Hriadeľ ruky je obyčajná skrutka DIN 912 M4×20.
* Trecia spojka drží silou malých magnetov 5×2 mm proti podložke DIN 125 M10, takže v nej nie je pružina, ktorá by povolila.
* Kúpiť treba len bežné skrutky, podložky, magnety, mosadzné vložky a ložiská MR63, MR74 a 6700.

Vzhľad, poloha serva a medzera 3,7 mm ostávajú ako vo v2. Spojka sa nastaví mincami na 0,0136 až 0,016 N·m. Pri tom majú zuby
napätie do 7,7 MPa (dovolené je 8,5 MPa). Neoverené zostáva: životnosť tlačených zubov, presné sily magnetov a pevnosť hornej časti stĺpa
pri záťaži L5 (výpočet MKP stĺpa je potrebný; týka sa to už aj v2).

# T4 torso – adversarial verification, lens ASSEMBLY / RESIN MANUFACTURING / ELECTRICAL

Verifier run of 2026-11-17 on the STL set `bbc136411578d453` (148 parts, 24 printed) against `T4_zivica.md` (Z1–Z5).
Nothing in the design files was changed. Scripts and raw results: `/tmp/claude-0/gapwf/fin/T4/overenie_montaz/`.

**Verdict: not ready to print.** Two blockers (service trap behind the glued collar ring; the neck / foot / FPC joint cannot be
made in the stated order and has no disconnect), fourteen majors, six minors. K7 "45 steps, 0 collisions" is true for the rigid
parts it sweeps, but it never tests disassembly, flexible parts, or the resin rules.

## 1. How it was tested

| script | what | engine |
|---|---|---|
| `om_lib.py` | independent STL reader, BVH groups, swept triangle-crossing test (depth > 0.02), ray / tool-channel probes | Blender BVH |
| `t01_servis.py` → `.json` | service: stage out past the glued ring; T_stred off with the stage / pinion in place | sweep 0.25–0.5 mm |
| `t02_montaz.py` → `.json`, `.log` | stage + neck together through the bore; neck out; collar disc along the neck; capacitor clip; USB-C plug envelope; connector headroom; STS3215 top; lift module out through the door; tool channels F1 / F2 / F5 | sweep + rays |
| `t03_tlac.py` → `.json`, `.log` | every printed part, 1–3 orientations: size, suction cups (layer-by-layer sealed air regions, voxel 0.4), islands, plate-facing area | numpy / scipy |
| `t04_zavity.py` → `.json` | hole diameter and thinnest wall around every insert, magnet, pin and screw (24 radial rays × 3 stations) | BVH rays |
| `t05_doplnky.py` → `.json` | forced-host insert walls, countersink land under F2 / F1, cable corner, door sill, thread engagement lengths | BVH rays |
| `t06_demontaz.py` → `.json` | keyhole removal of T_stred + ring + stage around the pan pinion; FPC clamp screw through the empty well | sweep + rays |

Re-run: `/opt/venv/bl/bin/python t0X_*.py` (t03: `/opt/venv/cad/bin/python t03_tlac.py`). Each takes 3 s … 12 min.

## 2. Findings

### Blockers

**M01 – After the collar ring is glued nothing below it can be serviced (pan servo, pan pinion, J1 servo, deck, pan FPC).**
* Stage up with `golier_prstenec` in the bore: `P_sachta × golier_prstenec` collide from 1.25 mm of travel, depth 1.40 mm
  (journal r 28.07 vs ring bore r 26.75). `t01` S1.
* T_stred up with the pan pinion on the servo: `T_stred × pastorok_pan` at 34.5 mm of travel, depth 1.5 mm (front lip inner half
  depth 27.30 / relief 27.55, pinion tip y −28.77). Same result when the stage is lifted together with T_stred. `t01` S2 / S3.
* The pinion cannot leave while the stage is in (it sits under the stage top plate r 26.5 and the journal).
* Keyhole escape (T_stred + ring + stage + disc + neck lifted together, shift −Y, lift on): 12 variants, lift 35.0 / 35.2 / 35.4
  × shift 1.6 / 1.8 / 2.0 / 2.4 – every one meets the pinion at 34.4–34.6 mm of lift (depth 0.5–0.7), i.e. before the T_stred
  bosses have left the deck (35.0) and a shift is possible; at 2.4 the back lip also meets the deck lobe. No path. `t06`.
* Spec §11 "Service: pan stage steps 16 → 12 backwards; J1 / pan servo: T_stred off after the stage is out" passes through
  step 14 = the glued ring. Z5 lists "the ability to replace a servo" as not negotiable.
* The glued ring is also the ONLY thing that stops the stage being pulled up (L1, robot lifted by the head): pivot pin and gear
  mesh are axial slide fits.
* Fix (either): (a) stage max radius ≤ 26.5 so that it passes the glued ring: drop the r 28.07 journal drum and its tape, guide
  the stage top by the collar disc in the ring (0.25 running seam, already there) and give the stage its own axial retention
  (M3 shoulder screw + steel washer through the hub disc into a bonded insert in a thicker deck boss, head in a Ø7 × 2.2
  counterbore of the foot); or (b) keep the journal and make the ring removable: 3 radial bayonet lugs in the T_stred bore
  (a T4-owned copy of the ring; the B part stays as the visual reference) plus the same axial retention. Then re-run K7 backwards.

**M02 – Neck + foot + FPC cannot be joined in the stated order, and the head / neck can never be unplugged.**
* `parts_pan.json` assembly: A3 (bench) solders the 7 neck wires to the FPC paddle and bonds the paddle into the foot; C1 drops
  the stage "with the FPC" through the bore WITHOUT the neck; C1b clamps the static FPC end under the stage; C3 lowers the neck.
  The FPC is one piece fixed to the stage (apron groove, drum, clamp), free length from the fin to the paddle 37.3 mm
  (`FPC.free_len_lift`); the well top is 39.8 mm above the fin exit and the end window is closed above z −15. The paddle cannot
  be outside the torso when the stage is inside.
* B/montaz.txt step 9 and service step 6 expect connectors in the torso ("odpoj vodiče hlavy, konektor SERVO"); T4 has a soldered
  and bonded joint at the bottom of a 40 mm deep well. Replacing the tilt MG90S in the neck means cutting the FPC.
* Geometry that does work (`t02` A, A2): stage + neck + foot pass the bore together with 0 crossings; the neck + foot alone
  leave the well with ring and disc in place with 0 crossings.
* Fix: a connector at the foot. 8-pole 0.5 mm FFC/ZIF (about 6 × 4 × 1) on a 10 × 12 × 0.8 PCB in the existing 1.0 pocket of
  L_pata, neck wires soldered to that PCB on the bench; the FPC tail latches in after the neck is down (reach through the end
  window at pan +90, door side). Or declare the order "stage + neck as one sub-assembly" and add that sweep to K7. Either way
  step A3 / C1 / C3 must be rewritten and the FPC needs a drawing with its developed length.

### Majors (must be fixed before printing)

**M03 – Heat-set inserts (17 in T_ram) and thin insert bosses.** Measured (`t04`, `t05`):
| insert | host | hole now | wall now | wall with a bonded hole (OD + 0.1) | rule Z3.4a |
|---|---|---|---|---|---|
| vl_F2_1..6 M2.5 | T_ram | Ø3.2 | 1.40 | 1.20 | ≥ 1.6 |
| vl_F3_1..4 M2.5 | T_ram | Ø3.2 | 1.30 | 1.10 | ≥ 1.6 |
| vl_F5 M2.5 | T_ram | Ø3.2 | 1.80 | 1.60 | ok |
| vl_F8_L1..P3 M2 | T_ram | Ø2.9 | 2.65, **0.80 at #3 next to the key slot** | 2.45 / **0.60** | ≥ 1.6 |
| vlozka_stred_1..4 M2.5 | T_stred | Ø3.6 | 1.40 | 1.40 | ≥ 1.6 |
| vl_F10_1/2 M2 | P_sachta | Ø3.3 | 1.35, screw in the insert 2.3 | – | ≥ 1.6, engagement ≥ 3.0 |
Fix: holes Ø3.6 / Ø3.3 everywhere; bosses r ≥ 3.4 (M2.5) and r ≥ 3.25 (M2); turn the F8 pattern 30° or move the key to azimuth
180°; F10 = M2 × 6 with the pad 1 mm thicker or a through insert.

**M04 – Thread-forming screws in bosses thinner than the rule (Z3.4b: boss ≥ 2.5 d, engagement ≥ 2 d, 1.5 to an edge).**
| joint | pilot wall | engagement | note |
|---|---|---|---|
| F4 pan servo, M2 in T_ram posts | 1.20 | 3.55 | carries the pan stall reaction |
| F11 MG90S tab, M2 in the bracket post | 1.30 | 3.55 | |
| F12 ear → foot, M2 in the 4.0 mm foot | 1.15 | 5.44 | the whole lift load path (L1 / L2) with one Ø1.5 dowel in 0.81 webs |
| F7 controller, M2 × 4 | 1.65 | 2.43 | opened in service → rule 4a |
| F14 buck / amplifier | ≥ 3.5 | 2.43 | |
| skr_fpc clamp screw | 0.83–1.15 (clamp) | 1.80 (deck) | countersunk in a 2.2 mm clamp |
Fix: F4 → M2 × 10 through the post into a captive M2 nut (slot from the side); F7 → bonded M2 inserts in r 3.25 standoffs;
F11, F14 → bosses Ø5.0 and M2 × 8; clamp → pan head, clamp 3.0 thick, bonded insert in the deck; F12 → see M10 (L_pata).

**M05 – Countersunk heads in thin resin (Z3.5).** The six F2 countersinks leave 0.77 mm of floor under the cone
(cone bottom z −83.07, floor top −82.30; `t05`); F1 leaves 1.57 (ok). Also countersunk: crank screw M2.5 in the P_kluka hub
(wall 1.18), FPC clamp, tongue M1.6. Fix: F2 → ISO 7380 button head M2.5 × 6 in a flat counterbore Ø5.2 × 0.7 (1.5 left, head
0.7 proud, 0.8 to the base plane z −86.0); crank and clamp → pan heads.

**M06 – Press fits and holes at nominal size (Z3.6, Z3.11).** Ø6 pin in Ø5.95 (T_paluba), crank pin Ø2 in Ø1.98 (wall 1.20),
stop pin Ø2 in Ø1.98 (wall 1.21), ear dowel Ø1.5 in Ø1.48 (webs 0.81), 6805 seat Ø37.00 +0.05 "with CA", dummy post Ø24.96.
No hole in the model carries the +0.10…0.15 resin compensation and no drill list exists. Fix: all pin holes = d + 0.05…0.10,
bonded with epoxy; model the bearing seat Ø37.15 and the post Ø24.90 with a file-to-fit note; give a drill table
(Ø1.7 pilots, Ø2.05, Ø2.3, Ø2.8, Ø3.3, Ø3.6, Ø6.1 running bore of the gear / hub).

**M07 – Features that must flex.** (a) Capacitor clip: 230° ring r 5.05 around a Ø10 can, mouth chord 9.15: the +X sweep shows
0.42 mm of interference over 4 mm (`t02` C); the −Z path named in `parts_ram.json` is blocked by the shoulder boss (depth 4.7).
(b) Door hook tabs 0.85 × 8 × 4.8, handled at every door opening (Z3.1 forbids < 1.2 on handled features).
Fix: clip → 180° saddle + cable-tie slot; hooks → delete (the ledge and the four magnet bosses already locate the door, 0.1 to the
pad risers) or replace by two bonded Ø1.5 steel pins.

**M08 – Printed servo spline (Z3.9).** P_kluka carries a printed 21T serration Ø4.44 / 4.84 with a 1.18 wall and a countersunk
screw. Fix: crank with a pocket for the cut MG90S horn (as the B neck does), 2 horn screws + the servo screw. The bush
interface of T_klb (blind Ø4 × 6 "spline cut in the arm round") needs the same decision now, before it is frozen.

**M09 – P_sachta prints with four sealed suction cups.** In the K10 orientation (stage top to the plate) the lightening pockets
of the journal drum are closed by the top plate: 226, 71, 70, 68 mm², 6.8 mm deep, never vented (`t03`). Bottom-to-plate has no
cup but then the 1.5 mm top plate is a flat ceiling over the same pockets. Fix: one Ø2.5 vent per pocket through the top plate
(hidden under the collar disc), or leave the pockets open at the top.

**M10 – Eleven parts are still FDM / POM designs; none has a resin print strategy.** Conversion needs, per part:
| part | label | what the resin version needs |
|---|---|---|
| T_ram | petg | bonded inserts and bosses (M03), F4 nuts (M04), clip → saddle (M07); fillets R ≥ 1 at column feet, posts, bridges; print standing, tilted 20° about X (14 islands, 1405 mm² plate-facing, all on the underside / inside), supports off the stop-ring faces x ±39.1 and the boss faces ±38.4 |
| T_paluba | petg | 1.8 plate with a 0.6 membrane under the 180° stop groove and a press bore: take the stop out of the deck (two bonded steel pins against a lug of the gear) so the plate stays 1.8, bore slide + epoxy, print on edge 30–45° (flat = 107 mm² cup and a warped thrust face) |
| T_prichytka_fpc | petg | 2.2 → 3.0 thick, pan head (M04 / M05) |
| T_drziak_repro | petg | ring 1.6 → 2.0, washers under the 3 heads |
| P_drziak_serva | petg | lands 0.85 / 1.05 above the F10 slots and the 0.8 ledge → ≥ 1.5 or steel washers; post Ø5; fillets |
| L_pata | petg | a 4.0 mm resin plate cannot hold an M2 thread (walls 1.15) or an insert (0.4): cut it from 4 mm aluminium / brass with tapped M2, or redesign the ear joint so that resin is only in compression |
| L_jazyk | petg | key prongs 1.5, M1.6 countersunk → pan head; could merge with the connector PCB carrier of M02 |
| L_ucho | pom | webs 0.78–0.85 around the dowel, screw hole and slot end; steel pin in a resin slot needs the Z3.8 pressure check or a liner; plate ≥ 3.0 or 1.5 mm steel sheet |
| T_puzdro_L/P | pom | friction flange on disc springs (Z3.7 steel washers both sides), spline (M08) |
| Z_naboj_test | petg | fine as resin: plate on supports tilted 30°, 0 cups; post fit per M06 |
Spec §4.7 gives an orientation for 4 shells only; "top down", "open side up", "underside up" can be read both ways – read
the wrong way T_bok prints as a 557 mm² cup and T_stred keeps a 344 mm² × 4.8 trough cup (the Ø1.6 vents sit at ±X, the stated
tilt is about X). State every orientation as "which face is toward the build plate"; vents ≥ Ø2.5.

**M11 – Warp of the arch is not tolerated by the pan bearing.** The lower pivot is in the chassis (pin 0.025 radial), the upper
journal bore is in T_stred (0.15 with tape / 0.28 bare). T_stred is located only by the cap spigot (0.21–0.28 radial) 85 mm
below the bore. Typical ± 0.3 lean of an 85 mm open arch exceeds the journal clearance; nothing is adjustable. Fix: F1
clearance holes Ø3.2 and the instruction "tighten F1 only after the stage is in and turns freely", or the M01(a) layout.

**M12 – The USB-C port of the ESP32-S3-Zero cannot be used in the assembled torso.** Mouth at (−24, 19.7, −68) facing −X: free
length 18.7–23.0 mm to T_bok_P; a 12.4 × 6.5 plug envelope also meets the T_stred boss web by 2.7 mm (`t02` D). The door
opening starts at x −28.25. Fix: mirror the carrier layout (module on the +X half, mouth at x ≈ 0 facing −X) so that the plug
lies inside the door opening.

**M13 – Connectors are not defined well enough to wire the torso.** (a) Both FPCs are specified into JST-GH / JST-SH, which are
crimp wire connectors. (b) Headroom above the board is 7.1 mm (deck), below it 5.2 mm (floor); the modelled 2.95 mm blocks match
side-entry parts, which mate along Z. (c) The board bottom z −77 is 4.75 mm below the door sill (z −72.25): the J1 connector is
not in the line of sight. (d) The MAX98357A (I2S × 3, 5 V, GND) and the 470 µF capacitor have no connector or wire path.
(e) The carrier is a custom PCB with "indicative" connector blocks and no schematic. Fix: ZIF for the FPCs, top-entry headers
(mating along Y through the door) for everything else, all on z ≥ −70; add the amplifier header; deliver a pin table.

**M14 – Servo bus power.** Spec §9 daisy-chains controller → STS3215 → STS3032 on one 5264 lead; pack.md §3 puts the STS3215 on
VBAT (6.0–8.4 V) and the STS3032 on the 5 V rail. One chain cannot do both. Fix: two bus headers (VBAT / GND / DATA and
5 V / GND / DATA); check the STS3032 voltage limit on the purchased servo.

**M15 – Pan / lift FPC: fatigue, resistance, obtainability.** Custom 2-layer 3.0 × 0.12 in two dynamic bends of R 3.84–4.0
(32–33 × thickness; outer-copper strain t / 2R ≈ 1.5 %). A 0.12 mm 2-layer build has ≈ 12 µm copper: a 0.45 mm power trace is
≈ 0.48 Ω over 150 mm, i.e. ≈ 1 V round trip at 1 A on the servo rail (the "≈ 1 A each" of pack.md assumes 35 µm). Together
with the J1 FPC, the LED PCB and the carrier this makes four custom electronic parts (Z5). Fix: single-sided FPC with the
copper on the neutral axis and 35 µm copper, or an off-the-shelf 8-pole 0.5 mm FFC (4.5 wide; channel 3.0 → 4.6 high) with
5 V and GND doubled; state the bend-life assumption in the document.

**M16 – No cable routes.** The spec's bundle corner (y 14.2…15.4, z −82…−78) is 1.55 mm wide beside the T_stred bosses that
descend through it (`t05`: x ±29, z −80 / −76); the gap from the cradle end to the right column is 2.7 mm; no saddle, clip or
tie point is modelled. The bundle to the right column alone is 4 power wires + 3 arm wires. Fix: three tie-slot saddles
(cradle rear wall above z −72, where 7.75 mm are free, and one per column), wires in the model as reserved volumes, and a K7
row that lowers T_stred against them.

### Minors

* **m17** F5 (J1 mesh set screw) is reachable only with the right arm, joint and cap off (tool ray stops on T_bok_P at 13.2 mm).
* **m18** T_klb is doubly seated: neck 2.2 = stop ring 0.7 + cap flange 1.5. Shorten the neck by 0.2 so the flange is always
  clamped; supports only on the neck end face.
* **m19** STS3215: 0.49 mm of foam is all that is above the case; the stack has no slack. Measure the bottom cover (rear axle
  boss of the double-shaft version) before printing; add a Ø10 relief in the deck at (−18, 0).
* **m20** Fasteners: 14 screw types in 5 thread sizes (M1.6, M2, M2.5, M3, M8 on the stand) and 2 insert sizes. With M03–M05
  this reduces to M2 × 6 / × 10 and M2.5 × 6 / × 8 plus the servo screws.
* **m21** Lift-servo lead (`kabel_zdvih`, x 15.7…20.2) crosses the F10_1 tool channel; give it a tie point on the bracket.
* **m22** `montaz_trup.txt` / `NAVRH_trup.md` do not exist yet: no print list, post-cure, drill or bonding instructions.

## 3. Claims checked and found correct

* T_stred lowers over the populated tower; stage alone passes the bore; lift module leaves through the door with the ear off
  (0 crossings); with the ear on, only the crank pin meets the ear (as intended).
* Tool channels Ø4.5 for F1 / F2 from below are free (skirt notches work).
* Collar disc passes over the neck from either end; foot passes the disc slot.
* All printed parts fit 218 × 123 × 220 in every orientation tried (21 analysed, the 3 right-hand parts are mirrors; largest
  footprint Z_naboj_test 110 × 90).
* Hidden-fastener rule holds: heads are on the underside or under the arm hub.
* FPC clamp screw: with the neck out, a Ø4 driver reaches it through the collar-disc slot and the open well bottom at pan
  45…50° only (blocked by the disc or the well at 20, 30, 35, 40, 55, 60°; the Ø4.8 tool hole at pan −58.5 is covered by the
  disc). STATUS_pan's "L-key through the door" is not needed – but the neck cannot come out (M02).
* The integrator's "unfinished" list is accurate; nothing in it was found to be understated except the items above.

## 4. Not done

* No slicer run; `t03` uses 0.4 mm voxels and axis / single-tilt orientations.
* FPC and wire shapes were reasoned from lengths and envelopes, not simulated.
* Strength numbers (L1–L8) are another lens; only the resin rule violations that follow from measured walls are listed.
* STS3215 / STS3032 connector positions and the STS3032 voltage limit could not be checked against a datasheet here.

# T4 torso rev. 2 – adversarial verification, lens ASSEMBLY / SERVICE / RESIN PRINTING / ELECTRICAL / SIMPLICITY

Verifier run of 2026-11-17 (21:12–21:45 UTC) on the integrator's rev. 2 STL set (md5 of T_stred / T_spodok / P_sachta / pastorok_pan
identical to `overenie2_mechanika/stl_md5_before.txt`, i.e. the set behind `checks.json` stamp bb776d9f640e8354).
Nothing in the design files was changed. Scripts + raw results: `/tmp/claude-0/gapwf/fin/T4/overenie2_montaz/`.

**Verdict: not ready to print.** One blocker (the in-situ-bonded pan pinion locks T_stred on the tower, so the pan servo, the J1
servo, the deck and the carrier with the ESP32 can never be serviced without destroying parts), six majors, eight minors.
The integrator's K7 "S5 pan servo" row passes only because `t4_assembly.py` S5 *removes* T_stred from the scene instead of
sweeping it; K10 / K13 "print / cup" PASS rest on a broken size computation and on print tables that were never cup-tested.

## 1. How it was tested

| script | what | engine |
|---|---|---|
| `om_lib.py` | copy of the rev. 1 verifier library (STL reader, BVH groups, swept triangle-crossing test depth > 0.02, tool channels) | Blender BVH |
| `t01_tstred_pastorok.py` → `.json`, `t01.log` | service: T_stred + front stack + F1 inserts lifted off the tower with the pan pinion bonded on the STS3032 (state S5 before T_stred goes); with / without pinion; +Y dog-legs | sweep 0.5 mm |
| `t01b_unik.py` → `.json`, `t01b.log` | 12 escape paths: lift 30 / 32 / 33 / 33.5, shift forward −Y 1.5 / 2 / 3, lift the rest | sweep 0.5 mm |
| `t02_usb.py`, `t02b_door.py` → `.json`, `t02c_sill.py` | USB-C plug with real overmold sizes vs the assembled torso (door off); clear door opening per z / y band; sill height | surface samples in a box |
| `t03_tlac2.py` → `.json`, `t03.log`, `t03b.log` | every printed part in the orientation its module states: size vs 211.68 × 118.37 × 220 − 5 mm, suction cups (air open toward the FEP, closed toward the plate), islands; voxel 0.4 | numpy / scipy (engine of `overenie_montaz/t03_tlac.py`) |
| `t04_f4.py`, `t04b_f4.py` → `.json` | F4 (pan-servo screws, slotted ±0.3 for backlash): D1.3 key / D3 driver channels with the stage in (T7) and out (T5b); brute force over 337 aim points on the bore top | BVH rays |
| `t05_elektro.py` → `.json` | FFC loop resistance, contact current, 5 V peak budget (typical, UNVERIFIED part data) | arithmetic |

Re-run: `/opt/venv/bl/bin/python t01_tstred_pastorok.py` (100 s), `t01b_unik.py` (5 min), `t02_usb.py` (30 s), `t02b_door.py`, `t04_f4.py`,
`t04b_f4.py` (each < 10 s); `/opt/venv/cad/bin/python t03_tlac2.py [part …]` (≈ 35 s all); `python3 t05_elektro.py`.

## 2. Findings

### Blocker

**B1 – T_stred cannot come off once the pan pinion is bonded (T5b): pan servo, J1 servo, deck / bridge and carrier are not serviceable.**
* Straight lift of T_stred (+ front stack, F1 inserts, frame magnets) in the S5 state (stage, neck, lift module, door, caps, joints,
  F1 screws out; deck still on – F3a / F3b are not reachable with T_stred on): `T_stred × pastorok_pan` from **34.0 mm** of travel,
  depth **1.9 mm**, at (4.66, −28.51, −44.0) (`t01`). Pinion tip y −28.77 lies in front of the lip inner face (relief y −27.55):
  the pinion sits under the T_stred wall in plan. The same lift without the pinion: 0 crossings.
* No dog-leg exists: +Y shifts 1.0–2.5 after the spigot hit T_spodok 1.98–4.7 mm at 4.6 mm (`t01`); forward −Y shifts 1.5 / 2 / 3 after
  lifts of 30 / 32 / 33 / 33.5 hit T_paluba (0.55–1.03 mm), T_spodok (0.92–2.8 mm) and stop pin 1 (0.38–1.46 mm) – 12 of 12 variants
  blocked (`t01b`). The 0.25 / 0.5 tower clearances leave no lateral play.
* The pinion is bonded with Loctite 638 on the spline **in situ** (17.15-4, t4_assembly T5b) and cannot be pulled off; the spec's
  release method (250 °C) is not possible in place: the tip is 0.6 mm from the resin front stack (inner faces y −29.4) and 0.3 mm above
  the STS3032 top.
* Consequences: S5 (pan servo), J1 STS3215 service, deck / T_most / T_cap service – all need T_stred off. The carrier cannot leave
  through the door (integrator K7 S6, confirmed: clear door opening |x| ≤ 19.13…20.32 at z −67…−58, `t02b`) and its declared
  fall-back "carrier with T_stred off (S5 route)" is blocked too. Z5 "the ability to replace a servo" (not negotiable) is lost.
* K7 does not see it: `t4_assembly.py` S5 has `remove=SERVICE_T_STRED_OFF` (T_stred teleported away), no sweep row.
* **Smallest fix:** make the pan pinion removable from above without heat, through the bore with the stage out – e.g. an 18T m0.8
  pinion with a hub BELOW the teeth (already allowed by 17.2.1, servo lowered by h with the post shims) and an M3 grub screw onto the
  spline, or the pinion bonded to a separable adapter held by the servo's own centre screw; then add a K7 row "T_stred up over the tower
  with the pan servo + pinion in place" (sweep, not remove) and a row "pinion out through the bore". Independently: make the carrier
  pass the door (integrator's rev. 3 proposal): the clear opening measured at y 29…33 is 38.3 wide at z −62.5…−58 and 40.6 at
  z −67…−62.5 (not 41.5), and the sill is T_stred material up to z −70 for y ≥ 32 (`t02b`, `t02c_sill.py`) – board ≤ 38 wide and
  lifted 1.5 before it moves out.

### Majors (must be fixed before printing)

**M1 – USB-C of the ESP32-S3-Zero cannot take a real cable (D4 / rev. 1 M12 not fixed).**
* RAM H1 / integrator "USB-C plug envelope free" uses an envelope x −21…−0.5, y 19.4…26.0, **z −66.5…−58.5 = 8.0 mm tall** – smaller
  than the USB-C plug shell itself (8.34) and any overmold.
* Seated plug, overmold from the mouth (−0.5, 22.7, −62.5) along −X (`t02`): USB-C spec max overmold 12.35 × 6.5 → **1.67 mm** into
  DPS_riadenie (the J_BUS_V header x −8.5…−1, z −58…−53.5, y ≤ 23.5 and J_BUS_5 x −7.5…−0.5, z −71.5…−67); typical 11.0 × 6.0 → 1.0;
  slim 9.5 × 5.0 → 0.25 (J_BUS_V). The plugged 3-pin housings on those headers (mating +Y, not modelled) stand in the same path.
* Insertion: the door clear opening at the plug height is |x| ≤ 19.13 (z −62.5…−58, y 29…33) / 20.32 (z −67…−62.5) (`t02b`), i.e.
  18.6 mm from the mouth. Shell 6.65 + overmold + strain relief of any straight cable (≥ 25 mm) is longer, and the cable would have to
  turn 90° toward the door within 0.5 mm of the overmold end.
* Together with B1 the board can never be reflashed or recovered by cable in the assembled robot (OTA only).
* **Fix:** a bought 90° USB-C FPC extension (slim male end into the module, female socket bonded in the door frame facing +Y), or
  mount the module so its USB-C faces the door; keep z −69…−56 free of headers for x −22…0 if the plug stays along X. Re-check with a
  12.35 × 6.5 × 25 plug + cable bend, not an 8 mm box.

**M2 – P_sachta prints with 8 suction cups in the stated orientation.**
* PAN print table: "top plate (z −2.0 face) on the build plate … pockets between ring, ribs and walls open toward the vat – no closed
  cup". Pockets open toward the vat and closed by the top plate ARE suction cups in bottom-up MSLA.
* `t03`: 8 cups, each 6.4 mm deep, in the same layers (3.6…10.0 mm from the plate): 117.8 / 113.3 / 112.0 / 105.8 mm² at stage
  (±6, ±18) and 33.3 / 32.2 / 30.2 / 28.2 mm² at (±16, ±15), z −3.5…−10 (journal-ring pockets) – ≈ 570 mm² sealed at once, next
  to the journal ring r 26.37 (a fit face). Raised on supports: the same 8 cups. Flipped (hub disc toward the plate on supports, top
  plate toward the FEP): **0 cups**.
* PAN check G never ran a cup / island test (it is a wall scan + a hard-coded `fits_printer=True`).
* **Fix:** 8 × Ø2.5 vents through the top plate (z −3.5…−2) into the pockets (under the glued collar disc), or print flipped
  (supports on the hub-disc underside = epoxy face, sand flat).

**M3 – T_spodok: a 255 mm² suction cup under the pan servo (RAM "no closed cavity" was never tested).**
* `t03`, stated orientation "cap underside toward the plate, tilted 15° about X" (sign not stated – both tried):
  (+15°) cup **258 mm² × 6.4 mm** at (0, −20.1, −77) = the pocket under the STS3032 (floor −82.3); column-foot boxes 25.4 / 24.6 mm²
  × 4.0 at (±38.5, 2.7, −80.4); 28.8 mm² × 5.6 at (−33, 5.3, −77.6); blind stop-pin holes 8 mm² × 8.4.
  (−15°) **266.7 mm² × 1.6** at (−2.3, 17.5, −81.4) (tub floor behind the cradle) and **253 mm² × 4.0** at (0, −20.3, −79.5).
* **Fix:** Ø3 drain through the cap floor at the low point of the pan-servo pocket (≈ (0, −20.8, −82.3), hidden by the base), Ø2.5
  vent into each column-foot box, state the tilt sign; clean the blind Ø3.05 × 8.7 pin holes before bonding.

**M4 – The pan backlash can never be set with the gears in mesh.**
* The 36T gear is bonded to the stage on the bench (t4_assembly B4b) and arrives with the stage at T7. F4 (slotted ±0.3 "set C on
  assembly", backlash target 0.04…0.08) is driven only at T2, before the pinion exists (T5b).
* With the stage in (T7) every D1.3 channel from both F4 heads, vertical or tilted 5…25° toward the axis, is blocked by P_sachta
  (21.6…49.8 mm), F4_1 also by the pinion at 6.75 mm (`t04`). Spec 17.11 T7 "set pan C / backlash and tighten F4 with a ball-end 1.3
  through the bore" is therefore impossible.
* With the stage out after T5b, F4_2 has 277 free straight D1.3 paths; F4_1 only 76, all tilted 24…29° (aim r 12…14, B az 130…160)
  because the bonded pinion covers its head (`t04b`) – usable with a ball-end key, but the gear is not there yet.
* **Fix:** RAM's own sequence: B4b without the gear; T5c bare 36T gear on the taped T_cap, mesh, set backlash (0.05 paper strip),
  tighten F4 (F4_1 with the ball-end at 25…29°), epoxy on the gear top, then T7 lowers the stage onto it. Add the row to K7.

**M5 – Neck ZIF does not take the specified FFC; the carrier ZIF part number does not exist.**
* DPS_krk uses Hirose **FH19C-5S-0.5SH(10)** (parts_pan.json, t4_common R2 notes). FH19C is the 0.2 mm-FPC version (FH19SC = 0.3 mm);
  the FFC everywhere is "0.10 flex / 0.3 stiffened ends" (t4_pan.py `ffc_par` description, stiffener 0.3 at line 739). A 0.3 tail does
  not enter / latch in an FH19C. (Hirose datasheet snippet via search; vendor PDFs not reachable from this session.)
* Carrier J_PAN_A/B **FH12-5S-0.5SH(55)**: the Hirose FH12 0.5 mm tables found list 6 positions and up; the 5-position FH12 is the
  1.0 mm FH12-5S-1SH (search snippets; UNVERIFIED but no listing of a 0.5 mm 5S was found).
* **Fix:** one ZIF for a 0.3 mm, 0.5 mm-pitch, 5-position FFC that is actually stocked, used at all 4 places (or FFC with 0.2 mm
  stiffened ends for FH19C at both ends); confirm on a distributor page before the PCBs are drawn; re-model the heights.

**M6 – The FFC pair cannot be installed in the stated order (tethered stage), and K7 does not test it.**
* 17.11: B4 bonds the FFC pair to the stage; T4 routes it carrier ZIFs → cradle-wall slot → deck slot → static anchor BEFORE T5.
  t4_assembly T4b brings `ffc_A_nosic / ffc_B_nosic` with the carrier, but the stage carrying the same FFCs only at T7 "straight down
  through the glued ring". Physically the stage is tethered to the deck from T4 by the free length 52.6 mm (outer run 22 + U 10.3 +
  inner run 17.5 + …, parts_pan.json `ffc_lengths`): T5 must pass the tethered stage up through the bore of the descending T_stred
  (0.15 radial), and T6 glues the collar ring with the FFC pair running through it (glue on the FFC). None of this is a K7 row (FFC
  is in `FLEX`, the stage is swept as a free part from 60 mm above).
* **Fix:** route the carrier tails only after T6: stage held above the torso, both tails fed down the empty bore → deck slot (r 22.4…23.6,
  visible from above) → cradle-wall slot (exit above the carrier top, reachable from the door) → ZIFs; Kapton static anchor through
  the bore; then lower the stage (= reverse of S3). Write it in 17.11 / t4_assembly and add a K7 row.

### Minors

* **m1 – Pan/neck power through the FFC is at its limit (UNVERIFIED part data).** `t05`: conductor 0.30 × 0.035 → 0.31 Ω each, rail
  (3 in parallel) 0.10 Ω, loop with 4 ZIF contacts 0.27 Ω → 0.38 V drop at the spec's 1.4 A peak, 0.46 V and **0.57 A per contact**
  (rating 0.5 A) with both MG90S stalled + 0.3 A head. 5 V peak sum ≈ 4.2 A (STS3032 1.0, 2 × MG90S 1.4, ESP32 0.35, amp 0.8, LEDs 0.22,
  head 0.4) on one D36V28F5 (3.2 A). No 5 V budget exists in the spec. Fix: write the budget, firmware never drives both MG90S into
  stall together, measure the drop on the bench.
* **m2 – Lift-servo PicoBlade pair "parked loose" (PD11)** on the rotating stage at stage x 17.2…22.7, y 17.2…20.5, z −29…−17 with
  70 mm pigtail + 60 mm lead: nothing keeps it out of the front-stack zone below z −28.5 at pan ≤ −60. Fix: the spec's clip slot or
  a tie point on the bracket post.
* **m3 – FFC slack and folds.** FFC-A / B are 190.3 / 178.2 mm of 203 → 12.7 / 24.8 mm slack with no modelled storage place; the soft
  45° fold CF is opened and re-creased at every stage removal (S3). Fix: a slack loop zone above the carrier top edge (z −53.5…−48.2),
  and make CF a radius bend (R ≥ 1) instead of a crease.
* **m4 – TOWER_CLEAR 0.25 is between two resin prints** (F1 boss column ↔ stop post 1, ±0.15 each, Z3.12). Fix: dry-fit T_stred on
  the bare T_spodok before inserts / pins are bonded and sand post 1 where it rubs (write it in B1).
* **m5 – Simplicity.** 8 screw kinds (ISO 7380 M2×6, M2×10, M2.5×6, M3×6; DIN 7991 M2.5×6, M2×5, arm M2.5×5; thread-forming M2×6)
  against the plan's "M2 / M2.5, one or two lengths"; 3 Ø2 dowel lengths (2×4.5, 2×5, 2×6) → one Ø2×6 would do; 4 washer kinds;
  3 custom metal parts + a drilled bought Al arm (+ possibly lathe work on the 36T gear); 2 custom PCBs; 47 assembly steps with a 24 h
  cure inside the main torso sequence (T5b) – the in-situ bond is also the root of B1.
* **m6 – K10 size check is broken.** `checks.py` K10: `ext = b[3:] - b[:3]` on a bbox stored as [xmin, xmax, ymin, ymax, zmin, zmax]
  → extents like T_stred [70.4, −114.0, 44.0]; negative values pass any limit. Real sizes in the stated orientations (`t03`): all 16 fit
  with 5 mm (largest T_stred 77.4 × 104.5 × 106.7, T_spodok 63.7 × 89.6 × 99.9). P_sachta / P_drziak_serva have no print record (K10
  says so) and no cup test anywhere (M2).
* **m7 – Documents vs data.** T13Lb "1.5 hex key" for ISO 7380 M2 (socket 1.3); stop pins "6.0 deep" (17.9) vs bonded 8.4 / hole 8.7
  (RAM); spec closes the door (T14) before the base FFC is plugged through it (T16; integrator T15); recommended torques F8 0.015 and F4
  0.02 N·m cannot be set with hobby torque tools – give "seat + angle" instead; T_paluba orientation "plate 70°" does not say about
  which axis (about X: 1 cup 23 mm² × 0.8; about Y: none).
* **m8 – Bought parts still open.** No 2 arm connectors on the rev. 2 carrier (rev. 1 had 2 × JST-SH 3p) although "2 arms later" is in
  Z5 and the arm interface is frozen; an aluminium arm for the MG90S micro spline was not found as a product (search finds 23T–25T
  aluminium horns only) – decide the P05 fallback now, before drilling the r 10.00 pin hole.

## 3. Claims checked and found correct

* T_stred lowers / lifts straight over the tower when the pinion is absent: 0 crossings (`t01`), consistent with K7 T5.
* Integrator K7 S6 is real: the door clear opening at the carrier height is |x| ≤ 19.13…20.32 (`t02b`), the board is 49.8 wide.
* F4 can be driven after T5b with the stage out (F4_2 277 straight D1.3 paths, F4_1 76 at 24…29°), not with the stage in (`t04`, `t04b`).
* All 16 printed parts fit the Saturn 4 Ultra volume with 5 mm in their stated orientation (`t03`).
* No cups / only trivial cups: T_bok_L, T_dvere, T_drziak_led, T_drziak_repro, T_svetlovod, T_mriezka, T_cap, Z_naboj_test,
  P_drziak_serva (0); T_klb 3 × 7.2–8.0 mm² × 2.0 (magnet pockets, as OBAL states); T_stred 2 × 21 mm² × 2.0 + 2 × 5.8 mm² (F1 boss
  pockets; OBAL states ≤ 31.5).

## 4. Not done

* FFC contact side (Type A vs the four creases and the two bottom-contact ZIF families) was not traced – needs the FFC strip normals.
* FFC / pigtail / lead shapes were not swept; plugging and ZIF-latch reach were judged from geometry only.
* No slicer run; voxels 0.4 mm (cups < ~0.8 mm and features < 0.4 mm are missed); T_bok_P / T_klb_P not run (mirrors).
* Bought-part data (FH12 / FH19C tables, MG90S spline, STS3032 / STS3215 connectors and currents, FFC conductor size) from search
  snippets only; hirose / lcsc / chipdip PDF hosts are not reachable from this session (DNS blocked).
* Strength (K12) is another lens and was not re-checked.

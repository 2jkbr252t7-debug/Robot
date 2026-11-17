# REV. 2 – task list for the RAM builder (t4_ram.py). Read T4_spec.md §17 first; numbers = t4_common.R2 (rev2 block).
0. Backup t4_ram.py and t4_ram_checks.py to rev2_backup/<name>.ram.bak. Import R2 / envelopes_rev2 from t4_common; deviations
   in a block "additions by ram rev2" at the end of t4_common + parts_ram.json["deviations"]. Export via t4_obal.export_abs.
   Everything printed is tough resin (mat resin_black / resin_white); metal parts mat 'alu' (add 2.70e-3) or steel / brass.
1. DELETE: T_ram (merge into T_spodok), T_prichytka_fpc, skr_fpc, all F2 parts (skr_F2_*, vl_F2_*), F5 (skr_F5, vl_F5), F6
   (skr_F6), cap_pan, the skirt disc, every heat-set insert hole (all inserts are now BONDED: hole = OD + 0.1).
2. T_spodok (merged, one print ≈ 90 × 61 × 96): rev. 1 T_spodok + rev. 1 T_ram geometry, then: spigot continuous except
   4 notches 7.8 wide at the F1 bosses (none within |x| 31.0…35.6); 6805 seat Ø37.15; plinth / foot ring / J1_PASS as
   rev. 1; NO skirt; J1 stop lug 4.0 × 4.0 radial r 17.0…21.0, z −102.0…−98.0 at az 90°, R1.0 roots.
   Cradle: long walls y ±(12.55…15.05), x −32.2…25.8, z −82.3…−48.2; −X end wall x −32.2…−29.7; roots R2.0 (R1.0 at the
   servo corners). J1 support: 4 corner pads 5.0 × 5.0 at the case-bottom corners (top z −83.3); WINDOW through the floor
   over the rest of the STS3215 footprint (x −29.5…15.7, y ±12.35) incl. the J1_PASS; F16 holes Ø2.4 slotted ±0.3 in x at
   the pad centres (positions to be confirmed on the real servo – list as open); bumper post x 16.7…18.3, |y| ≤ 4,
   z −83.3…−70.0 + 1.0 PORON pad part.
   Columns: web x ±(34.4…37.4), y −9…15; ribs y −9…−6.5 and 12.5…15 to x ±42.0; box closure x ±(40.0…42.0), y −9…15,
   z −52.0…−34.0; foot x ±(33.0…37.6) with R2 gussets; boss disc r 11.6 x ±(34.4…38.4) about (y 3, z −17), R2 roots;
   stop ring r 11.6…12.8 x ±(38.4…39.1) + backing flange r 12.8 x ±(37.4…39.1); key slot 3.0 × 1.5 at az 0°; F8 bonded
   M2 insert holes (Ø3.3 × 3.3 + pilot) on r 7.5 at az 60/180/300 (azimuth in the y–z plane about the shoulder axis,
   (dy, dz) = r(cos, sin)); delete the Ø10 spring spigot.
   Pan-servo posts x ±(11.25…17.25), y −24.6…−17.1, top −56.50, DIN 562 M2 slots (4.1 × 1.35, 1.5 under the top, open
   ±X), Ø2.3 holes at x ±14.0 slotted ±0.3 along the C direction, R1 roots. Stop-pin posts Ø7.0: post 1 at (27.09, 12.89)
   from the floor to −50.60 with a rib to the cradle back wall, post 2 at (−21.37, −21.06) as a bracket off the cradle
   front wall z −57.6…−50.6, R2 roots; pin holes Ø3.05 × 6.0; koliky_dorazu Ø3 × 12 steel, top −44.60.
   Bosses r 3.4 with bonded M2.5 insert holes (Ø3.6 × 4.3 + Ø2.8 pilot) from the top, z −52.5…−48.2: F3a at (20.0, ±13.8),
   (−33.5, ±10.0); F3b at (6.0, ±15.95). Carrier standoffs r 3.25 at (±19.0, z −62.5), face y 16.50, bonded M2 inserts
   axis Y. Board standoffs Ø5 × 1.5 (buck right web, amp left web) + Ø4 vent through each web. Capacitor saddle r 5.1
   (180°) on the floor for the cap lying along X at (x 6…19, y 20.2, z −77.0) + tie slot 2.8 × 1.2 at x 12.5. Tie saddles:
   cradle back wall (x −10, z −50), each column web inner face (y 12, z −45). FFC slot in the cradle back wall x 17…24,
   z −51.0…−50.0 (1.0). Base-FFC floor slot x −6…6, y 21.2…22.5 down through the plinth wall to z −91.0 (check ≥ 1.2 skin).
   F1: 4 pads r 3.4 z −82.3…−81.0 at (±29, ±19), Ø3.2 holes, counterbore Ø6.5 × 1.9 from below (ISO 7380 + DIN 125).
   Drain Ø3 × 2. State print orientation (underside up tilted 15°, supports only on the inside / underside, never on the
   seat Ø37.15, spigot outer face or cradle inner faces) and drains.
3. T_paluba (resin): plate z −48.20…−46.20, rev. 1 outline + back lobe (r ≤ 25.1, B az 0…180), trimmed to r ≤ 26.6 for
   B az 16…232 (stop-lug sweep); through slot x −6.1…12.1, y −18.1…18.1 for T_most; static FFC wall r 23.50…25.10,
   z −46.20…−43.00, B az 15…165 (R1 root); FFC slot r 22.4…23.6, B az 26…34; Ø2.8 holes for F3a at (20.0, ±13.8),
   (−33.5, ±10.0); no pivot boss, no stop groove, no clamp. Print orientation + flatness note (warp: screwed flat).
4. T_most (Al 2.0): x −6.0…12.0, y −18.0…18.0, z −48.20…−46.20, corners R2; tapped M3 at (0,0) (model Ø2.5); Ø2.8 at
   (6.0, ±15.95). T_cap (resin): Ø7.70 × 4.40 (z −46.20…−41.80), Ø3.4 hole, edges R0.3. ptfe_podlozka 24 × 10 × 0.30
   (z −46.20…−45.90); ptfe_cap tape (0.13 on T_cap → Ø7.96). Pivot hardware: DIN 9021 M3 washer z −41.80…−41.00,
   ISO 7380 M3 × 6 head z −41.00…−39.35. Shim strips 2 × 4 × 30 × 0.10 at z −48.30…−48.20 on the J1 servo top.
5. Bought / moved parts: servo_pan case z −72.70…−49.70 (tabs −56.50…−54.00, boss to −46.20, spline to −42.70);
   pastorok_pan = plain m0.8 18T involute, face 4.0, bore 5.0, z −45.90…−41.90 at PAN_AX, phased to koleso_pan (agree
   with PAN); servo_J1 as rev. 1 (z −83.3…−48.3); pastorok_J1 m1 18T face 4.0 bore 6.0 at z −90.00…−86.00; Z_koleso_J1
   same plane; Z_naboj_test: sun-gear stub moved to the new plane, stop block az 270 ± 19.0 at r 17.0…21.0, otherwise
   rev. 1 (+integrator changes). menic x −47.7…−38.9, zosilnovac x 38.9…41.9 (rest as rev. 1), kondenzator along X at
   (6…19, y 20.2, z −77.0). DPS_riadenie: PCB 46 × 18 × 1.6 at x −23…23, y 16.50…18.10, z −71.5…−53.5; ESP32-S3-Zero
   block x −0.5…23.0 (y 18.1…22.6) with the USB-C mouth at (−0.5, 20.2, −62.5) facing −X; keep the plug envelope
   x −21.0…−0.5, y 17.0…24.0, z −66.5…−58.5 free; connector blocks per §17.6 table (FH12-5S ×2 top edge, FH12-10S-1SH
   bottom edge, 2 × 3-pin 2.5 mm vertical headers); all parts y ≤ 23.5. Screws F1, F3a, F3b, F4, F7, F8 (into your column),
   F14, F15, F16 per §17.9 with DIN 125 washers; inserts as bonded solids.
6. Checks (t4_ram_checks.py, new / changed): tower inside the white lip outline − 0.5 for T_stred lowering (all new posts,
   bosses, carrier) and inside the tub − 0.3; C 18.00 / 21.600; J1 sweep ±155 vs the dummy (lug 4 × 4 vs block ±19.0);
   stop pins at r 30.0 / B az 25.43 & 224.57, tops −44.60; deck r ≤ 26.6 in B az 16…232; carrier USB plug envelope free
   of every part; every carrier connector reachable by a straight line from the door opening (x ±28.25, z −72.25…−11.75)
   at pan 0; tool channels Ø4.5 for F1 / F3 / F7 / F16 (F4 with a ball-end key at ≤ 10° through the bore); insert walls
   ≥ 1.6; walls ≥ 2.5 (cradle) / 3.0 (column web) / 2.0 elsewhere; roots R ≥ 1 listed; buck / amp air ≥ 1.5; K10 / K13
   print table. Write STATUS_rev2_ram.md and parts_ram.json.

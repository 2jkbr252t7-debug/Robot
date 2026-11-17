
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

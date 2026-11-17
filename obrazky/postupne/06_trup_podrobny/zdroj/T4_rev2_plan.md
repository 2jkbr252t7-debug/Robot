# T4 rev. 2 – lead decisions after the resin reviews (binding for the rework)

> **UPDATE 2026-11-17 12:00 UTC (lead): the user confirmed the printer (Saturn 4 Ultra 16K, 211.68 x 118.37 x 220) and the resin
> (Elegoo Tough). New allowables in T4_zivica.md Z2: 8.5 MPa normal use, 4.3 MPa sustained / unfilleted notch, 12.9 MPa abuse, all
> incl. stress concentration. Section 17 of the spec was written with 12 / 6 MPa: every strength number there must be re-checked and
> the geometry thickened / filleted where it no longer passes. K12 uses the new allowables.**


Inputs: `T4_zivica.md` (resin rules Z0–Z5, load cases L1–L8 – user requirement), `overenie_montaz.md` (M01–M16, m17–m22),
`overenie_pevnost.md` (S01–S15, m16–m19, MATERIAL section), `zjednodusenie.md` (architecture + P01–P20).
The current geometry (rev. 1) passes K1–K11 but is NOT printable in resin and NOT serviceable. Rev. 2 keeps the approved
exterior, visible seams, the finished head / neck parts (B) and the Z5 function list; everything else may change.
Goal in the user's words: strong, does not break, resin, as uncomplicated as possible but fully functional.

## D1. Architecture (accepted: zjednodusenie §3 "slim stage", P01)
* Every permanent part of the pan stage inside r ≤ 26.5 → the stage (without neck and lift module) leaves upward through the
  glued collar ring (inner r 26.748). The ring is never a bearing or a stop.
* Upper bearing: T_stred gets a ring shoulder at z −2 and a journal bore r 26.65 from z −10.5 to −2 (tube wall 3.95). Stage
  journal r 26.37 resin + 0.13 PTFE tape (= shim). Radial play 0.15.
* Axial retention + pivot: deck boss with a bonded M2.5 insert; Ø6 steel / brass sleeve clamped by M2.5×8 ISO 7380 + DIN 9021
  washer; hub bore reamed Ø6.05–6.10 runs on the sleeve; axial play ≤ 0.3 (target 0.1). Screw reached from above through the
  empty well, head in a counterbore of the foot. Pivot / sleeve seat must satisfy S06 (bonded bush, no press fit).
* L1 path and L2 path as in zjednodusenie §3.4 – PROVE them with numbers (K12). At lift 0 the foot must land on the hub disc
  (rest gap 0.1–0.2) so L2 bypasses the lift mechanism; firmware parks the head at lift 0.
* F1 holes Ø3.2 clearance; F1 tightened only after the stage spins freely (M11).

## D2. Cables (accepted: P02, P11)
* Both custom FPCs are dropped. Pan + lift: stock 0.5 mm-pitch FFC (stacked pair, or one wider FFC if the duct allows), into ZIF
  connectors on the carrier (reachable through the door, z ≥ −70) and on a small rigid neck board DPS_krk in a pocket of the
  foot (B neck wires soldered to it on the bench). Lift servo: inline 3-pin connector. Name real ZIF part numbers (e.g. Hirose
  FH12 / Molex 52559 class) and real FFC (pitch, poles, length, contacts same side / opposite side) – check widths from datasheets.
* J1 crossing is the base round; the torso keeps the floor slot and a J1 ZIF / header on the carrier at z ≥ −70.
* Every connector reachable through the door (at a stated pan angle); defined cable routes with tie-slot saddles (M16).

## D3. Drives and mechanisms
* Pan gear pair: BOUGHT metal gears (brass or steel; S01). Prefer a standard, easy-to-buy module (m0.5 / m0.8 / m1 – check that
  the chosen gears are actually sold in hobby shops / AliExpress / Mädler; m1 would match J1). Keep the pan stop at ±90 with
  the hard stop on BONDED STEEL PINS (S05, P09), engagement ≥ 2.5, deck under it a full plate ≥ 1.8. The rolling-loop drum
  must coexist with a full (not sawn) gear if at all possible – do not ask the user to saw a gear unless there is no other way.
  Gears are attached to servos through the SUPPLIED servo horn (screws into the horn) or a bought metal spline adapter – never a
  printed spline (Z3.9). Same rule for the J1 pinion (STS3215 25T: a bought 25T-bore metal gear or a gear on the supplied horn).
* Lift: keep the crank (dead centres at 0 and 20). Crank = bought aluminium servo arm for the MG90S (check spline count / bore of
  the purchased servo) with the Ø2 steel pin riveted / bonded through it, or the supplied horn with the pin in double shear (P05,
  S13). Ear = METAL flat part (2 mm aluminium 5754/6061 or 1.5 mm stainless) – the one custom metal part; deliver a dimensioned
  drawing (PNG + DXF) so the user can cut it by hand or order it (S02, S14). Ear ↔ foot joint must load resin in compression or
  use two screws ≥ 8 mm apart in the bending plane into captive nuts / bonded inserts (S04); foot stays resin if that works,
  otherwise aluminium flat bar (then a second drawing). Lift servo held in a closed pocket gripping both case ends (or both tabs
  with 2 screws), walls ≥ 2.0, R ≥ 1 roots (S02, S12).
* J1: keep the off-axis STS3215 + brass m1 18T/18T + 6805 (zjednodusenie "keep"). Cradle walls 2.5, servo screwed through its own
  holes, J1 centre distance set by 0.1 shims instead of the F5 grub (P06), stop lug 4 × 4 with R 1 roots or a bonded steel pin
  (S07). STS3215 not resting on a thin resin floor: ≥ 1 mm air or ≥ 2 mm pads under the corners only (S10); buck converter
  1.5 air + vent. Firmware: STS3215 torque limit ≤ 30 %, temperature limits; the base slip clutch (0.25–0.4 N·m, metal friction
  faces, steel washers) is a SAFETY PART of the base round – write it into the base interface.
* Skirt disc: delete it from the torso (S11); the base round hides the J1 pinion orbit. Record it in the base interface.

## D4. Structure and fastening (accepted: P03, P04, P07, P08, P10 if simple, P12)
* Merge T_ram into T_spodok (one resin part; keep T_paluba as the J1 service lid). Columns: web ≥ 3.0, ribs into the foot,
  R ≥ 2 at foot and boss, box section at the shoulder boss (S08).
* One fastener family: M2×6, M2×10, M2.5×6, M2.5×8 ISO 7380 (button head) + M2×6 thread-forming only for one-time joints in Ø5
  bosses with ≥ 4 engagement; bonded brass inserts (M2 Ø3.2/3.3 hole, M2.5 Ø3.5/3.6 hole, boss r ≥ 3.25 / 3.4) or captive DIN 562
  square nuts. No heat-set, no countersunk heads in resin, steel washers under every head on resin (S03, S09, M03–M05).
* No interference fits: pins, sleeves, bearings, magnets bonded with epoxy in slide fits; fit holes drilled / reamed after curing
  (drill table) – model holes at FINAL size, walls must allow drilling (M06).
* Door: delete the hook tabs (P07, S15); ledge + 4 magnet pairs locate it; finger notch / suction cup to open. Close the see-through
  of the door top seam (rabbet) and of the side-seam ends (spigot slit) now that space is free.
* Capacitor: saddle + cable tie (M07). Arm bushes and disc springs deferred to the arm round; freeze the T_klb bore / magnets /
  wire groove interface (P08). T_klb neck −0.2 so the flange is always clamped (m18); R 0.5–1 at its steps (m16).
* Carrier: USB-C of the ESP32-S3-Zero reachable with a straight plug through the door (M12); two servo bus headers (VBAT for
  STS3215, 5 V for STS3032 – confirm the STS3032 voltage), amplifier header, capacitor on the 5 V rail, pin table (M13, M14).
* Every loaded inside corner R ≥ 1 (≥ 0.5 where space forbids, listed) – Z3.3. Pockets vented ≥ Ø2.5.

## D5. Robustness margins
* Running clearances moving ↔ static: ≥ 1.0 hard, ≥ 1.3 wherever it costs nothing (Z3.12). Head vs torso (K9): keep the firmware
  tilt limit 27.5° for lift 10–15 in the documents.

## D6. New / changed checks (integrator)
* K12 STRENGTH: a script that recomputes, on the final geometry, every row of the strength table (overenie_pevnost.md; reuse its
  scripts) for L1–L8 with the Z2 allowables and safety factors; PASS only if every loaded feature is within the Z2 allowable of its load class (normal 8.5 /
  sustained 4.3 / abuse 12.9 MPa incl. stress concentration), or is a bought metal part checked against its own material.
* K13 RESIN RULES: no part labelled petg / pom; no heat-set insert; no countersunk head on resin; every insert boss / thread-forming
  boss meets Z3.4; every pin / sleeve / bearing / magnet a slide fit with an epoxy note; listed loaded roots have the fillet;
  no flexing feature; every printed part has a print orientation, support faces, drain / vent result (K10 extended).
* K7: new rows – stage up through the glued ring; neck out with DPS_krk; lift module out through the door; pivot screw tool path;
  FFC into the ZIFs; pan servo service with T_stred off; USB-C plug.
* K1–K11 as before on the new geometry.

## D7. Documents (docs agent, Slovak)
Material section (from overenie_pevnost MATERIAL, verified numbers only), print table per part (orientation, support faces, drain),
drill table, torque table, epoxy joints, the metal ear drawing (+ foot if metal), buy list with real part numbers (gears, FFC,
ZIF, aluminium servo arm, pins, sleeves, inserts, washers, nuts), assembly + SERVICE order (every servo), firmware limits (pan
torque, J1 torque ≤ 30 %, tilt 27.5° at lift 10–15, park at lift 0, crank range 3–177°), and what the base round must provide.

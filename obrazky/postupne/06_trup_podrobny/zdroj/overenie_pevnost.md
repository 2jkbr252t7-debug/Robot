# T4 torso – adversarial verification, lens STRENGTH OF THE RESIN PARTS (T4_zivica Z2–Z4, load cases L1–L8)

Verifier run of 2026-11-17 on the STL set `bbc136411578d453` (148 parts). Nothing in the design files was changed.
Scripts, logs, JSON rows and FE pictures: `/tmp/claude-0/gapwf/fin/T4/overenie_pevnost/` (sub-folder `out/`).
The findings of `overenie_montaz.md` (M01–M16, m17–m22) are taken as known. They are not reported again. Where this run
adds a strength number to one of them, the number is in §6.

**Verdict: not ready to print. Several printed parts break in normal use or during assembly.** The pan gear, the lift
module (ear, bracket, F12) and the specified screw torques fail by factors of 2–20, not by percentages. Every abuse case
L1–L8 fails somewhere. The resin design rules Z3.3 (fillets), Z3.7 (creep) and Z3.10 (heat) are broken at loaded
features. Counts: **4 blockers, 11 majors, 4 minors**, plus numbers for 9 montaz findings.

## 1. Method, allowables, loads

**Material model (Z2).** The design resin is "tough ABS-like": UTS 35 MPa, E 1.8 GPa. Allowable 12 MPa static (σ1 or
bearing), 6 MPa sustained or at an unfilleted notch. For abuse cases (L1–L6, L8) Z4 asks for SF ≥ 2 on the allowable, so
the limit is 6 MPa. Shear limit is 0.6 × the allowable. For epoxy bonds I assumed 8 MPa shear strength on sanded resin or
knurled brass (the low end of the 8–10 MPa in the brief), with a working value of 8/3 = 2.7 MPa. Repeated handling such as
100 door openings uses the 6 MPa notch/fatigue value. Margin = limit / stress. A margin below 1 is a FAIL.

**Loads used.**

| case | value used | source / assumption |
|---|---|---|
| L1 | 15 N up on the head | Z4 |
| L2 | 30 N down on the head, lift 0 / 10 / 20 | Z4 |
| L3 | 0.6 N·m about the pan axis | Z4 |
| L4 | clutch slip 0.25 N·m; a hand forcing the J1 stop 0.6 N·m (assumed, same as L3) | Z4 + assumption |
| L5 | 10 N at 72 mm (0.72 N·m); robot lifted by one arm 15 N | Z4 |
| L6 | sideways topple: 0.69 J (1 kg, centre of gravity drop 0.07 m, ASSUMED); mean force 229–686 N for a 3–1 mm stop | estimate |
| L7 | M2 0.15 N·m, M2.5 0.3 N·m. Preload F = T/(K·d) with K 0.2 into brass and K 0.3 for thread-forming in resin | Z4 + VDI-type K |
| L8 pan | STS3032 stall 4.5 kg·cm @ 6 V = 0.441 N·m. Rated 1.5 kg·cm. ×2 at the gear | reseller listings that copy the Feetech data (rcdrone.top, evelta, aifitlab); no Feetech PDF opened |
| L8 J1 | STS3215 C001: 19.5 kg·cm @ 7.4 V = 1.91 N·m; **2.17 N·m at 8.4 V** (2S full, linear scaling ASSUMED); 12 V versions 30 kg·cm = 2.94 N·m; C044 27.4 kg·cm @ 7.4 V | DFRobot / openelab / robotshop listings |
| L8 lift | MG90S stall 1.8 kg·cm @ 4.8 V, **2.2 kg·cm @ 6 V = 0.216 N·m** (21.6 N at the crank pin r 10) | components101 and other spec pages; no TowerPro PDF |
| head mass | 0.17 kg (head + neck + foot): 1.67 N, sustained | STATUS_pan C (assumed there) |
| magnets | N52 Ø5×2: 6.67 N on steel in contact (supermagnete S-05-02-N52N). One magnet pair at a 0.2 gap: **6 N ASSUMED** | supermagnete listing |

**Geometry is measured on the STL.** `pv_lib.py` takes plane sections (area, centroid and second moments by scan-line
integration) and line chords, from the earlier attempt; its self-test on the Ø6 dowel reproduces A and I to 0.1 %.
`fe2d.py` is new: a plane-stress Q4 finite-element model on a 0.05 mm raster of a real section. Its self-test on a
cantilever gives 276 vs 285 MPa and a deflection of 22.34 vs 22.22 mm. FE stress is reported as the maximum 0.25 × 0.25 mm
patch mean outside the 0.4 mm contact zone; raw element maxima at sharp corners depend on the mesh. Fillets were measured
by a probe along the corner bisector (§5).

**Not done.** No 3D FE. The thin-plate parts (deck, ledge, cradle walls) and the column/cap shell interaction use beam or
plate formulas with stated widths. The foam (PORON) stiffness, the MG90S output-bearing rating and the STS3215 case
temperature are not published or not found; these are marked UNVERIFIED. No physical test was run.

## 2. Load paths

### 2.1 L1 – robot lifted by the head (15 N)
head → neck (B) → epoxy bond to `L_pata` (front neck half only, 0.59 MPa peel, OK) → **F12**: one M2 thread-forming screw
plus a Ø1.5 dowel, with the ear cantilevered 13.4 mm behind the joint (prying tension 100 N) → `L_ucho` slot (FE 14.5 MPa)
→ steel crank pin → `P_kluka` (pin seat 14.9 MPa) → MG90S spline and output bearing (15 N, 6.15 mm outboard of the turret,
no rating) → servo case → `P_drziak_serva` (F11 tab post 10.4 MPa; the ledge cannot pull) → 2 × F10 in slots → bracket
pads on the well back wall (4.1 MPa) → `P_sachta` well → top plate → journal cone → **nothing for 1.24 mm** →
`golier_prstenec` (its glue carries 0.014 MPa) → T_stred collar tube → shell → 4 × F1 (3.8 N each) → T_spodok → plinth →
6805 → base hub (base round; the 3-finger collet is the only retention).

**Is the stage retained axially at all?** Yes, but only through the glued collar ring. It retains the stage after a free
rise of **1.24 mm**: analytic 1.239, measured 1.237 by overenie_geometria g01. The stop pin reaches only **0.70 mm** into
the deck groove: pin bottom z −46.7, deck top z −46.0. **So the ±90° hard stop has disengaged before the ring catches the
stage.** A head that is lifted and turned can go past 90° and tear the pan FPC. In the same raised position the gear mesh
face drops from 3.2 to 2.16 mm, which raises tooth stress by ×1.48. In strength terms the ring contact is harmless
(0.09 N/mm line load). The defect is functional, and it combines with M01: the stage cannot be serviced. The montaz fix
M01(a) was checked here: an M3 shoulder screw with a Ø7 steel washer on the 1.2 mm hub disc gives 0.57 MPa punching shear,
and the M3 insert bond 0.28 MPa. Both pass. Set the axial play to ≤ 0.3 mm so that the stop pin stays engaged.

### 2.2 L2 – 30 N down on the head
* **Lift 0:** the foot hangs 0.5 above the hub disc and the pin has 0.1 of slot play. The 30 N goes through the ear, pin,
  crank, MG90S and bracket until 0.4 mm of deflection closes the gap. Before that happens the ear upper web reaches
  60 MPa and cracks at 17.5 N. If the ear survives, the 0.8 ledge is at about 23 MPa when the foot lands. After landing:
  hub disc → gear → PTFE washer (0.09 MPa) → deck → 0.5 PORON → STS3215 case → 1.2 cap floor (about 8 MPa, estimate) →
  plinth → 6805 (0.24 MPa on the 1.5 shoulder) → base.
* **Mid lift:** the force crosses the crank arm. The servo would need 0.30 N·m but stalls at 0.216, so it is back-driven
  (no rating published) and the head sinks to lift 0. The crank arm reaches 11.2 MPa and the ear 33.6 MPa first.
* **Lift 20:** the crank is at top dead centre, so the servo sees no torque, but the ear, pin and bracket see the full
  30 N with no end stop. The ear reaches 60 MPa, the same as at lift 0.
* **Deck:** the 0.6 mm floor under the stop groove is 33 MPa if the foam does not back it, and the 1.8 plate is 11 MPa.
  The foam and the J1 servo take a real but unquantified share. The J1 servo height tolerance is ±0.3 against a 0.5 foam.

### 2.3 L3 / L8 – pan
A hand on the head, or the servo, loads the printed teeth: **43 MPa Lewis / 67.5 MPa FE** at 0.6 N·m. At STS3032 stall:
**63.5 / 99.3 MPa**. Even the servo's rated torque gives 21 / 33 MPa. The ±90° stop is a 0.7 mm-deep steel pin in a resin
groove: 31.7 MPa bearing at L3 and 46.7 MPa at stall.

### 2.4 L4 / L8 – J1
Everything relies on the base slip clutch. The base round has not designed it yet; the dummy stand uses disc springs on
an M8 whose slip torque was never computed. With slip at 0.25 N·m all J1 parts pass. With the clutch locked, an STS3215
at 2.17 N·m loads the brass m1 18T pinion to 244 MPa (the brass yield is about 250) and the 1.6 cradle walls to
24–49 MPa.

## 3. Results table

Margin = limit/stress. "limit" = allowable, divided by 2 for abuse cases. Stresses are in MPa unless marked. Rows are
grouped by assembly. The script that produced each row is named in brackets.

| # | feature (part) | load case | section (measured) | stress | allowable → limit | margin | verdict |
|---|---|---|---|---|---|---|---|
| 1 | pan gear tooth, P_koleso (resin m0.8, b 3.2 in mesh) [p01, p03] | normal: STS3032 rated 1.5 kg·cm (0.29 N·m at the gear) | real tooth z −44: s 1.53 at root r 13.38, tip r 15.19; **no root fillet** | Lewis 21.2 / FE 33.1 | 12 | 0.36–0.57 | **FAIL** |
| 2 | 〃 | L3 0.6 N·m | 〃, Ft 41.7 N | 43.2 / 67.5 | 12 → 6 | 0.09–0.14 | **FAIL (> UTS)** |
| 3 | 〃 | L8 STS3032 stall (0.88 N·m at the gear) | Ft 61.3 N | 63.5 / 99.3 | 12 → 6 | 0.06–0.09 | **FAIL (> UTS)** |
| 4 | pan pinion 18T, bought "POM or brass" [p01] | L3 / L8 | Y 0.309, b 3.2 | 52.7 / 77.5 | POM ≈ 20, brass ≈ 100 (assumed) | POM 0.38 / brass 1.3–1.9 | POM **FAIL**, brass OK |
| 5 | required resin face width at the 6 MPa limit [p01] | L3 / L8 | – | 48 / 71 mm needed | 3.2 available | – | **resin cannot work** |
| 6 | pan stop: groove end in T_paluba [p01] | L3 / L8 | pin engagement 0.70 × Ø2 | 31.7 / 46.7 | 12 → 6 | 0.19 / 0.13 | **FAIL** |
| 7 | stop pin seat Ø2 × 3.5 in P_koleso [p01] | L3 / L8 | lever 0.65 | 13.4 / 19.7 | 12 → 6 | 0.45 / 0.30 | **FAIL** |
| 8 | stop engagement while the stage is lifted [p08] | L1 | rise 1.24 vs engagement 0.70 | stop lost | engaged | – | **FAIL (function)** |
| 9 | gear ↔ hub epoxy bond [p01] | L3 / L8 | annulus r 3.0–12.6 | 0.19 / 0.28 | 2.7 → 1.33 | 7 / 4.7 | OK |
| 10 | pivot Ø6 running in the gear / hub bore [p08] | L3 / L8 | 6 × 2.8 projected | 2.7 / 4.0 | Z3.8 5 | 1.85 / 1.25 | OK |
| 11 | pivot Ø6 press seat in the deck boss [p08] | L3 / L8 | 6 × 3.5, lever 1.6 | 8.2 / 12.1 | 12 → 6 | 0.73 / 0.50 | **FAIL** |
| 12 | PTFE washer [p08] | L2 | r 6.2–12.0 | 0.09 | 5 | 55 | OK |
| 13 | T_paluba 0.6 floor under the groove (no foam backing) [p07, p08] | L2 | groove floor 0.6 measured (z −47.8…−47.2) | 33 | 12 → 6 | 0.18 | **FAIL** (foam share unknown) |
| 14 | T_paluba 1.8 plate (no foam backing) [p08] | L2 | 1.8 strip, span 25.1 | 11.0 | 12 → 6 | 0.55 | **FAIL** (foam share unknown) |
| 15 | collar-ring glue (the only axial retention) [p08] | L1 | Ø56.5 × 6 | 0.014 | 2.7 → 1.33 | ≫ | OK |
| 16 | L_ucho ear plate, FE [p03] | L2 30 N, lift 0 / 20 (upper web 1.2, closing web 0.8) | x −18.65 section, A 101.7 | **60.0** (raw 86) | 12 → 6 | 0.10 | **FAIL** (cracks at 17.5 N, reaches 12 MPa at 6 N) |
| 17 | 〃 | L2 30 N, mid lift | 〃 | 33.6 | 6 | 0.18 | **FAIL** |
| 18 | 〃 | L1 15 N, lift 0 / 20 | 〃 | 14.5 | 6 | 0.41 | **FAIL** |
| 19 | 〃 | L1 15 N, mid | 〃 | 6.2 | 6 | 0.97 | **FAIL** (marginal) |
| 20 | 〃 | head weight 1.67 N sustained | 〃 | 3.3 | 6 (creep) | 1.8 | OK (< 2) |
| 21 | ear slot / steel pin contact (Z3.8) [p03] | L2 / L8 / running | Ø2 × 2.5 projected | 6.0 / 4.3 / 0.33 | 5 | 0.83 / 1.16 / 15 | **FAIL** at L2 |
| 22 | P_kluka crank arm, FE [p03] | L2 mid (force across the arm) | x −15.75 section, arm 2.5 thick | 11.2 | 6 | 0.54 | **FAIL** |
| 23 | 〃 | L8 MG90S stall 0.216 N·m | 〃 | 8.1 | 6 | 0.74 | **FAIL** |
| 24 | 〃 | L2 lift 0 (pin pulled toward the 1.21 tip ligament) | 〃 | 6.9 | 6 | 0.87 | **FAIL** |
| 25 | 〃 | L1 mid / lift 20 | 〃 | 5.6 / 3.5 | 6 | 1.07 / 1.7 | OK (< 2) |
| 26 | crank pin seat Ø2 × 2.5, pin cantilevered 1.65 to the ear plane [p03] | L1 / L2 / L8 | eccentric bearing | 14.9 / 29.8 / 21.4 | 6 | 0.40 / 0.20 / 0.28 | **FAIL** |
| 27 | P_drziak_serva tab post (F11 host) [p04] | L2 / L8 / L1 | 5.0 × 4.6 (Z 17.6), lever 6.1; tab-screw force 72 / 52 / 30 N | 25.1 / 18.1 / 10.4 | 6 | 0.24 / 0.33 / 0.58 | **FAIL** |
| 28 | P_drziak_serva ledge 0.8 under the servo [p02, p04] | **head weight, sustained, lift > 0** | 0.8 × 6.1 cantilever, reaction 5.7 N at its −X end | 15 (full width) … 65 (5 mm) | 6 (creep) | 0.09–0.40 | **FAIL in normal use** |
| 29 | 〃 | L2 at lift 0 until the foot lands (0.4 mm deflection) | 〃 | 23 | 6 | 0.26 | **FAIL** |
| 30 | F11 M2 thread-forming pilot in the post [p04] | L2 / L1 | Ø2 × 5 | 7.2 / 3.0 | 6 | 0.83 / 2.0 | **FAIL** at L2 |
| 31 | P_sachta bracket pad root (r 3.0, sharp) [p02, p04] | L2 / L8 / L1 | annulus r 1.65–3.0 (I 57.8), lever 2.8 | 8.2 / 5.9 / 4.1 | 6 | 0.73 / 1.0 / 1.46 | **FAIL** at L2 |
| 32 | F10 slots ±1 in x, x-load held by friction only (Z3.7) [p04] | L2 / L8 | 2 × M2, μ 0.3 | needs 130 / 94 N clamp per screw | ≤ 86 N (12 MPa under the head) | 0.66 / 0.91 | **FAIL** |
| 33 | F12 thread in L_pata, prying (screw tension 100 / 201 N) [p04] | L1 / L2 at lift 0 / 20 | M2 × 5.44, thread-shear area 17.1 mm² | 5.9 / 11.8 | 7.2 → 3.6 | 0.61 / 0.31 | **FAIL** |
| 34 | F12 screw head on the ear flange [p04] | L1 / L2 | pan head Ø3.8 | 14 / 28 | 6 | 0.43 / 0.21 | **FAIL** |
| 35 | ear dowel Ø1.5 in the flange [p04] | L1 / L2 | 1.5 × 2.6 | 6.0 / 12.1 | 6 | 1.0 / 0.50 | **FAIL** |
| 36 | L_pata plate at the bond edge y 0 [p02, p04] | L1 | 4.0 × 32 effective (Z 98 at full width, measured) | 4.1 | 6 | 1.46 | OK (< 2) |
| 37 | neck ↔ foot epoxy (front half, assumed 45 × 10 solid) [p04] | L1 | – | 0.59 peel | ~2 (assumed) | 3.4 | OK |
| 38 | MG90S output, side load 6.15 mm outboard of the turret [p04] | L1 / L2 | – | 15 / 30 N; 92 / 184 N·mm | not published | – | UNVERIFIED (risk) |
| 39 | T_klb neck x 38.4–40.6, sharp step (Kt 2.5 assumed) [p06, p08] | L5 0.72 N·m / lifted by one arm | Z 964 mm³ measured | 1.87 / 0.64 | 12 → 6 | 3.2 / 9 | OK |
| 40 | F8: 3 × M2 bonded inserts in the column boss [p08] | L5 / one arm | toe at r 11: max bolt 29.8 / 10.2 N | 0.99 / 0.34 | 2.7 → 1.33 | 1.35 / 3.9 | OK (< 2) |
| 41 | T_klb + F8, sideways topple [p08] | L6 (estimate) | capacity 282 N (neck at 12 MPa) / 356 N (F8 bond) | impact 229–686 N (assumed) | – | 0.4–1.5 | **likely FAIL** |
| 42 | T_ram column above the bridges, column alone [p06, p08] | L5 10 N along X, arm up/down (1.10 N·m at z −55) | U channel Z 47.2 (x-bending), measured | 23.3 | 12 → 6 | 0.26 | **FAIL** (cap shell share not counted) |
| 43 | 〃 | lifted by one arm 15 N | Z 45.1 | 6.1 | 6 | 0.98 | **FAIL** (marginal) |
| 44 | T_ram column foot z −76 (carry-over M/2 = 550 N·mm) [p06, p09] | L5 | A 50.2, Z 21.0, measured | 26 | 6 | 0.23 | **FAIL** |
| 45 | T_ram column torsion, open U (J ≈ 85 mm⁴) [p08] | L5 10 N along Y | – | τ 4.3 | 7.2 → 3.6 | 0.84 | **FAIL** |
| 46 | column stop ring 0.7 × 1.2 under the cap seat flange, clamped by F8 [p06, p09] | L7 3 × 375 N (sustained) | ring r 11.6–12.8 = 92 mm² | 12.2 | 6 (creep) | 0.49 | **FAIL** (OK at 0.048 N·m: 3.9) |
| 47 | J1 brass m1 18T pinion / sun (bought) [p08] | L4 clutch 0.25 N·m / L8 stall 2.17 N·m | b 3.2, Y 0.309 | 28 / **244** | brass ≈ 100 | 3.6 / 0.41 | OK / **FAIL** |
| 48 | T_ram cradle walls 1.6, STS3215 reaction couple 48 N [p07, p08] | L4 / L8 | 1.6 plate strip 10–20 mm, span 34.5 (measured 1.6) | 3–6 / 24–49 | 12 → 6 | ≥ 1 / 0.12–0.25 | OK / **FAIL** |
| 49 | T_spodok J1 stop lug 2.5 × 2.5, root R 0 [p07, p08, p10] | L4 clutch-limited / hand 0.6 N·m | 2.5 × 2.5 measured, lever 1.15 | 5.6 nominal (11.2 with Kt 2) / 13.4 | 6 (notch) / 6 | 0.54 / 0.45 | **FAIL** |
| 50 | T_spodok floor 1.2 under the STS3215 (inside the plinth r 17, with the pinion passage) [p07, p08] | L2, half on r < 17 | 1.2 measured everywhere under the case | ≈ 8.4 (estimate) | 6 | 0.71 | **FAIL** (estimate) |
| 51 | 6805 seat: shoulder r 17–18.5 / seat wall 2.5 [p07, p08] | L2 + weight | wall 2.5 measured at 5 azimuths | 0.24 | 12 | ≫ | OK |
| 52 | T_spodok skirt disc 1.0 × 4.5 (lowest visible edge, handled) [p08] | handling knock 20 N (assumed) | 1.0 × 10 effective | 54 | 12 → 6 | 0.11 | **FAIL** |
| 53 | F1 (T_stred ← T_spodok) [p08] | L1 | 4 screws | 3.8 N each | – | ≫ | OK |
| 54 | T_dvere hook tab 0.85 × 8 [p10, p08] | L7 opening by levering the bottom (100×) | 0.85 × 8, lever 1.25, hook load 5.7 N | 7.4 | 6 (repeated) | 0.81 | **FAIL** |
| 55 | 〃 | door pulled at its top edge | 11 N per hook | 14.3 | 6 | 0.42 | **FAIL** |
| 56 | door / frame magnet bonds [p08] | L7 pull-off | Ø5 × 2 pocket | 0.13 | 2.7 | 20 | OK |
| 57 | F1 / F2 / F3: M2.5 into bonded insert Ø3.5 × 4 [p08] | **L7 0.3 N·m** (preload 600 N) | bond 44 mm² | 13.6 | epoxy 8 (ultimate) | 0.59 | **FAIL** (max 0.088 N·m for SF 2) |
| 58 | F8 / F10: M2 into bonded insert Ø3.2 × 3 [p08] | **L7 0.15 N·m** (375 N) | bond 30 mm² | 12.4 | 8 | 0.64 | **FAIL** (max 0.048 N·m) |
| 59 | M2 thread-forming F4 / F11 (3.55), F7 (2.43), FPC clamp (1.80), F12 (5.44) [p08] | **L7 0.15 N·m** (250 N, K 0.3) | strip-out 234 / 160 / 119 / 359 N | 250 N applied | – | 0.94 / 0.64 / 0.48 / 1.4 | **FAIL** (strips at assembly; max 0.036–0.108 N·m) |
| 60 | screw heads on resin without washers [p08] | L7 | M2 Ø3.8 / M2.5 Ø4.5–4.7 | 35–62 | 12 | 0.2–0.34 | **FAIL** (crush / creep) |
| 61 | P_kluka hub 1.18 around the M2.5 countersunk head (M05) [p08] | L7 0.3 N·m | 1.18 × 1.5 ring, hoop force 95 N | 54 | 12 | 0.22 | **FAIL – splits at assembly** |
| 62 | thread-forming boss hoop factor (Z3.4b) [p08] | assembly | walls 1.15 (F12), 1.20 (F4), 1.30 (F11, LED/speaker), 0.83 (FPC clamp), 1.65 (F7) | 1.69 / 1.59 / 1.42 / 2.63 / 1.00 × rule boss | 1.0 | – | **FAIL** except F7 |

## 4. Findings

### Blockers (break in normal use or in assembly)

**S01 – The printed pan gear cannot carry the torque of its own servo (Z3.9, L8, L3; also normal use).**
Measured tooth of P_koleso at z −44: root thickness s 1.53 at r 13.38, tip r 15.19, **no root fillet** (the profile
meets the root circle 13.4 with a corner). Face width in mesh 3.2. Lewis (Y 0.377) gives 21 / 43 / 64 MPa at the rated
torque, L3 and STS3032 stall. The plane-stress FE of the real tooth gives 33 / 67.5 / 99 MPa. The UTS is 35 MPa. So the
teeth break at the first stall or hand twist, and they creep at the rated torque. Resin teeth would need a 48–71 mm face
to reach the 6 MPa limit, so this is not a geometry tweak. The bought pinion "POM or brass" is also wrong as POM: 53 MPa
at L3.
*Fix:* buy a metal pair, brass or steel, m0.8 36T + 18T. Lewis 43 MPa at L3 and 64 MPa at stall are fine for brass.
Bond the 36T gear to the printed hub with epoxy plus the 2 existing Ø2 dowels: bond 0.19–0.28 MPa, margin ≥ 4.7. Cut the
full gear to the 200° sector with a saw if the FPC drum must stay. Specify the pinion as brass. Set the STS3032 torque
limit in firmware (it protects only against the servo, not a hand). A printed resin gear is not acceptable at m0.8 in
this space.

**S02 – The lift module carries the head on a 0.8 mm resin ledge and a cracked-in-advance ear: it fails under the head
weight (sustained) and at a finger press (L2, Z3.1, Z3.3).**
* *Bracket.* The ear force acts at x −18.65, 12.3 mm outboard of the MG90S case end (x −6.5). The case is held only by the
  0.8 ledge, which can only push up, and by one tab screw at x −1.25. Measured ledge 0.8, measured post 5.0 × 4.6.
  Statics: tab-screw force 72 / 52 / 30 N and ledge reaction 102 N at L2 / L8 / L1, all concentrated at the ledge's −X
  end. Post root 25 / 18 / 10 MPa against a limit of 6.
* *Sustained.* With the head held at lift > 0, the head weight alone gives 15–65 MPa in the 0.8 ledge against a creep
  allowable of 6. All roots are sharp (R 0 measured, §5).
* *Ear.* FE of the real `L_ucho` section shows L2 60 MPa at the 0.8 closing web and slot end at lift 0 / 20. It reaches
  12 MPa at 6 N and cracks at 17.5 N. Mid lift 33.6 MPa. L1 14.5 MPa.
* *Lift 0.* The foot lands on the hub disc only after 0.4 mm. At that deflection the ledge is at 23 MPa.

*Fix (smallest robust set):*
* Hold the MG90S in a closed pocket that grips the case at both x ends, top and bottom. At L2 the contact forces become
  46 N and 16 N instead of 102 N and 72 N, because the supports are 22.5 mm apart instead of 5.1. Use ≥ 2.0 walls with
  R ≥ 1 roots. Alternatively keep both MG90S tabs with 2 screws in tension (27.7 mm apart, 18.8 N each at L2; p09).
* Cut `L_ucho` from 2.0 mm aluminium (5754 / 6061) or 1.5 mm stainless. The geometry-only FE stress of 60 MPa at L2 then
  has SF ≥ 3. The steel pin then runs in metal, which settles Z3.8.
* Set the foot gap at rest to 0.1 so that L2 at lift 0 goes straight into the hub disc, and park the head at lift 0 when
  idle.
* Pin the crank pin in double shear, or use an aluminium 9 g servo arm as the crank (check the spline count of the bought
  MG90S). See S04 for F12.

**S03 – Specified screw torques (L7) destroy the resin joints during assembly.**
* M2.5 at 0.3 N·m gives about 600 N preload against a bonded-insert capacity of 352 N (8 MPa on Ø3.5 × 4).
* M2 at 0.15 N·m gives 375 N against 241 N (Ø3.2 × 3).
* Thread-forming M2 at K 0.3 gives 250 N against a strip-out of 234 N (3.55 engaged), 160 N (F7), 119 N (FPC clamp) and
  359 N (F12).
* Heads bear on resin at 35–62 MPa with no washers.
* The crank's countersunk M2.5 wedges its 1.18 hub wall to 54 MPa hoop.

*Fix:* put a torque table in the documents:
* M2 into bonded inserts: ≤ 0.05 N·m.
* M2.5 into bonded inserts: ≤ 0.09 N·m.
* M2 thread-forming: ≤ 0.04 N·m, or "seat the head + 1/8 turn", for engagement < 3. Up to 0.07 for 3.5 engaged, 0.10
  for 5.4.
* Steel washers (DIN 125 / 433) under every head that bears on resin.
* No countersunk heads in resin (montaz M05).
* A drop of low-strength threadlocker only on metal–metal threads of screws opened in service. Keep it off the resin; it
  can craze it.

**S04 – Ear → foot joint F12 is a single screw in prying (L1, L2).**
The ear acts 13.4 mm behind a 4.0 mm-high joint, so the lever to the bearing edge is 2.0. Screw tension is 100 N at L1
and 201 N at L2 (lift 0 / 20). Thread shear in the resin foot is 5.9 / 11.8 MPa (limit 3.6). The head on the 0.85-web ear
flange is 14 / 28 MPa. The Ø1.5 dowel is 6 / 12 MPa. This joint fails at the first lift-by-the-head (L1), which is an
everyday handling case.
*Fix:* if the ear is metal (S02), make the foot from 4 mm aluminium flat bar with a tapped M2 (montaz M10). A metal-to-metal
joint at 201 N stresses an M2 8.8 screw to about 97 MPa, which is fine. If the foot stays resin, the joint needs two
screws spaced ≥ 8 mm in the bending plane, which the 4 mm foot cannot give.

### Majors (break under abuse cases, margin < 2, or a broken resin rule on a loaded feature)

**S05 – Pan hard stop: 0.7 mm of steel pin in a resin groove, and it disengages when the head is lifted (L3, L8, L1).**
* The groove end bears 31.7 MPa at L3 and 46.7 at stall. The pin seat in the gear is at 13.4 / 19.7 MPa.
* The deck floor under the groove is 0.6 mm (measured), which is 33 MPa at L2 without backing.
* Under L1 the stage rises 1.24 mm, more than the 0.70 mm engagement.

*Fix:*
* Two Ø3 steel dowels bonded vertically, embedded ≥ 6 mm in deck bosses of Ø ≥ 7, as stops at r ≥ 18. Force ≤ 33 N at
  0.6 N·m, bearing ≤ 5 MPa. Strike them with a lug of the brass gear or a Ø3 steel pin.
* Engagement ≥ 2.5 mm.
* Axial play of the stage ≤ 0.3 mm (M01(a) shoulder screw).
* Deck back to a full 1.8–2.5 plate with no groove.

**S06 – Pan pivot press seat (L3, L8).**
The radial mesh force is 46 N at L3 and 68 N at stall, and 1.04 × of it reaches the pivot. It loads the Ø6 pin in a 3.5
resin seat to 8.2 / 12.1 MPa (limit 6). The running side in the gear bore (2.7 / 4.0 MPa) is OK.
*Fix:* bond the pin (no press fit, M06) into a flanged brass bush of about Ø6 / Ø9 × 6 with a Ø12 flange, bonded in the
deck. Or take most of the moment out with the shoulder-screw retention of M01(a), which also clamps the pin top.

**S07 – J1 strength rests entirely on a clutch that does not exist yet (L8, L4).**
* Clutch slipping at 0.25 N·m: everything passes (pinion 28 MPa, cradle walls 3–6).
* Clutch locked against an STS3215 at 2.17 N·m (8.4 V; 2.94 N·m on a 12 V version): brass pinion 244 MPa, at yield, and
  1.6 cradle walls 24–49 MPa.
* The J1 stop lug, 2.5 × 2.5 with a sharp root, is at 11.2 MPa with Kt 2 even when the clutch limits the torque (notch
  limit 6). A hand forcing the stop gives 13.4 nominal.

*Fix:*
* Make the base clutch a specified safety part: slip 0.25–0.4 N·m after creep, steel or brass friction faces, steel
  washers both sides (Z3.7), and a test step in the assembly instructions.
* Set the STS3215 torque limit (firmware) to ≤ 30 %.
* Stop lug 4 × 4 with R 1 roots, or a bonded steel pin as the lug.
* Cradle walls 2.5 with the servo screwed by its own mounting holes. Clamping between thin walls is not a torque path.

**S08 – Shoulder column under arm loads (L5, L6).**
With the column carrying the load alone, the U-channel is at 23 MPa above the bridges and 26 MPa at its foot (z −76, Z 21
measured). That is for a 10 N axial push at the arm tip with the arm up or down. A 15 N lift by one arm gives 6.1 MPa
(limit 6). A 10 N fore-aft force gives 4.3 MPa torsion of the open U (limit 3.6). The side cap is clamped at the shoulder
and sits on the spigot, so it carries an unknown share. That share is a load path nobody designed: a 0.21–0.28 fit plus
the flange clamp on the 0.7 stop ring. For a sideways topple (L6, estimate) the shoulder survives 282 N (neck) / 356 N
(F8 bond) against an estimated mean impact of 229–686 N.
*Fix:*
* Column web 2.0 → 3.0, ribs carried down into the foot, R ≥ 2 at the foot and the boss.
* Close the U into a box section (2.0 walls): torsion constant J 85 → 2200 mm⁴, ×26 (p09).
* Make the arm hub a deliberate break-away (the pull-off magnets already exist) that releases before 150 N.
* Get the cap shell's share from a 3D FE or a bench test. A 15 N hang by one arm is easy to test.

**S09 – Creep of clamped resin stacks and springs (Z3.7).**
* The F8 preload of 3 × 375 N at the specified torque presses the cap flange on the 0.7 × 1.2 column stop ring at
  12.2 MPa sustained. It drops to 3.9 MPa at 0.048 N·m.
* The two DIN 2093 disc springs stand with their edges directly on a resin spigot and bush flange. A 0.25 N·m collar at
  μ 0.2 and r_m 3.8 needs 164 N (2 friction faces) to 329 N (1 face) of spring load (p09; spring rating not verified).
  That is 10–20 N/mm of line load on the resin edge. The edge indents and the 0.25 N·m friction-collar torque drifts.
* The F5 grub screw holds the J1 centre distance by a sustained push into a bonded insert.
* The F10 slots hold x by friction (row 32).

*Fix:* steel washers on both faces of every spring and every resin clamp. Set the J1 centre distance with a shim, not a
pushing screw. Replace the F10 slots by a dowel plus a hole and shim in y.

**S10 – Heat (Z3.10) on loaded thin resin.**
* The STS3215 case bottom sits directly on the 1.2 floor of T_spodok (the pocket, measured 1.2 everywhere under the
  case), which also carries L2 at about 8 MPa.
* The MG90S stands on the 0.8 ledge.
* The buck converter's back face is exactly 1.0 from the right column web (x −37.4 vs −36.4).

Servo cases near stall run well above the 55–60 °C HDT. The STS3215 over-temperature cut-out was not verified (Feetech
servos have a temperature limit register, typically set around 70 °C – UNVERIFIED).
*Fix:* a ≥ 1 mm air gap or ribs under the STS3215 (pads of ≥ 2 mm under the case corners only, floor ≥ 2.0). No servo
standing on a < 2 mm resin feature. Buck converter gap 1.5 with a vent path. Set firmware temperature limits.

**S11 – Skirt disc 1.0 mm is the lowest visible edge and is handled (Z3.1).**
A 20 N edge knock (assumed) gives 54 MPa. It is a K4-declared thin feature, but it is handled: the torso is set down on
it, and a tipping torso lands on it.
*Fix:* 2.0 thick with an R 1 root, or move it into the base.

**S12 – Bracket pads and F10 (L2).** The pad root (r 3.0 boss, sharp, on a 1.6 wall) is at 8.2 MPa and the F10 insert
bearing at 5.5 MPa. The x-load relies on friction (needs 130 N clamp; the head on resin allows 86 N). *Fix:* as S02 plus
pads r 4.0 with R 1 roots, a dowel instead of slots, washers.

**S13 – Crank (L2 / L8).** Arm 11.2 MPa at L2 mid and 8.1 MPa at stall (FE, real section). Pin seat 15 / 30 / 21 MPa
because the pin is cantilevered 1.65 mm to the ear plane. *Fix:* an aluminium servo arm as the crank with the pin
riveted or bonded through it, or pin in double shear. The resin crank needs a hub ≥ 2.0 and no printed spline (M08).

**S14 – Ear slot wear (Z3.8, L2).** Projected pressure 6.0 MPa at L2 and 4.3 MPa at MG90S stall in a 2.5 resin plate. A
running steel pin wears it. *Fix:* a metal ear (S02) or a bonded steel or bronze liner.

**S15 – Door hooks (numbers for M07(b)).** 7.4 MPa per opening by levering the bottom (100×, limit 6) and 14.3 MPa when
pulled at the top. Four 6 N magnet pairs hold the door with about 24 N, so a suction cup is needed. *Fix:* as M07: delete
the hooks; the ledge and magnets locate the door.

### Minors
* **m16** – The T_klb neck/body step and body/end step are sharp (R 0 measured). Stress is low (1.9 MPa with Kt 2.5) but
  this is the L6 impact path; add R 0.5–1.0.
* **m17** – T_stred magnet pocket floors 0.6, T_mriezka webs 0.6, T_bok seam-lip root ridge 0.7: unloaded, but pressed
  during bonding or assembly. Press magnets with a flat tool and no hammer. Acceptable in tough resin.
* **m18** – P_sachta back floor 0.9 / 0.7 in the FPC groove is partly in the L2 path; the back wall at |x| < 6.1 sits on
  the hub disc and carries most of it. Not quantified; prefer 1.5.
* **m19** – T_drziak_repro ring 1.6 under 3 M2 thread-forming heads: low load, but needs washers and 2.0 (montaz M10).

## 5. Sharp inside corners at loaded roots (Z3.3)

There is no fillet operation anywhere in `t4_ram.py`, `t4_pan.py` or `t4_obal.py`. The only radii in the design are the
vertical box edges of `rbox` (well corners R 1.5, foot corners 0.8, dummy plate 8.0) and the LED-holder ears (1.0).
The bisector probe (`p10_fillets.py`) measured:

| loaded corner | part | measured R | load |
|---|---|---|---|
| ear plate / flange root (x −17.4, y 12.4) | L_ucho | 0 | L1, L2 |
| ledge root (y 17.1, z −41.1) | P_drziak_serva | 0 | head weight, L2 |
| tab post root (y 17.1, z −18.0) | P_drziak_serva | 0 | F11 |
| lower and upper bracket pad roots | P_sachta | 0 / 0 | F10 |
| arm face / hub step (x −14.5) | P_kluka | 0 | crank torque |
| tooth root (FE section) | P_koleso | none (corner at r 13.4) | all pan loads |
| neck / body step x 40.6 (az 0 and 90) | T_klb_L | 0 / 0 | L5, L6 |
| body / end step x 50.956 | T_klb_L | 0 | arm journal |
| J1 stop lug root z −98 | T_spodok | 0 | L4 |
| column web / rib corner | T_ram | 0 | L5 |
| door hook tab / root | T_dvere | ≈ 0.7 (curved tab face, inconclusive) | L7 |

Also sharp according to the code (boxes fused without fillets): the column foot / U-rib ends at z −77, the cradle-wall to
F2-boss junctions, the pan-servo posts under their 3.6 shelf, the T_stred screw-boss webs, the collar-tube gussets and the
side-cap seat flange root. Every one of these needs R ≥ 1 (R ≥ 0.5 where space forbids).

## 6. Numbers added to known montaz findings (not re-reported)

* **M01** – The stage rises 1.24 mm before the ring holds it. The ±90° stop is lost after 0.70 mm. The mesh face drops
  3.2 → 2.16. The ring glue carries 0.014 MPa. The fix (a) was checked: 0.57 MPa hub-disc punching, 0.28 MPa M3 insert
  bond.
* **M03** – At the specified torques every bonded insert is overloaded: M2.5 13.6 MPa and M2 12.4 MPa on the epoxy (rows
  57–58). The walls do not matter until the torque is fixed.
* **M04** – Strip-out forces 119–359 N against a 250 N preload (row 59). Hoop factors are 1.4–2.6 × a rule boss (row 62).
* **M05** – Crank countersunk M2.5: 54 MPa hoop in the 1.18 wall. Countersunk F2 cone bearing about 38 MPa at 0.3 N·m.
* **M06** – No new numbers. The press fits must become bonded slide fits. The pivot seat (S06) is also overloaded.
* **M07(b)** – Door hooks 7.4 / 14.3 MPa (S15).
* **M08** – The printed 21T serration at 0.30 N·m: flank bearing 11 MPa if all 21 teeth bear, 33 MPa if a third do. Hoop
  6.5 MPa in the 1.18 wall. At MG90S stall: 7.9 / 23.8 / 4.7 MPa (p09). Fail.
* **M10** – L_ucho in resin: FE 60 MPa (row 16). L_pata thread: rows 33–35. P_drziak_serva lands: head bearing 52 MPa at
  0.15 N·m.
* **M11** – The column and cap-flange compliance found here (S08) adds to the arch lean.

## 7. K4 thin features – are they loaded, and are they acceptable in resin?

| K4 declared feature | loaded? | resin verdict |
|---|---|---|
| T_stred 0.6 floors behind the frame magnet pockets | magnet pull acts away from the floor (glue 0.13 MPa); pressed at bonding | OK with care (m17) |
| T_stred relief step 1.0 at the crown | no | OK |
| T_bok seam-lip root ridge 0.7 | slides on during assembly | OK (m17) |
| T_dvere hook tabs 0.85 | yes, every opening | **FAIL** (S15 / M07) |
| T_mriezka webs 0.6 | no (glued); handled | OK in tough resin (m17) |
| T_drziak_repro ring 1.6 | lightly, by 3 screws | needs 2.0 + washers (m19) |
| T_spodok skirt 1.0 | handled / knocked | **FAIL** (S11) |
| T_ram 0.7 floor behind the F8 inserts | no (pull is toward the face) | OK |
| T_ram stop ring 0.7 × 1.2 | yes: F8 clamp, cap knocks | **FAIL** sustained at the specified torque (S09) |
| T_ram 0.9 shoulder behind the F5 insert | sustained grub-screw reaction | creep (S09) |
| T_ram 0.7 collars above the 4 cradle F2 seats | no (preload pulls away) | OK |
| T_ram 1.4 ring of the 6 F2 bosses | yes (L7) | **FAIL** at the specified torque (row 57, M03) |
| T_ram standoffs 1.0, clip arms 1.2 | clip flexes | M07(a) |
| T_ram 1.2–1.4 walls at cradle / post pilots | yes (L7, F4) | **FAIL** at the specified torque (row 59) |
| T_ram spigot Ø10 wall, flange step 1.0 | disc springs (sustained) | creep (S09) |
| T_paluba 0.6 under the stop groove | yes (L2, L3) | **FAIL** (S05) |
| T_paluba 1.4 around F3 holes, FPC wall 1.6 | lightly | OK |
| T_prichytka_fpc 1.13 at the countersunk screw | yes (L7) | **FAIL** (row 59, M04 / M05) |
| P_sachta back floor 0.9 / 0.7 | partly (L2) | prefer 1.5 (m18) |
| P_sachta glue groove (top plate 1.2 left) | L1 path, low stress | OK |
| P_sachta lands 0.7 | PTFE tape rubbing | OK |
| P_koleso FPC lip 0.6 | no | OK |
| P_koleso 0.6 floors under the dowels | no (bond carries the torque) | OK |
| P_drziak_serva ledge 0.8 | **yes – sustained head weight** | **FAIL** (S02) |
| P_drziak_serva lands 0.85 / 1.05 at F10 | yes (screw heads) | **FAIL** (S03, S12) |
| P_kluka hub wall 1.2 | yes (torque + countersunk wedge) | **FAIL** (S13, M05 / M08) |
| L_pata webs 0.81 / 0.85, skins 1.05 / 1.15 | yes (F12) | **FAIL** (S04) |
| L_jazyk prongs 1.5, countersink rim 1.1 | M1.6 countersunk at assembly | M05 |
| L_ucho webs 0.78 / 0.8 / 0.85 | yes | **FAIL** (S02) |
| T_svetlovod flange 1.2 | no (glued) | OK |
| T_klb walls 1.25 between counterbores / pockets | F8 heads (52 MPa at 0.15 N·m) | needs washers and the torque of S03 |
| STATUS_obal: socket rim 0.94 (visible white) | no load, can be knocked | chip risk, accept |

## 8. Creep, wear, heat – summary

* **Creep (6 MPa sustained):**
  * head weight on the bracket ledge: FAIL (S02);
  * F8 cap-flange clamp: FAIL at the specified torque (S09);
  * disc springs on resin, F5 grub, F10 friction (S09);
  * ear under the head weight 3.3 MPa: OK with margin 1.8;
  * deck / floor under the J1 servo weight: negligible.
* **Wear (Z3.8, 5 MPa projected for a sliding steel pin):**
  * ear slot 6.0 at L2 (FAIL) and 0.33 in running;
  * pivot 2.7 (L3), 4.0 (stall), about 1.4 at rated torque: OK;
  * journal on PTFE: low;
  * crank pin turning in its resin seat under 15–30 N: FAIL (S13).
* **Heat (Z3.10):** STS3215 on the 1.2 floor, MG90S on the 0.8 ledge, buck converter exactly 1.0 from the column (S10).

## 9. Scripts (all `/opt/venv/cad/bin/python`, run in `overenie_pevnost/`)

| script | what | runtime |
|---|---|---|
| `pv_lib.py` | STL reader, sections, scan integration, chords, z-buffer (from the first attempt, kept) | – |
| `p00_selftest.py` | analytic check of pv_lib, first column sections | 5 s |
| `fe2d.py` | plane-stress Q4 FE on a raster of a real section (self-test: `python fe2d.py`) | 3 s |
| `p01_gear.py` | measured tooth profile, Lewis, stop pin / groove, gear bond | 20 s |
| `p02_probe.py` | sections and chords of the crank, ear, foot, bracket, pads | 15 s |
| `p03_fe_lift.py` | FE of the ear, crank and gear tooth for L1 / L2 / L3 / L8 / head weight (+ PNGs `out/fe_*.png`) | 90 s |
| `p04_lift_joints.py` | lift-servo support statics, F10, F11, F12, foot, neck bond | 2 s |
| `p06_probe_shoulder.py`, `p07_probe_j1.py` | sections of the shoulder, column, cradle, floor, plinth, lug, deck | 30 s |
| `p08_rest.py` | L1 / L2 paths, pivot, shoulder, column, J1, door, L7 fastener table | 2 s |
| `p09_extra.py` | countersunk cone bearing, printed serration, column-foot carry-over, fix checks (metal F12, two-point servo hold, steel stop dowel, box column) | 1 s |
| `p10_fillets.py` | corner-bisector radius probes | 5 s |

Results: `out/*.log` (text) and `out/*.json` (rows).

## 10. MATERIAL (for the documents)

The same text is returned in the structured output `material`.

### Required cured properties (any brand – check its datasheet, tested to ISO 527 / ASTM D638 after the stated post-cure)
* Tensile strength ≥ 35 MPa (≥ 40 preferred).
* Elongation at break ≥ 15 % (≥ 20 % preferred).
* Flexural / tensile modulus 1.5–2.2 GPa.
* Flexural strength ≥ 45 MPa.
* HDT at 0.45 MPa ≥ 55 °C (≥ 60 preferred).
* Shore D 78–86.
* 405 nm and a standard FEP / ACF vat on the Saturn 4 Ultra.

Notched Izod is often not given; prefer resins sold as "tough", "ABS-like" or "nylon-like" over "standard" or "8K". The
design allowables follow from these: 12 MPa static, 6 MPa sustained or at an unfilleted notch, SF ≥ 2 on abuse cases.

### Example resins (datasheet numbers as found on 2026-11-17)
1. **Anycubic ABS-Like Resin Pro 2.** Tensile 35–40 MPa (US page) or 35–45 (EU). Elongation 35–40 % or 30–40 %. Flexural
   strength 35–40 or 40–50 MPa. HDT about 60–65 °C. Shore 82–84 D. Manufacturer shop pages read via search; the TDS PDF
   was not opened. It meets Z2 at the low end of tensile.
2. **Siraya Tech Blu** (standard). 39 MPa, 25 % elongation, E 1.5 GPa, Shore D 85 (retailer listings, UNVERIFIED; the
   official TDS page could not be reached; HDT not found). **Siraya Tech Blu Nylon Black** (official TDS as quoted in
   search results): 45 MPa at break, 50 % elongation, E 1.75 GPa; HDT not extracted. Blu Nylon or a Blu + Tenacious blend
   is the tougher option for the lift and pan parts.
3. **Elegoo ABS-Like Resin V3.0.** No numeric TDS found. Elegoo states only relative gains (+71 % elongation, +23 % bending
   strength, +34 % impact against earlier versions) and user reports are mixed. UNVERIFIED: ask Elegoo for the TDS or
   test a bar before using it for structural parts. It is the printer maker's resin and is profiled for the Saturn 4
   Ultra.
4. Not suitable for structural parts:
   * **Phrozen TR250LV** (high temperature): 25 MPa, E 0.9 GPa, 20 %, HDT 80 °C. Below the 35 MPa requirement; only for a
     heat-exposed, low-stress part.
   * **Phrozen Aqua 8K Gray** ("standard"): 21–35 MPa, 12–20 % on the spec sheet but 4.8–7.6 % in the V4 guide, HDT
     71–79 °C. Too brittle.

### Which parts may use ordinary (standard) resin
Only parts that carry no screw, tab, pin, magnet or handling load:
* `T_svetlovod`: it must be clear anyway; clear standard or clear tough;
* optionally `T_mriezka`, though its 0.6 webs are better in tough resin.

Everything else carries a screw, insert, pin, magnet or load path (shells included: the L1 path runs through T_stred and
F1). **Recommended plan: one tough resin for every part, then paint** (2K satin white / black as on the head).

**Not in resin at all** (results of this check):
* pan gear and pinion in brass (S01);
* `L_ucho` (and preferably `L_pata`) in aluminium or stainless (S02, S04);
* pan stops and J1 stop as steel dowels (S05, S07);
* steel washers under every head and on both sides of every spring (S03, S09).

### Print, wash, cure
* Orient load-critical parts so that tension faces and fillets are free of supports (teeth roots, ear, bracket roots).
  MSLA strength is nearly isotropic; support marks are the notch.
* Wash in IPA ≥ 95 % (or the cleaner the resin maker specifies): 2 × 2–3 min, dirty then clean bath. Keep the wash short;
  tough resins swell and soften in alcohol.
* Let parts dry completely (≥ 30 min, or blow out the holes) before curing. Trapped IPA gives soft, cloudy, weak zones.
* Post-cure exactly as the datasheet says (typically 405 nm, 2–5 min per side for small parts, warm cure only if stated).
  **Over-curing embrittles:** never exceed about 1.5 × the stated time. Do not leave parts in the curing station or a
  sunny window.
* Remove supports before curing on thin features, where it is less brittle.
* Wait 24 h before loading or drilling.

### Drill and ream after curing
* Model holes slightly undersize and drill them to size with sharp HSS bits at low speed, pecking, without heat.
* Fit holes are slide fits, + 0.05–0.10 mm.
* Drill list (montaz M06): Ø1.7 (M2 pilots), 2.05 (Ø2 pins), 2.3 (M2 clearance), 2.8 (M2.5 clearance), 3.3 / 3.6 (M2 /
  M2.5 inserts, OD + 0.1), 6.1 (running bore on the Ø6 pivot; ream 6.05 H8 if available), 37.15 (6805 seat, file to fit).
* Never thread-form near an edge, and observe the torque table (S03).

### Bonding
* Use a structural 2-component epoxy (slow, ≥ 30 min pot life) for inserts, pins, bearings, magnets, the gear and the
  ring.
* Assumed shear strength on abraded resin or knurled brass: 8–10 MPa. This is an ASSUMPTION; read the epoxy's datasheet
  and do a pull test on one insert.
* Prepare: abrade (240 grit), wipe with IPA, and bond only fully cured parts (uncured resin inhibits epoxy). Slide fits
  0.05–0.10, cure 24 h at room temperature before loading.
* Do not use cyanoacrylate for structural joints, the 6805 seat included: it is brittle and weak in peel.
* Keep anaerobic threadlocker off resin.

### Ageing and limits
* Keep parts out of direct sunlight; UV keeps curing the resin, which embrittles and yellows it. The paint is the UV
  protection.
* HDT 55–60 °C: no heaters, car dashboards or sunny windows. Keep ≥ 1 mm of air between servo cases and the buck converter
  and any loaded resin.
* Set servo torque and temperature limits in firmware.
* Sustained stresses ≤ 6 MPa: resin creeps.
* Uncured resin is a skin sensitiser: gloves and ventilation; dispose of used IPA correctly.

### Sources (searched 2026-11-17; host pages of elegoo.com and siraya.tech were not reachable from this session)
* STS3032: rcdrone.top/products/feetech-sts3032-servo-motor, evelta.com (sts3032 6v 4.5kg), aifitlab.com.
* STS3215: dfrobot.com/product-2961.html, openelab.io (C001 / C044 / C046), eu.robotshop.com (12 V 30 kg·cm),
  servodatabase.com.
* MG90S: components101.com/motors/mg90s-metal-gear-servo-motor, scribd MG90S Tower Pro sheet.
* Magnet: supermagnete.de S-05-02-N52N.
* Resins: anycubic.com ABS-Like Resin Pro 2 (US / EU / UK pages); siraya.tech TDS pages (as quoted by search);
  phrozen3d.com TR250LV and Aqua 8K pages; elegoo.com ABS-Like V3.0 page (qualitative only).

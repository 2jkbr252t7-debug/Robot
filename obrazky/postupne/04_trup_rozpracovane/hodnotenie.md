# T1 – independent judgement of the internal packaging concepts (torso + base)

Judge: independent reviewer. Inputs: `k2/`, `k3/` (layout.json, check.json, envelope.json, koncept.md, prev_*.png).
**K1 was not delivered** – no `T1/k1` directory exists and the orchestrator passed only two summaries – so two concepts
were scored. Output: the merged final packaging in `T1/pack/` (layout.json, envelope.json, check.json, prev_*.png, pack.md).

User brief §0 decides the weighting. The user said "Nechcem také kockaté telo, ani podstavec, ani ruky … buď moderný,
podobný obrázku … pôjdeme zase postupne." So the packaging that wins is the one that leaves the exterior designers the most
freedom for SOFT, compact shells near the R01 size, provided it is mechanically buildable.

## 1. What I re-ran myself (do not trust the self-reports)

All re-runs were done with `t1lib` and are kept in `T1/pack/judge/`.

| check | K2 claimed | K2 re-run | K3 claimed | K3 re-run |
|---|---|---|---|---|
| static clashes | 0 | **0** | 0 | **0** |
| `sweep(STD_POSES)` | 10 instances, all arm↔head | **10, all arm↔head** (poses 10, 12, 13, 16) | (20 incl. own poses) | **10 in STD, all arm↔head** (same poses) |
| tipping rest | 20.1° / 27.4 mm / 16.1 at 0.15 g | **20.1° / 27.4 / 16.1** | 22.5° / 29.0 / 18.5 | **22.5° / 29.0 / 18.5** |
| tipping worst (arms 90–100°, lift 20, tilt 40) | 15.9° / 10.4 at 0.15 g | **15.9° / 10.4** | 17.4° / 11.9 | **17.4° / 11.9** |
| mass | 892 g | 892.2 g | 918 g | 918.1 g |
| gear centre distances | J1 m1 18/18 C 18; pan m0.8 18/36 C 21.6 | correct; the mesh overlap is constant over J1 ±150 and pan ±85 | pan 18→20→36 m0.8, C 15.2 / 22.4 | correct (computed from the part positions) |
| allowed pairs hiding moving clashes | – | none (the overlaps of every allowed pair stay constant over 7 poses) | – | none: `A_*_servo × T_shell` = 0 mm³ in all poses; K3's 63 allow-pairs are only over-cautious |
| parts outside their soft shell | – | only intended ones: the J1 parts in the plinth gap, the spline boss, the wheel and caster bottoms | – | the J1 servo (19 cm³), plinth, bearing and FPC loop rise 18.6 mm above the base into the open torso bottom, by design |

All the arm↔head instances in both concepts lie outside the head-dependent arm limit tables, so firmware forbids them.
The proportions force this: in R01 the head (±55, ears ±58.8) is wider than the arm inner faces (±46.5–47.5).

### Datasheet spot checks (web search; vendor PDFs blocked by the proxy)
| part | used | found | confidence |
|---|---|---|---|
| Feetech STS3215 | 45.2 × 24.7 × 35, 55 g, 25T Ø5.9 | 45.2 × 24.7 × 35 mm, 55 ± 1 g, 25T/OD5.9 (DFRobot, Mouser, servodatabase) | high (footprint), medium (whether the 35 includes the boss) |
| Feetech STS3032 | 23.2(23.5) × 12.1(12.5) × 28.5, 20–21 g, 360° | 23.2 × 12.1 × 28.5, 20 g single-shaft; the C036 double-shaft is 32 × 12 × 27.5 | medium |
| EMAX ES9052MD (K2 arm) | 19.9 × 8.8 × 26.35, 1.3 kg·cm | 19.9 × 8.8 × 26.35, 5.5 g, 1.3 kg·cm @ 6 V (some listings 0.65) | medium; at 0.65 kg·cm it is still 14× the need |
| Hitec HS-35HD (K3 arm) | 18.6 × 7.6 × 15.5, 4.5 g, 0.8 kg·cm | 18.6 × 7.6 × 15.5, 4.5 g, 11 oz·in = 0.79 kg·cm, **nylon gears, analog** | high |
| 6806-2RS / 6805-2RS | 30×42×7, 22 g / 25×37×7, 22 g | 6806: 23–27 g | high (dims) |
| N20 + magnetic encoder | K2 34 + 8 + 5 plug; K3 34 incl. encoder | 1:150 listings: 30.5 mm body excl. shaft, gearbox 9 mm; the board/plug can stand proud | medium. K2's envelope is safe; K3 has only 2 mm to its J1 pillar |

## 2. Findings per concept

### K2 – off-axis gears, compact
**Strong points**
* It is the most compact and the most "soft-shell friendly". The minimum interior is a ≥ 40.9, so the smallest soft torso is about 86 × 78 and R01's 91 × 78 fits. The base minimum is 140.4 × 109.8, against R01's 138 × 110.
* The torso bottom is closed and rounded (R16). A thin rotating dark skirt r 34 fills the 3 mm gap, and that gap is exactly the R01 plinth ring.
* The reasoning holds. With the STS3215 shaft on the axis, the plug end lands at x 44.7, outside the soft interior at 42.3. I verified this.
* Every joint has real support:
  * J1: 6805 bearing, plus hard stops at ±155°.
  * Pan: a Ø6 pin with PTFE thrust at the bottom, and a dedicated Ø56.4 journal in a POM ring at the top, 36 mm apart.
  * Lift: a scotch-yoke crank with dead centres at both ends.
  * Arms: a servo in each paddle, with the spline held in a static socket.
* Pan uses a single direct 2:1 mesh.
* The arm range is honest: −45…+135, limited by the 180° servo.

**Defects found (all fixed in `pack/`)**
1. **Arm paddle wall 1.4 mm.** The cut box was 20.2 inside a 23 mm paddle. The brief asks for ≥ 2.0 on shells. The servo envelope also left only 1.65 mm on the outer side.
2. **J1 hub bridge was a 60 × 13 × 2 PETG plate.** It carries the whole rotating mass (≈ 0.5 kg) and the tipping moments. A 0.4 N·m moment (a 2 N push on the head) gives ≈ 45 MPa in the plate, which is at the PETG yield point. There is free height for a 6 mm beam (z 23–29), which gives ≈ 4 MPa.
3. **The casters (0, ±34) and cliff sensors (±14, ±40) sat directly under the battery cells.** This contradicts K2's own claim of bays that open from below. The bottom plate cannot carry them where the bay openings are.
4. **The pan and lift cable is not credible as specified.**
   * The 2 × 4 bonded wire ribbon in the drum rolling loop bends at R 5.2. That is R/D ≈ 6 for Ø0.85 wires, against the dynamic-flex practice of ≥ 10× the diameter.
   * The lift-loop envelope is 2.5 mm wide, which cannot hold a 3.6 mm ribbon in a rolling U at all.
   * The fix is one 2-layer polyimide FPC, 3.0 × 0.12 mm, standing on edge. Bend ratio: ≈ 43× in the pan loop and ≈ 29× in the lift loop.
5. **The J1 POM pinion** sees ≈ 28–33 MPa at the clutch-slip / 15 % torque-limit load, which is the POM fatigue level. It should be brass.

**Accepted risks:** zero vertical slack above the STS3215 (static, measure the servo); backlash in two gear pairs (≈ 0.2–0.6°, slotted cradle); total height 215 (top of the range); wheels visible as a ≤ 6 mm dark sliver in the ground gap (K3 has the same).

### K3 – J1 in the base
**Strong points**
* Direct-drive J1 on the axis: no gears, no slip clutch, no added backlash.
* Only 4 conductors cross J1, and the FPC loop is sized for ±170°.
* The heavy base gives a lower CoG: 22.5° / 17.4° tip angles.
* Height 210, in the middle of the range.
* The base packing is clean: packs between the casters, IR sensors outside the hatches.
* It answers the "can J1 live in the base?" question honestly.

**Defects found**
1. **Hard on the soft exterior.** This decides the ranking.
   * The base grows +7 % in both directions (148 × 118) and its corners are 97 % full.
   * The torso must be 92 × 84 with an **open bottom r 38.8** over a **static Ø75 × 18.6 mm plinth**. The plinth fills the lowest ≈ 23 mm of the torso.
   * So the torso cannot tuck its belly in – the soft rounded bottom that R01 shows – and its lip height varies from z 44 to 51 (visible as a wavy dark band in `prev_rest_front`).
   * This is the opposite of what the user asked for.
2. **The J1 servo stands on a 1.6 mm PETG bridge over the left N20, with 2 mm to the motor/encoder end.** Some N20 encoder boards and plugs stand proud of the 34 mm. The 1.9 N·m stall reaction also goes into that bridge.
3. **The pan top support is the finished B collar disc running in its static ring with PTFE tape in the 0.25 mm cosmetic seam.** A visible resin part becomes a plain bearing (wear, squeak, a seam that changes). K2 uses a dedicated journal instead.
4. **The arm range claim "−45…+180 mechanical" is physically impossible.** That is 225° of travel from an analog nano servo (HS-35HD class), which gives ≈ 180° at best with extended pulses. The servo also has nylon gears, so it relies entirely on the friction collar.
5. **The pan train has an idler.** Two meshes means ≈ ±0.3° backlash, and there is one more part.
6. **The pan cable is 10 loose AWG30 wires in a 160 mm C-loop trough.** It is workable (R ≥ 8), but undefined compared with an FPC.

## 3. Scores (0–100)

| criterion (weight) | K2 | K3 | note |
|---|---|---|---|
| compactness / freedom for a SOFT exterior near R01 (30) | **25** | 15 | K2 86×78 minimum torso with a closed round belly and a base ≈ R01; K3 +7 % base, open-bottom torso over a Ø75 drum, wavy lip |
| mechanical soundness + buildability, resin/FDM + hobby servos (25) | **19** | 16 | K2: every joint supported, weak J1 tooth (mitigated), thin bridge. K3: excellent J1 direct drive, but the bridge over the motor, the collar used as a bearing and the impossible 225° arm range |
| packaging margins + serviceability + assembly (15) | 10 | 9 | K2: zero vertical slack, casters/IR under the bays. K3: full base corners, 2 mm N20 margin, J1 service via snap hooks |
| stability (10) | 8 | **9** | 20.1° / 15.9° vs 22.5° / 17.4° (both re-run) |
| cable routing across pan / J1 (10) | 6 | **8** | K2: good J1 FPC, but the pan ribbon is under-rated and the lift envelope too thin. K3: 4-wire J1 FPC ±170, loose pan C-loop |
| cost / complexity / noise (10) | 6 | **7** | K2: 2 gear pairs + clutch + collet. K3: no J1 gears, but an idler and 6 ground contacts |
| **total** | **74** | **64** | |

**Winner: K2.** It is the only concept that keeps the internals inside a soft shell of R01 size with a closed, rounded
torso bottom and an R01-sized base, and its mechanics are coherent. Every defect found is local and was fixed without
changing the exterior envelope.

## 4. Grafts from the runner-up (K3) into the final packaging
| graft | from | why |
|---|---|---|
| Friction (slip) collar ≈ 0.25 N·m around the arm spline socket, in addition to K2's magnetic pull-off | `k3/koncept.md` §ARMS | Forcing an arm by hand slips the collar instead of stripping the micro-servo gears |
| J1 FPC rolling loop laid out for ±170° (≈ 110 mm in the channel instead of 103) | `k3/koncept.md` §2 | Cable margin beyond K2's ±155° hard stop, so homing and stop hits never tension the FPC |
| Run-while-charging policy: dock mode ≤ 3 W, the base node watches VBAT ≥ 8.35 V and puts the robot to sleep so the IP2326 terminates | `k3/koncept.md` §3 | K2 only said "terminates when off" – this makes it a rule the firmware can enforce |
| Head power estimate 1.5 W (K3) as the upper bound of the budget, 5 V-rail sequencing (no two stalls at once), 8–10 A BMS | `k3/koncept.md` §3 | Conservative runtime: the 3000 mAh typical drops to ≈ 7.9 h, so 3500 mAh cells are specified (≈ 9.2 h) |

Not grafted, with the reason:
* **K3 direct-drive J1.** It needs the servo on the axis. In the soft torso the plug end hits the shell; in the base it needs the plinth that defeats the soft exterior.
* **4 casters.** I computed the hexagon support: the same 22.1 mm margin at the worst CoG shift as K2's diamond, so it adds no stability.
* **Idler pan gear and collar-as-bearing.** Both are worse than K2's.
* **Under-neck lift servo.** It would add ≈ 12 mm of height to an already 215 mm robot.

## 5. Must-fix items for the winner – status in `pack/`
| # | item | status |
|---|---|---|
| M1 | Arm paddle wall 1.4 → 2.0; servo 0.35 mm inward (flush with the inner face, bonded to the outer wall); paddle outside unchanged | **applied** (layout) |
| M2 | J1 hub bridge 2 mm plate → 13 × 6 beam z 23–29 | **applied** (layout) |
| M3 | Casters carried by the battery-bay covers; cliff sensors moved to the corner pockets (±40, ±31) with bottom windows | **applied** (layout + envelope) |
| M4 | Pan + lift cable = one 2-layer polyimide FPC 3.0 × 0.12 on edge; lift-loop envelope 2.5 → 3.1 mm | **applied** (layout + text) |
| M5 | J1 pinion brass (sun was already brass); torque limit 15 %, slip clutch, re-homing on the ±155 stop | **applied** (layout material + text) |
| M6 | STS3215 top 80.5 vs deck 81.0: measure the real servo, shim the cradle | open (phase 2, static, no clash) |
| M7 | Arm servo 180° travel: verify on purchase; firmware arm table mandatory | open (firmware) |
| M8 | Wheels show as a dark sliver in the 6 mm ground gap: black tyres + a recessed dark foot | exterior note (envelope.json) |

All checks were re-run on the merged layout. The results are in `pack/check.json` and `pack/pack.md` §0.
* **Static clashes:** 0.
* **STD sweep:** 10 arm↔head instances, all outside the firmware table.
* **Own extra poses (23):** 3 head-envelope artefacts. The re-run real-head check gives 0.45 mm over the plateau and 1.0 mm for the lugs.
* **Moving-part clearances:** ≥ 1.0. The widened lift loop is 1.05 mm from the front frame column. The well-corner clearance of 0.6 mm in K2's `gaps2.json` came from an older layout; it is 1.0 here.
* **Mass:** 910.7 g, CoG z 74.5.
* **Tipping:** 20.1° at rest; 15.8° / 10.3 mm at 0.15 g in the worst pose.
* **Minimum soft envelope:** unchanged – torso a ≥ 40.9 (≈ 86 × 78), base ≥ 140.4 × 109.8.

## Zhrnutie (SK)
* Hodnotil som 2 koncepty; K1 nebol odovzdaný. Všetky kontroly som spustil sám a zhodujú sa s hláseniami: 0 statických kolízií. V štandardných polohách je 10 kolízií ruka ↔ hlava a všetky zakazuje firmvérová tabuľka limitov rúk. Prevrátenie: K2 20,1° / 15,9°, K3 22,5° / 17,4°.
* **Víťaz: K2 (74 b.) pred K3 (64 b.).** K2 sa zmestí do mäkkého, zaobleného trupu ≈ 86–89 × 78–80 so zatvoreným oblým spodkom a do podstavca ≈ 142 × 110 (ako R01).
* K3 má elegantný priamy pohon J1 v podstavci, ale podstavec je o 7 % väčší, trup má otvorené dno nad tmavým valcom Ø75 × 18,6 mm (nedá sa zaobliť brucho) a sľubuje rozsah rúk 225° s nano servom, čo nie je možné.
* Do finálneho balenia (`T1/pack/`) som z K3 prevzal:
  * treciu spojku v ramennom puzdre,
  * slučku J1 na ±170°,
  * pravidlo nabíjania počas behu,
  * konzervatívnejší odhad spotreby (preto články 3500 mAh).
* Opravil som chyby K2:
  * stena rúk 2,0 mm,
  * pevnejší mostík náboja J1,
  * kolieska a senzory okraja už nie sú pod batériami,
  * kábel hlavy cez pan a zdvih je plochý FPC,
  * pastorok J1 je mosadzný.

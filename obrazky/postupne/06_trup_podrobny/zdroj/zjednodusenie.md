# T4 torso – simplification and architecture review (resin, hobby builder, one MSLA printer)

Reviewer run of 2026-11-17 on the STL set `bbc136411578d453` (148 parts, 24 printed). Nothing in the design was changed.
Scripts and raw results: `/tmp/claude-0/gapwf/fin/T4/zjednodusenie/` (`m01`…`m06`, json + log). The findings of
`overenie_montaz.md` (M01–M16, m17–m22) are taken as known and are not repeated; this review builds on them. Where the
strength verifier's raw output (`overenie_pevnost/out/*.log`) already has a number, it is cited as "pevnost p0x".

**Verdict.** The two blockers come from the architecture: the glued collar ring is the only upper bearing *and* the only
axial stop of a stage that is bigger than the ring, and the only cable to the neck is soldered at the bottom of the well.
Both can be removed by construction. The recommended architecture: a **slim stage** (every permanent part r ≤ 26.5)
that passes the glued ring, a **journal bore stepped into T_stred under the ring**, a **pivot screw** for axial
retention, and **one stock FFC pair** from the controller to a **plug-in neck board** in the foot. Together with five
smaller simplifications this takes the torso from 148 to 133 parts, from 24 to 18 printed parts (17 with an optional
merge), and from 17 screw kinds to 4 plus the servo-supplied screws, the J1 pinion screw and one thread-forming size. It
removes both custom FPCs and every heat-set insert, and every servo can then be replaced. Nothing visible changes, the
finished head and neck parts are untouched, and every Z5 function stays.
The price is a real remodel of the PAN module (stage, foot, cables), a medium one of RAM (base part, deck) and a small one
of OBAL (bore step, door), plus re-running K2–K7.

---------------------------------------------------------------------------------------------------------------------

## 1. What was measured

| script | what | key result |
|---|---|---|
| `m01_stage_radius.py` | r_max per z of every stage / lift part; collar ring and disc; T_stred bore; corner radius of the finished neck; well-corner wall if trimmed to r 26.5 | ring r_in **26.748**, disc r **26.5**; T_stred bore r 28.342 for z −10.5…4.0, collar tube to r ≈ 30.6; P_sachta r_max **28.15** (corners, z −42.5…−17.5), 27.06 (z −16.5…−10.5), journal 28.07 (z −10.5…−3.5); neck blade 45.0 × 20.0 with **corner r 0.5** (z −36…−20) |
| `m02_pan_duct.py` | free height between the static deck and the rotating stage per (r, azimuth), sweep pan ±85; pivot zone; what occupies the J1 axis | duct r 16–25, az 10–170: floor −46.0, ceiling −41.9 → **4.1 mm**, **3.4 mm** under the drum lip (r 16.25, z −42.6); outside r 25.1 (az 45–135) there is no deck and the tower may not grow (lip 27.30 − 0.5); J1 axis r < 7: STS3215 z −83.3…−48.3, cap floor −84.5…−83.3, sun gear −90…−86.8 |
| `m03_stage_space.py` | free volume on the stage (stage frame, lift swept 0…20, crank swept), inside PAN_ENV and above z −41.2; door line of sight (81 lines from the opening) | free: +X end 89 %, −X end 92 %, front face below the journal 93 %, back-right corner beside the bracket 89 %, below the bracket lug 37 %. Door: **±X ends at pan ±85: 81/81 lines free**, +X end window at the foot (pan +85) 85 %, back-right corner (pan 0) 26–33 %, front face (pan ±85) 12 % |
| `m04_inventory.py` | categories, screw kinds, T_ram + T_spodok merged envelope | 17 screw kinds; merged part 89.6 × 60.7 × 95.8, 45.5 g resin, fits 211.68 × 118.37 × 220 |
| `m05_numbers.py` | every derived number quoted below (FFC electrics and bend ratios, pivot stack, retention stresses, journal) | see sections 3–4 |
| `m06_counts.py` | part counts before / after from parts.json and the deltas of this report | 148 → 133 parts; 24 → 18 printed |

Catalogue data (web search, snippets only; the vendor pages could not be opened from this session): a 0.5 mm-pitch
6-way FFC is 3.5 mm wide with 0.035 mm conductors, rated 0.5 A (Würth 6876, RS listing). GCT and Assmann also rate
0.5 mm FFC at 0.5 A per conductor and 1.0 mm FFC at 1 A. The Molex 0.50 mm FFC spec gives ≤ 2.2 Ω/m per conductor.
ISO 8735 / DIN 7979 pins with an internal thread start at Ø6 with an M4 thread and a length of 16. The 5-pole width
(3.0) is derived from the same 0.5 mm rule and is **not verified**.

---------------------------------------------------------------------------------------------------------------------

## 2. TASK 1 – options checked against the geometry

| option | measured fact | verdict |
|---|---|---|
| **(a) as written by the verifier**: stage r ≤ 26.5, collar disc in the ring = upper bearing, shoulder screw in the deck | the pivot alone lets the stage tilt: pin r 3.000 in bore r 3.024 over 3.0 mm of bore → **0.92°** → **0.62 mm** at the disc (z −2), against a 0.25 visible seam. The disc and ring are painted, visible parts, so any rubbing shows. | the slim stage and the screw are right; using the visible seam as a bearing is not → **(a′)** |
| **(a′) slim stage + journal bore stepped into T_stred under the ring** | T_stred keeps r 28.35 for the ring seat (z −2…4) and gets a shoulder at z −2 plus a bore **r 26.65** for z −10.5…−2. The tube wall goes 2.25 → 3.95 (+2.9 g). Stage journal r 26.50 incl. 0.13 PTFE tape → **0.15 radial** (as now). Stage vs ring: **0.248** radial | **recommended** (section 3) |
| (b) removable collar ring (bayonet / screws) | the ring is 1.5 wide (r 26.748–28.25) × 6 tall, a finished B part (§3.2). Lugs mean a modified copy. There is no grip for turning except the painted top, no room for screws, and a lock needs a flexing part. | reject – changes a finished part, adds a tool and a lock |
| (c) top-down, T_stred last | slim stage vs white lip (27.30 at x 0) 0.80 ✓, but pan pinion tip y −28.8 vs lip relief 27.55 (**1.25 overlap**) and lift module y 29.3 / 30.95 vs 27.30 ✗. Both must go in after T_stred, and the pinion then sits under the stage. | reject – the pinion and the lift module make it impossible |
| (d) merge T_ram + T_paluba + clamps | merging the **deck** into T_ram traps the J1 servo: it must drop in from above with its pinion through the floor slot, and the deck is its only service lid. Merging **T_ram into T_spodok** instead removes F2: 89.6 × 60.7 × 95.8, 45.5 g, fits. | do T_ram → T_spodok; keep T_paluba; delete T_prichytka_fpc |
| (e) connector at the foot vs pigtail + inline connector | a stage junction board must sit at a ±X end (the only spots with door access, 81/81 lines). That is r > 26.5, so it would have to come off before the stage is pulled, and it has no mount within r 26.5 (end wall 1.6, only 1.4 mm to r 26.5 at y 0). A plug-in **neck board in the foot** moves out with the neck, and its ZIFs face the +X window (85 % line of sight at pan +85). | **neck board in the foot** (verifier's M02 fix a), fed by stock FFC |
| (f) stock FFC / wires instead of both custom FPCs | duct 4.1 / **3.4** high. A 5-pole 0.5 mm FFC is 3.0 wide and fits unchanged; 6-pole (3.5) needs the drum lip raised 0.5; 8-pole (4.5) does not fit. **Two stacked 5-pole FFCs = 10 conductors**: 3 × 5 V, 3 × GND, TX, RX, PWM tilt, PWM lift. Rated 1.5 A per rail vs 1.4 A peak (head 0.5 + one MG90S stall 0.7 + other MG90S 0.2). Drop over 200 mm: **0.41 V at 1.4 A**, 0.12 V typical; the custom FPC (0.45 × 12 µm, 2 per rail) gives 0.89 V. U-turn R 3.9 / t 0.1 → R/t 39. Copper on the neutral axis gives ≈ 0.45 % strain; the verifier gives ≈ 1.5 % for the 2-layer FPC. **Loose wires** in the duct: R/D 4.9 with Ø0.8 wires, and 10 wires need 3 layers in 3.4 mm. | **stock FFC pair** for pan + lift. Loose wires only as a fallback for low cycle counts. |
| (f) J1 crossing | only base ↔ torso crosses J1, because the battery is in the base (pack §3): VBAT, GND, data bus, wake. A capsule slip ring needs the axis, but at r < 7 the STS3215 occupies z −83.3…−48.3 and only **2.3 mm** remain between the sun gear top (−86.8) and the cap underside (−84.5). | no slip ring. Stock FFC in the base loop (base round); the torso keeps only the floor slot (6.8 wide fits 2 × 3.0 flat) and a ZIF on the carrier |
| (g) crank on the supplied MG90S horn | the crank zone x −17.0…−12.8 equals horn hub + arm. The B neck already uses a cut horn (arms 1.6 thick). With an assumed arm width of 4.0 at r 10 and L1 × 2: 9.4 MPa net tension and 9.4 MPa pin bearing in the nylon/POM horn. Pin radius tolerance ±0.1 only moves the stroke ±0.2, because both ends are dead centres. | do – removes P_kluka, the printed spline (M08) and the countersunk crank screw |
| (h) one screw family | 17 kinds now (m04) | M2 × 6 / × 10, M2.5 × 6 / × 8, all ISO 7380, into bonded inserts or captive square nuts DIN 562 M2, plus M2 thread-forming for one-time joints, plus the servo-supplied screws and the M3 J1 pinion screw |

---------------------------------------------------------------------------------------------------------------------

## 3. Recommended architecture

### 3.1 Principle
1. **Everything that stays on the pan stage is inside r 26.5.** The stage then leaves upward through the glued ring
   (r 26.748) whenever the neck and the lift module are out. Everything wider leaves first: the neck through the disc
   slot, and the lift module, ear and lift-loop part of the FFC through the door.
2. **The upper bearing is a journal in T_stred below the ring.** The ring is decoration and seam only, never a bearing or a stop.
3. **Axial retention is a screw on the pan axis**, reached from above through the empty well.
4. **Every rotating or lifting joint is crossed by one stock FFC pair.** The neck plugs into it at the foot. All
   disconnects are door-reachable at pan +85 / 0, except the controller ZIFs, which sit right behind the door.
5. **Resin carries no thread that is opened in service.** It is all bonded brass inserts or captive square nuts.

### 3.2 Part list (printed, all one tough ABS-like resin + paint)

| part | what it does | change vs now |
|---|---|---|
| **T_spodok** (= old T_spodok + T_ram, one print 89.6 × 60.7 × 95.8, ≈ 45.5 g) | base plate, 6805 seat, J1 cradle and pocket, pan-servo posts, controller / buck / amp mounts, both shoulder columns, cap spigot | merged; F2 (6 screws, 6 inserts, 6 countersinks over 0.77 mm) gone; columns are continuous with the floor (arm loads L5/L6 no longer go through two M2.5 inserts) |
| **T_paluba** | J1 servo lid (clamps it on foam), pivot boss, FFC duct wall r 23.5–25.1, static FFC slot | resin; pivot boss raised to z −44.0 with a bonded M2.5 insert; stop groove → 2 bonded Ø2 pins; FFC slot instead of clamp; F3 into bonded inserts |
| **T_stred** | centre band + collar tube; **ring seat r 28.35 z −2…4 on a new shoulder at z −2**; **journal bore r 26.65, z −10.5…−2** (lead-in chamfer) | bore step (internal, invisible); F1 bosses r 3.4; nothing else |
| T_bok_L/P, T_klb_L/P, T_svetlovod, T_mriezka | unchanged roles (approved exterior, hidden F8) | F8 → bonded inserts, pattern turned 30° off the key slot |
| T_dvere | door, 4 magnet pairs, located by the frame ledge | hook tabs deleted |
| T_drziak_led, T_drziak_repro (or one front bracket, P10) | LED box, speaker clamp | resin; optional merge |
| **P_sachta (slim)** | well 47 × 22 (inner corners **R2.5**), outer trimmed to **r 26.5** over the full height (corner wall **1.35**, neck-corner clearance **0.59**); journal band **r 26.37 + 0.13 PTFE tape**, z −10.5…−3.0; top plate, hub disc, back floor, bracket pads | journal drum r 28.07, fin, apron groove, Ø4.8 tool hole and the four sealed pockets (M09) gone |
| P_koleso | pan gear + FFC drum | stays a separate part; material / joint per the strength review (pevnost p01: printed m0.8 teeth need 48 mm face for L3) |
| P_drziak_serva | lift module carrier (door) | resin; L2 must not go through the 0.8 ledge (pevnost p04) |
| L_pata | foot: bonded to the front neck half; **neck-board pocket under its +X end (≤ 12 × 16 × 1.8)**; **counterbore Ø10 × 2.3** over the pivot screw; captive **DIN 562 M2** square nut for F12; printed key for the ear (no Ø1.5 dowel) | resin, no thread in resin |
| L_ucho | ear (slot for the crank pin) | resin, webs ≥ 1.2, slot liner / thickness per strength |
| Z_naboj_test | bench fixture, not part of the robot | resin |
| deleted | T_ram (merged), T_prichytka_fpc, P_kluka (horn), L_jazyk (no tongue), T_puzdro_L/P + 4 disc springs (deferred to the arm round, T_klb bore Ø8.05 / Ø10.2 frozen as the interface) | |

Bought, new or changed: **2 × FFC 0.5 mm 5-pole, 200 mm** (stock length; fold the excess at the carrier end), and
**DPS_krk** neck board (rigid 0.8, ≤ 12 × 16): 2 × low-profile ZIF 5p (≤ 1.0 high, to fit the 1.8 pocket) + 7 solder
pads for the B wires + 3 pads for the lift-servo pigtail. Also: a lift-servo pigtail of 3 × AWG30 silicone with an inline 1 × 3 connector; a pivot sleeve Ø6.0 × 3.1
(steel or brass tube); an M2.5 × 8 ISO 7380 screw and a DIN 9021 M2.5 washer (Ø8 × 0.8); 2 × Ø2 stop pins; square nuts
DIN 562 M2. On the carrier: 2 × ZIF 5p for the pan pair, plus 1–2 for J1, at z ≥ −70 and facing the door.
Deleted: custom pan/lift FPC, micro junction `spoj_zdvih`, F5 set screw + insert, FPC clamp screw, crank screw, tongue
screw, ear dowel, the deck stop dowel `kolik_dorazu`.

### 3.3 Upper bearing (collar)
* Measured: ring inner r 26.748, disc r 26.5, today's T_stred bore r 28.342.
* New bore r 26.65 (z −10.5…−2.0). Stage journal r 26.50 incl. tape → 0.15 radial. Tape 0 / 0.13 / 0.26 is the
  adjustment shim (Z3.12). The disc keeps its 0.248 running seam to the ring and is now centred by the journal 1 mm below it.
* The shoulder at z −2 gives the glued ring a flat axial seat, so B montaž step 10 ("flush with a flat plate") gets easier.
* Journal load from a 10 N side push on the head (assumed head centre z +40): 23 N → **0.058 MPa**.
* M11 (lean of the arch): F1 holes in the base are Ø3.2 clearance. Tighten F1 only after the stage spins freely. The
  spigot (0.21–0.28) leaves enough float.

### 3.4 Pivot, axial retention, load paths
* **Pivot stack.** The deck boss carries a bonded M2.5 insert (Ø3.5 × 3.5) and a Ø6.1 × 1.0 seat for the sleeve. The
  sleeve is Ø6.0 × 3.1 (z −44.0…−40.9), so its top stands 0.10 above the hub disc. The M2.5 × 8 ISO 7380 screw and the
  DIN 9021 washer clamp the sleeve. The washer overlaps the hub disc, axial play **0.10** (shim with 0.1 washers).
  Top of the screw head is at z −38.7, which needs a counterbore of 2.3 in the 4.0 foot (1.7 left). The gear and hub
  bore (reamed Ø6.05–6.10) runs on the sleeve over 3.0 mm.
  A bought internally threaded Ø6 pin (ISO 8735 / DIN 7979, M4) would be simpler, but it starts at 16 long. It would
  reach z −56.9, through the deck underside (−47.8) into the STS3215 (top −48.3), so a sleeve + screw is used instead.
* **L1 (15 N up, ×2 = 30 N).** Path: head → neck → foot → ear → crank pin → horn → MG90S → bracket → F10 → well →
  hub disc → washer → screw → insert → deck → F3 → base part → 6805 → base hub.
  Washer bearing 1.39 MPa, hub-disc punching 0.99 MPa, insert bond 0.78 MPa, all ≪ 6–12 MPa.
  The stop pin can no longer leave its groove: the play is 0.10, against 1.237 of lift under L1 today (pevnost p08 / g01).
* **L2 (30 N down).** At lift 0: foot → hub disc → gear → PTFE washer (0.09 MPa, pevnost p08) → deck → cradle walls → floor.
  This needs the foot to land on the hub disc instead of loading the crank and ledge. Recommendation: close the rest
  gap from 0.5 to 0.1–0.2 (strength review to confirm).
  Lift > 0: the crank back-drives the MG90S (30 N × 10 mm = 0.3 N·m > stall) until the foot lands. That yield is by design.
* **Radial on the pivot.** Sleeve bearing L3 **2.56 MPa**, L8 **3.77 MPa** (forces from pevnost p08), ≤ 5 MPa (Z3.8).

### 3.5 Cables
* **Pan + lift: one stock FFC pair (2 × 5p, stacked).** The ZIFs on the carrier sit at the door.
  * Path: deck slot → existing rolling-loop duct (inner run on the drum r 15.7, U-turn R 3.9, outer run on the wall
    r 23.5, z −46.0…−43.0, 0.4 under the drum lip) → riser at stage azimuth 8–17° (back sector, as today).
  * **Flat lift loop on the +X end wall.** The fixed leg is bonded flat on the end wall at y −6…−3 (r ≤ 25.4, so it is
    permanent and needs no fin). The U is in the x–z plane with R 2.8–3.0 (R/t ≈ 30), outer leg at x ≈ 31.1
    (r ≤ 31.7 vs PAN_ENV 32.2 at the top). The moving leg folds into the end window (narrowed to y −2.5…+4.5) and plugs
    into the 2 ZIFs of DPS_krk.
  * Conductors: 3 × 5 V, 3 × GND, TX, RX, PWM tilt, PWM lift.
* **Neck (B wires, unchanged parts).** The 7 B wires come down the neck tunnel into the foot slot (x 11.6–15.0) and are
  soldered on the bench to DPS_krk in the foot pocket. No connector crimping is needed, and the neck board leaves with the neck.
* **Lift servo.** Its lead is shortened and gets an inline 1 × 3 connector at the +X end, door-reachable at pan +85.
  A 3 × AWG30 pigtail from DPS_krk forms a 20 mm hanging loop beside the FFC loop (y +5…+8). The pigtail
  connector + loop must be laid out with K3.
* **J1 (base round).** Stock FFC in the base rolling-loop annulus. 2 × 5p in the frozen 7 mm channel gives
  4 × VBAT / 4 × GND = 2 A rated and 0.66 V drop at an assumed 3 A peak. That is marginal at 6.0 V, so the base round
  should use a 1.0 mm-pitch FFC or 3 × 0.5 mm. In the torso: floor slot unchanged, ZIF on the carrier.

### 3.6 Assembly order (bench groups B, torso steps T)
* B1 base part: ream / drill per a drill list, bond inserts, bond the 6805 (slide fit Ø37.15 + epoxy).
* B2 deck: pivot insert, sleeve seat, 2 stop pins, PTFE washer.
* B3 T_stred: F1 inserts, front stack (F13).
* B4 stage: P_sachta + P_koleso. FFC pair: anchor on the drum, riser, fixed leg bonded flat on the end wall.
* B5 lift module: MG90S + horn crank (pin drilled at r 10.0) + bracket.
* B6 neck per B montaž 1–8: foot bonded to the front half, B wires soldered to DPS_krk in the foot pocket.

| T | step | direction / access |
|---|---|---|
| 1 | J1 servo + pinion into the cradle; mesh with the dummy hub, set C 18.00 with shim strips | −Z |
| 2 | pan servo onto the posts (F4: M2 × 10 + square nuts) | −Z |
| 3 | foam, deck (F3) | −Z |
| 4 | carrier, buck, amp, capacitor, wiring; bench test on the stand | ±X / −Y |
| 5 | T_stred over the tower, F1 loose | −Z |
| 6 | glue the collar ring on the shoulder | −Z |
| 7 | pan pinion through the bore | −Z (tool at r 21.6 + 2.25 < 26.65 ✓) |
| 8 | stage + FFC pair through the ring; FFC tails down the deck slot into the carrier ZIFs | −Z, then door |
| 9 | pivot screw through the empty well; spin ±90; tighten F1 | −Z |
| 10 | lift module (F10) | door, pan 0 |
| 11 | neck from above (B 9) | −Z |
| 12 | at pan +85 through the door: FFC tails into the DPS_krk ZIFs, lift-servo plug | door |
| 13 | ear (F12 into the square nut) | door, pan 0 |
| 14 | collar disc (B 10) | – |
| 15 | caps, T_klb (F8) | ∓X |
| 16 | door | – |
| 17 | head (B 11–21) | – |
| 18 | torso onto the base | – |

That is 18 torso steps + 6 bench groups (spec §11 has 20 steps). Steps 3 and F2/F5 work are gone.

### 3.7 Service order (every servo replaceable)
* **Head / display:** B service only.
* **Tilt MG90S (neck):** head off (B E1–E5) → door, pan +85: open 2 ZIFs, unplug the lift pigtail → door, pan 0: F12
  → neck up through the disc slot (DPS_krk passes the window 9 × 23 and the slot) → B E7.
* **Lift MG90S:** door: unplug the inline 1 × 3 (pan +85), F12 and ear off the pin, 2 × F10 (pan 0) → module out through
  the door. The verifier's t02 path (ear off) found 0 crossings.
* **Pan STS3032, pinion, FFC, stage:** neck out + lift module out → pivot screw from above (hex 1.5, on the axis) →
  open the carrier ZIFs (door) → stage + disc + FFC pair up through the ring → pinion screw from above → F4.
  F4 sits at r 25.1, so a straight Ø4.5 tool hits the r 26.65 bore: use a ball-end 1.5 key, or a driver shaft ≤ Ø3.0
  (edge at r 26.6). Lifting the servo out through the bore is **not verified**; the fallback is T_stred off.
* **J1 STS3215:** the above + T_klb ×2 (F8) + caps → F1 ×4 → T_stred up → deck (F3 ×4) → servo up with its pinion.

### 3.8 What it costs (remodel)
* **PAN (major).** P_sachta slim: trim r 26.5, corners R2.5, journal r 26.37, delete fin / apron / tool hole / pockets,
  window narrowed. L_pata: pocket, counterbore, square-nut slot, key. L_ucho resin. Delete P_kluka and L_jazyk; add a horn
  model. FFC models: pan loop pair (same duct) and the flat lift loop (new envelope x 25.1…31.3, replaces FPC_LIFT).
  DPS_krk and the lift pigtail. PAN_ENV row z −10.5…−3 → 26.5.
* **RAM (medium).** Union T_ram + T_spodok, delete the F2 features. Deck: pivot boss + insert + sleeve seat, stop pins,
  FFC slot, F3 bonded bosses (r ≥ 3.4). F4 square-nut slots, F7 inserts, delete F5 and the clamp. Carrier: ZIF positions
  (M12–M14 still open).
* **OBAL (small).** T_stred bore step + shoulder: one cylinder add and one cut on the cached blank, ≈ 13 + 4 s per
  spec §4.1 timings. F1 boss r 3.4. Delete the door hooks.
* **t4_common.** COLLAR / R_JOURNAL / PIVOT / FPC_PAN / FPC_LIFT / WIN_END / FOOT.
* **Checks to re-run.**
  * K2, K3: new loop envelopes, the slim-stage clearances unchanged or larger.
  * K5: journal 0.15 in the new bore.
  * K7: new rows for the stage up through the glued ring, the neck up with DPS_krk, the lift module out, the pivot-screw
    tool channel, and FFC tails into the ZIFs.
  * K10: print strategy for the merged base part.

---------------------------------------------------------------------------------------------------------------------

## 4. TASK 2 – simplification table

Action: **remove / merge / off-the-shelf / keep**. The "ref" column points to the proposal ids of section 5.

### 4.1 Printed parts (24)
| part | action | reason | ref |
|---|---|---|---|
| T_stred | keep (+ bore step) | approved exterior, one arch for the seams; the bore step makes the stage serviceable | P01 |
| T_bok_L / T_bok_P | keep | approved seams x ±33.3 | – |
| T_dvere | keep, delete hook tabs | the 0.85 hooks are handled at every opening (M07b); the ledge + 4 magnets locate it, and it pops off undamaged (L6) | P07 |
| T_klb_L / T_klb_P | keep | visible joint, hides F8 and clamps the cap flange | – |
| T_puzdro_L / T_puzdro_P (POM) | remove (defer) | the arm and its servo / horn are not designed yet. A printed spline is forbidden (Z3.9) and the clutch belongs in the arm's torque path. Freeze only the T_klb bore Ø8.05 / Ø10.2. | P08 |
| T_svetlovod | keep | clear part, light bar | – |
| T_mriezka | keep | grey inset with an approved seam | – |
| T_drziak_led + T_drziak_repro | merge (consider) | adjacent (LED box z −36…−29, ring z −70…−36): one front bracket with 3–4 screws instead of 2 parts / 5 screws | P10 |
| T_spodok + T_ram | merge | removes F2 (6 screws, 6 inserts at 1.1–1.4 walls, 6 countersinks over 0.77); continuous column; fits the printer | P03 |
| T_paluba | keep | the J1 servo lid; merging it would trap the servo | P13 |
| T_prichytka_fpc | remove | FFC held by a slot + Kapton; the 2.2 clamp with a countersunk M2 was M04/M05 | P02 |
| Z_naboj_test | keep (fixture) | bench stand only; fine in resin | – |
| P_sachta | keep, slim | r ≤ 26.5 is what solves M01 | P01 |
| P_koleso | keep separate | wear / strength part (pevnost p01) – must stay replaceable; joint and material per the strength review | P20 |
| P_drziak_serva | keep | the lift module (r 33.4) cannot pass the bore; it is the door-service unit | – |
| P_kluka | remove → supplied horn | printed 21T spline (M08), countersunk M2.5 in a 1.18 wall | P05 |
| L_pata | keep, redesign | carries the neck board, the counterbore and the F12 square nut; no thread in resin | P02 / P04 |
| L_jazyk | remove | the FFC goes straight into the neck-board ZIF; the tongue and its M1.6 go | P02 |
| L_ucho | keep (resin) | separate because it cannot be lowered through the well with the foot; webs / liner per strength | P12 |

### 4.2 Fastener groups
| group | now | action | after |
|---|---|---|---|
| F1 T_spodok → T_stred | 4 × M2.5 × 8 csk, glued inserts, wall 1.4 | keep joint; bosses r 3.4; Ø3.2 clearance holes (M11) | M2.5 × 8 ISO 7380 + bonded inserts |
| F2 T_spodok → T_ram | 6 × M2.5 csk + heat-set | **remove** (merge) | – |
| F3 deck → T_ram | 4 × M2.5 × 6 pan + heat-set | bonded inserts r ≥ 3.4 | M2.5 × 6 ISO 7380 |
| F4 pan servo | 2 × M2 × 6 thread-forming, wall 1.2 | through the post into square nuts | M2 × 10 + DIN 562 |
| F5 J1 set screw | M2.5 grub + insert, reachable only with the right arm off (m17) | **remove**; set C with 0.1 shim strips, deck clamps | – |
| F6 J1 pinion | M3 × 8 csk | keep (bought pinion + servo shaft) | M3 × 8 ISO 10642 |
| F7 controller | 2 × M2 × 4–5 thread-forming, opened in service | bonded inserts r 3.25 | M2 × 6 ISO 7380 |
| F8 T_klb | 6 × M2 × 10 SHCS + heat-set (one 0.8 wall) | bonded inserts, pattern turned 30° | M2 × 10 ISO 7380 |
| F9 gear dowels | 2 × Ø2 + epoxy | keep / per strength | – |
| F10 bracket | 2 × M2 × 4, 2.3 engaged | pads +1.0, bonded inserts | M2 × 6 ISO 7380 |
| F11 MG90S tab | M2 × 6 thread-forming, opened when the servo is replaced | captive nut in a Ø6.4 post | M2 × 6 + DIN 562 |
| F12 ear → foot | M2 × 8 thread-forming in a 4.0 foot (1.15 walls) + Ø1.5 dowel in 0.81 webs | square nut in the foot (1.4 / 1.4 skins), printed key | M2 × 6 + DIN 562 |
| F13 LED / speaker | 5 × M2 × 6 thread-forming, one-time | keep (Z3.4b, bosses Ø5) | M2 × 6 thread-forming |
| F14 buck / amp | 4 × M2 × 4 thread-forming | bosses Ø5, one-time | M2 × 6 thread-forming |
| FPC clamp, crank, tongue | M2 csk, M2.5 csk, M1.6 csk | **remove** | – |
| pivot (new) | – | sleeve + washer + bonded insert | M2.5 × 8 ISO 7380 |
| **kinds** | 17 (m04) | | 4 machine + 1 thread-forming + M3 pinion + servo-supplied; inserts M2 / M2.5 bonded; 1 nut type |

### 4.3 Special bought parts
| item | action | reason |
|---|---|---|
| custom pan / lift FPC 3.0 × 0.12 (3 folds, 2 T-branches, solder paddle) | **off-the-shelf**: 2 × FFC 0.5 mm 5p 200 mm | fits the duct unchanged (3.0 in 3.4); 10 conductors; 0.41 V vs 0.89 V drop; copper on the neutral axis; unpluggable |
| custom J1 FPC 6.0 × 0.15 (base) | **off-the-shelf** FFC (base round) | slip ring impossible (axis occupied); prefer 1.0 mm pitch for the VBAT drop |
| micro junction `spoj_zdvih` (1.27 header on FR4 bonded to the FPC) | remove | the lift servo plugs into the neck board via a pigtail + inline 1 × 3 |
| DPS_krk neck board (new, rigid) | add | replaces the solder joint at the bottom of the 40 mm well (M02); rigid PCB, ordered with the carrier |
| DPS_riadenie carrier | keep (custom) | add ZIFs at z ≥ −70; M12–M14 (USB-C, connectors, bus power) still open |
| DPS_led | keep (or a cut stock strip if one with 5.0 pitch exists) | – |
| T_klb disc springs ×4 | remove (defer with the bush) | P08 |
| PTFE strips + journal band + washer | keep | they are the adjustment shims (0.13 steps) |
| foam pads (J1, MG90S) | keep | they absorb ±0.3 servo tolerance without tight pockets |
| magnets (door 8, shoulder 6) | keep | – |
| stop dowel in the deck groove (0.6 floor) | replace by 2 bonded Ø2 pins in the deck + a gear lug | groove floor 0.6 (M10), pin leaves the groove under L1 today |

### 4.4 Tight tolerances
| fit | now | action |
|---|---|---|
| journal 0.15 | r 28.20 in 28.35 | keep 0.15 at r 26.50 in 26.65; tape = shim |
| collar disc ↔ ring 0.25 | visible seam | keep; centred by the journal, not used as a bearing |
| pivot 0.025 | pressed pin Ø6 in Ø5.95 | Ø6.0 sleeve clamped by a screw; bore reamed Ø6.05–6.10 |
| 6805 seat Ø37.00 +0.05 "with CA" | press | slide fit Ø37.15 + epoxy (M06) |
| C 18.00 (J1) via F5 | set screw | shim strips 0.1 |
| C 21.600 (pan) | tab holes ±0.3 | keep |
| K3 clearances at exactly 1.000 (well ↔ pinion, floor ↔ deck) | zero margin | the slim stage does not reduce them; raise to 1.3 where the remodel touches them (Z3.12) |
| neck on the lands 0.17–0.30 | – | keep (finished neck) |
| crank r 10.00 | printed | drilled in the horn; ±0.1 harmless (dead centres) |

### 4.5 Assembly steps (spec §11, 20 steps)
| step | action |
|---|---|
| 1 inserts heat-set / glued | all **bonded** (epoxy); 6 fewer (F2), 1 fewer (F5) |
| 3 T_ram → T_spodok | **removed** (merge) |
| 4–7 J1, pinion, pan servo, deck | keep; F5 → shims |
| 12 stage through the bore | keep, now **through the glued ring** and reversible; + pivot screw |
| 13 lift module | keep; FFC no longer threaded on the stage |
| 14 ring glue | moved **before** the stage (step T6) – the ring is never in the stage's way |
| 15 neck with soldered FFC tail (impossible order, M02) | neck from above, then **plug** 2 ZIFs + 1 plug through the door |
| 16 ear | keep (square nut) |
| 19 door hooks | removed |
| service "16 → 12 backwards" through the glued ring (M01) | now possible: neck → lift module → pivot screw → stage up |

---------------------------------------------------------------------------------------------------------------------

## 5. Proposals ranked by benefit

| id | proposal | removes / solves | effort | rec. |
|---|---|---|---|---|
| P01 | slim stage (r ≤ 26.5) + T_stred journal bore r 26.65 under a ring shoulder + pivot sleeve / screw retention | M01 blocker, M09 cups, M06 pin press fit; the stop pin can no longer jump out (L1) | large | do |
| P02 | stock FFC pair from the carrier through pan + lift loops into a plug-in neck board in the foot; lift servo on a pigtail | M02 blocker, M15, M13a (crimp connectors on FPC), custom FPC, solder joint in the well, tongue, clamp, micro junction | large | do |
| P03 | merge T_ram into T_spodok | F2 ×6 + inserts ×6 + countersinks over 0.77 (M03 / M05), one assembly step, a weak joint in the arm load path | medium | do |
| P04 | one screw family + bonded inserts + DIN 562 square nuts; no thread in thin resin | M03 / M04 / M05 / m20; 17 → 7 kinds incl. supplied | medium | do |
| P05 | crank = supplied MG90S horn, Ø2 pin at r 10.0 | P_kluka, printed spline (M08), countersunk M2.5 in 1.18 | small | do |
| P06 | J1 mesh set by shim strips instead of F5 | grub screw, insert, side tool hole, m17 | small | do |
| P07 | delete door hook tabs | 0.85 handled features (M07b) | small | do |
| P08 | defer T_puzdro + disc springs to the arm round | 2 POM parts, 4 springs, a spline decision before the arm exists | small | do |
| P09 | pan stop: 2 bonded Ø2 pins in the deck + a lug under the gear | 0.6 groove floor, the dowel `kolik_dorazu` | small | do |
| P10 | merge LED box + speaker ring into one front bracket | 1 part, 1–2 screws | small | consider |
| P11 | J1 crossing: stock FFC in the base loop, no slip ring | custom J1 FPC | medium (base round) | do |
| P12 | ear located by a printed key + square nut | Ø1.5 dowel in 0.81 webs | small | consider |
| P13 | merge T_paluba into the base part | – (would trap the J1 servo) | – | reject |
| P14 | (b) removable bayonet collar ring | – (finished-part change, no grip, needs a lock) | medium | reject |
| P15 | (c) top-down build, T_stred last | – (pinion 1.25 into the lip, lift module 2+ outside it) | – | reject |
| P16 | (a) collar disc as the upper bearing | – (0.62 mm lateral at the disc vs 0.25 seam) | – | reject |
| P17 | loose silicone wires instead of FFC in the pan duct | – (R/D 4.9, 3 layers in 3.4 mm) | – | reject (fallback only) |
| P18 | capsule slip ring for J1 | – (2.3 mm free on the axis) | – | reject |
| P19 | stage junction board at a ±X end with the B wires as the lift loop | – (r > 26.5, no mount, competes with the loop) | – | reject |
| P20 | merge P_koleso into P_sachta | – (gear must stay replaceable; collar disc is glued on the stage) | – | reject |

---------------------------------------------------------------------------------------------------------------------

## 6. Keep as is (looks complicated, should stay)

* J1 drive off-axis (STS3215 at x −18, two brass gears, 6805 in a rotating foot ring, slip clutch in the base). The axis
  is taken by the stage stack and the hub. Direct drive or a slip ring has no room (2.3 mm free on the axis).
* Pan rolling-loop duct on a half-toothed drum. Measured, it is the only crossing that fits 4.1 / 3.4 mm. Only the
  cable changes to stock.
* Crank lift with dead centres at both ends: it holds the head without servo torque at rest and at full lift.
* Separate lift module through the door (r 33.4 cannot pass the bore).
* T_stred as one arch + two side caps + cap spigot + 8 seam tabs: they give the approved seams with no visible screws.
* T_klb clamping the cap flange with hidden F8: approved look, and it carries the arm.
* T_paluba as a separate lid: it is the only service access to the J1 servo.
* P_koleso as a separate part: the strength review needs it replaceable or bought.
* PTFE tapes / strips and foam pads: they are the shim and tolerance elements the resin rules ask for.
* Door with magnets as the service opening (lift module, controller, all disconnects).
* Collar ring glued (finished B part, approved 0.1 seam). After P01 it is never in the way.

---------------------------------------------------------------------------------------------------------------------

## 7. Not verified / assumptions (do not treat as passed)

* No CAD was changed and no K-check re-run.
  * The slim stage, flat lift loop, neck board pocket, pigtail loop and pivot stack are dimensioned from the STL
    measurements above, not modelled.
  * K3 / K7 must confirm the flat loop envelope (x 25.1…31.3, r ≤ 31.7 at the top) and the stage path up through the ring.
  * Lifting the STS3032 out through the r 26.65 bore is not verified.
* FFC data come from search snippets (pages not reachable from this session).
  * Verify on the purchased part: 5-pole width 3.0 (derived), thickness ≈ 0.1, 0.5 A per conductor, ≤ 2.2 Ω/m.
  * Bend life of FFC at R/t ≈ 30 (lift) / 39 (pan) is not known: bench-cycle 10⁵ before trusting it.
* Currents (head 0.5 A, MG90S stall 0.7 A, torso VBAT peak 3 A) are the task brief / assumed values, not datasheets.
* MG90S horn: arm width (assumed 4.0 at r 10), hub height and hole positions not measured; measure the supplied horn.
* ISO 7380 M2.5 head (dk 4.7, k 1.375) and DIN 9021 M2.5 (Ø8 × 0.8) are catalogue nominals, not checked here.
* `m03` free fractions use a 0.5 mm grid with 0.5 dilation and bounding-box fills for the servo / neck / foot; they are
  indicative. A z-parity interior fill was tried and dropped because it mis-filled the open well.
* Strength items cited from `overenie_pevnost/out` (p01, p04, p08) are that verifier's numbers, not re-derived.

Sources (web search, catalogue data):
- [Würth Elektronik 6876 FFC 6-way 0.5 mm (RS)](https://uk.rs-online.com/web/p/ribbon-cable/7635527)
- [GCT standard FFC jumper cables (Mouser)](https://www.mouser.bg/gct-standard-ffc-jumper-cables)
- [Assmann FFC datasheet](https://www.assmann-wsw.com/uploads/datasheets/ASS_7540_CArev.pdf)
- [Molex 0.50 mm FFC spec (LCSC)](https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2310121421_MOLEX-0152660321_C17735165.pdf)
- [DIN EN ISO 8735 table](https://fasten.it/norms/norm/din_en_iso_8735)
- [Kipp K1909 internal-thread pins](https://www.marek.eu/data/katalogove-listy/kipp/K1909.pdf)

# NOVA mini – T1 / K3 "J1 in the base" – internal packaging concept (torso + base)

Files (all in this folder): `layout.json` (t1lib), `gen_layout.py` (generator), `check.json` (all checks merged),
`envelope.json` (minimum interior for the exterior designers), `prev_*.png` (previews with the real B head; `prev_rest_*`,
`prev_awake_*` = lift 12.5 / tilt 10 / pan 30 / arms 60, −20; `prev_base_plan_*`, `prev_torso_plan_*` = internals only),
helper scripts `check.py`, `check_static.py`, `sweep_std.py`, `head_real.py`, `envelope.py`, `merge_check.py`.
World frame as in the brief (mm, Z up, floor z 0, FRONT −Y, robot RIGHT −X).

## 0. Result – and the honest answer to the K3 question

**Can the J1 STS3215 live in a 36–42 mm base?** Only partly. A standing STS3215 is 35 mm + spline/horn ≈ 40 mm tall and
45 × 25 mm in plan (+12 mm plugs). I tried every floor-level arrangement (servo along X / along Y, direct or 1:1 geared,
N20 line at y 0 / front / rear, packs front-rear / left-right / single cells, base up to +10 %): with **4 × 18650 + a coaxial
N20 pair + the STS3215 on one level only 3 cells fit** inside a soft pebble ≤ 152 × 121 – the superellipse corners kill
the 66 mm cell rows; a single-level layout needs ≈ 150 × 140. A lying servo needs bevel gears and is worse in plan
(45 × 40). The chosen K3 therefore **stacks the servo on a bridge above the left N20** (case z 21.9–56.9, spline up on the
J1 axis, direct drive). The **base shell stays 40 mm high** (shell z 6–40 + 6 mm ground clearance) and is a soft pebble
**148 × 118** (+7 % / +7 % vs R01) that holds everything, but the **top 17 mm of the servo rise into a static dark plinth
Ø75 (z 40–58.6)**. The plinth carries the J1 bearing and goes into an **open-bottom torso** – visually the R01 "dark gap ring"
(4–10 mm visible), technically it occupies the lowest ≈ 23 mm of the torso.
So K3 does **not** free torso height. Z_TT = 127.8 follows from: servo top 56.9 → J1 bearing/loop/deck 57.9–67.2 → pan gear
67.5–70.0 → crank tip 1 mm above the deck through a notch in the pan cup → crank centre 80.2 → + 47.6 (B neck geometry).
What K3 buys: **direct-drive J1 (zero backlash, no J1 gears, no gear hard stops, servo never loaded by the torso)**,
the 55 g servo low in the base, only **4 conductors across J1**, and a clean centred torso stack (deck → pan → lift → well).

| item | value |
|---|---|
| Z_TT (collar top) / total height rest / full lift | **127.8 / 209.8** / 229.8 (R01 target 205–215) |
| torso placeholder | **92 W × 84 D × 85.8 H** (z 42–127.8), superellipse n 2.35, R16, wall 2.2, raised collar plateau r 29.8 (1.5), open bottom r 38.8 |
| base placeholder | **148 × 118 × 40** (shell z 6–40, n 2.4, R10, wall 2), dark plinth Ø75 |
| arms | soft paddles 30 × 21 × 80 (14 above / 66 below the shoulder axis), shoulder axis (y 0, z 109.8 = 21 % below the top), outer faces ±68.5 |
| mass / CoG rest | **918 g** / (0.7, −1.0, 70.1) |
| tipping rest / worst | **22.5°** (margin 29.0, at 0.15 g 18.5) / **17.4°** (arms 90–100° forward + lift 20 tilt +40: 22.8 / 11.9 mm) |
| static clashes | **0** |
| sweep | 18 STD + 19 own poses, 20 clash instances, **0 unresolved**: arm-vs-head beyond the firmware arm table (15), crude t1lib head/lug boxes at B-table limit poses (5) – the real B meshes clear: head ↔ torso top ≥ 0.46 mm (at the B plateau edge, B table criterion ≥ 0.25), lugs/neck ↔ well ≥ 1.0 |
| min clearances moving parts | pan stage ↔ torso 1.0, neck/tongue ↔ pan stage 1.0, torso ↔ base (rigid) 1.0, arm ↔ torso 1.3, arm ↔ base 3.8 |
| runtime typical 4.3 W | **8.5 h** (4 × 3000 mAh) / **10.0 h** (4 × 3500 mAh); idle 2.9 W → 12.7 / 14.8 h |

## 1. Joints

### J1 – torso yaw ±150°
* **Actuator**: Feetech STS3215 7.4 V – case 45.2 × 24.7 × 35, 55 g, 25T spline Ø5.9, 12-bit magnetic encoder 360°,
  stall ≈ 19.5 kg·cm = 1.9 N·m @ 7.4 V [datasheet listings, high]; 2 × 5264 plugs on the far end face, assumed low on the
  face [medium] → 12 mm plug + bend envelope. Standing, **spline up on the J1 axis**, body along +X (shaft 11.5 mm from the
  −X end), static, screwed (4 × M2) to a PETG bridge 0.3 mm above the left N20 (pillar between the motor ends + 2 legs
  beside the motor).
* **Transmission**: direct. Stock Ø20 Al horn on the spline; the torso hub engages it with **2 dog pins (torque only,
  ±0.3 axial float)** – the servo carries neither the torso weight nor tipping moments.
* **Bearing**: 6806-2RS 30 × 42 × 7 (C0 ≈ 2.9 kN, 22 g) on the axis, z 57.9–64.9 (inner ring 1.0 above the servo top).
  Outer ring in the static plinth seat (3 PETG snap hooks; release with a pin through 3 Ø3 holes in the torso deck at
  J1 = 0), inner ring on the torso hub (hub land r 15–16.3; the deck is relieved over the outer ring/seat by 1.1).
  Rotating mass ≈ 440 g; a 1 N side push at the head (≈ 0.15 N·m) tilts the ball bearing < 0.1°.
* **Range / stops**: ±150° by the STS3215 EEPROM angle limits (steps 341…3755) + torque limit; the J1 FPC loop is laid out
  for **±170°**, so a 20° overrun damages nothing. Direct drive needs no gear hard stop; nothing in the base/torso
  interface collides at any J1 angle (all rotating parts below z 59.6 are outside r 38.8, the plinth is r ≤ 37.5).
* **Torque**: J_z ≈ 5.4·10⁻⁴ kg·m² (head 2.3, torso 1.8, arms 1.35, neck/pan 0.2 ·10⁻⁴). 150° in 1.0 s (trapezoid, 0.25 s
  ramps): α 14 rad/s² → 0.008 N·m; 2RS seals + FPC ≤ 0.02 N·m → **≤ 0.03 N·m vs ≈ 0.6 N·m rated / 1.9 N·m stall (> 20×)**.
  Vertical axis → no gravity holding torque.

### PAN – ±85° mechanical (±80° firmware)
* **Actuator**: Feetech STS3032 – 23.2 × 12.1 × 28.5 (incl. spline), tabs 32, 20 g, 4.5 kg·cm stall / 1.5 kg·cm rated
  @ 6 V, 360° 12-bit magnetic, serial bus [retailer listings, medium] – on the 5 V rail, **inverted (spline down) at the torso
  +X side** (case x 28.1–40.2, y −12.2…11, z 73.3–96.0), static (torso) → no servo cable across pan.
* **Transmission**: pinion 18T → idler 20T (Ø3 pin in the deck, at (19.9, 10.3)) → pan gear 36T, m0.8 POM, 2.5 wide,
  plane z 67.5–70.0 → **2:1** (servo ±170° for ±85°, inside its 360°). Backlash 2 meshes ≈ ±0.3° at the head
  (option: split spring-loaded idler).
* **Bearings**: bottom – Ø4 steel pivot of the pan gear in a bronze bush in the torso deck + PTFE thrust washer 0.3
  (axial ≈ 2.5 N); top – the B collar disc r 26.5 runs in the static ring r 26.75 lined with PTFE tape (≈ 0.05 radial).
  Radial supports 60 mm apart.
* **Stops**: EEPROM limits; nothing collides at any pan angle (all pan-stage parts inside r 27.2, all static torso parts
  outside r 28.0, verified 1.0 mm); only the cable loop limits (laid out for ±95°).
* **Torque**: J ≈ 2.7·10⁻⁴ kg·m²; 90° in 0.4 s → 0.014 N·m; thrust washer + ring + bush + loop ≈ 0.012 N·m → 0.026 N·m at
  the stage → **0.014 N·m at the servo (2 meshes, η 0.9) = 0.14 kg·cm vs 1.5 rated (10×) / 4.5 stall (30×)**.

### LIFT – 0 … 20 mm
* **Actuator**: MG90S (22.8 × 12.2 × 22.7, spline top 28.5, 13.4 g, 1.8 / 2.2 kg·cm @ 4.8 / 6 V [datasheet, high]) lying in
  the pan cup under the neck, **shaft along −X at z 80.2 (Z_TT − 47.6)**; case x −12.2…10.5, y −16.8…6, z 74.1–86.3
  (0.9 below the well, 1.0 below the neck bottom at rest); cable boot on the +y end face.
* **Transmission**: steel crank r 10 → Ø2 pin → slot 20.2 × 2.2 in a **new tongue** (PETG 2.9 thick, 2 × M2 into inserts in the
  neck bottom, at the −X end so the B wire exits at x 13–15 stay free) = scotch yoke (B_mechanism_review §5a).
  **Both end positions are dead centres** – zero holding torque, no buzz. The crank and the tongue foot drop through a
  notch in the cup plate down to 1.0 mm above the torso deck (this saved 4.4 mm of height). The 47 × 22 well (resin, 2 PTFE
  strips) is the linear guide; a 5 × 24.6 relief at its −X bottom (wall locally 1.3 thick) passes the slotted tongue foot.
  Analytic crank clearance to the neck ≥ 4.5 (neck bottom = z_c + 18.5 − 10·cos θ).
* **Load**: neck + head 211 g → 2.07 N + well friction ≈ 0.2 N → max 0.023 N·m (mid-stroke) = **0.23 kg·cm vs 1.8 (7.8×)**.
* **Stops**: dead centres + slot ends; firmware keeps the B tilt-vs-lift table.

### TILT – unchanged B design (MG90S in the neck), ±40° per the B lift table; worst gravity moment at ±40° ≈ 0.06 N·m vs
0.18–0.22 N·m (3×).

### ARMS – one actuator per arm, −45° … +180° (head-dependent firmware limit)
* **Choice: servo inside the arm paddle**, its spline + horn clamped in a static shoulder boss in the torso, the case turns
  with the arm. Why: inside the torso the pan/well sweep (r 27.2) leaves only ≈ 15 mm beside it at shoulder height – no
  servo with its shaft along X fits (MG90S needs 28.5); an MG90S *in* the arm would need a 27 mm paddle (R01: 18–22).
* **Actuator**: nano servo, Hitec HS-35HD class (18.6 × 7.6 × 15.5, 4.5 g, 0.8 kg·cm @ 4.8 V [datasheet, medium-high]) in a
  21 mm paddle (case x ±(49.5–65)). Horn clamped in the torso boss by a **friction collar slipping at ≈ 0.25 N·m**, so
  forcing the arm by hand cannot strip the nylon gears.
* **Torque**: arm 19.5 g, shell CoG ≈ 26 mm below the axis → 0.004 N·m at 90° + 0.0015 N·m dynamic (90° in 0.3 s) =
  0.056 kg·cm vs 0.8 (14×).
* **Clearances**: arm ↔ torso 1.3 (cap ↔ shell), arm ↔ base 3.8 (hanging, J1 0/90), arm ↔ arm 85.
  Arm ↔ head: the head is 110 wide and its bottom only 21 mm above the shoulder axis, so the up-swing is limited when the
  head faces forward. **Firmware arm table** (right arm, max angle with ≥ 2 mm to the head envelope over the full tilt
  range of that lift row; left arm = same with the pan sign inverted; back limit −45° always free):

  | lift \ pan | −85 | −60 | −30 | 0 | +30 | +60 | +85 |
  |---|---|---|---|---|---|---|---|
  | 0 (rest) | 180 | 175 | 104 | **94** | 111 | 104 | 180 |
  | 12.5 (awake) | 125 | 139 | 87 | 90 | 60* | 92 | 106 |
  | 20 | 119 | 132 | 101 | 93 | 135 | 108 | 114 |

  *60° because the row includes tilt −40 (head back drops towards the right shoulder at pan +30); with tilt ≥ 0 ≈ 110°.
  Computed with a 2 mm longer arm than the final one → conservative. Firmware: use the more retracted lift row and the
  more restrictive neighbouring pan column; "arms up" gestures first turn the head ≥ 75° away from that arm.
* **Cable**: 3 × AWG30 ultra-flex from the case end face over the paddle top → 240° arc slot (r 9–11) under the black cap →
  60 mm service loop in the torso (`T_kabel_ramena_*`).

### WHEELS
* 2 × N20 6 V 1:150 with magnetic Hall encoders (12 × 10 gearbox, body 34 incl. encoder + 10 mm D-shaft, ≈ 12 g
  [listings, medium; larger envelope taken]) coaxial on y = 0 (x ±16.5…±50.5, z 10–20), wheels Ø30 × 9 (PETG hub + TPU
  tyre) at x ±56.5, axle z 15, through floor slots; 4 × Pololu 3/8" ball casters at (±46, ±30), 0.5 mm above the wheel
  contact plane (the robot rocks ≤ 0.5 mm about the axle). DRV8833 on the base PCBA, PWM limited to 6 V effective.
* Torque: 0.92 kg, rolling + 0.3 m/s² + 5° slope → 0.6 N per wheel × 15 mm = 9 N·mm vs ≈ 150 N·mm stall (> 15×); max speed
  ≈ 0.3 m/s (use 0.15). The robot turns in place about the J1 axis.

## 2. Cable routing across PAN and J1
**J1 – 4 conductors, ±150° (laid out for ±170°)**: 2-layer polyimide FPC, rolled-annealed Cu 35 µm, 5 mm wide, standing on
edge – VBAT (4.6 mm trace, ≈ 4 A), GND (2.6 mm), BUS (0.3), GND/shield (0.3). Path: base PCBA → up inside the plinth →
slot in the plinth top plate → static anchor on the bearing seat (inner wall r 23.5) → **rolling loop in the annulus r 24–36,
z 59.7–64.7** → U-bend R 6.35 (≈ 30 × FPC thickness, dynamic-flex rated) → outer run on the rotating skirt (r 36.5) →
rotating anchor 35.9° ahead of the static one → up through the deck → torso PCB (JST-GH 4). Runs 95.7 mm + bend 20 →
**116 mm in the channel, ≈ 146 mm total**; at +170° the band spans 0…216°, at −170° −134…+10° (inner run ≥ 4 mm, outer
≥ 6 mm). The STS3215 is on the base side → its bus/power never cross J1.

**PAN – 10 conductors, ±85° + 20 mm lift**: head 4 (5 V, GND, TX, RX, Ø0.85 as B), tilt servo 3, lift servo 3, ultra-flex
silicone AWG30 (≥ 40 × 0.05 mm strands) in a PTFE sleeve. Path: neck bottom exits (x 13–15) → **U-slack loop for the lift
inside the cup** (x 11–17, z 72.7–80.3, 1.0 below the neck wire box at rest) → along the cup bottom to +y (y 13–16) and
across to x −16 → leaves the cup at r ≈ 22 on the −X side → **horizontal C-loop in a static PETG trough on the torso −X side**
(r 27.5–38.5, y ±21, z 72.5–81.5), ≈ 160 mm, bend radius ≥ 8 mm (strand strain ≈ 0.3 %) → clamp → torso PCB. The −X side is
free because the pan servo sits at +X. Arm cables: §1.

## 3. Electronics and power architecture
```
head ESP32-S3 + 3.5" (B) ──4 wires: 5V, GND, UART TX/RX 1 Mbit── torso ESP32-S3-Zero (25×18)
torso ESP32-S3-Zero ── PWM: lift MG90S, tilt MG90S, arm nano R/L ── I2S → MAX98357A → Ø28 8 Ω speaker
                    ── WS2812B chest bar ── half-duplex servo bus 1 Mbit (74LVC1G126 + 1 kΩ):
                         STS3032 pan (ID 2, torso) ──J1 FPC──► STS3215 J1 (ID 1, base) + base node (ID 20)
base PCBA (custom 36×22): STM32G030K8 + DRV8833PWP (2× N20 + encoders) + TPS563201 5 V/2 A + AP2112K 3.3 V
          ── VL53L1X ToF (I2C), 4× ITR8307 cliff IR, 6× WS2812B-2020 front bar, VBAT divider, charger status pin
power: 4×18650 as two 1S2P blocks (front/rear; series link + balance tap) → 2S BMS 8–10 A → AO4407A P-MOSFET
       (slide switch drives the gate only) → VBAT 6.0–8.4 V → STS3215 directly, DRV8833, base 5 V buck, J1 FPC → torso
       Pololu D36V28F5 5 V / 3.2 A (+470 µF at the servo connectors) → micro servos, STS3032, head, amp, LEDs, MCU
charge: USB-C (base back) → IP2326 2S boost charger (5 V 2–3 A in → ≈ 1.15 A @ 10 W, 1.75 A @ 15 W) → pack via the BMS
```
* Connectors: torso PCB JST-PH 3p × 4 (servos), JST-GH 4p head, JST-GH 4p J1 FPC, JST-PH 4p pan bus; base JST-GH (FPC,
  STS3215 VBAT/bus, N20 6p × 2, ToF, IR, LEDs), XT30 + JST-XH 3p (balance) on each pack lead (reachable in the hatch).
* **5 V rail (torso)**: idle 0.6 A, typical bursts 1.2 A, design peak 3.0 A (head 0.5, arms 0.7, pan 0.5, lift/tilt 0.7,
  amp 0.3, LEDs 0.15, MCU 0.1) – fine for the 3.2 A D36V28F5 only with firmware sequencing (no simultaneous stalls);
  base 5 V ≈ 0.1 A idle / 0.5 A peak.
* **Run while charging**: yes, in a low-power dock mode (≤ 3 W). The IP2326 has no power path: the load hangs on the pack and
  the charger supplies charge + load up to 10–15 W; the base node watches VBAT ≥ 8.35 V and sends the robot to sleep so the
  charger can terminate (no float at 4.2 V/cell). Phase-2 upgrade: a PD power-path charger (BQ25713 class).

| state | content | W at the pack |
|---|---|---|
| idle (awake, face on, Wi-Fi, no motion) | head 1.5, ear LEDs 0.1, torso MCU 0.15, servos holding 0.43 (STS3215 0.22), base node + ToF + IR + encoders 0.25, light bars 0.2, conversion 0.25 | **2.9** |
| typical (desk companion) | idle + servo motion 10 % (0.75), driving 5 % (0.11), speech 10 % (0.05), Wi-Fi/AI bursts (0.5) | **4.3** |
| peak (sequenced) | 5 V rail 15 W / 0.9 + STS3215 moving 11 + 2 × N20 4.4 + base 1 | **≈ 38 (5.1 A)** |

Runtime with 85 % usable: 4 × 3000 mAh (43.2 → 36.7 Wh): idle 12.7 h, **typical 8.5 h**; 4 × 3500 mAh (50.4 → 42.8 Wh): idle
14.8 h, **typical 10.0 h**. Charging ≈ 6.5 h (10 W adapter) / 4.5 h (15 W). Stall worst case (STS3215 2.7 A + N20 2 × 1.5 A +
5 V side) ≈ 8 A → BMS 8–10 A plus firmware current limits (STS3215 torque limit, motor PWM ≤ 70 %); 35E/MJ1 cells allow
8–10 A each.

## 4. Mass, CoG, tipping
| group | g | main items |
|---|---|---|
| base | **479** | packs 2 × 98, STS3215 55, shell 74 (resin 2 mm), N20 2 × 12, wheels 2 × 7, casters 4 × 4, 6806 outer 14, plinth 21, deck 22, cradles 12, PCBA/BMS/charger/ToF/IR/LED/wires ≈ 25 |
| torso | **149** | shell 61, deck 13, pan servo 20, hub/horn/skirt/inner ring 16, speaker 8, PCB + modules 16, gears/brackets/bosses/trough/cables ≈ 15 |
| pan stage | **39** | lift MG90S 13.4, well 8.9, collar disc 8.8, gear/plate/frame/crank/cables 8.3 |
| lift | **46** | neck + tilt servo 45 (B), tongue 1.2 |
| arms | **2 × 19.5** | shell 13.9, nano servo 4.5, cap + cable 1.1 |
| head | **165** | B |
| **total** | **918** | CoG (0.7, −1.0, 70.1) |

Support polygon: wheels (±56.5, 0) + casters (±46, ±30). Tipping (t1lib, 0.15 g in the worst direction): rest 22.5°
(29.0 / 18.5 mm), awake 20.8° (27.7 / 16.7), arms back + head up 18.3° (24.3 / 13.3), J1 90° + arms forward 21.8°,
**worst: arms forward 90–100° + lift 20 / tilt +40 → 17.4° (22.8 / 11.9 mm)**. The base carries 52 % of the mass with its own
CoG at ≈ z 22 – that is what keeps a 210 mm robot stable.

## 5. Assembly order, service access, hidden fasteners
**Base** (white pebble shell + dark bottom plate/foot; the plate carries everything):
1. Bottom plate: motor cradles + N20 + wheels, 4 casters, 4 IR boards, battery trays, J1 cradle (pillar + bridge over the
   left N20) + STS3215 (4 × M2), base PCBA over the right N20.
2. Deck on 4 posts (BMS, charger with USB-C at the back wall, slide switch). Plinth (drum + top plate + bearing seat, one black
   PETG part) dowelled to the deck posts, coaxial with the servo spline (jig on the horn). J1 FPC static end clipped to the
   seat, tail down to the PCBA.
3. White base shell lowered from above (plinth through the Ø76.6 top opening), **4 × M2.5 from below** into shell bosses.
4. Packs through **2 bottom hatches** (front/rear, 2 screws each, pull tabs; XT30 + balance plug inside the hatch).
**Torso** (main U-shell = front + sides + top, removable back panel – matches R01's panel seams):
5. Deck sub-assembly: deck + hub + skirt (one PETG part), 6806 pressed on the hub and clipped; bronze bush, idler pin,
   pan servo + bracket, speaker, chest bar, PCB + modules, pan trough, shoulder bosses; pan stage (cup + frame + lift MG90S
   + crank + well) dropped on the pivot with the PTFE washer.
6. Main shell slid on from the back (well top passes under the top wall, collar hole aligned), 4 screws from inside into the
   deck bosses. Neck from above into the well, tongue screwed under it through the back opening, collar disc + ring from
   above, head – all per B montaz. Back panel: **2 screws under the arms** (allowed).
7. Arms: spline into the shoulder boss, horn screw from inside (before the back panel).
8. Torso onto the base: hub/bearing into the plinth seat (snap hooks click), dog pins into the STS3215 horn, FPC tail plugged
   through the deck slot (via the back panel).
**Service**: battery → bottom hatches; USB-C + switch + charge LED → base back; arm servo → pull the arm (friction spline +
1 screw), paddle halves on magnets/clips; pan or lift servo → back panel, then head/neck out (B service) and the pan stage
off its pivot; J1 servo → release the snap hooks through the deck holes (J1 = 0), lift the torso, 3 screws of the plinth,
lift the servo out. **No screws on the front, sides or top.**

## 6. How much the soft shells constrain the internals
* **Base**: the superellipse corners bind. The pack rows reach 97 % of the n 2.4 interior at their outer corners; casters and
  cliff sensors only fit at (±46, ±30) / (±44, ±41); the packs must keep |y| ≥ 13.4 to pass the servo (|y| 12.35), which sets
  the depth 118. The bottom R10 roll costs ≈ 4 mm at the floor (packs modelled as real cylinders tuck into it). A flatter,
  more slab-like base (n ≥ 3) would give ≈ 6 mm back.
* **Torso**: the open bottom (r 38.8 for the Ø75 plinth) dictates ≥ 84 mm depth at the bottom; the R16 / n 2.35 corners keep
  the pan servo at x ≤ 40.2 / |y| ≤ 12 (torso ≥ 92 wide), the PCB at x ±20, the light bar at ±17. Above z ≈ 113 only the
  well sweep (r 28), the shoulder bosses and the arm cable loops remain, so the upper torso may taper towards the B head
  keep-out (flat r 30 + the B shoulder drop); `envelope.json` gives the exact minimum per 5 mm slice (hull + 1 mm).
* **Head keep-out**: the placeholder top (R16 + 1.5 mm raised plateau r 29.8) gives ≥ 0.46 mm to the real head over all B-table
  poses × pan ±85° (worst at the plateau edge – inherent to B).
* **Arms**: 21 mm paddles are possible only with a nano servo; an MG90S would need 27 mm.

## 7. Top risks
1. **Plinth + open-bottom torso**: the R01 dark ring becomes a Ø75 static drum; the torso lip height varies on a placeholder
   (z ≈ 44 at the sides, ≈ 51 front/back) – the exterior must design that edge deliberately.
2. **Base footprint +7 % and the servo stacked on a motor**: if the real N20 + encoder is longer than 34 mm it hits the J1
   pillar (2 mm margin) – measure before printing.
3. **Arm-up gestures are head-limited** (≈ 94° at rest, pan 0): the firmware table is mandatory; the user may expect "arms up".
4. **Nano arm servos** (nylon gears, 0.8 kg·cm): robustness relies on the friction collar; fallback MG90S → 27 mm arms.
5. **STS3032 data from retailer listings only**: confirm 360° position mode and the 28.5 mm height; pan backlash ±0.3°.
6. **Pan cable loop** (10 wires, frequent motion): needs ultra-flex wire and the trough; custom FPC is the fallback.
7. **5 V rail at 3.2 A and 5–8 A pack peaks**: firmware sequencing, 8–10 A BMS.
8. **J1 overrun protection is firmware-only** (direct drive): the ±170° FPC loop is the mechanical safety margin.

## 8. Súhrn (SK)
* K3 „J1 v podstavci“: servo STS3215 stojí priamo v osi otáčania trupu – priamy pohon bez ozubenia, ložisko 6806 nesie trup.
* Na jednu úroveň so 4 článkami 18650 a dvoma motormi N20 sa servo do nízkeho mäkkého podstavca nezmestí (zmestili by sa len
  3 články), preto stojí na mostíku nad ľavým motorom a jeho vrch zasahuje do tmavého sokla Ø75 pod trupom.
* Podstavec ostáva vysoký 40 mm (148 × 118, o 7 % väčší ako R01); mäkký „kamienok“ všetko pojme, ale jeho rohy sú plné.
* Trup 92 × 84 × 86 má otvorené dno nad soklom; celková výška 210 mm, hmotnosť 918 g, prevrátenie až pri náklone ≥ 17°.
* Otáčanie hlavy: STS3032 cez medzikoleso 2:1; zdvih krku: MG90S s kľukou (v krajných polohách mŕtve body); ramená: nano servá.
* Cez J1 idú len 4 vodiče (plochý FPC v otočnej slučke ±170°), cez otáčanie hlavy 10 vodičov v žľabe na ľavej strane trupu.
* Výdrž typicky 8,5–10 h, nabíjanie USB-C vzadu, batérie zospodu cez 2 krytky, žiadne skrutky spredu, zboku ani zhora.
* Obmedzenie: ruky nad ≈ 94° len pri zdvihnutej alebo otočenej hlave (tabuľka limitov vo firmvéri).

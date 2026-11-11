# T1 – NOVA mini variant B: TORSO + BASE, phase 1 (layout / packaging blockout)

## 0. LATEST USER FEEDBACK (overrides anything below)
"Nechcem také kockaté telo, ani podstavec, ani ruky – buď moderný, podobný obrázku, máš voľnú ruku, ale pôjdeme zase
postupne." → The user does NOT want a boxy torso, boxy base or boxy arms. Shapes must be MODERN and SOFT (smooth,
flowing, curvature-continuous surfaces, crowned faces, no flat slabs with small fillets, no visible steps), in the
spirit of R01 but with a free hand. We go STEP BY STEP: this round = (1) internal packaging that fits inside soft
shells and (2) several exterior FORM variants for the user to choose from. Detailed cutaways / phase-2 CAD come only
after the user picks. Consequence for packaging: a soft shell has little usable volume in its corners – keep the
internals compact and centred (assume the torso interior is a superellipse n ≈ 2.2–2.5 in plan, shrinking toward
the top and the bottom with ≥ 15 mm edge rounding; the base interior is a soft pebble/slab with tapered sides).

Phase 1 = decide WHERE everything goes and HOW each joint is driven, with simple envelopes at true part sizes,
proved by collision sweeps, CoG/tipping numbers, a power budget and renders. Detailed printable CAD is phase 2
(after the user approves). User language is Slovak – every text on an image and every user-facing file is Slovak
with diacritics; technical notes for other agents may be English.

## 1. User decisions (fixed)
* Wheels (differential drive) + 2 arms + **rotating torso J1 ±150°** driven by a **Feetech STS3215** bus servo.
* **Head pan ±80° in the neck** (the collar disc turns; the neck + head pan with it). Design for ±85° mechanical.
* Battery **4 × 18650 (2S2P, 7.4 V nom., ~43–50 Wh)** + **USB-C charging**; long runtime is the goal (> 8 h typical use).
* Torso size: "adapt the torso to the size of the whole robot" → follow the R01 proportions (section 4) with the
  finished head 110 × 79 × 66.
* The look is `ref/R01_celok_zadanie.png` (white satin shells, black joints, cyan light bars, dark plinth/foot).

## 2. What is finished and must NOT change: neck + head, variant B rev. E2
Files: `/tmp/claude-0/gapwf/fin/B/stl/*.stl` (rest pose, B frame), docs `B/montaz.txt`, `B/ZMENY_E2.md`,
`B_mechanism_review.md` (lift + pan recommendation – read §5a/§5b), `E2/E2_spec.md`. Images: `T1/ref/`.
B frame: x, y as world; **z_world = z_B + (Z_TT − 4)**, Z_TT = world z of the torso top (= collar disc top).
B-frame numbers (rest = neck retracted):
* torso top z 4; collar **disc** r 26.5, z −2…4, with a slot 45.5 × 20.5 for the neck – the disc is the TOP of the
  PAN stage (turns with pan, running seam 0.25 to the ring); collar **ring** r 26.75…28.25, z −2…4, glued in a torso
  recess r 28.35 (static, torso). The disc needs real support (bearing / PTFE) – it only "rested" on the recess floor
  in the illustrative torso.
* neck blade 45 × 20 (x ±22.5, y ±10, vertical edges R0.5), z −36.5…6.5 at rest, slides **20 mm** up (lift) inside a
  **well 47 × 22** (R1.5 corners) that belongs to the pan stage; neck bottom face z −36.5 rest / −16.5 extended.
* wires leave the neck bottom face: 4 head wires (Ø0.85, 5 V, GND, 2 signals – UART to the head) at x ≈ 13.8, y 0…2.4;
  3 tilt-servo wires AWG30 at x 13.2…14.6, y −6.7…−3.7. They move with lift (20 mm) and pan.
* hinge axis (tilt, X axis at y 0) z −3.5 rest / 16.5 extended; tilt ±40° allowed only per the lift table in montaz.txt
  (e.g. lift 12.5 → tilt −40…+30). Head shell x ±55 (ears ±58.8, z 33.5…59.5), y −33 (bezel front) … +33, z 7…86
  rest; the head bottom is 3 mm above the torso top at rest.
* masses: head ≈ 165 g (CoG ≈ (0, −8, 46) B frame), neck + tilt servo ≈ 45 g.
* Allowed: a NEW separate part attached under the neck bottom (z_B < −36.5, e.g. a foot / slider carrying the lift
  crank slot) and holes/inserts in the neck bottom face for it. Anything else on the neck/head = report as a
  proposal, do not assume it.

## 3. Coordinate system & tools
World mm, Z up, floor z = 0, origin = centre of the base on the floor, FRONT = −Y, robot RIGHT = −X. J1 and pan both
turn about the world Z axis through x = y = 0 (neck centred on the torso, torso centred on the base).
Library: `/tmp/claude-0/gapwf/fin/T1/t1lib.py` (read its docstring) – layout JSON → envelopes, poses (j1, pan, lift,
tilt, armR, armL), `clashes`, `sweep(STD_POSES)`, `gaps`, `cog`, `tipping`, `export`; the finished neck/head is added
automatically (B_* envelopes, groups P/T/L/H). Preview: `/opt/venv/bl/bin/python T1/t1_preview.py --dir <export>
--out <prefix> --real-head --views iso,front,side,cut --cut-names <shell names>` (≈10 s per view at 500 px / 12 spp;
4 CPU cores are shared by several agents – previews ≤ 600 px, ≤ 16 samples). Example layout: `T1/test/demo.json`.
build123d 0.13 in /opt/venv/cad; Blender 5.2 bpy in /opt/venv/bl (Cycles CPU only).

## 4. Target proportions (R01 scaled to the head width 110) – a GUIDE for size, not for the boxy look (see §0)
Measured on R01 (3/4 view, ±10 %): torso ≈ 0.83 × head width (≈ 91), torso height ≈ 1.1 × head height (≈ 87), torso
depth ≈ 75–80; base ≈ 1.25 × head width (≈ 138) × ≈ 110 deep × ≈ 36–40 high incl. a dark recessed foot; arms = paddles
≈ 30 wide × 18–22 thick × 75–85 long hanging from black shoulder caps (Ø 22–26) at ≈ 20 % of the torso height below
its top, outer arm faces ≈ ±67 (inside the base outline); torso sits on a dark plinth/gap ring on the base top; total
height at rest ≈ 205–215 mm. Torso plan: superellipse (n ≈ 2.6–3.2) with large vertical-edge rounding, top and bottom
edges rounded ~10–14; the torso top must be FLAT at least to r 30 around the collar (head tilt clearance was verified
with a flat plateau r 29.8 and a shoulder that drops ≥ 1.6 mm at |y| 32, ≥ 3.7 at 33, ≥ 12 at 35 – keep that or
re-check the head sweep). R01 details: torso front = separate front panel (vertical seams near the front corners),
cyan light bar ≈ 40 % of the torso width at ≈ 35 % below the top, a grey slot under it (= speaker grille or button);
base front: cyan light bar. Deviate (≤ ~10 %) only if packaging forces it, and report it.

## 5. Functions to package
TORSO (group T, turns with J1):
* J1 drive: STS3215 (body ≈ 45.2 × 24.7 × 35, 55 g, 25T spline; shaft ≈ 11–12 mm from one short end on the centre
  line – leave ±1 mm; serial bus 1 Mbps half-duplex, 6–8.4 V → runs straight from 2S). Torso yaw bearing (e.g.
  6806-2RS 30×42×7, 61806, 6808 40×52×7, or a thin-section / 4-point turntable) – the bearing, not the servo, carries
  the torso weight and tipping moments. The STS3215 position range is 360° (4096 steps) – a 1:1 gear or direct drive both
  work for ±150°; with gears check backlash and add hard stops at ±155°.
* PAN stage (group P): collar disc + well 47 × 22 + lift mechanism, ±85°. Actuator choice is yours (MG90S, SCS0009 /
  STS3032 bus servo, …), direct or geared; bearing/bushing choice yours. The well sweeps r ≈ 26–28 about Z – everything
  static must stay out of that cylinder over the well depth.
* LIFT (moves group L by 0…20 mm): recommendation = crank on an MG90S-class servo, r 10, pin in a slot across a neck
  foot, dead centres at both ends (B_mechanism_review §5a); the well is the linear guide. Neck + head ≈ 210 g, so
  ≈ 2.1 N at the crank pin. Alternatives allowed if better.
* ARMS (groups AR/AL): one actuator per arm, swing about the shoulder X axis; range at least −45° (back) … +180° (up)
  where geometry allows; the arms must never hit the head (ears at x ±58.8!), the base or each other in any pose –
  if full +180° is impossible, define the real limits. Options: micro servo inside the torso, or **servo inside the
  arm paddle** (shaft into the torso shoulder boss, case turns with the arm) – choose and justify.
* Torso controller (ESP32-C3 SuperMini 22.5×18 or ESP32-S3-Zero 25×18): UART to the head (the head ESP32-S3 is the
  brain), PWM for the micro servos, half-duplex bus for the STS3215 (+ bus servos), UART to the base node.
  5 V buck for servos + head (≥ 3 A peak, e.g. Pololu D36V28F5 17.8×17.8 or MP1584-class), 470 µF at the servo rail.
* Speaker Ø28 (8 Ω, 1–2 W) behind the grey slot on the torso front, I2S amp MAX98357A (17.8 × 19) – sound generated by
  the torso controller (the 4 head wires leave no pair for audio). Torso front light bar: WS2812B / SK6812 strip behind
  a light guide.
* Cable runs: head 4 + tilt servo 3 + lift servo 3 (+ pan servo if on the P side) across the PAN joint (±85° + 20 mm
  lift slack) – a service loop or clock-spring, defined path, no slip ring. J1 crossing: ≤ 6 conductors (VBAT 2×, GND,
  bus/UART…) as a rolling loop / flat cable in an annular channel – give the length and the path.
BASE (group B, static):
* 4 × 18650 (Ø18.6 × 65.2 bare cells; 47 g each), 2S2P spot-welded pack + 2S BMS with balance; pack must be
  replaceable from the bottom (cover with screws), no hot glue on cells.
* USB-C charging: 2S boost charger (IP2326-class module, 5 V 2 A in, ~1 A charge – ≈ 4–5 h) or a PD-based alternative;
  state whether the robot can run while charging (power path) – choose and justify. USB-C port + power switch on the
  base back (not visible in front views), charge LED visible.
* Drive: 2 × N20 gear motors with magnetic encoders (12 × 10 gearbox, total ≈ 34 mm + encoder ≈ 8 mm; 3 mm D shaft),
  wheels Ø30–34 × 8–10 with rubber tyres hidden mostly inside the base outline (R01 shows no wheels!), 1–2 ball casters
  (e.g. Pololu 3/8" ball, 10 mm tall); ground clearance ≥ 6 mm. Motor driver DRV8833 (18 × 16) + base node MCU
  (STM32G030 or a second ESP32-C3) talking to the torso over UART/bus.
* Sensors: front ToF (VL53L0X/VL53L1X module ~ 13 × 18) behind a dark window, 2–4 cliff IR sensors (TCRT5000 boards
  or ITR8307 parts) in the underside, base front light bar (WS2812B strip + light guide), optional underglow.
* J1 interface: hub/flange fixed to the base top carrying the yaw bearing / servo horn; base top ring visible as the
  dark plinth.
CHECKS everyone must report: static clashes = 0; `sweep(STD_POSES)` = 0 plus your own extra poses (pan ±85 with lift
0/20 and tilt per table, arms over their full ranges, J1 ±150 with arms forward/up); min clearances of moving parts
≥ 1.0 mm (≥ 2 mm for arm↔head/ears, arm↔base); CoG + tipping (`tipping(pose, accel_g=0.15)`) for rest and the worst
pose; total mass; power budget (idle, typical, peak) and runtime from 4 × 18650 at 3000 mAh / 3500 mAh with 85 %
usable; torque check of every actuator (holding + moving, with a ≥ 2× margin); assembly order and service access
(battery, USB-C, servo replacement) without visible screws on the front/sides/top.

## 6. Manufacturing assumptions
Exterior shells: resin MSLA (as the head) or FDM + filler/paint; walls ≥ 2.0 (shells), ≥ 1.6 (internal), seams
0.3–0.6, fillets on everything visible. Internal frames/brackets may be FDM (PETG). M2/M2.5/M3 screws into brass
heat-set or glued inserts; no visible screws on the top/front/sides (bottom and the back panel under the arms are ok).
Build volume to respect: 218 × 123 × 220 (Saturn 4 Ultra class) for resin parts.

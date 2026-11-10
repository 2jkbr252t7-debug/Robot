# NOVA mini – head/neck mechanism review (skeptical pass on variant B)

**Verdict: keep_B** – the pan collar disc + 20 mm pop-up neck + direct-drive MG90S tilt in the neck top is the right
kinematic family for this head. No alternative removes the fundamental problem (a 66 mm deep head tilting ±40° needs
17–22 mm of air under its bottom edge); the alternatives either show that air permanently, move it into a visible
track/dome, or put a hole in the head bottom. B is also the only option that *degrades gracefully*: if the lift is never
built, the same parts locked at full extension are the simplest fixed-neck robot ("variant C" below).
What must change is not the kinematics but (1) the lift actuator, which is still undesigned, (2) the operating policy
(the robot must not be stuck at 0° tilt most of the time) and (3) the surface quality of the neck/lugs, which is what the
user is actually complaining about ("schodíky, rozbité kusy").

## 1. What B is, and what the renders show

Geometry (world mm, rest frame, torso top plateau z = 4, r 29.8): head W108 × H77 × D66 (softhead, soft rim), head bottom
z = 7 at rest (3 mm gap), lifted to 27; hinge axis AXZ = 16.5 when lifted (10.5 mm *below* the head bottom, inside the
R10 neck knuckle); neck blade 45 × 20 sliding in a 47 × 22 well; collar disc Ø53 + ring, flush at z = 4; tilt servo in
the neck top, shaft on the axis, horn keyed into the −X lug cap, MR85 on a hollow pin on +X, wires through the pin.
Verified by checks.json r5: ±40° clearance 0.2 to the collar/torso at full lift, tilt-vs-lift interlock table, seams
≤ 0.5, no through-holes from 27 z-buffer viewpoints.

Renders closeB/01–08 vs R01: 01/02/03 (rest) look right – flush collar, no visible neck, glass almost full-face.
04/07 (lifted) are the weak spot: the neck reads as two boxy halves with a separate "pill" (knuckle cylinder) and sharp
35° saddle chamfers; the lug cylinders stand proud of the neck like glued-on parts. 08 (underside at tilt) shows the
rectangular lug boxes and the knuckle as a bolted-on sub-assembly. This is a *surface* problem (the knuckle/saddle/lug
transitions are built from boxes + cylinders with R2 corners), not a mechanism problem – see §5c.
Note also: R01 itself shows ~12 mm of black neck (≈0.11 × head width) – the reference is **not** flush. B is tighter
than the reference at rest and ~10 mm "taller" than the reference at full lift.

## 2. Quick geometry – where the head's lower front edge goes

Head bottom profile taken from softhead (bottom flat from y ≈ −24 to +3, front rim rises 4 mm at y = −33, back rounds
up 20 mm); torso top plateau r 29.8 then the 22 mm shoulder dome (drop 1.6 mm at |y| 32, 3.7 at 33, 12.3 at 35).
Tilt + = nod down. Pivot offsets are relative to the head bottom (+ below, − inside the head).

| pivot (rest frame) | head bottom | tilt | front-bottom edge → (y, z) | lowest head point z | min clearance |
|---|---|---|---|---|---|
| B lifted, z 16.5 (+10.5) | 27 | +40 | (−34.6, 6.4) | 5.7 | **+2.2** |
| same | 27 | −40 | (−15.9, 48.9) | 13.4 (back) | +9.4 |
| B axis at rest z −3.5, no lift | 7 | +40 | (−34.6, −13.6) | −14.3 | **−17.8** (crash) |
| low pivot in collar z 0 | 7 | ±40 | (−32.4, −12.8) | −13.5 / −5.8 | −17.5 / −9.8 |
| pivot at head bottom centre z 7 | 7 | ±40 | (−27.9, −11.1) | −11.9 / −4.2 | −15.9 / −8.2 |
| pivot 20 mm inside head z 27 | 7 | ±40 | (−15.0, −6.4) | −7.2 / 0.5 | −11.2 / −3.5 |
| pivot at head centre z 45.5 (−38.5) | 7 | +40 | (−3.1, −2.1) | −2.9 | −6.9 |
| pivot at front bottom edge (−28, 7) | 7 | −40 | – | −22.2 (back) | −26.2 |

Minimum lift (from the 3 mm rest gap) for ±40° with 0.5 mm clearance, as a function of pivot height:
pivot +10.5 (B) → 18.5 mm; +5 → 18.0; 0 → 16.5; −10 → 14.5; −20 → 12.0; −30 → 9.5; −38.5 (head centre) → 7.5;
−50 → 5.0. The drop is dominated by the head half-depth (33 sin 40° = 21.2 mm); raising the pivot buys only
0.23 mm per mm. B's 20 mm lift is within 1.5 mm of the minimum for its pivot – the lift is not oversized.
Only a pivot ≥ 90 mm above the bottom (above the head top) makes the front edge stationary – and then the head
translates 33 mm instead of nodding.

A pivot *inside* the head needs an opening in the head floor for the neck stem: half-length ≈ h·tan 40° + 10/cos 40°
→ h = 20: 30 mm each way = 60 mm long slot in a 66 mm deep floor, visible from below exactly in poses 05/08.

## 3. Alternatives considered

**A. Keep B** (pan disc, 20 mm pop-up, tilt servo in neck). Look: flush at rest, 23 mm black neck at full lift, no holes
(verified). Actuators 3 (pan, lift, tilt) – lift undesigned. Parts: 2 neck halves, 2 lugs, disc+ring, pin, MR85, horn,
+ lift crank/slider. Resin + hobby servo: proven in r5 (MG90S tolerance ±0.3 handled with foam, fits documented).
Noise: 2 servos moving in sequence (lift, then tilt) for a "look down"; the lift carries ~1.2 N. Cables: 4 wires via
hollow pin (pure twist), service loop of 20 mm in the torso – benign. Risk: resin well binding (1.0 clearance, 40 deep),
dust in the 0.25 slot, and the interlock makes the head rigid at rest (0° tilt) – mitigated by the policy in §5b.

**B. Fixed neck at full height ("C")** – B without the lift, neck fixed at z 0 (head bottom 27). Look: permanent 23 mm
black neck (R01 shows ~12). Actuators 2, parts −3, zero lift risk, cables static. Cheapest, most robust, quietest.
Loses the "wakes up / periscopes" feature and is visibly taller than R01. Natural fallback: same printed parts.

**C. Low pivot in the torso collar / ball-in-collar (tilting neck segment).** Whole neck+head rock about an axis at or
under the torso top; the collar becomes a black sphere segment sealing the Ø57 ring. Sphere through the ring with centre
z −10: R 31.8, dome 17.8 mm tall above the torso; the stem base swings 22 mm of arc (40°) and the ring sits 64° from the
pole, so 40° + 18° stem half-angle = 58° just seals. But the pivot is then 35 mm below the head bottom: at +40 the head
front edge moves to y −48, z −4 (in front of and below the torso top), mid-bottom points land on the torso rim → 0 mm
margin and a 33 mm forward lunge of the whole head. Also a big black dome where R01 has a thin collar. Rejected.

**D. Remote centre: cylindrical head bottom rocking on an arc track (virtual pivot at the head centre).** The only
kinematics with a *constant* envelope: if the head bottom is a cylinder about the tilt axis, no point ever drops, so the
3 mm gap stays at ±40° with no lift. Cost in numbers: R40 (axis at head centre) → the bottom rises 17.4 mm at |y| 33
(boat-shaped underside, visible in every side view – not R01); R55 → 11 mm rise but the head centre already translates
10.6 mm; arc travel 28–38 mm, so the guide track in the head is ≥ 50 mm long and its slot through the skin is covered by
the ~20 mm neck shoe only over 20 mm – 30+ mm of track slot is exposed at the extremes (exactly the "hole seen from
below" the user forbids). Needs curved rails or 4 rollers in resin (tolerance stack, rattle), a geared or cable drive
along the arc (no direct servo), and the pan disc under it. 3 actuators, ~2× parts, high novelty risk. Rejected.

**E. Pivot inside the head (gimbal / low head pivot, no lift).** Pivot 20 mm inside: still −11 mm at +40 (needs 14.5 mm
lift anyway) and a 60 mm floor slot. Pivot at the head centre: needs 7.5 mm lift *and* a full-length floor slot, and
the yoke must pass the display board (85.5 × 55.5 + 9 mm) – no room. Rejected.

**F. Head rocking on a curved neck top (cradle).** A concave head bottom on a convex neck dome has its pivot at the dome
centre, i.e. *below* the contact – identical to row "low pivot" (−17 mm). A convex rocker in a concave cradle is case D
with the track problem. Rejected.

**G. Cam-coupled lift (1 actuator for lift + tilt).** Tilt servo in the neck as now; the neck is pushed up by a cam
follower on the head lugs riding a fixed cam in the torso so that L(θ) ≈ 0.46·|θ| mm/deg. Saves the lift servo but the
tilt servo then lifts the head (0.9 N·cm at 10 mm, fine) through a sliding resin cam (friction, wear, stick-slip under a
90 g head), tilt and lift become inseparable (no "periscope", no independent sleep pose), and the cam needs ±1 mm
accuracy over 40 mm in resin. Clever, not robust. Rejected for a hobby build.

## 4. Scoring (1 bad … 5 good)

| criterion | A keep B | B fixed neck | C ball/low pivot | D remote centre | E head pivot | G cam lift |
|---|---|---|---|---|---|---|
| look at rest (gap, visible joints) | 5 | 3 (23 mm neck) | 2 (18 mm dome) | 3 (boat bottom) | 4 | 5 |
| look at ±40° (holes, gaps) | 4 | 4 | 2 | 1 (open track) | 1 (floor slot) | 4 |
| actuators | 3 (3) | 5 (2) | 4 | 3 | 4 | 4 (2) |
| parts count | 3 | 4 | 3 | 1 | 3 | 2 |
| resin + hobby servo buildability | 4 | 5 | 3 | 1 | 2 | 2 |
| noise / robustness | 3 | 5 | 4 | 2 | 3 | 2 |
| cable routing | 4 | 5 | 3 | 2 | 3 | 3 |
| cost | 3 | 5 | 4 | 2 | 4 | 4 |
| risk | 3 (lift undesigned) | 5 | 2 | 1 | 2 | 2 |
| **total** | **32** | **41** | 27 | 16 | 26 | 28 |

Honest reading: the fixed neck wins on engineering merit; B wins on the look the user chose (flush at rest, "wakes up")
and shares every printed part with the fixed neck. Since B ⊃ fixed neck, keep B and treat the lift as an add-on stage.

## 5. Recommendation: keep_B, with three amendments

**a) Design the lift now (it is the open risk).** Crank drive, not a rack: MG90S (or MG90S-class) on a horizontal X-axis
shaft in the torso at z ≈ −45, crank radius 10 mm (throw 20 mm, 180° sweep), 2 mm steel pin on the crank running in a
horizontal slot (20.2 × 2.2) across the neck foot; the 47 × 22 well remains the linear guide (add two 0.5 mm PTFE tape
strips on the long faces, or make the foot a separate POM/printed slider 46.5 × 21.5 with 0.25 clearance). Both end
positions are dead centres → zero holding torque, no servo buzz at rest or at full lift, sinusoidal soft start/stop,
~0.5 s for 20 mm. Load 1.2 N × 10 mm = 1.2 N·cm ≪ 22 N·cm stall. Hard stops: the collar disc (neck shoulder at z −20)
and the slot ends. Cables: 20 mm service loop clipped to the torso wall; servo lead down the neck as now.
Pan: the whole shaft/crank/well assembly sits on the pan turntable (the pan disc, neck and lift rotate together), so
the lift servo lead joins the pan slip loop – allow ±90° pan with a 120 mm loop; no slip ring needed.

**b) Operating policy (firmware).** Rest −20 = sleep/off only. Default awake pose −7.5 mm (12.5 mm neck visible – the
R01 proportion): tilt −40…+30 allowed per the r5 table, so nods and "look at the notebook" need no lift. Full lift only
for +40 (looking straight down at the desk). This removes the "robot cannot nod at rest" objection without changing
geometry; keep the step rule (more-retracted value wins) and never tilt below −17.5.

**c) Surface, not mechanism – what the renders actually need.** (i) Neck section: 45 × 20 with full R10 ends
(stadium), the knuckle cylinder tangent to the stadium walls, so no "pill on a box". (ii) Saddle: replace the 35° planar
land by a fillet/blend tangent to both the R10.5 saddle and the neck face (R ≥ 3), keeping wall ≥ 1.2 (check volume).
(iii) Lugs: not separate boxes – model each lug as a loft from the head floor pad to a Ø22 disc concentric with the
axis, filleted R3 into the floor, and extend the head floor's soft outline 2 mm below the lug tops so the lug roots are
in shadow from below. (iv) Keep the 0.5 seam only on the end faces (hidden by the lugs); the visible seam line is the
disc/ring 0.25 ring – fine. (v) Parting plane of the neck halves at y = 0 shows as a line at full lift (04): move the
split to the back face (front half = U-channel, back = lid) or add a 0.3 decorative groove so it reads as intended.
None of this changes AXZ, HZ, the servo pocket or the checks already passed in r5.

## 6. Residual risks of B after the amendments
Resin well straightness over 40 mm (print the well as a separate insert tube, glued), dust at the 0.25 slot (accept;
or a 0.5 mm felt lip under the disc), MG90S lift servo lifetime (the crank sees load only mid-stroke), and the lift
servo noise at wake-up (expected, part of the gesture). If the lift proves troublesome in the first build, lock the
crank at top dead centre → variant "fixed neck" with identical head/neck parts.

Súhrn (SK): mechanizmus B ponechať; žiadna alternatíva nerieši fakt, že 66 mm hlboká hlava potrebuje pri ±40° 17–22 mm
vzduchu pod spodnou hranou. Dorobiť zdvih (kľuka na MG90S, mŕtve body), zmeniť prevádzkovú polohu (−7.5 mm = kývanie bez
zdvihu) a vyhladiť krk/uši (stadión 45×20, tangentné sedlo, lofty namiesto kvádrov) – to je to, čo používateľ vidí ako
"schodíky a rozbité kusy".

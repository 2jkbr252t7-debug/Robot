# K2 – "servo dole + remeň / lanko" (arm servo low in the torso, belt or cord up to the shoulder)

Verdict: **NOT FEASIBLE** (left side misses for the SCS0009 even with every optimistic assumption; right side impossible
for any servo). Measured on the T4 torso as it is (voxel map 0.5 mm of `trup_servo/map1.npz`, clearances 0.3 static /
1.0 moving, pan −90.3…+90.3, lift 0…20) with the parts this concept may move treated as removable.

## Why it fails – the x-budget (scripts `xbudget.py`, `xbudget2.py`, image `img/k2_rozpocet_x.png`)
A belt or a Dyneema cord loop only connects **parallel** shafts (a quarter-twist needs ≈ 4–6° fleet angles over the
≈ 50 mm span – not reliable for a toothed belt, marginal for a cord, so rejected). The servo shaft must therefore be
parallel to X and both pulleys must lie in the **same plane x = const**.

1. **Shoulder end** (`xbudget.py` A): a pulley disc about (y 3, z −17) must clear the side-cap wall (true 2.2 offset of the
   approved outer surface) by 0.5. Outer face of the pulley plane xb1 ≤ 42.93 (flange r 5 = 12T GT2), 42.37 (r 7),
   42.04 (r 8). With the wall locally thinned to 1.2: +1.0 mm. Inner limit at the shoulder: pan/lift sweep r 33.4 + 1.0
   → x 34.4 (only 10.1 mm free on the axis up to the wall at x 44.52, `direct.py`).
2. **Servo end**: case [x_face − H, x_face], x_face = xb1 − w − 0.3 (w = pulley width: cord drum 3.0, GT2 3 mm + flanges
   4.6, GT2 6 mm 7.6). Low in the torso the J1 servo (STS3215, case to x 15.7, PORON + bumper post to x 18.3 for |y| ≤ 4,
   plug reservation x ≤ 27, |y| ≤ 8, z −66.3…−48.3, cradle walls |y| 12.55…15.05 to x 25.8) and the stop-pin-1 rib
   (y ≥ 8.9) bound how far inboard the case may start.
3. Largest case depth that fits anywhere below the deck (`xbudget2.json`, both orientations of 23.2 × 12.1):

| side | map variant | best pulley option | H_max | SCS0009 needs |
|---|---|---|---|---|
| left | as reserved (J1 plug zone as is, servo before T_stred) | Dyneema drum, r 5 | **11.6** | 21.5 … 25.25 |
| left | optimistic (J1 plug zone cut to z ≥ −57.3, bumper post thinned to a 1.2 wall, servo fitted after T_stred, from the side) | GT2 3 mm, 12T (r 5) | **19.5** | 21.5 … 25.25 |
| left | optimistic + cap wall thinned to 1.2 at the pulley | GT2 3 mm, 12T | ≈ 20.5 | 21.5 … 25.25 |
| right | any | any | **≤ 6.6** (SCS0009) / ≤ 14.1 (KST X06) | J1 case + end wall reach x −32.2 |

   Left misses by ≥ 2.0 mm (case 21.5, unverified) to 5.7 mm (case 25.25) in the most optimistic stack, by ≈ 10 mm with
   the J1 plug zone as reserved. Right side: the J1 servo occupies x −29.5…15.7 (end wall −32.2) over the whole lower
   torso, so no servo with its shaft along X can sit inboard of the right belt plane; the front/back corners are taken by
   stop pin 2, the F1 bosses / T_stred lowering path, the pan servo and the carrier.
4. Only a wing servo (KST X06, 16.6 along the shaft) would fit on the LEFT (H_max 19.0…20.6), but it has 120° travel,
   PWM without feedback, and there is still no place on the right → not a solution.

## Why not a direct drive (user question)
On the shoulder axis there are **10.1 mm** between the pan/lift sweep (+1.0 clearance, x 34.4) and the inner face of the
side-cap wall (x 44.52). The SCS0009 is ≥ 21.5 mm long along its shaft (+3.75 spline), so its output face would be at
x 55.9: **9.1 mm out of the torso surface** (x 46.76); MG90S 10.3, STS3032 10.6, even the KST X06 4.2 (`direct.json`).
The user rejected a servo sticking out, so a direct drive inside the torso is not possible.

## What K2 would have been (for comparison only)
* SCS0009 lying next to the J1 servo +X end, shaft +X at (38.0, −2.25, −75.45), case x 16.5…38.0 × y −8.3…3.8 ×
  z −81.4…−58.2 (23.2 along Z) – would overlap the J1 bumper wall by 2.0 and the reserved J1 plug zone by 8.2 in z (z −66.3…−58.2).
* Closed GT2 belt 3 mm, 12T / 12T (1:1), C ≈ 58.7, L ≈ 141.4 (stock 140 / 142 + slotted servo seat ±1), belt plane
  x 38.3…42.9 through a hollow column (box closure, head flanges and amplifier moved).
* Shoulder: Ø5 steel shaft, MR105ZZ in the column boss, 12T pulley, outer MR105 in the side-cap wall boss (cap would
  carry arm loads), slip clutch 0.12 N·m in the arm hub, hidden stop pin on the arm hub for load-based homing.
* Advantages it would have had: static servo cable (≈ 80 mm to J_BUS_5), quiet belt, thin black ring only.
* Weak points even if it fitted: 12T pulley is below the usual GT2 minimum (belt fatigue, tooth skip at the 0.12 N·m
  clutch = 31 N tension difference on a 3 mm belt), outer bearing in the removable side cap, a window through the
  shoulder column next to the J1 servo, the J1 plug zone squeezed, right arm impossible.

## Arm gap (common to all in-torso servo concepts, `armgap.py` → `armgap.json`)
Passive arm pebble (armgeo.to_world, dx < 0 = toward the torso) vs the approved torso exterior with a CLOSED side-cap
surface around the shaft (only a flush thin ring, no protruding joint). Arm inner skin on the axis x 50.64 at dx 0
(surface 46.76 → 3.88 on the axis).
| dx | gap at rest | min gap −45…+135 | where |
|---|---|---|---|
| 0.0 | 3.78 | 1.45 at +135 | arm skin near (49.9, 5.7, −27.2), 10.5 from the axis |
| −0.5 | 3.29 | 0.96 at +135 | |
| −1.0 | 2.80 | 0.47 at +135 (≥ 1.0 only up to +115) | |
| −2.0 | 1.82 | −0.52 (≥ 1.0 only up to +80) | |
| −3.0 | 0.84 | −1.49 | |
Recommendation (any concept with a passive arm): dx −0.45 → gap 3.3 at rest, 1.0 at +135; or dx −1.0 with the range
limited to −45…+115 (gap 2.8 at rest, 1.0 at +115). The old figures 4.67 / 1.90 were measured to the T_bok_L mesh,
which has the r 14 socket hole; with the hole closed the critical point (r 10.5 from the axis) is real surface.

## Files
xbudget.py / xbudget.json (A: shoulder pulley limit, first B pass), xbudget2.py / xbudget2.json / .log (H_max per side,
variant, pulley, servo), direct.py / direct.json (direct-drive numbers), armgap.py / armgap.json (arm gap vs dx),
hardmap.py / hard.npz (map with removable parts deleted), hslice.py + d2/ (diagnostic slices),
obr_rozpocet.py → img/k2_rozpocet_x.png (Slovak evidence image).

## Zhrnutie (SK)
Koncept K2 (servo dole v trupe a remeň alebo lanko hore k ramenu) sa nedá postaviť. Remeň spája len rovnobežné
hriadele, takže servo musí ležať s hriadeľom v osi X a jeho remenica v tej istej rovine ako remenica ramena. Pri ramene
je medzi otáčaním hlavy a stenou krytu len 10,1 mm, takže rovina remeňa končí najďalej na x 42,9 a telo serva by
muselo siahať až po x 16,5 – tam je servo J1. Vľavo je miesto najviac pre 19,5 mm telo (SCS0009 má 21,5 až 25,25),
vpravo len 6,6 mm. Priamy pohon nejde z rovnakého dôvodu: servo by z trupu trčalo 9,1 mm.

"""
NOVA mini v8.2 - TORSO + NECK + ARMS (manifest "torso").   "MODERNÝ - NIČ NEVIDNO", proportions "B+"
Run from the repo root:   /opt/venv/cad/bin/python -m nova_v8.cad_torso [--check [--others] [--motion]]
Exports STEP (first) + STL + manifest into build_v8/ (never build/, which holds the finished v7.3).

Numbers: nova_v8/spec.py (TORSO incl. chest_strip, NECK, ARM, MICRO_SERVO, BASE.yaw_hub).  Every dimension that
follows the body is derived from the spec (no literal z / x / y of the shell, the neck or the arms in this file).

v8.2 "B+" (spec v8.2 block; the v8.1 design below is kept feature-for-feature, only the proportions change)
  * Torso 88 x 72 x 65 -> 94 x 76 x 82 (superellipse n2.7, z 36..118, R17 top / R8 bottom); shoulder / arm axis
    z 98 (bore Ø18), chest strip 36 x 5 at z 92, turntable T04 Ø82 on the 6806 seated on the base hub top z 35,
    STS3215 body z 41..76.
  * The bottom stack (T04, 6806 housing, T08 cradle, STS3215, controller slot, magnets) follows the base top /
    TORSO.z0; the top stack (6805, pan gears N03/N04, pan servo + horn, frame T07 housing/plate, collar, cone,
    barrel) follows TORSO.z1 / NECK; the arm servos, their tab blocks, the frame wings and the shoulder rings
    follow the shoulder axis; shell-hugging items (front board E25, T02 magnets, T01 bottom screws, nail recess,
    frame ears) follow TORSO.w / d.
  * Arms +20 % (spec ARM egg 110 / 76.4 / 48.8, half 15.6 x 8.4, mid_x 64, splay 8 deg): tip, hub and coupler
    scale with the egg; shoulder ring A05 Ø24/Ø18 (spec bore 18, ring width 3 kept), coupler A04 Ø16.6 (0.7 radial
    gap in the ring kept).  Neck: collar N01 45 x 36 (z 118..123), cone z 123..130, barrel Ø30 x 30 on y 0 / z 140.

v8.1 design (review of the v8.0 build + v8.1b review of the first v8.1 pass -> DEVIATIONS, printed on every run)
  * ONE PARTING LINE on the plane y = 0 (front/back clamshell) instead of the v8.0 band + 2 side shells: the line
    is aligned with the shoulder axis and the head tilt axis; on the flanks it runs straight through the shoulder,
    hidden behind the arm, and across the top it disappears under the collar.  THE FRONT HAS NO SEAM AT ALL - only
    the smoked chest strip.  0.5 seam, outer edges R0.25, closed from behind by a ledge of T01 (no light, no
    see-through), ledge depth 2.05 -> reads as a fine shadow line.
  * THE BACK HAS NO SEAM EITHER (v8.1b): the whole rear half shell T02 is the tool-free service cover - no separate
    door, no U outline.  Held by 2 top snap tongues under the T01 top wall, a tongue-and-groove along the flank seam
    (T01 ledge running in a T02 channel -> no step, no gap, T02 cannot spring out) and 2 hidden Ø5 N52 magnet pairs
    into T04.  Opening: fingernail into the black T04 recess under the rear bottom edge (black on black, in the
    shadow line), slide T02 back (tongues free after 6.5 mm) 19 mm until its top wall clears the collar, lift off
    -> controller, USB-C, servos all accessible.  No screws.  (v8.1 said "6.5 mm, lift" - blocked by the collar.)
  * Chest: ONE smoked dead-front strip (spec chest_strip) flush with the surface: 5x WS2812B-2020 light bar
    + VL53L0X ToF + ambient light sensor behind the same dark window (IR-transmissive smoked PMMA, invisible off).
  * No screws visible anywhere: T01 + T08 -> T04 with countersunk M2 from below (heads 0.2 sunk, T04 underside faces
    the base, 1 mm gap), arm screws inside the arm, neck screws inside the cone bore (covered by the head).
  * No vents on the skin: 7 slots in T04 (torso underside) exchange air with the base cavity (heat < 1 W).
  * Torso bottom T04 carries the 6806 outer race (housing OD45, bore 42, 7.5 below the hub top, shoulder ID38.6 on
    the outer ring only) and the STS3215 cradle T08 (3x M2 into T04; spline DOWN on the yaw axis, horn E21H on the
    base hub; axial retention = M3 from below into the spline, base module).

Kinematics / joint tags
  J1  torso: T01 T02 T04 T05 T06, N01 collar, A05 rings, all torso internals (T07 T08 T09 E21..E25 M21..M23 N04)
  J2  pan stage:  N02 cone + spigot, N06 barrel, N03 hub gear
  J4/J5  arms:  A01..A04 (-R on -X = J4, -L on +X = J5) + arm servo horns E22H
  ""  E21H yaw-servo horn (bolted to the hub fixed in the base)

Visible parts
  T01  front shell (y <= -0.25): shoulder-ring seats (front halves), chest-window opening, inner: seam ledge
       (sides + top, reaches 2.5 mm behind T02), 2 tab blocks for the arm-servo FAR tabs, 4 bosses for the frame
       T07 (M2 from below), 3 bottom bosses (M2 from below through T04), 2 bosses for the front board E25,
       2 collar pin holes (y -7, off the seam), 2 grooves for the T02 snap tongues.
  T02  rear shell = service cover (y >= +0.25): shoulder-ring seats (rear halves), 2 top snap tongues under the T01
       top wall, channel for the T01 ledge on the flanks, 2 magnet bosses (Ø5x2 N52) at the bottom.
  T04  black turntable plate (spec ring_od) x 2.5 + 6806 housing (interface with the base B15/B09), 6x M2
       countersunk from below, cable arc slot, 7 vent slots, 2 magnet pockets + nail recess for T02.
  T05  smoked dead-front window (chest strip - 0.2) flush, 0.8 flange behind the wall (smoked PC / PMMA).
  T06  RENDER-ONLY: the cyan light bar glowing through T05 (0.15 mm skin in front of the window face).
  N01  black collar (spec NECK.collar), drafted 22 deg, bore Ø26.9 (0.45 gap to the cone), 2 pins into T01 +
       VHB on T01 only; underside relieved 0.2 over T02 (T02 slides out under it without rubbing).
  N02  black cone r13 -> r10 + spigot in the 6805 (unchanged interface).   N06  black barrel Ø30 x 30 (interface for
       the head modules unchanged: end walls 3.5, cross-horn recess 1.8, Ø3.2 pivot, 2 pilots y +-7.5; the v8.0
       decorative grooves removed - not a real split).
  A01  white outer arm shell (local x >= +0.25).  A02 white inner shell + snap lip + hub (clipped inside the egg).
       A03 black TPU tip (inner-front-bottom).  A04 black joint coupler (trimmed servo horn inside).  A05 black
       shoulder ring, 0.7 proud.  No painted-on "lens panel" groove on A01 (fake seam).
Internals (internal=True)
  T07  frame (PETG): 6805 housing + plate, pan-servo rails, side wings over the arm servos with the NEAR-tab
       blocks; 4 ears screwed into T01 (the rear shell carries nothing -> removable).
  T08  STS3215 cradle on T04 (3x M2 from below).  T09 hold-down strap.  N03 / N04 1:1 pan gears 20T m1.  M21 6806,
  M22  6805.  M23 4 Ø5 N52 magnets (T02 latch).  E21 STS3215 (spline down), E21H its horn.  E22 arm micro servos +
  E22H horns.  E23 pan micro servo + E23H.  E24 controller ESP32-C3 SuperMini + MP1584 5 V + bus driver (spec v8.1
  review 2; behind T02).  E25 front board: 5x WS2812B-2020 + VL53L0X + ALS behind T05.   (cad_internals.py holds the
  detailed versions of the bought parts E21..E25/M21/M22 -> render with "exclude" = its SUPERSEDED list.)
"""
from __future__ import annotations

import math
import os
import sys
import time

from build123d import (Align, Axis, Box, Cone, Cylinder, Edge, Face, Plane, Pos, Rot, Sphere, Vector, Wire,
                       extrude, fillet, mirror, offset, revolve, scale)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from nova.cad.common import PartRec, export_parts, superellipse_wire  # noqa: E402
from nova_v8 import spec as S  # noqa: E402

OUT_DIR = os.path.join(ROOT, "build_v8")
MANIFEST = "torso"
BIG = 400.0

# ============================================================================================
# shared numbers (spec)            values in the comments: v8.2 (v8.1 in brackets where it changed)
# ============================================================================================
TS, NK, AR, MS, BS = S.TORSO, S.NECK, S.ARM, S.MICRO_SERVO, S.BASE
TA, TB, TN = TS["w"] / 2, TS["d"] / 2, TS["n"]            # 47, 38, 2.7          (44, 36)
T_Z0, T_Z1 = TS["z0"], TS["z1"]                            # 36, 118              (40, 105)
R_TOP, R_BOT = TS["r_top"], TS["r_bottom"]                 # 17, 8                (16)
WALL = TS["wall"]                                          # 2.0
CH = TS["chest_strip"]                                     # 36 x 5 at z 92       (34 x 5 at z 84)
SH = TS["shoulder"]                                        # z 98, bore 18        (89, 16)
T04_H, RING_OD = TS["bottom_plate"]["h"], TS["bottom_plate"]["ring_od"]   # 2.5, 82 (77)
Z_SH = T_Z0 + T04_H                                        # 38.5 white shells stand on T04 (42.5)
YS = TS["yaw_servo"]
YS_L, YS_W, YS_H = YS["body"]                              # 45.2, 24.7, 35
YS_Z0, YS_Z1 = YS["z_body"]                                # 41, 76               (45, 80)
YAW_BRG = BS["yaw_hub"]["bearing"]                         # 30/42 x 7
YAW_BRG_Z1 = BS["yaw_hub"]["z_top"]                        # 35 = base top        (39)
CO, CN = NK["collar"], NK["cone"]                          # collar 45 x 36 z 118..123, cone z 123..130
PAN_BRG = NK["pan_bearing"]                                # 25/37 x 7
TLY, TLZ = NK["tilt_axis"]["y"], NK["tilt_axis"]["z"]      # 0, 140               (127)
BAR_R, BAR_L = NK["barrel_d"] / 2, NK["barrel_len"]        # 15, 30
EGG = AR["egg"]                                            # 110 / 76.4 / 48.8, 15.6 x 8.4 (99 / 71 / 48, 13 x 7)
AX_Y, AX_Z = AR["axis"]["y"], AR["axis"]["z"]              # 0, 98                (89)
MID, SPLAY = AR["mid_x"], AR["abduction_deg"]              # 64, 8                (58)
assert abs(SH["z"] - AX_Z) < 1e-9
assert abs(CO["z0"] - T_Z1) < 1e-9 and abs(CN["z0"] - CO["z1"]) < 1e-9
assert abs(T_Z0 - YAW_BRG_Z1 - 1.0) < 1e-9                 # 1 mm dark gap between T04 and the base top
assert abs(YS_Z0 - YAW_BRG_Z1 - 6.0) < 1e-9                # horn stack: hub top -> STS3215 output face

# ============================================================================================
# local design constants
# ============================================================================================
SEAM = 0.5                 # v8.1: 0.4-0.6 (spec band seam 0.6 is v8.0)
HS = SEAM / 2
SEAM_R = 0.25              # outer seam edge radius
LEDGE_D = WALL + 0.05      # ledge face depth behind the seam

# --- micro servo (MG90S class) catalogue envelope -----------------------------------------------
MS_L, MS_W, MS_H = 22.8, MS["body"][1], MS["body"][2]      # 22.8 x 12.2 x 22.7 (case incl. tab level)
MS_SHAFT_END = 5.9         # shaft centre from the near end of the case
MS_TABS = MS["tabs_len"]   # 32.5
MS_TAB_Z = (15.9, 18.4)    # tab underside / top above the case bottom
MS_TAB_HOLE = 2.45         # hole centre from the tab end
MS_DOME_R, MS_DOME_H = 5.9, 3.0
MS_SPL_R, MS_SPL_H = 2.4, MS["height_with_spline"] - MS_H - MS_DOME_H     # 2.8
HOLE_FAR = MS_L - MS_SHAFT_END + MS_TAB_HOLE                # 19.35 from the shaft
HOLE_NEAR = MS_SHAFT_END + MS_TAB_HOLE                      # 8.35

# --- STS3215 ----------------------------------------------------------------------------------
YS_SHAFT_END = YS_W / 2    # output axis assumed centred in the square end (catalogue drawing not available)
YS_X0, YS_X1 = -YS_SHAFT_END, YS_L - YS_SHAFT_END          # -12.35 .. +32.85 (body toward robot LEFT, +X)
YS_HW = YS_W / 2

# --- shoulder ring / coupler (spec bore; ring width 3 and the 0.7 radial coupler gap of v8.1 kept) -----------
A05_RI = SH["bore_d"] / 2                                  # 9      (8)
A05_RO = A05_RI + 3.0                                      # 12     (11)  ring Ø24 / Ø18
A05_X0, A05_X1 = TA - 4.0, TA + 0.7                        # 43 .. 47.7 (0.7 proud of the flank)
A04_R = A05_RI - 0.7                                       # 8.3    (7.3) coupler Ø16.6
SH_BOSS_R = A05_RO + 2.5                                   # 14.5   (13.5) shell boss around the ring seat

# --- arm servo placement (on the spec shoulder axis, spline tip 1 mm inside the flank) ---------------
ARM_SPL_X = TA - 1.0                                       # spline tip |x| 46 (43)
ARM_TOP_X = ARM_SPL_X - MS_SPL_H - MS_DOME_H               # case top |x| 40.2 (37.2)
ARM_BOT_X = ARM_TOP_X - MS_H                               # case bottom |x| 17.5 (14.5)
ARM_TAB_X0, ARM_TAB_X1 = ARM_BOT_X + MS_TAB_Z[0], ARM_BOT_X + MS_TAB_Z[1]   # 33.4 .. 35.9
ARM_CASE_Z1 = AX_Z + MS_W / 2                              # case top face in Z (case width 12.2 lies along Z) 104.1
TAB_BLK_X = ARM_TAB_X1 + 0.05
FAR_BLK_X1 = TA - 2.5                                      # T01 far-tab block outer end |x| 44.5 (41.5)
FAR_BLK_Y = (-(HOLE_FAR + 3.65), -(MS_L - MS_SHAFT_END) - 0.2)    # -23.0 .. -17.1  (T01)
NEAR_BLK_Y = (MS_SHAFT_END + 0.2, HOLE_NEAR + 4.15)               # 6.1 .. 12.5     (T07)
NEAR_BLK_X1 = A05_X0 - 1.0 - 0.4                           # 41.6: 0.4 clear of the shoulder boss (38.6)

# --- pan drive: 1:1 spur gears 20T m1 (centre distance 20); the whole stack hangs from the torso top wall ----
G_Z, G_M = 20, 1.0
G_CD = G_Z * G_M
PB_Z1 = T_Z1 - WALL                                        # 6805 top = top-wall underside 116 (103)
PB_Z0 = PB_Z1 - PAN_BRG[2]                                 # 109 (96)
PB_RI, PB_RO = PAN_BRG[0] / 2, PAN_BRG[1] / 2              # 12.5, 18.5
G_Z1 = PB_Z0 - 1.5                                         # gear faces z 103.5..107.5 (90.5..94.5)
G_Z0 = G_Z1 - 4.0
PAN_SERVO_Y = G_CD
PAN_HORN_Z0, PAN_HORN_Z1 = G_Z0 - 1.5, G_Z0 + 1.6          # 102.0 .. 105.1 (89.0 .. 92.1)
PAN_SPL_TOP = G_Z0 + 1.1                                   # 104.6 (91.6)
PAN_TOP_Z = PAN_SPL_TOP - MS_SPL_H - MS_DOME_H             # case top 98.8 (85.8)
PAN_BOT_Z = PAN_TOP_Z - MS_H                               # 76.1 (63.1)
PAN_TAB_Z0, PAN_TAB_Z1 = PAN_BOT_Z + MS_TAB_Z[0], PAN_BOT_Z + MS_TAB_Z[1]   # 92.0 .. 94.5

# --- T07 frame -----------------------------------------------------------------------------------
T07_HOUSE_Z0 = G_Z1 + 0.8  # underside of the 6805 housing / rear plate, 0.8 over the gears 108.3 (95.3)
WING_Z0 = ARM_CASE_Z1 + 0.2   # underside of the wings, 0.2 over the arm-servo cases 104.3 (v8.1: = 95.3 as well)
T07_LIP_RI = 17.0
T07_HOUSE_RO = 20.5
T07_EARS = [(-20.0, -21.0), (20.0, -21.0), (-(TA - 10.0), -8.0), (TA - 10.0, -8.0)]   # all into T01 (side +-37)
T07_PLATE_Z = (PB_Z0, PB_Z0 + 3.0)                         # 109 .. 112 (96 .. 99)
RAIL_Y = (13.0, 28.5)
RAIL_L, RAIL_R = (-13.5, -6.2), (17.2, 24.0)

# --- T04 / T08 ----------------------------------------------------------------------------------
YH_RO = 22.5                                               # 6806 housing OD45
YH_Z0 = YAW_BRG_Z1 - YAW_BRG[2] - 0.5                      # housing bottom 27.5 (31.5)
YH_BORE_R = YAW_BRG[1] / 2                                 # 21
YH_SHOULDER_R = 19.3       # v8.1b: ID 38.6 bears on the 6806 OUTER ring only (v8.0 ID 36 rubbed on the 2RS seals)
CABLE_SLOT = dict(r0=23.0, r1=29.0, a0=155.0, a1=205.0)
POST_A, POST_B = (-17.5, 0.0, 2.5), (35.2, 0.0, 2.2)       # strap posts (x, y, r)
# T01 -> T04 screws: front one 5.5 inside the shell front, the two side ones on a circle 2.7 inside the T04 rim
# (same margin as v8.1: r 35.8 on the Ø77 disc) at the v8.1 angle -30 deg
T01_SCREW_R = RING_OD / 2 - 2.7                            # 38.3
T01_SCREWS = [(0.0, -(TB - 5.5))] + [(sx * T01_SCREW_R * math.cos(math.radians(30.0)),
                                      -T01_SCREW_R * math.sin(math.radians(30.0))) for sx in (1, -1)]
# T08 -> T04 screws: only where T04 is a flat 2.5 plate (r 24.7 .. 38.3: outside the housing OD45, inside the disc).
# v8.0 screwed POST_A (-17.5, 0) "from below" - that point lies in the T04 centre hole -> the screw held nothing.
T08_SCREWS = [(POST_B[0], POST_B[1]), (-19.0, -16.5), (-25.0, 21.0)]
T04_SCREWS = T01_SCREWS + T08_SCREWS                       # 6x M2 countersunk from below (T02 has none any more)
CSK_SINK = 0.2                                             # screw heads 0.2 below the T04 underside (B09 rim slides)
VENT_A = (240.0, 252.0, 288.0, 300.0, 82.0, 90.0, 98.0)
VENT_R = (25.5, 30.0)
VENT_W = 1.8
T08_Z1 = Z_SH + 1.5
T08_HOLE_R = 12.0
CRADLE_Z1 = YS_Z0 + 15.0                                   # anti-torque walls up to 56 (60)
CR_T = 1.6
PCB = dict(x=24.0, y0=18.0, t=1.6, z0=Z_SH + 1.7, z1=Z_SH + 1.7 + 18.5)   # z 40.2 .. 58.7 (44.2 .. 62.7)
STRAP_Z = (YS_Z1, YS_Z1 + 2.5)

# --- rear cover T02 = the service door (v8.1b) --------------------------------------------------------
# The whole rear half shell is the tool-free service cover: 2 top snap tongues under the T01 top wall, a tongue-
# and-groove along the flank seam (T01 ledge in a T02 channel), 2 magnet pairs into T04 at the bottom.  Opening:
# fingernail into the black T04 recess under the rear bottom edge, slide T02 19 mm back, lift off (see SLIDE).
MAG_XY = [(-12.0, TB - 6.1), (12.0, TB - 6.1)]             # T02 latch magnets y 31.9 (29.9), clear of E24 / IT08
MAG_D, MAG_T_T02, MAG_T_T04 = 5.0, 2.0, 1.5                # Ø5x2 N52 in T02, Ø5x1.5 N52 in T04
MAG_BOSS_R = 3.3
NAIL_W, NAIL_D = 12.0, 1.0                                 # recess in T04 under the T02 bottom edge (black, hidden)
NAIL_Y = (TB - 5.0, TB + 9.0)                              # 33 .. 47 (31 .. 45)
TONGUE_X = (-(TA - 18.0), TA - 18.0)                       # T02 snap tongues under the T01 top wall +-29 (+-26)
TOP_ZONE_Z = T_Z1 - 15.0                                   # tongues / grooves live above this z 103 (90)
TONGUE_RELEASE = 6.5                                       # the snap tongues leave the T01 top wall after 6.5
# v8.2 review: T02 removal stroke.  After only 6.5 mm (v8.1 text) the T02 top wall is still under the collar N01
# (to y 18) and its shoulder seats still wrap the A05 rings (to y 12) -> lifting collided (CAD).  The pure +Y slide
# is free (the shell widens towards the front, so its flanks move away from the internals), so T02 slides back
# until the top wall clears the collar, then lifts off.
SLIDE = max(TONGUE_RELEASE, A05_RO + 0.5, CO["d"] / 2 + 1.0)   # 19 (collar rear edge 18 + 1)
CHAN_RIB = (3.5, 4.3)                                      # T02 channel rib offsets (T01 ledge 2.05..3.4)
CHAN_VOID = (1.95, 3.5)
CHAN_Y1 = 3.6                                              # channel closed at y 2.65..3.6 (ledge ends at 2.5)
CHAN_Z0 = T_Z0 + R_BOT + 0.5                               # vertical wall only (above the R8 bottom fillet) 44.5

# --- front board ----------------------------------------------------------------------------------
E25 = dict(x=CH["w"] / 2 + 6.0, z0=CH["z"] - 7.0, z1=CH["z"] + 7.0, y0=-(TB - 5.2), t=1.6,
           boss=(CH["w"] / 2 + 4.0, CH["z"]))              # 48 x 14 at y -32.8, z 85..99 (46 x 14, y -30.8, z 77..91)
GLOW = dict(w=24.0, h=1.6)                                 # light bar of the 5 LEDs (x +-12: ToF/ALS at +-14.5 stay dark)

# --- neck ----------------------------------------------------------------------------------------
COLLAR_TAPER = 22.0
COLLAR_BORE_R = 13.45      # v8.1b: 0.45 radial gap to the cone r13 (v8.0: 1.0 - the torso interior showed through)
COLLAR_RELIEF = 0.2        # collar underside lifted 0.2 over the T02 half: sits on T01 only, T02 slides out freely
NECK_HOLE_R = 15.0
COLLAR_PINS = [(-(CO["w"] / 2 - 4.5), -7.0), (CO["w"] / 2 - 4.5, -7.0)]   # in T01, x +-18 (+-17)
NECK_STEP_Z = CN["z0"] + 2.0   # cone bore step r10 -> r8 = seat of the barrel snap hooks 125 (112)
SPIGOT_SH_R = 13.6
BAR_END = 3.5
HORN_RECESS = 1.8
SADDLE_GAP = 0.3

# --- arms (everything scales with the spec egg) ------------------------------------------------------------
ZC = EGG["widest_z"] - AX_Z                 # -21.6 (-18)
C_TOP = EGG["top_z"] - EGG["widest_z"]      # 33.6  (28)
C_BOT = EGG["widest_z"] - EGG["bottom_z"]   # 27.6  (23)
HW_, HT_ = EGG["half_w"], EGG["half_t"]     # 15.6, 8.4  (13, 7)
EGG_L = EGG["top_z"] - EGG["bottom_z"]      # 61.2  (51)
ARM_WALL = 1.8
ARM_HS = 0.25                               # 0.5 seam A01 / A02 / A03
TIP_ZTOP = EGG["bottom_z"] + 0.2157 * EGG_L  # tip seam height = 21.6 % of the egg (v8.1: 11 of 51)
TIP_YB = 0.1154 * HW_                       # 1.8 (1.5)
TIP_TILT = 45.0


def _egg_inner_x():
    """|x| where the shoulder axis (y 0, z AX_Z) enters the splayed egg (inner face of the arm)."""
    c, s = math.cos(math.radians(SPLAY)), math.sin(math.radians(SPLAY))
    d = -HT_
    for _ in range(30):                     # local point of the global axis line x = MID + d: (d c, 0, -d s)
        zl = -d * s
        d = -HT_ * math.sqrt(max(0.0, 1 - ((zl - ZC) / C_TOP) ** 2)) / c
    return MID + d


X_EGG_IN = _egg_inner_x()                   # 57.7 (52.75)
HUB_R, HUB_X0 = A04_R + 1.7, X_EGG_IN - 1.25    # A02 hub r 10.0 (9.0) from x 56.45 (51.5)
A04_X0, A04_X1 = ARM_SPL_X, X_EGG_IN + 1.75     # coupler 46 .. 59.45 (43 .. 54.5), 1.75 inside the egg
A04_SCREW_Y = A04_R - 3.3                       # 2x M2 hub -> coupler at y +-5.0 (+-4.5)
HORN_ARM = (13.0, 5.6, 1.6)

DEVIATIONS = [
    "TORSO.band (v8.0 centre band + 2 side shells) replaced by ONE parting line on y=0 (front shell T01 / rear "
    "shell T02): front without any seam; line hidden behind the arms and under the collar.",
    "Seams 0.5 mm (spec band.seam 0.6 is v8.0; v8.1 asks 0.4-0.6).",
    "Arm micro servos: FAR tab on a T01 block, NEAR tab on the T07 frame (v8.0: both on the side shells).",
    "T07 frame screwed to T01 only (4 ears; the v8.0 rear ear would sit in the removable rear shell).",
    "Collar pins moved from y 0 to y -7 (y 0 is now the parting line); v8.2 x +-18 (collar 45 wide).",
    "No separate rear door (spec v8.1 'rear door flush, hidden magnetic latch'): the WHOLE rear half shell T02 is "
    "the tool-free service cover - 2 top snap tongues, tongue-and-groove on the flank seam, 2x Ø5 N52 magnet pairs "
    "into T04; removes the U door seam from the back (back view = one clean surface).  Part T03 no longer exists.",
    "Barrel N06 decorative grooves removed (interface for H09/H10 and the head variants unchanged).",
    "T06 is a render-only glow of the LED bar (renderer has no transmissive smoked glass); 24 x 1.6 over the 5 LEDs "
    "(v8.2: the window grew to 36 x 5, the 5-LED bar stays 24 so ToF / ALS at x +-14.5 stay dark).",
    "6806 housing shoulder ID 38.6 (bears on the outer ring only; v8.0 ID 36 touched the 2RS seals).",
    "Collar bore Ø26.9 (0.45 gap to the cone r13; v8.0 Ø28 showed the torso interior), collar underside relieved "
    "0.2 over T02.",
    "T08 -> T04: 3x M2 from below at (35.2, 0), (-19, -16.5), (-25, 21) - v8.0 'POST_A' screw at (-17.5, 0) was in "
    "the T04 centre hole and held nothing.  T04 screw heads sunk 0.2 (B09 slide rim underneath).",
    "v8.2: shoulder ring A05 Ø24/Ø18 - spec gives only the bore 18; the v8.1 ring width 3 is kept.  Coupler A04 "
    "Ø16.6 (v8.1 Ø14.6) keeps the 0.7 radial gap in the ring bore.  Arm wall stays 1.8 (not scaled).",
    "v8.2: the pan stack (6805, gears, pan servo, frame housing) is 13 mm higher (follows the top wall), the arm "
    "servos 9 mm (shoulder axis); the frame wings now start 0.2 over the arm-servo cases (z 104.3) while the 6805 "
    "housing starts 0.8 over the gears (z 108.3) - in v8.1 both were z 95.3.",
    "v8.2: T01 bottom screws at (0, -32.5) and (+-33.2, -19.2) (v8.1 (0, -30.5), (+-31, -18)); front board E25 "
    "48 x 14 at y -32.8 / z 85..99; T02 magnets y 31.9; frame side ears x +-37 - all follow the larger shell.",
    "v8.2 review: T02 removal stroke 6.5 -> 19 mm.  v8.1 'slide 6.5, lift off' was impossible: the T02 top wall is "
    "still under the collar N01 (CAD: 74 mm3 at +1 mm lift) and its seats wrap the A05 rings; the +Y slide itself is "
    "free (checked to 20 mm), so T02 slides 19 mm back under the 0.2 collar relief and then lifts off.  No geometry "
    "change.",
]


# ============================================================================================
# helpers
# ============================================================================================

def bx(x0, x1, y0, y1, z0, z1):
    x0, x1 = min(x0, x1), max(x0, x1)
    y0, y1 = min(y0, y1), max(y0, y1)
    z0, z1 = min(z0, z1), max(z0, z1)
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)


def cyl_z(x, y, r, z0, z1):
    return Pos(x, y, min(z0, z1)) * Cylinder(r, abs(z1 - z0), align=(Align.CENTER, Align.CENTER, Align.MIN))


def cyl_x(y, z, r, x0, x1):
    lo, hi = min(x0, x1), max(x0, x1)
    return Pos(lo, y, z) * Rot(0, 90, 0) * Cylinder(r, hi - lo, align=(Align.CENTER, Align.CENTER, Align.MIN))


def cyl_y(x, z, r, y0, y1):
    lo, hi = min(y0, y1), max(y0, y1)
    return Pos(x, lo, z) * Rot(-90, 0, 0) * Cylinder(r, hi - lo, align=(Align.CENTER, Align.CENTER, Align.MIN))


def union(shapes):
    out = None
    for s in shapes:
        out = s if out is None else out + s
    return out


def stadium_y(xc, zc, w, h, y0, y1):
    r = h / 2
    s = bx(xc - (w / 2 - r), xc + (w / 2 - r), y0, y1, zc - r, zc + r)
    return (s + cyl_y(xc - (w / 2 - r), zc, r, y0, y1) + cyl_y(xc + (w / 2 - r), zc, r, y0, y1)).clean()


def slot_z(r0, r1, ang, w, z0, z1):
    """Radial stadium slot (vertical through-cut) from radius r0 to r1 at angle ang (deg)."""
    a = math.radians(ang)
    c, s = math.cos(a), math.sin(a)
    rm, L = (r0 + r1) / 2, r1 - r0
    core = Pos(rm * c, rm * s, (z0 + z1) / 2) * Rot(0, 0, ang) * Box(L, w, z1 - z0)
    return core + cyl_z(r0 * c, r0 * s, w / 2, z0, z1) + cyl_z(r1 * c, r1 * s, w / 2, z0, z1)


def place(shape, origin, z_dir, x_dir):
    return Plane(origin=origin, x_dir=x_dir, z_dir=z_dir).location * shape


def csk_hole(x, y, z_face, r_hole=1.2, r_head=2.2, depth=6.0):
    """Countersunk hole from a downward-facing face at z_face (screw from below; z_face above the real face = head
    sunk below it)."""
    h = cyl_z(x, y, r_hole, z_face - 1, z_face + depth)
    k = r_head - r_hole
    c = Pos(x, y, z_face - 0.01) * Cone(r_head, r_hole, k + 0.01, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return h + c + cyl_z(x, y, r_head, z_face - 2, z_face)


def check(name, s, vol_min=0.05):
    assert s is not None, name
    sol = s.solids()
    assert len(sol) >= 1, f"{name}: no solids"
    for so in sol:
        assert so.is_valid, f"{name}: invalid solid"
    assert s.volume > vol_min, f"{name}: volume {s.volume}"
    return s


def try_fillet(shape, edges, r, name=""):
    if not edges:
        return shape
    try:
        f = shape.fillet(r, edges)
        if f.is_valid and abs(f.volume - shape.volume) < 0.05 * shape.volume:
            return f
        print(f"   [fillet rejected] {name}")
    except Exception as e:  # noqa: BLE001
        print(f"   [fillet skipped] {name}: {str(e)[:80]}")
    return shape


def fuse(a, b, name=""):
    """a + b with a validity / volume guard (coincident B-spline faces silently corrupt OCC fuses)."""
    r = a + b
    ok = r.is_valid and r.volume >= max(a.volume, b.volume) - 1e-3 and r.volume <= a.volume + b.volume + 1e-3
    assert ok, f"fuse failed: {name} ({a.volume:.0f} + {b.volume:.0f} -> {r.volume:.0f}, valid={r.is_valid})"
    return r


def one(s, name):
    """Largest solid (drops OCC slivers) - printed parts must be one piece."""
    sol = sorted(s.solids(), key=lambda q: q.volume, reverse=True)
    if len(sol) > 1:
        small = [round(q.volume, 3) for q in sol[1:]]
        print(f"   [{name}] dropped {len(sol) - 1} sliver(s) {small}")
        assert all(v < 0.5 for v in small), f"{name}: real extra solids {small}"
    return sol[0]


_cache: dict = {}


def cached(key, fn):
    if key not in _cache:
        _cache[key] = fn()
    return _cache[key]


# ============================================================================================
# torso outer body + offsets
# ============================================================================================

def body():
    def mk():
        w = superellipse_wire(TA, TB, TN, T_Z0, count=96)
        s = extrude(Face(w), T_Z1 - T_Z0, dir=(0, 0, 1))
        s = fillet(s.edges().group_by(Axis.Z)[-1], R_TOP)
        s = fillet(s.edges().group_by(Axis.Z)[0], R_BOT)
        assert s.is_valid
        return s
    return cached("body", mk)


def off(d):
    if d <= 0:
        return body()

    def mk():
        o = offset(body(), amount=-d)
        assert o.is_valid and o.volume < body().volume - 500, f"offset {d} failed"
        return o
    return cached(("off", round(d, 3)), mk)


def skin(d0, d1):
    return cached(("skin", d0, d1), lambda: off(d0) - off(d1))


def above(z=Z_SH):
    return bx(-BIG, BIG, -BIG, BIG, z, BIG)


def wall():
    return cached("wall", lambda: (body() - off(WALL)) & above())


def front_zone():
    return bx(-BIG, BIG, -BIG, -HS, -BIG, BIG)


def rear_zone():
    return bx(-BIG, BIG, HS, BIG, -BIG, BIG)


def round_seam(s, y0, name):
    """R0.25 on the OUTER edges lying in the seam plane y = y0 (premium soft shadow line)."""
    inner = off(1.0)
    edges = []
    for e in s.edges():
        bb = e.bounding_box()
        if abs(bb.min.Y - y0) < 0.02 and abs(bb.max.Y - y0) < 0.02 and e.length > 5.0:
            if not inner.is_inside(e.position_at(0.5)):      # a point ON the curve (center() of a U lies inside)
                edges.append(e)
    return try_fillet(s, edges, SEAM_R, name)


# ============================================================================================
# gears
# ============================================================================================

def gear_face(z, m, phase_deg=0.0, backlash=0.12, n_inv=7):
    pa = math.radians(20.0)
    rp = m * z / 2
    rb, ra, rf = rp * math.cos(pa), rp + m, rp - 1.25 * m

    def inv(a):
        return math.tan(a) - a
    psi = math.pi / (2 * z) - backlash / (2 * rp)

    def fa(r):
        r = max(r, rb)
        return psi + inv(pa) - inv(math.acos(rb / r))
    rs = [rb + (ra - rb) * i / (n_inv - 1) for i in range(n_inv)]
    pts = []
    for k in range(z):
        c = math.radians(phase_deg) + 2 * math.pi * k / z
        a_root = fa(rb) - 0.02
        seq = [(rf, c - a_root)] + [(r, c - fa(r)) for r in rs] + [(r, c + fa(r)) for r in reversed(rs)] + \
              [(rf, c + a_root)]
        pts += [Vector(r * math.cos(a), r * math.sin(a), 0) for r, a in seq]
    return Face(Wire.make_polygon(pts, close=True))


def gear(z, m, cx, cy, z0, z1, phase_deg=0.0):
    return Pos(cx, cy, z0) * extrude(gear_face(z, m, phase_deg), z1 - z0)


# ============================================================================================
# purchased components (catalogue envelopes)
# ============================================================================================

def micro_servo_local():
    """MG90S envelope.  Local frame: origin = spline axis on the case top plane, +Z = output, +X = toward the
    far end of the case."""
    x0, x1 = -MS_SHAFT_END, MS_L - MS_SHAFT_END
    c = bx(x0, x1, -MS_W / 2, MS_W / 2, -MS_H, 0)
    c = try_fillet(c, c.edges().filter_by(Axis.Z), 0.6, "servo case")
    t0, t1 = MS_TAB_Z[0] - MS_H, MS_TAB_Z[1] - MS_H
    xc = (x0 + x1) / 2
    tab = bx(xc - MS_TABS / 2, xc + MS_TABS / 2, -MS_W / 2, MS_W / 2, t0, t1)
    for hx in (-HOLE_NEAR, HOLE_FAR):
        tab = tab - cyl_z(hx, 0, 1.0, t0 - 1, t1 + 1) - bx(hx, hx + math.copysign(5, hx), -0.5, 0.5, t0 - 1, t1 + 1)
    c = c + tab
    c = c + cyl_z(0, 0, MS_DOME_R, -0.01, MS_DOME_H) + cyl_z(7.2, 0, 2.8, -0.01, 1.2)
    c = c + cyl_z(0, 0, MS_SPL_R, MS_DOME_H - 0.01, MS_DOME_H + MS_SPL_H)
    c = c + bx(x1 - 0.01, x1 + 1.6, -1.6, 1.6, -MS_H + 0.8, -MS_H + 4.0)       # cable strain relief
    return c


def sts3215_local():
    """Feetech STS3215 envelope 45.2 x 24.7 x 35.  Local frame: origin = output axis on the horn face, +Z = output."""
    c = bx(YS_X0, YS_X1, -YS_HW, YS_HW, -YS_H, 0)
    c = try_fillet(c, c.edges().filter_by(Axis.Z), 1.5, "sts case")
    for zg in (-4.0, -YS_H + 5.0):          # case split lines
        ring = bx(YS_X0 - 1, YS_X1 + 1, -YS_HW - 1, YS_HW + 1, zg - 0.25, zg + 0.25) - \
            bx(YS_X0 + 0.3, YS_X1 - 0.3, -YS_HW + 0.3, YS_HW - 0.3, zg - 1, zg + 1)
        c = c - ring
    c = c + cyl_z(0, 0, 5.0, -0.01, 1.5)                     # output boss (spline inside the horn)
    c = c + cyl_z(0, 0, 2.95, 1.49, 1.6)
    c = c - cyl_z(0, 0, 1.5, -6.0, 1.7)                      # M3 centre thread of the output (axial screw IT03)
    c = c + bx(YS_X0 - 2.0, YS_X0 + 0.01, -3.0, 3.0, -YS_H + 2.0, -YS_H + 7.0)   # cable exit (shaft end, top)
    return c


def bearing(ri, ro, z0, z1, x=0.0, y=0.0):
    w = z1 - z0
    t = (ro - ri) * 0.28
    b = cyl_z(x, y, ro, z0, z1) - cyl_z(x, y, ri, z0 - 1, z1 + 1)
    groove = (cyl_z(x, y, ro - t, z0 - 1, z1 + 1) - cyl_z(x, y, ri + t, z0 - 1, z1 + 1)) - \
        cyl_z(x, y, ro, z0 + 0.35, z1 - 0.35)
    return b - groove if w > 1 else b


def horn_micro_x(sx):
    """Trimmed micro-servo horn on an arm servo spline (global, side sx)."""
    hub = cyl_x(AX_Y, AX_Z, 3.5, sx * (ARM_TOP_X + MS_DOME_H + 0.2), sx * (ARM_SPL_X + HORN_ARM[2])) - \
        cyl_x(AX_Y, AX_Z, MS_SPL_R, sx * (ARM_TOP_X + MS_DOME_H), sx * ARM_SPL_X)
    L, W, T = HORN_ARM
    arm = bx(sx * ARM_SPL_X, sx * (ARM_SPL_X + T), -W / 2, W / 2, AX_Z - L / 2 + W / 2, AX_Z + L / 2 - W / 2)
    arm = arm + cyl_x(0, AX_Z - L / 2 + W / 2, W / 2, sx * ARM_SPL_X, sx * (ARM_SPL_X + T)) + \
        cyl_x(0, AX_Z + L / 2 - W / 2, W / 2, sx * ARM_SPL_X, sx * (ARM_SPL_X + T))
    return (hub + arm).clean()


# ============================================================================================
# TORSO shells (clamshell on y = 0)
# ============================================================================================

def shoulder_boss(sx):
    return cyl_x(AX_Y, AX_Z, SH_BOSS_R, sx * (A05_X0 - 1.0), sx * (TA + 2)) & off(0.3)    # never share the outer face


def shoulder_cut(sx):
    return cyl_x(AX_Y, AX_Z, A05_RO + 0.2, sx * A05_X0, sx * (TA + 5)) + \
        cyl_x(AX_Y, AX_Z, A05_RI + 0.6, sx * (A05_X0 - 3), sx * (TA + 5))


def bottom_boss(x, y, h=4.0):
    """Boss standing on T04 (M2 from below through T04), bridged to the wall."""
    if abs(x) > 1:
        arm = bx(x, math.copysign(TA + 2.0, x), y - 3, y + 3, Z_SH, Z_SH + h)
    else:
        arm = bx(x - 3, x + 3, y, math.copysign(TB + 4.0, y), Z_SH, Z_SH + h)
    return (cyl_z(x, y, 3.0, Z_SH, Z_SH + h) + arm) & off(1.0)


def ledge_keepout():
    """Zones where the T01 seam ledge must not be (shoulder bosses, bearing housing, T02 snap tongues)."""
    k = cyl_z(0, 0, T07_HOUSE_RO + 1.0, T_Z1 - 25.0, T_Z1 + 15.0)
    for sx in (1, -1):
        k = k + cyl_x(AX_Y, AX_Z, A05_RO + 3.5, sx * (TA - 14.0), sx * (TA + 6.0))
    for x in TONGUE_X:
        k = k + bx(x - 4.6, x + 4.6, -8.0, 4.0, TOP_ZONE_Z - 5.0, BIG)
    return k


def seam_ledge():
    """T01 ledge along the parting line (sides + top): fused into the T01 wall (offset 1..2) and reaching 2.5 mm
    behind the T02 wall (offset 2.05..3.4) - closes the 0.5 seam from behind and aligns the shells."""
    a = skin(1.0, 3.3) & bx(-BIG, BIG, -3.0, -HS, -BIG, BIG)          # different inner offsets: never two
    b = skin(LEDGE_D, 3.4) & bx(-BIG, BIG, -HS - 0.5, 2.5, -BIG, BIG)  # coincident B-spline faces in a fuse
    return ((a + b) & above(Z_SH + 1.0)) - ledge_keepout()


def t02_tongue(x):
    anchor = bx(x - 4, x + 4, HS, 3.0, TOP_ZONE_Z, BIG) & skin(1.0, 3.1)
    tongue = bx(x - 4, x + 4, -6.0, 0.5, TOP_ZONE_Z, BIG) & skin(LEDGE_D, 3.2)
    bump = bx(x - 3, x + 3, -5.3, -4.5, TOP_ZONE_Z, BIG) & skin(1.7, 2.4)
    return anchor + tongue + bump


def front_shell_t01():
    s = wall() & front_zone()
    s = round_seam(s, -HS, "T01 seam")
    s = fuse(s, seam_ledge(), "T01 ledge")
    for sx in (1, -1):
        s = fuse(s, shoulder_boss(sx) & front_zone(), "T01 shoulder boss")
        b1 = bx(sx * TAB_BLK_X, sx * FAR_BLK_X1, FAR_BLK_Y[0], FAR_BLK_Y[1], AX_Z - 3.5, AX_Z + 3.5) & off(1.0)
        s = fuse(s, b1, "T01 far-tab block")
    for sx in (1, -1):
        s = s - shoulder_cut(sx) - cyl_x(-HOLE_FAR, AX_Z, 0.8, sx * (TAB_BLK_X - 0.5), sx * (FAR_BLK_X1 - 3.1))
    # bosses for the frame T07 (M2 from below)
    for (x, y) in T07_EARS:
        s = s + (cyl_z(x, y, 3.0, T07_PLATE_Z[1], T_Z1 + 1.0) & off(1.0))
        s = s - cyl_z(x, y, 0.8, T07_PLATE_Z[1] - 1, T07_PLATE_Z[1] + 3.5)
    # bottom bosses (M2 from below through T04)
    for (x, y) in T01_SCREWS:
        s = s + bottom_boss(x, y) - cyl_z(x, y, 0.8, Z_SH - 1, Z_SH + 3.5)
    # bosses for the front board E25 (screws from behind through the board)
    bxx, bzz = E25["boss"]
    for sx in (1, -1):
        s = s + (cyl_y(sx * bxx, bzz, 2.2, -TB - 1, E25["y0"]) & off(1.0))
        s = s - cyl_y(sx * bxx, bzz, 0.8, E25["y0"] - 1.9, E25["y0"] + 0.1)     # blind (v8.0-style 3.5 broke through)
    # ONE chest window
    s = s - stadium_y(0, CH["z"], CH["w"], CH["h"], -TB - 5, -TB + 8)
    # neck hole + collar pins + grooves for the T02 snap bumps
    s = s - cyl_z(0, 0, NECK_HOLE_R, T_Z1 - 7.0, T_Z1 + 5.0)
    for (x, y) in COLLAR_PINS:
        s = s - cyl_z(x, y, 1.35, T_Z1 - 5.0, T_Z1 + 5.0)
    for x in TONGUE_X:
        s = s - (bx(x - 3.4, x + 3.4, -5.6, -4.2, TOP_ZONE_Z, BIG) & skin(1.6, 2.2))
    return one(s, "T01")


def t02_channel():
    """Groove for the T01 seam ledge along the flanks + the top: T02 is held in X and Z along the whole parting line
    and only slides +Y (removal).  Returns (material to fuse, void to cut), both limited to where the ledge exists."""
    zone = above(CHAN_Z0) - ledge_keepout()
    rib = (skin(1.0, CHAN_RIB[1]) & bx(-BIG, BIG, HS, CHAN_Y1, -BIG, BIG)) & zone
    void = (skin(CHAN_VOID[0], CHAN_VOID[1]) & bx(-BIG, BIG, -HS - 1.0, 2.65, -BIG, BIG)) & zone
    return rib, void


def rear_shell_t02():
    """Rear half shell = the tool-free service cover (v8.1b): no door seam, no screws, no visible latch."""
    s = wall() & rear_zone()
    s = round_seam(s, HS, "T02 seam")
    for sx in (1, -1):
        s = fuse(s, shoulder_boss(sx) & rear_zone(), "T02 shoulder boss")
    for sx in (1, -1):
        s = s - shoulder_cut(sx)
    for x in TONGUE_X:
        s = fuse(s, t02_tongue(x), "T02 tongue")
    rib, void = t02_channel()
    s = fuse(s, rib, "T02 channel") - void
    for (x, y) in MAG_XY:          # hidden magnetic latch: Ø5x2 N52 in T02 against Ø5x1.5 N52 in T04
        boss = cyl_z(x, y, MAG_BOSS_R, Z_SH, Z_SH + 5.0) & off(1.0)
        s = fuse(s, boss, "T02 magnet boss")
        s = s - cyl_z(x, y, MAG_D / 2 + 0.1, Z_SH - 1, Z_SH + MAG_T_T02 + 0.1)
    s = s - cyl_z(0, 0, NECK_HOLE_R, T_Z1 - 7.0, T_Z1 + 5.0)
    return one(s, "T02")


def window_t05():
    w = (body() - off(WALL + 0.4)) & stadium_y(0, CH["z"], CH["w"] - 0.2, CH["h"] - 0.2, -TB - 5, -TB + 8)
    fl = skin(WALL, WALL + 0.8) & stadium_y(0, CH["z"], CH["w"] + 3.0, CH["h"] + 3.0, -TB - 5, -TB + 8)
    return one(fuse(w, fl, "T05 flange"), "T05")


def glow_t06():
    g = skin(-1.0, 0.15) & stadium_y(0, CH["z"], GLOW["w"], GLOW["h"], -TB - 5, -TB + 8)
    return one(Pos(0, -0.15, 0) * g, "T06")          # 0.15 skin moved just in front of the window face


def plate_t04():
    d = cyl_z(0, 0, RING_OD / 2, T_Z0, Z_SH)
    d = try_fillet(d, d.edges().group_by(Axis.Z)[-1], 0.8, "T04 top")
    d = try_fillet(d, d.edges().group_by(Axis.Z)[0], 0.8, "T04 bottom")
    h = cyl_z(0, 0, YH_RO, YH_Z0, T_Z0 + 0.01)
    h = try_fillet(h, h.edges().group_by(Axis.Z)[0], 0.6, "housing")
    d = d + h
    d = d - cyl_z(0, 0, YH_BORE_R, YH_Z0 - 1, YAW_BRG_Z1) - cyl_z(0, 0, YH_SHOULDER_R, YH_Z0 - 2, Z_SH + 2)
    d = d - cable_slot(T_Z0 - 2, Z_SH + 2)
    for (x, y) in T04_SCREWS:
        d = d - csk_hole(x, y, T_Z0 + CSK_SINK, 1.2, 2.2, 6)
    for a in VENT_A:
        d = d - slot_z(VENT_R[0], VENT_R[1], a, VENT_W, T_Z0 - 1, Z_SH + 1)
    for (x, y) in MAG_XY:
        d = d - cyl_z(x, y, MAG_D / 2 + 0.1, Z_SH - MAG_T_T04 - 0.1, Z_SH + 1)
    d = d - bx(-NAIL_W / 2, NAIL_W / 2, NAIL_Y[0], NAIL_Y[1], Z_SH - NAIL_D, Z_SH + 1)   # black nail recess under T02
    return d


def cable_slot(z0, z1):
    c = CABLE_SLOT
    rm, hw = (c["r0"] + c["r1"]) / 2, (c["r1"] - c["r0"]) / 2
    ring = cyl_z(0, 0, c["r1"], z0, z1) - cyl_z(0, 0, c["r0"], z0 - 1, z1 + 1)
    pts = [Vector(0, 0, 0)] + [Vector(60 * math.cos(math.radians(a)), 60 * math.sin(math.radians(a)), 0)
                               for a in (c["a0"], 180.0, c["a1"])]
    wedge = Pos(0, 0, z0) * extrude(Face(Wire.make_polygon(pts, close=True)), z1 - z0)
    s = ring & wedge
    for a in (c["a0"], c["a1"]):
        s = s + cyl_z(rm * math.cos(math.radians(a)), rm * math.sin(math.radians(a)), hw, z0, z1)
    return s


def magnets_m23():
    m = None
    for (x, y) in MAG_XY:
        a = cyl_z(x, y, MAG_D / 2, Z_SH + 0.05, Z_SH + 0.05 + MAG_T_T02)
        b = cyl_z(x, y, MAG_D / 2, Z_SH - 0.05 - MAG_T_T04, Z_SH - 0.05)
        m = a + b if m is None else m + a + b
    return m


# ============================================================================================
# torso internals
# ============================================================================================

def cradle_t08():
    z0, z1 = Z_SH, T08_Z1
    p = bx(-20.5, 34.0, -(YS_HW + 0.2 + CR_T + 0.6), YS_HW + 0.2 + CR_T + 0.6, z0, z1) + \
        bx(-27.5, 27.5, YS_HW + 0.2 + CR_T + 0.6, 21.8, z0, z1)
    p = p + cyl_z(POST_B[0], POST_B[1], POST_B[2] + 0.4, z0, z1)
    p = p - cyl_z(0, 0, T08_HOLE_R, z0 - 1, z1 + 1)
    yi = YS_HW + 0.2
    for sy in (1, -1):
        p = p + bx(YS_X0 - 0.2 - CR_T, 24.0, sy * yi, sy * (yi + CR_T), z1 - 0.3, CRADLE_Z1)
    p = p + bx(YS_X0 - 0.2 - CR_T, YS_X0 - 0.2, -(yi + CR_T), yi + CR_T, z1 - 0.3, CRADLE_Z1)
    p = p - bx(YS_X0 - 3, YS_X0 + 1, -5, 5, CRADLE_Z1 - 7, CRADLE_Z1 + 1)       # cable notch
    for (xa, xb) in ((YS_X0, YS_X0 + 5), (YS_X1 - 5, YS_X1)):
        for sy in (1, -1):
            p = p + bx(xa, xb, sy * (YS_HW - 5), sy * YS_HW, z1 - 0.3, YS_Z0)
    for (x, y, r) in (POST_A, POST_B):
        p = p + cyl_z(x, y, r, z1 - 0.3, STRAP_Z[0])
        p = p - cyl_z(x, y, 0.8, STRAP_Z[0] - 7, STRAP_Z[0] + 1)            # strap screws from above
    p = p + cyl_z(T08_SCREWS[1][0], T08_SCREWS[1][1], 3.0, z0, z0 + 4.5)     # free corner boss (x < servo end)
    for sx in (1, -1):
        post = bx(sx * 23.0, sx * 27.0, PCB["y0"] - 1.2, PCB["y0"] + PCB["t"] + 2.2, z1 - 0.3, PCB["z1"] - 0.2)
        groove = bx(sx * 22.0, sx * (PCB["x"] + 0.6), PCB["y0"] - 0.15, PCB["y0"] + PCB["t"] + 0.15,
                    PCB["z0"] - 0.2, PCB["z1"] + 1)
        p = p + post - groove
    for (x, y) in T08_SCREWS:      # 3x M2 from below through T04 (POST_B, corner boss, rear-left PCB post)
        p = p - cyl_z(x, y, 0.8, z0 - 1, z0 + 6.5)
    return p


def strap_t09():
    x0, x1 = POST_A[0] - 3.0, POST_B[0] + 1.8
    s = bx(x0 + 4, x1 - 4, -4, 4, *STRAP_Z) + cyl_z(x0 + 4, 0, 4, *STRAP_Z) + cyl_z(x1 - 4, 0, 4, *STRAP_Z)
    s = s & bx(x0, x1, -4, 4, *STRAP_Z)
    for (x, y, r) in (POST_A, POST_B):
        s = s - cyl_z(x, y, 1.1, STRAP_Z[0] - 1, STRAP_Z[1] + 1)
    return s


def frame_t07():
    """Internal frame: 6805 housing, plate, pan-servo rails, wings over both arm servos with the NEAR-tab blocks.
    Screwed into 4 T01 bosses -> the whole upper mechanism lives on the front shell."""
    h = cyl_z(0, 0, T07_HOUSE_RO, T07_HOUSE_Z0, PB_Z1)
    plate = bx(-24.0, 24.0, -24.0, -16.5, *T07_PLATE_Z) + \
        bx(-24.0, RAIL_R[1], 9.0, RAIL_Y[1], T07_HOUSE_Z0, T07_PLATE_Z[1])
    p = h + plate
    for sx in (1, -1):
        wing = bx(sx * 17.0, sx * NEAR_BLK_X1, -17.0, NEAR_BLK_Y[1], WING_Z0, T07_PLATE_Z[1])
        blk = bx(sx * TAB_BLK_X, sx * NEAR_BLK_X1, NEAR_BLK_Y[0], NEAR_BLK_Y[1], AX_Z - 3.5, T07_PLATE_Z[1])
        p = p + wing + blk
    for (xa, xb) in (RAIL_L, RAIL_R):
        p = p + bx(xa, xb, RAIL_Y[0], RAIL_Y[1], PAN_TAB_Z0 - 2.0, T07_HOUSE_Z0 + 0.01)
    p = p + bx(RAIL_L[1], RAIL_R[0], 12.8, 13.7, PAN_TAB_Z0 - 2.0, PAN_TAB_Z0 + 1.0)        # front stop web
    gz0, gz1 = PAN_TAB_Z0 - 0.25, PAN_TAB_Z1 + 0.25
    p = p - bx(RAIL_L[1] - 5.2, RAIL_L[1] + 0.2, 12.0, 30.0, gz0, gz1)
    p = p - bx(RAIL_R[0] - 0.2, RAIL_R[0] + 5.2, 12.0, 30.0, gz0, gz1)
    p = p - cyl_z(0, 0, PB_RO, PB_Z0, PB_Z1 + 1) - cyl_z(0, 0, T07_LIP_RI, T07_HOUSE_Z0 - 1, PB_Z1 + 1)
    p = p - cyl_z(0, PAN_SERVO_Y, 11.6, G_Z0 - 2, T07_HOUSE_Z0 + 0.0)
    for (x, y) in T07_EARS:
        p = p - cyl_z(x, y, 1.15, min(WING_Z0, T07_HOUSE_Z0) - 2, T07_PLATE_Z[1] + 1)   # through wings + plate
    for xc in (sum(RAIL_L) / 2, sum(RAIL_R) / 2):
        p = p - cyl_y(xc, PAN_TAB_Z1 + 4.0, 0.8, RAIL_Y[1] - 6, RAIL_Y[1] + 1)
    for sx in (1, -1):        # near-tab pilots (M2 from inside through the servo tab)
        p = p - cyl_x(HOLE_NEAR, AX_Z, 0.8, sx * (TAB_BLK_X - 0.5), sx * NEAR_BLK_X1)
    p = p & off(WALL + 0.3)                                   # 0.3 clear of both shells' inner skin
    p = p - (skin(WALL - 0.01, 3.75) & bx(-BIG, BIG, -3.3, 2.85, -BIG, BIG))   # clear of the seam ledge
    p = p - ((skin(WALL - 0.01, CHAN_RIB[1] + 0.3) & bx(-BIG, BIG, -3.3, CHAN_Y1 + 0.3, -BIG, BIG)) &
             (above(CHAN_Z0) - ledge_keepout()))                              # ... and of the T02 channel
    return one(p, "T07")


def hub_gear_n03():
    g = gear(G_Z, G_M, 0, 0, G_Z0, G_Z1, phase_deg=90.0 + 180.0 / G_Z)
    g = g + cyl_z(0, 0, 14.3, G_Z1 - 0.01, PB_Z0)
    g = g - cyl_z(0, 0, 4.0, G_Z0 - 1, PB_Z0 + 1)
    for sx in (1, -1):
        g = g - cyl_z(sx * 7.0, 0, 0.8, G_Z0 + 0.8, PB_Z0 + 1)
    return g


def servo_gear_n04():
    g = gear(G_Z, G_M, 0, PAN_SERVO_Y, G_Z0, G_Z1, phase_deg=270.0)
    L = 18.3
    rec = bx(-L / 2 + 2.95, L / 2 - 2.95, PAN_SERVO_Y - 2.95, PAN_SERVO_Y + 2.95, G_Z0 - 1, PAN_HORN_Z1 + 0.1) + \
        cyl_z(-L / 2 + 2.95, PAN_SERVO_Y, 2.95, G_Z0 - 1, PAN_HORN_Z1 + 0.1) + \
        cyl_z(L / 2 - 2.95, PAN_SERVO_Y, 2.95, G_Z0 - 1, PAN_HORN_Z1 + 0.1) + \
        cyl_z(0, PAN_SERVO_Y, 3.7, G_Z0 - 1, PAN_HORN_Z1 + 0.1)
    g = g - rec - cyl_z(0, PAN_SERVO_Y, 1.3, G_Z0 - 1, G_Z1 + 1)
    for sx in (1, -1):
        g = g - cyl_z(sx * 6.5, PAN_SERVO_Y, 0.7, G_Z0, G_Z1 + 1)
    return g


def pan_horn_e23h():
    y = PAN_SERVO_Y
    hub = cyl_z(0, y, 3.5, PAN_HORN_Z0, PAN_HORN_Z1) - cyl_z(0, y, MS_SPL_R, PAN_HORN_Z0 - 0.1, PAN_SPL_TOP)
    L, W = 18.0, 5.6
    arm = bx(-L / 2 + W / 2, L / 2 - W / 2, y - W / 2, y + W / 2, G_Z0, PAN_HORN_Z1) + \
        cyl_z(-L / 2 + W / 2, y, W / 2, G_Z0, PAN_HORN_Z1) + cyl_z(L / 2 - W / 2, y, W / 2, G_Z0, PAN_HORN_Z1)
    return (hub + arm).clean() - cyl_z(0, y, MS_SPL_R, PAN_HORN_Z0 - 0.1, PAN_SPL_TOP)


def yaw_horn_e21h():
    h = cyl_z(0, 0, 10.0, YAW_BRG_Z1, YAW_BRG_Z1 + 2.5) + cyl_z(0, 0, 4.5, YAW_BRG_Z1 + 2.5, YS_Z0 - 1.6)
    for k in range(4):
        a = math.radians(45 + 90 * k)
        h = h - cyl_z(7.0 * math.cos(a), 7.0 * math.sin(a), 1.1, YAW_BRG_Z1 - 1, YAW_BRG_Z1 + 3)
    return h - cyl_z(0, 0, 1.6, YAW_BRG_Z1 - 1, YS_Z0)


def controller_e24():
    b = bx(-PCB["x"], PCB["x"], PCB["y0"], PCB["y0"] + PCB["t"], PCB["z0"], PCB["z1"])
    y1 = PCB["y0"] + PCB["t"]
    # SuperMini (22.5 x 18) right of centre, its USB-C mouth faces -X at x -4.9 (reachable with T02 removed;
    # normal updates OTA / through the head S3 over UART)
    xs = -4.0
    sm = bx(xs, xs + 22.5, y1 + 2.5, y1 + 3.5, PCB["z0"] + 0.25, PCB["z0"] + 18.25)
    pins = bx(xs + 1.0, xs + 21.5, y1 - 0.01, y1 + 2.5, PCB["z0"] + 1.0, PCB["z0"] + 3.5) + \
        bx(xs + 1.0, xs + 21.5, y1 - 0.01, y1 + 2.5, PCB["z0"] + 15.0, PCB["z0"] + 17.5)
    chip = bx(xs + 7.0, xs + 16.0, y1 + 3.49, y1 + 4.3, PCB["z0"] + 5.0, PCB["z0"] + 13.0)
    usb = bx(xs - 0.9, xs + 6.5, y1 + 3.49, y1 + 6.7, PCB["z0"] + 5.5, PCB["z0"] + 14.5)
    # MP1584 5 V buck module + bus driver (v8.0: DRV8833 - the motors moved to the base node, spec review 2)
    drv = bx(-23.5, -5.5, y1 + 2.5, y1 + 3.5, PCB["z0"] + 1.0, PCB["z0"] + 17.0) + \
        bx(-22.5, -6.5, y1 - 0.01, y1 + 2.5, PCB["z0"] + 1.5, PCB["z0"] + 4.0) + \
        bx(-17.5, -11.5, y1 + 3.49, y1 + 4.5, PCB["z0"] + 6.0, PCB["z0"] + 12.0)
    con = bx(-23.0, -8.0, PCB["y0"] - 1.0, PCB["y0"] + PCB["t"] + 4.0, PCB["z1"] - 0.01, PCB["z1"] + 6.0) + \
        bx(19.0, 23.5, PCB["y0"] - 1.0, PCB["y0"] + PCB["t"] + 4.0, PCB["z1"] - 0.01, PCB["z1"] + 6.0)
    return b + sm + pins + chip + usb + drv + con


def front_board_e25():
    """5x WS2812B-2020 light bar + VL53L0X (x +14.5) + ambient light sensor (x -14.5), all behind T05."""
    y0, zc = E25["y0"], CH["z"]
    b = bx(-E25["x"], E25["x"], y0, y0 + E25["t"], E25["z0"], E25["z1"])
    for sx in (1, -1):
        b = b - cyl_y(sx * E25["boss"][0], E25["boss"][1], 1.1, y0 - 1, y0 + E25["t"] + 1)
    leds = union(bx(x - 1.1, x + 1.1, y0 - 0.9, y0 + 0.01, zc - 1.1, zc + 1.1) for x in (-10, -5, 0, 5, 10))
    tof = bx(12.3, 16.7, y0 - 1.0, y0 + 0.01, zc - 1.2, zc + 1.2)
    als = bx(-15.5, -13.5, y0 - 0.7, y0 + 0.01, zc - 1.0, zc + 1.0)
    return b + leds + tof + als


# ============================================================================================
# NECK
# ============================================================================================

def collar_n01():
    from build123d import Solid
    w0 = superellipse_wire(CO["w"] / 2, CO["d"] / 2, TN, CO["z0"], count=64)
    k = (CO["z1"] - CO["z0"]) * math.tan(math.radians(COLLAR_TAPER))
    w1 = superellipse_wire(CO["w"] / 2 - k, CO["d"] / 2 - k, TN, CO["z1"], count=64)
    c = Solid.make_loft([w0, w1], ruled=True)
    c = try_fillet(c, c.edges().group_by(Axis.Z)[-1], 1.4, "collar top")
    c = c - cyl_z(0, 0, COLLAR_BORE_R, CO["z0"] - 1, CO["z1"] + 1)
    c = c - bx(-BIG, BIG, -HS, BIG, CO["z0"] - 1, CO["z0"] + COLLAR_RELIEF)   # sits on T01 only
    for (x, y) in COLLAR_PINS:
        c = c + cyl_z(x, y, 1.2, CO["z0"] - 1.4, CO["z0"] + 0.01)
    return c


def cone_n02():
    z0, z1, rb, rt = CN["z0"], CN["z1"], CN["r_bottom"], CN["r_top"]
    pts = []
    n = 16
    for i in range(n + 1):
        z = z0 + (z1 - z0) * i / n
        r = rt + (rb - rt) * ((z1 - z) / (z1 - z0)) ** 2
        pts.append(Vector(r, 0, z))
    edges = [Edge.make_line(Vector(0, 0, z0), pts[0]), Edge.make_spline(pts),
             Edge.make_line(pts[-1], Vector(0, 0, z1)), Edge.make_line(Vector(0, 0, z1), Vector(0, 0, z0))]
    trumpet = revolve(Face(Wire(edges)), Axis.Z, 360)
    c = trumpet + cyl_z(0, 0, rb, CO["z0"], z0 + 0.01) + cyl_z(0, 0, SPIGOT_SH_R, PB_Z1, CO["z0"] + 0.01) + \
        cyl_z(0, 0, PB_RI, PB_Z0, PB_Z1 + 0.01)
    c = c - cyl_z(0, 0, 10.0, PB_Z0 + 1.5, NECK_STEP_Z) - cyl_z(0, 0, 8.0, NECK_STEP_Z - 0.01, z1 + 2)
    c = c - cyl_z(0, 0, 4.0, PB_Z0 - 1, PB_Z0 + 2)
    for sx in (1, -1):
        c = c - cyl_z(sx * 7.0, 0, 1.2, PB_Z0 - 1, PB_Z0 + 2)
    c = c - cyl_x(TLY, TLZ, BAR_R + SADDLE_GAP, -BAR_L, BAR_L)
    return c


def barrel_n06():
    hb = BAR_L / 2
    b = cyl_x(TLY, TLZ, BAR_R, -hb, hb)
    b = try_fillet(b, b.edges(), 1.0, "barrel ends")
    zs = NECK_STEP_Z          # snap hooks catch under the r10 -> r8 step of the cone bore
    stem = cyl_z(0, 0, 7.8, zs - 3.5, TLZ - BAR_R + 2.5)
    b = b + stem
    b = b - cyl_x(TLY, TLZ, BAR_R - WALL, -(hb - BAR_END), hb - BAR_END)
    b = b - cyl_z(0, 0, 4.5, zs - 5.0, TLZ)
    b = b - bx(-1.0, 1.0, -10, 10, zs - 4.0, zs + 0.4)
    for sx in (1, -1):
        hook = (cyl_z(0, 0, 9.1, zs - 3.1, zs - 0.3) - cyl_z(0, 0, 7.7, zs - 4.0, zs + 1.0)) & \
            bx(sx * 3.0, sx * 10, -3.0, 3.0, zs - 12.0, zs + 8.0)
        b = b + hook
    # both ends: cross-horn recess, pivot hole, 2 screw bosses (interface for H09/H10 of all head variants)
    for sx in (1, -1):
        xa, xb = sx * (hb - HORN_RECESS), sx * (hb + 1)
        rec = bx(xa, xb, -9.6, 9.6, TLZ - 2.9, TLZ + 2.9) + bx(xa, xb, -2.9, 2.9, TLZ - 9.6, TLZ + 9.6) + \
            cyl_x(TLY, TLZ, 4.0, xa, xb)
        b = b - rec
        b = b - cyl_x(TLY, TLZ, 1.6, sx * (hb - BAR_END - 1), sx * (hb + 1))
        for sy in (1, -1):
            b = b + cyl_x(sy * 7.5, TLZ, 2.4, sx * (hb - BAR_END - 3.5), sx * (hb - BAR_END + 0.01))
            b = b - cyl_x(sy * 7.5, TLZ, 0.7, sx * (hb - BAR_END - 3.0), sx * (hb + 1))
    c45 = math.cos(math.radians(45))
    slot = Pos(0, TLY + 13 * c45, TLZ + 13 * c45) * Rot(45, 0, 0) * Box(9.0, 5.0, 8.0)
    return b - slot


# ============================================================================================
# ARMS (left arm built, right mirrored)
# ============================================================================================

def egg_local(d=0.0):
    sph = Sphere(1.0)
    top = scale(sph & Pos(0, 0, 1) * Box(4, 4, 2), by=(HT_ - d, HW_ - d, C_TOP - d))
    bot = scale(sph & Pos(0, 0, -1) * Box(4, 4, 2), by=(HT_ - d, HW_ - d, C_BOT - d))
    return Pos(0, 0, ZC) * top.fuse(bot).clean()


def halfspace(p: Vector, n: Vector, size=300.0):
    pl = Plane(origin=p, z_dir=n)
    return pl.location * Pos(0, 0, size / 2) * Box(size, size, size)


def tip_plane():
    za = TIP_ZTOP - AX_Z
    ya = -HW_ * math.sqrt(max(0.0, 1 - ((za - ZC) / C_BOT) ** 2))
    A = Vector(0, ya, za)
    B = Vector(0, TIP_YB, ZC - C_BOT * math.sqrt(1 - (TIP_YB / HW_) ** 2))
    d = (B - A).normalized()
    m = Vector(0, -d.Z, d.Y)
    mid = (A + B) * 0.5 - Vector(0, 0, ZC)
    if m.dot(mid) < 0:
        m = -m
    t = math.radians(TIP_TILT)
    n = (m * math.cos(t) + Vector(-1, 0, 0) * math.sin(t)).normalized()
    return A, n


def round_split(s, x0, name, r=0.25):
    inner = egg_local(0.9)
    edges = [e for e in s.edges() if abs(e.bounding_box().min.X - x0) < 0.02 and
             abs(e.bounding_box().max.X - x0) < 0.02 and e.length > 2 and not inner.is_inside(e.position_at(0.5))]
    return try_fillet(s, edges, r, name)


def arm_left():
    loc = Pos(MID, AX_Y, AX_Z) * Rot(0, -SPLAY, 0)
    E0, Ei = egg_local(0.0), egg_local(ARM_WALL)
    shell = E0 - Ei
    A, n = tip_plane()
    hs_tip_out = halfspace(A + n * ARM_HS, n)
    hs_tip_cut = halfspace(A - n * ARM_HS, n)
    pos_x = bx(ARM_HS, 50, -50, 50, -80, 50)
    neg_x = bx(-50, -ARM_HS, -50, 50, -80, 50)
    # v8.2: seam R0.25 on the uncut halves, THEN the tip cut (with the +20 % egg the A01 seam edge ending on the
    # tip-cut face could not be filleted any more - fillet before booleans)
    a01 = round_split(shell & pos_x, ARM_HS, "A01 seam") - hs_tip_cut
    a02 = round_split(shell & neg_x, -ARM_HS, "A02 seam") - hs_tip_cut
    # snap lip: outer bodies united first, the inner egg subtracted once (v8.2: fusing two pieces that share the
    # inner egg_local(2.9) face produced an inverted solid)
    lip = ((egg_local(1.0) & bx(-1.5, -ARM_HS + 0.2, -50, 50, -80, 50)) +
           (egg_local(ARM_WALL + 0.05) & bx(-ARM_HS - 0.2, 2.5, -50, 50, -80, 50))) - egg_local(2.9)
    lip = lip - halfspace(A - n * 2.8, n)
    assert lip.is_valid and lip.volume > 0, "A02 lip"
    a02 = fuse(a02, lip, "A02 lip")
    plug = egg_local(ARM_WALL + 0.05) & (halfspace(A - n * 2.5, n) - halfspace(A + n * (ARM_HS + 0.4), n))
    tip = (E0 & hs_tip_out) + plug
    a01w, a02w, tipw = loc * a01, loc * a02, loc * tip
    # hub on the shoulder axis, CLIPPED INSIDE THE EGG (v8.0 bug: it stuck 225 mm3 out of the inner face)
    hub = cyl_x(AX_Y, AX_Z, HUB_R, HUB_X0, MID + 1.0) & (loc * neg_x) & (loc * egg_local(0.4))
    a02w = fuse(a02w, hub, "A02 hub")
    a02w = a02w - cyl_x(AX_Y, AX_Z, A04_R + 0.2, HUB_X0 - 5, A04_X1)
    for sy in (1, -1):
        a02w = a02w - cyl_x(sy * A04_SCREW_Y, AX_Z, 1.2, A04_X1 - 0.1, MID + 2)
        a02w = a02w - cyl_x(sy * A04_SCREW_Y, AX_Z, 2.1, A04_X1 + 1.2, MID + 2)
    tipw = tipw - cyl_x(AX_Y, AX_Z, HUB_R + 0.3, HUB_X0 - 5, MID + 2)
    # A04 joint coupler
    c = cyl_x(AX_Y, AX_Z, A04_R, A04_X0, A04_X1)
    c = try_fillet(c, c.faces().sort_by(Axis.X)[0].edges(), 0.5, "A04 edge")
    L, W, T = HORN_ARM
    rec = bx(A04_X0 - 1, A04_X0 + T + 0.1, -W / 2 - 0.15, W / 2 + 0.15, AX_Z - L / 2 + W / 2, AX_Z + L / 2 - W / 2) + \
        cyl_x(0, AX_Z - L / 2 + W / 2, W / 2 + 0.15, A04_X0 - 1, A04_X0 + T + 0.1) + \
        cyl_x(0, AX_Z + L / 2 - W / 2, W / 2 + 0.15, A04_X0 - 1, A04_X0 + T + 0.1) + \
        cyl_x(AX_Y, AX_Z, 3.7, A04_X0 - 1, A04_X0 + T + 0.1)
    c = c - rec - cyl_x(AX_Y, AX_Z, 1.2, A04_X0, A04_X1 + 1) - cyl_x(AX_Y, AX_Z, 2.3, A04_X0 + T + 1.2, A04_X1 + 1)
    for sy in (1, -1):
        c = c - cyl_x(sy * A04_SCREW_Y, AX_Z, 0.75, A04_X1 - 5, A04_X1 + 1)
    # A05 ring
    r = cyl_x(AX_Y, AX_Z, A05_RO, A05_X0, A05_X1) - cyl_x(AX_Y, AX_Z, A05_RI, A05_X0 - 1, A05_X1 + 1)
    r = try_fillet(r, [e for e in r.faces().sort_by(Axis.X)[-1].edges() if e.radius > A05_RO - 0.1], 0.5, "A05")
    out = dict(A01=one(a01w, "A01"), A02=one(a02w, "A02"), A03=one(tipw, "A03"), A04=c, A05=r)
    for k in ("A01", "A02"):                  # a lost half shell must never pass silently (v8.2 first pass)
        bb = out[k].bounding_box()
        assert bb.size.Z > 0.9 * EGG_L and bb.size.Y > 1.8 * HW_ * 0.95, f"{k} lost its shell: {bb.size}"
    return out


# ============================================================================================
# build
# ============================================================================================

def build():
    t0 = time.time()
    P = []

    def add(pid, name, shp, mat, sub, joint, expl, internal=False, note=""):
        n = len(shp.solids())
        if n != 1 and not pid[0] in "EM":
            print(f"   [WARN] {pid}: {n} solids (printed part should be one piece)")
        P.append(PartRec(pid, name, check(pid, shp), mat, sub, joint, expl, internal, note))

    # ---- torso shells ----
    add("T01", "Predná škrupina trupu", front_shell_t01(), "white", "torso", "J1", (0, -30, 0),
        note="jediná deliaca rovina y=0 (skrytá za rukami a pod golierom), predok bez škáry; 1 okno hrude, "
             "lišta za škárou, bloky serv rúk, 4 nálitky rámu T07, 3× M2 zospodu")
    add("T02", "Zadná škrupina trupu = servisný kryt", rear_shell_t02(), "white", "torso", "J1", (0, 30, 0),
        note="celý zadný diel je servisný kryt bez náradia: 2 horné jazýčky s poistkou, pero-drážka po škáre, "
             f"skrytá magnetická západka 2× Ø5 N52 do T04; zloženie: vysunúť {SLIDE:g} mm dozadu (pod golierom), "
             "potom zdvihnúť; žiadne skrutky, žiadne dvierka, žiadny viditeľný výrez")
    add("T04", "Otočný tanier trupu", plate_t04(), "black", "torso", "J1", (0, 0, -25),
        note=f"Ø{RING_OD:g}×{T04_H:g} + puzdro vonkajšieho krúžku 6806 (Ø42, osadenie Ø38.6 len na vonkajší krúžok) "
             f"na sedle základne (vrch z {YAW_BRG_Z1:g}), 6× M2 zápustné zospodu (hlavy 0.2 pod povrchom), 7 vetracích "
             "štrbín zospodu, 2 magnety západky T02")
    add("T05", "Dymové okno hrude (dead-front)", window_t05(), "glass", "torso", "J1", (0, -25, 0),
        note=f"{CH['w']:g}×{CH['h']:g} dymový PMMA prepúšťajúci IR (940 nm pre VL53L0X), zarovno s povrchom, z {CH['z']:g}, "
             "príruba za stenou; za ním LED pás + ToF + senzor svetla (zhasnuté = čierny lesklý pás)")
    add("T06", "Svit LED pásu cez dymové okno", glow_t06(), "cyan_led", "torso", "J1", (0, -25, 0),
        note="LEN VIZUALIZÁCIA: tyrkysový svetelný pás 24×1.6 svietiaci cez T05 (zhasnutý = neviditeľný)")
    print(f"  torso shells {time.time() - t0:.1f}s")

    # ---- neck ----
    add("N01", "Golier krku", collar_n01(), "black", "neck", "J1", (0, 0, 10),
        note=f"{CO['w']:g}×{CO['d']:g} (z {CO['z0']:g}–{CO['z1']:g}), úkos 22°, otvor Ø26.9 (škára 0.45 ku kužeľu), 2 kolíky "
             "+ VHB len na T01; spodok nad T02 odľahčený 0.2 (T02 sa vysunie bez trenia)")
    add("N02", "Kužeľ krku s čapom", cone_n02(), "black", "neck", "J2", (0, 0, 20),
        note="čap Ø25 v 6805, osadenie na vnútornom krúžku, 2× M2 zhora do N03 (skryté v hlave)")
    add("N06", "Valec náklonu", barrel_n06(), "black", "neck", "J2", (0, 0, 32),
        note=f"Ø{2 * BAR_R:g}×{BAR_L:g} na osi y {TLY:g} / z {TLZ:g}, rozhranie pre H09/H10 všetkých hláv; hladký "
             "(bez ozdobných drážok)")
    print(f"  neck {time.time() - t0:.1f}s")

    # ---- arms ----
    L = arm_left()
    for side, sx, j in (("R", -1, "J4"), ("L", 1, "J5")):
        g = {k: (v if sx > 0 else mirror(v, Plane.YZ)) for k, v in L.items()}
        sub = "arm_" + side
        nm = "pravá" if side == "R" else "ľavá"
        add(f"A01-{side}", f"Vonkajšia škrupina ruky {nm}", g["A01"], "white", sub, j, (sx * 30, 0, 0),
            note=f"vajce {EGG['top_z']:g}/{EGG['widest_z']:g}/{EGG['bottom_z']:g}, ½š {HW_:g}, ½h {HT_:g}, os ramena "
                 f"z {AX_Z:g}, stred x {MID:g}, odklon {SPLAY:g}°, stena {ARM_WALL:g}, hladká (bez falošnej drážky)")
        add(f"A02-{side}", f"Vnútorná škrupina ruky {nm}", g["A02"], "white", sub, j, (sx * 22, 0, 0),
            note=f"náboj Ø{2 * HUB_R:g} vo vnútri vajca s lôžkom A04, 2× M2 skryté pod A01, zámkový lem")
        add(f"A03-{side}", f"Špička ruky {nm}", g["A03"], "rubber", sub, j, (sx * 30, -8, -15),
            note="TPU, zátka zachytená medzi A01/A02, škára 0.5")
        add(f"A04-{side}", f"Spojka kĺbu ramena {nm}", g["A04"], "black", sub, j, (sx * 14, 0, 0),
            note=f"Ø{2 * A04_R:g}, skrátené rameno serva v drážke, axiálna skrutka M2")
        add(f"A05-{side}", f"Krúžok ramena {nm}", g["A05"], "black", sub, "J1", (sx * 7, 0, 0),
            note=f"Ø{2 * A05_RO:g}/Ø{2 * A05_RI:g}, 0.7 nad povrchom, vlepený do T01")
    print(f"  arms {time.time() - t0:.1f}s")

    # ---- internals ----
    add("T07", "Vnútorný rám trupu", frame_t07(), "grey", "torso", "J1", (0, 0, 18), True,
        note="PETG: puzdro 6805, koľajnice pan serva, krídla s blokmi serv rúk, 4× M2 do T01")
    add("T08", "Kolíska serva trupu", cradle_t08(), "grey", "torso", "J1", (0, 0, -8), True,
        note="PETG na T04 (3× M2 zospodu: stĺpik B, rohový nálitok, zadný stĺpik DPS): steny proti krútiacemu "
             "momentu STS3215, 2 stĺpiky lišty, drážky pre DPS")
    add("T09", "Prítlačná lišta serva", strap_t09(), "grey", "torso", "J1", (0, 0, 14), True,
        note="2× M2 do stĺpikov T08")
    add("N03", "Ozubené koleso krku 20z", hub_gear_n03(), "grey", "neck", "J2", (0, 0, 8), True,
        note="m1, 20 z, príruba Ø28.6 pod vnútorným krúžkom 6805")
    add("N04", "Ozubené koleso serva 20z", servo_gear_n04(), "grey", "neck", "J1", (0, 8, 8), True,
        note="m1, 20 z, na ramienku pan serva, prevod 1:1 (os 20 mm)")
    add("M21", "Ložisko 6806-2RS", bearing(YAW_BRG[0] / 2, YAW_BRG[1] / 2, YAW_BRG_Z1 - YAW_BRG[2], YAW_BRG_Z1),
        "metal", "torso", "J1", (0, 0, -12), True, note="30×42×7, vonkajší krúžok v T04, vnútorný na náboji základne")
    add("M22", "Ložisko 6805-2RS", bearing(PB_RI, PB_RO, PB_Z0, PB_Z1), "metal", "torso", "J1", (0, 0, 14), True,
        note="25×37×7 v T07, nesie hlavu")
    add("M23", "Magnety západky servisného krytu T02", magnets_m23(), "metal", "torso", "J1", (0, 22, -6), True,
        note="4× Ø5 N52: 2× 5×2 v T02, 2× 5×1.5 v T04 (opačná polarita) = skrytá západka zadného krytu")
    yaw = place(sts3215_local(), (0, 0, YS_Z0), (0, 0, -1), (1, 0, 0))
    add("E21", "Servo trupu Feetech STS3215", yaw, "servo", "torso", "J1", (0, 0, -4), True,
        note=f"45.2×24.7×35, drážkovanie DOLE na osi J1, telo z {YS_Z0:g}–{YS_Z1:g}, v kolíske T08 na T04")
    add("E21H", "Ramienko STS3215 (na náboji základne)", yaw_horn_e21h(), "metal", "torso", "", (0, 0, -16), True,
        note="disk Ø20, priskrutkovaný k náboju základne")
    for side, sx, j in (("R", -1, "J4"), ("L", 1, "J5")):
        sv = place(micro_servo_local(), (sx * ARM_TOP_X, AX_Y, AX_Z), (sx, 0, 0), (0, -1, 0))
        add(f"E22-{side}", f"Servo ruky MG90S {'pravé' if side == 'R' else 'ľavé'}", sv, "servo", "torso", "J1",
            (sx * 12, 0, 0), True, note="MG90S / SCS0009, predné ucho na bloku T01, zadné na krídle T07, 2× M2")
        add(f"E22H-{side}", "Ramienko serva ruky (skrátené)", horn_micro_x(sx), "white", "arm_" + side, j,
            (sx * 14, 0, 0), True)
    pan = place(micro_servo_local(), (0, PAN_SERVO_Y, PAN_TOP_Z), (0, 0, 1), (1, 0, 0))
    add("E23", "Servo otáčania hlavy MG90S", pan, "servo", "torso", "J1", (0, 14, 0), True,
        note="v koľajniciach T07, ozubený prevod 1:1 na krk")
    add("E23H", "Ramienko pan serva", pan_horn_e23h(), "white", "torso", "J1", (0, 14, 6), True)
    add("E24", "Riadiaca DPS (ESP32-C3 SuperMini + MP1584 5 V + budič zbernice)", controller_e24(), "pcb", "torso", "J1", (0, 18, 0),
        True, note="48×18.5 v drážkach T08, prístup po vysunutí zadného krytu T02")
    add("E25", "Predná DPS (5× WS2812B-2020 + VL53L0X + ALS)", front_board_e25(), "pcb", "torso", "J1",
        (0, -14, 0), True, note="na 2 nálitkoch T01, všetko za jedným dymovým oknom T05")
    print(f"  internals {time.time() - t0:.1f}s")
    return P


# ============================================================================================
# checks
# ============================================================================================

def _bb_apart(ba, bb):
    return ba.min.X > bb.max.X or bb.min.X > ba.max.X or ba.min.Y > bb.max.Y or bb.min.Y > ba.max.Y or \
        ba.min.Z > bb.max.Z or bb.min.Z > ba.max.Z


def interference(parts, others=(), tol=0.5):
    allp = list(parts) + list(others)
    own = {p.id for p in parts}
    bad = []
    for i in range(len(allp)):
        for j in range(i + 1, len(allp)):
            a, b = allp[i], allp[j]
            if a.id not in own and b.id not in own:
                continue
            if _bb_apart(a.shape.bounding_box(), b.shape.bounding_box()):
                continue
            try:
                ab = a.shape & b.shape
                v = 0.0 if ab is None else ab.volume
            except Exception:  # noqa: BLE001
                v = -1
            if v > tol or v < 0:
                bad.append((a.id, b.id, round(v, 2)))
    return bad


def _rot_pr(p, shape):
    return PartRec(p.id, p.name, shape, p.mat, p.sub, p.joint, p.explode, p.internal, p.note)


# cad_internals.SUPERSEDED (copy used only when that module cannot be imported)
_SUPERSEDED_FALLBACK = ["BE1-1", "BE1-2", "BE2", "BE3", "BE4", "BE5", "BE6", "BM2-L", "BM2-R", "BM5", "BW1", "E21",
                        "E21H", "E22-L", "E22-R", "E22H-L", "E22H-R", "E23", "E23H", "E24", "E25", "E31", "E32",
                        "E33-L", "E33-R", "M21", "M22"]


def superseded():
    try:
        from nova_v8 import cad_internals as CI
        return set(CI.SUPERSEDED)
    except Exception as ex:  # noqa: BLE001
        print(f"  [cad_internals not importable ({str(ex)[:60]}) - SUPERSEDED fallback list]")
        return set(_SUPERSEDED_FALLBACK)


def motion_check(parts, others=(), tol=0.5, sup=()):
    """Sweep the joints in CAD and report collisions (SUPERSEDED envelopes and deforming cables excluded).
       arms J4/J5 -30..180 vs torso + base + head at pose 0;  pan J2 +-90 (cone, barrel and the whole head of every
       loaded head variant) vs the torso + the arms at 0;  J1 +-150 (torso + arms + neck + head) vs the base."""
    sup = set(sup)
    allp = [p for p in list(parts) + list(others) if p.id not in sup]
    own = {p.id for p in parts}
    out = []

    def hit(a, b):
        if _bb_apart(a.bounding_box(), b.bounding_box()):
            return 0.0
        try:
            i = a & b
            return 0.0 if i is None else i.volume
        except Exception:  # noqa: BLE001
            return -1.0

    cable = ("IW", "BW")
    fixed_t = [p for p in allp if p.joint == "J1" and not p.id.startswith(cable)]
    upper = [p for p in allp if p.joint in ("J2", "J3") and not p.id.startswith(cable)]
    base = [p for p in allp if p.joint == "" and p.id not in ("E21H", "IT02", "IT03") and not p.id.startswith(cable)]
    arms = [p for p in allp if p.joint in ("J4", "J5")]
    for side, j in (("L", "J5"), ("R", "J4")):
        mov = [p for p in allp if p.joint == j]
        ax = Axis((0, AX_Y, AX_Z), (1, 0, 0))
        for ang in (-30, 0, 30, 60, 90, 120, 135, 150, 165, 180):
            for m in mov:
                sh = m.shape.rotate(ax, -ang)
                for f in fixed_t + base + upper:
                    if m.id not in own and f.id not in own:
                        continue
                    v = hit(sh, f.shape)
                    if v > tol or v < 0:
                        out.append((f"{j}={ang}", m.id, f.id, round(v, 1)))
    mov = [p for p in allp if p.joint in ("J2", "J3") and p.id not in ("N03",) and not p.id.startswith(cable)]
    for ang in (-90, -60, -30, 30, 60, 90):
        for m in mov:
            sh = m.shape.rotate(Axis.Z, ang)
            for f in fixed_t + arms:
                if m.id not in own and f.id not in own:
                    continue
                if f.id == "N04" or m.id == "N04":
                    continue                       # 1:1 gear pair turns together with the stage
                v = hit(sh, f.shape)
                if v > tol or v < 0:
                    out.append((f"J2={ang}", m.id, f.id, round(v, 1)))
    rot = [p for p in allp if p.joint in ("J1", "J2", "J3", "J4", "J5") and not p.id.startswith(cable)]
    for ang in (-150, -120, -90, -45, 45, 90, 120, 150):
        for m in rot:
            sh = m.shape.rotate(Axis.Z, ang)
            for f in base:
                if m.id not in own and f.id not in own:
                    continue
                v = hit(sh, f.shape)
                if v > tol or v < 0:
                    out.append((f"J1={ang}", m.id, f.id, round(v, 1)))
    return out


OTHER_BUILDS = [("build_v8", None), ("build_v8_var_aplus", ("head_aplus",)), ("build_v8_var_b", ("head_b",))]
OTHER_INFO: dict = {}


def other_modules(stand_in=False):
    """Parts of the other v8 modules = their CURRENT exported builds (manifest + STEP in build_v8 / head-variant
    dirs).  Stale v8.1 builds are reported; with stand_in=True they are replaced by v8.2 stand-ins where that is an
    exact move: heads +13 (HEAD.z0 117 -> 130, size unchanged), base yaw seat/hub B09 B14 B15 B17 -4 (base top
    39 -> 35, interface unchanged in plan; B01/B02 resized -> left out), internals left out."""
    import json
    from build123d import import_step
    out = []
    for d, only in OTHER_BUILDS:
        mdir = os.path.join(ROOT, d, "manifest")
        for fn in sorted(os.listdir(mdir)) if os.path.isdir(mdir) else []:
            name = fn[:-5]
            if not fn.endswith(".json") or name == MANIFEST or (only and name not in only):
                continue
            if name.startswith("concept"):
                continue
            recs = json.load(open(os.path.join(mdir, fn)))
            bb = {r["id"]: r["bbox"] for r in recs}
            dz, stale, keep = 0.0, False, None
            if name.startswith("head"):
                shell = next((r for r in recs if r["joint"] == "J3" and r["id"].endswith("01")), None)
                z0 = shell["bbox"]["min"][2] if shell else S.HEAD["z0"]
                stale = abs(z0 - S.HEAD["z0"]) > 0.5
                dz = S.HEAD["z0"] - z0
            elif name == "base" and "B01" in bb:
                ztop = bb["B01"]["min"][2] + bb["B01"]["size"][2]
                stale = abs(ztop - BS["z1"]) > 0.3
                dz = BS["z1"] - ztop
                keep = {"B09", "B14", "B15", "B17"}
            elif name == "internals" and "IN03" in bb and "IT04" in bb:
                # its 6805 / 6806 must sit where this module puts M22 / M21
                stale = abs(bb["IN03"]["min"][2] - PB_Z0) > 0.3 or \
                    abs(bb["IT04"]["min"][2] - (YAW_BRG_Z1 - YAW_BRG[2])) > 0.3
                keep = set()
            mt = time.ctime(os.path.getmtime(os.path.join(mdir, fn)))
            OTHER_INFO[name] = dict(dir=d, mtime=mt, parts=len(recs), stale=stale, dz=round(dz, 2))
            if stale and not stand_in:
                print(f"  [{name}] STALE (v8.1) build {mt} - skipped (use --stand-in for v8.2 stand-ins)")
                continue
            got = []
            for r in recs:
                if stale and keep is not None and r["id"] not in keep:
                    continue
                p = os.path.join(ROOT, d, "step", f"{r['id']}.step")
                if not os.path.exists(p):
                    continue
                shp = import_step(p)
                if stale and abs(dz) > 1e-6:
                    shp = Pos(0, 0, dz) * shp
                got.append(PartRec(r["id"], r["name"], shp, r["mat"], r["sub"], r["joint"], tuple(r["explode"]),
                                   r["internal"], r["note"]))
            tag = f"STAND-IN (v8.1 moved {dz:+.1f} in z)" if stale else "current"
            print(f"  [{name}] {len(got)} STEP parts, {tag}, {mt}")
            out += got
    return out


def cross_interference(parts, others, sup, tol=0.5):
    """Own parts vs the other modules, SUPERSEDED envelopes excluded on both sides."""
    own = [p for p in parts if p.id not in sup]
    oth = [p for p in others if p.id not in sup]
    bad = []
    for a in own:
        ba = a.shape.bounding_box()
        for b in oth:
            if _bb_apart(ba, b.shape.bounding_box()):
                continue
            try:
                ab = a.shape & b.shape
                v = 0.0 if ab is None else ab.volume
            except Exception:  # noqa: BLE001
                v = -1
            if v > tol or v < 0:
                bad.append((a.id, b.id, round(v, 2)))
    return bad


def step_roundtrip(ids=None):
    from build123d import import_step
    bad = []
    import json
    recs = json.load(open(os.path.join(OUT_DIR, "manifest", f"{MANIFEST}.json")))
    for r in recs:
        if ids and r["id"] not in ids:
            continue
        s = import_step(os.path.join(OUT_DIR, "step", f"{r['id']}.step"))
        ok = all(q.is_valid for q in s.solids()) and abs(s.volume - r["volume_mm3"]) < max(0.5, 2e-3 * r["volume_mm3"])
        if not ok:
            bad.append((r["id"], round(s.volume, 1), r["volume_mm3"]))
    return bad


def spec_report(ps):
    """Key v8.2 numbers measured on the CAD."""
    by = {p.id: p.shape.bounding_box() for p in ps}
    t01, t02, t04 = by["T01"], by["T02"], by["T04"]
    w = max(t01.max.X, t02.max.X) - min(t01.min.X, t02.min.X)
    d = max(t01.max.Y, t02.max.Y) - min(t01.min.Y, t02.min.Y)
    a = by["A01-L"].max.X - by["A01-R"].min.X
    rows = [("torso w x d (shells)", f"{w:.2f} x {d:.2f}", f"{TS['w']:g} x {TS['d']:g}"),
            ("white shells z / T04 top", f"{min(t01.min.Z, t02.min.Z):.2f} .. {max(t01.max.Z, t02.max.Z):.2f} / "
             f"{t04.max.Z:.2f}", f"{Z_SH:g} .. {T_Z1:g} / {Z_SH:g} (torso {T_Z0:g}..{T_Z1:g})"),
            ("T04 disc / housing bottom", f"Ø{t04.max.X - t04.min.X:.2f} / z {t04.min.Z:.2f}", f"Ø{RING_OD:g}"),
            ("collar N01 w x d, z", f"{by['N01'].max.X - by['N01'].min.X:.2f} x {by['N01'].max.Y - by['N01'].min.Y:.2f}, "
                                    f"z {by['N01'].min.Z + 1.4:.2f}..{by['N01'].max.Z:.2f}",
             f"{CO['w']:g} x {CO['d']:g}, {CO['z0']:g}..{CO['z1']:g}"),
            ("cone N02 top", f"{by['N02'].max.Z:.2f}", f"{CN['z1']:g}"),
            ("barrel N06 top / x-length", f"{by['N06'].max.Z:.2f} / {by['N06'].max.X - by['N06'].min.X:.2f}",
             f"{TLZ + BAR_R:g} (axis z {TLZ:g}) / {BAR_L:g}"),
            ("arm A01-L+A02-L z", f"{min(by['A01-L'].min.Z, by['A02-L'].min.Z):.2f} .. "
                                  f"{max(by['A01-L'].max.Z, by['A02-L'].max.Z):.2f}",
             f"{EGG['bottom_z']:g} .. {EGG['top_z']:g} (splay 8 deg)"),
            ("arm span (A01 outer faces)", f"{a:.2f}", f"OVERALL.w_arms {S.OVERALL['w_arms']:g}"),
            ("E21 STS3215 z", f"{by['E21'].min.Z:.2f} .. {by['E21'].max.Z:.2f}", f"{YS_Z0:g} .. {YS_Z1:g} (+boss/cable)"),
            ("M21 6806 z", f"{by['M21'].min.Z:.2f} .. {by['M21'].max.Z:.2f}", f"top {YAW_BRG_Z1:g}"),
            ("M22 6805 z", f"{by['M22'].min.Z:.2f} .. {by['M22'].max.Z:.2f}", f"under the top wall {T_Z1 - WALL:g}")]
    for r in rows:
        print(f"   {r[0]:36s} CAD {r[1]:34s} spec {r[2]}")


def load_own_step():
    """This module's parts from its exported STEP (re-run the checks without rebuilding: --from-step)."""
    import json
    from build123d import import_step
    recs = json.load(open(os.path.join(OUT_DIR, "manifest", f"{MANIFEST}.json")))
    ps = [PartRec(r["id"], r["name"], import_step(os.path.join(OUT_DIR, "step", f"{r['id']}.step")), r["mat"],
                  r["sub"], r["joint"], tuple(r["explode"]), r["internal"], r["note"]) for r in recs]
    return ps, recs


def service_check(ps, slides=(SLIDE,), lifts=(0.0, 2.0, 10.0)):
    """Rear cover T02 removal: slide +Y, then lift +Z - collisions with every other part of this module."""
    t02 = next(p for p in ps if p.id == "T02").shape
    rest = [p for p in ps if p.id != "T02"]
    out = []
    for sl in slides:
        for lf in lifts:
            m = Pos(0, sl, lf) * t02
            bm = m.bounding_box()
            for p in rest:
                if _bb_apart(bm, p.shape.bounding_box()):
                    continue
                i = m & p.shape
                v = 0.0 if i is None else i.volume
                if v > 0.01:
                    out.append((f"slide {sl:g} lift {lf:g}", p.id, round(v, 2)))
    return out


if __name__ == "__main__":
    t0 = time.time()
    if "--from-step" in sys.argv:
        ps, recs = load_own_step()
        print(f"  loaded {len(ps)} own parts from STEP ({OUT_DIR})")
    else:
        ps = build()
        recs = export_parts(ps, MANIFEST, step=True, out_dir=OUT_DIR)
        for r in recs:
            print(f"  {r['id']:7s} {r['mat']:9s} {r['sub']:6s} {r['joint']:3s} {'int' if r['internal'] else '   '} "
                  f"size={r['bbox']['size']} min={r['bbox']['min']} vol={r['volume_mm3']}")
        print("STEP round-trip problems:", step_roundtrip())
    print("spec check:")
    spec_report(ps)
    if "--check" in sys.argv:
        print("interference (own):", interference(ps))
        print(f"T02 removal (slide +Y to {SLIDE:g}, then lift +Z; M23 = the T02 magnets that travel with it, "
              "T01 at mid-slide = the snap bump):",
              service_check(ps, slides=(TONGUE_RELEASE / 2, TONGUE_RELEASE, 12.0, SLIDE), lifts=(0.0,)) +
              service_check(ps, slides=(SLIDE,), lifts=(1.0, 5.0, 15.0, 40.0)))
        if "--others" in sys.argv or "--motion" in sys.argv:
            sup = superseded()
            oth = other_modules(stand_in="--stand-in" in sys.argv)
            print("other builds:", OTHER_INFO)
            print("interference vs other modules (SUPERSEDED excluded):", cross_interference(ps, oth, sup))
            if "--motion" in sys.argv:
                print("motion:", motion_check(ps, oth, sup=sup))
        elif "--motion-own" in sys.argv:
            print("motion (own parts only):", motion_check(ps, (), sup=()))
    print("deviations:\n  - " + "\n  - ".join(DEVIATIONS))
    print(f"[{MANIFEST}] {len(recs)} parts in {time.time() - t0:.1f}s -> {OUT_DIR}")

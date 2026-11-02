"""
NOVA – master specification (single source of truth).

ALL dimensions in millimetres.  Coordinate system (used by CAD and by renders):
  * Z up.  Origin = floor contact plane of the bottom plate B02, centre of the base footprint.
  * Robot FRONT faces  -Y  (front view camera sits at -Y looking +Y).
  * Robot RIGHT side   = -X  (appears on the LEFT of a front view).
  * Robot LEFT side    = +X.
  * Default pose = every joint at 0 deg: head looks straight forward, arms hang down.

Pure Python (no dependencies) so it can be imported both by the build123d CAD
scripts (/opt/venv/cad) and by the Blender render scripts (/opt/venv/bl).

=====================================================================================
CHANGELOG v7.1  (after the mechatronics review)  – THESE NUMBERS SUPERSEDE ANY NUMBER
QUOTED IN OLDER TASK BRIEFS.  Always read values from this file.
  * Base is 6 mm taller (z1 36 -> 42; matches the target photo and fits the J1 drive).
    EVERYTHING above the base moved up +6 mm: torso 43..145, collar top 151.5,
    tilt axis z=184, head 172..268, shoulder axis z=118, arm egg z +6, all torso/head
    feature heights +6.
  * Neck tilt housing N06: barrel Ø40 x 36 (was Ø30 x 48), NO stem – the N02 cone top
    (r 12.5 at z 168) meets the barrel underside; hub caps N07 Ø39 x 6 (gap 0.6);
    total width 49.2.  Cable passage at the cone/barrel junction 14x8.
    Tilt servo sits on the tilt axis inside the barrel; passive side = 6703 bearing on a
    hollow pin (ID 13) for the cable bundle + flat spiral gravity-compensation spring.
  * Head underside recess 58 x 56 R14, depth 34 (clears tilt -20/+30 and the Ø39 caps).
    Head vents moved to the front underside (y≈-37), two groups of 3 slots.
  * Bezel 124 x 92 (was 88), glass 108 x 82 (was 76), display centre / eyes z=218,
    camera hole z=256.4 (3 mm glass margin).
  * Collar N01: outer edge height 2.0 (sloped flange), bore 37 for the 61805 pan bearing.
  * Torso rear door 76 x 80 with LOW inlet vents + top exhaust vents (Pi 5 cooling).
  * Base: GM3506 moved off-axis with a GT2 belt (4.5:1); slip ring on the yaw axis;
    slim speaker lying flat, rear grille 3 x 15 holes Ø2.5.
  * Joint sign conventions defined (see JOINTS). Arms above 125° only with head pan = 0.

CHANGELOG v7.2  (after the design-fidelity review of the target photo R01) – SUPERSEDES v7.1
  * BASE smaller & tighter: 166 x 128, plan corner R24, LED 44 wide at z=20.
  * TORSO 112 x 92, z 43..142 (99 tall).  NEW STRUCTURE (see TORSO dict):
      - T04 is now a VISIBLE black bottom TRAY 100 x 80, z 43..47.5 (a 4.5 mm black band under
        the white body, like R01); the white shell starts at z=47.5 with a small R8 bottom rounding.
      - T01 is a CENTRE BAND |x|<=35 running front -> over the top -> down the back (seams at
        x=±35 run full depth, NO cross seam on top).  At the front, T01 drops down over the
        tray to z=43.  T02-R / T02-L are the two SIDE SHELLS (they carry the shoulder bores).
      - T03 rear door 60 x 76 sits inside the band on the back.
      - LED 34x4 at z=100, sensor window 23x4 at z=83.5, shoulder axis z=115.
  * NECK: collar 52 x 42 (sloped flange, edge 2.0), cone r 16.5 -> 11.5 (z 149..165),
    tilt axis z=181, barrel Ø40 x 36 + caps Ø39 x 6 (mechatronics fix kept).
  * HEAD z 169..265 (zc 217): depth reduced (white shell y -46..+44, back R28), front-view
    corner R32; bezel 127 x 91 R30 protruding 7 mm (2.5 mm white rim all round); glass
    119 x 79 R22 centred z=216 (top band 7, bottom 5); display zc 211.5; camera window z 250.5;
    eyes 13 x 21.5 R6.5 at x=±12, z=209.5; ears protrude 5.5 at y=-4, z=213; back cover
    112 x 66 R20; neck recess 56 x 56 R16 depth 34.
  * ARMS: slimmer & shorter egg (half_w 16, half_t 8.5; top 127, widest 87, bottom 53),
    splay 8°; joint cover x 57.5..68.5; mid_x 73.9.  BLACK TIP A03 is on the INNER side
    (toward the torso), lower front, wrapping under the bottom; A01 outer shell is fully white.

CHANGELOG v7.3  (after the manufacturing/assembly review – details in docs/REVIEW_NOTES.md)
  * Tilt barrel N06 Ø42 (SCS0009 corner r 18.19 needs inner Ø38), caps N07 Ø41; each N07 has a
    Ø18 hub that passes through a Ø18.4 hole in the head-recess side wall into the head frame H11.
    Head recess depth 35.  N02 is ONE piece (no seams).
  * Glass print: top border 9 mm (camera window fully inside the printed band), others 4.
    Bezel corner R29.5 (uniform 0.3 mm gap to H01).
  * T01 band: the BACK also drops straight down to z=43 as an apron (like the front); the R8
    bottom rounding exists only on the side shells T02-R/L (mouldable with a -Z core pull).
    Tray screws moved off the seams.  Rear door 60 x 84 at zc=96 (Pi access); vent rows are
    explicit z lists.
  * Base: cells at x=-38/-58, NEW B08 battery hatch in B02 (42x76 R4 at x=-48), B02 screws at
    (±75,0), feet at (±62,±48), USB-C opening 12.6 x 6.8 R3.4 (plug overmold fits).
  * A04 starts at |x|=57.8 (0.8 mm rotating gap to A05).
  * v7.3b (R01 matched-camera comparison): torso plan exponent n 3.2 -> 2.7 (rounder corners);
    arm paddle longer & wider (top 130, widest 86, bottom 49, half_w 17.5) – R01 arms reach down
    almost to the torso bottom.
  * IDs: ASCII -R/-L suffixes everywhere.  H04C (camera window) and H04E (eyes) are RENDER-ONLY
    objects, not parts.  Internal part numbers: see docs/REVIEW_NOTES.md §Internal part numbers.
=====================================================================================
"""
from math import sqrt

NAME = "NOVA"
VERSION = "v7.3"
DZ = 6.0                  # global lift applied in v7.1 (kept for reference)

# ---------------------------------------------------------------------------
# Overall stack (Z levels)
# ---------------------------------------------------------------------------
FLOOR_Z = -1.2            # underside of rubber feet B04 (renders put the floor here)
BASE_Z0, BASE_Z1 = 0.0, 42.0          # base: bottom plate underside .. top surface
TORSO_Z0, TORSO_Z1 = 43.0, 142.0      # torso: tray bottom (1 mm gap above base top) .. top
NECK_COLLAR_Z1 = 148.5                # top of N01 collar
TILT_AXIS = dict(y=0.0, z=181.0)      # head-tilt (pitch) axis, parallel to X
PAN_AXIS = dict(x=0.0, y=0.0)         # head-pan (yaw) axis, vertical
HEAD_Z0, HEAD_Z1 = 169.0, 265.0       # head outer shell bottom .. top
OVERALL = dict(w=166.0, d=128.0, h=HEAD_Z1 - FLOOR_Z)   # ~266 mm tall; width over the arms ~173

# ---------------------------------------------------------------------------
# Materials (keys used by CAD part records and by the Blender material library)
# ---------------------------------------------------------------------------
MATERIALS = {
    "white":      dict(desc="biely lesklo-satén PC/ABS (RAL 9003)", rgb=(0.93, 0.93, 0.92), rough=0.28, clearcoat=0.35),
    "black":      dict(desc="čierny soft-touch (RAL 9005 mat)",     rgb=(0.008, 0.008, 0.009), rough=0.30, spec=0.30),
    "black_satin":dict(desc="čierny saténový plast (kryty krku)",   rgb=(0.010, 0.010, 0.011), rough=0.45, spec=0.35),
    "black_gloss":dict(desc="čierny lesklý plast",                   rgb=(0.02, 0.02, 0.022), rough=0.15),
    "rubber":     dict(desc="čierne TPU 85A / guma",                 rgb=(0.022, 0.022, 0.024), rough=0.75, spec=0.3),
    "glass":      dict(desc="tvrdené sklo 1.1 mm, čierna potlač",    rgb=(0.004, 0.004, 0.005), rough=0.015),
    "cyan_led":   dict(desc="svetlovod PMMA opál – tyrkysová LED",   rgb=(0.0, 0.88, 1.0), emit=2.2),
    "eye":        dict(desc="obsah displeja – oči (teplá biela)",    rgb=(1.0, 0.76, 0.46), emit=1.3),
    "frost":      dict(desc="matný svetlosivý PMMA (okienko senzora)", rgb=(0.80, 0.81, 0.82), rough=0.6),
    "grey":       dict(desc="sivý technický plast (vnútorná kostra)", rgb=(0.35, 0.36, 0.38), rough=0.5),
    "pcb":        dict(desc="DPS zelená/čierna",                     rgb=(0.03, 0.18, 0.08), rough=0.4),
    "metal":      dict(desc="hliník / oceľ",                         rgb=(0.75, 0.76, 0.78), rough=0.25, metallic=1.0),
    "servo":      dict(desc="servo – telo čierne/modré",              rgb=(0.05, 0.08, 0.18), rough=0.45),
    "battery":    dict(desc="článok 18650 (fólia)",                  rgb=(0.10, 0.35, 0.65), rough=0.35),
    "display":    dict(desc="LCD modul",                             rgb=(0.04, 0.04, 0.05), rough=0.3),
}

# ---------------------------------------------------------------------------
# BASE  (B)  – the robot stands permanently on it; it is the heavy, stable
#              power/sound module and the body-yaw turntable.
# ---------------------------------------------------------------------------
BASE = dict(
    w=166.0, d=128.0, plan_r=24.0,       # plan rounded rectangle
    z0=BASE_Z0, z1=BASE_Z1,
    plate_h=4.0, plate_inset=3.0,         # B02 black bottom plate, inset from white shell
    shell_wall=2.5, top_fillet=10.0, bottom_fillet=2.0,
    turntable_d=92.0, turntable_recess=2.0,   # recessed seat on top face under the torso (B05 disc sits in it)
    led=dict(w=44.0, h=4.0, r=2.0, z=20.0),   # B03 front light guide (cyan)
    grille=dict(rows=3, cols=15, hole_d=2.5, pitch=4.0, z=(10.0, 14.0, 18.0), xc=20.0),  # rear speaker grille
    usb_c=dict(w=12.6, h=6.8, x=-36.0, z=18.0),                        # rear opening (receptacle recessed 1.2)
    button=dict(d=7.0, x=-22.0, z=18.0),                                # power button, rear
    feet=dict(d=14.0, h=1.2, xy=[(62, 48), (-62, 48), (62, -48), (-62, -48)]),
    screws=dict(d=3.0, xy=[(75, 0), (-75, 0), (0, 52), (0, -52)]),      # M3 into heat-set inserts
    battery_hatch=dict(w=42.0, d=76.0, r=4.0, x=-48.0, y=0.0),         # B08 in B02 (EU 2023/1542)
    # internal layout (v7.1)
    yaw_bearing=dict(id=40.0, od=52.0, w=7.0),          # 6808-2RS on the yaw axis under the top
    yaw_motor=dict(x=48.0, y=0.0, d=40.0, h=20.0),      # GM3506 off-axis, GT2 belt 16T -> 72T
    batteries=dict(x=(-38.0, -58.0), y=0.0, d=18.5, len=65.0),   # 2x 18650 along Y, above the hatch
    speaker=dict(x=26.0, y=40.0, d=36.0, h=6.0),        # slim speaker lying flat, ducted to rear grille
)

# ---------------------------------------------------------------------------
# TORSO (T)  – plan section is a superellipse |x/a|^n + |y/b|^n = 1
# ---------------------------------------------------------------------------
TORSO = dict(
    z0=TORSO_Z0, z1=TORSO_Z1,             # z0 = underside of the black tray T04
    shell_z0=47.5,                        # white shell starts above the 4.5 mm tray band
    w=112.0, d=92.0, n=2.7,               # main section (between the roundings); n 2.7 = softer "pillow" corners (R01)
    r_bottom=8.0, r_top=22.0,             # vertical roundings of the WHITE shell (bottom at shell_z0)
    wall=2.4,
    # T01 centre band |x|<=35, front + top + back, seams at x=±35 full depth; at the front it
    # continues down over the tray to z0.  T02-R/T02-L = side shells (|x|>35) with the shoulders.
    band=dict(half_w=35.0, seam=0.6),
    rear_door=dict(w=60.0, h=84.0, r=12.0, zc=96.0, seam=0.6,  # T03 inside the band, on the back (z 54..138)
                   vents=dict(w=28.0, h=2.0, z=(128.0, 124.0, 120.0, 116.0, 112.0)),   # top exhaust rows
                   vents_low=dict(w=28.0, h=2.0, z=(64.0, 68.0, 72.0, 76.0))),         # low inlet rows
    band_apron=dict(front=True, back=True, bottom_fillet=2.0),   # T01 drops straight to z0 front AND back
    tray=dict(w=100.0, d=80.0, h=4.5, n=3.2, screw_xy=[(28, 22), (-28, 22), (28, -22), (-28, -22)],
              band_screw_xy=[(0, 34), (0, -34)], j1_screw_pcd=32.0,
              center_hole_d=20.0),       # T04 visible black bottom tray (z0 .. z0+h)
    led=dict(w=34.0, h=4.0, r=2.0, z=100.0),     # T05 cyan light guide on the band (front)
    sensor=dict(w=23.0, h=4.0, r=2.0, z=83.5),   # T06 frosted window (ToF + ambient light)
    shoulder=dict(z=115.0, y=0.0, bore_d=23.0, cbore_d=31.4, cbore_depth=1.5),
    neck_hole_d=34.0,
)


def torso_section(z):
    """Outer superellipse half-axes (a, b) of the WHITE torso shell at height z (quarter-round roundings).
    Valid for shell_z0 <= z <= z1."""
    t = TORSO
    a0, b0 = t["w"] / 2, t["d"] / 2
    shrink = 0.0
    zb = t.get("shell_z0", t["z0"]) + t["r_bottom"]
    zt = t["z1"] - t["r_top"]
    if z < zb:
        r = t["r_bottom"]; u = (zb - z) / r
        shrink = r * (1 - sqrt(max(0.0, 1 - u * u)))
    elif z > zt:
        r = t["r_top"]; u = (z - zt) / r
        shrink = r * (1 - sqrt(max(0.0, 1 - u * u)))
    return a0 - shrink, b0 - shrink

# ---------------------------------------------------------------------------
# NECK (N)
# ---------------------------------------------------------------------------
NECK = dict(
    collar=dict(w=52.0, d=42.0, z0=TORSO_Z1, z1=NECK_COLLAR_Z1, bore_d=32.0, lip_d=35.0, lip_h=1.2,
                edge_h=2.0),                                                 # N01 fixed, sloped flange
    pan_bearing=dict(id=25.0, od=37.0, w=7.0, z0=132.6),                     # 61805-2RS in a boss under the torso top
    cone=dict(z0=149.0, z1=165.0, r_bottom=16.5, r_top=11.5, wall=2.0),     # N02 trumpet, pans, ONE piece
    tilt_housing=dict(barrel_d=42.0, barrel_len=36.0, stem_d=0.0,
                      cable_slot=(14.0, 8.0)),                              # N06 barrel, pans (no stem)
    caps=dict(d=41.0, len=6.0, dome=1.5, gap=0.6, hub_d=18.0, hub_len=5.8), # N07 L/R caps (tilt with head) + Ø18 hub into H11
    pan_range=(-90, 90), tilt_range=(-20, 30),
)

# ---------------------------------------------------------------------------
# HEAD (H)
# ---------------------------------------------------------------------------
HEAD = dict(
    w=132.0, d=90.0, h=96.0, y0=-46.0, y1=44.0,       # white shell from front rim (y=-46) to back (y=+44)
    z0=HEAD_Z0, z1=HEAD_Z1, zc=(HEAD_Z0 + HEAD_Z1) / 2,  # zc = 217
    r_front_view=32.0,           # corner radius of the silhouette seen from the front (edges // Y)
    r_back=28.0,                 # rounding of the back edge loop
    r_front_rim=2.0,             # rounding of the white rim around the bezel
    wall=2.2,
    bezel=dict(w=127.0, h=91.0, r=29.5, protrude=7.0, front_fillet=3.0, depth=16.0),   # H03 black frame
    glass=dict(w=119.0, h=79.0, r=22.0, t=1.1, recess=1.0, print_border=4.0, print_top=9.0, zc=216.0),  # H04
    camera=dict(hole_d=3.2, z=250.5, module=(8.5, 8.5, 5.0)),                          # unprinted window; USB UVC module
    display=dict(outline=(105.5, 67.2, 4.0), active=(95.04, 53.86), zc=211.5),         # 4.3" RGB 800x480
    eyes=dict(w=13.0, h=21.5, r=6.5, x=12.0, z=209.5),                                 # default expression
    ear=dict(d=36.0, protrude=5.5, y=-4.0, z=213.0, ring_od=30.0, ring_id=23.0, mic_hole_d=1.0),  # H05 + H06
    back_cover=dict(w=112.0, h=66.0, r=20.0, seam=0.6),                                # H02
    neck_recess=dict(w=56.0, d=56.0, r=16.0, depth=35.0, hub_hole_d=18.4),
    vents=dict(n=3, w=16.0, h=1.6, pitch=4.0, y=-37.0, x=(-20.0, 20.0)),   # underside front, 2 groups
)
# front of black bezel  y = HEAD["y0"] - bezel.protrude = -53.0 ; glass front y = -52.0

# ---------------------------------------------------------------------------
# ARMS (A) – right arm on -X, left arm mirrored on +X
# ---------------------------------------------------------------------------
ARM = dict(
    axis=dict(y=0.0, z=115.0),               # shoulder pitch axis // X
    abduction_deg=8.0,                       # paddle splayed outward at the bottom (R01)
    egg=dict(top_z=130.0, widest_z=86.0, bottom_z=49.0, half_w=17.5, half_t=8.5),   # default pose, before splay
    mid_x=73.9,                              # |x| of the split plane (A01/A02) at the joint
    joint_cover=dict(od=26.0, x0=57.8, x1=68.5, spigot_od=22.0, spigot_len=3.0, bore_d=14.0),  # A04
    ring=dict(od=31.0, id=23.0, t=2.5, x_out=57.0),                                           # A05 (torso |x|=56)
    boss=dict(od=26.0, id=22.4),            # on A02 inner shell
    tip=dict(side="inner", z_top=65.0, y_max=2.0, wrap_bottom=True),   # A03 black crescent, INNER lower front
    range=(-30, 180),
    free_range=(-30, 125),                   # above 125° only while |head pan| <= 2° (firmware interlock)
)

# ---------------------------------------------------------------------------
# Kinematics summary (5 DOF).  Sign conventions (used by renders):
#   J1 +  body turns to the robot's LEFT (counter-clockwise seen from above)
#   J2 +  head turns to the robot's LEFT (+X)
#   J3 +  head looks UP (nose-up);  range -20 (down) .. +30 (up)
#   J4/J5 + arm swings FORWARD and up (tip toward -Y); 0 = hanging
# ---------------------------------------------------------------------------
JOINTS = [
    dict(id="J1", name="Otáčanie tela (základňa)", axis="Z", range="360° nekonečne (zberací krúžok)",
         drive="gimbal BLDC GM3506 + remeň GT2 4.5:1 + AS5048A + SimpleFOC", where="B"),
    dict(id="J2", name="Otáčanie hlavy (krk)", axis="Z", range="±90°",
         drive="Feetech SCS0009 + ložisko 61805 + preklzová spojka", where="T top"),
    dict(id="J3", name="Náklon hlavy", axis="X", range="−20° / +30°",
         drive="Feetech SCS0009 v N06 + špirálová pružina (kompenzácia váhy)", where="N06"),
    dict(id="J4", name="Pravé rameno", axis="X", range="−30° / +180° (nad 125° len pri hlave rovno)",
         drive="Feetech SCS0009", where="T"),
    dict(id="J5", name="Ľavé rameno", axis="X", range="−30° / +180° (nad 125° len pri hlave rovno)",
         drive="Feetech SCS0009", where="T"),
]

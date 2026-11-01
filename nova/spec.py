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
"""
from math import sqrt

NAME = "NOVA"
VERSION = "v7"

# ---------------------------------------------------------------------------
# Overall stack (Z levels)
# ---------------------------------------------------------------------------
FLOOR_Z = -1.2            # underside of rubber feet B04 (renders put the floor here)
BASE_Z0, BASE_Z1 = 0.0, 36.0          # base: bottom plate underside .. top surface
TORSO_Z0, TORSO_Z1 = 37.0, 139.0      # torso: 1 mm gap above base top
NECK_COLLAR_Z1 = 145.5                # top of N01 collar
TILT_AXIS = dict(y=0.0, z=178.0)      # head-tilt (pitch) axis, parallel to X
PAN_AXIS = dict(x=0.0, y=0.0)         # head-pan (yaw) axis, vertical
HEAD_Z0, HEAD_Z1 = 166.0, 262.0       # head outer shell bottom .. top
OVERALL = dict(w=178.0, d=144.0, h=HEAD_Z1 - FLOOR_Z)   # ~263 mm tall

# ---------------------------------------------------------------------------
# Materials (keys used by CAD part records and by the Blender material library)
# ---------------------------------------------------------------------------
MATERIALS = {
    "white":      dict(desc="biely lesklo-satén PC/ABS (RAL 9003)", rgb=(0.93, 0.93, 0.92), rough=0.28, clearcoat=0.35),
    "black":      dict(desc="čierny soft-touch (RAL 9005 mat)",     rgb=(0.018, 0.018, 0.02), rough=0.5, spec=0.35),
    "black_gloss":dict(desc="čierny lesklý plast",                   rgb=(0.02, 0.02, 0.022), rough=0.15),
    "rubber":     dict(desc="čierne TPU 85A / guma",                 rgb=(0.022, 0.022, 0.024), rough=0.75, spec=0.3),
    "glass":      dict(desc="tvrdené sklo 1.1 mm, čierna potlač",    rgb=(0.01, 0.01, 0.012), rough=0.02),
    "cyan_led":   dict(desc="svetlovod PMMA opál – tyrkysová LED",   rgb=(0.20, 0.90, 1.0), emit=16.0),
    "eye":        dict(desc="obsah displeja – oči (teplá biela)",    rgb=(1.0, 0.86, 0.66), emit=12.0),
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
    w=178.0, d=144.0, plan_r=40.0,       # plan rounded rectangle
    z0=0.0, z1=36.0,
    plate_h=4.0, plate_inset=3.0,         # B02 black bottom plate, inset from white shell
    shell_wall=2.5, top_fillet=10.0, bottom_fillet=2.0,
    turntable_d=92.0, turntable_recess=0.8,   # recessed seat on top face under the torso
    led=dict(w=64.0, h=4.0, r=2.0, z=19.0),   # B03 front light guide (cyan)
    grille=dict(rows=2, cols=13, hole_d=2.2, pitch=4.5, z=(15.5, 22.5)),  # rear speaker grille
    usb_c=dict(w=9.4, h=3.6, x=-62.0, z=18.0),                         # rear, robot-right side
    button=dict(d=7.0, x=-48.0, z=18.0),                                # power button, rear
    feet=dict(d=14.0, h=1.2, xy=[(64, 46), (-64, 46), (64, -46), (-64, -46)]),
    screws=dict(d=3.0, xy=[(70, 0), (-70, 0), (0, 58), (0, -58)]),      # M3 into heat-set inserts
)

# ---------------------------------------------------------------------------
# TORSO (T)  – plan section is a superellipse |x/a|^n + |y/b|^n = 1
# ---------------------------------------------------------------------------
TORSO = dict(
    z0=TORSO_Z0, z1=TORSO_Z1,
    w=106.0, d=90.0, n=3.2,               # main section (between the roundings)
    r_bottom=16.0, r_top=22.0,            # vertical roundings at bottom/top (quarter-round profile)
    wall=2.4,
    front_panel=dict(half_w=38.0, y_cut=-21.0, seam=0.6),     # T01 = shell ∩ |x|<=38 ∩ y<=-21
    rear_door=dict(w=76.0, h=76.0, r=14.0, zc=88.0, seam=0.6,  # T03 projected on rear surface
                   vents=dict(n=5, w=28.0, h=2.0, pitch=4.0, z0=110.0)),
    bottom_plate=dict(w=70.0, d=54.0, h=3.0, n=3.2, screw_xy=[(24, 17), (-24, 17), (24, -17), (-24, -17)],
                      center_hole_d=20.0),
    led=dict(w=40.0, h=4.0, r=2.0, z=96.0),     # T05 cyan light guide on front panel
    sensor=dict(w=26.0, h=4.0, r=2.0, z=80.0),  # T06 frosted window (ToF + ambient light)
    shoulder=dict(z=112.0, y=0.0, bore_d=23.0, cbore_d=31.4, cbore_depth=1.5),
    neck_hole_d=40.0,
)


def torso_section(z):
    """Outer superellipse half-axes (a, b) of the torso at height z (quarter-round roundings)."""
    t = TORSO
    a0, b0 = t["w"] / 2, t["d"] / 2
    shrink = 0.0
    zb = t["z0"] + t["r_bottom"]
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
    collar=dict(w=58.0, d=46.0, z0=TORSO_Z1, z1=NECK_COLLAR_Z1, bore_d=36.0, lip_d=40.0, lip_h=1.0),  # N01 fixed
    cone=dict(z0=146.0, z1=162.0, r_bottom=19.0, r_top=12.5, wall=2.0),     # N02 trumpet, pans, 2 halves
    tilt_housing=dict(barrel_d=30.0, barrel_len=48.0, stem_d=20.5, stem_z0=158.0,
                      cable_slot=(12.0, 6.0)),                              # N06 T-housing, pans
    caps=dict(d=29.0, len=6.0, dome=1.5, gap=0.6),                          # N07 L/R hub caps, tilt with head
    pan_range=(-90, 90), tilt_range=(-20, 30),
)

# ---------------------------------------------------------------------------
# HEAD (H)
# ---------------------------------------------------------------------------
HEAD = dict(
    w=132.0, d=100.0, h=96.0, y0=-46.0, y1=54.0,      # white shell from front rim (y=-46) to back (y=+54)
    z0=HEAD_Z0, z1=HEAD_Z1, zc=(HEAD_Z0 + HEAD_Z1) / 2,  # zc = 214
    r_front_view=28.0,           # corner radius of the silhouette seen from the front (edges // Y)
    r_back=24.0,                 # rounding of the back edge loop
    r_front_rim=2.5,             # rounding of the white rim around the bezel
    wall=2.2,
    bezel=dict(w=124.0, h=88.0, r=24.0, protrude=4.5, front_fillet=3.0, depth=16.0),   # H03 black frame
    glass=dict(w=108.0, h=76.0, r=16.0, t=1.1, recess=1.0, print_border=4.0),          # H04
    camera=dict(hole_d=3.2, z=250.0, module=(8.5, 8.5, 5.0)),                          # H12 mini FPC camera
    display=dict(outline=(105.5, 67.2, 4.0), active=(95.04, 53.86), zc=210.0),         # 4.3" DSI 800x480
    eyes=dict(w=11.0, h=19.0, r=5.5, x=10.5, z=210.0),                                 # default expression
    ear=dict(d=36.0, protrude=8.0, y=4.0, z=214.0, ring_od=30.0, ring_id=23.0, mic_hole_d=1.0),  # H05 + H06
    back_cover=dict(w=100.0, h=66.0, r=18.0, seam=0.6),                                # H02
    neck_recess=dict(w=68.0, d=46.0, r=12.0, depth=29.0),
    vents=dict(n=6, w=14.0, h=1.6, pitch=4.0, y=30.0),   # underside, rear
)
# front of black bezel  y = HEAD["y0"] - bezel.protrude = -50.5 ; glass front y = -49.5

# ---------------------------------------------------------------------------
# ARMS (A) – right arm on -X, left arm mirrored on +X
# ---------------------------------------------------------------------------
ARM = dict(
    axis=dict(y=0.0, z=112.0),               # shoulder pitch axis // X
    abduction_deg=3.0,                       # paddle splayed outward at the bottom
    egg=dict(top_z=126.0, widest_z=74.0, bottom_z=42.0, half_w=19.0, half_t=10.0),  # in arm-local frame
    mid_x=72.4,                              # |x| of the split plane (A01/A02) at the joint
    joint_cover=dict(od=26.0, x0=54.5, x1=65.5, spigot_od=22.0, spigot_len=3.0, bore_d=14.0),  # A04
    ring=dict(od=31.0, id=23.0, t=2.5, x_out=54.0),                                           # A05
    boss=dict(od=26.0, id=22.4),            # on A02 inner shell
    tip=dict(z_top=62.0, y_max=-4.0),        # A03 black soft crescent: lower-front-outer zone
    range=(-30, 180),
)

# ---------------------------------------------------------------------------
# Kinematics summary (5 DOF)
# ---------------------------------------------------------------------------
JOINTS = [
    dict(id="J1", name="Otáčanie tela (základňa)", axis="Z", range="360° nekonečne (zberací krúžok)",
         drive="gimbal BLDC GM3506 + AS5048A + SimpleFOC", where="B"),
    dict(id="J2", name="Otáčanie hlavy (krk)", axis="Z", range="±90°", drive="Feetech SCS0009 serial-bus servo",
         where="T top"),
    dict(id="J3", name="Náklon hlavy", axis="X", range="−20° / +30°", drive="Feetech SCS0009 v N06", where="N06"),
    dict(id="J4", name="Pravé rameno", axis="X", range="−30° / +180°", drive="Feetech SCS0009", where="T"),
    dict(id="J5", name="Ľavé rameno", axis="X", range="−30° / +180°", drive="Feetech SCS0009", where="T"),
]

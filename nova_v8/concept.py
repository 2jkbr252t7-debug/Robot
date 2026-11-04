"""
NOVA mini (v8) – CONCEPT dimensions (mm).  Same coordinate system as v7: Z up, origin on the floor
under the centre of the base, robot FRONT = -Y, robot RIGHT = -X.  Pure Python.

This is a concept-stage spec for quick sketches (head A vs head B on a common mini body).
Exports go to build_v8/ (NOT build/, which holds the finished v7.3 model).
"""

NAME = "NOVA mini"
VERSION = "v8-koncept"
TARGET_H = 190.0

# ---- base: drive module with 2 wheels + 2 ball casters, torso-yaw servo in the centre ----
BASE = dict(
    w=130.0, d=108.0, z0=0.0, z1=38.0, plan_r=26.0, top_fillet=8.0,
    ground_clear=4.0,                                   # underside of the shell above the floor
    wheel=dict(d=36.0, w=10.0, x=52.0, y=4.0),          # wheels at x=±52 (axle slightly behind centre)
    caster=dict(d=12.0, y=(-40.0, 44.0)),               # front/back ball casters
    cliff_sensors=[(52, -44), (-52, -44), (52, 44), (-52, 44)],   # IR/ToF looking down, at the corners
    led=dict(w=40.0, h=3.5, z=20.0),                    # front light guide
    batteries="2x 18650 along X, front and back of the yaw servo",
    yaw=dict(servo="Feetech STS3215 (kovové prevody, magnetický enkodér) – zvislo v strede",
             bearing="tenkostenné ložisko 6806-2RS (30/42x7) alebo točňa", range="±150° (slučka kábla, bez zberacieho krúžku)"),
)

# ---- torso: rotates on the base (J1 = servo, direct drive through the bearing) ----
TORSO = dict(z0=39.0, z1=104.0, w=88.0, d=72.0, n=2.7, r_top=16.0, r_bottom=8.0,
             led=dict(w=28.0, h=3.5, z=84.0), shoulder_z=88.0)

# ---- neck: pan servo in the torso top, short collar, tilt barrel under the head ----
NECK = dict(collar=dict(w=42.0, d=34.0, z0=104.0, z1=109.0), cone=dict(z0=109.0, z1=116.0, r_bottom=13.0, r_top=10.0),
            tilt_axis=dict(y=0.0, z=126.0), barrel_d=30.0, barrel_len=30.0)

# ---- head (both variants): ESP32-S3 + 3.5" IPS 480x320 on one board ----
DISPLAY = dict(outline=(86.0, 56.0, 6.0), active=(73.44, 48.96), note="3.5\" IPS 480x320 (ST7796/ILI9488), QSPI/SPI, s ESP32-S3")
HEAD = dict(z0=116.0, z1=190.0, w=106.0, d=66.0, zc=153.0)

HEAD_A = dict(   # "ako na fotke": rounded box, protruding black bezel, flat glass, ear discs with LED rings
    w=106.0, h=74.0, y0=-33.0, y1=33.0, r_front_view=26.0, r_back=20.0,
    bezel=dict(w=101.0, h=69.0, r=23.5, protrude=5.0), glass=dict(w=92.0, h=60.0, r=16.0, zc=153.0),
    ear=dict(d=28.0, protrude=4.0, y=-3.0, z=153.0, ring_od=23.0, ring_id=17.0),
    eyes=dict(w=10.5, h=17.5, r=5.25, x=10.0, z=150.0),
)
HEAD_B = dict(   # "kapsula s vizorom": very round capsule, black curved visor wrapping into the sides
    w=110.0, h=76.0, d=70.0, r_front_view=34.0, r_back=26.0,
    visor=dict(arc_w=118.0, h=54.0, r_plan=95.0, zc=154.0, wrap=14.0),   # cylindrical visor, wraps 14 mm into the sides
    ear=dict(d=24.0, flush=True, y=4.0, z=154.0, ring_od=24.0, ring_id=18.0),
    eyes=dict(w=11.0, h=18.0, r=5.5, x=10.5, z=151.0),
)

# ---- arms (concept): smaller paddles, same idea as v7.3 ----
ARM = dict(axis=dict(y=0.0, z=88.0), egg=dict(top_z=98.0, widest_z=70.0, bottom_z=47.0, half_w=13.0, half_t=7.0),  # bottom 9 mm above the base top: torso yaw sweeps the arms over the base
           mid_x=58.0, abduction_deg=8.0)

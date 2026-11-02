"""
NOVA mini – v8.0 master specification (single source of truth for v8).  Pure Python, mm.
Coordinate system as v7: Z up, origin on the floor under the centre of the base,
robot FRONT = -Y, robot RIGHT = -X (left in a front view).  Default pose: all joints 0.

Decisions (user, 2026-11-01): smaller (~191 mm), wheels in the base, torso rotates separately,
head variant A (flat glass – cheaper), ESP32-S3 + 3.5" display, parts ordered from China (AliExpress),
cheapest variant that still works reliably.

v8.0 architecture
  * Head: ESP32-S3 + 3.5" IPS 480x320 touch board (e.g. Waveshare ESP32-S3-Touch-LCD-3.5 or the cheaper
    Guition JC3248W535) – face, mic, speaker amp, Wi-Fi AI.  TILT SERVO IS INSIDE THE HEAD (rotates with
    the head), its horn is bolted to the pan stage through the side wall of the barrel pocket
    (a micro servo cannot sit coaxially in a Ø30 barrel – lesson from v7).
  * Neck: pan micro servo vertical in the torso top + 6805 bearing (head load never on the servo spline).
  * Torso yaw (J1): ONE Feetech STS3215 mounted IN THE TORSO BOTTOM (rotates with the torso), spline DOWN,
    horn bolted to a hub fixed in the base; thin bearing 6806 between torso and base carries the load.
    Direct drive, no gears, ±150°, cable loop (no slip ring).  Keeps the base low.
  * Base: drive module – 2x N20 gear motors with encoders, wheels Ø34, 2 ball casters, 4 cliff sensors,
    2x 18650 + charger/boost, motor driver, speaker.  USB-C + switch at the rear, 2 charging pads under the
    rear for a future dock.
  * Torso controller: ESP32-C3 SuperMini (servos, motors, sensors, battery) <-> head ESP32-S3 over UART.
    Neck bundle: 5V, GND, TX, RX (4 thin silicone wires).  Yaw loop: battery + motor + sensor wires (Ø6 bundle).
  * Servos: arms + head pan + head tilt = 4x micro servo in the common 23x12.2 mm envelope with 32 mm tabs:
    MG90S (cheapest, PWM) or Feetech SCS0009 (quieter, feedback) are drop-in alternatives.

=====================================================================================
v8.1 – "MODERNÝ, NIČ NEVIDNO" (user, 2026-11-01): supersedes v8.0 wherever they differ
  * WHEELS FULLY HIDDEN: no wheel arches, no visible tyres. The base is a closed monolithic white shell whose
    skirt comes down to z=3 all round; the wheels (inside the footprint) protrude only ~3 mm below the skirt
    edge. From any side/top view you see a clean body with a thin dark shadow line at the floor.
    Casters, cliff sensors, dock pads, USB-C (underside rear) and a recessed power button are on the UNDERSIDE.
  * UNDERGLOW instead of the front LED strip: a 360° cyan light ring in the shadow gap under the skirt
    that lights the desk (very modern, also a status light).  No base front LED, no rear openings.
  * NO VISIBLE SCREWS anywhere; seams only where parts really split, 0.4–0.6 mm, aligned.
  * TORSO: chest = ONE smoked "dead-front" strip (LED + ToF/light sensor behind the same dark window),
    rear = the WHOLE rear half shell T02 as a tool-free service cover (snap tongues + 2 hidden N52 magnet pairs,
    one y=0 parting line behind the arms – no door seam), all vents on the underside / hidden in seams.
  * HEAD A: one-piece H01 (no back cover), smoked glass laminated to the LCD with 0.2 mm OCA (touch works),
    tilt servo beside the barrel pocket driving a 1:1 gear pair, passive M3 pivots on the tilt axis.
  * Firmware soft limit: arm > 135° while the head is pitched down and panned towards that arm can touch the
    lower bezel corner -> limit the arm to 135° in that combination.
    Head B: arm <= 155° when the head is pitched below -5° and panned towards that arm (free to 180° otherwise).
  * Speaker grille = fine micro-perforation on the base underside rim (invisible from the side).
  * All three head variants are built on this body: A (flat glass), A+ (curved R180), B (frameless visor R100).
  * v8.1 review 2 (internals): BASE NODE – STM32G030 + DRV8833 + 5 V buck on the base board IB09-2, a slave on
    the 1-wire servo bus: drives both N20 (encoders), the 4 cliff sensors and the underglow, stops at a table edge
    locally.  Only 6 wires cross J1 (VBAT, GND, bus, speaker ±, GND) as a flat band in a ROLLING LOOP
    (constant 209 mm, ±150°) – replaces the Ø6 bundle.  Neck bundle = 6 wires (5 V/GND 26 AWG + TX, RX, speaker ±).
    Torso ESP32-C3 uses 11 of 13 GPIO (pin map in BOM_v8.md kap. 7).
=====================================================================================
v8.2 – PROPORCIE "B+" (user, 2026-11-02: "taký malý trup? veľký podstavec a hlava?") – supersedes v8.1 numbers
  The torso was too short (0.88 x head height; R01 has the torso TALLER than the head).  Study:
  obrazky/v8_koncept/v8_studia_proporcii_Bplus.png.  Changes (everything else of v8.1 stays):
  * TORSO 88 x 72 x 65  ->  94 x 76 x 82 (z 36..118); shoulder axis z 98; chest strip z 92; turntable ring OD 82.
  * BASE 130 x 108 x 39 ->  124 x 104 x 35; wheels Ø34 -> Ø30 (axle z 15, x ±48), still fully hidden.
  * ARMS +20 % (egg 61 long, 31 wide, 17 thick), mid_x 64.
  * NECK collar 45 x 36 on the torso top (z 118..123), cone z 123..130, tilt axis z 140.
  * HEAD unchanged in size (3.5" display), moved up 13 mm: z 130..204.  Overall height 204 mm.
v8.3 – MÄKKÉ TVARY (user: "hrozne hranatá základňa, trup moc kockatý, moc veľká medzera… buď moderný, voľná ruka")
  Same sizes/heights as v8.2, new form language (shared outer surfaces in nova_v8/forms.py, prototype renders
  obrazky/v8_koncept/v8_makke_tvary.png):
  * BASE = "pebble plate": plan superellipse n 2.2 (124 x 104 at the top edge), straight conical side shrinking
    to 90 % at the skirt edge z 3 (the robot seems to float on the underglow), crisp top round R7, flat top with a
    circular DISH Ø80 x 2 mm in which the torso foot stands -> torso/base gap only 1 mm, turntable hidden.
  * TORSO = "bulb": round foot Ø72 in the dish flaring (quarter-round, 18 mm) to the belly superellipse n 2.15
    (94 x 76), convex barrel narrowing 3.6 / 2.4 mm towards the shoulders, round R18 into a small flat top
    under the neck collar.  No straight walls, no visible turntable ring.
  * NECK collar 44 x 34 (fits the smaller flat top); arms mid_x follows the narrower shoulder (torso surface at
    the arm axis z 98 is ~ x ±43.4).  Wheels may move inwards (x ±46) because the conical skirt is narrower at
    the bottom (keep >= 0.5 mm tyre clearance).
=====================================================================================
=====================================================================================
v9.0 – "KLASIK" (user's choice 2026-11-02 after rejecting v8.2/v8.3: concept c1 "Klasik R01+",
  obrazky/v8_koncept/v8_4_navrhy.png column 1, renders obrazky/v8_koncept/navrhy/c1_r01_hero.png).
  SUPERSEDES the v8.2 / v8.3 body forms.  Outer forms are defined ONLY in nova_v8/klasik.py from KLASIK below.
  * BASE: white slab 134 x 109 (squircle n 3.6), z 8..33.5, drafted side, elliptical top round 5.5 x 4.5, standing
    on a recessed BLACK FOOT 118 x 93 (z 1..8.6) with the 360° cyan underglow ring just outside the foot
    (z 3.4..6.2).  Wheels Ø30 x 9 at x ±44 (axle z 15) inside the foot outline, ball casters Ø10 at y ±40,
    1 mm ground clearance.  2x 18650 along X in front of / behind the axle.
  * TORSO: 83 x 69 x 82 (squircle n 3.4, z 35..117), 1.5 mm shadow gap over the flat base top, bottom round 7,
    2.6 / 1.4 mm taper to the top, 22 mm shoulder dome into a flat Ø42 circle under the collar.  ONE parting
    line = the outline of a front panel in the plane y = -28 (echoes the display bezel); chest light pill 30 x 3.6
    at z 82.  Hidden circular turntable (J1) under the torso, STS3215 spline down as in v8.
  * ARMS: R01 paddles 72 long, 35 wide, 13.6 thick (white outer shell + black inner shell showing as a crescent),
    yawed 22° (front edge in), splayed 7°, on glossy black bead joints Ø25.6; shoulder axis X at y +1, z 93.
  * NECK: black collar Ø44 (z 116..119.6), visible column Ø25.6 -> 23.2, the black tilt barrel/yoke shows under the
    head; HEAD (A, A+, B unchanged in size) moved to z 135.1..209.1, tilt axis inside the head at z 145.1 (head
    bottom + 10, as v8.1).  Overall height 209 mm.
  * Everything else of v8.1 stays ("nič nevidno", hidden ports underneath, underglow, base node, J1 rolling loop…).
=====================================================================================
"""
from math import sqrt

NAME = "NOVA mini"
VERSION = "v9.0"
FLOOR_Z = 0.0

# v9.0 KLASIK – outer forms (used by nova_v8/klasik.py; numbers from the chosen concept c1)
KLASIK = dict(
    base=dict(w=134.0, d=109.0, n=3.6, z0=8.0, z1=33.5, r_bot=1.6, draft=1.6, r_top_h=5.5, r_top_v=4.5),
    foot=dict(w=118.0, d=93.0, z0=1.0, ring_z=(3.4, 6.2), ring_out=1.2, ring_in=0.6),
    torso=dict(w=83.0, d=69.0, n=3.4, h=82.0, gap=1.5, r_bot=7.0, dome_v=22.0, top_r=21.0, taper_a=2.6, taper_b=1.4,
               seam_y=-28.0, chest=dict(z=82.0, w=30.0, h=3.6)),
    shoulder=dict(y=1.0, z=93.0, hub_r=12.8, recess=1.6),
    arm=dict(length=72.0, shoulder_u=0.77, half_t=6.8, half_w=17.5, n=2.6, yaw=22.0, splay=7.0, inner_face_x=49.0),
    neck=dict(collar_d=44.0, collar_z=(116.0, 119.6), column_r=(12.8, 11.6), visible=15.5),
    head_z0=135.1,
)

MATERIALS_FROM = "nova.spec.MATERIALS"   # same material keys as v7 (white, black, glass, cyan_led, eye, rubber, ...)

# ---------------------------------------------------------------------------
BASE = dict(
    w=134.0, d=109.0, z0=0.0, z1=33.5, plan_r=25.0, top_fillet=5.0, wall=2.0,           # v9.0 KLASIK slab (forms: klasik.py)
    skirt_z0=1.0,                                                 # v9.0: black foot down to z 1 (white slab from z 8)
    form=dict(n=2.2, taper=0.90, r_top=7.0, dish_d=2.0, dish_od=80.0),   # v8.3 pebble plate (nova_v8/forms.py)
    underglow=dict(z=2.0, inset=3.0, note="360° tyrkysový svetelný prstenec pod okrajom – svieti na stôl"),
    wheel=dict(d=30.0, w=9.0, x=44.0, y=0.0, axle_z=15.0),       # v9.0: Ø30 x 9 inside the foot outline
    motor=dict(type="N20 6V s enkodérom (1:100 – 1:150)", body=(12.0, 10.0, 24.0), gearbox_len=9.0),
    caster=dict(d=10.0, y=(-40.0, 40.0)),                         # v9.0 KLASIK
    cliff_sensors=dict(xy=[(47, -39), (-47, -39), (47, 39), (-47, 39)], window=(7.0, 4.0), type="TCRT5000 alebo VL53L0X"),
    # v8.1 CAD positions (base review: the rear caster sits at (0, 44), so the pads/ports moved outwards)
    usb_c=dict(where="underside rear", x=-23.0, y=38.0), button=dict(where="underside, recessed", x=23.0, y=38.0),
    dock_pads=dict(xy=[(-34, 39), (34, 39)], d=6.0),              # spring-pin pads under the rear (future dock)
    batteries=dict(count=2, d=18.5, len=65.0, axis="X", y=(-28.0, 28.0), z=6.0),   # front and back of the hub
    speaker=dict(d=28.0, h=5.0, x=0.0, y=-28.0),
    yaw_hub=dict(d=24.0, bearing=(30.0, 42.0, 7.0), z_top=33.5),  # hub fixed in the base, 6806 bearing at the top
)

TORSO = dict(
    z0=35.0, z1=117.0, w=83.0, d=69.0, n=3.4, r_top=22.0, r_bottom=7.0, wall=2.0,          # v9.0 KLASIK (forms: klasik.py)
    band=dict(half_w=27.0, seam=0.6),                             # centre band front->top->back like v7.3
    form=dict(n=2.15, foot_r=36.0, flare=18.0, ka=3.6, kb=2.4, r_top=18.0, gap=1.0),   # v8.3 bulb (nova_v8/forms.py)
    chest_strip=dict(w=30.0, h=3.6, z=82.0, note="svetelná linka hrude: LED + ToF/svetlo za tým istým oknom"),
    shoulder=dict(z=93.0, y=1.0, bore_d=18.0),
    bottom_plate=dict(h=2.5, ring_od=50.0),                       # v9.0: hidden turntable plinth Ø50 under the torso
    yaw_servo=dict(type="Feetech STS3215", body=(45.2, 24.7, 35.0), spline_down=True, z_body=(40.0, 75.0)),
    controller="ESP32-C3 SuperMini + MP1584 5 V + budič zbernice 74LVC1G126 (motory riadi uzol základne STM32G030)",
)


def torso_section(z):
    t = TORSO
    a0, b0 = t["w"] / 2, t["d"] / 2
    zb, zt = t["z0"] + t["r_bottom"], t["z1"] - t["r_top"]
    s = 0.0
    if z < zb:
        u = (zb - z) / t["r_bottom"]; s = t["r_bottom"] * (1 - sqrt(max(0.0, 1 - u * u)))
    elif z > zt:
        u = (z - zt) / t["r_top"]; s = t["r_top"] * (1 - sqrt(max(0.0, 1 - u * u)))
    return a0 - s, b0 - s


NECK = dict(
    collar=dict(w=44.0, d=44.0, z0=116.0, z1=119.6),             # v9.0: round black collar Ø44
    cone=dict(z0=119.1, z1=129.1, r_bottom=12.8, r_top=11.6),      # v9.0: visible column
    pan_bearing=(25.0, 37.0, 7.0),                                # 6805 under the collar
    tilt_axis=dict(y=0.0, z=145.1), barrel_d=30.0, barrel_len=30.0,   # v9.0: head bottom + 10
    pan_range=(-90, 90), tilt_range=(-20, 20),
)

DISPLAY = dict(outline=(86.0, 56.0, 6.0), active=(73.44, 48.96),
               board="ESP32-S3 + 3.5\" IPS 480x320 dotyk (Waveshare ESP32-S3-Touch-LCD-3.5 / Guition JC3248W535)")

HEAD = dict(   # variant A ("ako na fotke"), flat glass
    w=106.0, h=74.0, z0=135.1, z1=209.1, zc=172.1, y0=-33.0, y1=33.0, r_front_view=26.0, r_back=20.0, wall=2.0,  # v9.0 +18.1
    bezel=dict(w=101.0, h=69.0, r=23.5, protrude=5.0), glass=dict(w=92.0, h=60.0, r=16.0, zc=172.1, print_top=7.0),
    camera=dict(d=2.8, z=198.6, note="voliteľná kamera OV2640/OV5640 na FPC"),
    ear=dict(d=28.0, protrude=4.0, y=-3.0, z=172.1, ring_od=23.0, ring_id=17.0),
    eyes=dict(w=10.5, h=17.5, r=5.25, x=10.0, z=169.1),
    back_cover=dict(w=88.0, h=50.0, r=15.0, seam=0.6),
    barrel_pocket=dict(w=36.0, d=40.0, r=12.0, ceiling_z=162.6),
    tilt_servo=dict(where="v hlave vedľa kapsy valca, os = os náklonu, telo smerom hore", envelope=(25.5, 12.2, 23.2)),
)

ARM = dict(axis=dict(y=1.0, z=93.0), egg=dict(top_z=109.6, widest_z=79.0, bottom_z=37.6, half_w=17.5, half_t=6.8),
           mid_x=55.0, abduction_deg=7.0, range=(-30, 180))           # v9.0 KLASIK paddles (forms: klasik.py arm_*)

MICRO_SERVO = dict(body=(23.0, 12.2, 22.7), tabs_len=32.5, height_with_spline=28.5,
                   options="MG90S (PWM, najlacnejšie) alebo Feetech SCS0009 (sériová zbernica, tichšie)")

OVERALL = dict(h=HEAD["z1"], w_arms=138.0, base=(BASE["w"], BASE["d"]))   # v9.0 KLASIK arm span (concept)

JOINTS = [
    dict(id="J0", name="Jazda (2 kolesá)", drive="2x N20 s enkodérom, diferenciálny pohon"),
    dict(id="J1", name="Otáčanie trupu", range="±150°", drive="Feetech STS3215 v trupe, priamy pohon + ložisko 6806"),
    dict(id="J2", name="Otáčanie hlavy", range="±90°", drive="mikro servo + ložisko 6805"),
    dict(id="J3", name="Náklon hlavy", range="±20°", drive="mikro servo v hlave"),
    dict(id="J4", name="Pravé rameno", range="−30° / +180°", drive="mikro servo"),
    dict(id="J5", name="Ľavé rameno", range="−30° / +180°", drive="mikro servo"),
]

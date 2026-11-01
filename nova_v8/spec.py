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
    rear door flush with a hidden magnetic latch, all vents on the underside / hidden in seams.
  * Speaker grille = fine micro-perforation on the base underside rim (invisible from the side).
  * All three head variants are built on this body: A (flat glass), A+ (curved R180), B (frameless visor R100).
=====================================================================================
"""
from math import sqrt

NAME = "NOVA mini"
VERSION = "v8.1"
FLOOR_Z = 0.0

MATERIALS_FROM = "nova.spec.MATERIALS"   # same material keys as v7 (white, black, glass, cyan_led, eye, rubber, ...)

# ---------------------------------------------------------------------------
BASE = dict(
    w=130.0, d=108.0, z0=0.0, z1=39.0, plan_r=26.0, top_fillet=8.0, wall=2.2,
    skirt_z0=3.0,                                                 # v8.1: closed skirt down to z=3, no wheel arches
    underglow=dict(z=2.0, inset=3.0, note="360° tyrkysový svetelný prstenec pod okrajom – svieti na stôl"),
    wheel=dict(d=34.0, w=10.0, x=52.0, y=4.0, axle_z=17.0),      # tyre top z=34 -> 2.8 mm under the top wall
    motor=dict(type="N20 6V s enkodérom (1:100 – 1:150)", body=(12.0, 10.0, 24.0), gearbox_len=9.0),
    caster=dict(d=12.0, y=(-40.0, 44.0)),
    cliff_sensors=dict(xy=[(52, -44), (-52, -44), (52, 44), (-52, 44)], window=(7.0, 4.0), type="TCRT5000 alebo VL53L0X"),
    usb_c=dict(where="underside rear", x=-20.0, y=46.0), button=dict(where="underside, recessed", x=20.0, y=46.0),
    dock_pads=dict(xy=[(-8, 50), (8, 50)], d=6.0),                # spring-pin pads under the rear (future dock)
    batteries=dict(count=2, d=18.5, len=65.0, axis="X", y=(-28.0, 28.0), z=6.0),   # front and back of the hub
    speaker=dict(d=28.0, h=5.0, x=0.0, y=-28.0),
    yaw_hub=dict(d=24.0, bearing=(30.0, 42.0, 7.0), z_top=39.0),  # hub fixed in the base, 6806 bearing at the top
)

TORSO = dict(
    z0=40.0, z1=105.0, w=88.0, d=72.0, n=2.7, r_top=16.0, r_bottom=8.0, wall=2.0,
    band=dict(half_w=27.0, seam=0.6),                             # centre band front->top->back like v7.3
    chest_strip=dict(w=34.0, h=5.0, z=84.0, note="jeden dymový pás: LED + ToF/svetlo za tým istým oknom"),
    shoulder=dict(z=89.0, y=0.0, bore_d=16.0),
    bottom_plate=dict(h=2.5, ring_od=77.0),                       # black turntable ring visible under the torso
    yaw_servo=dict(type="Feetech STS3215", body=(45.2, 24.7, 35.0), spline_down=True, z_body=(45.0, 80.0)),
    controller="ESP32-C3 SuperMini + DRV8833 + nabíjanie/boost na jednej malej DPS",
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
    collar=dict(w=42.0, d=34.0, z0=105.0, z1=110.0),
    cone=dict(z0=110.0, z1=117.0, r_bottom=13.0, r_top=10.0),
    pan_bearing=(25.0, 37.0, 7.0),                                # 6805 under the collar
    tilt_axis=dict(y=0.0, z=127.0), barrel_d=30.0, barrel_len=30.0,
    pan_range=(-90, 90), tilt_range=(-20, 20),
)

DISPLAY = dict(outline=(86.0, 56.0, 6.0), active=(73.44, 48.96),
               board="ESP32-S3 + 3.5\" IPS 480x320 dotyk (Waveshare ESP32-S3-Touch-LCD-3.5 / Guition JC3248W535)")

HEAD = dict(   # variant A ("ako na fotke"), flat glass
    w=106.0, h=74.0, z0=117.0, z1=191.0, zc=154.0, y0=-33.0, y1=33.0, r_front_view=26.0, r_back=20.0, wall=2.0,
    bezel=dict(w=101.0, h=69.0, r=23.5, protrude=5.0), glass=dict(w=92.0, h=60.0, r=16.0, zc=154.0, print_top=7.0),
    camera=dict(d=2.8, z=180.5, note="voliteľná kamera OV2640/OV5640 na FPC"),
    ear=dict(d=28.0, protrude=4.0, y=-3.0, z=154.0, ring_od=23.0, ring_id=17.0),
    eyes=dict(w=10.5, h=17.5, r=5.25, x=10.0, z=151.0),
    back_cover=dict(w=88.0, h=50.0, r=15.0, seam=0.6),
    barrel_pocket=dict(w=36.0, d=40.0, r=12.0, ceiling_z=144.5),
    tilt_servo=dict(where="v hlave vedľa kapsy valca, os = os náklonu, telo smerom hore", envelope=(25.5, 12.2, 23.2)),
)

ARM = dict(axis=dict(y=0.0, z=89.0), egg=dict(top_z=99.0, widest_z=71.0, bottom_z=48.0, half_w=13.0, half_t=7.0),
           mid_x=58.0, abduction_deg=8.0, range=(-30, 180))

MICRO_SERVO = dict(body=(23.0, 12.2, 22.7), tabs_len=32.5, height_with_spline=28.5,
                   options="MG90S (PWM, najlacnejšie) alebo Feetech SCS0009 (sériová zbernica, tichšie)")

OVERALL = dict(h=HEAD["z1"], w_arms=2 * (ARM["mid_x"] + ARM["egg"]["half_t"]) + 8, base=(BASE["w"], BASE["d"]))

JOINTS = [
    dict(id="J0", name="Jazda (2 kolesá)", drive="2x N20 s enkodérom, diferenciálny pohon"),
    dict(id="J1", name="Otáčanie trupu", range="±150°", drive="Feetech STS3215 v trupe, priamy pohon + ložisko 6806"),
    dict(id="J2", name="Otáčanie hlavy", range="±90°", drive="mikro servo + ložisko 6805"),
    dict(id="J3", name="Náklon hlavy", range="±20°", drive="mikro servo v hlave"),
    dict(id="J4", name="Pravé rameno", range="−30° / +180°", drive="mikro servo"),
    dict(id="J5", name="Ľavé rameno", range="−30° / +180°", drive="mikro servo"),
]

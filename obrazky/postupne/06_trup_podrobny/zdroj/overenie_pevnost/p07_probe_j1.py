"""p07 probe: J1 - cradle walls, floor under the STS3215, plinth / 6805 seat wall, stop lug, skirt; deck; bridges"""
import numpy as np, math, pv_lib as L
log = L.Log("p07_probe_j1")
lo, hi = L.bbox(L.load("T_spodok")); log("T_spodok", lo.round(2), hi.round(2))
# cradle walls: chords along y at several x, z
for x in (-25.0, -10.0, 5.0, 15.0):
    for z in (-75.0, -65.0, -55.0, -50.0):
        log("T_ram chords along y at x %.0f z %.0f:" % (x, z), L.chords("T_ram", (x, -30, z), (0, 1, 0), lo=0, hi=60))
log("T_ram -X end wall chords along x at (y 0, z -65):", L.chords("T_ram", (-40, 0, -65), (1, 0, 0), lo=0, hi=20))
# floor of T_spodok under the servo: vertical chords on a grid inside the pocket footprint
for x in (-28.0, -24.0, -18.0, -10.0, -5.0, 0.0, 5.0, 10.0, 15.0):
    for y in (-11.0, -6.0, 0.0, 6.0, 11.0):
        ch = L.chords("T_spodok", (x, y, -110), (0, 0, 1))
        log("T_spodok vertical chords at (%5.1f, %5.1f): %s" % (x, y, [(round(a - 110, 2), round(b - 110, 2), c) for a, b, c in ch]))
# plinth / bearing seat wall: radial chords at z -94.5 (bearing zone) and -88 (gear zone), several azimuths
for z in (-94.5, -91.5, -88.0, -85.7):
    for az in (0, 90, 180, 270, 135):
        d = (math.cos(math.radians(az)), math.sin(math.radians(az)), 0)
        ch = L.chords("T_spodok", (0, 0, z), d)
        log("T_spodok radial chords z %.1f az %3d: %s" % (z, az, ch))
# stop lug at azimuth 90 (r 18.5..21, 2.5 wide, z -100..-98): sections z = const
for z in (-99.0, -98.2, -97.5):
    r = L.sec("T_spodok", "z", z, window=(-3, 3, 17.5, 22.0), h=0.01)
    log("stop lug z %.1f: A %.2f x %.2f..%.2f y %.2f..%.2f" % (z, r["A"], r.get("umin", 0), r.get("umax", 0), r.get("wmin", 0), r.get("wmax", 0)))
# deck sections across the groove at azimuth 45, and the pivot boss
for az in (30, 60, 90, 120, 150):
    d = (math.cos(math.radians(az)), math.sin(math.radians(az)), 0)
    log("T_paluba radial chords z -47.0 az %3d: %s" % (az, L.chords("T_paluba", (0, 0, -47.0), d)))
log("T_paluba pivot boss vertical chords at r 4.5:", L.chords("T_paluba", (4.5, 0, -60), (0, 0, 1)))
# bridges column <-> cradle (z -60..-50, |x| 23..34.4)
for x in (25.0, 30.0, 33.0, -25.0, -30.0):
    r = L.sec("T_ram", "x", x, window=(-20, 22, -66, -44), h=0.02)
    log("T_ram section x %.0f (z -66..-44): A %.1f y %.2f..%.2f z %.2f..%.2f" % (x, r["A"], r.get("umin", 0), r.get("umax", 0), r.get("wmin", 0), r.get("wmax", 0)))
# pan-servo posts (F4): chords around the pilot at (+-14, -20.79)
for x in (14.0, -14.0):
    log("post F4 at x %.0f: chords along y at z -58.5:" % x, L.chords("T_ram", (x, -40, -58.5), (0, 1, 0), lo=0, hi=40))
    log("                    chords along x at y -20.79 z -58.5:", L.chords("T_ram", (x - 10, -20.79, -58.5), (1, 0, 0)))
    log("                    vertical chords at (x, -23.5):", L.chords("T_ram", (x, -23.5, -90), (0, 0, 1)))

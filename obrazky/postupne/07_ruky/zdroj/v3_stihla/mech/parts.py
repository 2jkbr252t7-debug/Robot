"""R3/mech - arm-side joint parts for the packaging options M1..M4.  Frame B (mm, Z up, front -Y, robot LEFT = +X),
LEFT arm at rest; the right arm is the mirror x -> -x.  Shoulder axis || X through (y 3.0, z -17.0).

Every part is a solid of revolution about the shoulder axis given by its (x, r) profile polygon, optionally limited to an
azimuth sector (az measured about the axis from +Y toward +Z, degrees: 0 = back, 90 = up, 180 = front, 270 = down),
or a small cylinder || X (magnets).  Roles (who moves with whom):
    arm    - fixed to the arm (hub, bearing outer ring + shields, steel washer, rib)
    drive  - fixed to the M4 arm shaft (M4 screw, drive hub, clutch magnets); moves against the arm only while the clutch slips
    static - fixed to the torso plug (ring, seat, stop lug, bearing inner ring)
    torso  - drawn only (parts hidden inside the plug: MR74 A2), never checked
Wall rules used by fit.py (user rules: printed wall >= 1.2, sliding clearance >= 0.3):
    distance to the OUTER arm surface >= 1.2 (cover wall) for arm parts, >= 1.5 (0.3 + 1.2) for drive/static parts
    distance to the INNER arm surface >= 1.2 for steel arm parts and drive/static parts (+0.3), >= 0 for printed arm parts
    (they merge with the inner shell A_vnut); the plug ring passes through the arm's hole by design and is not checked.
Run  /opt/venv/cad/bin/python parts.py            -> prints the options
     /opt/venv/cad/bin/python parts.py --stl      -> stl/<option>/<part>.stl (build123d)"""
import sys, os, math, json
sys.dont_write_bytecode = True
import numpy as np

YA, ZA = 3.0, -17.0
HERE = os.path.dirname(os.path.abspath(__file__))
X_PLUG_FACE = 46.756 - 1.0          # approved torso surface on the axis minus the 1.0 recess


class Part:
    def __init__(self, name, role, prof=None, az=None, kind="printed", mag=None, color="white", note="", pebble=True,
                 req_out=None, req_in=None):
        self.name, self.role, self.kind, self.color, self.note = name, role, kind, color, note
        self.prof = None if prof is None else np.asarray(prof, float)
        self.az = az                  # None = full revolution, else (az0, az1) degrees, az1 > az0
        self.mag = mag                # dict(r, az, d, x0, x1) for a cylinder || X
        self.pebble = pebble
        slide = role in ("drive", "static")
        steel = kind in ("steel", "magnet")
        self.req_out = req_out if req_out is not None else (1.5 if slide else 1.2)
        self.req_in = req_in if req_in is not None else (1.5 if slide else (1.2 if steel else 0.0))

    # -------------------------------------------------------------------------------------------------- geometry
    def xr_bounds(self):
        if self.mag is not None:
            m = self.mag
            return m["x0"], m["x1"], m["r"] - m["d"] / 2, m["r"] + m["d"] / 2
        return self.prof[:, 0].min(), self.prof[:, 0].max(), self.prof[:, 1].min(), self.prof[:, 1].max()

    def outline_xr(self):
        """(x, r) polygon (closed) - for magnets the rectangle spanned in (x, r)"""
        if self.mag is not None:
            x0, x1, r0, r1 = self.xr_bounds()
            return np.array([(x0, r0), (x1, r0), (x1, r1), (x0, r1)])
        return self.prof

    def surface(self, h=0.15):
        """surface samples (N, 3) in frame B"""
        if self.mag is not None:
            m = self.mag
            a = math.radians(m["az"])
            c = np.array([0.0, YA + m["r"] * math.cos(a), ZA + m["r"] * math.sin(a)])
            rr = m["d"] / 2
            th = np.linspace(0, 2 * np.pi, max(12, int(2 * np.pi * rr / h)), endpoint=False)
            xs = np.arange(m["x0"], m["x1"] + 1e-9, h)
            S = [np.c_[np.repeat(xs, len(th)), np.tile(c[1] + rr * np.cos(th), len(xs)), np.tile(c[2] + rr * np.sin(th), len(xs))]]
            for x in (m["x0"], m["x1"]):
                for rho in np.arange(0, rr + 1e-9, h):
                    n = max(1, int(2 * np.pi * rho / h))
                    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
                    S.append(np.c_[np.full(n, x), c[1] + rho * np.cos(t), c[2] + rho * np.sin(t)])
            return np.concatenate(S)
        P = self.prof
        pts = []
        for i in range(len(P)):
            p, q = P[i], P[(i + 1) % len(P)]
            n = max(2, int(math.ceil(np.hypot(*(q - p)) / h)))
            t = np.linspace(0, 1, n, endpoint=False)
            pts.append(p + t[:, None] * (q - p))
        E = np.concatenate(pts)                       # (x, r) boundary points
        a0, a1 = (0.0, 360.0) if self.az is None else self.az
        out = []
        for x, r in E:
            n = max(1, int(math.radians(a1 - a0) * r / h) + 1) if r > 1e-6 else 1
            ph = np.radians(np.linspace(a0, a1, n, endpoint=self.az is not None))
            out.append(np.c_[np.full(n, x), YA + r * np.cos(ph), ZA + r * np.sin(ph)])
        if self.az is not None:                       # end caps of a sector: fill the profile polygon
            x0, x1, r0, r1 = self.xr_bounds()
            X, Rr = np.meshgrid(np.arange(x0, x1 + 1e-9, h), np.arange(r0, r1 + 1e-9, h), indexing="ij")
            Q = np.c_[X.ravel(), Rr.ravel()]
            Q = Q[_inpoly(Q, P)]
            for a in (a0, a1):
                ph = math.radians(a)
                out.append(np.c_[Q[:, 0], YA + Q[:, 1] * math.cos(ph), ZA + Q[:, 1] * math.sin(ph)])
        return np.concatenate(out)

    def to_dict(self):
        d = dict(name=self.name, role=self.role, kind=self.kind, color=self.color, note=self.note,
                 req_out=self.req_out, req_in=self.req_in, pebble=self.pebble)
        if self.mag is not None:
            d["magnet"] = self.mag
        else:
            d["profile_xr"] = self.prof.round(3).tolist()
            d["az"] = self.az
        return d


def _inpoly(Q, P):
    x, y = Q[:, 0], Q[:, 1]
    ins = np.zeros(len(Q), bool)
    for i in range(len(P)):
        x1, y1 = P[i]; x2, y2 = P[(i + 1) % len(P)]
        c = (y1 > y) != (y2 > y)
        with np.errstate(divide="ignore", invalid="ignore"):
            xi = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
        ins ^= c & (x < xi)
    return ins


def rect(x0, x1, r0, r1):
    return [(x0, r0), (x1, r0), (x1, r1), (x0, r1)]


def magnets(prefix, n, r, d, x0, x1, az0=0.0, role="drive"):
    return [Part(f"{prefix}{i + 1}", role, mag=dict(r=r, az=(az0 + 360.0 * i / n) % 360.0, d=d, x0=x0, x1=x1), kind="magnet",
                 color="magnet", note=f"NdFeB {d:g}x{x1 - x0:g} axial") for i in range(n)]


# stop sectors of B1+ (judge-final): lug 135.8 deg wide at az 247.8..383.5, rib 32.7 deg centred at 180.4 at rest;
# contacts at arm -51.0 and +140.5 deg (swing s rotates arm parts by -s in this azimuth convention)
LUG_AZ = (247.8, 383.5)
RIB_AZ = (180.4 - 32.7 / 2, 180.4 + 32.7 / 2)
STOP = (-51.0, 140.5)


def ring(a2_inside=False):
    if a2_inside:          # M4: A2 moved into the ring (x 49.6..52.1), bore steps D7 -> D5 at 52.1 (outboard shoulder)
        P = [(X_PLUG_FACE, 3.5), (52.1, 3.5), (52.1, 2.5), (52.5, 2.5), (52.5, 6.5), (X_PLUG_FACE, 6.5)]
    else:
        P = rect(X_PLUG_FACE, 52.5, 3.5, 6.5)
    return Part("PLG_kruzok", "static", P, color="black", pebble=False, note="plug ring D13 (visible in the gap), kept")


def options():
    O = {}
    # ======================================================================= M1: B1+ arm side unchanged (final_B1plus.json)
    P = [ring(),
         Part("PLG_cap", "static", [(52.5, 3.5), (55.1, 3.5), (55.1, 2.5), (59.5, 2.5), (59.5, 5.0), (52.5, 5.0)], color="black",
              note="seat D10 x 52.5..59.5, D7 bore for A2, bore D5"),
         Part("PLG_doraz", "static", rect(52.5, 55.0, 5.0, 6.6), az=LUG_AZ, color="black", note="stop lug on the seat"),
         Part("BRG_A2_MR74", "torso", rect(52.6, 55.1, 2.0, 3.5), kind="steel", color="steel", note="MR74 A2 inside the seat (torso drive)"),
         Part("M4_DIN912_M4x20", "drive", [(52.5, 0), (52.5, 2.0), (60.0, 2.0), (60.0, 3.5), (64.0, 3.5), (64.0, 0)], kind="steel",
              color="steel", note="arm shaft, head x 60..64"),
         Part("DRV_unasac", "drive", [(60.0, 3.5), (60.0, 4.5), (62.6, 4.5), (62.6, 11.0), (65.9, 11.0), (65.9, 0.0), (64.0, 0.0), (64.0, 3.5)],
              color="grey", note="drive hub: pocket on the M4 head + disc r 11 with 8 pockets"),
         Part("BRG_6700_vnut", "static", rect(55.5, 59.5, 5.0, 5.8), kind="steel", color="steel", note="6700ZZ inner ring (slides on the seat)"),
         Part("BRG_6700_vonk", "arm", rect(55.5, 59.5, 5.8, 7.5), kind="steel", color="steel", note="6700ZZ outer ring + shields (epoxied in the hub)"),
         Part("ARM_rebro", "arm", rect(53.0, 55.0, 5.5, 8.5), az=RIB_AZ, note="stop rib"),
         Part("ARM_naboj", "arm", [(53.0, 8.5), (55.5, 8.5), (55.5, 7.5), (59.6, 7.5), (59.6, 6.5), (60.0, 6.5), (60.0, 5.0), (60.6, 5.0),
                                   (60.6, 11.5), (66.4, 11.5), (66.4, 10.4), (67.6, 10.4), (67.6, 12.7), (59.6, 12.7), (59.6, 8.7),
                                   (55.5, 8.7), (55.5, 9.7), (53.0, 9.7)], note="arm hub: bearing bore, flange, wall r 11.5..12.7, lip ring"),
         Part("ARM_podlozka_M10", "arm", rect(60.6, 62.6, 5.25, 10.0), kind="steel", color="steel", note="DIN 125 M10 10.5x20x2 (friction partner)"),
         ] + magnets("DRV_magnet_5x2_", 8, 7.7, 5.0, 62.85, 64.85)
    O["M1"] = dict(title="B1+ bez zmeny", parts=P, stop=True, rhole=7.0, contacts=[("BRG_6700_vnut", "PLG_cap"), ("ARM_podlozka_M10", "DRV_unasac"),
                                                                          ("BRG_6700_vnut", "BRG_6700_vonk")],
                   rigid=[])
    # ======================================================================= M2: flat B1+ (same functions, plug reprint)
    # stop lug r 5.0..6.7 (stays inside the arm's hole radius 7.0 - 0.3), rib x 52.8..54.3 -> contact 1.5 x 1.4 = 2.1 mm2
    seat2 = [(52.5, 3.5), (55.1, 3.5), (55.1, 2.5), (56.5, 2.5), (56.5, 3.8), (58.6, 3.8), (58.6, 5.0), (52.5, 5.0)]
    lug2 = [(52.5, 5.0), (54.6, 5.0), (54.6, 5.5), (54.3, 5.5), (54.3, 6.7), (52.5, 6.7)]
    rib2 = rect(52.8, 54.3, 5.3, 8.5)
    P = [ring(),
         Part("PLG_cap", "static", seat2, color="black", note="seat D10 x 52.5..58.6, A2 + shoulder as B1+, D7.6 counterbore x 56.5..58.6 for the M4 head"),
         Part("PLG_doraz", "static", lug2, az=LUG_AZ, color="black", note="stop lug r 5.0..6.7 x 52.5..54.3 + step r 5.0..5.5 to x 54.6 (6700 inner ring rests on it)"),
         Part("BRG_A2_MR74", "torso", rect(52.6, 55.1, 2.0, 3.5), kind="steel", color="steel", note="MR74 A2 unchanged"),
         Part("M4_DIN912_M4x16", "drive", [(52.5, 0), (52.5, 2.0), (57.0, 2.0), (57.0, 3.5), (61.0, 3.5), (61.0, 0)], kind="steel",
              color="steel", note="DIN 912 M4x16 8.8, head x 57..61 (tip x 41.0), 1.6 of the head inside the seat counterbore"),
         Part("DRV_unasac", "drive", [(58.9, 3.5), (58.9, 14.25), (60.35, 14.25), (60.35, 4.7), (62.2, 4.7), (62.2, 0), (61.0, 0), (61.0, 3.5)],
              color="grey", note="drive hub: ring pressed on the head (x 58.9..61.0) + cap with 3 AF key; disc 1.45 thick (skin 0.25), 10 pockets D5.1 x 1.2"),
         Part("BRG_6700_vnut", "static", rect(54.6, 58.6, 5.0, 5.8), kind="steel", color="steel", note="6700ZZ inner ring"),
         Part("BRG_6700_vonk", "arm", rect(54.6, 58.6, 5.8, 7.5), kind="steel", color="steel", note="6700ZZ outer ring + shields"),
         Part("ARM_rebro", "arm", rib2, az=RIB_AZ, note="stop rib r 5.3..8.5 x 52.8..54.3"),
         Part("ARM_naboj", "arm", [(52.8, 8.5), (54.6, 8.5), (54.6, 7.5), (56.4, 7.5), (56.4, 14.3), (55.2, 14.3), (55.2, 9.7), (52.8, 9.7)],
              note="arm hub (part of A_vnut): bearing bore + washer backing"),
         Part("ARM_podlozka_M14", "arm", rect(56.4, 58.9, 7.5, 14.0), kind="steel", color="steel",
              note="DIN 125 M14 15x28x2.5 ZINC-PLATED STEEL (not A2), epoxied on the 6700 outer ring: friction partner"),
         ] + magnets("DRV_magnet_5x1_", 10, 10.5, 5.0, 59.15, 60.15)
    O["M2"] = dict(title="B1+ naplocho (6700 + podložka M14 okolo ložiska)", parts=P, stop=True, rhole=7.0,
                   contacts=[("BRG_6700_vnut", "PLG_cap"), ("BRG_6700_vnut", "PLG_doraz"), ("ARM_podlozka_M14", "DRV_unasac"),
                             ("BRG_6700_vnut", "BRG_6700_vonk"), ("BRG_6700_vonk", "ARM_podlozka_M14")], rigid=[])
    # ======================================================================= M2b: as M2 with MR128ZZ + DIN 125 M12 (smaller rim radius)
    P = [ring(a2_inside=True),
         Part("PLG_cap", "static", [(52.5, 2.5), (58.1, 2.5), (58.1, 4.0), (54.6, 4.0), (54.6, 4.4), (54.3, 4.4), (54.3, 5.0), (52.5, 5.0)],
              color="black", note="seat D10 at the root (x 52.5..54.3, stop zone), shoulder r 4.4 for the MR128 inner ring, D8 x 54.6..58.1, bore D5"),
         Part("PLG_doraz", "static", rect(52.5, 54.3, 5.0, 6.7), az=LUG_AZ, color="black", note="stop lug r 5.0..6.7 x 52.5..54.3"),
         Part("BRG_A2_MR74", "torso", rect(49.6, 52.1, 2.0, 3.5), kind="steel", color="steel", note="MR74 A2 moved 3.0 inboard into the ring"),
         Part("M4_DIN7984_M4x20", "drive", [(52.5, 0), (52.5, 2.0), (58.9, 2.0), (58.9, 3.5), (61.7, 3.5), (61.7, 0)], kind="steel",
              color="steel", note="DIN 7984 M4x20 (low head k 2.8), head x 58.9..61.7, tip x 38.9"),
         Part("DRV_unasac", "drive", [(58.4, 3.5), (58.4, 13.0), (59.85, 13.0), (59.85, 4.7), (62.9, 4.7), (62.9, 0), (61.7, 0), (61.7, 3.5)],
              color="grey", note="drive hub: ring on the head + cap with 2.5 AF key; disc 1.45, 9 pockets"),
         Part("BRG_MR128_vnut", "static", rect(54.6, 58.1, 4.0, 4.7), kind="steel", color="steel", note="MR128ZZ inner ring"),
         Part("BRG_MR128_vonk", "arm", rect(54.6, 58.1, 4.7, 6.0), kind="steel", color="steel", note="MR128ZZ outer ring + shields"),
         Part("ARM_rebro", "arm", rect(52.8, 54.6, 5.3, 8.5), az=RIB_AZ, note="stop rib r 5.3..8.5 x 52.8..54.6"),
         Part("ARM_naboj", "arm", [(52.8, 8.5), (54.6, 8.5), (54.6, 6.0), (55.9, 6.0), (55.9, 12.3), (54.7, 12.3), (54.7, 9.7), (52.8, 9.7)],
              note="arm hub: bearing bore + washer backing"),
         Part("ARM_podlozka_M12", "arm", rect(55.9, 58.4, 6.5, 12.0), kind="steel", color="steel",
              note="DIN 125 M12 13x24x2.5 zinc steel around the MR128 (0.5 epoxy ring)"),
         ] + magnets("DRV_magnet_5x1_", 9, 9.25, 5.0, 58.65, 59.65)
    O["M2b"] = dict(title="B1+ naplocho, MR128 + podložka M12", parts=P, stop=True, rhole=7.0,
                    contacts=[("BRG_MR128_vnut", "PLG_cap"), ("ARM_podlozka_M12", "DRV_unasac"),
                              ("BRG_MR128_vnut", "BRG_MR128_vonk"), ("BRG_MR128_vonk", "ARM_podlozka_M12")], rigid=[])
    # ======================================================================= M3: clutch in the torso, arm side = 6700 + keyed hub
    hub3 = [(52.8, 8.5), (54.6, 8.5), (54.6, 7.5), (58.9, 7.5), (58.9, 3.5), (61.0, 3.5), (61.0, 0.0), (62.2, 0.0), (62.2, 4.7),
            (60.1, 4.7), (60.1, 8.7), (55.2, 8.7), (55.2, 9.7), (52.8, 9.7)]
    P = [ring(),
         Part("PLG_cap", "static", seat2, color="black", note="seat as M2"),
         Part("PLG_doraz", "static", lug2, az=LUG_AZ, color="black", note="stop lug as M2"),
         Part("BRG_A2_MR74", "torso", rect(52.6, 55.1, 2.0, 3.5), kind="steel", color="steel"),
         Part("M4_DIN912_M4x16", "drive", [(52.5, 0), (52.5, 2.0), (57.0, 2.0), (57.0, 3.5), (61.0, 3.5), (61.0, 0)], kind="steel",
              color="steel", note="keyed rigidly to the arm hub (no clutch in the arm)"),
         Part("BRG_6700_vnut", "static", rect(54.6, 58.6, 5.0, 5.8), kind="steel", color="steel"),
         Part("BRG_6700_vonk", "arm", rect(54.6, 58.6, 5.8, 7.5), kind="steel", color="steel"),
         Part("ARM_rebro", "arm", rib2, az=RIB_AZ),
         Part("ARM_naboj", "arm", hub3, note="arm hub with a web over the 6700 and a cap keyed on the M4 head (hex 3 AF + press ring)"),
         ]
    O["M3"] = dict(title="spojka v trupe (ruka len náboj)", parts=P, stop=True, rhole=7.0,
                   contacts=[("BRG_6700_vnut", "PLG_cap"), ("BRG_6700_vnut", "PLG_doraz"), ("BRG_6700_vnut", "BRG_6700_vonk"),
                             ("BRG_6700_vonk", "ARM_naboj")],
                   rigid=[("M4_DIN912_M4x16", "ARM_naboj")])
    # ======================================================================= M4: ultra-flat, no mechanical stop (Hall homing), A2 moved
    seat4 = [(52.5, 2.5), (54.6, 2.5), (54.6, 3.8), (57.0, 3.8), (57.0, 5.0), (53.0, 5.0), (53.0, 5.5), (52.5, 5.5)]
    P = [ring(a2_inside=True),
         Part("PLG_cap", "static", seat4, color="black", note="seat D10 x 52.5..56.8, shoulder ring for the 6700, D7.6 counterbore from 54.4"),
         Part("BRG_A2_MR74", "torso", rect(49.6, 52.1, 2.0, 3.5), kind="steel", color="steel", note="MR74 A2 moved 3.0 inboard into the ring"),
         Part("M4_DIN912_M4x16", "drive", [(52.5, 0), (52.5, 2.0), (55.1, 2.0), (55.1, 3.5), (59.1, 3.5), (59.1, 0)], kind="steel",
              color="steel", note="DIN 912 M4x16, head x 55.1..59.1 (tip x 39.1)"),
         Part("DRV_unasac", "drive", [(57.3, 3.5), (57.3, 14.25), (58.75, 14.25), (58.75, 4.7), (60.3, 4.7), (60.3, 0), (59.1, 0), (59.1, 3.5)],
              color="grey", note="drive hub as M2, 1.5 lower"),
         Part("BRG_6700_vnut", "static", rect(53.0, 57.0, 5.0, 5.8), kind="steel", color="steel"),
         Part("BRG_6700_vonk", "arm", rect(53.0, 57.0, 5.8, 7.5), kind="steel", color="steel"),
         Part("ARM_naboj", "arm", [(53.0, 7.5), (54.8, 7.5), (54.8, 14.3), (53.6, 14.3), (53.6, 8.7), (53.0, 8.7)], note="arm hub"),
         Part("ARM_podlozka_M14", "arm", rect(54.8, 57.3, 7.5, 14.0), kind="steel", color="steel", note="DIN 125 M14 on the 6700 outer ring"),
         Part("ARM_hall_magnet_3x2", "arm", mag=dict(r=9.0, az=180.0, d=3.0, x0=53.6, x1=54.8), kind="magnet", color="magnet",
              pebble=False, note="homing magnet for a Hall sensor in the plug ring - placement indicative only, not checked"),
         ] + magnets("DRV_magnet_5x1_", 10, 10.5, 5.0, 57.55, 58.55)
    O["M4"] = dict(title="ultra-plochý, Hallov snímač namiesto dorazu", parts=P, stop=False, rhole=7.0,
                   contacts=[("BRG_6700_vnut", "PLG_cap"), ("ARM_podlozka_M14", "DRV_unasac"), ("BRG_6700_vnut", "BRG_6700_vonk"),
                             ("BRG_6700_vonk", "ARM_podlozka_M14"), ("ARM_hall_magnet_3x2", "ARM_naboj")], rigid=[])
    return O


# ------------------------------------------------------------------------------------------------------- STL export
def export_stl(outdir=None):
    from build123d import Polyline, make_face, revolve, Axis, Plane, Cylinder, Location, export_stl as _ex, Vector
    outdir = outdir or os.path.join(HERE, "stl")
    ax = Axis((0, YA, ZA), (1, 0, 0))
    rep = {}
    for oid, opt in options().items():
        d = os.path.join(outdir, oid)
        os.makedirs(d, exist_ok=True)
        rep[oid] = {}
        for p in opt["parts"]:
            if p.mag is not None:
                m = p.mag; a = math.radians(m["az"])
                c = Vector(m["x0"], YA + m["r"] * math.cos(a), ZA + m["r"] * math.sin(a))
                s = Cylinder(m["d"] / 2, m["x1"] - m["x0"], rotation=(0, 90, 0), align=None).moved(Location(c))
            else:
                a0 = 0.0 if p.az is None else p.az[0]
                pts = [Vector(x, YA + r * math.cos(math.radians(a0)), ZA + r * math.sin(math.radians(a0))) for x, r in p.prof]
                f = make_face(Polyline(*pts, close=True))
                ang = 360.0 if p.az is None else p.az[1] - p.az[0]
                s = revolve(f, ax, ang)
            fn = os.path.join(d, p.name + ".stl")
            _ex(s, fn, tolerance=0.02, angular_tolerance=0.2)
            bb = s.bounding_box()
            rep[oid][p.name] = dict(role=p.role, kind=p.kind, color=p.color, valid=bool(s.is_valid), volume=round(s.volume, 2),
                                    bbox=[round(v, 3) for v in (bb.min.X, bb.min.Y, bb.min.Z, bb.max.X, bb.max.Y, bb.max.Z)],
                                    note=p.note)
            print(f"{oid} {p.name:24s} valid {s.is_valid} vol {s.volume:9.2f}  x {bb.min.X:.2f}..{bb.max.X:.2f}")
    json.dump(dict(frame="B: mm, Z up, front -Y, robot left +X; LEFT arm at rest; right = mirror x -> -x; shoulder axis || X "
                         "through (y 3, z -17)", note="magnet pockets are not cut out of the drive hub mesh (magnets overlap it)",
                   options=rep), open(os.path.join(outdir, "index.json"), "w"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    if "--stl" in sys.argv:
        export_stl()
    else:
        for oid, o in options().items():
            print(oid, o["title"])
            for p in o["parts"]:
                print("   %-24s %-6s x %6.2f..%6.2f r %5.2f..%5.2f" % ((p.name, p.role) + p.xr_bounds()))

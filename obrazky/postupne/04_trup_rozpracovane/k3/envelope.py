"""K3 – minimum interior envelope for the exterior designers -> envelope.json"""
import sys, json, math, time
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T1")
import t1lib as T
from build123d import Box, Pos

HERE = "/tmp/claude-0/gapwf/fin/T1/k3"
L = T.Layout(f"{HERE}/layout.json")
LAY = json.load(open(f"{HERE}/layout.json"))
Z_TT, SH = L.Z_TT, L.SH
CL = 1.0
DZ = 5.0
t0 = time.time()


def section_pts(shape, z0, z1):
    bb = shape.bounding_box()
    if bb.max.Z < z0 or bb.min.Z > z1:
        return []
    slab = Pos((bb.min.X + bb.max.X) / 2, (bb.min.Y + bb.max.Y) / 2, (z0 + z1) / 2) * \
        Box(bb.max.X - bb.min.X + 2, bb.max.Y - bb.min.Y + 2, z1 - z0)
    try:
        s = shape & slab
        if s.volume < 1e-3:
            return []
        verts, _ = s.tessellate(0.2, 0.3)
        return [(v.X, v.Y) for v in verts]
    except Exception as e:
        print("section fail", repr(e)[:60])
        return []


def rot(pts, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return [(x * c - y * s, x * s + y * c) for x, y in pts]


def hull_off(pts, off):
    h = T.hull([(round(x, 2), round(y, 2)) for x, y in pts])
    if len(h) < 3:
        return [[round(x, 1), round(y, 1)] for x, y in h]
    cx = sum(p[0] for p in h) / len(h); cy = sum(p[1] for p in h) / len(h)
    out = []
    for x, y in h:
        d = math.hypot(x - cx, y - cy) or 1
        out.append([round(x + off * (x - cx) / d, 1), round(y + off * (y - cy) / d, 1)])
    # thin the polygon (keep <= 48 points)
    step = max(1, len(out) // 48)
    return out[::step]


def slices(zlo, zhi, items, shell_mounted=()):
    """items: list of (name, shape_at_base_pose, transforms) where transforms = list of (rot_deg, dz)"""
    res = []
    z = zlo
    while z < zhi - 1e-6:
        z1 = min(z + DZ, zhi)
        pts, parts, pts_free = [], set(), []
        for name, sh, tfs in items:
            for dz in sorted({d for _, d in tfs}):
                p = section_pts(sh, z - dz, z1 - dz)
                if not p:
                    continue
                parts.add(name)
                for r, d in tfs:
                    if d == dz:
                        rp = rot(p, r)
                        pts += rp
                        if name not in shell_mounted:
                            pts_free += rp
        if pts:
            xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
            rec = {"z": [round(z, 1), round(z1, 1)],
                   "x": [round(min(xs) - CL, 1), round(max(xs) + CL, 1)],
                   "y": [round(min(ys) - CL, 1), round(max(ys) + CL, 1)],
                   "r_max": round(max(math.hypot(*p) for p in pts) + CL, 1),
                   "hull_plus_1mm": hull_off(pts, CL), "parts": sorted(parts)}
            if pts_free and len(pts_free) != len(pts):
                xf = [p[0] for p in pts_free]; yf = [p[1] for p in pts_free]
                rec["without_shell_mounted"] = {"x": [round(min(xf) - CL, 1), round(max(xf) + CL, 1)],
                                                "y": [round(min(yf) - CL, 1), round(max(yf) + CL, 1)]}
            res.append(rec)
        z = z1
    return res


PAN = [-85 + 5 * i for i in range(35)]
J1 = [-150 + 10 * i for i in range(31)]
torso_items = []
for c in L.comps:
    n, g = c["name"], c["group"]
    if n in ("T_shell",) or g in ("AR", "AL", "H"):
        continue
    sh = L.raw(n)
    bb = sh.bounding_box()
    if g == "T":
        torso_items.append((n, sh, [(0, 0)]))
    elif g == "P":
        torso_items.append((n, sh, [(p, 0) for p in PAN]))
    elif g == "L":
        torso_items.append((n, sh, [(p, l) for p in PAN for l in (0, 10, 20)]))
    elif g == "B" and bb.max.Z > 40.0:
        torso_items.append((n, sh, [(j, 0) for j in J1]))
SHELL_MOUNTED = {"T_rameno_R_puzdro", "T_rameno_L_puzdro", "T_svetlo_hrud", "T_reproduktor", "B_golier_prstenec",
                 "T_zlab_pan", "T_drziak_serva_pan", "T_paluba"}
torso = slices(40.0, Z_TT, torso_items, SHELL_MOUNTED)
print("torso slices", len(torso), round(time.time() - t0))

base_items = [(c["name"], L.raw(c["name"]), [(0, 0)]) for c in L.comps if c["group"] == "B" and c["name"] != "Z_shell"]
base = slices(0.0, 40.0, base_items, {"Z_paluba", "Z_okno_ToF", "Z_svetlo_predne", "Z_ToF", "Z_koliesko_1", "Z_koliesko_2", "Z_koliesko_3",
                                       "Z_koliesko_4", "Z_vypinac", "Z_nabijacka"})
print("base slices", len(base), round(time.time() - t0))

arm_items = [(c["name"], L.raw(c["name"]), [(0, 0)]) for c in L.comps if c["group"] == "AR" and c["name"] != "A_R_skrupina"]
arm = slices(SH[1] - 70, SH[1] + 16, arm_items)
print("arm slices", len(arm), round(time.time() - t0))


def bbox_all(sl):
    return {"x": [min(s["x"][0] for s in sl), max(s["x"][1] for s in sl)],
            "y": [min(s["y"][0] for s in sl), max(s["y"][1] for s in sl)],
            "z": [sl[0]["z"][0], sl[-1]["z"][1]]}


env = {
    "concept": "K3 – J1 v podstavci (STS3215 stojí v osi J1 nad ľavým N20, sokel Ø75 do otvoreného dna trupu)",
    "frame": "world mm, Z up, floor z=0, FRONT=-Y, robot RIGHT=-X. Torso slices in the torso frame (J1=0); pan-stage (P) "
             "and lift (L) parts swept over pan -85..+85 (5 deg) and lift 0/10/20; static base parts that rise into the "
             "torso (plinth, J1 bearing, J1 loop, J1 servo top) swept over J1 -150..+150. Base slices in the base frame. "
             "Every extent already includes +1.0 mm clearance. The shell INNER surface must enclose each slice "
             "(hull_plus_1mm); add the wall (>= 2.0) outside. Parts marked shell_mounted touch the shell on purpose.",
    "shell_mounted_parts": sorted(SHELL_MOUNTED),
    "torso_internal_bbox_incl_1mm": bbox_all(torso),
    "base_internal_bbox_incl_1mm": bbox_all(base),
    "arm_internal_bbox_incl_1mm_right_arm_frame_at_0deg": bbox_all(arm),
    "torso_slices": torso, "base_slices": base, "arm_R_slices_(left = mirror x)": arm,
    "fixed_interfaces": {
        "torso_top": {"z": Z_TT, "collar": "B collar disc r 26.5 (pan, z Z_TT-6..Z_TT) in the static ring r 26.75..28.25 "
                      "glued in a recess r 28.35 through the torso top wall; flush with the torso top",
                      "flat_zone": "torso top flat (z = Z_TT) at least to r 30 around the axis",
                      "head_keepout": "beyond r 30 keep the B-verified shoulder: surface drops >= 1.6 mm at |y| 32, "
                                      ">= 3.7 at 33, >= 12 at 35 below Z_TT (or re-run the head sweep)",
                      "pan_well_sweep": "nothing static inside r 28.0 from z %.1f to %.1f (well + collar sweep r 26.9)"
                                        % (Z_TT - 41.0, Z_TT)},
        "torso_bottom_J1": {"torso_lowest_z": 42.0, "base_top_z": 40.0,
                            "open_bottom": "torso bottom OPEN: no torso material inside r 38.8 between z 40 and the torso "
                                           "deck underside z 65.2 (static dark plinth r 37.5 rises to z 58.6, J1 bearing "
                                           "seat r 23.5 to z 64.9). Visible dark plinth ring = R01 'dark gap ring'.",
                            "torso_deck": "z 65.2..67.2, screwed to >= 4 internal bosses of the torso shell",
                            "plinth": {"r_out": 37.5, "z": [40.0, 58.6], "flange_under_base_top": "r 37.5..42, z 36..38"},
                            "J1_bearing": "6806-2RS 30x42x7 at z 57.9..64.9 on the axis (outer ring static in the plinth)",
                            "J1_loop": "FPC rolling loop annulus r 24..36, z 59.7..64.7; rotating outer wall r 36.5..37.6, z 59.6..65.2"},
        "shoulders": {"axis_y": SH[0], "axis_z": SH[1], "torso_side_max_abs_x_near_arm": 46.0,
                      "spline_hole": "r 4 through the torso wall at x +-(43.5..46)",
                      "arm_inner_face_abs_x": 47.5, "arm_outer_face_abs_x": 68.5, "cap": "black cap D24 x 1.2 at |x| 47.3",
                      "arm_sweep": "paddle 30 (y) x 21 (x) x 80 (14 above / 66 below the axis) turning about X; "
                                   "range -45..+180 (head-dependent firmware limit, see check.json arm table); "
                                   "torso surface must stay at |x| <= 46.0 inside r 70 of the axis",
                      "arm_min_interior": "x 17.7 (servo case 15.5 + tabs, 1.8 walls), y 13.2 half, see arm slices"},
        "base": {"outline": "pebble 148 x 118 (superellipse n 2.4 placeholder), z 6..40, ground clearance 6",
                 "wheel_openings": "floor slots 12 x 30 at x +-56.5 (wheels D30 x 9, x +-(52..61), axle z 15, protrude 6)",
                 "caster_openings": "D14 at (+-46, +-30) – Pololu 3/8in ball casters, ball 0.5 mm above the wheel contact plane",
                 "cliff_IR_holes": "D5 at (+-44, +-41)",
                 "battery_hatches": "2 bottom hatches 70 x 42 (front y -12..-54, rear y 12..54), 2 screws each",
                 "USB_C": "back wall x 14, z 33.1 (opening 10 x 4)", "power_switch": "back wall x -22, z 33.5 (lever slot 5 x 2.5)",
                 "charge_LED": "on the IP2326 board next to the USB-C (light pipe in the port opening)",
                 "ToF_window": "front, x 0, z 13..26 (dark window 20 x 15)",
                 "front_light_bar": "front, x +-19, z 28.2..31.3 (light guide in the wall)"},
        "torso_front": {"light_bar": "x +-16, z 98.9..102.1, 32 % below the top (R01 ~35 %)",
                        "speaker_grille": "slot 28 x 2.6 at z 91 (R01 grey slot) in front of the D28 speaker (z 67.5..96.5)"},
    },
}
json.dump(env, open(f"{HERE}/envelope.json", "w"), indent=1, ensure_ascii=False)
print("done", round(time.time() - t0))

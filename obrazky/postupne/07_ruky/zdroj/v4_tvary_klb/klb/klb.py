"""NOVA mini - R4/klb: variants of the VISIBLE shoulder joint between the torso and arm "B" (importable, pure numpy:
works in the CAD venv AND in Blender's python).

Frame B: mm, Z up, FRONT = -Y, robot LEFT = +X.  Shoulder axis || X through (y 3.0, z -17.0).  Everything here is the
LEFT side in assembly position at rest (arm swing 0); the right side is the mirror x -> -x.

Variants (each = the parts that differ from today's scene; the torso, head, neck, base and arm B stay as in
R3/img/work/scene_v3.py):
    K0  today: thin black plug ring D13 visible in the 3.7 mm gap (reference, nothing changes)
    K1  "golier": black collar D22 (r 7.6..11, end x 46.3, R1.5 round) on the arm, rotates with the arm, reaching into a
        flat pocket of the plug face (r 7.2..11.9, floor x 45.4); arm opening D22.2 instead of D14
    K2  "kryt v trupe": static black cylinder D26.4 grows out of the torso socket (part of the reprinted plug, end x 47.4,
        R0.7 round, face recess D21.6 x 1.0, 3 screw access bores D4.6); arm unchanged
    K3  "jeden valec": static cover as K2 + rotating black ring D26.2 on the arm (end x 48.3, R0.6) with a spigot
        r 7.0..10.0 filling the 0.9 seam (labyrinth) -> reads as one black cylinder D26 with a fine seam; arm opening D26.4
    K3v (optional) K3 with the arm moved 1.5 mm outwards (joint 1.5 longer, robot 3.0 mm wider, white gap +1.5)

Part roles:  'static'  = fixed to the torso (plug cartridge, drawn as is)
             'rotating' = fixed to the arm: pose it with the arm, i.e. world matrix = swing_matrix(deg) (same as the arm
                          shells in scene_v3.pose_arm); the matrix is the same for every dx because the axis is || X.
             p["stl"] is the VISIBLE part for rendering; p["print_stl"] (K1/K3/K3v) is the printable black part = collar /
             ring merged with the M2b arm hub + stop rib (one black print glued into the white inner half A_vnut).
Materials:   'cierna' (black resin) / 'ocel_cierna' (screws) - the keys of scene_v3.SPEC.
Arm:         variant "B" of R3/tvar/variants.py at dx = klb.arm_dx(vid); the arm's inner half gets an opening of
             diameter 2 * v["arm_hole_r"] (14 today); the closed render solid needs no change, but a dark filler inside the
             collar / ring bore hides the white closed face (see scene_klb.build_variant).
Numbers:     klb_summary.json (gaps, visible lengths, front-view band), chk_klb.json (all checks), build_klb.json (meshes).
Cameras:     the joint reads best from the front ortho close-up and the frontal 3/4 ("p34f", dv (0.42, -1, 0.26)) and the
             back 3/4 ("p34b", dv (0.85, 0.95, 0.40)); the hero direction (0.95, -0.80, 0.30) hides it behind the arm.

Usage (Blender, after exec of scene_v3.py without its dispatch, see R4/klb/scene_klb.py):
    import klb
    v = klb.variant("K3")
    for o in v["hide"]: do not load these scene parts (the original plug 'zatka' + 'zatka_skrutky' are replaced)
    for p in v["parts"]:          # p: id, name_sk, role, mat, stl (left side), replaces (scene part names it replaces)
        o = imp(p["stl"], p["id"] + "_L", p["mat"])   ... mirror_copy(o, p["id"] + "_P") for the right side
        if p["role"] == "rotating": o.matrix_world = M4(klb.swing_matrix(deg))   (right side: klb.mirror_matrix(...))
    arm: build_arm_variant("B", klb.arm_dx(vid))  (= -1.0 today, +0.5 for K3v)
"""
import os, math
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
STL = os.path.join(HERE, "stl")
YA, ZA = 3.0, -17.0
X_SH = 46.7556349321583            # torso surface on the shoulder axis (t4_common.X_SH)
DX0 = -1.0                         # today's arm shift (variants.DX)
SOCKET_R = 14.0                    # hole of the torso side cover T_bok_L around the axis (measured from the mesh: 13.996)
PLUG_R = 13.5                      # plug body radius (g2.PLUG body_r)
RING_R = 6.5                       # static plug ring (g2.PLUG ring_r), x 45.756 .. 52.5 (M2b)


# ------------------------------------------------------------------------------------------------ profile helpers
def round_poly(pts, radii, n=10):
    """closed polygon [(x, r)] with a fillet radius per vertex (0 = sharp) -> discretised polygon (x, r)"""
    P = np.asarray(pts, float)
    N = len(P)
    out = []
    for i in range(N):
        p0, p1, p2 = P[i - 1], P[i], P[(i + 1) % N]
        rad = radii[i]
        if rad <= 0:
            out.append(p1)
            continue
        a = p0 - p1; b = p2 - p1
        la, lb = np.linalg.norm(a), np.linalg.norm(b)
        a /= la; b /= lb
        ang = math.acos(max(-1.0, min(1.0, float(a @ b))))
        t = rad / math.tan(ang / 2)                 # distance from the corner to the tangent points
        t = min(t, 0.49 * la, 0.49 * lb)
        rr = t * math.tan(ang / 2)
        q0, q1 = p1 + a * t, p1 + b * t
        bis = (a + b) / np.linalg.norm(a + b)
        c = p1 + bis * (rr / math.sin(ang / 2))
        a0 = math.atan2(*(q0 - c)[::-1]); a1 = math.atan2(*(q1 - c)[::-1])
        da = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
        for k in range(n + 1):
            th = a0 + da * k / n
            out.append(c + rr * np.array([math.cos(th), math.sin(th)]))
    return np.array(out)


def poly_dist(Q, P):
    """signed 2-D distance of points Q (N, 2) to the closed polygon P (M, 2): negative inside"""
    Q = np.atleast_2d(np.asarray(Q, float)); P = np.asarray(P, float)
    A = P; B = np.roll(P, -1, axis=0)
    AB = B - A
    L2 = np.maximum((AB ** 2).sum(1), 1e-18)
    d = np.full(len(Q), np.inf)
    inside = np.zeros(len(Q), bool)
    for i in range(len(P)):
        t = np.clip(((Q - A[i]) @ AB[i]) / L2[i], 0, 1)
        C = A[i] + t[:, None] * AB[i]
        d = np.minimum(d, np.hypot(*(Q - C).T))
        y1, y2 = A[i, 1], B[i, 1]
        c = (y1 > Q[:, 1]) != (y2 > Q[:, 1])
        with np.errstate(divide="ignore", invalid="ignore"):
            xi = A[i, 0] + (Q[:, 1] - y1) * (B[i, 0] - A[i, 0]) / (y2 - y1)
        inside ^= c & (Q[:, 0] < xi)
    return np.where(inside, -d, d)


def to_xr(P):
    """frame-B points -> (x, r) about the shoulder axis"""
    P = np.asarray(P, float)
    return np.c_[P[..., 0], np.hypot(P[..., 1] - YA, P[..., 2] - ZA)]


# ------------------------------------------------------------------------------------------------ the variants
# all x for the variants at dx = DX0 (today's arm position); K3v adds SHIFT_K3V to every arm-side x and to the cover end
SHIFT_K3V = 1.5

# K1 - collar on the arm (rotating) + flat pocket in the plug face
K1 = dict(x_end=46.3, r_in=7.6, r_out=11.0, r_round=1.5, r_round_in=0.5,
          pocket=dict(r_in=7.2, r_out=11.9, x_floor=45.4),      # plug face pocket (cut from the static plug)
          hole_r=11.1)                                          # opening in the arm's inner half A_vnut (was D14)
# K2 / K3 - static cover (part of the plug) + K3 ring on the arm (rotating)
COVER = dict(r=13.2, x_end=47.4, r_round=0.7, x_root=41.0, r_in=6.85, x_step=44.5, screw_hole_r=2.3,
             recess=dict(r=10.8, depth=1.0, r_round=0.3))     # labyrinth: face recess r <= 10.8, 1.0 deep (rim 10.8..13.2)
K3 = dict(x_end=48.3, r_in=7.0, r_out=13.1, r_round=0.6, r_round_in=0.3, hole_r=13.2,
          spigot=dict(r_out=10.0, len=1.0, r_round=0.3))      # spigot r 7.0..10.0 standing 1.0 proud of the ring face:
#   front x 47.3 = only 0.1 past the cover end x 47.4 (axial overlap with the cover rim 0.1; 0.9 to the recess floor x 46.4,
#   0.8 radial to the recess wall r 10.8) - it hides the seam from a radial view, it is not a deep labyrinth (verifier R4)
# the internal (hidden) back of a collar / ring nests around the M2b hub tube (r 8.5..9.7 from x 52.8) and stops on the
# hub disc (x 54.7): glue gaps 0.1; the inner step stays 0.4 in front of the stop rib (x 52.8) and clear of the stop
# lug of the plug (x 52.5 .. 54.3, r <= 6.7)
NEST = dict(x_step=52.4, r_step=9.8, x_back=54.6, r_rim=12.4, x_rim=55.6)   # rim wraps the hub disc (r <= 12.3) for r_out > 12.4


def collar_profile(x_end, r_in, r_out, r_round, r_round_in, shift=0.0, spigot=None):
    """(x, r) polygon of a rotating collar / ring: visible tube r_in..r_out from x_end, hidden back nesting on the hub;
    spigot = dict(r_out, len, r_round): an inner step r_in..spigot r_out reaching len in front of x_end (labyrinth)"""
    s = shift
    x0 = x_end - (spigot["len"] if spigot else 0.0)
    pts = [(x0 + s, r_in), (NEST["x_step"] + s, r_in), (NEST["x_step"] + s, NEST["r_step"]), (NEST["x_back"] + s, NEST["r_step"])]
    if r_out > NEST["r_rim"] + 0.3:
        pts += [(NEST["x_back"] + s, NEST["r_rim"]), (NEST["x_rim"] + s, NEST["r_rim"]), (NEST["x_rim"] + s, r_out)]
    else:
        pts += [(NEST["x_back"] + s, r_out)]
    pts += [(x_end + s, r_out)]
    rad = [r_round_in] + [0.0] * (len(pts) - 2) + [r_round]
    if spigot:
        pts += [(x_end + s, spigot["r_out"]), (x0 + s, spigot["r_out"])]
        rad += [0.0, spigot["r_round"]]
    return round_poly(pts, rad, 12)


def cover_profile(shift=0.0):
    """(x, r) polygon of the static cover (the part of the new plug outboard of x_root): r_in..r 13.5, end x_end"""
    c = COVER
    rc = c["recess"]
    xf = c["x_end"] + shift - rc["depth"]
    pts = [(c["x_root"], c["r_in"]), (c["x_step"], c["r_in"]), (c["x_step"], RING_R), (xf, RING_R), (xf, rc["r"]),
           (c["x_end"] + shift, rc["r"]), (c["x_end"] + shift, c["r"]), (c["x_root"], c["r"])]
    return round_poly(pts, [0.0, 0.0, 0.0, 0.0, 0.0, rc["r_round"], c["r_round"], 0.0], 12)


def cover_trim_profile(shift=0.0):
    """region removed from the old plug before the cover is added: everything outboard of x_step outside the ring"""
    c = COVER
    return np.array([(c["x_step"], RING_R), (70.0, RING_R), (70.0, 15.0), (c["x_step"], 15.0)])


def pocket_profile():
    p = K1["pocket"]
    return np.array([(p["x_floor"], p["r_in"]), (70.0, p["r_in"]), (70.0, p["r_out"]), (p["x_floor"], p["r_out"])])


def stl(vid, pid):
    return os.path.join(STL, vid, pid + ".stl")


ORIG_PLUG = "/tmp/claude-0/gapwf/fin/R1/img_v2/work/stl/zatka.stl"
ORIG_SCREWS = "/tmp/claude-0/gapwf/fin/R1/img_v2/work/stl/zatka_skrutky.stl"

VARIANTS = {
    "K0": dict(name_sk="K0 – dnes: tenký krúžok D13", short_sk="dnes", dx=DX0, visible_d=13.0, rotates_with="torso (static)",
               idea_sk="Medzi trupom a rukou je vidieť len tenký čierny krúžok D13 zo zátky (3,7 mm medzera).",
               parts=[dict(id="PLG_zatka_K0", name_sk="zátka kĺbu (pôvodná)", role="static", mat="cierna", replaces=["zatka"]),
                      dict(id="PLG_skrutky", name_sk="skrutky zátky", role="static", mat="ocel_cierna", replaces=["zatka_skrutky"])],
               hide=["zatka", "zatka_skrutky"]),
    "K1": dict(name_sk="K1 – golier D22 na ruke", short_sk="golier na ruke", dx=DX0, visible_d=2 * K1["r_out"], rotates_with="arm",
               idea_sk="Čierny golier D22 je súčasťou ruky (točí sa s ňou) a zasúva sa do plochého vybrania v zátke – "
                       "hrubý čierny krk od trupu do ruky.",
               parts=[dict(id="PLG_zatka_K1", name_sk="zátka s vybraním pre golier", role="static", mat="cierna", replaces=["zatka"]),
                      dict(id="PLG_skrutky", name_sk="skrutky zátky", role="static", mat="ocel_cierna", replaces=["zatka_skrutky"]),
                      dict(id="ARM_golier_K1", name_sk="golier ruky D22", role="rotating", mat="cierna", replaces=[],
                           print_id="ARM_naboj_golier_K1",
                           profile=lambda: collar_profile(K1["x_end"], K1["r_in"], K1["r_out"], K1["r_round"], K1["r_round_in"]))],
               hide=["zatka", "zatka_skrutky"], arm_hole_r=K1["hole_r"]),
    "K2": dict(name_sk="K2 – kryt kĺbu D26 v trupe", short_sk="kryt v trupe", dx=DX0, visible_d=2 * COVER["r"], rotates_with="torso (static)",
               idea_sk="Zátka vyrastie z jamky trupu ako pevný čierny valec D26 (ako kryt 04 na R08); ruka sa nemení, "
                       "v medzere ostáva tenký krúžok D13.",
               parts=[dict(id="PLG_zatka_K2", name_sk="zátka s krytom D26", role="static", mat="cierna", replaces=["zatka"],
                           profile=lambda: cover_profile()),
                      dict(id="PLG_skrutky", name_sk="skrutky zátky", role="static", mat="ocel_cierna", replaces=["zatka_skrutky"])],
               hide=["zatka", "zatka_skrutky"]),
    "K3": dict(name_sk="K3 – jeden čierny valec D26", short_sk="celý valec", dx=DX0, visible_d=2 * COVER["r"], rotates_with="both",
               idea_sk="Pevný kryt D26 z trupu + čierny prstenec D26 na ruke so škárou 0,9 mm – vyzerá ako jeden veľký čierny "
                       "valec medzi trupom a rukou (R01, R08 04+05).",
               parts=[dict(id="PLG_zatka_K3", name_sk="zátka s krytom D26", role="static", mat="cierna", replaces=["zatka"],
                           profile=lambda: cover_profile()),
                      dict(id="PLG_skrutky", name_sk="skrutky zátky", role="static", mat="ocel_cierna", replaces=["zatka_skrutky"]),
                      dict(id="ARM_prstenec_K3", name_sk="prstenec ruky D26", role="rotating", mat="cierna", replaces=[],
                           print_id="ARM_naboj_prstenec_K3",
                           profile=lambda: collar_profile(K3["x_end"], K3["r_in"], K3["r_out"], K3["r_round"], K3["r_round_in"], 0.0, K3["spigot"]))],
               hide=["zatka", "zatka_skrutky"], arm_hole_r=K3["hole_r"]),
    "K3v": dict(name_sk="K3v – ako K3, ruka o 1,5 mm ďalej", short_sk="K3 + ruka ďalej", dx=DX0 + SHIFT_K3V, visible_d=2 * COVER["r"],
                rotates_with="both", optional=True,
                idea_sk="Ako K3, ale ruka je o 1,5 mm ďalej od trupu – kĺb je o 1,5 mm dlhší, robot o 3 mm širší.",
                parts=[dict(id="PLG_zatka_K3v", name_sk="zátka s krytom D26 (dlhšia o 1,5)", role="static", mat="cierna", replaces=["zatka"],
                            profile=lambda: cover_profile(SHIFT_K3V)),
                       dict(id="PLG_skrutky", name_sk="skrutky zátky", role="static", mat="ocel_cierna", replaces=["zatka_skrutky"]),
                       dict(id="ARM_prstenec_K3v", name_sk="prstenec ruky D26", role="rotating", mat="cierna", replaces=[],
                            print_id="ARM_naboj_prstenec_K3v",
                            profile=lambda: collar_profile(K3["x_end"], K3["r_in"], K3["r_out"], K3["r_round"], K3["r_round_in"], SHIFT_K3V, K3["spigot"]))],
                hide=["zatka", "zatka_skrutky"], arm_hole_r=K3["hole_r"]),
}
VIDS = ("K0", "K1", "K2", "K3", "K3v")
MAIN = ("K0", "K1", "K2", "K3")


def variant(vid):
    v = dict(VARIANTS[vid])
    v["id"] = vid
    v["parts"] = [dict(p, stl=stl(vid, p["id"]), **({"print_stl": stl(vid, p["print_id"])} if "print_id" in p else {}))
                  for p in v["parts"]]
    v.setdefault("arm_hole_r", 7.0)
    p = stl(vid, f"A_vnut_otvor_{vid}")
    if os.path.exists(p):
        v["arm_inner_half_stl"] = p      # A_vnut shell (wall 1.6) with the variant's opening, frame B (not for rendering)
    return v


def arm_dx(vid):
    return VARIANTS[vid]["dx"]


def swing_matrix(deg):
    """4x4 pose of every 'rotating' part (and of the arm) for a swing of deg (+ = forward / up), left side"""
    a = math.radians(-deg); c, s = math.cos(a), math.sin(a)
    M = np.eye(4)
    M[1, 1], M[1, 2], M[2, 1], M[2, 2] = c, -s, s, c
    T = np.eye(4); T[:3, 3] = (0.0, YA, ZA)
    Ti = np.eye(4); Ti[:3, 3] = (0.0, -YA, -ZA)
    return T @ M @ Ti


def mirror_matrix(M):
    """pose matrix of the right side = D M D with D = diag(-1, 1, 1)"""
    D = np.diag([-1.0, 1, 1, 1])
    return D @ np.asarray(M) @ D


if __name__ == "__main__":
    for vid in VIDS:
        v = variant(vid)
        print(vid, v["name_sk"], "dx", v["dx"], [(p["id"], p["role"], os.path.exists(p["stl"])) for p in v["parts"]])

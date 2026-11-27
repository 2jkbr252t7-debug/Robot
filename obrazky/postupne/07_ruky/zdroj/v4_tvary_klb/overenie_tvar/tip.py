"""black tip (A_spicka = the inner half beyond the tip plane, as scene_v4.build_arm_variant): volume, cut-edge wedge angles,
the seam-step at the tip (REV / LIP), tip plane vs cover"""
import sys, json, math
sys.dont_write_bytecode = True
import numpy as np
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R4/overenie_tvar"); import armsurf_own as AS
VB = AS.VB
OUT = {}
h = 0.1
for vid in ["B0", "B1", "B2", "B3"]:
    pt, n = VB.tip_plane_local(vid)
    # volume of the inner half beyond the plane (grid h), and of the whole arm beyond the plane
    xs = np.arange(-14, 10, h); ys = np.arange(-17, 17, h); zs = np.arange(-72, -45, h)
    X, Y = np.meshgrid(xs, ys, indexing="ij"); X = X.ravel(); Y = Y.ravel()
    v_in = v_all = 0
    for z in zs:
        P = np.c_[X, Y, np.full(len(X), z)]
        ins = VB.inside_local(vid, P)
        beyond = (P - pt) @ n > 0
        c = AS.secf(vid, np.array([-z / 72]))[0][0]
        v_all += int((ins & beyond).sum()); v_in += int((ins & beyond & (P[:, 0] < c)).sum())
    R = dict(utip=float(VB.params(vid).get("UTIP", VB.U_TIP)) if not VB.params(vid).get("base") else 0.85,
             tip_vol_inner_half=round(v_in * h ** 3, 0), vol_whole_arm_beyond_plane=round(v_all * h ** 3, 0))
    # cut edge: skin points of the inner half on the plane -> angle between skin normal and plane normal
    S, lab, U = AS.cloud(vid, 0.05, 0.6, 1.0)
    m = (lab == 0) & (np.abs((S - pt) @ n) < 0.03)
    E = S[m]
    def F(P):
        uu = np.clip(-P[:, 2] / 72, 1e-9, 1 - 1e-9)
        c, ti, to, wi, wo, ni, no = AS.secf(vid, uu)
        dx = P[:, 0] - c
        return (np.abs(dx) / ti) ** ni + (np.abs(P[:, 1]) / wi) ** ni - 1
    hh = 1e-4
    g = np.stack([(F(E + hh * np.eye(3)[i]) - F(E - hh * np.eye(3)[i])) / (2 * hh) for i in range(3)], 1)
    g /= np.linalg.norm(g, axis=1)[:, None]
    phi = np.degrees(np.arccos(np.clip(g @ n, -1, 1)))          # tip wedge = phi, body wedge = 180 - phi
    k = int(np.argmin(np.minimum(phi, 180 - phi)))
    R["cut_edge_points"] = int(len(E))
    R["tip_wedge_min_deg"] = round(float(phi.min()), 1); R["body_wedge_min_deg"] = round(float((180 - phi).min()), 1)
    R["worst_edge_at_local"] = E[k].round(2).tolist(); R["worst_edge_u"] = round(float(-E[k, 2] / 72), 3)
    R["cut_u_range_on_skin"] = [round(float(-E[:, 2].max() / 72), 3), round(float(-E[:, 2].min() / 72), 3)]
    # cut on the seam face (flat, normal +x for the inner half): angle
    R["seam_face_wedge_deg"] = round(float(np.degrees(np.arccos(abs(n[0])))), 1)
    # does the plane reach the cover's skin above the bottom apex? (cover points beyond the plane: the cover stays white
    # there and simply continues over the black tip)
    mc = (lab == 1) & ((S - pt) @ n > 0)
    R["cover_skin_beyond_plane_u_from"] = round(float(U[mc].min()), 3) if mc.any() else None
    # seam step at the tip zone
    us = np.linspace(R["cut_u_range_on_skin"][0], 0.999, 50)
    wi, wo = VB.half_widths(vid, us)
    R["seam_step_in_tip_zone_mm"] = [round(float((wi - wo).min()), 3), round(float((wi - wo).max()), 3)]
    OUT[vid] = R
    print(vid, R, flush=True)
json.dump(OUT, open("out/tip.json", "w"), indent=1)

"""min radius of curvature of the section halves along u (own superellipse curvature, analytic param) + where the black tip
plane cuts; reports per half: min radius over u in [0.05, UTIP-cut], u where it is < 1.9 / < 1.6 / < 1.2"""
import sys, json
sys.dont_write_bytecode = True
import numpy as np
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R4/overenie_tvar"); import armsurf_own as AS
VB = AS.VB


def minrad(t, w, n):
    a = np.linspace(1e-4, np.pi / 2 - 1e-4, 40001)
    ca, sa = np.cos(a), np.sin(a)
    x = t * ca ** (2 / n); y = w * sa ** (2 / n)
    x1, y1 = np.gradient(x, a), np.gradient(y, a); x2, y2 = np.gradient(x1, a), np.gradient(y1, a)
    k = np.abs(x1 * y2 - y1 * x2) / (x1 ** 2 + y1 ** 2) ** 1.5
    j = int(np.argmax(k))
    return 1 / k[j], float(np.degrees(np.arctan2(y[j], x[j])))


OUT = {}
for vid in ["B0", "B1", "B2", "B3"]:
    pt, nrm = VB.tip_plane_local(vid)
    us = np.round(np.arange(0.02, 0.99, 0.01), 3)
    rows = []
    for u in us:
        c, ti, to, wi, wo, ni, no = [float(np.ravel(v)[0]) for v in AS.secf(vid, np.array([u]))]
        ri, ai = minrad(ti, wi, ni); ro, ao = minrad(to, wo, no)
        # is the whole section beyond the tip plane? (fraction of the section's y=0 outer / inner face points beyond)
        Pin = np.array([c - ti, 0, -72 * u]); Pout = np.array([c + to, 0, -72 * u])
        rows.append(dict(u=float(u), r_in=round(ri, 3), r_out=round(ro, 3), at_deg_out=round(ao, 1),
                         inner_face_in_tip=bool((Pin - pt) @ nrm > 0), outer_face_in_tip=bool((Pout - pt) @ nrm > 0)))
    body = [r for r in rows if 0.05 <= r["u"] <= 0.95 and not r["outer_face_in_tip"]]
    bi = [r for r in rows if 0.05 <= r["u"] <= 0.95 and not r["inner_face_in_tip"]]
    ko = min(body, key=lambda r: r["r_out"]); ki = min(bi, key=lambda r: r["r_in"])
    OUT[vid] = dict(min_out=ko, min_in=ki, rows=rows,
                    u_out_below_1p9=[r["u"] for r in body if r["r_out"] < 1.9], u_out_below_1p2=[r["u"] for r in body if r["r_out"] < 1.2],
                    u_in_below_1p6=[r["u"] for r in bi if r["r_in"] < 1.6], u_in_below_1p9=[r["u"] for r in bi if r["r_in"] < 1.9])
    print(vid, "outer min r %.3f @u %.2f (%.0f deg)" % (ko["r_out"], ko["u"], ko["at_deg_out"]), "| inner min r %.3f @u %.2f" % (ki["r_in"], ki["u"]),
          "| out<1.9:", OUT[vid]["u_out_below_1p9"][:3], "..", OUT[vid]["u_out_below_1p9"][-3:], " in<1.9:", OUT[vid]["u_in_below_1p9"][:2], OUT[vid]["u_in_below_1p9"][-2:])
    print("    ", [(r["u"], r["r_out"], r["r_in"]) for r in rows if r["u"] in (0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 0.8, 0.85, 0.9, 0.95)])
json.dump(OUT, open("out/secrad.json", "w"), indent=1)

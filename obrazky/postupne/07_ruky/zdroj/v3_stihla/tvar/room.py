"""R3/tvar: room for the joint inside each arm variant (left arm at rest, swing-independent because the hub is coaxial).
For coaxial discs of radius r about the shoulder axis: the x range over which the whole disc lies inside the arm interior
(interior = analytic inset of the shell by WALL; inset reduces ti/to/w like v1geo.inside_local -> approximate wall)."""
import sys, json, numpy as np
sys.dont_write_bytecode = True
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R3/tvar")
import variants as VA
out = {}
th = np.linspace(0, 2 * np.pi, 180, endpoint=False)
xs = np.arange(44.0, 80.0, 0.05)
for vid in VA.VIDS:
    R = {}
    for wall in (0.0, 1.2, 1.6):
        for r in (5.0, 7.5, 10.0, 11.0, 12.7, 14.0):
            ok = []
            for x in xs:
                P = np.c_[np.full_like(th, x), 3.0 + r * np.cos(th), -17.0 + r * np.sin(th)]
                ok.append(VA.inside_local(vid, VA.to_local(P), wall).all())
            ok = np.array(ok)
            R[f"wall{wall}_r{r}"] = [round(float(xs[ok].min()), 2), round(float(xs[ok].max()), 2)] if ok.any() else None
    L_ = np.c_[xs, np.full_like(xs, 3.0), np.full_like(xs, -17.0)]
    ins = VA.inside_local(vid, VA.to_local(L_))
    R["axis_skin"] = [round(float(xs[ins].min()), 2), round(float(xs[ins].max()), 2)]
    out[vid] = R
    print(vid, R["axis_skin"], {k: v for k, v in R.items() if k.startswith("wall1.2")})
json.dump(out, open("/tmp/claude-0/gapwf/fin/R3/tvar/room.json", "w"), indent=1)

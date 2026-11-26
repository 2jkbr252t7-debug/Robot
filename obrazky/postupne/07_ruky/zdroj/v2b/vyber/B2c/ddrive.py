"""JUDGE: direct-drive budget on the shoulder axis from the own moving model (mov.npz).
For a body coaxial with the arm axis (|y-3| <= hw, |z+17| <= hw) its inner face x_in must keep 1.0 from the swept set:
x_in >= max over its z-range of r_max(z) + 1.0 (r of reachable moving samples, pan +-90.3, lift 0..20)."""
import numpy as np, json
D = np.load("mov.npz"); R = D["R"].astype(float); L = D["L"].astype(float); Rt = D["Rt"]; Lt = D["Lt"]
def cyl(P): return np.hypot(P[:,0],P[:,1]), np.degrees(np.arctan2(P[:,1],P[:,0])), P[:,2]
out = {}
for side, (a0, a1) in (("L", (-12.0, 25.0)), ("R", (155.0, 192.0))):
    rR,tR,zR = cyl(R); rL,tL,zL = cyl(L)
    def reach(t):   # azimuth reachable within [a0,a1] by pan +-90.3
        lo, hi = a0 - 90.3, a1 + 90.3
        d = (t - lo) % 360.0
        return d <= (hi - lo)
    mR = reach(tR); mL = reach(tL)
    res = {}
    for hw in (6.0, 7.5):
        zs = (-17 - hw, -17 + hw)
        a = mR & (zR >= zs[0]) & (zR <= zs[1])
        b = mL & (zL <= zs[1]) & (zL + 20 >= zs[0])
        rmax = max(rR[a].max(), rL[b].max())
        who = Rt[a][rR[a].argmax()] if rR[a].max() >= rL[b].max() else Lt[b][rL[b].argmax()]
        # without the lift module (lift servo, crank, holder): only P_sachta + golier + neck parts
        keepR = a & ~np.isin(Rt, ["servo_zdvih","P_drziak_serva","rameno_zdvih","cap_kluky","skr_ramena","konektor_zdvih","kabel_zdvih","skr_F11","matica_F11","podl_F11","pigtail","fpc_lift"])
        rmax2 = max(rR[keepR].max(), rL[b].max())
        x_in = rmax + 1.0; x_in2 = rmax2 + 1.0
        res[f"hw {hw}"] = dict(r_max=round(rmax,2), by=str(who), x_in=round(x_in,2), free_to_surface=round(46.756-x_in,2),
                               free_to_inner_wall=round(44.52-x_in,2), without_lift_module=dict(r_max=round(rmax2,2), free=round(46.756-x_in2,2)))
    out[side] = res
print(json.dumps(out, indent=1)); json.dump(out, open("ddrive.json","w"), indent=1)

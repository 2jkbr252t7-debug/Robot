"""max right-arm angle (deg) without contact with the head, per pan / lift / tilt; left arm = mirror (pan -> -pan).
Bisection on volume clash (tol 0.05 mm3), then the 2 mm clearance angle is verified with distance_to."""
import sys, json, time
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T1")
import t1lib as T

L = T.Layout("/tmp/claude-0/gapwf/fin/T1/k2/layout.json")
HEAD = ["B_hlava", "B_usi", "B_ram_tvar", "B_uska"]
ARM = ["A_R_ruka", "A_R_kryt"]


def hits(p):
    return bool(L.clashes(p, 0.05, only_moving=True, names=HEAD + ARM))


def gap(p):
    return L.gaps(p, ARM, HEAD)[0]


def limit(base):
    p = dict(base, armR=180)
    if not hits(p):
        return 180.0
    lo, hi = 60.0, 180.0
    while hi - lo > 1.0:
        m = (lo + hi) / 2
        if hits(dict(base, armR=m)):
            hi = m
        else:
            lo = m
    # back off until >= 2 mm clearance
    a = lo
    while a > 60 and gap(dict(base, armR=a)) < 2.0:
        a -= 1.0
    return a


if __name__ == "__main__":
    t0 = time.time()
    states = [(0, 0), (12.5, 30), (12.5, -40), (20, 0), (20, 40), (20, -40)]
    out = {}
    for lift, tilt in states:
        row = {}
        for pan in (-85, -60, -30, 0, 30, 60, 85):
            row[pan] = limit({"pan": pan, "lift": lift, "tilt": tilt})
        out[f"lift{lift}_tilt{tilt}"] = row
        print(lift, tilt, row, round(time.time() - t0), flush=True)
    json.dump(out, open("/tmp/claude-0/gapwf/fin/T1/k2/arm_limits.json", "w"), indent=1)

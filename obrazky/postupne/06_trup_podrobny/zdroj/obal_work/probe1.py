import sys, numpy as np, math
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4")
import t4_common as C

def F(P):
    P = np.atleast_2d(P).astype(float)
    d = C.TOP - P[:, 2]
    a = np.interp(d, C.PD, C.PA); b = np.interp(d, C.PD, C.PB); n = np.interp(d, C.PD, C.PN)
    return (np.abs(P[:, 0]) / a) ** n + (np.abs(P[:, 1]) / b) ** n - 1.0

def normal(P, h=(1e-3, 1e-3, 0.08)):
    P = np.atleast_2d(P).astype(float); g = np.zeros_like(P)
    for k in range(3):
        e = np.zeros(3); e[k] = h[k]
        g[:, k] = (F(P + e) - F(P - e)) / (2 * h[k])
    return g / np.linalg.norm(g, axis=1)[:, None]

def wall(x, z, side, w=0.0):
    p = np.array([x, C.y_surface(x, z, side), z]); n = normal(p)[0]
    return p - w * n, n

print("b_outer(z): ", {z: round(C.prof(C.TOP - z)[1], 3) for z in (1.4, 1.75, 1.9, 2.1, 2.5)})
print("a_outer(z): ", {z: round(C.prof(C.TOP - z)[0], 3) for z in (1.4, 1.75, 1.9, 2.1, 2.5)})
for z in (-10.5, -8, -6.6, -5.6, -4.5, -3, -2, -1, 0, 1, 1.75):
    P = C.inner_section(z, 2.2, 360)
    r = np.hypot(P[:, 0], P[:, 1]); th = np.degrees(np.arctan2(P[:, 1], P[:, 0])) % 360
    f = lambda a: float(r[np.argmin(np.abs(th - a))])
    print(f"z {z:6.2f} rho_i: az0 {f(0):6.2f} az30 {f(30):6.2f} az50 {f(50):6.2f} az70 {f(70):6.2f} az90 {f(90):6.2f} min {r.min():.2f}")
# front wall numbers
print("front wall (outer y, inner(2.2) y, normal):")
for (x, z) in [(0, -32.5), (15.3, -32.5), (17.5, -32.5), (19.5, -32.5), (20.35, -32.5), (22, -32.5), (0, -48), (11.5, -48), (12.5, -48), (0, -51), (14, -51), (0, -37), (0, -65),
               (9.9, -41.1), (9.9, -60.9), (14.29, -42.75), (0, -67.5), (0, -70), (0, -34.5), (-14.29, -59.25)]:
    p, n = wall(x, z, -1); q = p - 2.2 * n; q34 = p - 3.4 * n
    print(f"  x {x:6.2f} z {z:6.2f}: outer y {p[1]:7.3f}  inner y {q[1]:7.3f} (x {q[0]:.2f} z {q[2]:.2f})  n ({n[0]:.3f},{n[1]:.3f},{n[2]:.3f})  inset3.4 y {q34[1]:.3f}")
print("back wall magnets / hooks:")
for (x, z) in [(25, -24), (21, -24), (29, -24), (25, -28), (25, -20), (21, -28), (25, -60), (21, -60), (29, -60), (12, -12), (16, -12), (20, -12), (12, -9.5), (20, -9.5), (12, -14.5), (0, -12), (18, -12), (28.25, -24), (30.25, -24), (0, -72), (0, -71.4)]:
    p, n = wall(x, z, +1)
    s = f"  x {x:6.2f} z {z:6.2f}: outer y {p[1]:7.3f} n ({n[0]:.3f},{n[1]:.3f},{n[2]:.3f})"
    for w in (2.2, 3.6, 4.0, 4.5, 4.7, 7.2):
        q = p - w * n; s += f" | w{w}: r {math.hypot(q[0], q[1]):.2f} z {q[2]:.2f}"
    print(s)

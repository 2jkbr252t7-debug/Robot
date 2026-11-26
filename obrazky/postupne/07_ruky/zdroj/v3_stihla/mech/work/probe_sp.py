import numpy as np, math, sys
m = np.load("/tmp/claude-0/gapwf/fin/R2c/oprava/spodok_mod_L.npy")
lo = np.array((20, -30, -75.)); h = 0.5
n = m.shape
xs = lo[0] + (np.arange(n[0]) + 0.5) * h; ys = lo[1] + (np.arange(n[1]) + 0.5) * h; zs = lo[2] + (np.arange(n[2]) + 0.5) * h
Fz = np.load("/tmp/claude-0/gapwf/fin/R2c/vyber/B2c/colfill_B1merge_L.npz")
print(Fz.files, {k: Fz[k].shape for k in Fz.files})
P = Fz["P"].astype(float)
F = np.load("/tmp/claude-0/gapwf/fin/R2c/oprava/free_L.npz")
fxs, fys, fzs = F["xs"], F["ys"], F["zs"]
ds, dm, dl, capmin = F["ds"], F["dm"], F["dl"], F["capmin"]
for z in [float(a) for a in sys.argv[1:]]:
    k = int(np.argmin(abs(zs - z))); zz = zs[k]
    kf = int(np.argmin(abs(fzs - zz)))
    fz = P[abs(P[:, 2] - zz) < 0.26]
    fill = set((round(p[0]*2)/2, round(p[1]*2)/2) for p in fz)
    print(f"\nz {zz:.2f}  '#' T_spodok(mod)  'f' column fill  '.' other hard  's' sweep  'c' beyond cap  'o' free  '+' r4.5  'S' servo case  'X' vert axis")
    print("      " + "".join("|" if abs(x-round(x))<0.3 and int(round(x))%2==0 else " " for x in xs if 26<=x<=48))
    for j in range(n[1]-1, -1, -1):
        y = ys[j]
        if y > 18 or y < -22: continue
        row = ""
        for i in range(n[0]):
            x = xs[i]
            if not (26 <= x <= 48): continue
            fi = int(np.argmin(abs(fxs - x))); fj = int(np.argmin(abs(fys - y)))
            rv = math.hypot(x-39, y-3)
            key = (round((x)*2)/2, round(y*2)/2)
            if m[i, j, k]: c = '#'
            elif any(abs(x-a)<0.26 and abs(y-b)<0.26 for a,b in [key]) and key in fill: c='f'
            elif 32.95 <= x <= 45.05 and -14.3 <= y <= 8.9 and zz <= -45: c='S'
            elif ds[fi,fj,kf] < 0.55: c='.'
            elif dm[fi,fj,kf] < 1.25: c='s'
            elif x > capmin[fj,kf]-0.55: c='c'
            else: c='o'
            if rv < 0.3: c = 'X'
            elif abs(rv-4.5) < 0.25 and c == 'o': c = '+'
            row += c
        print(f"{y:6.2f}" + row)

import numpy as np, math, sys
F = np.load("/tmp/claude-0/gapwf/fin/R2c/oprava/free_L.npz")
xs, ys, zs = F["xs"], F["ys"], F["zs"]; h = 0.5
ds, dm, dl, capmin = F["ds"], F["dm"], F["dl"], F["capmin"]
X, Y = np.meshgrid(xs, ys, indexing="ij")
for z in [float(a) for a in sys.argv[1:]]:
    kz = int(np.argmin(abs(zs - z)))
    print(f"\nz {zs[kz]:.2f}: '.' hard(ds<0.3) 's' sweep 'l' lower-path 'c' beyond cap  'o' free  '+' r=4.5 ring about (39,3) 'X' axis")
    ix = [i for i in range(len(xs)) if 26 <= xs[i] <= 48]
    print("      " + "".join("|" if abs(xs[i]-round(xs[i]))<0.3 and int(round(xs[i]))%2==0 else " " for i in ix))
    for j in range(len(ys)-1, -1, -1):
        y = ys[j]
        if y > 20 or y < -20: continue
        row = ""
        for i in ix:
            x = xs[i]; rv = math.hypot(x-39, y-3)
            if ds[i,j,kz] < 0.3+h/2: c='.'
            elif dm[i,j,kz] < 1.0+h/2: c='s'
            elif dl[i,j,kz] < 0.5+h/2: c='l'
            elif x > capmin[j,kz]-0.3-h/2: c='c'
            else: c='o'
            if abs(rv-4.5) < 0.25 and c=='o': c='+'
            if rv < 0.3: c='X'
            row += c
        print(f"{y:6.2f}" + row)

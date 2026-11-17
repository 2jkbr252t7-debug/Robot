"""t03 - TLAC ZO ZIVICE (MSLA): pre kazdy tlaceny diel a zvolenu orientaciu:
  * rozmer v orientacii voci 218 x 123 x 220
  * PRISAVKY: uzavrete vzduchove / zivicove kapsy pocas tlace (vrstva po vrstve, 2D oblasti vzduchu, ktore nie su spojene s okolim cez
    uz vytlacene vrstvy) - objem, najvacsia plocha pri FEP folii, v ktorej vyske sa odvzdusnia
  * OSTROVY: 2D oblasti materialu, ktore zacinaju bez materialu pod sebou (kazdy potrebuje podperu) - pocet, plocha, kde
  * plocha stien obratenych k platforme (do 35 deg od vodorovnej) = kde budu stopy po podperach
Voxel 0.4 mm (hrubsi ako realna vrstva 0.05: kapsy mensie nez ~0.8 mm sa nezachytia).
Spustenie: /opt/venv/cad/bin/python t03_tlac.py [diel ...]  -> t03_tlac.json"""
import sys, os, json, math, struct, time
import numpy as np
from scipy import ndimage as ndi

T4 = "/tmp/claude-0/gapwf/fin/T4"
OUT = T4 + "/overenie_montaz"
H = 0.4
T0 = time.time()


def say(*a):
    print(f"[{time.time() - T0:6.1f}]", *a, flush=True)


def read_stl(path):
    with open(path, "rb") as f:
        f.read(80)
        n = struct.unpack("<I", f.read(4))[0]
        d = np.frombuffer(f.read(n * 50), dtype=np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]))
    return d["v"].astype(np.float64)


def basis(u):
    u = np.asarray(u, float); u /= np.linalg.norm(u)
    a = np.array([1.0, 0, 0]) if abs(u[0]) < 0.9 else np.array([0, 1.0, 0])
    e1 = np.cross(u, a); e1 /= np.linalg.norm(e1); e2 = np.cross(u, e1)
    return np.array([e1, e2, u])            # riadky = nove osi


def voxelize(T, h=H):
    """T: (n,3,3) trojuholniky v suradniciach tlace (z' = vyska nad platformou).  Vrati occ[k, i, j] (k = vrstva), pociatok"""
    lo = T.reshape(-1, 3).min(0) - 2.5 * h + np.array([0.0137, 0.0071, 0.0113]); hi = T.reshape(-1, 3).max(0) + 2.5 * h
    nx, ny, nz = (np.ceil((hi - lo) / h)).astype(int) + 1
    diff = np.zeros((nx, ny, nz + 1), np.int32)
    a, b, c = T[:, 0], T[:, 1], T[:, 2]
    for t in range(len(T)):
        A, B, Cc = a[t], b[t], c[t]
        x0 = min(A[0], B[0], Cc[0]); x1 = max(A[0], B[0], Cc[0]); y0 = min(A[1], B[1], Cc[1]); y1 = max(A[1], B[1], Cc[1])
        i0 = int(math.ceil((x0 - lo[0]) / h)); i1 = int(math.floor((x1 - lo[0]) / h))
        j0 = int(math.ceil((y0 - lo[1]) / h)); j1 = int(math.floor((y1 - lo[1]) / h))
        if i1 < i0 or j1 < j0:
            continue
        den = (B[1] - Cc[1]) * (A[0] - Cc[0]) + (Cc[0] - B[0]) * (A[1] - Cc[1])
        if abs(den) < 1e-12:
            continue
        xs = lo[0] + h * np.arange(i0, i1 + 1); ys = lo[1] + h * np.arange(j0, j1 + 1)
        X, Y = np.meshgrid(xs, ys, indexing="ij")
        w0 = ((B[1] - Cc[1]) * (X - Cc[0]) + (Cc[0] - B[0]) * (Y - Cc[1])) / den
        w1 = ((Cc[1] - A[1]) * (X - Cc[0]) + (A[0] - Cc[0]) * (Y - Cc[1])) / den
        w2 = 1.0 - w0 - w1
        m = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
        if not m.any():
            continue
        Z = w0 * A[2] + w1 * B[2] + w2 * Cc[2]
        ii, jj = np.nonzero(m)
        kk = np.clip(np.ceil((Z[m] - lo[2]) / h).astype(int), 0, nz)
        np.add.at(diff, (ii + i0, jj + j0, kk), 1)
    cnt = np.cumsum(diff, axis=2)[:, :, :nz]
    occ = (cnt % 2) == 1
    # oprava stlpcov s neparnym poctom priesecnikov (luc trafil hranu): prevezmi suseda
    bad = (diff.sum(2) % 2) == 1
    if bad.any():
        bi, bj = np.nonzero(bad)
        for i, j in zip(bi, bj):
            for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                p, q = i + di, j + dj
                if 0 <= p < nx and 0 <= q < ny and not bad[p, q]:
                    occ[i, j] = occ[p, q]; break
    return np.ascontiguousarray(occ.transpose(2, 0, 1)), lo, int(bad.sum())


class UF:
    def __init__(self):
        self.p = [0]; self.out = [True]          # uzol 0 = okolie
    def new(self, outside=False):
        self.p.append(len(self.p)); self.out.append(outside); return len(self.p) - 1
    def find(self, a):
        while self.p[a] != a:
            self.p[a] = self.p[self.p[a]]; a = self.p[a]
        return a
    def union(self, a, b):
        a, b = self.find(a), self.find(b)
        if a == b:
            return a
        if self.out[b] and not self.out[a]:
            a, b = b, a
        self.p[b] = a; self.out[a] = self.out[a] or self.out[b]
        return a


def analyse(occ, lo, Bm, h=H, min_area=2.0):
    """occ[k, i, j]; platforma pod vrstvou 0 (diel na podperach: priestor pod dielom je otvoreny)"""
    nz, nx, ny = occ.shape
    st4 = ndi.generate_binary_structure(2, 1)
    uf = UF()
    prev_lab = None; prev_ids = None
    comp = {}      # koren -> dict(vol, amax, k0, k_last, cx..)
    node_info = {}
    cups_closed = []
    prev_solid = np.zeros((nx, ny), bool)
    islands = []
    for k in range(nz):
        sol = occ[k]
        # ---- ostrovy
        if k > 0 and sol.any():
            lab_s, ns = ndi.label(sol, structure=np.ones((3, 3)))
            if ns:
                ov = ndi.maximum(prev_solid, lab_s, index=np.arange(1, ns + 1))
                ar = ndi.sum(np.ones_like(lab_s), lab_s, index=np.arange(1, ns + 1)) * h * h
                for q in np.nonzero(ov == 0)[0]:
                    ci, cj = ndi.center_of_mass(lab_s == q + 1)
                    p = np.array([lo[0] + ci * h, lo[1] + cj * h, lo[2] + (k + 0.5) * h]) @ Bm      # spat do suradnic dielu
                    islands.append(dict(vyska=round(k * h, 1), plocha=round(float(ar[q]), 2), bod_dielu=[round(float(v), 1) for v in p]))
        prev_solid = sol
        # ---- vzduch
        air = ~sol
        lab, n = ndi.label(air, structure=st4)
        ids = np.zeros(n + 1, np.int64)
        if n:
            border = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
            areas = ndi.sum(np.ones_like(lab), lab, index=np.arange(1, n + 1)) * h * h
            for q in range(1, n + 1):
                ids[q] = 0 if (q in border or k == 0) else uf.new(False)
                if ids[q]:
                    node_info[ids[q]] = (k, float(areas[q - 1]))
            if prev_lab is not None:
                m = (lab > 0) & (prev_lab > 0)
                pairs = np.unique(np.stack([lab[m], prev_lab[m]], 1), axis=0) if m.any() else []
                for q, r in pairs:
                    uf.union(ids[q], prev_ids[r])
        # stav po vrstve k: uzavrete komponenty, ktore maju uzol vo vrstve k
        if n:
            for q in range(1, n + 1):
                if ids[q] == 0:
                    continue
                root = uf.find(ids[q])
                if uf.out[root]:
                    continue
                ccc = comp.setdefault(("live", root), dict(k0=k, vol=0.0, amax=0.0, k_last=k, seed=None))
        prev_lab, prev_ids = lab, ids
        # akumulacia: pre kazdy uzol vrstvy k, ktory je teraz uzavrety, pripocitaj plochu
        live = {}
        if n:
            for q in range(1, n + 1):
                if ids[q] == 0:
                    continue
                root = uf.find(ids[q])
                if not uf.out[root]:
                    live[root] = live.get(root, 0.0) + node_info[ids[q]][1]
        # prekluc zaznamy na aktualne korene
        newcomp = {}
        for (tag, r), cc in comp.items():
            r2 = uf.find(r)
            if uf.out[r2]:
                cc["k_vent"] = k
                if cc["vol"] > 0:
                    cups_closed.append(cc)
                continue
            if ("live", r2) in newcomp:
                o = newcomp[("live", r2)]
                o["vol"] += cc["vol"]; o["amax"] = max(o["amax"], cc["amax"]); o["k0"] = min(o["k0"], cc["k0"])
            else:
                newcomp[("live", r2)] = cc
        comp = newcomp
        for r, a in live.items():
            cc = comp.setdefault(("live", r), dict(k0=k, vol=0.0, amax=0.0, k_last=k, seed=None))
            cc["vol"] += a * h; cc["amax"] = max(cc["amax"], a); cc["k_last"] = k
            if cc["seed"] is None or a >= cc["amax"]:
                q = [qq for qq in range(1, n + 1) if ids[qq] and uf.find(ids[qq]) == r]
                ci, cj = ndi.center_of_mass(np.isin(lab, q))
                p = np.array([lo[0] + ci * h, lo[1] + cj * h, lo[2] + (k + 0.5) * h]) @ Bm
                cc["seed"] = [round(float(v), 1) for v in p]
    for (tag, r), cc in comp.items():
        cc["k_vent"] = None
        if cc["vol"] > 0:
            cups_closed.append(cc)
    cups = [dict(objem_mm3=round(c["vol"], 1), max_plocha_mm2=round(c["amax"], 1), od_vysky=round(c["k0"] * h, 1),
                 odvzdusnenie_vo_vyske=(None if c["k_vent"] is None else round(c["k_vent"] * h, 1)),
                 hlbka_mm=round(((c["k_vent"] if c["k_vent"] is not None else c["k_last"] + 1) - c["k0"]) * h, 1), bod_dielu=c["seed"])
            for c in cups_closed if c["amax"] >= min_area and c["vol"] >= 3.0]
    cups.sort(key=lambda c: -c["max_plocha_mm2"])
    isl = [i for i in islands if i["plocha"] >= 0.3]
    return cups, isl


def down_area(T, u, deg=35.0):
    n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); ar = 0.5 * np.linalg.norm(n, axis=1)
    n = n / np.maximum(2 * ar, 1e-12)[:, None]
    m = (n @ u) < -math.cos(math.radians(deg))
    c = T.mean(1)
    return float(ar[m].sum()), c[m], ar[m]


def rot(axis, deg):
    a = math.radians(deg); c, s = math.cos(a), math.sin(a)
    return {"x": np.array([[1, 0, 0], [0, c, -s], [0, s, c]]), "y": np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]]),
            "z": np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]])}[axis]


# diel: [(popis orientacie, smer "od platformy" v suradniciach dielu)]
def tilt(u, axis, deg):
    return (rot(axis, deg) @ np.asarray(u, float)).tolist()


ORI = {
    "T_stred": [("spec 4.7: vrch k platforme, naklon 20 okolo X", tilt((0, 0, -1), "x", 20)), ("spodny okraj k platforme, naklon 20 okolo X", tilt((0, 0, 1), "x", 20))],
    "T_bok_L": [("otvorena strana (svik) od platformy, naklon 25 okolo Y", tilt((-1, 0, 0), "y", 25)), ("svik k platforme, naklon 25", tilt((1, 0, 0), "y", 25))],
    "T_dvere": [("vnutorna plocha k platforme (spec)", (0, 1, 0)), ("stojato, spodna hrana k platforme, naklon 20 okolo X", tilt((0, 0, 1), "x", -20))],
    "T_klb_L": [("celo ramena od platformy (K10: arm interface face up)", (1, 0, 0)), ("celo ramena k platforme", (-1, 0, 0))],
    "T_puzdro_L": [("os zvislo, priruba k platforme", (1, 0, 0))],
    "T_svetlovod": [("priruba k platforme", (0, -1, 0))],
    "T_mriezka": [("priruba k platforme", (0, -1, 0))],
    "T_drziak_led": [("otvorena strana od platformy", (0, -1, 0)), ("otvorena strana k platforme", (0, 1, 0))],
    "T_drziak_repro": [("naplocho", (0, 1, 0))],
    "T_spodok": [("spec 4.7: spodok (pata) k platforme, naklon 15 okolo X", tilt((0, 0, 1), "x", 15)), ("vana k platforme, naklon 15 okolo X", tilt((0, 0, -1), "x", 15))],
    "T_ram": [("FDM poloha: stojato, spodok k platforme", (0, 0, 1)), ("stojato, naklon 20 okolo X", tilt((0, 0, 1), "x", 20)), ("hore nohami (stlpy k platforme), naklon 20 okolo X", tilt((0, 0, -1), "x", 20))],
    "T_paluba": [("FDM: spodok k platforme", (0, 0, 1)), ("na hrane, naklon 30 okolo X", tilt((0, 0, 1), "x", 60))],
    "T_prichytka_fpc": [("naplocho", (0, 0, 1))],
    "Z_naboj_test": [("doska k platforme (plocho)", (0, 0, 1)), ("doska naklonena 30 okolo X", tilt((0, 0, 1), "x", 30))],
    "P_sachta": [("K10: vrch stola k platforme, os sachty zvislo", (0, 0, -1)), ("vrch stola k platforme, naklon 15 okolo X", tilt((0, 0, -1), "x", 15)), ("spodok k platforme", (0, 0, 1))],
    "P_koleso": [("naplocho, celo k platforme", (0, 0, 1)), ("naplocho, opacne", (0, 0, -1))],
    "P_drziak_serva": [("FDM: stojato na policke", (0, 0, 1)), ("zadna doska k platforme", (0, 1, 0))],
    "P_kluka": [("naplocho", (1, 0, 0))],
    "L_pata": [("naplocho, vrch k platforme", (0, 0, -1)), ("na hrane, naklon 30", tilt((0, 1, 0), "x", 30))],
    "L_jazyk": [("FDM poloha", (-1, 0, 0))],
    "L_ucho": [("doska ucha k platforme", (1, 0, 0))],
}

if __name__ == "__main__":
    names = sys.argv[1:] or list(ORI)
    res = {}
    if os.path.exists(OUT + "/t03_tlac.json"):
        res = json.load(open(OUT + "/t03_tlac.json"))
    for n in names:
        T = read_stl(f"{T4}/stl/{n}.stl")
        res[n] = []
        for txt, u in ORI[n]:
            Bm = basis(u)
            Tp = T @ Bm.T
            ext = (Tp.reshape(-1, 3).max(0) - Tp.reshape(-1, 3).min(0)).round(1).tolist()
            s3 = sorted(ext); fits = s3[0] <= 123 and s3[1] <= 218 and s3[2] <= 220 and ext[2] <= 220
            occ, lo, nbad = voxelize(Tp)
            cups, isl = analyse(occ, lo, Bm)
            da, dc, dar = down_area(T, np.asarray(Bm[2]))
            # kde su plochy obratene k platforme (suradnice dielu): histogram po z dielu a |x|
            r = dict(orientacia=txt, smer_od_platformy=[round(float(v), 3) for v in Bm[2]], rozmer_xy_vyska=ext, zmesti_sa=bool(fits),
                     objem_voxel_mm3=round(float(occ.sum()) * H ** 3, 0), stlpce_opravene=nbad,
                     prisavky=cups[:8], n_prisaviek=len(cups), ostrovy_n=len(isl), ostrovy=sorted(isl, key=lambda i: -i["plocha"])[:14],
                     plocha_k_platforme_mm2=round(da, 0))
            res[n].append(r)
            say(n, "|", txt, "| rozmer", ext, "| prisavky", len(cups), [(c["max_plocha_mm2"], c["hlbka_mm"], c["bod_dielu"]) for c in cups[:4]],
                "| ostrovy", len(isl), "| plocha k platforme", round(da))
        json.dump(res, open(OUT + "/t03_tlac.json", "w"), indent=1, ensure_ascii=False)
    say("hotovo")

"""t04 - ZAVITY / VLOZKY / KOLIKY / MAGNETY v zivici (pravidla Z3.4 - Z3.6): pre kazdy spojovaci prvok zmeria na STL hostitela
priemer otvoru, najtensiu stenu okolo otvoru (radialne luce po 15 deg v 3 rezoch pozdlz osi) a dlzku v materiali.
Spustenie: /opt/venv/bl/bin/python t04_zavity.py -> t04_zavity.json"""
import sys, json
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4/overenie_montaz")
from om_lib import *

PRINTED_N = [n for n in ALL if PRINTED[n]]
TREE = {n: Group([n]) for n in PRINTED_N}


def axis_of(n):
    V = mesh(n).V
    c = V.mean(0)
    ext = V.max(0) - V.min(0)
    # os = smer, v ktorom ma diel kruhovy prierez: pre skrutky / vlozky / koliky su dva rozmery bbox rovnake (alebo je to najdlhsi smer)
    u, s, vt = np.linalg.svd(V - c, full_matrices=False)
    d = vt[0]
    # zarovnaj na hlavnu os ak je blizko
    k = int(np.argmax(np.abs(d)))
    if abs(d[k]) > 0.97:
        d = np.zeros(3); d[k] = 1.0
    # pre kratke valce (magnet 5 x 2, vlozka 3.5 x 4 ...) je hlavna os PCA nespolahliva -> vezmi smer najmensieho rozptylu, ak su dva vacsie rovnake
    if s[0] / max(s[1], 1e-9) < 1.25:
        d = vt[2]
        k = int(np.argmax(np.abs(d)))
        if abs(d[k]) > 0.97:
            d = np.zeros(3); d[k] = 1.0
    t = (V - c) @ d
    return c, d / np.linalg.norm(d), float(t.min()), float(t.max()), V


def radial(host, c, d, t, nang=24, rmax=14.0):
    """z bodu na osi (c + t d) radialne luce: (polomer otvoru, stena za nim).  Vrati zoznam (r_otvor, stena) pre luce, ktore zacinaju vo vzduchu"""
    G = TREE[host]
    a = np.cross(d, [0, 0, 1.0] if abs(d[2]) < 0.9 else [1.0, 0, 0]); a /= np.linalg.norm(a); b = np.cross(d, a)
    p0 = c + t * d
    out = []
    for k in range(nang):
        ang = 2 * math.pi * k / nang
        u = math.cos(ang) * a + math.sin(ang) * b
        h = G.tree.ray_cast(Vector(p0), Vector(u), rmax)
        if h[0] is None:
            out.append((None, None)); continue
        r1 = h[3]
        h2 = G.tree.ray_cast(Vector(p0 + u * (r1 + 0.02)), Vector(u), rmax)
        w = h2[3] + 0.02 if h2[0] is not None else None
        out.append((r1, w))
    return out


def host_of(n):
    """tlaceny diel, v ktorom prvok sedi: najvacsi podiel vrcholov prvku vnutri / do 0.25 mm od povrchu"""
    V = mesh(n).V
    best = (0, None)
    for hn in PRINTED_N:
        Vh = mesh(hn).V
        lo, hi = Vh.min(0) - 0.5, Vh.max(0) + 0.5
        if np.any(V.max(0) < lo) or np.any(V.min(0) > hi):
            continue
        G = TREE[hn]
        cnt = 0
        for p in V[:: max(1, len(V) // 120)].tolist():
            h = G.tree.find_nearest(Vector(p), 0.3)
            if h[0] is not None:
                cnt += 1
        if cnt > best[0]:
            best = (cnt, hn)
    return best[1]


def measure(n, host=None, ts=None):
    c, d, t0, t1, V = axis_of(n)
    host = host or host_of(n)
    if host is None:
        return dict(prvok=n, host=None)
    r_el = float(np.linalg.norm(np.cross(V - c, d), axis=1).max())
    rows = []
    for f in (ts or (0.2, 0.5, 0.8)):
        t = t0 + f * (t1 - t0)
        rr = [(a, b) for a, b in radial(host, c, d, t) if a is not None]
        if len(rr) < 12:
            rows.append(dict(f=f, pozn="mimo materialu (luce netrafili otvor)", n_lucov=len(rr))); continue
        r1 = np.array([a for a, b in rr]); w = np.array([b if b is not None else np.nan for a, b in rr])
        rows.append(dict(f=f, d_otvoru=round(2 * float(np.median(r1)), 2), stena_min=round(float(np.nanmin(w)), 2), stena_median=round(float(np.nanmedian(w)), 2),
                         n_lucov=len(rr)))
    return dict(prvok=n, host=host, mat_host=MAT[host], d_prvku=round(2 * r_el, 2), dlzka=round(t1 - t0, 2), os=[round(float(x), 2) for x in d],
                stred=[round(float(x), 2) for x in c], rezy=rows)


R = {}
def main():
    GROUPS = {
        "vlozky": [n for n in ALL if n.startswith("vl_") or n.startswith("vlozka_")],
        "magnety": [n for n in ALL if n.startswith("magnet_")],
        "koliky_capy": ["cap_pan", "cap_kluky", "kolik_kolesa_1", "kolik_kolesa_2", "kolik_dorazu", "kolik_ucha"],
        "skrutky": [n for n in ALL if n.startswith("skr")],
    }
    for g, names in GROUPS.items():
        R[g] = []
        for n in names:
            try:
                m = measure(n)
            except Exception as e:
                m = dict(prvok=n, chyba=str(e))
            R[g].append(m)
            rz = m.get("rezy") or []
            say(g, n, "->", m.get("host"), m.get("mat_host"), "d", m.get("d_prvku"), "L", m.get("dlzka"),
                [(q.get("d_otvoru"), q.get("stena_min")) for q in rz])
    json.dump(R, open(OUT + "/t04_zavity.json", "w"), indent=1, ensure_ascii=False)
    say("hotovo")


if __name__ == "__main__":
    main()

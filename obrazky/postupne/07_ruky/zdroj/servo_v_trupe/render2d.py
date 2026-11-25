"""Slovak-labelled section images of the measured free space (Pillow, DejaVu Sans).  Reads map1.npz, exact_multi_*.json,
exact_kst.json, layout_a.json.  Writes obr/01_volne_miesto_v_trupe.png and obr/02_servo_na_osi_ramena.png."""
import sys, os, json, math
sys.dont_write_bytecode = True
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial.transform import Rotation as Rot
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R1/geo"); sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4")
OUT = os.path.join(HERE, "obr"); os.makedirs(OUT, exist_ok=True)
FN = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"; FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
f12, f14, f16, f20, f26 = (ImageFont.truetype(FN, s) for s in (12, 14, 16, 20, 26))
b14, b16, b20, b28 = (ImageFont.truetype(FB, s) for s in (14, 16, 20, 28))
D = np.load(os.path.join(HERE, "map1.npz"))
lo, H = D["lo"], float(D["h"]); N = tuple(D["n"])
interior, static, moving, free = D["interior"], D["static"], D["moving"], D["free"]
lower, s1 = D["lower"], D["s1"]
free_opt = interior & ~static & ~moving
C_OUT, C_INT, C_STAT, C_MOV, C_FREE, C_TIGHT, C_LOW, C_S1 = ((255, 255, 255), (238, 238, 238), (150, 152, 158), (246, 166, 70),
                                                            (70, 170, 90), (178, 222, 178), (92, 150, 215), (170, 110, 200))


def J(name, default=None):
    p = os.path.join(HERE, name)
    return json.load(open(p)) if os.path.exists(p) else default


def cls_at(P):
    """class index per world point: 0 outside, 1 interior-other, 2 static, 3 moving, 4 free, 5 tight (free without the
    clearance), 6 free but on the T_stred lowering path, 7 free but on the S1 path"""
    k = np.floor((P - lo) / H).astype(int)
    ok = np.all((k >= 0) & (k < np.array(N)), axis=1)
    out = np.zeros(len(P), np.int8)
    kk = k[ok]
    i, j, l = kk[:, 0], kk[:, 1], kk[:, 2]
    c = np.ones(len(kk), np.int8)
    c[~interior[i, j, l]] = 0
    c[static[i, j, l]] = 2
    c[moving[i, j, l]] = 3
    c[free_opt[i, j, l]] = 5
    f = free[i, j, l]
    c[f] = 4
    c[f & lower[i, j, l]] = 6
    c[f & s1[i, j, l] & ~lower[i, j, l]] = 7
    out[ok] = c
    return out


PAL = np.array([C_OUT, C_INT, C_STAT, C_MOV, C_FREE, C_TIGHT, C_LOW, C_S1], np.uint8)


class Panel:
    def __init__(self, axis, value, hr, vr, scale, title):
        self.axis, self.value, self.hr, self.vr, self.s, self.title = axis, value, hr, vr, scale, title
        rem = [k for k in range(3) if k != axis]
        self.ah, self.av = rem
        self.w = int((hr[1] - hr[0]) * scale); self.h = int((vr[1] - vr[0]) * scale)

    def world(self, px, py):
        P = np.zeros((len(px), 3))
        P[:, self.axis] = self.value
        P[:, self.ah] = self.hr[0] + (px + 0.5) / self.s
        P[:, self.av] = self.vr[1] - (py + 0.5) / self.s
        return P

    def pix(self, h, v):
        return ((h - self.hr[0]) * self.s, (self.vr[1] - v) * self.s)

    def image(self):
        py, px = np.mgrid[0:self.h, 0:self.w]
        P = self.world(px.ravel(), py.ravel())
        c = cls_at(P)
        img = PAL[c].reshape(self.h, self.w, 3)
        return Image.fromarray(img), P.reshape(self.h, self.w, 3)


def outline(im_draw, mask, colour, ox, oy, width=2, dash=False):
    e = mask & ~(np.roll(mask, 1, 0) & np.roll(mask, -1, 0) & np.roll(mask, 1, 1) & np.roll(mask, -1, 1))
    ys, xs = np.nonzero(e)
    for x, y in zip(xs, ys):
        if dash and ((x // 6 + y // 6) % 2):
            continue
        im_draw.rectangle([ox + x - width // 2, oy + y - width // 2, ox + x + width // 2, oy + y + width // 2], fill=colour)


def box_mask(Pimg, centre, R, dims):
    q = (Pimg.reshape(-1, 3) - np.array(centre)) @ np.array(R)
    m = np.all(np.abs(q) <= np.array(dims) / 2.0, axis=1)
    return m.reshape(Pimg.shape[:2])


def axes_grid(d, pnl, ox, oy, step=10):
    for v in range(-100, 101, step):
        x, _ = pnl.pix(v, 0)
        if 0 <= x <= pnl.w:
            d.line([(ox + x, oy), (ox + x, oy + pnl.h)], fill=(205, 205, 225), width=1)
            d.text((ox + x + 2, oy + pnl.h + 2), f"{v}", fill=(70, 70, 110), font=f12)
        _, y = pnl.pix(0, v)
        if 0 <= y <= pnl.h:
            d.line([(ox, oy + y), (ox + pnl.w, oy + y)], fill=(205, 205, 225), width=1)
            d.text((ox - 30, oy + y - 7), f"{v}", fill=(70, 70, 110), font=f12)


def blend_grid(img, step_px):
    a = np.array(img).astype(np.int16)
    return Image.fromarray(a.astype(np.uint8))


def text_box(d, x, y, lines, font=f16, fill=(25, 25, 25), lh=22):
    for i, t in enumerate(lines):
        d.text((x, y + i * lh), t, fill=fill, font=font)


# --------------------------------------------------------------------------- data for the overlays
scs = J("exact_multi_scs0009_FL.json") or {}
kst = J("exact_kst.json") or {}
LA = J("layout_a.json") or {}
m2 = J("map2.json") or {}


def pose(rec):
    if not rec:
        return None
    R = Rot.from_rotvec(rec["rotvec"]).as_matrix()
    return rec["centre"], R, rec["case"]


P_SCS = pose(scs) if scs else None
P_KST = pose(kst) if kst else None


# =========================================================================== image 1: free space map (left half)
def image1():
    S = 7.0
    panels = [Panel(2, -17.0, (-4, 52), (-42, 42), S, "Pôdorys vo výške osi ramena (z = −17)"),
              Panel(2, -56.0, (-4, 52), (-42, 42), S, "Pôdorys v dolnej časti trupu (z = −56)"),
              Panel(0, 40.0, (-42, 42), (-86, 6), S, "Bočný rez pod bočným krytom (x = 40)"),
              Panel(1, -22.0, (-4, 52), (-86, 6), S, "Rez vpredu pred stĺpom (y = −22)")]
    W, Hh = 1780, 1540
    im = Image.new("RGB", (W, Hh), (255, 255, 255))
    d = ImageDraw.Draw(im)
    d.text((40, 20), "Je v trupe miesto pre servo ramena? – zmerané voľné miesto (ľavá strana, pravá je zrkadlová)", fill=(20, 20, 20), font=b28)
    d.text((40, 62), "Model trupu T4 (169 dielov) + krk a hlava B; mriežka 0,5 mm; otáčanie hlavy −90,3…+90,3°, zdvih krku 0–20 mm",
           fill=(60, 60, 60), font=f16)
    d.text((40, 92), "Odpoveď: nie – servo s rozsahom aspoň 180° (SCS0009, MG90S, STS3032) sa do trupu nezmestí nikde.", fill=(170, 0, 0), font=b20)
    pos = [(70, 160), (540, 160), (70, 820), (740, 820)]
    for pnl, (ox, oy) in zip(panels, pos):
        img, Pimg = pnl.image()
        im.paste(img, (ox, oy))
        axes_grid(d, pnl, ox, oy)
        d.rectangle([ox, oy, ox + pnl.w, oy + pnl.h], outline=(90, 90, 90), width=1)
        d.text((ox, oy - 24), pnl.title, fill=(20, 20, 20), font=b16)
        hn, vn = "xyz"[pnl.ah], "xyz"[pnl.av]
        d.text((ox + pnl.w - 36, oy + pnl.h + 16), f"{hn} [mm]", fill=(70, 70, 110), font=f12)
        d.text((ox - 44, oy - 2), f"{vn} [mm]", fill=(70, 70, 110), font=f12)
        # shoulder axis
        if pnl.axis == 0:
            x, y = pnl.pix(3.0, -17.0)
            d.ellipse([ox + x - 5, oy + y - 5, ox + x + 5, oy + y + 5], outline=(200, 0, 0), width=2)
            d.text((ox + x + 8, oy + y - 22), "os ramena", fill=(200, 0, 0), font=f14)
        elif pnl.axis == 2 and abs(pnl.value + 17) < 0.1:
            x0, y = pnl.pix(30, 3.0); x1, _ = pnl.pix(52, 3.0)
            d.line([(ox + x0, oy + y), (ox + x1, oy + y)], fill=(200, 0, 0), width=2)
            d.text((ox + x0 - 70, oy + y - 20), "os ramena", fill=(200, 0, 0), font=f14)
        # overlays: SCS0009 closest pose (red dashed), KST X06 fit (dark green)
        for P_, col, dash in ((P_SCS, (210, 20, 20), True), (P_KST, (0, 90, 30), False)):
            if P_ is None:
                continue
            m = box_mask(Pimg, *P_)
            if m.any():
                outline(d, m, col, ox, oy, width=2, dash=dash)
    # labels inside panels (pointers)
    def lab(pi, h, v, text, col=(20, 20, 20), dx=8, dy=-8, font=f14):
        pnl = panels[pi]; ox, oy = pos[pi]
        x, y = pnl.pix(h, v)
        d.multiline_text((ox + x + dx, oy + y + dy), text, fill=col, font=font, spacing=2)
    lab(0, 0, 0, "otáčanie hlavy\n+ zdvih krku", (120, 60, 0), -40, -10)
    lab(0, 36.5, 12, "stĺp\nT_spodok", (40, 40, 40), -26, -40)
    lab(0, 44, -5, "T_klb", (40, 40, 40), -14, 30)
    lab(0, 31.5, -6, "medzera\n1,0 mm", (0, 90, 30), 4, -10)
    lab(1, 2, 0, "servo J1 (STS3215)", (40, 40, 40), -40, -40)
    lab(1, 1, -22, "servo otáčania\nhlavy", (40, 40, 40), -10, -6)
    lab(1, 4, 20, "riadiaca doska", (40, 40, 40), -10, -8)
    lab(2, 3, -45, "stĺp + zosilňovač", (40, 40, 40), -60, 30)
    lab(2, 0, -5, "T_klb (os ramena)", (40, 40, 40), -60, -2)
    lab(2, -30, -86, "zelené plochy sú hlboké len 7–8 mm (x 33…41)", (0, 90, 30), 0, -26)
    lab(3, 6, -25, "otáčanie hlavy", (120, 60, 0), -40, 0)
    lab(3, 26, -86, "modré: dráha výstupku T_stred", (30, 80, 160), -40, -26)
    # legend
    lx, ly = 1200, 160
    d.text((lx, ly), "Legenda", fill=(20, 20, 20), font=b20)
    items = [(C_STAT, "pevné diely trupu (kryty, stĺpy, servá, doska …)"),
             (C_MOV, "priestor, ktorým prechádza otáčanie hlavy\n±90° a zdvih krku 0–20 mm (+ kábel)"),
             (C_FREE, "voľné miesto s vôľou 1,0 mm k pohyblivým\na 0,3 mm k pevným dielom"),
             (C_TIGHT, "voľné len bez tejto vôle"),
             (C_LOW, "voľné, ale tadiaľ sa pri montáži spúšťa\nstredný kryt T_stred (servo len po ňom, zboku)"),
             (C_S1, "voľné, ale tadiaľ sa vyberá modul zdvihu\n(servis cez dvierka)")]
    y = ly + 36
    for col, t in items:
        d.rectangle([lx, y + 2, lx + 26, y + 20], fill=col, outline=(80, 80, 80))
        d.multiline_text((lx + 36, y), t, fill=(30, 30, 30), font=f14, spacing=3)
        y += 22 * (t.count("\n") + 1) + 12
    d.line([(lx, y + 12), (lx + 26, y + 12)], fill=(210, 20, 20), width=3)
    d.text((lx + 36, y + 2), "SCS0009 (23,2 × 12,1 × 21,5) v najlepšej nájdenej\npolohe – nezmestí sa", fill=(170, 0, 0), font=f14)
    y += 56
    d.line([(lx, y + 12), (lx + 26, y + 12)], fill=(0, 90, 30), width=3)
    d.text((lx + 36, y + 2), "KST X06 (20 × 7 × 16,6) – zmestí sa, ale len\ns rozsahom 120° a bez cesty k osi ramena", fill=(0, 80, 25), font=f14)
    y += 70
    # numbers
    d.text((lx, y), "Čo z merania vyplýva", fill=(20, 20, 20), font=b20)
    y += 34
    lines = NUM_LINES
    for t in lines:
        d.multiline_text((lx, y), t, fill=(25, 25, 25), font=f14, spacing=3)
        y += 21 * (t.count("\n") + 1) + 8
    p = os.path.join(OUT, "01_volne_miesto_v_trupe.png")
    im.save(p)
    return p


# =========================================================================== image 2: servo on the shoulder axis (layout a)
def arm_mask(Pimg, dx, ang=0.0):
    import armgeo as G
    Q = Pimg.reshape(-1, 3)
    Q2 = G.swing(Q, -ang) if ang else Q
    return G.inside_local(G.to_local(Q2, dx=dx)).reshape(Pimg.shape[:2])


def image2():
    import armgeo as G
    best = None
    for name, r in (LA.get("results") or {}).items():
        if name.startswith("SCS0009, case 21.5"):
            best = r["best"]
    pnl = Panel(1, 3.0, (14, 96), (-62, 14), 8.0, "Rez rovinou osi ramena (y = 3), pohľad spredu")
    W, Hh = 1460, 800
    im = Image.new("RGB", (W, Hh), (255, 255, 255))
    d = ImageDraw.Draw(im)
    d.text((40, 20), "Servo v trupe s hriadeľom priamo na osi ramena (variant a)", fill=(20, 20, 20), font=b28)
    d.text((40, 62), "Telo serva sa dá zasunúť najviac po vnútornú stenu stĺpa (x 34,4) – ďalej je otáčanie hlavy a servo zdvihu krku",
           fill=(60, 60, 60), font=f16)
    ox, oy = 70, 120
    img, Pimg = pnl.image()
    im.paste(img, (ox, oy))
    axes_grid(d, pnl, ox, oy)
    d.rectangle([ox, oy, ox + pnl.w, oy + pnl.h], outline=(90, 90, 90), width=1)
    d.text((ox, oy - 24), pnl.title, fill=(20, 20, 20), font=b16)
    d.text((ox + pnl.w - 36, oy + pnl.h + 16), "x [mm]", fill=(70, 70, 110), font=f12)
    # arm at the approved place and shifted
    a0 = arm_mask(Pimg, 0.0)
    outline(d, a0, (40, 40, 40), ox, oy, width=2)
    if best:
        dxn = best["arm_shift_needed"]
        a1 = arm_mask(Pimg, dxn)
        outline(d, a1, (30, 30, 200), ox, oy, width=2, dash=True)
        # case rectangle in this plane (phi of the best row)
        S_ = LA["results"]["SCS0009, case 21.5 (if 25.25 incl. shaft)"]
        phi = best["phi"]; e = np.array([math.cos(math.radians(phi)), math.sin(math.radians(phi))]); f = np.array([-e[1], e[0]])
        Q = Pimg.reshape(-1, 3)
        a = (Q[:, 1] - 3.0) * e[0] + (Q[:, 2] + 17.0) * e[1]; b = (Q[:, 1] - 3.0) * f[0] + (Q[:, 2] + 17.0) * f[1]
        mcase = ((Q[:, 0] >= best["x_in"]) & (Q[:, 0] <= best["case_out_face"]) & (a >= -5.9) & (a <= 23.2 - 5.9) & (np.abs(b) <= 6.05))
        mcase = mcase.reshape(Pimg.shape[:2])
        ov = np.array(im)
        sub = ov[oy:oy + pnl.h, ox:ox + pnl.w]
        sub[mcase] = (0.45 * sub[mcase] + 0.55 * np.array([220, 40, 40])).astype(np.uint8)
        ov[oy:oy + pnl.h, ox:ox + pnl.w] = sub
        im.paste(Image.fromarray(ov)); d = ImageDraw.Draw(im)
        outline(d, mcase, (180, 0, 0), ox, oy, width=2)
        msh = (Q[:, 0] >= best["case_out_face"]) & (Q[:, 0] <= best["spline_top"]) & (np.hypot(Q[:, 1] - 3, Q[:, 2] + 17) <= 2.0)
        outline(d, msh.reshape(Pimg.shape[:2]), (180, 0, 0), ox, oy, width=2)
        # dimension lines
        def hline(x0, x1, z, text, col=(150, 0, 0), dy=-22):
            p0 = pnl.pix(x0, z); p1 = pnl.pix(x1, z)
            d.line([(ox + p0[0], oy + p0[1]), (ox + p1[0], oy + p1[1])], fill=col, width=2)
            for p in (p0, p1):
                d.line([(ox + p[0], oy + p[1] - 6), (ox + p[0], oy + p[1] + 6)], fill=col, width=2)
            d.text((ox + p0[0] + 4, oy + p0[1] + dy), text, fill=col, font=f14)
        from t4_common import X_SH
        hline(best["x_in"], best["case_out_face"], -40.0, f"telo SCS0009 21,5 mm: x {fmt(best['x_in'])} … {fmt(best['case_out_face'])}")
        hline(X_SH, best["case_out_face"], -47.0, f"z trupu trčí {fmt(best['beyond_shell_mm'])} mm", dy=6)
        hline(50.8, 50.8 + dxn, 9.0, f"ruku treba posunúť von o {fmt(dxn)} mm", (30, 30, 200), dy=-22)
        x, y = pnl.pix(3.0 + 0, -17.0)
    x, y = pnl.pix(90, -17.0); x0, _ = pnl.pix(16, -17.0)
    d.line([(ox + x0, oy + y), (ox + x, oy + y)], fill=(200, 0, 0), width=1)
    d.text((ox + x - 80, oy + y + 4), "os ramena", fill=(200, 0, 0), font=f14)
    def lab(h, v, text, col=(20, 20, 20), font=f14):
        x, y = pnl.pix(h, v); d.multiline_text((ox + x, oy + y), text, fill=col, font=font, spacing=2)
    lab(15.5, -26, "otáčanie hlavy\n+ servo zdvihu", (120, 60, 0))
    lab(68, -50, "schválená ruka", (40, 40, 40))
    lab(74, 4, "ruka posunutá\n(potrebné pre variant a)", (30, 30, 200))
    # today's T_klb (analytic profile about the shoulder axis, KLB_PROFILE of t4_common + neck 38.6..40.6 r 11)
    import t4_common as TC
    prof = [(38.6, 11.0), (40.6, 11.0)] + [(TC.X_SH + a, r) for a, r in TC.KLB_PROFILE] + [(TC.X_SH + 12.0, 0.0)]
    up = [pnl.pix(x, -17.0 + r) for x, r in prof]; dn = [pnl.pix(x, -17.0 - r) for x, r in prof[::-1]]
    poly = [(ox + a, oy + b) for a, b in up + dn]
    d.line(poly + [poly[0]], fill=(0, 0, 0), width=1)
    lab(51.5, -2.5, "T_klb dnes", (0, 0, 0), f12)
    # legend
    lx, ly2 = 760, 590
    for col, t in ((C_STAT, "pevné diely trupu"), (C_MOV, "otáčanie hlavy + zdvih krku"), (C_FREE, "voľné miesto (s vôľou)"),
                   ((220, 90, 90), "telo serva SCS0009 na osi (prerezáva stĺp)")):
        d.rectangle([lx, ly2 + 2, lx + 26, ly2 + 20], fill=col, outline=(80, 80, 80))
        d.text((lx + 36, ly2), t, fill=(30, 30, 30), font=f14); ly2 += 28
    d.line([(lx, ly2 + 10), (lx + 26, ly2 + 10)], fill=(40, 40, 40), width=2); d.text((lx + 36, ly2), "schválená ruka (rez)", fill=(30, 30, 30), font=f14); ly2 += 28
    d.line([(lx, ly2 + 10), (lx + 26, ly2 + 10)], fill=(30, 30, 200), width=2); d.text((lx + 36, ly2), "ruka posunutá o potrebnú vzdialenosť", fill=(30, 30, 200), font=f14)
    # right column text
    lx, ly = 760, 120
    d.text((lx, ly), "Čísla (SCS0009, telo 21,5 mm – výhodnejší prípad)", fill=(20, 20, 20), font=b20)
    y = ly + 36
    for t in A_LINES:
        d.multiline_text((lx, y), t, fill=(25, 25, 25), font=f16, spacing=4)
        y += 24 * (t.count("\n") + 1) + 10
    p = os.path.join(OUT, "02_servo_na_osi_ramena.png")
    im.save(p)
    return p


def fmt(v, n=1):
    return f"{v:.{n}f}".replace(".", ",").replace("-", "−")


NUM_LINES = []
A_LINES = []
if __name__ == "__main__":
    cfg = J("render_texts.json", {})
    NUM_LINES[:] = cfg.get("img1", [])
    A_LINES[:] = cfg.get("img2", [])
    which = sys.argv[1:] or ["1", "2"]
    if "1" in which:
        print(image1())
    if "2" in which:
        print(image2())


# =========================================================================== image 3: KST X06 + cord / belt to the shoulder (layout b/c)
def image3():
    LB = J("layout_b.json")
    sh = np.array(LB["output_point"]); SHyz = np.array(LB["shoulder_axis_yz"])
    W, Hh = 1560, 860
    im = Image.new("RGB", (W, Hh), (255, 255, 255))
    d = ImageDraw.Draw(im)
    d.text((40, 20), "Servo vedľa stĺpa + prevod na os ramena (variant b / c)", fill=(20, 20, 20), font=b28)
    d.text((40, 62), "Jediné servo, ktoré sa vedľa ramena zmestí, je KST X06 (len 120°) v ľavom prednom rohu – cesta k osi je zatarasená",
           fill=(60, 60, 60), font=f16)
    panels = [Panel(0, 41.0, (-36, 24), (-62, 4), 8.0, "Rez x = 41 (pod bočným krytom, pohľad zľava)"),
              Panel(0, 43.5, (-36, 24), (-62, 4), 8.0, "Rez x = 43,5 (tesne pod stenou krytu)")]
    pos = [(70, 130), (600, 130)]
    for k, (pnl, (ox, oy)) in enumerate(zip(panels, pos)):
        img, Pimg = pnl.image()
        im.paste(img, (ox, oy)); axes_grid(d, pnl, ox, oy)
        d.rectangle([ox, oy, ox + pnl.w, oy + pnl.h], outline=(90, 90, 90), width=1)
        d.text((ox, oy - 24), pnl.title, fill=(20, 20, 20), font=b16)
        d.text((ox + pnl.w - 36, oy + pnl.h + 16), "y [mm]", fill=(70, 70, 110), font=f12)
        d.text((ox - 44, oy - 2), "z [mm]", fill=(70, 70, 110), font=f12)
        # cord corridor (r 3 / r 5) outline
        Q = Pimg.reshape(-1, 3)
        a = sh[1:]; b = SHyz; dd = b - a; Ld = np.linalg.norm(dd); u = dd / Ld
        P2 = Q[:, 1:]; t = np.clip(((P2 - a) @ u) / Ld, 0, 1); r = 3.0 + 2.0 * t
        m = (np.linalg.norm(P2 - (a + np.outer(t * Ld, u)), axis=1) <= r).reshape(Pimg.shape[:2])
        outline(d, m, (200, 0, 160), ox, oy, width=2)
        if P_KST is not None:
            mk = box_mask(Pimg, *P_KST)
            if mk.any():
                outline(d, mk, (0, 90, 30), ox, oy, width=2)
        x, y = pnl.pix(3.0, -17.0)
        d.ellipse([ox + x - 5, oy + y - 5, ox + x + 5, oy + y + 5], outline=(200, 0, 0), width=2)
        d.text((ox + x + 8, oy + y - 20), "os ramena", fill=(200, 0, 0), font=f14)
        x, y = pnl.pix(sh[1], sh[2])
        d.ellipse([ox + x - 4, oy + y - 4, ox + x + 4, oy + y + 4], outline=(0, 90, 30), width=2)
        d.text((ox + x - 30, oy + y + 8), "hriadeľ KST", fill=(0, 90, 30), font=f14)
    def lab(pi, h, v, text, col=(20, 20, 20)):
        pnl = panels[pi]; ox, oy = pos[pi]; x, y = pnl.pix(h, v)
        d.multiline_text((ox + x, oy + y), text, fill=col, font=f14, spacing=2)
    lab(0, -8, -33, "hlava stĺpa\nT_spodok", (30, 30, 30))
    lab(0, 6, -8, "objímka krytu\n+ T_klb", (30, 30, 30))
    lab(1, 6, -8, "objímka krytu\n+ T_klb", (30, 30, 30))
    lab(1, -35, -60, "stena krytu", (30, 30, 30))
    lx, y = 1130, 130
    d.text((lx, y), "Čísla", fill=(20, 20, 20), font=b20); y += 34
    lines = [
        f"• KST X06 v rohu: stred (29,2; −22,5; −55,6),\n  rezerva 1,5 mm; vkladá sa až po T_stred, zboku.",
        f"• Od hriadeľa KST k osi ramena je {fmt(LB['centre_distance_mm'])} mm.",
        "• Jedna dvojica koliesok m0,5 by mala\n  2 × 79 zubov, Ø 40,6 – nikde sa nezmestí.",
        "• Lanko alebo remienok (fialová dráha):\n  v každej rovine x 34–47 ho blokuje\n  aspoň 139 mm² dielov – hlava stĺpa\n  T_spodok, objímka krytu T_bok_L, T_klb.",
        "• Pri x 43,5 by lanko zasekávalo\n  1,5 mm do 2,2 mm steny bočného krytu.",
        "• KST má len 120° → prevod 1 : 1,5 do\n  rýchla; bez spätnej väzby (PWM).",
        "• Znova tlačiť: T_klb_L/P, T_bok_L/P\n  (+ T_spodok, ak lanko ide popri hlave\n  stĺpa); T_stred sa nedá zložiť,\n  kým je KST v rohu.",
        "• Záver: technicky na hrane, prakticky\n  horšie ako v1.",
    ]
    for t in lines:
        d.multiline_text((lx, y), t, fill=(25, 25, 25), font=f16, spacing=4); y += 24 * (t.count("\n") + 1) + 10
    y += 6
    for col, t in ((C_STAT, "pevné diely trupu"), (C_FREE, "voľné miesto (s vôľou)"), (C_LOW, "voľné, ale dráha T_stred pri montáži")):
        d.rectangle([lx, y + 2, lx + 26, y + 20], fill=col, outline=(80, 80, 80)); d.text((lx + 36, y), t, fill=(30, 30, 30), font=f14); y += 26
    d.line([(lx, y + 10), (lx + 26, y + 10)], fill=(200, 0, 160), width=3); d.text((lx + 36, y), "dráha lanka (kladky r 3 / r 5)", fill=(150, 0, 120), font=f14); y += 26
    d.line([(lx, y + 10), (lx + 26, y + 10)], fill=(0, 90, 30), width=3); d.text((lx + 36, y), "KST X06 (leží v x 21–37, v týchto rezoch nie je)", fill=(0, 90, 30), font=f14)
    p = os.path.join(OUT, "03_servo_vedla_stlpa_prevod.png")
    im.save(p)
    return p


if __name__ == "__main__" and "3" in sys.argv[1:]:
    print(image3())

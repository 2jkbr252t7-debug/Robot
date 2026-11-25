"""Slovak evidence image for K3: two sections of the LEFT shoulder (y = 3 front view, x = 39 side view) with the new parts,
rasterised from analytic inside-tests of the k3_parts geometry.  writes img/K3_rez_rameno.png"""
import sys, os, math
sys.dont_write_bytecode = True
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import k3_parts as KP
from matplotlib_path_free import inside_poly
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R1/geo")
import armgeo as AG
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4"); sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4/overenie3")
import t4_common as C
D = np.load(os.path.join(HERE, "k3map.npz"))
lo, h = D["lo"], float(D["h"]); hard, move, interior, lab = D["hard"], D["move"], D["interior"], D["lab"]
ln = [str(s) for s in D["lab_names"]]
bok = np.isin(lab, [ln.index("T_bok_L"), ln.index("T_bok_P")])
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
def font(s):
    try: return ImageFont.truetype(FONT, s)
    except Exception: return ImageFont.load_default()
F15, F18, F26 = font(15), font(18), font(28)
S = 16.0
COL = {"bg": (247, 247, 245), "hard": (172, 172, 180), "move": (245, 190, 120), "free": (255, 255, 255),
       "servo": (140, 100, 185), "rot": (215, 45, 45), "brg": (70, 110, 165), "stat": (45, 45, 55), "plug": (20, 20, 24),
       "arm": (215, 215, 215), "armline": (90, 90, 90)}
k = KP; YA, ZA, XV = k.YA, k.ZA, k.XV


def classify(Q):
    """colour key per point (later entries win)"""
    out = np.full(len(Q), "", dtype=object)
    x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
    ra = np.hypot(y - YA, z - ZA); rv = np.hypot(x - XV, y - YA)
    # arm pebble (interior) - drawn first, light
    ins = AG.inside_local(AG.to_local(Q)); out[ins] = "arm"
    # servo box + ears
    s = k.SV; c, sn = math.cos(math.radians(s["theta"])), math.sin(math.radians(s["theta"]))
    lx = c * (x - XV) + sn * (y - YA); ly = -sn * (x - XV) + c * (y - YA); lz = z - s["z_top"]
    box = (lx >= -s["sh"]) & (lx <= s["L"] - s["sh"]) & (np.abs(ly) <= s["W"] / 2) & (lz >= -s["H"]) & (lz <= 0)
    e = (s["ear_span"] - s["L"]) / 2
    ear = (lx >= -s["sh"] - e) & (lx <= s["L"] - s["sh"] + e) & (np.abs(ly) <= s["W"] / 2) & (lz >= -s["ear_below_top"][1]) & (lz <= -s["ear_below_top"][0])
    boss = (rv <= s["boss"][0]) & (lz >= 0) & (lz <= s["boss"][1])
    out[box | ear | boss] = "servo"
    # static: inner boss ring + stop ring + tongue
    b = k.BOSS
    st = ((ra >= b["r_in"]) & (ra <= b["r_out"]) & (x >= b["x"][0]) & (x <= b["x"][1])) | \
         ((ra >= b["stop"][0]) & (ra <= b["stop"][1]) & (x >= b["stop"][2]) & (x <= b["stop"][3]))
    st &= ~(rv <= 2.0)                                     # vertical shaft clearance bore
    tg = (rv >= k.TONGUE["r_in"]) & (rv <= k.TONGUE["r_out"]) & (z >= k.TONGUE["z"][0]) & (z <= k.TONGUE["z"][1])
    out[st | tg] = "stat"
    # plug + ring (black)
    p = k.PLUG
    xs = np.array([C.x_surface(yy, zz) for yy, zz in zip(y, z)]) - p["recess"]
    rmax = np.where(x < p["neck"][2], p["neck"][0], p["body"][0])
    pl = (x >= p["neck"][1]) & (ra <= rmax) & (x <= xs)
    pl &= ~((x < p["cav_x"]) & (ra < p["cav_r"]))
    pl &= ~((np.abs(y - YA) <= p["slot_y"]) & (z < ZA) & (x < 44.0))
    pl &= ~((x >= p["cav_x"]) & (x <= k.A1["x"][1]) & (ra < k.A1["D"] / 2)) & ~(ra < 2.3)
    rg = (ra <= k.RING["r"]) & (x >= xs - 0.5) & (x <= k.RING["x1"]) & (ra >= 2.3)
    rg &= ~((x >= k.A2["x"][0]) & (x <= k.A2["x"][1]) & (ra < k.A2["D"] / 2))
    rg |= (ra <= k.RING["seat_r"]) & (ra >= 2.3) & (x >= k.RING["seat_x"][0]) & (x <= k.RING["seat_x"][1])
    out[pl | rg] = "plug"
    # bearings
    br = np.zeros(len(Q), bool)
    for B_, ax in ((k.A1, "x"), (k.A2, "x"), (k.ARMBRG, "x")):
        br |= (ra >= B_["d"] / 2) & (ra <= B_["D"] / 2) & (x >= B_["x"][0]) & (x <= B_["x"][1])
    br |= (rv >= k.B1["d"] / 2) & (rv <= k.B1["D"] / 2) & (z >= k.B1["z"][0]) & (z <= k.B1["z"][1])
    out[br] = "brg"
    # rotating parts
    rot = (rv <= k.COUPLER["r"]) & (z >= k.COUPLER["z"][0]) & (z <= k.COUPLER["z"][1])
    rot |= (rv <= k.D_VS / 2) & (z >= k.COUPLER["z"][0]) & (z <= k.pinion_profile()[0][0])
    rot |= inside_poly(np.c_[z, rv], np.array(k.pinion_profile()))
    rot |= inside_poly(np.c_[x, ra], np.array(k.gear_profile()))
    rot |= (ra <= k.D_AS / 2) & (x >= k.gear_profile()[0][0]) & (x <= k.SHAFT_END)
    out[rot] = "rot"
    return out


def panel(axis, val, ru, rv_):
    W = int((ru[1] - ru[0]) * S); H = int((rv_[1] - rv_[0]) * S)
    U = ru[0] + (np.arange(W) + 0.5) / S; V = rv_[1] - (np.arange(H) + 0.5) / S
    UU, VV = np.meshgrid(U, V)
    if axis == "y": Q = np.c_[UU.ravel(), np.full(UU.size, val), VV.ravel()]
    else: Q = np.c_[np.full(UU.size, val), UU.ravel(), VV.ravel()]
    idx = np.floor((Q - lo) / h).astype(int); idx = np.clip(idx, 0, np.array(hard.shape) - 1)
    hd = hard[idx[:, 0], idx[:, 1], idx[:, 2]] | bok[idx[:, 0], idx[:, 1], idx[:, 2]]
    it = interior[idx[:, 0], idx[:, 1], idx[:, 2]]; mv = move[idx[:, 0], idx[:, 1], idx[:, 2]]
    rgb = np.zeros((UU.size, 3), np.uint8); rgb[:] = COL["bg"]
    rgb[it] = COL["free"]; rgb[mv] = COL["move"]; rgb[hd & it] = COL["hard"]
    cl = classify(Q)
    for key in ("arm", "servo", "stat", "plug", "brg", "rot"):
        rgb[cl == key] = COL[key]
    img = Image.fromarray(rgb.reshape(H, W, 3)); d = ImageDraw.Draw(img)
    def to_px(u, v): return (u - ru[0]) * S, (rv_[1] - v) * S
    for g in range(-200, 201, 10):
        x, _ = to_px(g, 0)
        if 0 <= x < W: d.line([(x, 0), (x, H)], fill=(200, 200, 225)); d.text((x + 2, H - 18), str(g), fill=(90, 90, 140), font=F15)
        _, yy = to_px(0, g)
        if 0 <= yy < H: d.line([(0, yy), (W, yy)], fill=(200, 200, 225)); d.text((3, yy + 2), str(g), fill=(90, 90, 140), font=F15)
    return img, to_px


A, tA = panel("y", 3.0, (22.0, 66.0), (-70.0, 3.0))
B, tB = panel("x", 39.0, (-26.0, 22.0), (-70.0, 3.0))
ML, MR = 360, 300
Wt = ML + A.size[0] + 30 + B.size[0] + MR; Ht = max(A.size[1], B.size[1]) + 340
cv = Image.new("RGB", (Wt, Ht), COL["bg"]); oA = (ML, 160); oB = (ML + A.size[0] + 30, 160)
cv.paste(A, oA); cv.paste(B, oB); d = ImageDraw.Draw(cv)
d.text((20, 14), "NOVA mini · ruky v2 · koncept K3: servo v trupe + jeden kužeľový pár (ľavé rameno; pravé je zrkadlové)", fill=(20, 20, 20), font=F26)
d.text((20, 58), "Vľavo: rez zvislou rovinou cez os ramena (y = 3), pohľad spredu.   Vpravo: rez x = 39 cez zvislý hriadeľ, pohľad zľava (predok robota vľavo).", fill=(60, 60, 60), font=F18)
d.text((20, 86), "Oranžová = priestor, ktorým sa otáča krk so servom zdvihu (±90°, zdvih 0–20 mm). Sivá = diely trupu, ktoré ostávajú. Biela = voľné miesto po úprave.", fill=(60, 60, 60), font=F18)
d.text((20, 114), "Fialová = servo SCS0009 · červená = otáčajúce sa diely · modrá = ložiská · čierna = nové pevné diely (stĺp, zátka s krúžkom) · svetlosivá = ruka.", fill=(60, 60, 60), font=F18)


def lab(tp, o, U, V, text, side, ty):
    x, y = tp(U, V); x += o[0]; y += o[1]
    if side == "L": tx = 20; anchor = "ls"; ex = ML - 8
    else: tx = Wt - MR + 10; anchor = "ls"; ex = Wt - MR + 4
    d.line([(x, y), (ex, ty)], fill=(0, 120, 170), width=2); d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=(0, 120, 170))
    for i, line in enumerate(text.split("\n")):
        d.text((tx, ty + 6 + 22 * i), line, fill=(10, 10, 10), font=F18, anchor=anchor)


lab(tA, oA, 43.0, -11.5, "kužeľové koleso 24 z\n(m 0,5, mosadz)", "L", 250)
lab(tA, oA, 37.5, -21.7, "kužeľový pastorok 16 z\n(prevod 1,5)", "L", 340)
lab(tA, oA, 38.0, -25.1, "ložisko MR63 v stĺpe", "L", 430)
lab(tA, oA, 35.0, -27.5, "stĺp (T_spodok), objímka\ns jazýčkom ložiska", "L", 490)
lab(tA, oA, 39.0, -32.0, "zvislý hriadeľ Ø3", "L", 580)
lab(tA, oA, 33.0, -36.0, "1,0 mm od otáčania krku\na serva zdvihu", "L", 650)
lab(tA, oA, 40.5, -40.5, "spojka na drážkovaní serva", "L", 760)
lab(tA, oA, 39.0, -56.0, "servo SCS0009 stojí,\nhriadeľ hore (pevne v trupe,\nkábel nejde cez kĺb)", "L", 900)
lab(tB, oB, 3.0, -17.0, "os ramena (y 3, z −17)", "R", 300)
lab(tB, oB, 11.0, -50.5, "ucho serva (rozmer\nneoverený)", "R", 820)
lab(tB, oB, 0.0, -60.0, "servo leží dopredu", "R", 950)
# extra labels for panel A on the right margin
lab(tA, oA, 46.0, -14.2, "2× ložisko MR74\nv čiernej zátke", "R", 200)
lab(tA, oA, 51.0, -10.8, "čierny krúžok Ø13:\njediné, čo z kĺbu vidno", "R", 400)
lab(tA, oA, 56.0, -23.5, "ložisko 6700 + trecia\nspojka v ruke", "R", 520)
lab(tA, oA, 60.0, -40.0, "pasívna ruka (bez\nelektroniky)", "R", 640)
y0 = Ht - 170
d.text((20, y0), "Prečo nie priamy pohon (servo priamo na osi): na osi ramena je od otáčajúceho sa serva zdvihu krku (r 33,4 + vôľa 1,0 → x 34,3) po vonkajší", fill=(20, 20, 20), font=F18)
d.text((20, y0 + 28), "povrch trupu (x 46,8) len 12,5 mm. Servo potrebuje pozdĺž hriadeľa ≥ 21,5 mm telo + 3,75 mm drážkovanie → trčalo by 9 mm z trupu. Ani bez modulu zdvihu", fill=(20, 20, 20), font=F18)
d.text((20, y0 + 56), "(len krk, r 26,5 + 1,0) by to nestačilo: 19,3 mm. Preto servo stojí nižšie, kde je trup širší, a rukou otáča cez jeden kužeľový pár (mazaný, pomalý = tichý).", fill=(20, 20, 20), font=F18)
d.text((20, y0 + 92), "Rozmery serva SCS0009 (výška tela 21,5, uši) sú neoverené – pred tlačou zmerať kúpený kus. Koncept, nie výkres na tlač.", fill=(130, 50, 50), font=F18)
out = os.path.join(HERE, "img", "K3_rez_rameno.png"); cv.save(out); print(out, cv.size)

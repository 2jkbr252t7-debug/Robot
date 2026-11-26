"""R3/tvar: comparison sheet of the 4 arm variants (Slovak labels).  CAD venv (Pillow).  Reads prev/fin/*.png + chk_variants.json
+ room.json.  Writes prev/fin/porovnanie_variantov.png"""
import os, sys, json
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import variants as VA
D = os.path.join(HERE, "prev", "fin")
CH = json.load(open(os.path.join(HERE, "chk_variants.json")))
RM = json.load(open(os.path.join(HERE, "room.json")))


def font(w, s):
    for fn in (f"/usr/share/fonts/opentype/inter/Inter-{w}.otf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if os.path.exists(fn):
            return ImageFont.truetype(fn, s)


F_T, F_S, F_H, F_N, F_B = font("Bold", 34), font("Regular", 17), font("SemiBold", 22), font("Regular", 16), font("SemiBold", 16)
BG = (244, 243, 240); CARD = (250, 250, 248); INK = (25, 25, 28); MUTED = (105, 105, 110); ACC = (196, 64, 40)


def comp(path, box):
    im = Image.open(path).convert("RGBA")
    W, H = im.size
    im = im.crop((int(box[0] * W), int(box[1] * H), int(box[2] * W), int(box[3] * H)))
    bg = Image.new("RGBA", im.size, CARD + (255,)); bg.alpha_composite(im)
    return bg.convert("RGB")


cols = list(VA.VIDS)
fr = {v: comp(os.path.join(D, f"front_{v}.png"), (0.02, 0.30, 0.98, 0.70)) for v in cols}
af = {v: comp(os.path.join(D, f"armfront_{v}.png"), (0.0, 0.0, 1.0, 0.92)) for v in cols}
he = {v: comp(os.path.join(D, f"hero_{v}.png"), (0.22, 0.38, 0.92, 0.72)) for v in cols}


def fit(d_, w):
    return {v: im.resize((w, int(im.height * w / im.width)), Image.LANCZOS) for v, im in d_.items()}


fr = fit(fr, 440); he = fit(he, 440)
af = {v: im.resize((int(im.width * 300 / im.height), 300), Image.LANCZOS) for v, im in af.items()}
cw, pad = 460, 30
Wt = pad * 2 + cw * 4 + 3 * 14
y0 = 150
ch_f, ch_h, ch_a = fr["0"].height, he["0"].height, 300
Ht = y0 + 50 + ch_f + 12 + ch_a + 12 + ch_h + 300 + 70
o = Image.new("RGB", (Wt, Ht), BG)
d = ImageDraw.Draw(o)
d.text((pad, 28), "NOVA mini · štíhlejšia ruka: varianty tvaru", font=F_T, fill=INK)
d.text((pad, 78), "Vnútorná plocha ruky, miesto uchytenia a medzera k trupu ostávajú; ruka chudne zvonka – hlavne vonkajší kryt.",
       font=F_S, fill=MUTED)
d.text((pad, 102), "Pohľad spredu (pokoj), detail ľavej ruky spredu, ľavá ruka zdvihnutá o 90°. Rýchly náhľad tvaru, nie výkres. Rozmery v mm.",
       font=F_S, fill=MUTED)
NAMES = {"0": "0 – súčasná ruka", "A": "A – mierne štíhlejšia", "B": "B – štíhla", "C": "C – najštíhlejšia"}
for i, v in enumerate(cols):
    x = pad + i * (cw + 14)
    d.rounded_rectangle((x, y0, x + cw, Ht - 70), 12, fill=CARD, outline=(222, 221, 216))
    d.text((x + 16, y0 + 12), NAMES[v], font=F_H, fill=ACC if v != "0" else INK)
    yy = y0 + 50
    o.paste(fr[v], (x + 10, yy)); yy += ch_f + 12
    o.paste(af[v], (x + 10 + (440 - af[v].width) // 2, yy)); yy += ch_a + 12
    o.paste(he[v], (x + 10, yy)); yy += ch_h + 14
    c = CH[v]; r = RM[v]
    p = VA.params(v)
    def f(a, n=1):
        return f"{a:.{n}f}".replace(".", ",")
    rows = [
        ("hrúbka ruky max", f(c['thickness_max'])),
        ("hrúbka pri kĺbe", f(c['thickness_at_joint_u022'])),
        ("  z toho vnútorná / vonkajšia časť (kryt)", f(c['inner_half_at_joint']) + " / " + f(c['outer_half_at_joint'])),
        ("šírka ruky (spredu dozadu) max", f(c['width_max'])),
        ("šírka robota cez ruky", f(c['robot_width_over_arms'])),
        ("medzera ruka – trup v pokoji", f(c['gap_rest'], 2)),
        ("najmenšia medzera −45° … +135°", f(c['gap_min_-45_135'], 2)),
        ("vnútri ruky na osi kĺbu (stena 1,2)", "x " + f(c["axis_inside_wall1.2_x"][0]) + " … " + f(c["axis_inside_wall1.2_x"][1])),
        ("puzdro r 12,7 sa zmestí po x", f(r['wall1.2_r12.7'][1]) if r["wall1.2_r12.7"] else "nezmestí sa"),
    ]
    for k, (a, b) in enumerate(rows):
        d.text((x + 16, yy + k * 27), a, font=F_N, fill=MUTED if a.startswith("  ") else INK)
        d.text((x + cw - 16, yy + k * 27), b, font=F_B, fill=INK, anchor="ra")
d.text((pad, Ht - 52), "Dnešný kĺb B1+ (puzdro r 12,7 až po x 67,6) sa zmestí len do súčasnej ruky; pre A, B, C treba kĺb v ruke skrátiť – rieši sa zvlášť.",
       font=F_S, fill=MUTED)
o.save(os.path.join(D, "porovnanie_variantov.png"))
print("sheet", o.size)

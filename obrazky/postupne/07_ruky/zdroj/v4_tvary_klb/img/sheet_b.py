"""R4 preview sheets for the arm-B rounding variants (Slovak labels).  CAD venv (Pillow).
reads prev/*.png (scene_v4.py renders) + ../tvar/out/nums_b.json; writes prev/nahlad_*.png"""
import sys, os, json
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R3/img/work")
import numpy as np
from PIL import Image, ImageDraw
import sheetlib as SL

HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(HERE, "prev")
N = json.load(open(os.path.join(HERE, "..", "tvar", "out", "nums_b.json")))
V = ["B0", "B1", "B2", "B3"]
TITLE = {"B0": "B0 – dnešná B", "B1": "B1 – squircle", "B2": "B2 – kvapka", "B3": "B3 – plochý kryt"}
IDEA = {"B0": "mydlový kamienok, vrch zrezaný,\nšev na rovníku",
        "B1": "mäkký hranol: ploché plochy,\ntesná, ale plynulá hrana",
        "B2": "plná pri kĺbe, štíhla k špičke,\nšev s tieňovou škárou",
        "B3": "plochý kryt s mäkkým lemom,\npresahuje vnútornú vaničku"}
BG, INK, MUTED, ACC = SL.BG, SL.INK, SL.MUTED, SL.ACCENT
CARD = (250, 250, 248)
F_T, F_S, F_H, F_B, F_SM = SL.font(40), SL.font(19, "Regular"), SL.font(24), SL.font(18, "Regular"), SL.font(15, "Regular")
F_BB = SL.font(18)


def comp(path, crop=None, w=None, h=None):
    im = Image.open(path).convert("RGBA")
    if crop:
        im = im.crop(crop)
    if w and not h:
        h = int(im.size[1] * w / im.size[0])
    if h and not w:
        w = int(im.size[0] * h / im.size[1])
    im = im.resize((w, h), Image.LANCZOS)
    bg = Image.new("RGBA", im.size, CARD + (255,)); bg.alpha_composite(im)
    return bg.convert("RGB")


def tight(path, pad=6):
    im = Image.open(path).convert("RGBA")
    im, _ = SL.crop_alpha(im, pad)
    return im


def fmt(x, d=1):
    from decimal import Decimal, ROUND_HALF_UP
    q = Decimal(repr(round(float(x), 6))).quantize(Decimal(1).scaleb(-d), rounding=ROUND_HALF_UP)
    return str(q).replace(".", ",")


W = 1400
M = 36
CW = (W - 2 * M - 3 * 18) // 4
rows = []
# ---------------------------------------------------------------- header
H0 = 150
sheet_parts = []
img = Image.new("RGB", (W, 2600), BG)
d = ImageDraw.Draw(img)
d.text((M, 26), "NOVA mini · ruka B: varianty zaoblení (náhľad)", font=F_T, fill=INK)
d.multiline_text((M, 84), "Ruka B (štíhla), ktorú si vybral, vľavo ako je dnes; vpravo tri modernejšie tvary. Plocha ruky pri trupe, uchytenie,\n"
                 "rozkyv a čierna špička ostávajú, medzera k trupu sa nezhoršila nikde. Spoločné: vrch ruky je teraz oblúk okolo osi kĺbu.",
                 font=F_S, fill=MUTED, spacing=8)
y = H0 + 10
# ---------------------------------------------------------------- column headers
CARD_H = int(os.environ.get("CARD_H", "1830"))
for i, v in enumerate(V):
    x = M + i * (CW + 18)
    d.rounded_rectangle([x, y, x + CW, y + CARD_H], 14, fill=CARD, outline=(222, 222, 218))
    d.text((x + 14, y + 12), TITLE[v], font=F_H, fill=INK if v == "B0" else ACC)
    d.multiline_text((x + 14, y + 44), IDEA[v], font=F_SM, fill=MUTED, spacing=4)
yA = y + 92


def label(x, yy, t):
    d.text((x + 14, yy), t, font=F_SM, fill=MUTED)


# row A: front of the robot (crop: torso + arms)
for i, v in enumerate(V):
    x = M + i * (CW + 18)
    im = comp(os.path.join(P, f"front_{v}.png"), crop=(70, 160, 430, 480), w=CW - 20)
    img.paste(im, (x + 10, yA + 22)); label(x, yA, "spredu")
yB = yA + 22 + im.size[1] + 14
# row A2: shoulder close-up from the front
for i, v in enumerate(V):
    x = M + i * (CW + 18)
    im = comp(os.path.join(P, f"armfront_{v}.png"), crop=(40, 0, 400, 470), w=CW - 20)
    img.paste(im, (x + 10, yB + 22)); label(x, yB, "spredu – detail ľavého ramena")
yC = yB + 22 + im.size[1] + 14
# row B: 3/4 with the left arm raised 90 deg
for i, v in enumerate(V):
    x = M + i * (CW + 18)
    im = comp(os.path.join(P, f"heroarm_{v}.png"), crop=(90, 20, 500, 400), w=CW - 20)
    img.paste(im, (x + 10, yC + 22)); label(x, yC, "zboku spredu, ľavá ruka hore 90°")
yD = yC + 22 + im.size[1] + 14
# row C: the arm alone - side (outside), 3/4, top
for i, v in enumerate(V):
    x = M + i * (CW + 18)
    label(x, yD, "samotná ruka: zvonka · zboku · zhora")
    a = tight(os.path.join(P, f"look_bok_{v}.png")); b = tight(os.path.join(P, f"look_tri_{v}.png"))
    c = tight(os.path.join(P, f"look_zhora_{v}.png"))
    H = 272
    ims = []
    for q, hh in ((a, H), (b, H), (c, int(H * 0.38))):
        s = hh / q.size[1]
        ims.append(q.resize((max(1, int(q.size[0] * s)), hh), Image.LANCZOS))
    # common scale for bok / tri (both 80 mm views); top view at the same mm scale as bok
    k = H / a.size[1]
    ims[1] = b.resize((int(b.size[0] * k * 0.95), int(b.size[1] * k * 0.95)), Image.LANCZOS)
    ims[2] = c.resize((int(c.size[0] * k * 0.95 * 9 / 8 * 8 / 9), int(c.size[1] * k * 0.95)), Image.LANCZOS)
    xx = x + 12
    for q in ims[:2]:
        bg = Image.new("RGBA", q.size, CARD + (255,)); bg.alpha_composite(q)
        img.paste(bg.convert("RGB"), (xx, yD + 26)); xx += q.size[0] + 6
    q = ims[2]
    bg = Image.new("RGBA", q.size, CARD + (255,)); bg.alpha_composite(q)
    img.paste(bg.convert("RGB"), (xx, yD + 26 + (H - q.size[1]) // 2))
yE = yD + 26 + 272 + 18
# row D: numbers
for i, v in enumerate(V):
    x = M + i * (CW + 18)
    n = N[v]
    base = N["B0"]
    step = n["seam_step"]
    seam = "šev 0,5 (ako dnes)" if step == 0 else (f"tieňová škára {fmt(step, 2)}" if step > 0 else f"kryt presahuje o {fmt(-step, 2)}")
    lines = [("hrúbka max / pri kĺbe", f"{fmt(n['thickness_max'])} / {fmt(n['thickness_joint'])}"),
             ("  kryt / vnútro pri kĺbe", f"{fmt(n['cover_joint'])} / {fmt(n['inner_joint'])}"),
             ("šírka ruky spredu dozadu", fmt(n["width_max"])),
             ("šírka cez ruky", fmt(n["robot_width_over_arms"])),
             ("medzera k trupu v pokoji", fmt(n["gap_rest"], 2)),
             ("  najmenšia pri pohybe", fmt(n["gap_min_m45_135"], 2)),
             ("stena nad kĺbom (M2b)", fmt(n["joint_wall_min"], 2)),
             ("šev", seam)]
    yy = yE
    for a_, b_ in lines:
        f = F_B if not a_.startswith("  ") else F_SM
        d.text((x + 14, yy), a_.strip() if not a_.startswith("  ") else "   " + a_.strip(), font=f, fill=INK if f == F_B else MUTED)
        w_ = d.textlength(b_, font=F_BB)
        d.text((x + CW - 14 - w_, yy), b_, font=F_BB, fill=INK)
        yy += 27
    ok = n["joint_wall_min"] >= 2.0
    col = (30, 140, 80) if ok else (214, 120, 20)
    d.rounded_rectangle([x + 10, yy + 8, x + CW - 10, yy + 62], 9, fill=col)
    t1 = "kĺb M2b sa zmestí, stena ≥ 2,0" if ok else f"kĺb M2b len tesne (stena {fmt(n['joint_wall_min'], 2)})"
    t2 = (f"rezerva +{fmt(n['joint_wall_min'] - 1.5, 2)} mm k požiadavke 1,5" if ok
          else f"rezerva len +{fmt(n['joint_wall_min'] - 1.5, 2)} mm")
    d.text((x + 20, yy + 13), t1, font=F_BB, fill=(255, 255, 255))
    d.text((x + 20, yy + 37), t2, font=F_SM, fill=(255, 255, 255))
yF = yy + 62 + 30
print("card bottom needed", yF - 10 - (H0 + 10), "have", CARD_H)
img = img.crop((0, 0, W, yF + 110))
d = ImageDraw.Draw(img)
foot = ("Rozmery v mm. Hrúbka = do strany (k trupu – von), šírka = spredu dozadu. Medzera k trupu: rovnaký výpočet ako doteraz (B0 = 3,70 / 1,13),\n"
        "najmenšia pri pohybe = v rozsahu −45° … +135°.  "
        "Nové varianty majú plochu pri trupe ako B, preto 3,70 v pokoji ostáva a pri zdvihnutí je medzera väčšia (oblejší vrch).\n"
        "Stena nad kĺbom = najtenšie miesto krytu nad otočným unášačom kĺbu M2b (overené fit.py). Kryt je nad kĺbom o ~0,5 mm plnší, preto hrúbka ~16 mm.\n"
        "Náhľad 500 px / 16 vzoriek – tvar, nie finálny render. Čierny krúžok kĺbu je zatiaľ z modelu v2 (kĺb sa ešte rieši zvlášť).")
d.multiline_text((M, yF), foot, font=F_SM, fill=MUTED, spacing=6)
out = os.path.join(P, "nahlad_zaoblenia.png")
img.save(out)
print(out, img.size)

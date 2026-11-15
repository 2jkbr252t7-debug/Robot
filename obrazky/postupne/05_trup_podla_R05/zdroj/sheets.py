"""Slovak comparison sheets: our renders next to the user's references R05 (torso) and R01 (whole robot).
Usage: python sheets.py <render dir> <out dir>"""
import sys, os
sys.path.insert(0, "/home/user/Robot")
from PIL import Image, ImageDraw
from nova.render.sheet import font, INK, MUTED

D, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
BG = (200, 196, 193)
PAPER = (246, 247, 245)


def comp(fn, bg=BG):
    b = Image.open(os.path.join(D, fn)).convert("RGBA")
    c = Image.new("RGBA", b.size, (*bg, 255)); c.alpha_composite(b)
    return c.convert("RGB")


def fit(im, w=None, h=None):
    k = (w / im.width) if w else (h / im.height)
    return im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)


r05 = Image.open("/home/user/Robot/referencie/R05_trup.png").convert("RGB")
r01 = Image.open("/tmp/claude-0/gapwf/fin/T2/r01_robot.png").convert("RGB")
# ------------------------------------------------------------------ sheet 1: torso vs R05
cells = [("spredu", (40, 130, 500, 520), "t_front.png"), ("zozadu", (560, 130, 1000, 520), "t_back.png"),
         ("pravý bok", (1110, 130, 1460, 520), "t_right.png"), ("zhora", (540, 580, 1010, 930), "t_top.png")]
CW, CH = 760, 640
S = Image.new("RGB", (60 + 4 * (CW + 20), 250 + 2 * (CH + 90) + 40), PAPER)
d = ImageDraw.Draw(S)
d.text((40, 30), "NOVA mini – trup podľa tvojho listu R05", font=font(60), fill=INK)
d.multiline_text((40, 112), "Hore tvoj návrh (R05), dole náš model z rovnakých pohľadov. Tvar je odmeraný z R05: hore pri krku úzky, ramená zaoblené, dole širší,\n"
                 "zaoblený predok aj zadok, tri diely (stredný pás + dva bočné), čierny spodok. Čierny krk a golier sú naše hotové diely.",
                 font=font(28, "Regular"), fill=MUTED, spacing=9)
for i, (nm, box, ours) in enumerate(cells):
    x = 40 + i * (CW + 20)
    a = r05.crop(box); a = fit(a, h=CH) if a.width / a.height < CW / CH else fit(a, w=CW)
    cell = Image.new("RGB", (CW, CH), (250, 250, 249)); cell.paste(a, ((CW - a.width) // 2, (CH - a.height) // 2))
    S.paste(cell, (x, 250))
    d.text((x, 250 + CH + 10), f"R05 – {nm}", font=font(32), fill=INK)
    b = comp(ours, (250, 250, 249)); b = fit(b, h=CH) if b.width / b.height < CW / CH else fit(b, w=CW)
    cell = Image.new("RGB", (CW, CH), (250, 250, 249)); cell.paste(b, ((CW - b.width) // 2, (CH - b.height) // 2))
    S.paste(cell, (x, 250 + CH + 90))
    d.text((x, 250 + 2 * CH + 100), f"NOVA – {nm}", font=font(32), fill=INK)
S.save(os.path.join(OUT, "NOVA_trup_vs_R05.png"), optimize=True)
print("sheet 1", S.size)
# ------------------------------------------------------------------ sheet 2: whole robot vs R01
H = 1500
a = fit(r01, h=H)
h_ = comp("hero_r01.png"); b = fit(h_, h=H)
fr, sd = fit(comp("front_full.png"), h=560), fit(comp("side_full.png"), h=560)
Wd = 40 + a.width + 40 + b.width + 40
S = Image.new("RGB", (Wd, 240 + H + 90 + 560 + 50), PAPER)
d = ImageDraw.Draw(S)
d.text((40, 30), "NOVA mini – telo podľa tvojho obrázka R01, s hotovou hlavou a krkom", font=font(54), fill=INK)
d.multiline_text((40, 110), "Vľavo tvoj obrázok, vpravo NOVA. Trup je podľa listu R05, ruky podľa R02, podstavec podľa R01. Hlava a krk sú naše hotové diely,\n"
                 "preto sa od obrázka líšia. Je to len vizualizácia na odsúhlasenie vzhľadu – nie diely na tlač.", font=font(29, "Regular"), fill=MUTED, spacing=10)
S.paste(a, (40, 240)); S.paste(b, (80 + a.width, 240))
d.text((40, 240 + H + 14), "R01 – tvoj obrázok", font=font(40), fill=INK)
d.text((80 + a.width, 240 + H + 14), "NOVA – nový model", font=font(40), fill=INK)
y2 = 240 + H + 90
S.paste(fr, (40, y2)); S.paste(sd, (60 + fr.width, y2))
tx = 100 + fr.width + sd.width
d.multiline_text((tx, y2 + 10),
                 "Rozmery (mm)\n"
                 "trup: šírka 105 (pri krku 57), hĺbka 80, výška 85 + čierny spodok 3,5\n"
                 "ruka: dĺžka 72, šírka 35, hrúbka 24; kĺb ramena Ø27\n"
                 "podstavec: 146 × 112 × 27 + čierna pätka 3,5\n"
                 "výška robota: ≈ 203 (krk zasunutý), ≈ 223 (krk vysunutý)",
                 font=font(30, "Regular"), fill=INK, spacing=12)
S.save(os.path.join(OUT, "NOVA_vs_R01.png"), optimize=True)
hero = comp("hero_r01.png"); hero.save(os.path.join(OUT, "NOVA_celok.png"))
print("sheet 2", S.size)

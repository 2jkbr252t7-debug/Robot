"""Slovak evidence image for K2: section y = const of the torso (voxel map) with the required servo case, the belt plane
and the shoulder pulley drawn in.  usage: obr_rozpocet.py  -> img/k2_rozpocet_x.png"""
import os, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
W = "/tmp/claude-0/gapwf/fin/R1/K2_dole_remen"
D = np.load("/tmp/claude-0/gapwf/fin/R1/trup_servo/map1.npz"); lo, H = D["lo"], float(D["h"])
static, moving, label, interior = D["static"], D["moving"], D["label"], D["interior"]
names = [str(s) for s in D["lab_names"]]
F = lambda s: ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", s)
FB = lambda s: ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", s)
os.makedirs(W + "/img", exist_ok=True)
Y0 = -2.25
rh, rv, sc = (8.0, 54.0), (-86.0, 1.0), 14
j = int((Y0 - lo[1]) / H)
S, M, L, I = static[:, j, :], moving[:, j, :], label[:, j, :], interior[:, j, :]
X = lo[0] + (np.arange(S.shape[0]) + 0.5) * H; Z = lo[2] + (np.arange(S.shape[1]) + 0.5) * H
i0, i1 = np.searchsorted(X, rh[0]), np.searchsorted(X, rh[1]); k0, k1 = np.searchsorted(Z, rv[0]), np.searchsorted(Z, rv[1])
col = {"servo_J1": (90, 130, 215), "pena_J1_celo": (90, 130, 215), "T_spodok": (95, 95, 110), "T_bok_L": (215, 210, 190),
       "T_stred": (215, 210, 190), "T_klb_L": (60, 60, 60), "T_paluba": (150, 120, 170), "T_most": (160, 160, 160),
       "zosilnovac": (200, 200, 200)}
img = np.full((i1 - i0, k1 - k0, 3), 255, np.uint8)
sub = (slice(i0, i1), slice(k0, k1))
img[I[sub]] = (246, 246, 246)
for lb in np.unique(L[sub][S[sub]]):
    m = S[sub] & (L[sub] == lb)
    img[m] = col.get(names[lb], (175, 175, 185))
img[M[sub]] = (245, 175, 90)
img = np.transpose(img, (1, 0, 2))[::-1]
im0 = Image.fromarray(img).resize((img.shape[1] * sc // 2, img.shape[0] * sc // 2), Image.NEAREST)
TOPH, PANEL = 70, 470
im = Image.new("RGB", (im0.size[0] + PANEL, im0.size[1] + TOPH), (255, 255, 255)); im.paste(im0, (0, TOPH))
pxmm = sc / 2 / H
def P(x, z): return ((x - rh[0]) * pxmm, (rv[1] - z) * pxmm + TOPH)
dr = ImageDraw.Draw(im, "RGBA")
for g in range(int(rh[0]), int(rh[1]) + 1):
    if g % 5 == 0:
        dr.line([P(g, rv[0]), P(g, rv[1])], fill=(150, 150, 220, 90)); dr.text((P(g, rv[1])[0] + 2, TOPH + 2), f"{g}", fill=(40, 40, 140), font=F(13))
for g in range(int(rv[0]), int(rv[1]) + 1):
    if g % 5 == 0:
        dr.line([P(rh[0], g), P(rh[1], g)], fill=(150, 150, 220, 90)); dr.text((2, P(rh[0], g)[1] + 1), f"{g}", fill=(40, 40, 140), font=F(13))
# required servo case (SCS0009, case 21.5) for a GT2 3 mm belt with a 12T shoulder pulley (best optimistic placement)
xf, Hc = 38.03, 21.5
case = [P(xf - Hc, -58.15), P(xf, -81.35)]
dr.rectangle(case, outline=(200, 0, 0, 255), width=4, fill=(230, 40, 40, 70))
dr.rectangle([P(xf - Hc, -58.15), P(18.5, -81.35)], fill=(200, 0, 0, 150))
# belt plane + pulleys
xb0, xb1 = 38.33, 42.93
dr.rectangle([P(xb0, -12.0), P(xb1, -81.0)], outline=(0, 120, 0, 255), width=2, fill=(40, 170, 60, 45))
dr.rectangle([P(xb0, -12.0), P(xb1, -22.0)], outline=(0, 90, 0, 255), width=3)
dr.line([P(30, -17), P(54, -17)], fill=(0, 0, 0, 160), width=1)
dr.ellipse([P(46.756 - 0.6, -17 + 0.6), P(46.756 + 0.6, -17 - 0.6)], fill=(0, 0, 0, 255))
# assumed (optimistic) J1 plug zone kept only above z -57.3
dr.rectangle([P(15.7, -48.3), P(27.0, -57.3)], outline=(20, 40, 120, 255), width=2)
dr.line([P(15.7, -66.3), P(27.0, -66.3)], fill=(20, 40, 120, 255), width=1)
dr.text((10, 8), "K2 – servo dole + remeň: prečo sa nezmestí", fill=(0, 0, 0), font=FB(22))
dr.text((10, 40), "rez y = −2,25 mm (najlepšie miesto pre servo vľavo), mierka v mm", fill=(0, 0, 0), font=F(16))
dr.text(P(19.0, -59.5), "potrebné telo SCS0009", fill=(150, 0, 0), font=FB(14))
dr.text(P(9.0, -83.3), "prekryv 2,0", fill=(150, 0, 0), font=FB(13))
dr.rectangle([P(43.2, -22.3), P(52.5, -24.0)], fill=(255, 255, 255, 230)); dr.text(P(43.4, -22.4), "remenica ramena", fill=(0, 110, 0), font=FB(12))
dr.text(P(44.0, -6.0), "dnešný kĺb", fill=(230, 230, 230), font=F(12))
dr.text(P(38.6, -62.0), "zosil.", fill=(60, 60, 60), font=F(11))
dr.text(P(43.4, -50.0), "rovina\nremeňa", fill=(0, 90, 0), font=F(13))
dr.text(P(9.3, -72.0), "servo J1", fill=(255, 255, 255), font=FB(15))
dr.text(P(12.0, -30.0), "otáčanie hlavy\n+ zdvih krku", fill=(150, 80, 0), font=F(14))
dr.text(P(46.5, -15.6), "os", fill=(0, 0, 0), font=F(13))
dr.text(P(16.0, -50.0), "konektory J1", fill=(20, 40, 120), font=F(12))
x0 = im0.size[0] + 14; y = TOPH + 10
lines = [("Remeň alebo lanko spája len rovnobežné hriadele.", 1),
         ("Remenica ramena aj remenica serva preto musia", 0),
         ("ležať v tej istej rovine kolmej na os X.", 0), ("", 0),
         ("Pri ramene: medzi otáčaním hlavy (x 34,4)", 0),
         ("a stenou bočného krytu (x 44,5) je 10,1 mm.", 0),
         ("Remenica Ø10 musí končiť najďalej na x 42,9.", 0),
         ("Rovina remeňa GT2 3 mm je teda x 38,3 … 42,9.", 0), ("", 0),
         ("Servo s hriadeľom v osi X musí mať čelo", 0),
         ("na x 38,0 a telo (21,5 mm) siaha až po x 16,5.", 0),
         ("Tam je servo J1 s dorazom (x 15,7 … 18,5).", 0), ("", 0),
         ("Výsledok (mapa 0,5 mm, vôle 0,3 / 1,0):", 1),
         ("vľavo najviac 19,5 mm pre telo serva aj keď", 0),
         ("zmenšíme zónu konektorov J1 a doraz J1;", 0),
         ("bez toho len 8,0 … 11,6 mm.", 0),
         ("SCS0009 potrebuje 21,5 … 25,25 mm.", 0),
         ("vpravo najviac 6,6 mm: servo J1 a jeho stena", 0),
         ("siahajú až po x −32,2.", 0), ("", 0),
         ("Priamy pohon (servo na osi ramena):", 1),
         ("10,1 mm voľnej dĺžky, SCS0009 má telo 21,5,", 0),
         ("trčalo by z trupu 9,1 mm.", 0), ("", 0),
         ("Záver: koncept K2 nie je realizovateľný.", 1)]
for t, b in lines:
    dr.text((x0, y), t, fill=(0, 0, 0) if not b else (120, 0, 0), font=FB(15) if b else F(15)); y += 22
# legend
y += 10
for c, t in (((230, 40, 40), "potrebné telo serva SCS0009"), ((40, 170, 60), "rovina remeňa a remenica ramena"),
             ((90, 130, 215), "servo J1 (otáčanie tela)"), ((245, 175, 90), "pohyb hlavy (±90°, zdvih 0–20)"),
             ((95, 95, 110), "rám T_spodok (stĺp sa môže zmeniť)"), ((215, 210, 190), "biele kryty trupu")):
    dr.rectangle([x0, y + 2, x0 + 18, y + 16], fill=c); dr.text((x0 + 26, y), t, fill=(0, 0, 0), font=F(14)); y += 22
out = W + "/img/k2_rozpocet_x.png"; im.save(out); print(out, im.size)

"""R4/klb: preview comparison sheet of the shoulder-joint variants (Slovak, with diacritics).
CAD venv: /opt/venv/cad/bin/python sheet_klb.py  -> prev500/nahlad_klb.png"""
import os, sys, json
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R3/img/work")
from PIL import Image, ImageDraw
import sheetlib as SL

HERE = os.path.dirname(os.path.abspath(__file__))
PV = os.path.join(HERE, "prev500")
SUM = json.load(open(os.path.join(HERE, "klb_summary.json")))
VIDS = ["K0", "K1", "K2", "K3", "K3v"]
HEAD = {"K0": ("K0 – dnes", "tenký krúžok D13"), "K1": ("K1 – golier", "D22 na ruke"), "K2": ("K2 – kryt v trupe", "pevný valec D26"),
        "K3": ("K3 – jeden valec", "kryt D26 + prstenec D26"), "K3v": ("K3v – ako K3", "ruka o 1,5 mm ďalej")}
ROWS = [("front", "Spredu, pravouhlo, ruka visí"), ("p34f", "Šikmo spredu, ruka visí"), ("p34fr", "Šikmo spredu, ruka hore o 90°"),
        ("p34b", "Šikmo zozadu, ruka visí"), ("p34br", "Šikmo zozadu, ruka hore o 90°")]


def f1(x):
    return f"{x:.1f}".replace(".", ",")


def f2(x):
    return f"{x:.2f}".replace(".", ",")


def facts(vid):
    s = SUM[vid]; L = s["look"]; g = s["gap_white_arm_torso"]
    out = [("viditeľný priemer", f"Ø {f1(s['visible_d'])}")]
    rw = {"K0": "trupom (zátka)", "K1": "rukou", "K2": "trupom (zátka)", "K3": "kryt trup, prstenec ruka", "K3v": "kryt trup, prstenec ruka"}[vid]
    out.append(("otáča sa s", rw))
    if vid == "K2":
        cv = s["cover_visible_mm"]
        out.append(("kryt vyčnieva", f"{f1(cv['hore'])} hore · {f1(cv['vpredu'])} vpredu"))
        out.append(("ruka – kryt", f"{f2(s['arm_to_cover_gap_pose_independent'])} (vždy)"))
    else:
        out.append(("čierna dĺžka", f"{f1(L['hore']['black_visible_mm'])} hore · {f1(L['vpredu']['black_visible_mm'])} vpredu · "
                                    f"{f1(L['dole']['black_visible_mm'])} dole"))
        if vid == "K0":
            out.append(("krúžok – otvor ruky", "0,50 (vnútri)"))
        elif vid == "K1":
            gp = s["rotating_part_gaps"]["ARM_golier_K1"]["PLG_zatka_K1"]["visible"]
            out.append(("golier – zátka", f"{f2(gp)}"))
        else:
            rid = "ARM_prstenec_" + vid
            gp = s["rotating_part_gaps"][rid]
            out.append(("prstenec – kryt / jamka", f"{f2(s['ring_to_cover_profile_gap'])} / {f2(gp['T_bok_L']['min'])}"))
    out.append(("biela medzera ruka–trup", f"{f1(g['rest'])} pokoj · {f1(g['at_135'])} pri 135°"))
    out.append(("šírka robota cez ruky", f"{f1(s['robot_width_over_arms'])}"))
    ch = {"K0": "nič", "K1": "zátka (vybranie), náboj ruky čierny s golierom, otvor v ruke D22",
          "K2": "len zátka (vyrastie z jamky)", "K3": "zátka ako K2, náboj ruky čierny s prstencom, otvor v ruke D26",
          "K3v": "ako K3 + zátka a skrutka o 1,5 dlhšie, ruka ďalej"}[vid]
    out.append(("mení sa", ch))
    return out


W = 1480
M = 30
gap = 10
cw = (W - 2 * M - 120 - gap * (len(VIDS) - 1)) // len(VIDS)     # 120 px left column for the row labels
LX = M + 120
ims = {}
for sh, _ in ROWS:
    for v in VIDS:
        im = Image.open(os.path.join(PV, f"{sh}_{v}.png")).convert("RGBA")
        bg = Image.new("RGBA", im.size, (236, 236, 233, 255)); bg.alpha_composite(im)
        r = cw / im.size[0]
        ims[(sh, v)] = bg.convert("RGB").resize((cw, int(im.size[1] * r)), Image.LANCZOS)
row_h = {sh: ims[(sh, VIDS[0])].size[1] for sh, _ in ROWS}
y = M
H = M + 120 + 50 + sum(row_h.values()) + gap * len(ROWS) + 420 + 90
S = Image.new("RGB", (W, H), SL.BG)
d = ImageDraw.Draw(S)
d.text((M, y), "NOVA mini · kĺb ramena: návrhy plnšieho kĺbu (ruka B)", font=SL.font(34), fill=SL.INK); y += 46
d.text((M, y), "Ľavé rameno, rovnaké kamery pre všetky varianty. Ruka ostáva pri trupe – zväčšujú sa len čierne diely kĺbu "
               "(inšpirácia R01 / R08).", font=SL.font(17, "Regular"), fill=SL.MUTED); y += 24
d.text((M, y), "Čierne diely sú rotačne súmerné okolo osi ramena, preto majú rovnakú vôľu v každej polohe ruky.",
       font=SL.font(17, "Regular"), fill=SL.MUTED); y += 40
for i, v in enumerate(VIDS):
    x = LX + i * (cw + gap)
    t, sub = HEAD[v]
    col = SL.INK if v == "K0" else SL.ACCENT
    d.text((x, y), t, font=SL.font(21), fill=col)
    d.text((x, y + 26), sub, font=SL.font(15, "Regular"), fill=SL.MUTED)
y += 54
for sh, lab in ROWS:
    words = lab.split(", ")
    yy = y + row_h[sh] // 2 - 10 * len(words)
    for w_ in words:
        d.text((M, yy), w_, font=SL.font(14, "SemiBold") if os.path.exists("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf") else SL.font(14),
               fill=SL.INK); yy += 20
    for i, v in enumerate(VIDS):
        x = LX + i * (cw + gap)
        S.paste(ims[(sh, v)], (x, y))
    y += row_h[sh] + gap
y += 8
ymax = y
for i, v in enumerate(VIDS):
    x = LX + i * (cw + gap)
    yy = y
    for k_, val in facts(v):
        d.text((x, yy), k_, font=SL.font(13, "Regular"), fill=SL.MUTED); yy += 17
        # wrap value
        words = val.split(" "); line = ""
        for w_ in words:
            t_ = (line + " " + w_).strip()
            if d.textlength(t_, font=SL.font(14)) > cw - 4:
                d.text((x, yy), line, font=SL.font(14), fill=SL.INK); yy += 18; line = w_
            else:
                line = t_
        d.text((x, yy), line, font=SL.font(14), fill=SL.INK); yy += 22
    ymax = max(ymax, yy)
y = ymax + 14
notes = ["Rozmery v mm. Biela medzera ruka–trup (bez čiernych dielov) je v K0–K3 rovnaká ako dnes: 3,7 v pokoji, 1,1 pri 135°, 0,97 pri skrytom "
         "dorazе +140,5°.".replace("dorazе", "doraze"),
         "Vôle čiernych dielov k trupu ≥ 0,88 (pravidlo ≥ 0,8); K2: ruka je od pevného krytu 1,29 v každej polohe. Náboj ruky (MR128 + podložka M12, "
         "rezerva M2b) ostáva, kĺb sa ešte prerobí na 6700ZZ.",
         "Náhľad 500 px / 16 vzoriek – koncept vzhľadu, nie výkres."]
for n in notes:
    d.text((M, y), n, font=SL.font(14, "Regular"), fill=SL.MUTED); y += 20
S = S.crop((0, 0, W, y + M))
out = os.path.join(PV, "nahlad_klb.png")
S.save(out)
print(out, S.size)

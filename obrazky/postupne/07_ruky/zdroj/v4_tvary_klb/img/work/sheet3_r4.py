"""R4 sheet 3: the recommended combination (arm B1 + joint K3) - large R01-like view, front view, joint close-ups next to
today's (B0 + K0, same cameras), reasons and open points.  Called from sheets_r4.py (run(H), H = the sheets_r4 module with the helpers)."""
import os
import numpy as np
from PIL import Image, ImageDraw

SHAPE, JOINT = "B1", "K3"


def run(H):
    sk, NS, NJ, CC = H.sk, H.NS, H.NJ, H.CC
    SW, M = H.SW, H.M
    S = Image.new("RGB", (SW, 3000), H.BG)
    d = ImageDraw.Draw(S)
    title = "NOVA mini · odporúčanie: ruka B1 + kĺb K3"
    intro = ("Najmodernejšie zaoblenie ruky z prvého listu (B1 – squircle) a najplnší kĺb z druhého listu (K3 – jeden čierny valec D26) spolu. "
             "Veľký obrázok je šikmo spredu ako zadanie R01, obe ruky visia, hlava otočená o 15°.")
    y0 = H.header(d, title, intro) + 4
    n, j, c = NS[SHAPE], NJ[JOINT], CC[SHAPE]
    c0 = CC["B0"]
    # ---------------------------------------------------------------- right column (sizes first)
    LW = 820
    xL = M
    xR = xL + LW + 14
    RW = SW - M - xR
    fc = H.cam("frontx")
    b4 = (fc.px((-80.0, 0, 0))[0], fc.px((0, 0, 89.5))[1], fc.px((80.0, 0, 0))[0], fc.px((0, 0, -117.5))[1])
    b4 = tuple(int(round(v)) for v in b4)
    w4 = RW - 150
    s4 = w4 / (b4[2] - b4[0])
    h4 = (b4[3] - b4[1]) * s4
    yr1 = y0
    hr1 = 64 + h4 + 14
    kc = H.cam("kp34")
    wk = (RW - 24 - 10) / 2
    hk = kc.H * wk / kc.W
    hpair = 44 + hk + 28
    yr2 = yr1 + hr1 + 14
    yr3 = yr2 + hpair + 14
    hL = yr3 + hpair - y0
    # ---------------------------------------------------------------- left: big R01-like view, fitted to the column height
    hero = H.load(f"r01_{SHAPE}_{JOINT}")
    bx = H.alpha_box([f"r01_{SHAPE}_{JOINT}"], thr=200, pad=60)
    s = min((LW - 24) / (bx[2] - bx[0]), (hL - 56) / (bx[3] - bx[1]))
    ph = H.Panel(hero, H.cam("r01"), bx, s, (0, 0))
    ph.at = (xL + (LW - ph.w) / 2, y0 + 50)
    ph.im = H.feather(ph.im, 40)
    H.card(d, xL, y0, xL + LW, y0 + hL)
    ph.paste(S)
    d.text((xL + 16, y0 + 12), "B1 – squircle  +  K3 – jeden valec D26", font=H.fH, fill=H.ACCENT)
    # front
    H.card(d, xR, yr1, xR + RW, yr1 + hr1)
    d.text((xR + 14, yr1 + 10), "spredu", font=H.fB, fill=H.INK)
    d.text((xR + 14, yr1 + 32), f"šírka cez ruky {sk(n['robot_width'])} mm, podstavec 146 mm", font=H.fSm, fill=H.MUTED)
    pf = H.Panel(H.load(f"frontx_{SHAPE}_{JOINT}"), fc, b4, s4, (xR + (RW - w4) / 2, yr1 + 60))
    pf.paste(S)
    # today vs new, same cameras
    for yy, nm, head in ((yr2, "kp34", "kĺb šikmo spredu, ruka visí"), (yr3, "kp34r", "kĺb šikmo spredu, ruka hore 90°")):
        H.card(d, xR, yy, xR + RW, yy + hpair)
        d.text((xR + 14, yy + 10), head, font=H.fB, fill=H.INK)
        cm = H.cam(nm)
        for i, (img, lab) in enumerate(((f"{nm}_B0_K0", "dnes: B0 + krúžok D13"), (f"{nm}_{SHAPE}_{JOINT}", "nové: B1 + K3"))):
            p = H.Panel(H.load(img), cm, (0, 0, cm.W, cm.H), wk / cm.W, (xR + 12 + i * (wk + 10), yy + 40))
            p.paste(S, bg=(255, 255, 255))
            d.text((p.at[0] + wk / 2, yy + 40 + hk + 6), lab, font=H.font(13, "SemiBold" if i else "Regular"),
                   fill=H.ACCENT if i else H.MUTED, anchor="ma", features=["-kern"])   # Inter kerns '1 +' to 'B1+'
    # ---------------------------------------------------------------- reasons / open points
    yb = y0 + hL + 16
    why = [f"B1 má najčistejšie moderné zaoblenie (squircle): plochší kryt, plynulá hrana, vrch ako oblúk okolo kĺbu. Je to jediný tvar, "
           f"pri ktorom netreba posúvať magnety ani zosilňovať šev – stena nad kĺbom {sk(n['wall'], 2)} (dnes 1,59), steny za magnetmi "
           f"{sk(n['post_cover'], 2)} / {sk(n['post_inner'], 2)}.",
           f"Medzera ruka–trup je {sk(n['gap_rest'], 2)} v pokoji a {sk(n['gap_min'], 2)} pri pohybe (dnes 1,12); robot je {sk(n['robot_width'])} mm "
           f"široký, o 0,8 mm užší ako dnes.",
           f"K3 robí z kĺbu jeden čierny valec D26 ako na R01 a R08: čierny pás spredu {sk(j['band'])} mm namiesto 12,8 mm. Vôle kĺbu: "
           f"prstenec – kryt 0,89, prstenec – jamka 0,90, biela medzera ruka–trup sa nemení.",
           f"Širšia ruka B1 pomáha aj kĺbu: biely lem okolo otvoru D26,4 je {sk(c['band_front'])} mm namiesto {sk(c0['band_front'])} mm pri B0 a biela "
           f"ruka je od pevného krytu {sk(c['white_arm_to_cover'], 2)} (pri B0 {sk(c0['white_arm_to_cover'], 2)})."]
    care = ["Kĺb K3 bol nezávisle overený na ruke B0; pre B1 som prepočítal len miesta, ktoré závisia od tvaru ruky (lem, ruka – kryt, "
            f"čierny náboj ostáva pod švom a {sk(c['part_to_cover_surface_min'])} mm od vonkajšieho krytu).",
            "Čierny náboj s prstencom sa lepí do ruky: potrebuje osový doraz (osadenie alebo 3 rebrá). Hranu otvoru D26,4 treba zraziť o 0,3–0,5.",
            "Zátka má zatiaľ vnútro z modelu v2 (len vizualizácia); prerobí sa spolu s kĺbom na ložisko 6700ZZ.",
            "Ak by sa ti viac páčila štíhlejšia špička, alternatíva je B2 + K3: medzera pri pohybe 1,57, ale os magnetov treba posunúť na 3,7 mm od okraja (stena krytu za magnetom má len 1,22)."]
    cw2 = (SW - 2 * M - 14) // 2
    fb = H.font(16, "Regular")

    def bullets(x, y, w, head, items, col):
        yy = y + 12
        d.text((x + 16, yy), head, font=H.fB, fill=col)
        yy += 30
        for it in items:
            lines = H.wrap(d, it, fb, w - 52)
            d.ellipse((x + 18, yy + 8, x + 25, yy + 15), fill=col)
            d.multiline_text((x + 34, yy), "\n".join(lines), font=fb, fill=H.INK, spacing=5)
            yy += len(lines) * 21 + 10
        return yy

    # measure first (draw on a scratch image) to size the cards equally
    tmp = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    def height(w, items):
        return 12 + 30 + sum(len(H.wrap(tmp, it, fb, w - 52)) * 21 + 10 for it in items) + 6
    hb = max(height(cw2, why), height(cw2, care))
    H.card(d, M, yb, M + cw2, yb + hb)
    H.card(d, M + cw2 + 14, yb, SW - M, yb + hb)
    bullets(M, yb, cw2, "Prečo práve táto kombinácia", why, H.GREEN)
    bullets(M + cw2 + 14, yb, cw2, "Na čo si dať pozor", care, H.ORANGE)
    yf = yb + hb + 18
    foot = ("Rozmery v mm. Čísla tvaru B1 a kĺbu K3 sú z nezávislých kontrol; čísla kombinácie (lem, ruka – kryt, náboj) sú môj prepočet "
            "z tých istých modelov. Koncept vzhľadu, nie výkres – mechanika kĺbu sa ešte prerobí okolo ložísk, ktoré sú na sklade.")
    ye = H.footer(d, yf, foot) + 22
    H.finish(S, ye, "v4_odporucanie.png")

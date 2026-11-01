"""Compose the head A / A+ / B comparison sheet from renders in /tmp/claude-0/v8cmp3/<variant>/ (hero, front, right)."""
import sys
sys.path.insert(0, '/home/user/Robot')
from nova.render import sheet as S  # noqa: E402
from nova.render.make_sheets import load, alpha_bbox, paste_fit, radial_fade, new_sheet  # noqa: E402

W, H = 3600, 2350
sh, d = new_sheet(W, H, "NOVA mini (v8) – VARIANTY HLAVY",
                  "rovnaké telo: kolesá, otočný trup, výška ~191 mm · ESP32-S3 + 3.5\" 480×320 · krycie sklo = dymový akryl (mŕtvy predok)")
cols = [("head_a", "A · PLOCHÉ SKLO", "čierny rám, ploché sklo 92×60 · najlacnejšie · ~2–4 €", "laserom vyrezaný dymový akryl 2 mm"),
        ("head_aplus", "A+ · JEMNE ZAKRIVENÉ", "rám ostáva, sklo R180 · nie je ploché · ~3–6 €", "prírez 92.5×60 R16, ohyb v rúre na MDF forme R178"),
        ("head_b", "B · VIZOR BEZ RÁMU", "zapustený vizor R100, najmodernejšie · ~3–8 €", "prírez 99×60, ohyb na PVC rúre Ø200 / MDF R100")]
cw = (W - 120) // 3
for i, (v, lab, desc, mfg) in enumerate(cols):
    x0 = 60 + i * cw
    rd = f"/tmp/claude-0/v8cmp3/{v}"
    d.text((x0 + 10, 200), lab, fill=S.INK, font=S.font(44, "Bold"))
    d.text((x0 + 10, 258), desc, fill=S.MUTED, font=S.font(24, "Medium"))
    d.text((x0 + 10, 292), mfg, fill=S.ACCENT, font=S.font(23, "SemiBold"))
    hero = load(rd, "hero", fade=None)
    bx = alpha_bbox(hero, 220)
    pw, ph = int(0.18 * (bx[2] - bx[0])), int(0.06 * (bx[3] - bx[1]))
    hero = hero.crop((max(0, bx[0] - pw), max(0, bx[1] - ph), min(hero.width, bx[2] + pw), min(hero.height, bx[3] + ph)))
    paste_fit(sh, radial_fade(hero, inner=0.74), (x0, 340, x0 + cw - 20, 1560))
    for k, vv in enumerate(["front", "right"]):
        im = load(rd, vv, fade=None)
        b2 = alpha_bbox(im, 60)
        im = im.crop((max(0, b2[0] - 15), max(0, b2[1] - 15), min(im.width, b2[2] + 15), min(im.height, b2[3] + 15)))
        bxx = (x0 + 20 + k * (cw // 2), 1620, x0 + (k + 1) * (cw // 2) - 20, 2230)
        paste_fit(sh, im, bxx)
        d.text(((bxx[0] + bxx[2]) / 2, 1605), "SPREDU" if vv == "front" else "BOK (−X)", fill=S.MUTED, font=S.font(22, "SemiBold"), anchor="mb")
    if i:
        d.line([(x0 - 10, 200), (x0 - 10, 2240)], fill=S.LINE, width=3)
d.text((W - 60, H - 36), "NOVA mini v8 · render z CAD modelu · varianty hlavy na porovnanie", fill=S.MUTED, font=S.font(22, "Medium"), anchor="rs")
out = "/home/user/Robot/obrazky/v8_koncept/v8_varianty_hlavy.png"
sh.save(out, optimize=True)
print(out)

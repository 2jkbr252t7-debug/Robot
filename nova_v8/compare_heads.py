"""Compose the head A vs head B concept sheet from renders in /tmp/claude-0/v8cmp/<head_a|head_b>/ (hero, front, right)."""
import sys
sys.path.insert(0, '/home/user/Robot')
from nova.render import sheet as S  # noqa: E402
from nova.render.make_sheets import load, alpha_bbox, paste_fit, radial_fade, new_sheet  # noqa: E402

W, H = 3000, 2350
sh, d = new_sheet(W, H, "NOVA mini (v8) – NÁČRT HLÁV",
                  "rovnaké telo s kolesami a otočným trupom · výška ~190 mm · ESP32-S3 + 3.5\" displej 480×320 · koncept")
cols = [("head_a", "A · AKO NA FOTKE", "zaoblený „televízorček“, čierny rám vystupuje 5 mm, ploché sklo, uši s LED krúžkom"),
        ("head_b", "B · KAPSULA S VIZOROM", "oblejšia hlava, čierne sklo sa zaobľuje do bokov, zapustené LED krúžky, bez rámu")]
for i, (v, lab, desc) in enumerate(cols):
    x0 = 60 + i * 1470
    rd = f"/tmp/claude-0/v8cmp/{v}"
    d.text((x0, 200), lab, fill=S.INK, font=S.font(46, "Bold"))
    d.text((x0, 262), desc, fill=S.MUTED, font=S.font(26, "Medium"))
    hero = load(rd, "hero", fade=None)
    bx = alpha_bbox(hero, 220)
    pw, ph = int(0.25 * (bx[2] - bx[0])), int(0.08 * (bx[3] - bx[1]))
    hero = hero.crop((max(0, bx[0] - pw), max(0, bx[1] - ph), min(hero.width, bx[2] + pw), min(hero.height, bx[3] + ph)))
    paste_fit(sh, radial_fade(hero, inner=0.72), (x0, 320, x0 + 900, 2240))
    for k, vv in enumerate(["front", "right"]):
        im = load(rd, vv, fade=None)
        b2 = alpha_bbox(im, 60)
        im = im.crop((max(0, b2[0] - 20), max(0, b2[1] - 20), min(im.width, b2[2] + 20), min(im.height, b2[3] + 20)))
        y0 = 340 + k * 950
        paste_fit(sh, im, (x0 + 930, y0, x0 + 1400, y0 + 900))
        d.text((x0 + 1165, y0 - 10), "SPREDU" if vv == "front" else "BOK (−X)", fill=S.MUTED, font=S.font(24, "SemiBold"), anchor="mb")
d.line([(1500, 200), (1500, 2240)], fill=S.LINE, width=3)
d.text((W - 60, H - 36), "NOVA mini v8 · koncept z CAD modelu (build123d → Blender Cycles) · nie je finálny návrh",
       fill=S.MUTED, font=S.font(22, "Medium"), anchor="rs")
out = "/home/user/Robot/obrazky/v8_koncept/v8_porovnanie_hlav.png"
sh.save(out, optimize=True)
print(out)

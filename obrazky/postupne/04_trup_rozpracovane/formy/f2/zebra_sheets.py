"""compose the zebra renders (tmp/zb/*.png from zebra.py) into labelled sheets zebra_torso/base/arm.png (Slovak)"""
import os
from PIL import Image, ImageDraw, ImageFont

D = os.path.dirname(os.path.abspath(__file__))
F = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
SHEETS = {
    "torso": ("Trup – zebra (odrazové pruhy, hustota ZF 28)", [
        ("torso_front_zozadu34", "spredu 3/4"), ("torso_front_zozadu", "spredu"),
        ("torso_zboku", "z boku (jamka ramena)"), ("torso_top_zozadu34", "zhora 3/4 (plocha vo vnútri goliera)")]),
    "base": ("Podstavec – zebra (odrazové pruhy, hustota ZF 28)", [
        ("base_front_zozadu34", "spredu 3/4"), ("base_zboku", "z boku"),
        ("base_top_zozadu", "zhora (miska, plochá podlaha r 37)"), ("base_top_zozadu34", "zhora 3/4")]),
    "arm": ("Krídlo (ľavé) – zebra (odrazové pruhy, hustota ZF 28)", [
        ("arm_out_zboku", "vonkajšia strana"), ("arm_out_zozadu34", "vonkajšia strana 3/4"),
        ("arm_in_zboku", "vnútorná strana (k trupu)"), ("arm_in_zozadu34", "vnútorná strana 3/4")]),
}
for key, (title, items) in SHEETS.items():
    W, H = 700, 560
    c = Image.new("RGB", (2 * W, 2 * H + 60), (245, 245, 243))
    d = ImageDraw.Draw(c)
    d.text((20, 14), title, fill=(20, 20, 20), font=ImageFont.truetype(FB, 28))
    for k, (fn, lab) in enumerate(items):
        im = Image.open(f"{D}/tmp/zb/{fn}.png").convert("RGB").resize((W, H))
        x, y = (k % 2) * W, 60 + (k // 2) * H
        c.paste(im, (x, y))
        d.rectangle([x + 8, y + 8, x + 16 + 13 * len(lab), y + 40], fill=(255, 255, 255))
        d.text((x + 12, y + 10), lab, fill=(20, 20, 20), font=ImageFont.truetype(F, 21))
    c.save(f"{D}/zebra_{key}.png")
    print("zebra sheet", key)

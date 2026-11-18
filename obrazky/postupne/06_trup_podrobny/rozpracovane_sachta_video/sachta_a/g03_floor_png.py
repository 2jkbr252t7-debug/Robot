"""quick-look image of the bottom thickness map (first solid interval that starts at the floor level) - for my own inspection"""
import numpy as np
from PIL import Image, ImageDraw
d = np.load("g02_maps.npz")
ft, top, bot, lowest = d["floor_t"], d["floor_top"], d["floor_bot"], d["lowest"]
xs, ys = d["xs"], d["ys"]
nx, ny = ft.shape
img = np.full((ny, nx, 3), 255, np.uint8)
# classes: lowest interval start z
cl = np.full(ft.shape, -1)
low = lowest
def col(v):
    return v
rgb = np.zeros((nx, ny, 3), np.uint8) + 255
m = ~np.isnan(low)
rgb[m & (low < -45)] = (120, 120, 255)            # drum shroud
rgb[m & (low >= -45) & (low < -42)] = (180, 180, 255) # lip
fl = m & (np.abs(low + 41.9) < 0.05) & (top <= -40.0)
rgb[fl] = (0, 160, 0)
thin = fl & (ft < 1.2)
rgb[thin] = (255, 160, 0)
vthin = m & (ft < 0.8)
rgb[vthin] = (255, 0, 0)
w41 = m & (np.abs(low + 41.9) < 0.05) & (top > -40.0)
rgb[w41] = (60, 60, 60)                            # wall going down to -41.9
w40 = m & (np.abs(low + 40.9) < 0.05)
rgb[w40] = (150, 150, 150)                         # wall edge -40.9
other = m & ~(fl | w41 | w40 | (low < -42)) 
rgb[other] = (200, 0, 200)
im = Image.fromarray(np.transpose(rgb, (1, 0, 2))[::-1])   # y up
im = im.resize((nx, ny))
im.save("g03_floor_map.png")
print("pixels", nx, ny, "other z:", sorted(set(np.round(low[other], 2).tolist()))[:20])

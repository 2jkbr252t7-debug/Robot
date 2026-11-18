import json, math, numpy as np, sa_lib as L
from g08_fillets import measure, S
res = []
res.append(measure("back window top corner (x -6.5, z -10.9) at y 12", S, 1, 12.0, (-10.9, -6.5), (-1, -1)))
res.append(measure("back window top corner (x -20.9, z -10.9) at y 11.5", S, 1, 11.5, (-10.9, -20.9), (-1, 1)))
res.append(measure("end window top corner (y -7, z -15) at x 24.3", S, 0, 24.3, (-7.0, -15.0), (1, -1)))
res.append(measure("end window top corner (y 3.4, z -15) at x 24.0", S, 0, 24.0, (3.4, -15.0), (-1, -1)))
res.append(measure("back window side (x -6.5) / back floor top (z -40.65) at y 12", S, 1, 12.0, (-40.65, -6.5), (1, -1)))
for r in res: print(r)
json.dump(res, open("g08b_windows.json", "w"), indent=1)

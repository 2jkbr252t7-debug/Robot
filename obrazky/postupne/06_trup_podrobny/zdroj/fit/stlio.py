import numpy as np
def load_stl(fn):
    with open(fn, 'rb') as f:
        f.seek(80); n = np.frombuffer(f.read(4), '<u4')[0]
        d = np.frombuffer(f.read(), dtype=np.dtype([('n','<f4',3),('v','<f4',(3,3)),('a','<u2')]), count=n)
    return d['v'].astype(float)   # (n,3,3)

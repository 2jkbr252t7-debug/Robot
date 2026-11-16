import numpy as np, struct
def load_stl(p):
    with open(p,'rb') as f:
        h=f.read(80); n=struct.unpack('<I',f.read(4))[0]
        d=np.frombuffer(f.read(n*50),dtype=np.dtype([('n','<f4',3),('v','<f4',(3,3)),('a','<u2')]))
    return d['v'].astype(float)   # (n,3,3)

def slice_z(T, z):
    """segments (m,2,2) of the mesh cut by the plane z"""
    d = T[:,:,2]-z
    segs=[]
    s = np.sign(d); s[s==0]=1
    m = ~((s[:,0]==s[:,1])&(s[:,1]==s[:,2]))
    for tri,dd in zip(T[m],d[m]):
        pts=[]
        for i in range(3):
            a,b=tri[i],tri[(i+1)%3]; da,db=dd[i],dd[(i+1)%3]
            if (da>=0)!=(db>=0):
                t=da/(da-db); pts.append(a[:2]+t*(b[:2]-a[:2]))
        if len(pts)==2: segs.append(pts)
    return np.array(segs)

def fill(segs, xs, ys):
    """even-odd fill: occ[j,i] True if (xs[i], ys[j]) inside"""
    occ=np.zeros((len(ys),len(xs)),bool)
    a=segs[:,0]; b=segs[:,1]
    for j,y in enumerate(ys):
        m=((a[:,1]>y)!=(b[:,1]>y))
        if not m.any(): continue
        xa=a[m,0]+(y-a[m,1])/(b[m,1]-a[m,1])*(b[m,0]-a[m,0])
        xa=np.sort(xa)
        cnt=np.searchsorted(xa, xs)
        occ[j]=(cnt%2)==1
    return occ

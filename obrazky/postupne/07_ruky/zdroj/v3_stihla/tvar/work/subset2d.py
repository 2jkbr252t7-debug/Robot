import numpy as np
n=2.3
def check(ki,kw,ni):
    C=-(1-ki); Ti=ki
    We0=(1-abs(C)**n)**(1/n)
    We=kw*We0
    th=np.linspace(np.pi/2,3*np.pi/2,20001)
    c,s=np.abs(np.cos(th)),np.abs(np.sin(th))
    r=((c/Ti)**ni+(s/We)**ni)**(-1/ni)
    X=C+r*np.cos(th); Y=r*np.sin(th)
    f=np.abs(X)**n+np.abs(Y)**n
    return f.max(), We
for ki in (1.0,0.85,0.78,0.7,0.62,0.55):
    for ni in (2.3,2.2,2.1,2.0):
        # find max kw with subset
        lo,hi=0.5,1.0
        for _ in range(40):
            m=(lo+hi)/2
            if check(ki,m,ni)[0]<=1+1e-9: lo=m
            else: hi=m
        print(f"ki {ki} ni {ni}: max kw {lo:.4f}  We/orig_max {lo*check(ki,lo,ni)[1]/lo:.4f}  -> width factor vs orig max {lo*(1-(1-ki)**n)**(1/n):.4f}")

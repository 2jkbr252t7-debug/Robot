import sys, numpy as np
sys.dont_write_bytecode=True
sys.path.insert(0,"/tmp/claude-0/gapwf/fin/R1/img_v1/work")
import v1geo as V
S=V.S
us=np.linspace(0,1,51)
hw,ht=S.arm_profile(us)
for u,w,t in zip(us,hw,ht):
    if abs(u*50-round(u*50))<1e-9 and int(round(u*50))%2==0: print(f"u {u:.2f} z {-72*u:6.1f} width {2*w:5.2f} thick {2*t:5.2f}")
uu=np.linspace(0,1,20001); w,t=S.arm_profile(uu)
print("max thick",2*t.max(),"at u",uu[t.argmax()],"max width",2*w.max(),"at",uu[w.argmax()])
print("thick at 0.22", 2*S.arm_profile(0.22)[1])
rows,top,bot=V.pebble_rows(400,480)
P=rows.reshape(-1,3)
W=V.to_world(P,dx=-1.0)
i=W[:,0].argmin(); j=W[:,0].max()
print("innermost world", W[i].round(3), "local", P[i].round(3), "u", -P[i,2]/72)
k=W[:,0].argmax(); print("outermost world", W[k].round(3), "local", P[k].round(3), "u", -P[k,2]/72)
print("width over arms", 2*W[:,0].max())
print("A_LOC", V.A_LOC, "att", V.att(-1.0))
# skins on the shoulder axis
for inset in (0,):
    print("axis skins dx-1", V.skins(3.0,-17.0,0.0,-1.0))

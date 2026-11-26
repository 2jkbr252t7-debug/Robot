# rough helical compression spring numbers for commonly sold springs (G=79 GPa steel; A2 ~ 70 GPa)
import math
def spring(name,d,OD,L0,n_tot,G=79000.0):
    D=OD-d; n=n_tot-2 if n_tot else None
    if n is None:
        # estimate total coils from pitch ~ D/3 (typical assortment springs) - ROUGH
        n_tot=round(L0/(D/3.0)); n=n_tot-2
    k=G*d**4/(8*D**3*n)
    Ls=n_tot*d
    C=D/d; Kw=(4*C-1)/(4*C-4)+0.615/C
    # allowable ~ 0.45*Rm, Rm(music wire, d~1) ~ 2000 MPa -> ~900 MPa corrected; A2 spring wire Rm~1800 -> ~800
    tau_allow=800.0
    Fmax_stress=tau_allow*math.pi*d**3/(8*D*Kw)
    Fsolid=k*(L0-Ls)
    print(f"{name:28s} d{d} OD{OD} L0{L0} ntot{n_tot} : k={k:5.2f} N/mm  Ls={Ls:4.1f}  F@solid={Fsolid:5.1f} N  F@800MPa={Fmax_stress:5.1f} N  usable~{min(Fsolid,Fmax_stress)*0.8:5.1f} N")
spring("Exvalos CSN 1x9x24x8.5",1.0,9,24,8.5)
spring("Exvalos CSN 1x9x30x10.5",1.0,9,30,10.5)
spring("Hornbach A2 6.6x33x0.7 (n est)",0.7,6.6,33,None,G=70000)
spring("Hornbach A2 9.2x66x0.8 (n est)",0.8,9.2,66,None,G=70000)
spring("Hornbach zinc 11x67x1 (n est)",1.0,11,67,None)
print()
# clutch preload needed: T = mu * F * r_m * faces
for mu in (0.12,0.2,0.3):
    for rm in (3.6,5.0,6.5):
        for faces in (2,):
            F=0.06/(mu*rm/1000*faces)
            print(f"T=0.06 N.m mu={mu} r_m={rm} faces={faces}: F={F:5.1f} N")
print()
# screw shank as axle: ISO 4762 ds M3 2.86..3.00, bearing bore 3 (0/-0.008) -> radial gap
for name,ds_min,ds_max,bore in (("M3 shank in MR63/683 bore 3",2.86,3.00,3.0),("M4 shank in MR74 bore 4",3.82,4.00,4.0)):
    print(f"{name}: diametral gap {bore-ds_max:.3f}..{bore-ds_min:.3f} mm (Loctite 638 max gap 0.25 mm diametral ~ OK if fill; 641 max 0.1?)")
# thread major diameter M3 6g: 2.874..2.980 ; M4 6g 3.838..3.978

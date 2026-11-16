import sys, time; sys.path.insert(0,'/tmp/claude-0/gapwf/fin/T4')
import t4_pan as M, t4_common as C
def rep(n, s, t):
    bb=s.bounding_box()
    print(f"{n:16s} valid {s.is_valid} solids {len(s.solids())} vol {s.volume:9.2f} bbox x {bb.min.X:.2f}..{bb.max.X:.2f} y {bb.min.Y:.2f}..{bb.max.Y:.2f} z {bb.min.Z:.2f}..{bb.max.Z:.2f} ({time.time()-t:.1f} s)", flush=True)
names = sys.argv[1:] or ['mk_koleso','mk_servo','mk_drziak','mk_kluka','mk_pata','mk_jazyk','mk_ucho','mk_spoj','mk_kabel','mk_sachta','mk_fpc']
for n in names:
    t=time.time()
    try:
        s=getattr(M,n)(); rep(n,s,t)
    except Exception as e:
        import traceback; traceback.print_exc(); print(n,'FAILED',e)

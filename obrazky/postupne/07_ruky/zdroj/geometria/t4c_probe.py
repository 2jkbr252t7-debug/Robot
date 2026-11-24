# read constants from T4 t4_common without executing heavy code: just grep the literals
import re
src = open("/tmp/claude-0/gapwf/fin/T4/t4_common.py").read()
for k in ("TOP", "XS", "SEAM", "Z_BOT", "Z_BASE_TOP", "SH_Y, SH_Z", "R_SOCKET", "KLB_PROFILE", "WALL"):
    m = re.search(r"^%s\s*=.*$" % re.escape(k), src, re.M)
    print("T4 t4_common:", m.group(0)[:150] if m else (k, None))

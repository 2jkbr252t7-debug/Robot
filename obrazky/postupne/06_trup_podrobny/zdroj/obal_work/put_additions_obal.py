"""append / replace the 'additions by obal' block of t4_common.py (only the text between the two markers is touched)"""
import fcntl, os
P = "/tmp/claude-0/gapwf/fin/T4/t4_common.py"
blk = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "additions_obal.txt")).read().rstrip("\n") + "\n"
A, B = "# >>> additions by obal", "# <<< end of additions by obal"
with open(P, "r+") as f:
    fcntl.flock(f, fcntl.LOCK_EX)
    s = f.read()
    if A in s and B in s:
        i = s.rfind("\n", 0, s.rfind("\n", 0, s.index(A))) + 1
        j = s.index(B) + len(B)
        j = s.index("\n", j) + 1 if "\n" in s[j:] else len(s)
        new = s[:i] + blk + s[j:]; mode = "replaced"
    else:
        new = s.rstrip("\n") + "\n\n\n" + blk; mode = "appended"
    f.seek(0); f.write(new); f.truncate()
    fcntl.flock(f, fcntl.LOCK_UN)
print(mode, len(s), "->", len(new))

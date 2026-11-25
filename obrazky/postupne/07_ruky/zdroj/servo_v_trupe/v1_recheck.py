"""re-check of the v1 outward arm shift (servo IN the arm, R1/navrh/dd2.py method) for the SCS0009 cases only"""
import sys, io, contextlib
sys.dont_write_bytecode = True
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R1/navrh"); sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R1/geo")
src = open("/tmp/claude-0/gapwf/fin/R1/navrh/dd2.py").read()
src = src.replace('cases = {"KST X06 20x7x16.6 s5": (20.0, 7.0, 16.6, 5.0), "KST X08 23.5x8x16.8 s5.5": (23.5, 8.0, 16.8, 5.5),\n         "ES9052MD 19.9x8.8x23.1 s4.7": (19.9, 8.8, 23.1, 4.7), ', 'cases = {')
src = src.replace(', "MG90S 22.8x12.2x22.7 s5.9": (22.8, 12.2, 22.7, 5.9)}', '}')
exec(compile(src, "dd2_subset", "exec"))

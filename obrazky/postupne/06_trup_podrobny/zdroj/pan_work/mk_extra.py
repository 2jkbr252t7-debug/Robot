"""parts_pan_extra.json: deviations / intended fits / assembly of the PAN module (merged into parts_pan.json by t4_pan.py)"""
import json
D = [
 dict(id="P1", item="L_jazyk (new part)", spec="7.3: tab x 22.3..27.0 as part of L_pata", actual="separate tongue, keyed (2 prongs) + 1 x M1.6x10 countersunk along -X, mounted after the neck is in the well",
      reason="a tab that is part of the foot cannot be lowered through the well (inner half length 23.5, end window only below z -15)"),
 dict(id="P2", item="guide lands in the well", spec="7.1: 4 PTFE strips on flat long faces, neck gap 0.87", actual="8 lands 0.70 high (2 front, 1 back + 1 short above the ear window, 4 on the end walls) as strip seats; neck gap 0.30 bare / 0.17 with 0.13 tape",
      reason="the neck must be guided: 0.87 per side would let the head rock by 2.8 deg; lands keep the tape off the window edges"),
 dict(id="P3", item="ear slot", spec="7.3 / EAR: slot 2.2 x 12.2, y 12.1..24.3", actual="2.2 x 12.7, y 11.6..24.3 (front end +0.5)",
      reason="at mid stroke the pin was 0.10 from the slot end, less than the 0.17..0.30 float of the neck in the well -> binding. Back end unchanged (sweep limit r 32.03): firmware keeps theta 3..177 deg"),
 dict(id="P4", item="ear dowel", spec="dowel D2 at x -15.5, zrel -4.3", actual="D1.5 x 5 at zrel -4.75", reason="the flange is only 3.1 high under the crank sweep (notch); D2 would leave 0.55 webs, D1.5 centred leaves 0.78"),
 dict(id="P5", item="ear flange y", spec="flange y 10.2..12.4", actual="9.8..12.4", reason="the foot back face is at y 9.8 (foot 19.6 deep); 10.2 would leave a 0.4 gap under the screw"),
 dict(id="P6", item="bracket pads / F10", spec="BRACKET_PADS (19.5, -30.0), (8.0, -14.5), face y 15.6, F10 = M2x6", actual="lower pad z -31.7, pad face y 15.4, insert hole 3.2 deep, F10 = 2 x M2x4 ISO 4762 (2.3 mm in the insert)",
      reason="the lug of the bracket and the F10_1 tool channel must pass under the frame magnet pad of T_stred at (25, -24) (the tilted pad and its riser reach x 18, z -29.14 seen along Y); 1.7 of PETG under the screw heads; 1.2 floor behind the insert hole"),
 dict(id="P7", item="bracket outline", spec="BRACKET x -5.3..17.6, z -41.9..-13.0; ledge y 17.1..26.2", actual="lug to x 22.9 (z -36.55..-29.7) around the lower pad, tab to z -12.3 around the upper screw, wedge lip y 29.45..30.95 behind the servo end, rest block y 12.6..13.0",
      reason="pad r 3.0 + slot +-1.0 needs the lug; the lip holds the far end of the servo (one tab only). All inside PAN_ENV (margin 1.48)"),
 dict(id="P8", item="pan gear sectors", spec="7.2: teeth 154.3..354.3 (200 deg), lip r 16.5", actual="21 teeth centred 154.3..354.3 (root sector 149.3..359.3), drum r 15.7 over 4..145, lip over 22..140",
      reason="whole teeth; at the hard stops +-90 the drum / lip stay 1.0 / 5.5 deg outside the pinion zone. The lip r 16.5 (spec 7.2) is outside the r 15.9 band of PAN_ENV (spec table) - back sector only, 2.3 from the FPC clamp"),
 dict(id="P9", item="rotating FPC anchor", spec="7.2 / 9: anchor on the drum at gear azimuth 30", actual="the FPC comes down onto the drum at gear azimuth 14 (riser), free inner run from 23.4",
      reason="shortest run from the lift loop at the +X end wall. U-turn at 92 + 0.402 x pan (57.8..126.2), inside the 56..128 of RAM; free length 47.3 (RAM 45.6)"),
 dict(id="P10", item="FPC lift loop", spec="9 / FPC_LIFT: legs y +-3.5, R 3.5, x 25.3..28.4, z -40.5..-15.5", actual="moving leg y -3.5 on the tongue, fixed leg y +4.5 on a fin of the well, R 4.0, envelope x 25.2..28.2, y -3.62..4.56, z -41.9..-13.4 (PAN['LIFT_LOOP_ENV'])",
      reason="fixed leg needs a backing (fin) and a path under the floor (apron, groove 0.2); U top at lift 20 = z -13.4, r max 28.57 <= 28.7"),
 dict(id="P11", item="tool hole in the stage top", spec="-", actual="D4.8 through the top plate at stage (0, 21.1)", reason="driver access to the clamp screw of T_prichytka_fpc (RAM, B frame (18.0, 11.0), axis Z) at pan -58.5 before the lift module / collar disc are mounted"),
 dict(id="P12", item="micro junction", spec="9: 2 x 3 pins on the bracket", actual="1 x 3 pin header 1.27 on an FR4 stiffener bonded to the FPC branch on the well back wall (x 16.6..22, z -41..-36.65), socket on the shortened servo lead",
      reason="the branch is part of the FPC outline; the bracket stays removable without unsoldering"),
 dict(id="P13", item="STL export", spec="t4_common.export_part", actual="t4_obal.export_abs (absolute deflection 0.01)", reason="instruction of the lead / OBAL finding"),
]
FITS = [
 "journal D56.14 (+ PTFE band 0.13 -> D56.40) in the bore of T_stred (measured r 28.342): radial 0.14 with tape / 0.27 bare",
 "stage top r 26.5 / collar disc (glued on z -2.0) in the collar ring r 26.75: running seam 0.25 (variant B)",
 "gear + hub bore D6.05 on the pivot pin D6 h6: 0.025 radial; gear underside on the PTFE washer (contact), 0.3 above the deck",
 "pan gear 36T / pinion 18T m0.8, C 21.600: flank gap 0.035..0.038 at every pose (93 poses, pinion rotated -2 x pan)",
 "stop pin D2 pressed in D1.98, runs in the deck groove 2.4 wide (0.2 per side), hard stops +-90",
 "P_koleso bonded to the hub disc of P_sachta + 2 dowels D2 x 4 (blind in the gear, floor 0.5)",
 "neck 45 x 20 between the lands: 0.30 bare / 0.17 with tape; foot 44.6 x 19.6: 0.37 to the tape; neck in the collar-disc slot 0.25 (B)",
 "foot top bonded to the FRONT neck half (z -36.5); foot 0.5 above the hub disc at rest (0.7 above the pin top)",
 "crank on the 21T spline (serration 4.44 / 4.84 on D4.8, overlap 3.5 mm3), M2.5x6 countersunk into the shaft; pin D2 pressed in D1.98",
 "crank pin D2 in the ear slot 2.2: 0.10 per side; crank arm <-> ear side gap 0.40 (set with the +-1.0 slots of the bracket)",
 "MG90S in the bracket: plate (y), ledge (z), tab face (x) in contact; wedge lip 0.20 behind the case, post 0.30 above the top end; F11 M2x6 thread-forming through the tab",
 "bracket on the 2 pads of the well (pockets r 3.25 over the pads r 3.0), 2 x M2x4 into glued M2 inserts",
 "ear flange on the foot back face: dowel D1.5 pressed in D1.48 (foot) / D1.55 (ear), M2x8 thread-forming in a D1.7 pilot",
 "tongue on the foot end face: 2 key prongs 1.5 x 1.4 x 1.0 in a slot +0.05, M1.6x10 self-tapping in a D1.3 pilot",
 "FPC: paddle bonded in the foot pocket, corner piece in the tongue recess, fixed leg bonded on the fin, run bonded in the 0.2 groove under the floor, "
 "inner run on the drum r 15.7 under the lip, outer run on the channel wall of T_paluba, static end in the clamp of T_prichytka_fpc, tail through the arc slot",
 "PTFE: 8 strips on the lands, band 5 x 177 on the journal (contact = bonded)",
]
ASM = [
 ("A1", "bench", "glue the 2 M2 inserts into the pads of P_sachta; press the stop pin into P_koleso (from below, 1.0 proud); bond P_koleso to the hub disc with epoxy + 2 dowels D2 x 4; PTFE strips on the 8 lands, band on the journal"),
 ("A2", "bench", "bond L_pata to the FRONT neck half (wires through the slot); optionally 2 x M2 countersunk from below into drilled pilots (front half only)"),
 ("A3", "bench", "solder the 7 neck wires to the FPC paddle; bond the paddle into the foot pocket"),
 ("B1", "bench", "MG90S into P_drziak_serva (+X), F11; lower tab of the servo cut off; press the D2 pin into P_kluka; crank onto the spline at servo zero (pin down), M2.5x6"),
 ("C1", "torso step 12", "stage (A1) straight -Z through the collar bore at pan 0: gear meshes axially with the pinion, stop pin drops into the groove"),
 ("C1b", "torso", "pan FPC into the channel: static end under the clamp, clamp screw from above through the D4.8 hole of the stage top at pan -58.5; tail through the arc slot to the controller"),
 ("C2", "torso step 13", "lift module (B1) -Y through the door onto the 2 pads, 2 x M2x4 (F10); plug the servo lead into the micro junction"),
 ("C3", "torso step 15", "neck (A2 / A3) -Z into the well, FPC loose to the +X end window; then collar disc glued on the stage top"),
 ("A5", "torso", "L_jazyk -X through the end window onto the foot, M1.6x10 (pan +90 turns it to the door); FPC corner piece into the tongue recess, fixed leg onto the fin"),
 ("C4", "torso step 16", "L_ucho: hook onto the crank pin from -X (crank at BDC, pan 0), slide -Y onto the dowel, F12 M2x8 through the door; set the 0.4 side gap with the bracket slots; cycle 0..20"),
]
json.dump(dict(deviations=D, intended_fits=FITS, assembly=[dict(step=a, where=b, text=c) for a, b, c in ASM],
               foot_to_neck=dict(joint="epoxy on the bottom face z -36.5 of the FRONT neck half only (the halves must still separate)",
                                 optional_screws=dict(size="2 x M2x8 countersunk, from below, heads flush at z -40.5", xy=[[-10.0, -5.0], [7.5, -5.0]],
                                                      into="krk_predna_polovica, D1.6 pilots 4 mm deep to be drilled through the foot holes (change of a finished part, spec open point 4)",
                                                      checked="B mesh sections z -36.3 .. -34: solid material at both positions; the neck's cross screws sit at x -15 and x +5, z -31 "
                                                              "(hole z -32 .. -30): the foot screws end at z -32.5 and are 0.7 / 3.2 mm beside them in plan"),
                                 wire_exits="neck wire channels at x 11.75 .. 14.5, y -6.5 .. -3.5 and y -2 .. +2 (B mesh) inside the foot slot x 11.6 .. 15.0, y -7.2 .. 2.6"),
               firmware=dict(lift_theta_deg=[3, 177], lift_law="lift = 10 (1 - cos theta)", pan_deg=[-85, 85], pan_hard_stop_deg=[-90, 90]),
               poses="pan_work/poses/lift10, lift20 (all parts at pan 0), pan_work/poses/fpc/fpc_zdvih_{0,10,20}.stl, fpc_pan_{-85,0,85}.stl; "
                     "functions t4_pan.pose_parts(lift), fpc_lift(lift), fpc_loop(pan), mk_kluka(theta)"),
          open("/tmp/claude-0/gapwf/fin/T4/pan_work/parts_pan_extra.json", "w"), indent=1, ensure_ascii=False)
print("extra written", len(D), len(FITS), len(ASM))

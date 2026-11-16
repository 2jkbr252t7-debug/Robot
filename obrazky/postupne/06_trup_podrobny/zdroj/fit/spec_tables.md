**OBAL (t4_obal.py) – shell-mounted volumes**

| zone | grp | shape | x | y | z | note |
|---|---|---|---|---|---|---|
| reproduktor | T | cyl ‖Y, r 14.00 | axis x 0.00 | -36.60 … -31.60 | axis z -51.00 | behind the grille |
| led_box | T | box | -17.50 … 17.50 | -36.60 … -30.10 | -36.0 … -29.0 | light guide flange + LED PCB + holder |
| rura_goliera | T | cyl ‖Z, r 30.60 (bore r 28.35) | axis x 0.00 | axis y 0.000 | -10.50 … 1.75 | collar tube = ring seat + journal bearing |
| klb_L | T | cyl ‖X, r 13.50 | 40.60 … 50.96 | axis y 3.00 | axis z -17.00 |  |
| klb_L_krk | T | cyl ‖X, r 11.00 | 38.40 … 40.60 | axis y 3.00 | axis z -17.00 |  |
| klb_L_cap | T | cyl ‖X, r 11.00 | 50.96 … 58.76 | axis y 3.00 | axis z -17.00 |  |
| klb_P | T | cyl ‖X, r 13.50 | -50.96 … -40.60 | axis y 3.00 | axis z -17.00 |  |
| klb_P_krk | T | cyl ‖X, r 11.00 | -40.60 … -38.40 | axis y 3.00 | axis z -17.00 |  |
| klb_P_cap | T | cyl ‖X, r 11.00 | -58.76 … -50.96 | axis y 3.00 | axis z -17.00 |  |

**RAM (t4_ram.py) – static tower, wings, parts under the cap, dummy**

| zone | grp | shape | x | y | z | note |
|---|---|---|---|---|---|---|
| servo_J1 | T | box | -29.50 … 15.70 | -12.35 … 12.35 | -83.30 … -48.30 | STS3215, shaft down at J1_AX |
| servo_J1_boss | T | cyl ‖Z, r 6.00 | axis x -18.00 | axis y 0.000 | -85.90 … -83.30 |  |
| servo_J1_plug | T | box | 15.70 … 27.0 | -8.0 … 8.0 | -66.30 … -48.30 | 2 x 5264 plugs + cable bend |
| ram_koliska | T | box | -31.60 … 23.0 | -14.15 … 14.15 | -82.30 … -47.80 | cradle walls 1.6 around the servo |
| paluba | T | box | -31.60 … 31.60 | -14.30 … 15.30 | -47.80 … -46.0 | deck plate on the cradle walls |
| paluba_zad | T | cyl ‖Z, r 25.10 | axis x 0.00 | axis y 0.000 | -47.80 … -46.0 | deck under the FPC channel (y > 0 half) |
| cap_pan | T | cyl ‖Z, r 3.00 | axis x 0.00 | axis y 0.000 | -47.70 … -41.20 |  |
| ptfe | T | cyl ‖Z, r 12.00 (bore r 6.20) | axis x 0.00 | axis y 0.000 | -46.0 … -45.70 |  |
| kanal_fpc_pan | T | cyl ‖Z, r 25.10 (bore r 23.50) | axis x 0.00 | axis y 0.000 | -46.0 … -42.90 | static wall of the pan rolling loop (y > 0 half) |
| fpc_pan | T | cyl ‖Z, r 23.50 (bore r 15.70) | axis x 0.00 | axis y 0.000 | -45.90 … -42.90 | pan rolling loop (y > 0 half) |
| servo_pan | T | box | -11.75 … 11.75 | -27.04 … -14.54 | -74.20 … -51.20 | STS3032, shaft up at PAN_AX |
| servo_pan_tabs | T | box | -16.25 … 16.25 | -27.04 … -14.54 | -58.0 … -55.50 |  |
| servo_pan_boss | T | cyl ‖Z, r 6.20 | axis x -5.85 | axis y -20.793 | -51.20 … -47.70 |  |
| servo_pan_plug | T | box | 11.75 … 18.75 | -24.80 … -16.80 | -72.70 … -64.70 |  |
| pastorok_pan | T | cyl ‖Z, r 8.00 | axis x -5.85 | axis y -20.793 | -45.50 … -42.30 | mounted from above AFTER T_stred |
| pastorok_pan_naboj | T | cyl ‖Z, r 4.00 | axis x -5.85 | axis y -20.793 | -47.70 … -45.50 |  |
| DPS_riadenie | T | box | -24.0 … 24.0 | 15.50 … 22.50 | -77.0 … -55.0 | carrier + ESP32-S3-Zero, service through the door |
| stlp_L | T | box | 34.40 … 42.0 | -9.0 … 15.0 | -78.0 … -30.0 | left column (U channel) |
| stlp_P | T | box | -42.0 … -34.40 | -9.0 … 15.0 | -78.0 … -30.0 |  |
| stlp_L_naboj | T | cyl ‖X, r 11.60 | 34.40 … 38.40 | axis y 3.00 | axis z -17.00 | shoulder boss |
| stlp_P_naboj | T | cyl ‖X, r 11.60 | -38.40 … -34.40 | axis y 3.00 | axis z -17.00 |  |
| stlp_L_doraz | T | cyl ‖X, r 12.80 (bore r 11.60) | 38.40 … 39.10 | axis y 3.00 | axis z -17.00 | stop ring |
| stlp_P_doraz | T | cyl ‖X, r 12.80 (bore r 11.60) | -39.10 … -38.40 | axis y 3.00 | axis z -17.00 |  |
| stlp_L_pata | T | box | 34.40 … 37.60 | -5.0 … 11.0 | -82.30 … -78.0 |  |
| stlp_P_pata | T | box | -37.60 … -34.40 | -5.0 … 11.0 | -82.30 … -78.0 |  |
| menic | T | box | -45.40 … -36.60 | -5.90 … 11.90 | -70.0 … -52.20 | D36V28F5 on the right column |
| zosilnovac | T | box | 36.60 … 39.60 | -5.90 … 11.90 | -71.50 … -52.20 | MAX98357A on the left column |
| kondenzator | T | cyl ‖Z, r 5.00 | axis x 41.00 | axis y 3.000 | -51.50 … -38.50 |  |
| pastorok_J1 | T | cyl ‖Z, r 10.00 | axis x -18.00 | axis y 0.000 | -90.0 … -86.80 |  |
| lozisko_6805 | T | cyl ‖Z, r 18.50 (bore r 12.50) | axis x 0.00 | axis y 0.000 | -98.0 … -91.0 |  |
| pata_J1 | T | cyl ‖Z, r 24.00 (bore r 17.00) | axis x 0.00 | axis y 0.000 | -91.0 … -84.50 | plinth / gear housing (notched) |
| pata_J1_dole | T | cyl ‖Z, r 21.00 (bore r 18.50) | axis x 0.00 | axis y 0.000 | -98.0 … -91.0 |  |
| sukna | T | cyl ‖Z, r 28.50 (bore r 24.00) | axis x 0.00 | axis y 0.000 | -86.20 … -85.20 |  |
| Z_koleso_J1 | Z | cyl ‖Z, r 10.00 | axis x 0.00 | axis y 0.000 | -90.0 … -86.80 |  |
| Z_naboj | Z | cyl ‖Z, r 12.50 | axis x 0.00 | axis y 0.000 | -100.0 … -91.0 |  |

**PAN (t4_pan.py) – pan stage (P, pan frame) and lift parts (L, rest pose)**

| zone | grp | shape | x | y | z | note |
|---|---|---|---|---|---|---|
| sachta | P | box | -25.10 … 25.10 | -12.60 … 12.60 | -41.30 … -3.0 | well 47 x 22, walls 1.6 (lower edge -41.3; corners trimmed to r 26.5 above z -3.0) |
| sachta_naboj | P | cyl ‖Z, r 12.60 | axis x 0.00 | axis y 0.000 | -42.20 … -41.0 | hub disc joining well and gear |
| sachta_dno_zad | P | box | -8.0 … 25.10 | 2.0 … 12.60 | -41.90 … -41.30 | well floor, back sector only |
| cap_otocny | P | cyl ‖Z, r 28.20 (bore r 24.00) | axis x 0.00 | axis y 0.000 | -10.50 … -4.50 | journal D56.4 |
| vrch_stola | P | cyl ‖Z, r 26.50 | axis x 0.00 | axis y 0.000 | -4.50 … -2.0 |  |
| golier_kotuc | P | cyl ‖Z, r 26.50 | axis x 0.00 | axis y 0.000 | -2.0 … 4.0 | finished part (B) |
| koleso_pan | P | cyl ‖Z, r 15.70 (bore r 3.00) | axis x 0.00 | axis y 0.000 | -45.70 … -42.20 |  |
| servo_zdvih | P | box | -6.50 … 16.0 | 17.10 … 29.30 | -41.10 … -18.30 | MG90S, shaft along -X |
| servo_zdvih_veza | P | cyl ‖X, r 5.90 | -12.50 … -6.50 | axis y 23.20 | axis z -24.20 |  |
| servo_zdvih_lalok | P | cyl ‖X, r 2.90 | -12.50 … -6.50 | axis y 23.20 | axis z -29.80 |  |
| servo_zdvih_ucho | P | box | -2.50 … 0.0 | 17.10 … 29.30 | -18.30 … -13.45 |  |
| servo_zdvih_kabel | P | box | 11.40 … 15.90 | 20.70 … 25.70 | -18.30 … -13.30 |  |
| kluka_naboj | P | cyl ‖X, r 3.60 | -17.0 … -12.80 | axis y 23.20 | axis z -24.20 |  |
| kluka_obalka | P | cyl ‖X, r 12.20 | -17.0 … -14.50 | axis y 23.20 | axis z -24.20 | crank sweep; only the FRONT half disc (y <= Y_LIFT + 2.2) is used |
| drziak_serva | P | box | -5.30 … 17.60 | 12.60 … 17.10 | -41.90 … -13.0 | bracket between the well back wall and the servo |
| drziak_serva_dno | P | box | -6.50 … 16.0 | 17.10 … 26.20 | -41.90 … -41.10 | ledge under the servo end |
| fpc_zdvih | P | box | 25.30 … 28.40 | -4.0 … 4.0 | -40.50 … -15.50 | flexible loop (may be folded during insertion) |
| pata | L | box | -22.30 … 22.30 | -9.80 … 9.80 | -40.50 … -36.50 | foot under the neck |
| pata_jazyk | L | box | 22.30 … 27.0 | -3.50 … 3.50 | -40.50 … -38.0 |  |
| ucho | L | box | -19.90 … -17.40 | 12.40 … 23.60 | -40.50 … -31.90 |  |
| ucho_koniec | L | box | -19.90 … -17.40 | 23.60 … 25.10 | -40.50 … -33.40 |  |
| ucho_priruba | L | box | -13.50 … -7.50 | 10.20 … 12.40 | -40.50 … -36.50 |  |
| ucho_priruba_nizka | L | box | -19.90 … -13.50 | 10.20 … 12.40 | -40.50 … -37.40 |  |
| krk | L | box | -22.50 … 22.50 | -10.0 … 10.0 | -36.50 … 6.50 | finished neck (B), envelope |

**PAN_ENV – swept radius limit of everything on the pan stage (r about the Z axis, pan frame)**

| z from | z to | r max | shell inner half depth b_i at both ends | margin |
|---|---|---|---|---|
| -45.7 | -41.9 | 15.9 | 37.74 / 37.59 | 21.69 |
| -41.9 | -22.0 | 34.0 | 37.59 / 35.60 | 1.60 |
| -22.0 | -18.0 | 33.5 | 35.60 / 34.86 | 1.36 |
| -18.0 | -11.5 | 32.2 | 34.86 / 33.36 | 1.16 |
| -11.5 | -10.5 | 28.3 | 33.36 / 33.09 | 4.79 |
| -10.5 | -4.5 | 28.2 | 33.09 / 31.21 | 3.01 |
| -4.5 | -3.0 | 28.2 | 31.21 / 30.64 | 2.44 |
| -3.0 | 4.0 | 26.5 | 30.64 / 28.34 | 1.84 |

**Derived numbers (true offsets)**

| quantity | value |
|---|---|
| X_SH (outer surface on the shoulder axis) | 46.756 |
| X_KLB_END (arm interface plane) | 58.756 |
| front surface at x 0, light bar z -32.5: outer y / inner y | -39.17 / -36.96 |
| front surface at x 0, grille z -48: outer y / inner y | -39.99 / -37.79 |
| front surface at x 0, speaker centre z -51: outer y / inner y | -40.01 / -37.81 |
| back surface at x 0, z -12.0: outer y / inner y | 35.76 / 33.49 |
| back surface at x 0, z -24.0: outer y / inner y | 38.15 / 35.93 |
| back surface at x 0, z -42.0: outer y / inner y | 39.80 / 37.60 |
| back surface at x 0, z -60.0: outer y / inner y | 39.60 / 37.40 |
| back surface at x 0, z -72.0: outer y / inner y | 37.45 / 35.14 |
| inner half width a_i / half depth b_i at z -10.5 | 43.21 / 33.09 |
| inner half width a_i / half depth b_i at z -4.5 | 40.58 / 31.21 |
| inner half width a_i / half depth b_i at z -2.0 | 37.85 / 30.21 |
| inner half width a_i / half depth b_i at z 1.75 | 29.42 / 28.34 |
| white lip inner half depth at x 0 (z -81) | 27.30 |
| white lip inner half depth at x 10 (z -81) | 27.06 |
| white lip inner half depth at x 16.75 (z -81) | 26.34 |
| white lip inner half depth at x 20 (z -81) | 25.76 |
| white lip inner half depth at x 25 (z -81) | 24.36 |
| white lip inner half depth at x 30 (z -81) | 22.19 |
| white lip inner half depth at x 33.05 (z -81) | 20.25 |
| lip inner half depth at x 16.25, z -81.0 (pan-servo tab corner needs 27.55) | 26.41 |
| lip inner half depth at x 16.25, z -80.5 (pan-servo tab corner needs 27.55) | 27.15 |
| lip inner half depth at x 16.25, z -80.0 (pan-servo tab corner needs 27.55) | 27.82 |
| lip inner half depth at x 16.25, z -79.0 (pan-servo tab corner needs 27.55) | 29.16 |
| lip inner half depth at x 16.25, z -78.0 (pan-servo tab corner needs 27.55) | 30.56 |
| door hook tab at x 12.0, z -12: outer y 35.04 -> inner corner radius (inset 3.6) | 33.44 |
| door hook tab at x 20.0, z -12: outer y 33.36 -> inner corner radius (inset 3.6) | 35.29 |
| door magnet pad at x 25.0, z -24.0: outer y 34.40 -> pad inner radius (inset 7.2) | 35.32 |
| door magnet pad at x 25.0, z -60.0: outer y 36.70 -> pad inner radius (inset 7.2) | 37.21 |

# Sky130 analog SAR blocks via PDK gencells (S/H, R-2R, comparator).
# magic -rcfile $MAGICRC -dnull -noconsole layout/magic/sar_adc_analog_gencell.tcl
drc off
gds rescale false

proc gencell_at {dev inst x y args} {
    select top cell
    box ${x}um ${y}um ${x}um ${y}um
    magic::gencell sky130::${dev} $inst {*}$args
    select top cell
}

proc boxum {x0 y0 x1 y1} {
    if {$x1 < $x0} { set t $x0; set x0 $x1; set x1 $t }
    if {$y1 < $y0} { set t $y0; set y0 $y1; set y1 $t }
    box ${x0}um ${y0}um ${x1}um ${y1}um
}

proc m1 {x0 y0 x1 y1} {
    select top cell
    boxum $x0 $y0 $x1 $y1
    paint m1
}

proc m2 {x0 y0 x1 y1} {
    select top cell
    boxum $x0 $y0 $x1 $y1
    paint m2
}

proc m3 {x0 y0 x1 y1} {
    select top cell
    boxum $x0 $y0 $x1 $y1
    paint m3
}

proc m4 {x0 y0 x1 y1} {
    select top cell
    boxum $x0 $y0 $x1 $y1
    paint m4
}

proc pin1 {name x0 y0 x1 y1} {
    select top cell
    boxum $x0 $y0 $x1 $y1
    paint m1
    label $name FreeSans 0.3um -m1
    port make
}

proc via12 {cx cy} {
    global VIAF CURRENT_CELL
    select top cell
    # pad 0.36 → via1 0.15 gets 0.105 enclosure
    set s 0.18
    set v 0.075
    boxum [expr {$cx - $s}] [expr {$cy - $s}] [expr {$cx + $s}] [expr {$cy + $s}]
    paint m1
    paint m2
    boxum [expr {$cx - $v}] [expr {$cy - $v}] [expr {$cx + $v}] [expr {$cy + $v}]
    paint via1
    if {[info exists VIAF]} { puts $VIAF "$CURRENT_CELL via1 $cx $cy" }
}

# li (tap ring) -> m1 -> m2. Used for pFET nwell taps that have no pcell m1.
proc via_nwell {cx cy} {
    global VIAF CURRENT_CELL
    select top cell
    set s 0.18
    set v 0.085
    boxum [expr {$cx - $s}] [expr {$cy - $s}] [expr {$cx + $s}] [expr {$cy + $s}]
    paint m1
    paint m2
    boxum [expr {$cx - $v}] [expr {$cy - $v}] [expr {$cx + $v}] [expr {$cy + $v}]
    paint mcon
    paint via1
    if {[info exists VIAF]} {
        puts $VIAF "$CURRENT_CELL mcon $cx $cy"
        puts $VIAF "$CURRENT_CELL via1 $cx $cy"
    }
}

proc via23 {cx cy} {
    global VIAF CURRENT_CELL
    select top cell
    # pad 0.40 → via2 0.20 gets 0.10 enclosure
    set s 0.20
    set v 0.10
    boxum [expr {$cx - $s}] [expr {$cy - $s}] [expr {$cx + $s}] [expr {$cy + $s}]
    paint m2
    paint m3
    boxum [expr {$cx - $v}] [expr {$cy - $v}] [expr {$cx + $v}] [expr {$cy + $v}]
    paint via2
    if {[info exists VIAF]} { puts $VIAF "$CURRENT_CELL via2 $cx $cy" }
}

proc via34 {cx cy} {
    global VIAF CURRENT_CELL
    select top cell
    # pad 0.50 → via3 0.20 gets 0.15 enclosure
    set s 0.25
    set v 0.10
    boxum [expr {$cx - $s}] [expr {$cy - $s}] [expr {$cx + $s}] [expr {$cy + $s}]
    paint m3
    paint m4
    boxum [expr {$cx - $v}] [expr {$cy - $v}] [expr {$cx + $v}] [expr {$cy + $v}]
    paint via3
    if {[info exists VIAF]} { puts $VIAF "$CURRENT_CELL via3 $cx $cy" }
}

# Gate contact north of diffusion so the via pad does not short S/D.
# m1 exists only above the diffusion, not through the channel.
# Returns the via Y. half_w is W/2 of the FET.
proc gate_tap {ox oy half_w} {
    set y0 [expr {$oy + $half_w + 0.25}]
    set cy [expr {$oy + $half_w + 0.70}]
    mv1 $ox $y0 $cy 0.28
    via12 $ox $cy
    return $cy
}

# Via above the pcell gate contact; m1 strap so the m2 pad clears S/D.
proc gate_via {ox oy half_w} {
    set y_contact [expr {$oy + $half_w + 0.28}]
    set gy [expr {$oy + $half_w + 0.55}]
    mv1 $ox $y_contact $gy 0.28
    via12 $ox $gy
    return $gy
}

# Gate contact then m3 so S/D can stay on m2 at ox±0.395.
proc gate_via3 {ox oy half_w} {
    set gy [gate_via $ox $oy $half_w]
    via23 $ox $gy
    return $gy
}

proc mv3 {x y0 y1 {w 0.35}} {
    m3 [expr {$x - $w / 2.0}] $y0 [expr {$x + $w / 2.0}] $y1
}

proc mh3 {y x0 x1 {w 0.35}} {
    m3 $x0 [expr {$y - $w / 2.0}] $x1 [expr {$y + $w / 2.0}]
}

proc mv1 {x y0 y1 {w 0.35}} {
    m1 [expr {$x - $w / 2.0}] $y0 [expr {$x + $w / 2.0}] $y1
}

proc mh1 {y x0 x1 {w 0.35}} {
    m1 $x0 [expr {$y - $w / 2.0}] $x1 [expr {$y + $w / 2.0}]
}

proc mv2 {x y0 y1 {w 0.35}} {
    m2 [expr {$x - $w / 2.0}] $y0 [expr {$x + $w / 2.0}] $y1
}

proc mh2 {y x0 x1 {w 0.35}} {
    m2 $x0 [expr {$y - $w / 2.0}] $x1 [expr {$y + $w / 2.0}]
}

file mkdir layout/magic layout/gds
set VIAF [open layout/magic/via_points.txt w]

# ---------------------------------------------------------------------------
# Sample/hold: CMOS TG + MIM, 3.3 V g5v0
#   Xn: vin -- nMOS(sample_en) -- vhold
#   Xp: vin -- pMOS(sen) -- vhold
#   inverter: sen = ~sample_en
#   Xch: vhold to avss
# ---------------------------------------------------------------------------
cellname create sample_hold
load sample_hold
set CURRENT_CELL sample_hold
gencell_at sky130_fd_pr__nfet_g5v0d10v5 xn 8 10 w 8.0 l 0.5
gencell_at sky130_fd_pr__pfet_g5v0d10v5 xp 22 10 w 16.0 l 0.5
gencell_at sky130_fd_pr__nfet_g5v0d10v5 xinvn 8 28 w 1.0 l 0.5
gencell_at sky130_fd_pr__pfet_g5v0d10v5 xinvp 16 28 w 2.0 l 0.5
gencell_at sky130_fd_pr__cap_mim_m3_1 xch 38 8 w 20.0 l 20.0

# measured gencell origins
set xn_ox 9.065;  set xn_oy 14.965
set xp_ox 23.065; set xp_oy 19.01
set in_ox 9.065;  set in_oy 29.465
set ip_ox 17.065; set ip_oy 30.01
set cap_ox 48.93; set cap_oy 18.2

m1 0 0 70 1.2
m1 0 42 70 43.2
pin1 vin_ecg 0.5 8 4 12
pin1 vhold 62 8 68 12
pin1 sample_en 0.5 26 4 30
pin1 avdd 58 40 68 43
pin1 avss 0.5 0 8 2

# vin_ecg -> nFET left; pFET source on the pcell m1 stripe at x~22.67
via12 2.25 10.0
via12 [expr {$xn_ox - 0.395}] $xn_oy
via12 22.67 16.0
via12 22.67 19.01
mh2 11.0 2.25 [expr {$xn_ox - 0.395}] 0.35
mv2 2.25 10.0 11.0 0.35
mv2 [expr {$xn_ox - 0.395}] 11.0 $xn_oy 0.35
mh2 2.2 2.25 18.0 0.35
mv2 2.25 2.2 10.0 0.35
# hop vhold m2 at y=3.5 on m3 — keep via pads clear of the vhold mh2 spine
mv2 18.0 2.2 2.55 0.35
via23 18.0 2.55
via23 18.0 4.45
mv3 18.0 2.55 4.45 0.35
mv2 18.0 4.45 16.0 0.35
mh2 5.5 18.0 20.0 0.35
mv2 20.0 5.5 19.01 0.35
mh2 16.0 20.0 22.85 0.35
mh2 19.01 20.0 22.85 0.35
mv2 22.67 16.0 19.01 0.35

# vhold south of nFET, drop east of the vin alley, then east under vin
via12 [expr {$xn_ox + 0.395}] $xn_oy
via12 [expr {$xp_ox + 0.395}] [expr {$xp_oy + 0.55}]
via12 66.0 10.0
mh2 3.5 [expr {$xn_ox + 0.395}] 21.0 0.35
mv2 [expr {$xn_ox + 0.395}] 3.5 $xn_oy 0.35
mv2 21.0 1.65 3.5 0.35
mh2 1.65 21.0 66.0 0.35
mv2 66.0 1.65 10.0 0.35
mh2 [expr {$xp_oy + 0.55}] [expr {$xp_ox + 0.395}] 24.8 0.35
mv2 [expr {$xp_ox + 0.395}] $xp_oy [expr {$xp_oy + 0.55}] 0.35
mv2 24.8 [expr {$xp_oy + 0.55}] 31.2 0.35
mh2 31.2 24.8 66.0 0.35
mv2 66.0 10.0 31.2 0.35
# MIM top is met4 inside the device; do not drop via3 on the cap (that shorts the plates).
# Top-plate m4 ends ~58.0; an east m4 strip ~59.4 has pcell via3 to the m3 bottom.
m4 56.4 17.9 57.8 18.5
m4 56.4 18.5 57.8 29.4
m4 56.4 29.0 66.5 29.4
m4 65.7 18.0 66.5 29.4
via34 66.0 18.2
via23 66.0 10.0
via12 66.0 10.0
mv3 66.0 10.0 18.2 0.4
# MIM bottom met3 -> avss at the west edge (no via3)
set cap_bot 38.4
via23 $cap_bot 1.1
via12 $cap_bot 1.1
mv3 $cap_bot 1.1 9.0 0.4

# sample_en on m3 so gate verticals do not weld S/D on m2
via12 2.25 28.0
via23 2.25 28.0
set xng [gate_via3 $xn_ox $xn_oy 4.0]
set ing [gate_via3 $in_ox $in_oy 0.5]
set ipg [gate_via3 $ip_ox $ip_oy 1.0]
set gsx 6.6
mh3 33.0 2.25 $ip_ox 0.40
mv3 2.25 28.0 33.0 0.40
mv3 $gsx $xng 33.0 0.40
mh3 $xng $gsx $xn_ox 0.40
set in_gsx [expr {$in_ox - 1.2}]
mv3 $in_gsx $ing 33.0 0.40
mh3 $ing $in_gsx $in_ox 0.40
set ip_gsx [expr {$ip_ox - 1.2}]
mv3 $ip_gsx $ipg 33.0 0.40
mh3 $ipg $ip_gsx $ip_ox 0.40
# Fillets at inverter-gate L-bends (jog corners, not FET vias)
m3 [expr {$in_gsx - 0.15}] [expr {$ing - 0.15}] [expr {$in_gsx + 0.15}] [expr {$ing + 0.15}]
m3 [expr {$ip_gsx - 0.15}] [expr {$ipg - 0.15}] [expr {$ip_gsx + 0.15}] [expr {$ipg + 0.15}]

# sen (inverter drains) jog on m2 then m3 spine east of the inverter
set senx 19.5
via12 [expr {$in_ox + 0.395}] $in_oy
via12 [expr {$ip_ox + 0.395}] $ip_oy
mh2 $in_oy [expr {$in_ox + 0.395}] $senx 0.35
mh2 $ip_oy [expr {$ip_ox + 0.395}] $senx 0.35
via23 $senx $in_oy
via23 $senx $ip_oy
mv2 $senx $in_oy $ip_oy 0.40
mv3 $senx $in_oy $ip_oy 0.40
set xpg [gate_via3 $xp_ox $xp_oy 8.0]
mv3 $senx $in_oy 35.0 0.40
mh3 35.0 $senx $xp_ox 0.40
mv3 $xp_ox $xpg 35.0 0.40
# Euclidean met3.1 fillets at L-bend inner corners (same net).
foreach {cx cy} {
    2.25 33.0
    19.5 35.0
    23.065 35.0
    6.6 19.515
} {
    m3 [expr {$cx - 0.15}] [expr {$cy - 0.15}] [expr {$cx + 0.15}] [expr {$cy + 0.15}]
}

# inverter nFET source -> avss on m3 at x=5 (west of sample_en m3 and vin m2)
set asx 5.0
via12 [expr {$in_ox - 0.395}] $in_oy
mh2 $in_oy [expr {$in_ox - 0.395}] $asx 0.35
via23 $asx $in_oy
via12 $asx 1.1
via23 $asx 1.1
mv3 $asx 1.1 $in_oy 0.35
via_nwell [expr {$in_ox - 1.065}] $in_oy
mh2 $in_oy [expr {$in_ox - 1.065}] [expr {$in_ox - 0.395}] 0.35
# inverter pFET source -> avdd
set ypick [expr {$ip_oy + 1.0 - 0.15}]
mh1 $ypick [expr {$ip_ox - 0.395}] [expr {$ip_ox - 1.5}] 0.35
mv1 [expr {$ip_ox - 1.5}] $ypick 42.5 0.35
via_nwell [expr {$ip_ox - 1.065}] $ip_oy
mh1 $ip_oy [expr {$ip_ox - 1.065}] [expr {$ip_ox - 0.395}] 0.35
# TG pFET nwell shares the inverter well (keep west edge clear of nFET)
select top cell
boxum 17.5 $xp_oy 24.5 $ip_oy
paint nwell
boxum 22.5 $xp_oy 24.5 $ip_oy
paint nwell

save sample_hold
file copy -force sample_hold.mag layout/magic/sample_hold.mag
gds write layout/gds/sample_hold_magic.gds

# ---------------------------------------------------------------------------
# Clocked comparator (g5v0 StrongARM-ish)
#   tail + input pair + pMOS latch + clk precharge + clkb reset + RS buffer
# ---------------------------------------------------------------------------
cellname create comparator
load comparator
set CURRENT_CELL comparator
gencell_at sky130_fd_pr__nfet_g5v0d10v5 xtail 28 6 w 8.0 l 0.5
gencell_at sky130_fd_pr__nfet_g5v0d10v5 x1 12 18 w 4.0 l 0.5
gencell_at sky130_fd_pr__nfet_g5v0d10v5 x2 36 18 w 4.0 l 0.5
gencell_at sky130_fd_pr__pfet_g5v0d10v5 x3 12 32 w 4.0 l 0.5
gencell_at sky130_fd_pr__pfet_g5v0d10v5 x4 36 32 w 4.0 l 0.5
gencell_at sky130_fd_pr__pfet_g5v0d10v5 x5 8 44 w 4.0 l 0.5
gencell_at sky130_fd_pr__pfet_g5v0d10v5 x6 40 44 w 4.0 l 0.5
gencell_at sky130_fd_pr__pfet_g5v0d10v5 xr1 22 44 w 2.0 l 0.5
gencell_at sky130_fd_pr__pfet_g5v0d10v5 xr2 52 44 w 2.0 l 0.5
gencell_at sky130_fd_pr__nfet_g5v0d10v5 xinvn 58 18 w 1.0 l 0.5
gencell_at sky130_fd_pr__pfet_g5v0d10v5 xinvp 58 32 w 2.0 l 0.5
gencell_at sky130_fd_pr__nfet_g5v0d10v5 xnq 70 18 w 2.0 l 0.5
gencell_at sky130_fd_pr__pfet_g5v0d10v5 xpq 70 32 w 4.0 l 0.5
gencell_at sky130_fd_pr__nfet_g5v0d10v5 xnb 82 18 w 2.0 l 0.5
gencell_at sky130_fd_pr__pfet_g5v0d10v5 xpb 82 32 w 4.0 l 0.5

set t_ox 29.065; set t_oy 10.965
set a_ox 13.065; set a_oy 20.965
set b_ox 37.065; set b_oy 20.965
set c_ox 13.065; set c_oy 35.01
set d_ox 37.065; set d_oy 35.01
set e_ox 9.065;  set e_oy 47.01
set f_ox 41.065; set f_oy 47.01
set r1_ox 23.065; set r1_oy 46.01
set r2_ox 53.065; set r2_oy 46.01
set in_ox 59.065; set in_oy 19.465
set ip_ox 59.065; set ip_oy 34.01
set qn_ox 71.065; set qn_oy 19.965
set qp_ox 71.065; set qp_oy 35.01
set bn_ox 83.065; set bn_oy 19.965
set bp_ox 83.065; set bp_oy 35.01

m1 0 0 96 1.5
m1 0 54 96 55.5
pin1 inp 0.5 16 4 20
pin1 inn 0.5 24 4 28
pin1 clk 0.5 4 4 8
pin1 comp_p 88 4 94 10
pin1 avdd 86 52 95 55
pin1 avss 0.5 0 8 2

# clk: pin, tail gate, precharge gates, inverter gates (m3; S/D stay on m2)
via12 2.25 6.0
via23 2.25 6.0
set tclk [gate_via3 $t_ox $t_oy 4.0]
set eclk [gate_via3 $e_ox $e_oy 2.0]
set fclk [gate_via3 $f_ox $f_oy 2.0]
set iclk [gate_via3 $in_ox $in_oy 0.5]
set pclk [gate_via3 $ip_ox $ip_oy 1.0]
mh3 3.6 2.25 57.3 0.35
mv3 2.25 3.6 6.0 0.35
mv3 32.0 3.6 $tclk 0.35
mh3 $tclk 32.0 $t_ox 0.35
# precharge clk: hop m2 so m3 does not cross inp; keep ≥0.3 µm from inp @17.2
mv3 16.5 3.6 29.6 0.35
mv3 16.5 32.0 50.8 0.35
mv3 $e_ox 3.6 15.2 0.35
via23 $e_ox 15.2
mv2 $e_ox 15.2 18.8 0.40
via23 $e_ox 18.8
mv3 $e_ox 18.8 50.8 0.35
mh3 50.8 $e_ox 37.5 0.35
mh3 50.8 40.2 57.3 0.35
mv3 $e_ox 50.8 $eclk 0.35
mv3 $f_ox 50.8 $fclk 0.35
via23 $f_ox 50.8
mv3 57.3 23.7 50.8 0.35
# clk vertical gap at y=22.6 so nd1 m3 can cross; hop on m2
mv3 57.3 3.6 21.5 0.35
via23 57.3 21.5
via23 57.3 23.7
mv2 57.3 21.5 23.7 0.35
mv3 57.3 23.7 $pclk 0.35
mh3 $iclk 57.3 $in_ox 0.35
mh3 $pclk 57.3 $ip_ox 0.35

# ntail: tail drain + input-pair sources
via12 [expr {$t_ox + 0.395}] $t_oy
via12 [expr {$a_ox - 0.395}] $a_oy
via12 [expr {$b_ox - 0.395}] $b_oy
mh2 14.2 [expr {$a_ox - 0.395}] [expr {$b_ox - 0.395}] 0.35
mv2 [expr {$t_ox + 0.395}] $t_oy 14.2 0.35
mv2 [expr {$a_ox - 0.395}] 14.2 $a_oy 0.35
mv2 [expr {$b_ox - 0.395}] 14.2 $b_oy 0.35

# inp / inn to input gates on m3
via12 2.25 18.0
via23 2.25 18.0
set ag [gate_via3 $a_ox $a_oy 2.0]
mh3 17.2 2.25 $a_ox 0.40
mv3 2.25 17.2 18.0 0.40
mv3 $a_ox 17.2 $ag 0.40
via12 2.25 26.0
via23 2.25 26.0
set bg [gate_via3 $b_ox $b_oy 2.0]
# inn spine below the pin via pad (pad extends to ~25.78 with s=0.20)
mh3 25.2 2.25 4.0 0.40
mv3 2.25 25.2 26.0 0.40
set innx [expr {$b_ox + 1.8}]
mv3 4.0 25.2 53.0 0.40
mh3 53.0 4.0 $innx 0.40
mv3 $innx 26.0 53.0 0.40
mh3 26.0 $b_ox $innx 0.40
mv3 $b_ox $bg 26.0 0.40

# nd1: drains on m2 (jogged east of FET so m2 does not weld input gates), gates on m3
set adx [expr {$a_ox + 1.1}]
set cdx [expr {$c_ox + 1.1}]
set r1dx [expr {$r1_ox + 0.395}]
via12 [expr {$a_ox + 0.395}] $a_oy
via12 [expr {$c_ox + 0.395}] $c_oy
via12 $r1dx $r1_oy
mh2 $a_oy [expr {$a_ox + 0.395}] $adx 0.35
mh2 $c_oy [expr {$c_ox + 0.395}] $cdx 0.35
set dg [gate_via3 $d_ox $d_oy 2.0]
set qng [gate_via3 $qn_ox $qn_oy 1.0]
set qpg [gate_via3 $qp_ox $qp_oy 2.0]
mh2 22.6 $adx $r1dx 0.35
mv2 $adx $a_oy 22.6 0.35
mv2 $cdx 22.6 $c_oy 0.35
mv2 $r1dx 22.6 $r1_oy 0.35
via23 $r1dx 22.6
mh3 22.6 $r1dx $qn_ox 0.35
mv3 $qn_ox 22.6 $qng 0.35
mv3 $qp_ox 22.6 $qpg 0.35
set dgsx 42.2
mh3 22.6 $r1dx $dgsx 0.35
mv3 $dgsx 22.6 $dg 0.35
# nd1 to x4 gate: hop m2 under innx (m3 gap). Keep west via clear of d_ox gate pad.
mh3 $dg $d_ox 37.9 0.35
mh3 $dg 40.2 $dgsx 0.35
via23 37.9 $dg
via23 40.2 $dg
mh2 $dg 37.9 40.2 0.35

# nd2: drains on m2 (jogged east of FET), x3 gate on m3
set bdx [expr {$b_ox + 1.1}]
set ddx [expr {$d_ox + 1.1}]
set r2dx [expr {$r2_ox + 0.395}]
via12 [expr {$b_ox + 0.395}] $b_oy
via12 [expr {$d_ox + 0.395}] $d_oy
via12 $r2dx $r2_oy
mh2 $b_oy [expr {$b_ox + 0.395}] $bdx 0.35
mh2 $d_oy [expr {$d_ox + 0.395}] $ddx 0.35
set cg [gate_via3 $c_ox $c_oy 2.0]
mh2 30.8 $bdx $r2dx 0.35
mv2 $bdx $b_oy 30.8 0.35
mv2 $ddx $d_oy 30.8 0.35
mv2 $r2dx 30.8 $r2_oy 0.35
via23 $bdx 30.8
mh3 30.8 $c_ox $bdx 0.35
mv3 $c_ox 30.8 $cg 0.35

# nd1p: x3 source + x5 drain (jog source west so m2 clears the x3 gate via)
set csx [expr {$c_ox - 1.1}]
via12 [expr {$c_ox - 0.395}] $c_oy
via12 [expr {$e_ox + 0.395}] $e_oy
mh2 $c_oy [expr {$c_ox - 0.395}] $csx 0.35
mh2 40.2 $csx [expr {$e_ox + 0.395}] 0.35
mv2 $csx $c_oy 40.2 0.35
mv2 [expr {$e_ox + 0.395}] 40.2 $e_oy 0.35

# nd2p: x4 source + x6 drain (jog source west clear of x4 gate via)
set dsx [expr {$d_ox - 1.1}]
via12 [expr {$d_ox - 0.395}] $d_oy
via12 [expr {$f_ox + 0.395}] $f_oy
mh2 $d_oy [expr {$d_ox - 0.395}] $dsx 0.35
mh2 41.6 $dsx [expr {$f_ox + 0.395}] 0.35
mv2 $dsx $d_oy 41.6 0.35
mv2 [expr {$f_ox + 0.395}] 41.6 $f_oy 0.35

# clkb: inverter drains on m2, reset gates on m3
via12 [expr {$in_ox + 0.395}] $in_oy
via12 [expr {$ip_ox + 0.395}] $ip_oy
set r1g [gate_via3 $r1_ox $r1_oy 1.0]
set r2g [gate_via3 $r2_ox $r2_oy 1.0]
set clkbx 61.0
mh2 $in_oy [expr {$in_ox + 0.395}] $clkbx 0.35
mh2 $ip_oy [expr {$ip_ox + 0.395}] $clkbx 0.35
via23 $clkbx $in_oy
via23 $clkbx $ip_oy
mv2 $clkbx $in_oy $ip_oy 0.40
mv3 $clkbx $in_oy 21.5 0.35
via23 $clkbx 21.5
mv2 $clkbx 21.5 23.7 0.35
via23 $clkbx 23.7
mv3 $clkbx 23.7 38.6 0.35
# clkb at y=38.6: gap at innx (m2 hop) and at clk spine x=57.3
mh3 38.6 $r1_ox 37.5 0.35
via23 37.5 38.6
via23 42.2 38.6
mh2 38.6 37.5 42.2 0.35
mh3 38.6 42.2 56.5 0.35
mh3 38.6 58.1 $clkbx 0.35
via23 56.5 38.6
via23 58.1 38.6
mh2 38.6 56.5 58.1 0.35
# Stay on m3 to the gate vias — do not drop via23 on the FET axis (that
# m2 pad welds the reset drain strap at ox±0.395).
mv3 $r1_ox 38.6 $r1g 0.35
mv3 $r2_ox 38.6 $r2g 0.35

# nq: first buffer drains on m2, second buffer gates on m3
# Jog drain straps east so m2 does not weld the buffer gate vias.
set qndx [expr {$qn_ox + 1.1}]
set qpdx [expr {$qp_ox + 1.1}]
set bndx [expr {$bn_ox + 1.1}]
set bpdx [expr {$bp_ox + 1.1}]
via12 [expr {$qn_ox + 0.395}] $qn_oy
via12 [expr {$qp_ox + 0.395}] $qp_oy
mh2 $qn_oy [expr {$qn_ox + 0.395}] $qndx 0.35
mh2 $qp_oy [expr {$qp_ox + 0.395}] $qpdx 0.35
set bng [gate_via3 $bn_ox $bn_oy 1.0]
set bpg [gate_via3 $bp_ox $bp_oy 2.0]
set nqx 74.5
mh2 $qn_oy $qndx $nqx 0.35
mh2 $qp_oy $qpdx $nqx 0.35
via23 $nqx $qn_oy
via23 $nqx $qp_oy
mv2 $nqx $qn_oy $qp_oy 0.40
# span both buffer drains so xpq joins nq
mv3 $nqx $qn_oy $qp_oy 0.40
mh3 27.0 $nqx $bn_ox 0.35
via23 $nqx 27.0
mv3 $bn_ox 27.0 $bng 0.35
mv3 $bp_ox 27.0 $bpg 0.35

# comp_p: second buffer drains -> pin
via12 [expr {$bn_ox + 0.395}] $bn_oy
via12 [expr {$bp_ox + 0.395}] $bp_oy
mh2 $bn_oy [expr {$bn_ox + 0.395}] $bndx 0.35
mh2 $bp_oy [expr {$bp_ox + 0.395}] $bpdx 0.35
via12 91.0 7.0
mh2 8.4 $bndx 91.0 0.35
mv2 $bndx 8.4 $bn_oy 0.35
mv2 $bpdx 8.4 $bp_oy 0.35
mv2 91.0 7.0 8.4 0.35

# avss on m2 so it does not weld clk/inn/nd1 on m3
foreach {sx sy} [list \
        [expr {$t_ox - 0.395}] $t_oy \
        [expr {$in_ox - 0.395}] $in_oy \
        [expr {$qn_ox - 0.395}] $qn_oy \
        [expr {$bn_ox - 0.395}] $bn_oy] {
    via12 $sx $sy
    via12 $sx 1.2
    mv2 $sx 1.2 $sy 0.35
    via_nwell [expr {$sx - 0.67}] $sy
    mh2 $sy [expr {$sx - 0.67}] $sx 0.35
}

# avdd: pick up pFET source at the top of diffusion, jog west, then up
foreach {sx sy hw} [list \
        [expr {$e_ox - 0.395}] $e_oy 2.0 \
        [expr {$f_ox - 0.395}] $f_oy 2.0 \
        [expr {$r1_ox - 0.395}] $r1_oy 1.0 \
        [expr {$r2_ox - 0.395}] $r2_oy 1.0 \
        [expr {$ip_ox - 0.395}] $ip_oy 1.0 \
        [expr {$qp_ox - 0.395}] $qp_oy 2.0 \
        [expr {$bp_ox - 0.395}] $bp_oy 2.0] {
    set ypick [expr {$sy + $hw - 0.15}]
    set jx [expr {$sx - 1.1}]
    mh1 $ypick $sx $jx 0.35
    mv1 $jx $ypick 54.5 0.35
    via_nwell [expr {$sx - 0.67}] $sy
    mh1 $sy [expr {$sx - 0.67}] $sx 0.35
}
# Euclidean met3.1 fillets at pin / via T-junctions (0.15 keeps met3.2 clear)
foreach {cx cy} {
    2.25 6.0
    2.25 18.0
    2.25 26.0
    2.50 25.45
    2.50 17.45
    2.49 3.84
    4.0 25.2
    4.0 53.0
    9.065 50.8
    13.065 17.2
    13.065 30.8
    23.065 38.6
    32.0 3.6
    32.06 15.58
    37.02 26.05
    38.865 26.0
    38.865 53.0
    42.2 37.56
    57.3 3.6
    57.3 50.8
    61.0 38.6
} {
    m3 [expr {$cx - 0.15}] [expr {$cy - 0.15}] [expr {$cx + 0.15}] [expr {$cy + 0.15}]
}

# pFET nwells: latch row + precharge/reset row, not over the input nFETs
select top cell
boxum 7.0 31.0 90.0 52.0
paint nwell

save comparator
file copy -force comparator.mag layout/magic/comparator.mag
gds write layout/gds/comparator_magic.gds

# ---------------------------------------------------------------------------
# 12-bit R-2R: poly 2R shunts + series R spine + CMOS TGs to vref/avss
#
# Per bit i (LSB at i=0):
#   rsh$i  (L=16 = 2R): bottom = tap t$i, top = node n$i
#   rser$i (L=8  = R):  bottom = n$i,     top = n${i+1}  (n12 == vout)
# Termination xt (L=16): bottom = avss, top = n0
# ---------------------------------------------------------------------------
cellname create r2r_dac
load r2r_dac
set CURRENT_CELL r2r_dac
select top cell

set pitch 13.5
set y_sh 2.0
set y_ser 24.0
set y_nh 48.0
set y_nl 62.0
set y_inv 76.0
# gencell_at point -> pcell origin (xhigh contacts are at origin ±5 / ±9)
set oxr 0.74
set oys16 10.645
set oys8 6.645
set oxn 1.065
set oynh 1.965
set oyph 3.01
set oyinvn 1.465
set oyinvp 2.01
# pFET column east of nFET enough for nwell↔p-tap ≥0.76 µm
set pfet_dx 11.0
set gnd_dx 13.5

gencell_at sky130_fd_pr__res_xhigh_po_0p35 xt 3 $y_sh w 0.35 l 16.0
for {set i 0} {$i < 12} {incr i} {
    set x [expr {12 + $i * $pitch}]
    gencell_at sky130_fd_pr__res_xhigh_po_0p35 rser$i $x $y_ser w 0.35 l 8.0
    gencell_at sky130_fd_pr__res_xhigh_po_0p35 rsh$i $x $y_sh w 0.35 l 16.0
    gencell_at sky130_fd_pr__nfet_g5v0d10v5 nh$i [expr {$x + 7}] $y_nh w 2.0 l 0.5
    gencell_at sky130_fd_pr__pfet_g5v0d10v5 ph$i [expr {$x + $pfet_dx}] $y_nh w 4.0 l 0.5
    gencell_at sky130_fd_pr__nfet_g5v0d10v5 nl$i [expr {$x + 7}] $y_nl w 2.0 l 0.5
    gencell_at sky130_fd_pr__pfet_g5v0d10v5 pl$i [expr {$x + $pfet_dx}] $y_nl w 4.0 l 0.5
    gencell_at sky130_fd_pr__nfet_g5v0d10v5 invn$i [expr {$x + 7}] $y_inv w 1.0 l 0.5
    gencell_at sky130_fd_pr__pfet_g5v0d10v5 invp$i [expr {$x + $pfet_dx}] $y_inv w 2.0 l 0.5
}

set w [expr {12 + 12 * $pitch + 8}]
m1 0 0 $w 1.5
m1 0 88 $w 89.5
# vref below the high TGs so the rail does not run through pFET S/D
mh2 45.5 3.25 [expr {$w - 2}] 0.4

# termination xt: bottom -> avss, top -> n0
set xtx [expr {3 + $oxr}]
set xty_top [expr {$y_sh + $oys16 + 9.0}]
set xty_bot [expr {$y_sh + $oys16 - 9.0}]
mv1 $xtx $xty_bot 1.5 0.35

for {set i 0} {$i < 12} {incr i} {
    set x [expr {12 + $i * $pitch}]
    set rx [expr {$x + $oxr}]
    set rsh_top [expr {$y_sh + $oys16 + 9.0}]
    set rsh_bot [expr {$y_sh + $oys16 - 9.0}]
    set rser_top [expr {$y_ser + $oys8 + 5.0}]
    set rser_bot [expr {$y_ser + $oys8 - 5.0}]
    set mx [expr {$x + 7}]
    set nxh [expr {$mx + $oxn}]
    set pxh [expr {$x + $pfet_dx + $oxn}]
    set nyh [expr {$y_nh + $oynh}]
    set pyh [expr {$y_nh + $oyph}]
    set nyl [expr {$y_nl + $oynh}]
    set pyl [expr {$y_nl + $oyph}]
    set nxi [expr {$mx + $oxn}]
    set pxi [expr {$x + $pfet_dx + $oxn}]
    set nyi [expr {$y_inv + $oyinvn}]
    set pyi [expr {$y_inv + $oyinvp}]

    # n$i: 2R top to series-R bottom (do not extend onto avss or 2R bottom)
    mv1 $rx $rsh_top $rser_bot 0.35

    # t$i: 2R bottom to TG drains. Jump vref on m3 so tap m2 does not hit the rail.
    set tapx [expr {$x + 4.2}]
    set n_dyt [expr {$nyh + 2.2}]
    set p_dyt [expr {$pyh + 3.2}]
    set nl_dyt [expr {$nyl + 2.2}]
    set pl_dyt [expr {$pyl + 3.2}]
    via12 $rx $rsh_bot
    mh2 $rsh_bot $rx $tapx 0.35
    mv2 $tapx $rsh_bot 44.0 0.35
    via23 $tapx 44.0
    via23 $tapx 47.0
    mv3 $tapx 44.0 47.0 0.35
    mv2 $tapx 47.0 $pl_dyt 0.35
    # Drain to tap on m2. m1 jog east of the contact, via at ndx/pdx so the
    # via pad does not sit beside the on-axis gate via. Keep clear of
    # dnx_inv (x+9.5) and avss (gndx = x+13.5).
    set ndx [expr {$nxh + 0.85}]
    set pdx [expr {$pxh + 0.85}]
    set n_dyh [expr {$nyh + 0.55}]
    set p_dyh [expr {$pyh + 0.55}]
    set n_dyl [expr {$nyl + 0.55}]
    set p_dyl [expr {$pyl + 0.55}]
    mh1 $n_dyh [expr {$nxh + 0.35}] $ndx 0.22
    mh1 $p_dyh [expr {$pxh + 0.35}] $pdx 0.22
    mh1 $n_dyl [expr {$nxh + 0.35}] $ndx 0.22
    mh1 $p_dyl [expr {$pxh + 0.35}] $pdx 0.22
    via12 $ndx $n_dyh
    via12 $pdx $p_dyh
    via12 $ndx $n_dyl
    via12 $pdx $p_dyl
    via12 $tapx $n_dyt
    via12 $tapx $p_dyt
    via12 $tapx $nl_dyt
    via12 $tapx $pl_dyt
    mv2 $ndx $n_dyh $n_dyt 0.35
    mv2 $pdx $p_dyh $p_dyt 0.35
    mv2 $ndx $n_dyl $nl_dyt 0.35
    mv2 $pdx $p_dyl $pl_dyt 0.35
    mh2 $n_dyt $ndx $tapx 0.35
    mh2 $p_dyt $pdx $tapx 0.35
    mh2 $nl_dyt $ndx $tapx 0.35
    mh2 $pl_dyt $pdx $tapx 0.35

    # high TG sources -> vref on m2 (m1 out of the FET shorts the tap ring)
    set vsx [expr {$nxh - 1.3}]
    set vpx [expr {$pxh - 1.3}]
    via12 [expr {$nxh - 0.4}] [expr {$nyh - 0.8}]
    via12 [expr {$pxh - 0.4}] [expr {$pyh - 1.8}]
    mh2 [expr {$nyh - 0.8}] [expr {$nxh - 0.4}] $vsx 0.35
    mh2 [expr {$pyh - 1.8}] [expr {$pxh - 0.4}] $vpx 0.35
    mv2 $vsx 45.5 [expr {$nyh - 0.8}] 0.35
    mv2 $vpx 45.5 [expr {$pyh - 1.8}] 0.35

    # avss on m3 so m2 tap/ladder can cross the column
    # avss east of the pFET; source vias inside the ring, then m2 south
    set gndx [expr {$x + $gnd_dx}]
    set sjx [expr {$nxh - 1.6}]
    set pjx [expr {$pxh - 1.6}]
    set nsy [expr {$nyl - 0.5}]
    set psy [expr {$pyl - 0.5}]
    set avy [expr {$nyl - 2.8}]
    via12 $gndx 1.2
    via23 $gndx 1.2
    # avss m3 only outside the series-R band; m2 spine ties the stubs together.
    m3 [expr {$gndx - 0.2}] 1.2 [expr {$gndx + 0.2}] 18.0
    m3 [expr {$gndx - 0.2}] 48.0 [expr {$gndx + 0.2}] $nyi
    mv2 $gndx 1.2 44.8 0.35
    mv2 $gndx 46.2 $nyi 0.35
    via23 $gndx 44.8
    via23 $gndx 46.2
    mv3 $gndx 44.8 46.2 0.35
    via12 $gndx $avy
    via23 $gndx $avy
    via12 $gndx [expr {$nyi - 1.0}]
    via23 $gndx [expr {$nyi - 1.0}]
    via12 [expr {$nxh - 0.4}] $nsy
    via12 [expr {$pxh - 0.4}] $psy
    mh2 $nsy [expr {$nxh - 0.4}] $sjx 0.35
    mv2 $sjx $avy $nsy 0.35
    mh2 $psy [expr {$pxh - 0.4}] $pjx 0.35
    mv2 $pjx $avy $psy 0.35
    mh2 $avy $sjx $gndx 0.35
    # inv nFET source -> avss. Do not via south of the contact (that m1 pad
    # sits on the gate poly contact). Jog west on m1, then down on m2.
    set nsx [expr {$nxi - 0.85}]
    mh1 $nyi [expr {$nxi - 0.35}] $nsx 0.22
    via12 $nsx $nyi
    mv2 $nsx 69.5 $nyi 0.35
    mh2 69.5 $nsx $gndx 0.35
    via12 $gndx 69.5
    via23 $gndx 69.5
    # p-substrate (nFET tap rings) -> avss on devices whose source is already avss.
    # Do not strap the high-nFET ring: that metal crosses the vref source drop.
    via_nwell [expr {$nxi - 1.065}] $nyi
    mh2 $nyi [expr {$nxi - 1.065}] $nsx 0.35
    via_nwell [expr {$nxh - 1.065}] $nsy

    # inverter pFET source -> avdd rail. Jog the vertical west of the FET
    # so it does not run beside the on-axis gate via pad.
    via12 [expr {$pxi - 0.4}] $pyi
    set avdx [expr {$pxi - 1.7}]
    mh2 $pyi [expr {$pxi - 0.4}] $avdx 0.35
    mv2 $avdx $pyi 88.7 0.35
    via12 $avdx 88.7
    # inverter pFET nwell: west tap ring to the existing avdd source strap only
    via_nwell [expr {$pxi - 1.065}] $pyi
    mh2 $pyi [expr {$pxi - 1.065}] [expr {$pxi - 0.4}] 0.35
    # Tie TG pFET nwells on a spine EAST of the pFETs so nwell stays
    # clear of nFET p-taps (diff/tap.20 needs ≥0.76 µm). nwell.1 min width 0.84.
    select top cell
    boxum [expr {$pxh + 0.15}] $pyh [expr {$pxh + 1.05}] $pyi
    paint nwell
    boxum [expr {$pxh - 0.45}] [expr {$pyh - 2.2}] [expr {$pxh + 0.55}] [expr {$pyh + 2.2}]
    paint nwell
    boxum [expr {$pxh - 0.45}] [expr {$pyl - 2.2}] [expr {$pxh + 0.55}] [expr {$pyl + 2.2}]
    paint nwell
    boxum [expr {$pxi - 0.45}] [expr {$pyi - 1.2}] [expr {$pxi + 0.55}] [expr {$pyi + 1.2}]
    paint nwell
    set dnx [expr {$x + 3.0}]
    set dnx_inv [expr {$x + 9.5}]
    set idy 75.0
    set hop 71.0
    # Inv drains: m1 east on contact Y (below gate via), via at jog X so
    # via m1 pad is not beside the gate contact.
    set nidx [expr {$nxi + 0.85}]
    set pidx [expr {$pxi + 0.85}]
    mh1 $nyi [expr {$nxi + 0.35}] $nidx 0.22
    mh1 $pyi [expr {$pxi + 0.35}] $pidx 0.22
    via12 $nidx $nyi
    via12 $pidx $pyi
    mv2 $nidx $idy $nyi 0.35
    mv2 $pidx $idy $pyi 0.35
    mh2 $idy $nidx $dnx_inv 0.35
    mh2 $idy $pidx $dnx_inv 0.35
    mv2 $dnx_inv $hop $idy 0.35
    via23 $dnx_inv $hop
    via23 $dnx $hop
    mh3 $hop $dnx $dnx_inv 0.35

    pin1 dac$i $x 82 [expr {$x + 3}] 86
    set dacx [expr {$x + 1.5}]
    set dac_ng [expr {$nyh + 1.28}]
    set dac_pg [expr {$pyl + 2.28}]
    set dac_ni [expr {$nyi + 0.78}]
    set dac_pi [expr {$pyi + 1.28}]
    set dn_pg [expr {$pyh + 2.28}]
    set dn_ng [expr {$nyl + 1.28}]
    # DAC gates on m3 so they do not weld the m2 tap spine.
    via12 $dacx 82.0
    via23 $dacx 82.0
    mv3 $dacx $dac_ng 82.0 0.35
    # met3.1 fillet at dac spine / high-TG gate stub T
    m3 [expr {$dacx - 0.15}] [expr {$dac_ng - 0.15}] [expr {$dacx + 0.15}] [expr {$dac_ng + 0.15}]
    foreach gyx [list \
        [list $nxh $dac_ng] \
        [list $pxh $dac_pg] \
        [list $nxi $dac_ni] \
        [list $pxi $dac_pi]] {
        set gx [lindex $gyx 0]
        set gy [lindex $gyx 1]
        via12 $gx $gy
        via23 $gx $gy
        mh3 $gy $dacx $gx 0.35
    }
    # d0n m2 spine at dnx (west of tap); m3 stubs at the TG gates only
    mv2 $dnx $dn_pg $idy 0.35
    via23 $dnx $dn_ng
    via23 $dnx $dn_pg
    via12 $nxh $dn_ng
    via23 $nxh $dn_ng
    via12 $pxh $dn_pg
    via23 $pxh $dn_pg
    mh3 $dn_ng $dnx $nxh 0.35
    mh3 $dn_pg $dnx $pxh 0.35
}

# n0: xt top to bit 0 node
set rx0 [expr {12 + $oxr}]
set rsh_top [expr {$y_sh + $oys16 + 9.0}]
via12 $xtx $xty_top
via12 $rx0 $rsh_top
mh2 $xty_top $xtx $rx0 0.4

# series R chain on m3 so the jogs do not weld the m2 tap spines
for {set i 0} {$i < 11} {incr i} {
    set x0 [expr {12 + $i * $pitch + $oxr}]
    set x1 [expr {12 + ($i + 1) * $pitch + $oxr}]
    set xm [expr {12 + $i * $pitch + 6.5}]
    set rser_top [expr {$y_ser + $oys8 + 5.0}]
    set rser_bot [expr {$y_ser + $oys8 - 5.0}]
    set yj [expr {38.0 + $i * 0.38}]
    via12 $x0 $rser_top
    via23 $x0 $rser_top
    via12 $x1 $rser_bot
    via23 $x1 $rser_bot
    mv3 $x0 [expr {$rser_top - 0.25}] [expr {$yj + 0.15}] 0.35
    mh3 $yj $x0 $xm 0.35
    mv3 $xm $yj [expr {$rser_bot - 0.25}] 0.35
    mh3 $rser_bot $xm $x1 0.35
    # met3.1 fillets at series-R L-bends
    m3 [expr {$xm - 0.15}] [expr {$yj - 0.15}] [expr {$xm + 0.15}] [expr {$yj + 0.15}]
    m3 [expr {$x0 - 0.15}] [expr {$yj - 0.15}] [expr {$x0 + 0.15}] [expr {$yj + 0.15}]
}

set x11 [expr {12 + 11 * $pitch + $oxr}]
set rser_top [expr {$y_ser + $oys8 + 5.0}]
via12 $x11 $rser_top
via23 $x11 $rser_top
mh3 $rser_top $x11 [expr {$w - 7}] 0.4
pin1 vout [expr {$w - 10}] [expr {$rser_top - 2}] [expr {$w - 4}] [expr {$rser_top + 2}]
via12 [expr {$w - 7}] $rser_top
via23 [expr {$w - 7}] $rser_top
pin1 vref 0.5 80 6 86
via12 3.25 45.5
via12 3.25 83.0
mv2 3.25 45.5 83.0 0.35
pin1 avss 0.5 0 8 2
pin1 avdd [expr {$w - 12}] 86 [expr {$w - 2}] 89
save r2r_dac
file copy -force r2r_dac.mag layout/magic/r2r_dac.mag
gds write layout/gds/r2r_dac_magic.gds

# ---------------------------------------------------------------------------
# Analog top: S/H + DAC + comparator, SAR analog nets
# ---------------------------------------------------------------------------
cellname create sar_adc_analog
load sar_adc_analog
set CURRENT_CELL sar_adc_analog
select top cell
getcell r2r_dac
select top cell
select cell r2r_dac
identify Xdac
move to 12um 12um
select top cell
getcell sample_hold
select top cell
select cell sample_hold
identify Xsh
move to 12um 108um
select top cell
getcell comparator
select top cell
select cell comparator
identify Xcmp
move to 90um 108um
select top cell

# vhold: S/H -> comparator inp
m2 62 116 92 117
# vdac: R-2R vout -> comparator inn
m2 181 46 181 116
m2 92 124 181 125
# sample_en into S/H
m1 12 134 12 150
# analog supplies
m1 12 12 180 13.2
m1 12 168 180 169.2
pin1 vin_ecg 12 116 18 122
pin1 vref 12 92 18 98
pin1 sample_en 12 148 18 154
pin1 comp_p 178 112 186 118
pin1 clk_cmp 88 112 94 116
for {set i 0} {$i < 12} {incr i} {
    set x [expr {24 + $i * 13}]
    pin1 dac$i $x 94 [expr {$x + 3}] 98
}
pin1 avdd 168 166 180 169
pin1 avss 12 12 24 14
save sar_adc_analog
file copy -force sar_adc_analog.mag layout/magic/sar_adc_analog.mag
gds write layout/gds/sar_adc_analog_magic.gds
close $VIAF
puts "analog gencell GDS written"
quit -noprompt

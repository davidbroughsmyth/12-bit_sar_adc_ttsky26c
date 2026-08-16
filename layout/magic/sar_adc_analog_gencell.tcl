# Sky130 analog SAR blocks via PDK gencells (S/H, R-2R, comparator).
# magic -rcfile $MAGICRC -dnull -noconsole layout/magic/sar_adc_analog_gencell.tcl
drc off
gds rescale false

proc gencell_at {dev inst x y args} {
    box ${x}um ${y}um ${x}um ${y}um
    magic::gencell sky130::${dev} $inst {*}$args
}

proc m1 {x0 y0 x1 y1} {
    box ${x0}um ${y0}um ${x1}um ${y1}um
    paint m1
}

proc m2 {x0 y0 x1 y1} {
    box ${x0}um ${y0}um ${x1}um ${y1}um
    paint m2
}

proc m3 {x0 y0 x1 y1} {
    box ${x0}um ${y0}um ${x1}um ${y1}um
    paint m3
}

proc pin1 {name x0 y0 x1 y1} {
    box ${x0}um ${y0}um ${x1}um ${y1}um
    paint m1
    label $name FreeSans 0.3um -m1
    port make
}

# ---------------------------------------------------------------------------
# Sample/hold: CMOS TG + MIM, 3.3 V g5v0
# ---------------------------------------------------------------------------
cellname create sample_hold
load sample_hold
gencell_at sky130_fd_pr__nfet_g5v0d10v5 xn 8 10 w 8.0 l 0.5
gencell_at sky130_fd_pr__pfet_g5v0d10v5 xp 22 10 w 16.0 l 0.5
gencell_at sky130_fd_pr__nfet_g5v0d10v5 xinvn 8 28 w 1.0 l 0.5
gencell_at sky130_fd_pr__pfet_g5v0d10v5 xinvp 16 28 w 2.0 l 0.5
gencell_at sky130_fd_pr__cap_mim_m3_1 xch 38 8 w 20.0 l 20.0
m1 0 0 70 1.2
m1 0 42 70 43.2
m1 4 8 36 9.2
m2 20 8 50 9.0
m3 36 8 58 28
pin1 vin_ecg 0.5 8 4 12
pin1 vhold 62 8 68 12
pin1 sample_en 0.5 26 4 30
pin1 avdd 58 40 68 43
pin1 avss 0.5 0 8 2
save sample_hold
file mkdir layout/magic layout/gds
file copy -force sample_hold.mag layout/magic/sample_hold.mag
gds write layout/gds/sample_hold_magic.gds

# ---------------------------------------------------------------------------
# Clocked comparator (g5v0 StrongARM-ish)
# ---------------------------------------------------------------------------
cellname create comparator
load comparator
gencell_at sky130_fd_pr__nfet_g5v0d10v5 xtail 28 6 w 8.0 l 0.5
gencell_at sky130_fd_pr__nfet_g5v0d10v5 x1 12 18 w 4.0 l 0.5
gencell_at sky130_fd_pr__nfet_g5v0d10v5 x2 36 18 w 4.0 l 0.5
gencell_at sky130_fd_pr__pfet_g5v0d10v5 x3 12 32 w 4.0 l 0.5
gencell_at sky130_fd_pr__pfet_g5v0d10v5 x4 36 32 w 4.0 l 0.5
gencell_at sky130_fd_pr__pfet_g5v0d10v5 x5 8 44 w 4.0 l 0.5
gencell_at sky130_fd_pr__pfet_g5v0d10v5 x6 40 44 w 4.0 l 0.5
gencell_at sky130_fd_pr__nfet_g5v0d10v5 xinvn 58 18 w 1.0 l 0.5
gencell_at sky130_fd_pr__pfet_g5v0d10v5 xinvp 58 32 w 2.0 l 0.5
gencell_at sky130_fd_pr__nfet_g5v0d10v5 xnq 70 18 w 2.0 l 0.5
gencell_at sky130_fd_pr__pfet_g5v0d10v5 xpq 70 32 w 4.0 l 0.5
gencell_at sky130_fd_pr__nfet_g5v0d10v5 xnb 82 18 w 2.0 l 0.5
gencell_at sky130_fd_pr__pfet_g5v0d10v5 xpb 82 32 w 4.0 l 0.5
m1 0 0 96 1.5
m1 0 54 96 55.5
m1 10 17 50 18.2
m2 26 6 34 20
pin1 inp 0.5 16 4 20
pin1 inn 0.5 24 4 28
pin1 clk 0.5 4 4 8
pin1 comp_p 88 4 94 10
pin1 avdd 86 52 95 55
pin1 avss 0.5 0 8 2
save comparator
file copy -force comparator.mag layout/magic/comparator.mag
gds write layout/gds/comparator_magic.gds

# ---------------------------------------------------------------------------
# 12-bit R-2R: poly resistors + CMOS TGs to vref/avss
# ---------------------------------------------------------------------------
cellname create r2r_dac
load r2r_dac
set pitch 13.0
gencell_at sky130_fd_pr__res_xhigh_po_0p35 xt 3 18 w 0.35 l 16.0
for {set i 0} {$i < 12} {incr i} {
    set x [expr {12 + $i * $pitch}]
    gencell_at sky130_fd_pr__res_xhigh_po_0p35 rser$i $x 28 w 0.35 l 8.0
    gencell_at sky130_fd_pr__res_xhigh_po_0p35 rsh$i $x 18 w 0.35 l 16.0
    gencell_at sky130_fd_pr__nfet_g5v0d10v5 nh$i $x 42 w 2.0 l 0.5
    gencell_at sky130_fd_pr__pfet_g5v0d10v5 ph$i [expr {$x + 5}] 42 w 4.0 l 0.5
    gencell_at sky130_fd_pr__nfet_g5v0d10v5 nl$i $x 56 w 2.0 l 0.5
    gencell_at sky130_fd_pr__pfet_g5v0d10v5 pl$i [expr {$x + 5}] 56 w 4.0 l 0.5
    gencell_at sky130_fd_pr__nfet_g5v0d10v5 invn$i $x 70 w 1.0 l 0.5
    gencell_at sky130_fd_pr__pfet_g5v0d10v5 invp$i [expr {$x + 5}] 70 w 2.0 l 0.5
    m2 $x 40 [expr {$x + 0.4}] 72
    pin1 dac$i $x 82 [expr {$x + 3}] 86
}
set w [expr {12 + 12 * $pitch + 8}]
m1 0 0 $w 1.5
m1 0 88 $w 89.5
m2 3 26 [expr {$w - 8}] 26.5
pin1 vout [expr {$w - 10}] 26 [expr {$w - 4}] 30
pin1 vref 0.5 80 6 86
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
getcell r2r_dac
select cell r2r_dac
identify Xdac
move to 12um 12um
getcell sample_hold
select cell sample_hold
identify Xsh
move to 12um 108um
getcell comparator
select cell comparator
identify Xcmp
move to 90um 108um

# vhold: S/H -> comparator inp
m2 62 116 92 117
# vdac: R-2R vout -> comparator inn
m2 160 38 160 116
m2 92 124 160 125
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
puts "analog gencell GDS written"
quit -noprompt

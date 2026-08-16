# Magic: TT 2x2 3v3 template + analog routes. Run via layout/magic/run_magic.sh
drc off
set TOP tt_um_davidbroughsmyth_sar_adc
set DEF layout/tt/tt_analog_2x2_3v3.def

if {![file exists $DEF]} {
    puts "missing $DEF"
    quit -noprompt
}

def read $DEF
cellname rename tt_um_template $TOP
load $TOP

proc draw_power_stripe {name x} {
    set x2 [expr {$x + 2}]
    box ${x}um 5um ${x2}um 220.76um
    paint met4
    box [expr {$x + 0.8}]um 110um [expr {$x + 1.2}]um 111um
    label $name FreeSans 0.25um -met4
    port make
    if {$name eq "VGND"} {
        port use ground
    } else {
        port use power
    }
    port class bidirectional
    port connections n s e w
}

draw_power_stripe VDPWR 1
draw_power_stripe VGND 4
draw_power_stripe VAPWR 7

# ua[0] vin_ecg into S/H (adjacent met4 drawing — analog pin check)
box 136.32um 0.80um 136.92um 90um
paint met4
box 120um 70um 150um 100um
paint met3
box 120um 70um 150um 100um
paint met4

# ua[1] vref into R-2R
box 117.00um 0.80um 117.60um 40um
paint met4
box 40um 22um 136um 22.4um
paint met2

for {set i 0} {$i < 12} {incr i} {
    set x [expr {44 + $i * 8}]
    box ${x}um 8um [expr {$x + 8}]um 8.35um
    paint poly
    box [expr {$x + 0.4}]um 18um [expr {$x + 0.7}]um 58um
    paint met2
}

# comparator abstract + digital abstract
box 152um 56um 176um 76um
paint met1
box 200um 40um 290um 160um
paint met1

select top cell
file mkdir layout/magic layout/gds layout/lef layout/reports
save ${TOP}
file rename -force ${TOP}.mag layout/magic/${TOP}.mag
gds write layout/gds/${TOP}_magic.gds
lef write layout/lef/${TOP}_magic.lef -hide -pinonly

# Analog extract for netgen (device LVS vs spice when cells exist)
extract do local
extract all
ext2spice lvs
ext2spice
quit -noprompt

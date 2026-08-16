# Magic: 12-bit R-2R poly resistor DAC array (scripted).
drc off
if {[info exists env(PDK_ROOT)]} {
    set tech $env(PDK_ROOT)/sky130A/libs.tech/magic/sky130A.tech
    if {[file exists $tech]} { tech load $tech }
}
box 0um 0um 256um 90um
paint m1
for {set i 0} {$i < 12} {incr i} {
    set x [expr {28 + $i * 18}]
    box ${x}um 40um [expr {$x+8}]um 40.35um
    paint poly
    box ${x}um 20um [expr {$x+16}]um 20.35um
    paint poly
    box ${x}um 78um [expr {$x+3.5}]um 81um
    paint m1
    label dac$i
    port make
}
box 2um 78um 8um 82um
paint m1
label vref
port make
box [expr {256-12}]um 38um [expr {256-6}]um 42um
paint m1
label vout
port make
save layout/magic/r2r_dac.mag
gds write layout/gds/r2r_dac_magic.gds
quit -noprompt

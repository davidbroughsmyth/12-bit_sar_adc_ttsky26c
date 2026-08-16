# Magic: StrongARM / two-stage comparator outline.
drc off
if {[info exists env(PDK_ROOT)]} {
    set tech $env(PDK_ROOT)/sky130A/libs.tech/magic/sky130A.tech
    if {[file exists $tech]} { tech load $tech }
}
box 0um 0um 60um 50um
paint m1
box 10um 18um 18um 26um
paint ndiff
box 32um 18um 40um 26um
paint ndiff
box 1um 20um 5um 23um
paint m1
label inp
port make
box 1um 28um 5um 31um
paint m1
label inn
port make
box 52um 8um 58um 12um
paint m1
label comp_p
port make
box 1um 8um 5um 11um
paint m1
label clk
port make
save layout/magic/comparator.mag
gds write layout/gds/comparator_magic.gds
quit -noprompt

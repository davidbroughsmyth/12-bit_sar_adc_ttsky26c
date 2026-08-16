# Magic analog top: S/H + R-2R + comparator.
drc off
if {[info exists env(PDK_ROOT)]} {
    set tech $env(PDK_ROOT)/sky130A/libs.tech/magic/sky130A.tech
    if {[file exists $tech]} { tech load $tech }
}
box 0um 0um 400um 180um
paint m1
box 10um 100um 90um 150um
paint m3
box 10um 5um 266um 95um
paint m2
box 286um 100um 346um 150um
paint m3
box 2um 118um 10um 124um
paint m1
label vin_ecg
port make
box 2um 80um 10um 86um
paint m1
label vref
port make
box 386um 118um 396um 124um
paint m1
label comp_p
port make
save layout/magic/sar_adc_analog.mag
gds write layout/gds/sar_adc_analog_magic.gds
quit -noprompt

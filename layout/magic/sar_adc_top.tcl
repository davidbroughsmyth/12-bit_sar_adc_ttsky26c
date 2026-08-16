# Magic chip top: analog west, digital east, pad labels.
drc off
if {[info exists env(PDK_ROOT)]} {
    set tech $env(PDK_ROOT)/sky130A/libs.tech/magic/sky130A.tech
    if {[file exists $tech]} { tech load $tech }
}
box 0um 0um 900um 500um
paint m1
box 120um 120um 520um 300um
paint m2
box 560um 120um 760um 280um
paint m3
box 10um 220um 80um 290um
paint m5
label vin_ecg
port make
box 10um 120um 80um 190um
paint m5
label vref
port make
box 20um 10um 90um 80um
paint m5
label clk
port make
save layout/magic/sar_adc_top.mag
gds write layout/gds/sar_adc_top_magic.gds
quit -noprompt

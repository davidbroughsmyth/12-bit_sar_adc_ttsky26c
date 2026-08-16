# Magic sky130A: sample/hold (3.3 V TG + MIM). Batch: magic -dnull -noconsole
drc off
if {[info exists env(PDK_ROOT)]} {
    set tech $env(PDK_ROOT)/sky130A/libs.tech/magic/sky130A.tech
    if {[file exists $tech]} { tech load $tech }
}
box 0um 0um 80um 50um
paint m1
box 40um 10um 70um 40um
paint m3
box 40um 10um 70um 40um
paint m4
box 1um 20um 5um 24um
paint m1
label vin_ecg
port make
box 72um 22um 76um 26um
paint m1
label vhold
port make
box 1um 40um 5um 43um
paint m1
label sample_en
port make
save layout/magic/sample_hold.mag
gds write layout/gds/sample_hold_magic.gds
quit -noprompt

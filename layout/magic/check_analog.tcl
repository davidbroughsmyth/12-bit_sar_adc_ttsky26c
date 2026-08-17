# DRC + extract one analog gencell GDS (after punch_vias).
# ANALOG_CELL=sample_hold|comparator|r2r_dac magic ... check_analog.tcl
drc euclidean on
gds rescale false

if {![info exists env(ANALOG_CELL)] || $env(ANALOG_CELL) eq ""} {
    puts stderr "ANALOG_CELL not set"
    quit -noprompt
}
set name $env(ANALOG_CELL)
set gds layout/gds/${name}_magic.gds
file mkdir layout/reports
gds read $gds
load $name
select top cell
drc check
drc catchup
set rf [open layout/reports/${name}_drc.txt w]
puts $rf "cell $name"
puts $rf [drc listall why]
puts $rf ""
puts $rf "COUNT [drc count total]"
close $rf
extract do local
extract all
ext2spice lvs
ext2spice
if {[file exists ${name}.spice]} {
    file rename -force ${name}.spice layout/reports/${name}_ext.spice
}
puts "checked $name"
quit -noprompt

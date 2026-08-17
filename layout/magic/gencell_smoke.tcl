# Smoke-test Magic PDK gencell (nfet + xhigh poly + MIM)
drc off
gds rescale false
cellname create _gencell_smoke
load _gencell_smoke
box 0um 0um 0um 0um
magic::gencell sky130::sky130_fd_pr__nfet_g5v0d10v5 xn w 2.0 l 0.5
box 15um 0um 15um 0um
magic::gencell sky130::sky130_fd_pr__pfet_g5v0d10v5 xp w 4.0 l 0.5
box 0um 20um 0um 20um
magic::gencell sky130::sky130_fd_pr__res_xhigh_po_0p35 xr w 0.35 l 8.0
box 20um 20um 20um 20um
magic::gencell sky130::sky130_fd_pr__cap_mim_m3_1 xc w 10.0 l 10.0
puts "INSTANCES:"
instance list
select top cell
gds write /tmp/gencell_smoke.gds
quit -noprompt

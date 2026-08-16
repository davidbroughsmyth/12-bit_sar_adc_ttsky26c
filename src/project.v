`default_nettype none
/*
 * Tiny Tapeout top (must live in src/ so tt-gds-action --check-docs finds it).
 * Analog + digital layout is in gds/tt_um_davidbroughsmyth_sar_adc.gds.
 * Synthesizable SAR RTL is under rtl/ (local tests).
 */
module tt_um_davidbroughsmyth_sar_adc (
    input  wire        VGND,
    input  wire        VDPWR, // 1.8v power supply
    input  wire        VAPWR, // 3.3v analog power supply
    input  wire [7:0]  ui_in,
    output wire [7:0]  uo_out,
    input  wire [7:0]  uio_in,
    output wire [7:0]  uio_out,
    output wire [7:0]  uio_oe,
    inout  wire [7:0]  ua, // ua[0]=vin_ecg, ua[1]=vref
    input  wire        ena,
    input  wire        clk,
    input  wire        rst_n
);
    wire unused = &{ena, clk, rst_n, ui_in, uio_in, ua};
endmodule

`default_nettype wire

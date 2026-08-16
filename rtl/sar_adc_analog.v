(* blackbox *)
module sar_adc_analog (
    input  wire        vin_ecg,
    input  wire        vref,
    input  wire        sample_en,
    input  wire [11:0] dac,
    output wire        comp_p,
    input  wire        clk_cmp,
    inout  wire        avdd,
    inout  wire        avss
);
    assign comp_p = 1'b0; // digital TB stub; analog GDS drives this pin
endmodule

`default_nettype none
// TT digital wrapper: gate clk/rst with ena, then SAR FSM + dividers.
module sar_adc_digital_tt (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        ena,
    input  wire        comp_p,
    output wire [11:0] adc,
    output wire        sample_en,
    output wire [11:0] dac,
    output wire        eoc
);
    wire gclk = clk & ena;
    wire grst = rst_n & ena;
    wire sample_tick, sar_clk_en;
    sar_adc_digital u_dig (
        .clk        (gclk),
        .rst_n      (grst),
        .comp_p     (comp_p),
        .adc        (adc),
        .sample_en  (sample_en),
        .dac        (dac),
        .eoc        (eoc),
        .sample_tick(sample_tick),
        .sar_clk_en (sar_clk_en)
    );
    wire unused = &{sample_tick, sar_clk_en};
endmodule
`default_nettype wire

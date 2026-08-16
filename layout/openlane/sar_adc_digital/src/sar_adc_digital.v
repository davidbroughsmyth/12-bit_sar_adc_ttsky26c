// Digital top for 12-bit SAR ADC.
// clk = 50 MHz, rst_n active-low.
// Default: 500 SPS, ~20 kHz bit-trial clock.
module sar_adc_digital #(
    parameter SAMPLE_DIV = 100_000,
    parameter SAR_DIV    = 2_500
) (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        comp_p,
    output wire [11:0] adc,
    output wire        sample_en,
    output wire [11:0] dac,
    output wire        eoc,
    output wire        sample_tick,
    output wire        sar_clk_en
);
    rate_divider #(
        .SAMPLE_DIV(SAMPLE_DIV),
        .SAR_DIV   (SAR_DIV)
    ) u_div (
        .clk        (clk),
        .rst_n      (rst_n),
        .sample_tick(sample_tick),
        .sar_clk_en (sar_clk_en)
    );

    sar_fsm u_fsm (
        .clk        (clk),
        .rst_n      (rst_n),
        .sample_tick(sample_tick),
        .sar_clk_en (sar_clk_en),
        .comp_p     (comp_p),
        .dac        (dac),
        .adc        (adc),
        .sample_en  (sample_en),
        .eoc        (eoc)
    );
endmodule

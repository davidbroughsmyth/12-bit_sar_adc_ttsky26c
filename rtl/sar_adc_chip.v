// Mixed-signal chip wrapper: digital SAR + analog blackbox.
module sar_adc_chip (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        vin_ecg,
    input  wire        vref,
    output wire [11:0] adc,
    output wire        sample_en,
    inout  wire        avdd,
    inout  wire        avss,
    inout  wire        dvdd,
    inout  wire        dvss
);
    wire        comp_p;
    wire [11:0] dac;
    wire        eoc;
    wire        sample_tick;
    wire        sar_clk_en;
    wire        clk_cmp;

    assign clk_cmp = clk;

    sar_adc_digital u_dig (
        .clk        (clk),
        .rst_n      (rst_n),
        .comp_p     (comp_p),
        .adc        (adc),
        .sample_en  (sample_en),
        .dac        (dac),
        .eoc        (eoc),
        .sample_tick(sample_tick),
        .sar_clk_en (sar_clk_en)
    );

    sar_adc_analog u_ana (
        .vin_ecg  (vin_ecg),
        .vref     (vref),
        .sample_en(sample_en),
        .dac      (dac),
        .comp_p   (comp_p),
        .clk_cmp  (clk_cmp),
        .avdd     (avdd),
        .avss     (avss)
    );
endmodule

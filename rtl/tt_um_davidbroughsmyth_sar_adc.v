`default_nettype none
// Local RTL wrapper (not scanned by Tiny Tapeout docs; src/project.v is).
module tt_um_davidbroughsmyth_sar_adc (
    input  wire        VGND,
    input  wire        VDPWR,
    input  wire        VAPWR,
    input  wire [7:0]  ui_in,
    output wire [7:0]  uo_out,
    input  wire [7:0]  uio_in,
    output wire [7:0]  uio_out,
    output wire [7:0]  uio_oe,
    inout  wire [7:0]  ua,
    input  wire        ena,
    input  wire        clk,
    input  wire        rst_n
);
    wire        gated_clk = clk & ena;
    wire        rst_n_g   = rst_n & ena;
    wire [11:0] adc;
    wire [11:0] dac;
    wire        sample_en;
    wire        eoc;
    wire        comp_p;
    wire        sample_tick;
    wire        sar_clk_en;

    sar_adc_digital u_dig (
        .clk        (gated_clk),
        .rst_n      (rst_n_g),
        .comp_p     (comp_p),
        .adc        (adc),
        .sample_en  (sample_en),
        .dac        (dac),
        .eoc        (eoc),
        .sample_tick(sample_tick),
        .sar_clk_en (sar_clk_en)
    );

    sar_adc_analog u_ana (
        .vin_ecg  (ua[0]),
        .vref     (ua[1]),
        .sample_en(sample_en),
        .dac      (dac),
        .comp_p   (comp_p),
        .clk_cmp  (gated_clk),
        .avdd     (VAPWR),
        .avss     (VGND)
    );

    assign uo_out  = ena ? adc[7:0] : 8'b0;
    assign uio_out = ena ? {2'b00, eoc, sample_en, adc[11:8]} : 8'b0;
    assign uio_oe  = ena ? 8'h3F : 8'h00;

    wire unused = |{ui_in, uio_in, VDPWR, ua[7:2], sample_tick, sar_clk_en};
endmodule

`default_nettype wire

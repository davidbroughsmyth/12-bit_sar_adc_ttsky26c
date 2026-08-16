// Rate divider: 50 MHz clk -> 500 SPS sample_tick and 20 kHz sar_clk_en.
// SAMPLE_DIV = 50e6 / 500 = 100_000
// SAR_DIV    = 50e6 / 20e3 = 2_500  (bit-trial period ~50 us)
module rate_divider #(
    parameter SAMPLE_DIV = 100_000,
    parameter SAR_DIV    = 2_500
) (
    input  wire clk,
    input  wire rst_n,
    output reg  sample_tick,
    output reg  sar_clk_en
);
    localparam integer SAMPLE_W = (SAMPLE_DIV <= 1) ? 1 : $clog2(SAMPLE_DIV);
    localparam integer SAR_W    = (SAR_DIV    <= 1) ? 1 : $clog2(SAR_DIV);

    reg [SAMPLE_W-1:0] sample_cnt;
    reg [SAR_W-1:0]    sar_cnt;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sample_cnt  <= {SAMPLE_W{1'b0}};
            sar_cnt     <= {SAR_W{1'b0}};
            sample_tick <= 1'b0;
            sar_clk_en  <= 1'b0;
        end else begin
            if (sample_cnt == SAMPLE_DIV[SAMPLE_W-1:0] - 1'b1) begin
                sample_cnt  <= {SAMPLE_W{1'b0}};
                sample_tick <= 1'b1;
            end else begin
                sample_cnt  <= sample_cnt + 1'b1;
                sample_tick <= 1'b0;
            end

            if (sar_cnt == SAR_DIV[SAR_W-1:0] - 1'b1) begin
                sar_cnt    <= {SAR_W{1'b0}};
                sar_clk_en <= 1'b1;
            end else begin
                sar_cnt    <= sar_cnt + 1'b1;
                sar_clk_en <= 1'b0;
            end
        end
    end
endmodule

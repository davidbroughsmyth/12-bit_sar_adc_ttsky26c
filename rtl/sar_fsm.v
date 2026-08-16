// 12-bit successive-approximation FSM.
// Timing (on sar_clk_en):
//   TRACK (sample_en=1) -> 12 bit trials (MSB first) -> UPDATE (latch adc, eoc)
// Comparator: comp_p=1 means vin >= vdac (keep trial bit), else clear.
module sar_fsm (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        sample_tick,
    input  wire        sar_clk_en,
    input  wire        comp_p,
    output reg  [11:0] dac,
    output reg  [11:0] adc,
    output reg         sample_en,
    output reg         eoc
);
    localparam [1:0] ST_IDLE    = 2'd0;
    localparam [1:0] ST_TRACK   = 2'd1;
    localparam [1:0] ST_CONVERT = 2'd2;
    localparam [1:0] ST_UPDATE  = 2'd3;

    reg [1:0] state;
    reg [3:0] bit_idx;
    reg       sample_req;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state      <= ST_IDLE;
            bit_idx    <= 4'd11;
            dac        <= 12'h000;
            adc        <= 12'h000;
            sample_en  <= 1'b0;
            eoc        <= 1'b0;
            sample_req <= 1'b0;
        end else begin
            eoc <= 1'b0;
            if (sample_tick)
                sample_req <= 1'b1;

            if (sar_clk_en) begin
                case (state)
                    ST_IDLE: begin
                        sample_en <= 1'b0;
                        if (sample_req || sample_tick) begin
                            sample_req <= 1'b0;
                            sample_en  <= 1'b1;
                            dac        <= 12'h000;
                            bit_idx    <= 4'd11;
                            state      <= ST_TRACK;
                        end
                    end
                    ST_TRACK: begin
                        sample_en <= 1'b0;
                        dac       <= 12'h800;
                        bit_idx   <= 4'd11;
                        state     <= ST_CONVERT;
                    end
                    ST_CONVERT: begin : conv
                        reg [11:0] nd;
                        sample_en <= 1'b0;
                        nd = dac;
                        if (!comp_p)
                            nd[bit_idx] = 1'b0;
                        if (bit_idx == 4'd0) begin
                            dac   <= nd;
                            state <= ST_UPDATE;
                        end else begin
                            nd[bit_idx - 4'd1] = 1'b1;
                            dac                <= nd;
                            bit_idx            <= bit_idx - 4'd1;
                        end
                    end
                    ST_UPDATE: begin
                        sample_en <= 1'b0;
                        adc       <= dac;
                        eoc       <= 1'b1;
                        state     <= ST_IDLE;
                    end
                    default: state <= ST_IDLE;
                endcase
            end
        end
    end
endmodule

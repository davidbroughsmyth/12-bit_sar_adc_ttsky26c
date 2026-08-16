`timescale 1ns/1ps

module tb_rate_divider;
    localparam SAMPLE_DIV = 1000;
    localparam SAR_DIV    = 250;

    reg clk;
    reg rst_n;
    wire sample_tick;
    wire sar_clk_en;

    integer sample_edges;
    integer sar_edges;
    integer last_sample;
    integer last_sar;
    integer i;
    integer errors;

    rate_divider #(
        .SAMPLE_DIV(SAMPLE_DIV),
        .SAR_DIV   (SAR_DIV)
    ) dut (
        .clk        (clk),
        .rst_n      (rst_n),
        .sample_tick(sample_tick),
        .sar_clk_en (sar_clk_en)
    );

    initial clk = 1'b0;
    always #10 clk = ~clk; // 50 MHz

    initial begin
        errors = 0;
        sample_edges = 0;
        sar_edges = 0;
        last_sample = 0;
        last_sar = 0;
        rst_n = 1'b0;
        repeat (8) @(posedge clk);
        rst_n = 1'b1;

        // Reset: ticks must be low immediately after release
        @(posedge clk);
        if (sample_tick !== 1'b0 || sar_clk_en !== 1'b0) begin
            $display("FAIL: ticks not low after reset");
            errors = errors + 1;
        end

        for (i = 0; i < SAMPLE_DIV * 4; i = i + 1) begin
            @(posedge clk);
            #1;
            if (sample_tick) begin
                if (sample_edges > 0 && (i - last_sample) !== SAMPLE_DIV) begin
                    $display("FAIL: sample_tick period %0d expected %0d", i - last_sample, SAMPLE_DIV);
                    errors = errors + 1;
                end
                last_sample = i;
                sample_edges = sample_edges + 1;
            end
            if (sar_clk_en) begin
                if (sar_edges > 0 && (i - last_sar) !== SAR_DIV) begin
                    $display("FAIL: sar_clk_en period %0d expected %0d", i - last_sar, SAR_DIV);
                    errors = errors + 1;
                end
                last_sar = i;
                sar_edges = sar_edges + 1;
            end
        end

        if (sample_edges !== 4) begin
            $display("FAIL: sample_tick count %0d expected 4", sample_edges);
            errors = errors + 1;
        end
        if (sar_edges !== (SAMPLE_DIV * 4) / SAR_DIV) begin
            $display("FAIL: sar_clk_en count %0d expected %0d",
                     sar_edges, (SAMPLE_DIV * 4) / SAR_DIV);
            errors = errors + 1;
        end

        if (errors == 0)
            $display("PASS: tb_rate_divider");
        else
            $display("FAIL: tb_rate_divider errors=%0d", errors);
        $finish;
    end
endmodule

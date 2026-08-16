`timescale 1ns/1ps

module tb_sar_timing;
    localparam SAMPLE_DIV = 80;
    localparam SAR_DIV    = 4;

    reg clk;
    reg rst_n;
    wire [11:0] adc;
    wire        sample_en;
    wire [11:0] dac;
    wire        eoc;
    wire        sample_tick;
    wire        sar_clk_en;
    wire        comp_p;

    integer errors;
    integer se_width;
    integer converting;
    integer eoc_seen;
    integer samples;

    // Mid-scale input
    assign comp_p = (dac <= 12'd2048);

    sar_adc_digital #(
        .SAMPLE_DIV(SAMPLE_DIV),
        .SAR_DIV   (SAR_DIV)
    ) dut (
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

    initial clk = 1'b0;
    always #10 clk = ~clk;

    initial begin
        errors = 0;
        rst_n = 1'b0;
        converting = 0;
        eoc_seen = 0;
        samples = 0;
        repeat (5) @(posedge clk);
        rst_n = 1'b1;

        repeat (SAMPLE_DIV * 6) @(posedge clk);

        if (samples < 4) begin
            $display("FAIL: expected >=4 samples, got %0d", samples);
            errors = errors + 1;
        end
        if (errors == 0)
            $display("PASS: tb_sar_timing");
        else
            $display("FAIL: tb_sar_timing errors=%0d", errors);
        $finish;
    end

    always @(posedge clk) begin
        if (!rst_n) begin
            se_width <= 0;
            converting <= 0;
        end else begin
            if (sample_en) begin
                se_width <= se_width + 1;
                converting <= 1;
                if (dac !== 12'h000) begin
                    $display("FAIL: dac not 0 during sample_en at t=%0t", $time);
                    errors <= errors + 1;
                end
            end else if (se_width != 0) begin
                // sample_en high for exactly one SAR period = SAR_DIV clocks
                if (se_width !== SAR_DIV) begin
                    $display("FAIL: sample_en width %0d expected %0d", se_width, SAR_DIV);
                    errors <= errors + 1;
                end
                se_width <= 0;
            end
            if (eoc) begin
                eoc_seen <= 1;
                samples <= samples + 1;
                converting <= 0;
            end
        end
    end
endmodule

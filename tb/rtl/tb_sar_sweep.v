`timescale 1ns/1ps

module tb_sar_sweep;
    localparam SAMPLE_DIV = 80;
    localparam SAR_DIV    = 4;
    localparam VREF       = 3.3;

    reg clk;
    reg rst_n;
    real vin;
    wire [11:0] adc;
    wire        sample_en;
    wire [11:0] dac;
    wire        eoc;
    wire        sample_tick;
    wire        sar_clk_en;
    wire        comp_p;

    integer errors;
    integer code;
    integer expected;
    integer bit_i;
    integer trial;
    integer result;

    assign comp_p = (vin >= (VREF * dac / 4096.0)) ? 1'b1 : 1'b0;

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

    function integer golden_sar;
        input integer vin_code;
        begin
            result = 0;
            for (bit_i = 11; bit_i >= 0; bit_i = bit_i - 1) begin
                trial = result | (1 << bit_i);
                if (vin_code >= trial)
                    result = trial;
            end
            golden_sar = result;
        end
    endfunction

    initial begin
        errors = 0;
        vin = 0.0;
        rst_n = 1'b0;
        repeat (8) @(posedge clk);
        rst_n = 1'b1;

        begin : sweep_loop
            for (code = 0; code < 4096; code = code + 1) begin
                vin = VREF * code / 4096.0;
                @(posedge eoc);
                @(posedge clk);
                #1;
                expected = golden_sar(code);
                if (adc !== expected) begin
                    $display("FAIL: code=%0d adc=%0d expected=%0d", code, adc, expected);
                    errors = errors + 1;
                    if (errors > 16)
                        disable sweep_loop;
                end
            end
        end
        if (errors == 0)
            $display("PASS: tb_sar_sweep 4096 codes");
        else
            $display("FAIL: tb_sar_sweep errors=%0d", errors);
        $finish;
    end
endmodule

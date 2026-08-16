`timescale 1ns/1ps

module tb_sar_adc_digital;
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
    integer eoc_count;
    integer sample_en_high;
    integer sample_en_edges;
    integer last_adc;
    integer i;
    integer expected;
    integer got;
    integer codes [0:15];
    integer ncodes;

    // Ideal R-2R: Vdac = VREF * dac / 4096
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
        integer bit_i;
        integer trial;
        integer result;
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

    task wait_eoc;
        begin
            @(posedge eoc);
            @(posedge clk);
            #1;
        end
    endtask

    initial begin
        errors = 0;
        eoc_count = 0;
        sample_en_high = 0;
        sample_en_edges = 0;
        last_adc = 0;
        vin = 0.0;
        rst_n = 1'b0;
        repeat (10) @(posedge clk);
        if (adc !== 12'h000 || dac !== 12'h000 || sample_en !== 1'b0 || eoc !== 1'b0) begin
            $display("FAIL: reset did not clear outputs adc=%h dac=%h sample_en=%b eoc=%b",
                     adc, dac, sample_en, eoc);
            errors = errors + 1;
        end
        rst_n = 1'b1;

        // Corner / walking-one codes (vin as equivalent integer code)
        ncodes = 16;
        codes[0]  = 0;
        codes[1]  = 1;
        codes[2]  = 2;
        codes[3]  = 2047;
        codes[4]  = 2048;
        codes[5]  = 2049;
        codes[6]  = 4095;
        codes[7]  = 4094;
        codes[8]  = 1;
        codes[9]  = 2;
        codes[10] = 4;
        codes[11] = 8;
        codes[12] = 16;
        codes[13] = 256;
        codes[14] = 1024;
        codes[15] = 3072;

        for (i = 0; i < ncodes; i = i + 1) begin
            vin = VREF * codes[i] / 4096.0;
            wait_eoc();
            expected = golden_sar(codes[i]);
            got = adc;
            if (got !== expected) begin
                $display("FAIL: vin_code=%0d got=%0d expected=%0d", codes[i], got, expected);
                errors = errors + 1;
            end
        end

        if (errors == 0)
            $display("PASS: tb_sar_adc_digital corners");
        else
            $display("FAIL: tb_sar_adc_digital errors=%0d", errors);
        $finish;
    end

    always @(posedge clk) begin
        if (rst_n && eoc)
            eoc_count <= eoc_count + 1;
        if (rst_n && sample_en)
            sample_en_high <= sample_en_high + 1;
    end

    always @(posedge sample_en)
        sample_en_edges <= sample_en_edges + 1;

    // adc must only change at EOC
    always @(posedge clk) begin
        if (rst_n) begin
            if (adc !== last_adc && !eoc) begin
                $display("FAIL: adc changed without eoc: %0d -> %0d t=%0t", last_adc, adc, $time);
                errors = errors + 1;
            end
            last_adc <= adc;
        end else
            last_adc <= 0;
    end
endmodule

`timescale 1ns/1ps
module tb_tt_um_sar_adc;
    reg VGND, VDPWR, VAPWR, ena, clk, rst_n;
    reg [7:0] ui_in, uio_in;
    wire [7:0] uo_out, uio_out, uio_oe;
    wire [7:0] ua;

    pullup (ua[1]); // vref idle; analog not driven in this digital TB

    tt_um_davidbroughsmyth_sar_adc dut (
        .VGND(VGND), .VDPWR(VDPWR), .VAPWR(VAPWR),
        .ui_in(ui_in), .uo_out(uo_out),
        .uio_in(uio_in), .uio_out(uio_out), .uio_oe(uio_oe),
        .ua(ua), .ena(ena), .clk(clk), .rst_n(rst_n)
    );

    initial clk = 0;
    always #10 clk = ~clk;

    initial begin
        VGND = 0; VDPWR = 1; VAPWR = 1;
        ui_in = 0; uio_in = 0; ena = 0; rst_n = 0;
        repeat (4) @(posedge clk);
        if (uo_out !== 8'h00 || uio_oe !== 8'h00) begin
            $display("FAIL: ena=0 should Hi-Z/zero outputs");
            $finish;
        end
        ena = 1;
        rst_n = 1;
        repeat (20) @(posedge clk);
        if (uio_oe !== 8'h3F) begin
            $display("FAIL: uio_oe expected 3F got %h", uio_oe);
            $finish;
        end
        $display("PASS: tb_tt_um_sar_adc");
        $finish;
    end
endmodule

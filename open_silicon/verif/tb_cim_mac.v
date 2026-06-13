`timescale 1ns/1ps
`default_nettype none
//
// Self-checking testbench for cim_mac_controller (8x8 INT8 systolic GEMM).
// Loads A and B over Wishbone, runs the array, reads back C, and compares
// against a software reference. Exits non-zero on any mismatch.
//
//   iverilog -g2012 -o build/tb_cim_mac.vvp \
//       open_silicon/rtl/cim_mac_controller.v open_silicon/verif/tb_cim_mac.v
//   vvp build/tb_cim_mac.vvp

module tb_cim_mac;
    localparam N = 8;

    reg         clk = 1'b0;
    reg         rst = 1'b1;
    reg         wb_stb = 1'b0;
    reg         wb_we  = 1'b0;
    reg  [31:0] wb_addr = 32'b0;
    reg  [31:0] wb_data_in = 32'b0;
    wire [31:0] wb_data_out;
    wire        wb_ack;
    wire [7:0]  analog_io;   // inout, intentionally left unconnected

    cim_mac_controller #(.N(N)) dut (
        .clk(clk), .rst(rst),
        .wb_stb(wb_stb), .wb_we(wb_we), .wb_addr(wb_addr),
        .wb_data_in(wb_data_in), .wb_data_out(wb_data_out), .wb_ack(wb_ack),
        .analog_io(analog_io)
    );

    always #5 clk = ~clk;   // 100 MHz

    integer A   [0:N-1][0:N-1];
    integer B   [0:N-1][0:N-1];
    integer Cref[0:N-1][0:N-1];
    integer errors = 0;
    integer tests  = 0;

    // --- Wishbone helpers (set up on negedge, hand off across posedge) ---
    task wb_write(input [31:0] addr, input [31:0] data);
        begin
            @(negedge clk);
            wb_addr = addr; wb_data_in = data; wb_we = 1'b1; wb_stb = 1'b1;
            @(posedge clk);
            while (!wb_ack) @(posedge clk);
            @(negedge clk);
            wb_stb = 1'b0; wb_we = 1'b0;
        end
    endtask

    task wb_read(input [31:0] addr, output [31:0] data);
        begin
            @(negedge clk);
            wb_addr = addr; wb_we = 1'b0; wb_stb = 1'b1;
            @(posedge clk);
            while (!wb_ack) @(posedge clk);
            data = wb_data_out;
            @(negedge clk);
            wb_stb = 1'b0;
        end
    endtask

    // signed byte for packing
    function [7:0] sb(input integer v);
        sb = v[7:0];
    endfunction

    integer i, j, kk, w;
    reg [31:0] word, rd;

    task load_and_run;
        begin
            // compute reference
            for (i = 0; i < N; i = i + 1)
                for (j = 0; j < N; j = j + 1) begin
                    Cref[i][j] = 0;
                    for (kk = 0; kk < N; kk = kk + 1)
                        Cref[i][j] = Cref[i][j] + A[i][kk] * B[kk][j];
                end

            // load A (0x100), row-major, 4 signed bytes per word
            for (w = 0; w < (N*N)/4; w = w + 1) begin
                word = { sb(A[(w*4+3)/N][(w*4+3)%N]),
                         sb(A[(w*4+2)/N][(w*4+2)%N]),
                         sb(A[(w*4+1)/N][(w*4+1)%N]),
                         sb(A[(w*4+0)/N][(w*4+0)%N]) };
                wb_write(32'h100 + w*4, word);
            end
            // load B (0x200)
            for (w = 0; w < (N*N)/4; w = w + 1) begin
                word = { sb(B[(w*4+3)/N][(w*4+3)%N]),
                         sb(B[(w*4+2)/N][(w*4+2)%N]),
                         sb(B[(w*4+1)/N][(w*4+1)%N]),
                         sb(B[(w*4+0)/N][(w*4+0)%N]) };
                wb_write(32'h200 + w*4, word);
            end

            // start, then poll STATUS until done
            wb_write(32'h000, 32'h1);
            rd = 0;
            while (!rd[0]) wb_read(32'h004, rd);

            // read C and compare
            for (i = 0; i < N; i = i + 1)
                for (j = 0; j < N; j = j + 1) begin
                    wb_read(32'h400 + (i*N + j)*4, rd);
                    tests = tests + 1;
                    if ($signed(rd) !== Cref[i][j]) begin
                        errors = errors + 1;
                        $display("  MISMATCH C[%0d][%0d]: hw=%0d ref=%0d",
                                 i, j, $signed(rd), Cref[i][j]);
                    end
                end
        end
    endtask

    integer seed = 32'hC1A0;
    reg [7:0] ra, rb;
    task gen_random;
        begin
            for (i = 0; i < N; i = i + 1)
                for (j = 0; j < N; j = j + 1) begin
                    // take 8 bits and sign-interpret -> proper INT8 in -128..127
                    ra = $random(seed); rb = $random(seed);
                    A[i][j] = $signed(ra);
                    B[i][j] = $signed(rb);
                end
        end
    endtask

    task gen_fill(input integer av, input integer bv);
        begin
            for (i = 0; i < N; i = i + 1)
                for (j = 0; j < N; j = j + 1) begin
                    A[i][j] = av; B[i][j] = bv;
                end
        end
    endtask

    task gen_identity_b;  // B = identity, A = ramp  => C should equal A
        begin
            for (i = 0; i < N; i = i + 1)
                for (j = 0; j < N; j = j + 1) begin
                    A[i][j] = (i*N + j) % 100 - 50;
                    B[i][j] = (i == j) ? 1 : 0;
                end
        end
    endtask

    integer trial;
    initial begin
        // reset
        repeat (4) @(posedge clk);
        rst = 1'b0;
        repeat (2) @(posedge clk);

        $display("[TB] cim_mac_controller 8x8 INT8 systolic GEMM");

        $display("[TB] Test 1: B = identity (C should equal A)");
        gen_identity_b; load_and_run;

        $display("[TB] Test 2: edge values A=+127, B=+127");
        gen_fill(127, 127); load_and_run;

        $display("[TB] Test 3: edge values A=-128, B=-128");
        gen_fill(-128, -128); load_and_run;

        for (trial = 0; trial < 5; trial = trial + 1) begin
            $display("[TB] Test %0d: random signed matrices", 4 + trial);
            gen_random; load_and_run;
        end

        $display("[TB] %0d checks, %0d errors", tests, errors);
        if (errors == 0) $display("[TB] RESULT: PASS");
        else             $display("[TB] RESULT: FAIL");
        if (errors != 0) $fatal(1, "verification failed");
        $finish;
    end

    // safety timeout
    initial begin
        #1_000_000;
        $display("[TB] TIMEOUT");
        $fatal(1, "timeout");
    end
endmodule
`default_nettype wire

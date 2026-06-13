`default_nettype none
// SPDX-FileCopyrightText: 2026 Project Moonshot
// Licensed under the Apache License, Version 2.0 (the "License")
//
// Digital Compute-in-Memory (CIM) tile: an 8x8 output-stationary INT8 systolic
// MAC array that computes C = A x B (signed 8-bit operands, 32-bit signed
// accumulators), wired to the Caravel Wishbone bus. This replaces the earlier
// 0xDEADBEEF interface stub so the synthesized logic reflects real compute
// (64 multiply-accumulate processing elements).
//
// PIPELINING (for all-corner 100 MHz / 10 ns closure on Sky130 130nm): a
// single-cycle 8x8 multiply + 32b accumulate is ~19 ns, and even one product
// register left the 8x8 multiply itself ~12 ns at the slow corner. We pipeline
// into stages:
//   (1) registered edge feeds  -> takes the input mux out of the multiply path
//   (2) split 8x8 multiply into two 8x4 partial products (registered):
//         a*b = 16*(a*bHi) + (a*bLo),  bHi = signed b[7:4], bLo = unsigned b[3:0]
//   (3) combine the partial products (registered)
//   (4) accumulate
// Operands still march one PE/cycle (the propagation registers ARE the systolic
// skew). Because accumulators are cleared once at start and add the registered
// product every cycle (out-of-window products are 0), the exact pipeline
// latency does not affect the result -- only RUN_CYCLES must cover it.
//
// NOTE: This is the *digital* CIM datapath. The analog charge-domain crossbar
// remains a behavioral/SPICE model (open_silicon/verif/analog_macro.spice) and
// is future hard-macro work; it cannot be expressed in synthesizable RTL.
//
// Wishbone register map (32-bit words):
//   0x000 CTRL   (W)  bit0 = start compute
//   0x004 STATUS (R)  bit0 = result valid (done)
//   0x100..0x13C A    (W)  activation matrix, 4x INT8 packed/word, row-major
//   0x200..0x23C B    (W)  weight matrix,     4x INT8 packed/word, row-major
//   0x400..0x4FC C    (R)  64 result words; word (i*8+j) = C[i][j]

// ---------------------------------------------------------------------------
// Processing element (2-stage: registered product, then accumulate)
// ---------------------------------------------------------------------------
module cim_pe (
    input  wire               clk,
    input  wire               rst,
    input  wire               clr_acc,  // clear accumulator (start of run)
    input  wire               en,       // accumulate registered product
    input  wire signed [7:0]  a_in,
    input  wire signed [7:0]  b_in,
    output reg  signed [7:0]  a_out,
    output reg  signed [7:0]  b_out,
    output reg  signed [31:0] acc
);
    // Two-stage pipelined signed multiply (split b into high/low nibbles) so a
    // full 8x8 multiply never forms the critical path at the slow corner.
    reg signed [12:0] pH, pL;   // stage 1: partial products a*bHi (s8*s4), a*bLo (s8*u4)
    reg signed [16:0] prod;     // stage 2: combined product a*b = 16*pH + pL
    always @(posedge clk) begin
        if (rst) begin
            a_out <= 8'sd0;
            b_out <= 8'sd0;
            pH    <= 13'sd0;
            pL    <= 13'sd0;
            prod  <= 17'sd0;
            acc   <= 32'sd0;
        end else begin
            a_out <= a_in;                                  // systolic propagation (east)
            b_out <= b_in;                                  // systolic propagation (south)
            pH    <= a_in * $signed(b_in[7:4]);             // stage 1a: a * bHi  (s8 * s4)
            pL    <= a_in * $signed({1'b0, b_in[3:0]});     // stage 1b: a * bLo  (s8 * u4)
            prod  <= pH * 6'sd16 + pL;                      // stage 2: a*b = 16*pH + pL
            if (clr_acc)
                acc <= 32'sd0;                              // clear once at start of run
            else if (en)
                acc <= acc + prod;                          // stage 3: accumulate
        end
    end
endmodule

// ---------------------------------------------------------------------------
// 8x8 systolic array
// ---------------------------------------------------------------------------
module cim_systolic_array #(
    parameter N = 8
) (
    input  wire                clk,
    input  wire                rst,
    input  wire                clr_acc,
    input  wire                en,
    input  wire [N*8-1:0]      a_west,    // lane i = bits [i*8 +: 8]
    input  wire [N*8-1:0]      b_north,   // lane j = bits [j*8 +: 8]
    output wire [N*N*32-1:0]   c_flat     // PE[i][j] -> word (i*N+j)
);
    genvar i, j;

    // a_h[i][j] feeds PE[i][j].a_in; PE drives a_h[i][j+1] (east hop).
    // b_v[i][j] feeds PE[i][j].b_in; PE drives b_v[i+1][j] (south hop).
    wire signed [7:0] a_h [0:N-1][0:N];
    wire signed [7:0] b_v [0:N][0:N-1];

    generate
        for (i = 0; i < N; i = i + 1) begin : g_west
            assign a_h[i][0] = $signed(a_west[i*8 +: 8]);
        end
        for (j = 0; j < N; j = j + 1) begin : g_north
            assign b_v[0][j] = $signed(b_north[j*8 +: 8]);
        end
        for (i = 0; i < N; i = i + 1) begin : g_row
            for (j = 0; j < N; j = j + 1) begin : g_col
                cim_pe pe (
                    .clk(clk), .rst(rst), .clr_acc(clr_acc), .en(en),
                    .a_in(a_h[i][j]),    .b_in(b_v[i][j]),
                    .a_out(a_h[i][j+1]), .b_out(b_v[i+1][j]),
                    .acc(c_flat[(i*N+j)*32 +: 32])
                );
            end
        end
    endgenerate
endmodule

// ---------------------------------------------------------------------------
// Wishbone-attached controller
// ---------------------------------------------------------------------------
module cim_mac_controller #(
    parameter N = 8
) (
`ifdef USE_POWER_PINS
    inout vdda1,    // Analog VDD (reserved)
    inout vssa1,    // Analog GND
    inout vccd1,    // Digital VDD
    inout vssd1,    // Digital GND
`endif
    input  wire        clk,
    input  wire        rst,
    input  wire        wb_stb,
    input  wire        wb_we,
    input  wire [31:0] wb_addr,
    input  wire [31:0] wb_data_in,
    output reg  [31:0] wb_data_out,
    output reg         wb_ack,
    inout  wire [7:0]  analog_io   // reserved for future analog macro; unused
);
    // Worst-case product lands at cycle (i+j+k)=21, plus feed-reg (+1) and the
    // 2-stage multiply pipeline (+2) -> ~24; RUN_CYCLES adds margin.
    localparam [5:0] RUN_CYCLES = 6'd36;
    localparam S_IDLE = 1'b0, S_RUN = 1'b1;

    reg signed [7:0] a_mem [0:N*N-1];
    reg signed [7:0] b_mem [0:N*N-1];

    reg        state;
    reg [5:0]  t;
    reg        done;
    reg        start_pulse;
    integer    bi;

    wire clr_acc = (state == S_RUN) && (t == 6'd0);
    wire en      = (state == S_RUN) && (t != 6'd0);

    // --- skewed edge feeds (combinational select from operand memories) ---
    reg signed [7:0] a_west_arr  [0:N-1];
    reg signed [7:0] b_north_arr [0:N-1];
    integer k;
    always @(*) begin
        for (k = 0; k < N; k = k + 1) begin
            if (state == S_RUN && t >= k[5:0] && t <= (k[5:0] + 6'd7)) begin
                a_west_arr[k]  = a_mem[k*N + (t - k)];
                b_north_arr[k] = b_mem[(t - k)*N + k];
            end else begin
                a_west_arr[k]  = 8'sd0;
                b_north_arr[k] = 8'sd0;
            end
        end
    end

    // --- pipeline stage: register the edge feeds (mux out of multiply path) ---
    reg signed [7:0] a_west_q  [0:N-1];
    reg signed [7:0] b_north_q [0:N-1];
    integer kq;
    always @(posedge clk) begin
        if (rst) begin
            for (kq = 0; kq < N; kq = kq + 1) begin
                a_west_q[kq]  <= 8'sd0;
                b_north_q[kq] <= 8'sd0;
            end
        end else begin
            for (kq = 0; kq < N; kq = kq + 1) begin
                a_west_q[kq]  <= a_west_arr[kq];
                b_north_q[kq] <= b_north_arr[kq];
            end
        end
    end

    wire [N*8-1:0] a_west_flat;
    wire [N*8-1:0] b_north_flat;
    genvar gi;
    generate
        for (gi = 0; gi < N; gi = gi + 1) begin : g_pack
            assign a_west_flat[gi*8 +: 8]  = a_west_q[gi];
            assign b_north_flat[gi*8 +: 8] = b_north_q[gi];
        end
    endgenerate

    wire [N*N*32-1:0] c_flat;
    cim_systolic_array #(.N(N)) array (
        .clk(clk), .rst(rst), .clr_acc(clr_acc), .en(en),
        .a_west(a_west_flat), .b_north(b_north_flat), .c_flat(c_flat)
    );

    always @(posedge clk) begin
        if (rst) begin
            wb_ack      <= 1'b0;
            wb_data_out <= 32'b0;
            state       <= S_IDLE;
            t           <= 6'd0;
            done        <= 1'b0;
            start_pulse <= 1'b0;
        end else begin
            start_pulse <= 1'b0;

            // Wishbone single-cycle handshake
            if (wb_stb && !wb_ack) begin
                wb_ack <= 1'b1;
                if (wb_we) begin
                    case (wb_addr[11:8])
                        4'h0: if (wb_data_in[0]) start_pulse <= 1'b1;   // CTRL
                        4'h1: for (bi = 0; bi < 4; bi = bi + 1)         // A load
                                  a_mem[{wb_addr[5:2], 2'b00} + bi] <= wb_data_in[bi*8 +: 8];
                        4'h2: for (bi = 0; bi < 4; bi = bi + 1)         // B load
                                  b_mem[{wb_addr[5:2], 2'b00} + bi] <= wb_data_in[bi*8 +: 8];
                        default: ;
                    endcase
                end else begin
                    case (wb_addr[11:8])
                        4'h0:    wb_data_out <= {31'b0, done};          // STATUS
                        4'h4:    wb_data_out <= c_flat[wb_addr[7:2]*32 +: 32]; // C
                        default: wb_data_out <= 32'h0;
                    endcase
                end
            end else begin
                wb_ack <= 1'b0;
            end

            // Run sequencing
            if (start_pulse) begin
                state <= S_RUN;
                t     <= 6'd0;
                done  <= 1'b0;
            end else if (state == S_RUN) begin
                if (t == RUN_CYCLES) begin
                    state <= S_IDLE;
                    done  <= 1'b1;
                end else begin
                    t <= t + 6'd1;
                end
            end
        end
    end
endmodule
`default_nettype wire

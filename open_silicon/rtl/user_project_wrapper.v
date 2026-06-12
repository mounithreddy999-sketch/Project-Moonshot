// SPDX-FileCopyrightText: 2026 Project Moonshot
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

`default_nettype none

// Efabless Caravel Defines
`define MPRJ_IO_PADS 38

/*
 *-------------------------------------------------------------
 *
 * user_project_wrapper
 *
 * This wrapper instantiates the Project Moonshot Compute-in-Memory
 * controllers. It provides the standard Efabless Caravel interface
 * required for SkyWater 130nm physical tape-out.
 *
 *-------------------------------------------------------------
 */

module user_project_wrapper #(
    parameter BITS = 32
) (
`ifdef USE_POWER_PINS
    inout vdda1,    // User area 1 AVDD
    inout vdda2,    // User area 2 AVDD
    inout vssa1,    // User area 1 AVSS
    inout vssa2,    // User area 2 AVSS
    inout vccd1,    // User area 1 VCCD
    inout vccd2,    // User area 2 VCCD
    inout vssd1,    // User area 1 VSSD
    inout vssd2,    // User area 2 VSSD
`endif

    // Wishbone Slave ports (WB MI A)
    input wb_clk_i,
    input wb_rst_i,
    input wbs_stb_i,
    input wbs_cyc_i,
    input wbs_we_i,
    input [3:0] wbs_sel_i,
    input [31:0] wbs_dat_i,
    input [31:0] wbs_adr_i,
    output wbs_ack_o,
    output [31:0] wbs_dat_o,

    // Logic Analyzer Signals
    input  [127:0] la_data_in,
    output [127:0] la_data_out,
    input  [127:0] la_oenb,

    // IOs
    input  [`MPRJ_IO_PADS-1:0] io_in,
    output [`MPRJ_IO_PADS-1:0] io_out,
    output [`MPRJ_IO_PADS-1:0] io_oeb,

    // Analog (direct connection to GPIO pad---use with caution)
    // Note that analog I/O is not available on the small version
    inout [`MPRJ_IO_PADS-10:0] analog_io,

    // Independent clock (on independent integer divider)
    input   user_clock2,

    // User maskable interrupt signals
    output [2:0] user_irq
);

    // -------------------------------------------------------------
    // PROJECT MOONSHOT: ANALOG CIM MACRO INSTANTIATION
    // -------------------------------------------------------------
    // This instantiates our Analog Compute-in-Memory (ACIM) controller
    // and wires it to the Caravel Wishbone bus for the SoC CPU to drive.

    analog_cim_controller #(
        .WL_WIDTH(256),
        .BL_WIDTH(256),
        .ADC_RES(8)
    ) moonshot_analog_macro (
    `ifdef USE_POWER_PINS
        .vdda1(vdda1),
        .vssa1(vssa1),
        .vccd1(vccd1),
        .vssd1(vssd1),
    `endif
        .clk(wb_clk_i),
        .rst(wb_rst_i),
        
        // Wishbone Control
        .wb_stb(wbs_stb_i),
        .wb_we(wbs_we_i),
        .wb_addr(wbs_adr_i),
        .wb_data_in(wbs_dat_i),
        .wb_data_out(wbs_dat_o),
        .wb_ack(wbs_ack_o),
        
        // Analog I/O Pins
        .analog_io(analog_io[7:0])
    );

    // Tie off unused signals
    assign io_out = 0;
    assign io_oeb = ~0; // All inputs
    assign la_data_out = 0;
    assign user_irq = 3'b000;

endmodule
`default_nettype wire

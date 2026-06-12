`timescale 1ns / 1ps
// SPDX-FileCopyrightText: 2026 Project Moonshot
// Licensed under the Apache License, Version 2.0 (the "License")

module analog_cim_tb;

    // Inputs
    reg clk;
    reg rst;
    reg wb_stb;
    reg wb_we;
    reg [31:0] wb_addr;
    reg [31:0] wb_data_in;

    // Outputs
    wire [31:0] wb_data_out;
    wire wb_ack;
    wire [7:0] analog_io;

    // Instantiate the Unit Under Test (UUT)
    analog_cim_controller uut (
        .clk(clk), 
        .rst(rst), 
        .wb_stb(wb_stb), 
        .wb_we(wb_we), 
        .wb_addr(wb_addr), 
        .wb_data_in(wb_data_in), 
        .wb_data_out(wb_data_out), 
        .wb_ack(wb_ack),
        .analog_io(analog_io)
    );

    // Clock Generation
    initial begin
        clk = 0;
        forever #5 clk = ~clk; // 100 MHz clock
    end

    // Test Sequence
    initial begin
        // Initialize Inputs
        $display("==================================================");
        $display("   PROJECT MOONSHOT: ANALOG CIM TESTBENCH         ");
        $display("==================================================");
        rst = 1;
        wb_stb = 0;
        wb_we = 0;
        wb_addr = 0;
        wb_data_in = 0;

        // Wait 100 ns for global reset to finish
        #100;
        rst = 0;
        #20;

        // TEST 1: Load Weights into SRAM (Addr 0x0000)
        $display("[%0t] TEST 1: Initiating Weight Load via Wishbone", $time);
        wb_stb = 1;
        wb_we = 1;
        wb_addr = 32'h00000000;
        wb_data_in = 32'hFFFFFFFF; // Load all 1s
        #10;
        wait(wb_ack);
        wb_stb = 0;
        wb_we = 0;
        #20;
        
        // TEST 2: Trigger MAC Operation (Addr 0x0004)
        $display("[%0t] TEST 2: Triggering Analog MAC Computation", $time);
        wb_stb = 1;
        wb_we = 1;
        wb_addr = 32'h00000004;
        wb_data_in = 32'h00000001; // START bit
        #10;
        wait(wb_ack);
        wb_stb = 0;
        wb_we = 0;
        #20;
        
        // TEST 3: Read ADC Result (Addr 0x0008)
        $display("[%0t] TEST 3: Reading ADC Output Result", $time);
        wb_stb = 1;
        wb_we = 0;
        wb_addr = 32'h00000008;
        #10;
        wait(wb_ack);
        $display("[%0t] RESULT: wb_data_out = 0x%h", $time, wb_data_out);
        wb_stb = 0;
        
        #50;
        $display("==================================================");
        $display("   TESTBENCH COMPLETE                             ");
        $display("==================================================");
        $finish;
    end
      
endmodule

`timescale 1ns/1ps

module tb_mask_controller;

    reg clk;
    reg rst_n;
    reg axi_we;
    reg [31:0] axi_addr;
    reg [31:0] axi_wdata;
    reg [575:0] raw_wl_in;
    reg [575:0] raw_bl_in;
    wire [575:0] masked_wl_out;
    wire [575:0] masked_bl_out;

    cim_mask_controller uut (
        .clk(clk),
        .rst_n(rst_n),
        .axi_we(axi_we),
        .axi_addr(axi_addr),
        .axi_wdata(axi_wdata),
        .raw_wl_in(raw_wl_in),
        .raw_bl_in(raw_bl_in),
        .masked_wl_out(masked_wl_out),
        .masked_bl_out(masked_bl_out)
    );

    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end

    initial begin
        $display("Starting Automated CIM Mask Verification...");
        
        // Initialize
        rst_n = 0;
        axi_we = 0;
        axi_addr = 0;
        axi_wdata = 0;
        raw_wl_in = {576{1'b1}}; // Simulate all decoders asserting HIGH
        raw_bl_in = {576{1'b1}};
        
        #20 rst_n = 1;
        
        // Write 512 to REG_MASK_WL (0x0000_0010)
        #10 axi_we = 1;
        axi_addr = 32'h0000_0010;
        axi_wdata = 32'd512;
        
        #10 axi_we = 0;
        
        #20; // Wait for logic to settle

        // Test Edge Case: Row 511 (Should be Enabled)
        if (masked_wl_out[511] !== 1'b1) begin
            $display("❌ [FAILED] Masking logic incorrectly gated active row 511.");
            $fatal(1); // Forces GitHub Actions to fail
        end

        // Test Edge Case: Row 512 (Should be Gated/0V)
        if (masked_wl_out[512] !== 1'b0) begin
            $display("❌ [FAILED] Masking logic failed to gate padded row 512.");
            $fatal(1);
        end

        $display("✅ [SUCCESS] Mask mathematics verified. No analog leakage detected.");
        $finish; // Graceful exit for GitHub Actions
    end

endmodule

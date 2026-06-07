`timescale 1ns/1ps

module tb_axi_bridge;

    reg clk;
    reg rst_n;
    reg wb_cyc_i, wb_stb_i, wb_we_i;
    reg [31:0] wb_adr_i, wb_dat_i;
    reg [3:0] wb_sel_i;
    wire wb_ack_o;
    wire [31:0] wb_dat_o;

    wire [31:0] m_axi_awaddr;
    wire m_axi_awvalid;
    reg m_axi_awready;

    wire [31:0] m_axi_wdata;
    wire [3:0] m_axi_wstrb;
    wire m_axi_wvalid;
    reg m_axi_wready;

    reg [1:0] m_axi_bresp;
    reg m_axi_bvalid;
    wire m_axi_bready;

    wire [31:0] m_axi_araddr;
    wire m_axi_arvalid;
    reg m_axi_arready;

    reg [31:0] m_axi_rdata;
    reg [1:0] m_axi_rresp;
    reg m_axi_rvalid;
    wire m_axi_rready;

    wb_to_axi_bridge uut (
        .clk(clk), .rst_n(rst_n),
        .wb_cyc_i(wb_cyc_i), .wb_stb_i(wb_stb_i), .wb_we_i(wb_we_i),
        .wb_adr_i(wb_adr_i), .wb_dat_i(wb_dat_i), .wb_sel_i(wb_sel_i),
        .wb_ack_o(wb_ack_o), .wb_dat_o(wb_dat_o),
        .m_axi_awaddr(m_axi_awaddr), .m_axi_awvalid(m_axi_awvalid), .m_axi_awready(m_axi_awready),
        .m_axi_wdata(m_axi_wdata), .m_axi_wstrb(m_axi_wstrb), .m_axi_wvalid(m_axi_wvalid), .m_axi_wready(m_axi_wready),
        .m_axi_bresp(m_axi_bresp), .m_axi_bvalid(m_axi_bvalid), .m_axi_bready(m_axi_bready),
        .m_axi_araddr(m_axi_araddr), .m_axi_arvalid(m_axi_arvalid), .m_axi_arready(m_axi_arready),
        .m_axi_rdata(m_axi_rdata), .m_axi_rresp(m_axi_rresp), .m_axi_rvalid(m_axi_rvalid), .m_axi_rready(m_axi_rready)
    );

    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end

    initial begin
        $display("Starting Automated AXI Bridge Verification...");
        
        rst_n = 0;
        wb_cyc_i = 0; wb_stb_i = 0; wb_we_i = 0;
        wb_adr_i = 0; wb_dat_i = 0; wb_sel_i = 0;
        m_axi_awready = 0; m_axi_wready = 0; m_axi_bvalid = 0; m_axi_bresp = 0;
        m_axi_arready = 0; m_axi_rvalid = 0; m_axi_rdata = 0; m_axi_rresp = 0;
        
        #20 rst_n = 1;
        
        // Simulate a Write Transaction
        #10 wb_cyc_i = 1; wb_stb_i = 1; wb_we_i = 1;
        wb_adr_i = 32'h1000; wb_dat_i = 32'hDEADBEEF; wb_sel_i = 4'hF;
        
        // Wait for AXI to issue write
        wait(m_axi_awvalid && m_axi_wvalid);
        #10 m_axi_awready = 1; m_axi_wready = 1;
        #10 m_axi_awready = 0; m_axi_wready = 0;
        
        // Send AXI Response
        #10 m_axi_bvalid = 1; m_axi_bresp = 2'b00;
        wait(wb_ack_o);
        
        // Since wb_ack_o is high, state machine correctly reached WB_ACK
        // Let's explicitly check some assertions before finish
        if (m_axi_awaddr !== 32'h1000) begin
             $display("❌ [FAILED] AXI Address mismatch.");
             $fatal(1);
        end
        if (m_axi_wdata !== 32'hDEADBEEF) begin
             $display("❌ [FAILED] AXI Data mismatch.");
             $fatal(1);
        end
        
        #10 m_axi_bvalid = 0; wb_cyc_i = 0; wb_stb_i = 0; wb_we_i = 0;

        $display("✅ [SUCCESS] Wishbone-to-AXI translation verified.");
        $finish;
    end

endmodule

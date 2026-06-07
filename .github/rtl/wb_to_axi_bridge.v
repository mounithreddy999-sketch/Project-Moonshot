// -----------------------------------------------------------------------------
// Module: wb_to_axi_bridge
// Description: Translates the Efabless Caravan Wishbone master signals 
//              from the PicoRV32 SoC into AXI4-Lite transactions for the 
//              CIM Tile controller.
// -----------------------------------------------------------------------------

module wb_to_axi_bridge (
    input  wire        clk,
    input  wire        rst_n,

    // --- Wishbone Slave Interface (From PicoRV32) ---
    input  wire        wb_cyc_i,
    input  wire        wb_stb_i,
    input  wire        wb_we_i,
    input  wire [31:0] wb_adr_i,
    input  wire [31:0] wb_dat_i,
    input  wire [3:0]  wb_sel_i,
    output reg         wb_ack_o,
    output reg  [31:0] wb_dat_o,

    // --- AXI4-Lite Master Interface (To cim_mask_controller) ---
    // Write Address Channel
    output reg  [31:0] m_axi_awaddr,
    output reg         m_axi_awvalid,
    input  wire        m_axi_awready,
    
    // Write Data Channel
    output reg  [31:0] m_axi_wdata,
    output reg  [3:0]  m_axi_wstrb,
    output reg         m_axi_wvalid,
    input  wire        m_axi_wready,
    
    // Write Response Channel
    input  wire [1:0]  m_axi_bresp,
    input  wire        m_axi_bvalid,
    output reg         m_axi_bready,
    
    // Read Address Channel
    output reg  [31:0] m_axi_araddr,
    output reg         m_axi_arvalid,
    input  wire        m_axi_arready,
    
    // Read Data Channel
    input  wire [31:0] m_axi_rdata,
    input  wire [1:0]  m_axi_rresp,
    input  wire        m_axi_rvalid,
    output reg         m_axi_rready
);

    // State Machine
    localparam IDLE         = 3'd0;
    localparam AXI_WR_ISSU  = 3'd1;
    localparam AXI_WR_RESP  = 3'd2;
    localparam AXI_RD_ISSU  = 3'd3;
    localparam AXI_RD_DATA  = 3'd4;
    localparam WB_ACK       = 3'd5;

    reg [2:0] state;

    wire wb_valid = wb_cyc_i && wb_stb_i;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            wb_ack_o <= 1'b0;
            wb_dat_o <= 32'd0;
            
            m_axi_awaddr <= 32'd0;
            m_axi_awvalid <= 1'b0;
            m_axi_wdata <= 32'd0;
            m_axi_wstrb <= 4'd0;
            m_axi_wvalid <= 1'b0;
            m_axi_bready <= 1'b0;
            
            m_axi_araddr <= 32'd0;
            m_axi_arvalid <= 1'b0;
            m_axi_rready <= 1'b0;
        end else begin
            // Default de-assertions
            wb_ack_o <= 1'b0;
            
            case (state)
                IDLE: begin
                    if (wb_valid && !wb_ack_o) begin
                        if (wb_we_i) begin
                            // Initiate AXI Write
                            m_axi_awaddr  <= wb_adr_i;
                            m_axi_wdata   <= wb_dat_i;
                            m_axi_wstrb   <= wb_sel_i;
                            m_axi_awvalid <= 1'b1;
                            m_axi_wvalid  <= 1'b1;
                            m_axi_bready  <= 1'b1;
                            state <= AXI_WR_ISSU;
                        end else begin
                            // Initiate AXI Read
                            m_axi_araddr  <= wb_adr_i;
                            m_axi_arvalid <= 1'b1;
                            m_axi_rready  <= 1'b1;
                            state <= AXI_RD_ISSU;
                        end
                    end
                end

                AXI_WR_ISSU: begin
                    if (m_axi_awready) m_axi_awvalid <= 1'b0;
                    if (m_axi_wready)  m_axi_wvalid  <= 1'b0;
                    if (!m_axi_awvalid && !m_axi_wvalid) begin
                        state <= AXI_WR_RESP;
                    end
                end

                AXI_WR_RESP: begin
                    if (m_axi_bvalid) begin
                        m_axi_bready <= 1'b0;
                        state <= WB_ACK;
                    end
                end

                AXI_RD_ISSU: begin
                    if (m_axi_arready) begin
                        m_axi_arvalid <= 1'b0;
                        state <= AXI_RD_DATA;
                    end
                end

                AXI_RD_DATA: begin
                    if (m_axi_rvalid) begin
                        wb_dat_o <= m_axi_rdata;
                        m_axi_rready <= 1'b0;
                        state <= WB_ACK;
                    end
                end

                WB_ACK: begin
                    wb_ack_o <= 1'b1;
                    state <= IDLE;
                end
                
                default: state <= IDLE;
            endcase
        end
    end

endmodule

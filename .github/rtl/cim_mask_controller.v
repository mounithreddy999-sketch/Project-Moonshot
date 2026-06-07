// -----------------------------------------------------------------------------
// Module: cim_mask_controller
// Description: AXI-mapped dynamic masking unit for the 22nm RRAM CIM Macro.
// This module interprets the compiler's Tile Descriptor to physically gate 
// Wordlines (WL) and Bitlines (BL) to prevent analog leakage on padded edge tiles.
// -----------------------------------------------------------------------------

module cim_mask_controller #(
    parameter ARRAY_DIM = 576,        // Physical array dimension (T)
    parameter IDX_WIDTH = 10          // ceil(log2(576)) = 10 bits
)(
    input  wire                 clk,
    input  wire                 rst_n,

    // --- AXI-Lite Interface (Simplified for scaffolding) ---
    input  wire                 axi_we,       // Write enable
    input  wire [31:0]          axi_addr,     // Register address
    input  wire [31:0]          axi_wdata,    // Data from compiler/DMA

    // --- Raw Decoder Inputs from the Sequencer ---
    input  wire [ARRAY_DIM-1:0] raw_wl_in,    // Standard computed Wordlines
    input  wire [ARRAY_DIM-1:0] raw_bl_in,    // Standard computed Bitline enables

    // --- Masked Outputs to the Physical Analog Drivers ---
    output wire [ARRAY_DIM-1:0] masked_wl_out,
    output wire [ARRAY_DIM-1:0] masked_bl_out
);

    // -------------------------------------------------------------------------
    // Control Registers
    // -------------------------------------------------------------------------
    // If the register holds a value >= ARRAY_DIM, no masking occurs.
    reg [IDX_WIDTH-1:0] reg_gate_wl_start;
    reg [IDX_WIDTH-1:0] reg_gate_bl_start;

    // AXI Write Logic (Address Map matches our previous CSR specification)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            reg_gate_wl_start <= ARRAY_DIM[IDX_WIDTH-1:0]; // Default: No masking
            reg_gate_bl_start <= ARRAY_DIM[IDX_WIDTH-1:0]; // Default: No masking
        end else if (axi_we) begin
            case (axi_addr)
                32'h0000_0010: reg_gate_wl_start <= axi_wdata[IDX_WIDTH-1:0]; // REG_MASK_WL
                32'h0000_0024: reg_gate_bl_start <= axi_wdata[IDX_WIDTH-1:0]; // REG_MASK_BL
            endcase
        end
    end

    // -------------------------------------------------------------------------
    // Dynamic Mask Vector Generation
    // -------------------------------------------------------------------------
    // Generate a 576-bit vector where bits < start_idx are 1, and >= start_idx are 0.
    
    wire [ARRAY_DIM-1:0] wl_mask_vector;
    wire [ARRAY_DIM-1:0] bl_mask_vector;

    // Using a generate block to create the wide comparison logic
    genvar i;
    generate
        for (i = 0; i < ARRAY_DIM; i = i + 1) begin : gen_masks
            assign wl_mask_vector[i] = (i < reg_gate_wl_start) ? 1'b1 : 1'b0;
            assign bl_mask_vector[i] = (i < reg_gate_bl_start) ? 1'b1 : 1'b0;
        end
    endgenerate

    // -------------------------------------------------------------------------
    // Physical Driver Gating (The Hardware Kill Switch)
    // -------------------------------------------------------------------------
    // Apply the logical AND. If the compiler flagged the row as padded, 
    // the mask bit is 0, forcing the physical wordline driver to stay at 0V.
    
    assign masked_wl_out = raw_wl_in & wl_mask_vector;
    assign masked_bl_out = raw_bl_in & bl_mask_vector;

endmodule

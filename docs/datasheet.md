# Project Moonshot: Preliminary Datasheet (v1.0)

**Heterogeneous Compute-in-Memory (CIM) Accelerator for Datacenter LLM Inference**

## 1. General Description
Project Moonshot is a heterogeneous Network-on-Package (NoP) accelerator architecture designed to overcome the "Memory Wall" in Trillion-Parameter LLM inference. It utilizes a $2 \times 2$ Universal Chiplet Interconnect Express (UCIe) mesh to intelligently route neural network sub-layers.
- **Attention Layers (Precision Critical):** Routed to Digital FP-CIM (Float-16 / BFloat-16) chiplets.
- **Feed-Forward Layers (Compute Heavy):** Routed to ultra-efficient Analog ACIM chiplets.

The architecture features an embedded AI compiler optimization pass that uses Polynomial Regression models to dynamically counter non-linear physical degradation (Thermal Drift, IR Drop, Device Mismatch).

## 2. Target Manufacturing Specifications
- **Process Node:** SkyWater 130nm (Open-Source)
- **Die Area:** $2.92 \text{mm} \times 3.52 \text{mm}$ (Per Chiplet)
- **Target Clock Speed:** 100 MHz (10.0 ns period)
- **Core Voltage (VCCD/VSSD):** 1.8V
- **Analog Macro Voltage (VDDA/VSSA):** 3.3V

## 3. Simulated Performance Metrics (Phase IV Results)
*Note: Results based on Python physics simulation framework over 10,000 samples.*

| Metric | Digital FP-CIM | Analog ACIM (Unmitigated) | Analog ACIM (AI Mitigated) |
|---|---|---|---|
| **Precision** | Exact (FP16) | Highly degraded (0.63 MSE) | Near-Exact (0.12 MSE) |
| **Thermal Drift Tolerance** | N/A | Fails > 1.5X | Stable up to 3.0X |
| **Energy / MAC** | ~ 1.5 pJ | ~ 0.1 pJ | ~ 0.15 pJ (Includes compiler overhead) |

## 4. Pinout Description (Caravel Wrapper)

| Pin Group | Direction | Width | Description |
|---|---|---|---|
| `wb_clk_i` | Input | 1 | Master Wishbone Clock (100 MHz target) |
| `wb_rst_i` | Input | 1 | Master System Reset (Active High) |
| `wbs_adr_i` | Input | 32 | Wishbone Address Bus |
| `wbs_dat_i` | Input | 32 | Wishbone Write Data Bus |
| `wbs_dat_o` | Output | 32 | Wishbone Read Data Bus |
| `wbs_we_i` | Input | 1 | Wishbone Write Enable |
| `wbs_stb_i` | Input | 1 | Wishbone Strobe |
| `wbs_ack_o` | Output | 1 | Wishbone Acknowledge |
| `analog_io` | In/Out | 8 | Direct Analog GPIO access for external testing |

## 5. Physical Floorplan Countermeasures
To combat IR Drop (center voltage sag), the `config.json` specifies a highly over-provisioned Power Delivery Network (PDN).
- **Core Ring Width:** $3.1 \mu\text{m}$
- **V/H Pitch:** $25.0 \mu\text{m}$
- **Target Density:** 40% (Leaving massive routing channels for analog isolation).

## 6. AI Safety Integrations
Compliant with the AI Verify Foundation framework. All hardware compilation passes are gated by `evaluator/moonshot_eval.py`, a Red-Teaming script that blocks the physical compilation of compromised or hallucinating weights.

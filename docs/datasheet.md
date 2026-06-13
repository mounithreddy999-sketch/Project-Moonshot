# Project Moonshot: Preliminary Datasheet (v1.0)

**Heterogeneous Compute-in-Memory (CIM) Accelerator for Datacenter LLM Inference**

> **Status note:** This datasheet describes the **target architecture**, characterized in a Python physics-simulation framework. Sections marked *Simulated* are software results, not silicon measurements. The physical artifact in this repo is a SkyWater 130nm tape-out of the digital Caravel interface (see `docs/tapeout_report.md`); the analog CIM compute macro is a behavioral model and the synthesizable compute datapath is future work.

## 1. General Description
Project Moonshot is a heterogeneous Network-on-Package (NoP) accelerator architecture designed to overcome the "Memory Wall" in Trillion-Parameter LLM inference. It uses a $2 \times 2$ Universal Chiplet Interconnect Express (UCIe) mesh to route neural-network sub-layers:
- **Attention Layers (Precision Critical):** routed to Digital FP-CIM (Float-16 / BFloat-16) chiplets.
- **Feed-Forward Layers (Compute Heavy):** routed to ultra-efficient Analog ACIM chiplets.

The architecture features a compiler optimization pass that uses Polynomial Regression (and a PyTorch DNN variant) to counter non-linear physical degradation (Thermal Drift, IR Drop, Device Mismatch). This routing and calibration is implemented and runnable in `simulator/`.

## 2. Target Manufacturing Specifications
- **Process Node:** SkyWater 130nm (Open-Source)
- **Die Area:** $2.92 \text{mm} \times 3.52 \text{mm}$ per chiplet *(this is the die size of the hardened feasibility vehicle)*
- **Target Clock Speed:** 100 MHz (10.0 ns period)
- **Core Voltage (VCCD/VSSD):** 1.8V
- **Analog Macro Voltage (VDDA/VSSA):** 3.3V

## 3. Simulated Performance Metrics (Phase IV Results)
*Note: Results from the Python physics-simulation framework over 10,000 samples (`simulator/`). Not silicon-measured.*

| Metric | Digital FP-CIM | Analog ACIM (Unmitigated) | Analog ACIM (AI Mitigated) |
|---|---|---|---|
| **Precision** | Exact (FP16) | Highly degraded (0.63 MSE) | Near-Exact (0.12 MSE) |
| **Thermal Drift Tolerance** | N/A | Fails > 1.5X | Stable up to 3.0X |
| **Energy / MAC** | ~ 1.5 pJ | ~ 0.1 pJ | ~ 0.15 pJ (Includes compiler overhead) |

*Reproduce the drift-vs-recovery result with `python simulator/math_engine/analog_thermal_drift.py`.*

## 4. Pinout Description (Caravel Wrapper) — *implemented in RTL*

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
| `analog_io` | In/Out | 8 | Direct Analog GPIO access (reserved for the future analog macro) |

> The current `analog_cim_controller.v` implements the Wishbone handshake (244 synthesized cells); the CIM compute datapath behind this interface is not yet synthesizable RTL.

## 5. Physical Floorplan Countermeasures — *implemented in `config.json`*
The IR-drop simulation showed center-voltage sag causes catastrophic MSE in analog CIM, so the floorplan over-provisions the Power Delivery Network (PDN) as a forward-looking countermeasure for the analog macro.
- **Core Ring Width:** $3.1 \mu\text{m}$
- **V/H Pitch:** $25.0 \mu\text{m}$
- **Target Density:** 40% (leaving routing/isolation channels and reserved area for the analog macro)

## 6. AI Safety Integration — *simulated harness*
The build flow includes `evaluator/moonshot_eval.py`, a red-team harness (modeled on the AI Verify Foundation approach) that probes a **mock** model for prompt-injection and hallucination failures and gates compilation on a safety threshold. It currently runs against a simulated `MockFoundationModel`; wiring it to a real model checkpoint is future work.
